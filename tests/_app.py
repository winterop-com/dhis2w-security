"""Build the pack's own CLI app and MCP server for a version tree, without the host's root CLI.

The suite mounts the pack's contribution on a bare Typer app carrying the root options the
commands read (`--profile`, `--json`), so what a test drives is this pack's surface alone.
"""

from __future__ import annotations

import os
from typing import Annotated

import typer
from dhis2w_core.cli_output import JSON_OUTPUT
from fastmcp import FastMCP

from dhis2w_security.plugin import plugin


def build_pack_app(version_key: str = "v43") -> typer.Typer:
    """Build a Typer app with the pack's `security` sub-app mounted for `version_key`."""
    app = typer.Typer(no_args_is_help=True, add_completion=False, pretty_exceptions_enable=False)

    @app.callback()
    def _root(
        profile: Annotated[str | None, typer.Option("--profile", "-p")] = None,
        json_: Annotated[bool, typer.Option("--json", "-j")] = False,
    ) -> None:
        """Set the active DHIS2 profile and the output mode for this invocation."""
        if profile:
            os.environ["DHIS2_PROFILE"] = profile
        JSON_OUTPUT.set(json_)

    plugin.contribute(version_key).mount_cli(app)
    return app


def build_pack_server(version_key: str = "v43") -> FastMCP:
    """Build a FastMCP server carrying the pack's tools for `version_key`."""
    server: FastMCP = FastMCP("security-mcp-test")
    plugin.contribute(version_key).register_mcp(server)
    return server
