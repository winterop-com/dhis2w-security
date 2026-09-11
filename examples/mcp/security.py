"""Exercise the cheap read-only `security_*` MCP tools via an in-process FastMCP Client.

Calls the three single-request read tools: `security_settings`, `security_authorities`,
and `security_version`. The long-running `d2w security audit` stays CLI-only and is not
an MCP tool.

The server here carries this pack's tools and nothing else. The dhis2w MCP server picks
the same tools up from the pack's entry point, so what it answers is what this prints.

Usage:
    uv run python examples/mcp/security.py
"""

from __future__ import annotations

import asyncio
import os

from dhis2w_core.plugin import resolve_startup_version
from fastmcp import Client, FastMCP

from dhis2w_security.plugin import plugin


def build_security_server() -> FastMCP:
    """Build a FastMCP server carrying this pack's tools for the active plugin tree."""
    server: FastMCP = FastMCP("dhis2w-security")
    plugin.contribute(resolve_startup_version()).register_mcp(server)
    return server


async def main() -> None:
    """Connect to the in-process MCP server and call the three security read tools."""
    profile = os.environ.get("DHIS2_PROFILE", "local_basic")
    async with Client(build_security_server()) as client:
        settings = await client.call_tool("security_settings", {"profile": profile})
        settings_payload = settings.data or settings.structured_content or {}
        print(f"security_settings returned {type(settings_payload).__name__}")

        authorities = await client.call_tool("security_authorities", {"profile": profile})
        authorities_payload = authorities.data or authorities.structured_content or {}
        print(f"security_authorities returned {type(authorities_payload).__name__}")

        version = await client.call_tool("security_version", {"profile": profile})
        version_payload = version.data or version.structured_content or {}
        print(f"security_version returned {type(version_payload).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
