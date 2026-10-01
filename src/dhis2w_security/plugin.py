"""The plugin object dhis2w-core loads from the `dhis2w.plugins.v1` entry-point group."""

from __future__ import annotations

from dhis2w_core.plugin import Contribution, extension

#: The plugin trees this pack ships, one per supported DHIS2 major.
SUPPORTED_VERSION_KEYS: frozenset[str] = frozenset({"v41", "v42", "v43", "v44"})
#: The tree an unrecognised version key binds to; v43 is the canonical baseline.
DEFAULT_VERSION_KEY = "v43"


class SecurityPlugin:
    """Plugin descriptor for the read-only DHIS2 security surface."""

    @extension
    def contribute(self, version_key: str) -> Contribution:
        """Contribute `d2w security` and the read-only `security_*` MCP tools for `version_key`."""
        tree = version_key if version_key in SUPPORTED_VERSION_KEYS else DEFAULT_VERSION_KEY
        return Contribution(
            name="security",
            description="Inspect DHIS2 security posture (settings, account authorities).",
            cli_module=f"dhis2w_security.{tree}.cli",
            mcp_module=f"dhis2w_security.{tree}.mcp",
        )


plugin = SecurityPlugin()
