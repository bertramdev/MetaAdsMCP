"""Tests for creative tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.creatives import get_creative, list_creatives


class TestListCreatives:
    """Tests for list_creatives tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted creative list."""
        mock_client.get_creatives.return_value = [
            {
                "id": "cr_1",
                "name": "Banner Ad",
                "title": "Shop Now",
                "call_to_action_type": "SHOP_NOW",
                "link_url": "https://example.com",
            },
        ]

        result = await list_creatives(mock_context)

        assert "## Ad Creatives" in result
        assert "Banner Ad" in result
        assert "SHOP_NOW" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no creatives."""
        mock_client.get_creatives.return_value = []

        result = await list_creatives(mock_context)

        assert "No creatives found" in result

    @pytest.mark.asyncio
    async def test_params(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes parameters to client."""
        mock_client.get_creatives.return_value = []

        await list_creatives(mock_context, account_id="act_123", limit=10)

        mock_client.get_creatives.assert_called_once_with(
            account_id="act_123", limit=10
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_creatives.side_effect = MetaAdsError("Access denied")

        result = await list_creatives(mock_context)

        assert "## Error" in result
        assert "Access denied" in result


class TestGetCreative:
    """Tests for get_creative tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted creative detail."""
        mock_client.get_creative.return_value = {
            "id": "cr_123",
            "name": "Hero Creative",
            "title": "Big Sale",
            "body": "Up to 50% off",
            "call_to_action_type": "LEARN_MORE",
            "link_url": "https://example.com/sale",
            "image_url": "https://example.com/img.jpg",
            "thumbnail_url": "https://example.com/thumb.jpg",
        }

        result = await get_creative(mock_context, creative_id="cr_123")

        assert "## Creative: Hero Creative" in result
        assert "Big Sale" in result
        assert "Up to 50% off" in result
        assert "LEARN_MORE" in result
        mock_client.get_creative.assert_called_once_with("cr_123")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_creative.side_effect = MetaAdsError("Creative not found")

        result = await get_creative(mock_context, creative_id="cr_bad")

        assert "## Error" in result
        assert "Creative not found" in result
