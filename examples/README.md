# Examples

Small, runnable examples of the `dhis2w-security` surfaces. Each one shows one thing and
assumes a configured DHIS2 profile (`d2w profile add <name>`).

- `cli/security.sh` — the `d2w security` command group: the settings and authorities
  reads, then the audit runner with its check selection, thresholds, resume, and the
  interactive sharing explorer.
- `mcp/security.py` — the three read-only `security_*` MCP tools, driven through an
  in-process FastMCP client.
