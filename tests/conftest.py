"""Shared test fixtures for tool tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsClient


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock MetaAdsClient with all async methods."""
    return AsyncMock(spec=MetaAdsClient)


@pytest.fixture
def mock_context(mock_client: AsyncMock) -> MagicMock:
    """Create a mock MCP Context with the mock client wired in."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context.client = mock_client
    return ctx
