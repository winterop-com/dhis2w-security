# CLAUDE.md

Guidance for Claude Code working in the `dhis2w-security` plugin pack.

## NO EMOJIS EVER

Not in commit messages, PR titles, PR descriptions, code comments, docstrings,
documentation, or any output. Use plain text (`[x]`, `[ ]`, `CRITICAL`, `Note:`,
`WARNING:`).

## This repository follows the host's rules

`dhis2w-security` is a plugin pack for
[dhis2w](https://github.com/winterop-com/dhis2w). The host's
[CLAUDE.md](https://github.com/winterop-com/dhis2w/blob/main/CLAUDE.md) is the
authority on conventions, and everything in it applies here: `uv` for every Python
operation (`uv add`, never a hand-edited dependency), the `src/` layout with the
`uv_build` backend, Pydantic for all structured data (no `dict`s, no `@dataclass`es),
Typer for the CLI, FastMCP for the MCP surface, pytest for every test, strict ruff +
mypy + pyright, full descriptive names, one-line Google-style docstrings on every
module, class, and function, conventional commits, no AI attribution, and the
greenfield voice: describe what the code does now, never how it got there.

## The version trees

`dhis2w_security.v41`, `.v42`, `.v43`, and `.v44` mirror the host's plugin trees. v43 is
the canonical baseline: new behaviour is written there first and copied to the
siblings, which differ only by import path until a wire shape genuinely diverges.
Every behaviour-changing edit lands in every tree; a new file lands in every tree,
a deletion in every tree. The tests are one tree parametrised over all of them,
never per-tree copies.

Version-invariant logic — the taxonomy, the severity model, the guardrails, the
orchestration, and the rendering — lives once in `dhis2w_security.core`.

## The pluginkit contract

The pack advertises one plain-class plugin object under the `dhis2w.plugins.v1`
entry-point group. Its `@extension def contribute(self, version_key)` returns a
`Contribution` naming the tree's `cli` and `mcp` modules; each of those exposes a
`register()` function. The object is a plain class, not a `BaseModel` — pluginkit
scans its attributes and a model subclass raises during that scan.

## Tests

The suite opts into the host's test environment: `dhis2w-core[testing]` as a dev
dependency and `pytest_plugins = ["dhis2w_core.testing"]` in the root `conftest.py`.
That carries the respx mocker default, the profile-environment reset, the
browser-launch guard, and the version-tree fixtures. Tests build this pack's own
Typer app and FastMCP server (`tests/_app.py`), never the host's root CLI.

Run every invocation with `BROWSER=true`.

## Before a PR

`make lint && make test` must pass.

## Releases

This pack releases the same version as the dhis2w host, the way every repository of the
ecosystem does (host `docs/decisions.md`, 2026-09-29). The host is released first; then this
pack pins `dhis2w-core`, `dhis2w-client` and, in the dev group, `dhis2w-core[testing]` and
`dhis2w-cli` to exactly that version, relocks (`uv lock --upgrade`, with `--refresh` when the
PyPI index lags behind the host's publish), passes `make lint` and `make test`, and is tagged
`vX.Y.Z` - the tag is what publishes to PyPI. A pack released before the host cannot resolve
it.
