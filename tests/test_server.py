"""Tests for server skeleton."""

from unittest.mock import MagicMock, patch

import pytest

from meta_ads_mcp.server import AppContext, app_lifespan, mcp


class TestAppContext:
    """Tests for AppContext."""

    def test_app_context_holds_client_and_config(self) -> None:
        """AppContext stores client and config."""
        mock_client = MagicMock()
        mock_config = MagicMock()
        ctx = AppContext(client=mock_client, config=mock_config)
        assert ctx.client is mock_client
        assert ctx.config is mock_config


class TestLifespan:
    """Tests for app_lifespan."""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_client(self) -> None:
        """Lifespan creates config and initializes client."""
        mock_config = MagicMock()
        mock_client = MagicMock()

        with (
            patch("meta_ads_mcp.server.MetaAdsConfig") as MockConfig,
            patch("meta_ads_mcp.server.MetaAdsClient") as MockClient,
        ):
            MockConfig.from_env.return_value = mock_config
            MockClient.return_value = mock_client

            mock_server = MagicMock()
            async with app_lifespan(mock_server) as ctx:
                assert isinstance(ctx, AppContext)
                assert ctx.config is mock_config
                assert ctx.client is mock_client
                mock_client.initialize.assert_called_once()


class TestMcpServer:
    """Tests for the MCP server instance."""

    def test_server_name(self) -> None:
        """Server has correct name."""
        assert mcp.name == "Meta Ads MCP"
