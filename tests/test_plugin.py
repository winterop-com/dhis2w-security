"""The pluginkit contract: the entry point declaration, the contributed modules, and the tree fallback."""

from __future__ import annotations

import tomllib
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from dhis2w_core.plugin import ENTRY_POINT_GROUP, Contribution, load_plugin_host

from dhis2w_security.plugin import plugin

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
TREES = ("v41", "v42", "v43")


def test_pyproject_declares_the_entry_point() -> None:
    """pyproject advertises the plugin object under the `dhis2w.plugins.v1` group."""
    manifest = tomllib.loads(_PYPROJECT.read_text())
    declared = manifest["project"]["entry-points"][ENTRY_POINT_GROUP]
    assert declared == {"security": "dhis2w_security.plugin:plugin"}


def test_installed_entry_point_loads_the_plugin_object() -> None:
    """The installed distribution resolves its entry point to the pack's plugin object."""
    found = [point for point in entry_points(group=ENTRY_POINT_GROUP) if point.value.startswith("dhis2w_security.")]
    if not found:
        pytest.skip("the pack is installed without its entry-point metadata (`uv pip install --no-deps -e .`)")
    assert found[0].load() is plugin


@pytest.mark.parametrize("tree", TREES)
def test_contribute_names_the_tree_modules(tree: str) -> None:
    """Each supported version key contributes that tree's CLI and MCP modules."""
    contribution = plugin.contribute(tree)
    assert isinstance(contribution, Contribution)
    assert contribution.name == "security"
    assert contribution.cli_module == f"dhis2w_security.{tree}.cli"
    assert contribution.mcp_module == f"dhis2w_security.{tree}.mcp"


def test_unknown_tree_falls_back_to_v43() -> None:
    """An unrecognised version key binds to the canonical v43 tree."""
    contribution = plugin.contribute("v99")
    assert contribution.cli_module == "dhis2w_security.v43.cli"
    assert contribution.mcp_module == "dhis2w_security.v43.mcp"


@pytest.mark.parametrize("tree", TREES)
def test_plugin_host_collects_the_pack(tree: str) -> None:
    """The host collects the pack's contribution off its entry point, for every tree."""
    host = load_plugin_host(tree)
    contributions = [c for c in host.contributions if c.cli_module == f"dhis2w_security.{tree}.cli"]
    assert len(contributions) == 1
    assert not [failure for failure in host.failures if "security" in failure.name]
