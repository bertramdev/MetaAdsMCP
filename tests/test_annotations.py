"""Tests that every registered MCP tool has correct ToolAnnotations."""

from __future__ import annotations

import pytest

from meta_ads_mcp.server import mcp
from meta_ads_mcp.tools import CREATE, DESTRUCTIVE, READ_ONLY, UPDATE

# ── Expected annotation mapping (tool name → annotation constant) ──────────

EXPECTED: dict[str, object] = {
    # accounts.py
    "get_ad_accounts": READ_ONLY,
    "get_account_info": READ_ONLY,
    # campaigns.py
    "list_campaigns": READ_ONLY,
    "get_campaign": READ_ONLY,
    "create_campaign": CREATE,
    "update_campaign": UPDATE,
    "get_campaign_diagnostics": READ_ONLY,
    # adsets.py
    "list_ad_sets": READ_ONLY,
    "get_ad_set": READ_ONLY,
    "create_ad_set": CREATE,
    "update_ad_set": UPDATE,
    "get_ad_set_diagnostics": READ_ONLY,
    # ads.py
    "list_ads": READ_ONLY,
    "get_ad": READ_ONLY,
    "create_ad": CREATE,
    "update_ad_status": DESTRUCTIVE,
    "get_ad_diagnostics": READ_ONLY,
    # insights.py
    "get_insights": READ_ONLY,
    "get_account_insights": READ_ONLY,
    "get_campaign_insights": READ_ONLY,
    "compare_performance": READ_ONLY,
    "get_breakdown_report": READ_ONLY,
    # creatives.py
    "list_creatives": READ_ONLY,
    "get_creative": READ_ONLY,
    "create_ad_creative": CREATE,
    "update_ad_creative": UPDATE,
    # audiences.py
    "list_audiences": READ_ONLY,
    "get_audience": READ_ONLY,
    "create_custom_audience": CREATE,
    "create_lookalike_audience": CREATE,
}


def _get_tools() -> dict:
    """Return the registered tool map from FastMCP."""
    return mcp._tool_manager._tools


# ── Structural tests ───────────────────────────────────────────────────────


class TestAllToolsAnnotated:
    """Ensure every registered tool has annotations and is covered by the mapping."""

    def test_every_tool_has_annotations(self):
        for name, tool in _get_tools().items():
            assert tool.annotations is not None, f"Tool '{name}' is missing annotations"

    def test_no_unmapped_tools(self):
        registered = set(_get_tools().keys())
        mapped = set(EXPECTED.keys())
        unmapped = registered - mapped
        assert not unmapped, f"Tools registered but not in EXPECTED mapping: {unmapped}"

    def test_no_stale_mapping_entries(self):
        registered = set(_get_tools().keys())
        mapped = set(EXPECTED.keys())
        stale = mapped - registered
        assert not stale, f"EXPECTED has entries for non-existent tools: {stale}"

    def test_tool_count(self):
        assert len(_get_tools()) == 30, f"Expected 30 tools, found {len(_get_tools())}"


# ── Per-tool annotation correctness ───────────────────────────────────────


@pytest.mark.parametrize("tool_name,expected_ann", list(EXPECTED.items()))
def test_tool_annotation_matches(tool_name, expected_ann):
    tools = _get_tools()
    assert tool_name in tools, f"Tool '{tool_name}' not registered"
    actual = tools[tool_name].annotations
    assert actual == expected_ann, (
        f"Tool '{tool_name}' annotation mismatch:\n"
        f"  expected: {expected_ann}\n"
        f"  actual:   {actual}"
    )


# ── Category-level invariant tests ────────────────────────────────────────


class TestReadOnlyTools:
    """Read-only tools must have readOnlyHint=True."""

    @pytest.fixture
    def read_tools(self):
        return {n: _get_tools()[n] for n, a in EXPECTED.items() if a is READ_ONLY}

    def test_read_only_hint(self, read_tools):
        for name, tool in read_tools.items():
            assert (
                tool.annotations.readOnlyHint is True
            ), f"'{name}' should be readOnlyHint=True"


class TestCreateTools:
    """Create tools must not be destructive and must not be idempotent."""

    @pytest.fixture
    def create_tools(self):
        return {n: _get_tools()[n] for n, a in EXPECTED.items() if a is CREATE}

    def test_not_destructive(self, create_tools):
        for name, tool in create_tools.items():
            assert (
                tool.annotations.destructiveHint is False
            ), f"'{name}' should be destructiveHint=False"

    def test_not_idempotent(self, create_tools):
        for name, tool in create_tools.items():
            assert (
                tool.annotations.idempotentHint is False
            ), f"'{name}' should be idempotentHint=False"


class TestUpdateTools:
    """Update tools must be idempotent and not destructive."""

    @pytest.fixture
    def update_tools(self):
        return {n: _get_tools()[n] for n, a in EXPECTED.items() if a is UPDATE}

    def test_not_destructive(self, update_tools):
        for name, tool in update_tools.items():
            assert (
                tool.annotations.destructiveHint is False
            ), f"'{name}' should be destructiveHint=False"

    def test_idempotent(self, update_tools):
        for name, tool in update_tools.items():
            assert (
                tool.annotations.idempotentHint is True
            ), f"'{name}' should be idempotentHint=True"


class TestDestructiveTools:
    """Destructive tools must have destructiveHint=True."""

    @pytest.fixture
    def destructive_tools(self):
        return {n: _get_tools()[n] for n, a in EXPECTED.items() if a is DESTRUCTIVE}

    def test_destructive_hint(self, destructive_tools):
        for name, tool in destructive_tools.items():
            assert (
                tool.annotations.destructiveHint is True
            ), f"'{name}' should be destructiveHint=True"

    def test_idempotent(self, destructive_tools):
        for name, tool in destructive_tools.items():
            assert (
                tool.annotations.idempotentHint is True
            ), f"'{name}' should be idempotentHint=True"
