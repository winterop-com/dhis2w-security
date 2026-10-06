# dhis2w-security

The security plugin pack for [dhis2w](https://github.com/winterop-com/dhis2w). It adds
the `d2w security` command group to the `d2w` CLI and three read-only `security_*` tools
to the dhis2w MCP server, and it reaches a DHIS2 instance through the same profiles,
auth providers, and typed client every other dhis2w surface uses.

Everything the pack does is a read. Requests go out as GET against a tested allowlist,
with a single documented exception: the default-credential probe makes one HTTP Basic
login attempt (see [Default-credential probe](#default-credential-probe)).

## Install

Alongside a global `d2w` install:

```bash
uv tool install 'dhis2w-cli[security]'
```

Inside a project that already has `dhis2w-cli`:

```bash
uv add dhis2w-security
```

The pack advertises its plugin object under the `dhis2w.plugins.v1` entry-point group,
so `d2w` and the MCP server pick it up as soon as it is installed in the same
environment. Nothing needs to be registered by hand.

## The CLI surface

```
d2w security settings        Password policy, credential expiry, registration, lockout
d2w security authorities     The audited account's authorities, grouped by risk category
d2w security audit           The full multi-check audit run, written to a report folder
d2w security report          Re-render an existing run's reports from its JSONL spine
```

`d2w --json security settings` emits the same data as a typed JSON object, as it does
everywhere in `d2w`.

`d2w security audit` streams a live progress display, runs the checks described below,
and writes a run folder holding the report in Markdown, plain text, CSV, and a
self-contained HTML bundle (open `report.dc.html`; the scan's data lives in
`report-data.js` beside a fixed template, runtime, and logo). Every HTML section header
carries a "See all checks" toggle listing each control the check evaluated with its live
PASS / FLAGGED / SKIPPED outcome, so a reader sees what was inspected and passed, not
only what tripped. A run is resumable, and `--checks` / `--skip` select the checks by
key. `d2w security report` re-renders a finished run without re-scanning.

`--sharing-graph` / `--visualize` additionally writes `sharing-explorer.html`, an offline
d3 bundle described under [Public metadata sharing](#public-metadata-sharing).

## The MCP tools

Three tools, each one read-only GET against an already-allowlisted path:

| Tool | What it answers |
| --- | --- |
| `security_settings` | The security slice of `/api/systemSettings` |
| `security_authorities` | The audited account's authorities, categorised by risk |
| `security_version` | The instance's version and patch posture |

`security_version` deliberately skips the external release feed, so the tool stays a
single DHIS2 request with no external egress; the feed-based behind-latest-patch
refinement is audit-only. The audit runner, the credential probe, the guest probe, and
the sharing scan are CLI-only: they are slow, they write to disk, and the probe makes a
login attempt, none of which belongs behind an agent's tool call.

## The checks

The audit runs these in canonical order. Each is selectable by its key.

### Version and patch posture (`version`)

Reads the running version and grades it: an end-of-life version line, patch and hotfix
currency within the supported line, and a curated security-advisory patch floor sourced
from the DHIS2 GitHub advisories. A newer release line is an informational note, not a
finding, because a supported non-latest line is a healthy state.

### Transport and security headers (`transport`)

Reads the TLS scheme off the resolved base URL and the security headers off one
`/api/system/info` response: Strict-Transport-Security, Content-Security-Policy (and
-Report-Only), X-Frame-Options, X-Content-Type-Options, the three cross-origin policy
headers, and Server. It flags plaintext HTTP, a missing HSTS / CSP / nosniff header,
missing anti-framing when neither X-Frame-Options nor a CSP `frame-ancestors` directive
is present, and a Server header that discloses a version token.

The grading goes past presence. A weak HSTS header has its `max-age` parsed with a
digit-only regex and raises one WARN when it is missing, invalid, non-positive, below a
day, or below the recommended year. A weak CSP is parsed into a directive map and
aggregated into one MEDIUM listing the failed directives: report-only-only mode, a
missing fetch directive on a content-governing policy, a broad source (`*`, `http:`,
`https:`, `data:`) or `unsafe-inline` / `unsafe-eval` in script sources, an un-locked-down
`object-src`, an unset or broad `base-uri`, and a present-but-broad `frame-ancestors`
(`strict-dynamic` is annotated, never warned). DHIS2's stock `frame-ancestors 'self';`
is a frame-only policy, so its content directives are left ungraded and a default
instance is never flagged; a missing `frame-ancestors` is owned by the anti-framing WARN
and never double-flagged. DHIS2 sets none of COOP/COEP/CORP, so those three absences are
aggregated into a single INFO rather than three WARNs that would fire on every stock
instance.

The same probe reads the live CORS response headers. DHIS2 emits
Access-Control-Allow-Origin and -Allow-Credentials only on a request carrying an Origin,
so the probe sends a benign foreign Origin (an unresolvable `.invalid` host, never the
instance's own origin, which DHIS2 always echoes) on its allowlisted
`GET /api/system/info` and grades what comes back: a wildcard or the reflected foreign
origin with credentials is HIGH, the same without credentials is WARN, and a specific
origin echoed with credentials is a trusted-origin-review WARN. That reads what the
server actually grants on the wire, complementing the settings check's read of the
declared `/api/configuration/corsWhitelist`.

### System security settings (`settings`)

Password policy and registration settings: a weak minimum password length, failed-login
lockout disabled, passwords that never expire, self-registration captcha disabled, users
able to self-grant their own authorities, email verification not enforced, a permissive
`*` CORS origin from `/api/configuration/corsWhitelist` (plus an INFO enumerating a
non-empty no-wildcard allowlist for review), a static reminder that DHIS2 has no global
2FA enforcement, and account recovery or email verification enabled while SMTP is
unconfigured. The email-verification WARN fires only when `enforceVerifiedEmail` is
explicitly off, so the key's absence on v41 is left untouched.

### Audited account authorities (`authorities`)

Groups the audited account's dangerous authorities into named categories: superuser
(ALL), user and role management including the `F_IMPERSONATE_USER` account takeover, app
management and custom JS/CSS, SQL views, route management, system configuration, metadata
import and export, tracker administration, and data administration.

### Instance role audit (`roles`)

Flags ALL-granting and dangerous-authority roles out of that same taxonomy, with member
counts. A role granting route management or user management is HIGH.

### User account hygiene (`hygiene`)

Joins privileged accounts to login recency and 2FA posture, including
superuser-without-2FA via the v42+ `/api/users/twoFactor` audit endpoint. A privileged
account that never logged in is HIGH and one gone stale past `--stale-days` is MEDIUM,
both as per-user rows. Active non-privileged accounts that never logged in or went stale
roll up into at most two aggregate WARNs carrying the offender count and a username
sample capped at ten, so a large instance never emits a row per account and a privileged
never-logged-in account is never double-counted. Password age is graded the same way but
independently of privilege: every active account whose password is older than
`--max-password-age` (a year by default) or was never set rolls up into one aggregate
WARN.

### Default-credential probe (`credential-probe`)

One HTTP Basic login attempt against `/api/me` with the well-known admin/district pair,
flagged CRITICAL when it succeeds. It is on by default and `--no-credential-probe` turns
it off. Exactly one attempt is made, and the probe touches no path other than `/api/me`.

### Anonymous access (`guest`)

Unauthenticated reads of login-required endpoints, plus the self-registration and
account-recovery state an anonymous caller can observe.

### Installed apps (`apps`)

Inventories side-loaded frontend code, App Hub update currency, and custom JS/CSS
injection, degrading cleanly when the App Hub is unreachable.

### Public metadata sharing (`sharing`)

Finds public-write and externally-accessible objects across the data-bearing and
exposure-prone metadata types. Each object's sharing block is decoded and built into a
single access graph alongside the user, role, and group principals, paged and capped by
`--max-objects` with loud truncation.

`--sharing-graph` / `--visualize` writes `sharing-explorer.html` into the run folder: a
self-contained offline d3 bundle over that same graph, answering who can concretely read
or write an object and by what path. It carries an object tree, exposure triage,
by-principal and by-role pivots, a force-directed graph of the sharing topology, and an
access-matrix heatmap of group access per object type.

### External login methods (`auth-methods`)

Inventories the pre-auth OIDC providers offered on the login page from `/api/loginConfig`
(each an INFO, as a federated trust path; SAML providers are not surfaced here) and the
OAuth2 clients DHIS2 acts as an authorization server for from `/api/oAuth2Clients`. A
broad grant type (client credentials, implicit, password, or the device-authorization
grant) or a loose redirect URI (a wildcard, or a non-loopback cleartext `http://` target;
loopback is not flagged, per RFC 8252) is MEDIUM, and a per-clean-client INFO is
suppressed when that client also trips a MEDIUM. `/api/oAuth2Clients` needs the
`F_OAUTH2_CLIENT_MANAGE` authority on v42/v43, so a 401/403/404 degrades the check with a
note (never retried) while the loginConfig findings still run. No secret field is
projected, so a client secret can never reach a finding.

### Personal access tokens (`tokens`)

Inventories the tokens readable by the audited account from `/api/apiToken` and flags a
non-expiring token (a null, absent, or already-past `expire`, HIGH) and a token with no
IP allowlist (HIGH), calling out the worst case of one that both never expires and is
usable from anywhere. A MEDIUM inventory summary states the scope verbatim, because scope
is a runtime authority distinction: `ApiToken` is private by default, so a non-superuser
sees only its own tokens and the run adds an INFO caveat that other users' are invisible,
while an account with ALL gets the system-wide inventory. The token secret is never on
the wire and is never read.

### Route API targets (`routes`)

Inventories DHIS2 Route objects from `/api/routes` and flags each whose destination
resolves to a private or internal address (RFC1918, loopback, link-local, unspecified,
IPv6 ULA), an internal hostname (`localhost`, `.internal`, `.local`, `.localdomain`), or
the cloud instance-metadata endpoint (the IPv4 and IPv6 metadata addresses and
`metadata.google.internal`, raised as the more specific metadata finding so one host
never produces two HIGHs). A Route is a server-side reverse proxy DHIS2 fetches on the
caller's behalf, which makes a private destination an SSRF primitive. The check also
flags `/**` subpath wildcards and routes with no required authorities that fall back to
ACL sharing, and notes routes carrying stored upstream credentials (the secret is
write-only upstream and never read; only the non-secret identity is shown). It inspects
the configured URL host only and never executes a route.

### Audit logging configuration (`audit-config`)

Reports the DHIS2 audit configuration: the `system.audit.enabled` master switch, the
`audit.logger` file sink, the `audit.database` sink, and the four
`audit.metadata` / `audit.aggregate` / `audit.tracker` / `audit.api` scope matrices. That
posture lives only in `dhis.conf` and no API endpoint exposes it, so the API-first result
is an INFO saying the posture is not API-readable, never a claim that auditing is off.
Pass `--dhis-conf <path>` (or set `DHIS2_CONF_LOCATION`) pointed at a local copy of the
server's `dhis.conf` to evaluate it; the check then flags auditing disabled
instance-wide, both sinks off, every scope matrix blank while auditing is on, and narrow
scope coverage that leaves scopes unmonitored or omits CREATE/UPDATE/DELETE/SECURITY. A
missing or unreadable path degrades with a note.

Secret redaction is enforced by construction: the parser retains only the audit keys plus
a set / not-set flag for the confidential keys (the encryption, connection, analytics,
LDAP, Redis, Artemis, OAuth2-keystore, and monitoring passwords) and physically cannot
hold a secret value, so no password can reach a rendered report.

## Version trees

The pack mirrors the host's plugin trees. `dhis2w_security.v41`, `dhis2w_security.v42`,
`dhis2w_security.v43`, and `dhis2w_security.v44` each carry the thin per-version shim
(`cli.py`, `mcp.py`, `service.py`, `models.py`, and the `_wire.py` holding that major's
wire divergences); v43 is the canonical baseline. Everything version-invariant — the
authority taxonomy, the severity model, the guardrail contract, the audit orchestration,
and the report and explorer rendering — lives once in `dhis2w_security.core`.

The plugin object binds the tree the host asks for and falls back to v43 for an
unrecognised version key.

## Upstream DHIS2 quirks

The code cites these entries in the host repository's
[DHIS2_ISSUES.md](https://github.com/winterop-com/dhis2w/blob/main/DHIS2_ISSUES.md), which carry the
version observed, a `curl` repro, and the expected-versus-actual behaviour:

- **#14** — the Route `auth` block: v41's undiscriminated four-variant union has no
  OAuth2 client-credentials variant, v42/v43's is a discriminated five-variant union.
- **#42** — `/api/systemSettings` returns `keyAnalysisDisplayProperty` lowercase, which
  the generated `DisplayProperty` enum rejects; `SecuritySettings` is the projection that
  parses.
- **#45** — an authorities endpoint that answers 500 on some deployments, which skips the
  check rather than failing it.
- **#52** — the OAuth2 client wire shape: v41 reads `cid` with array-typed
  `grantTypes` / `redirectUris`, v42/v43 read `clientId` with comma-string
  `authorizationGrantTypes` / `redirectUris`.
- **#54** — the audit scope matrix that is explicitly DISABLED rather than absent, which
  turns off a scope DHIS2 would otherwise audit by default.
- **#56** — `passwordLastUpdated` is nested under `userCredentials` on v41 and flattened
  onto the User on v42/v43.
- **#57** — an authority naming divergence between the API and the auditor app's own
  constant.
- **#58** — v42 and v43 removed every admin-readable per-user 2FA field from the User
  resource, so enrolment is read from the superuser-only `/api/users/twoFactor` endpoint
  and `/api/users/twoFactor` does not exist on v41 at all.
- **#60** — the CSP and HSTS headers a container or proxy adds rather than DHIS2 code,
  and DHIS2's frame-only default policy.

## Development

```bash
make install   # sync the environment
make lint      # ruff + mypy + pyright
make test      # pytest
```

See `CLAUDE.md` for the conventions this repository follows.
