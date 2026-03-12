"""Tests for ad tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.ads import get_ad, list_ads


class TestListAds:
    """Tests for list_ads tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted ad list."""
        mock_client.get_ads.return_value = [
            {
                "id": "ad_1",
                "name": "Ad Variant A",
                "status": "ACTIVE",
                "effective_status": "ACTIVE",
                "adset_id": "adset_1",
                "campaign_id": "camp_1",
                "creative": {"id": "cr_1"},
            },
        ]

        result = await list_ads(mock_context)

        assert "## Ads" in result
        assert "Ad Variant A" in result
        assert "cr_1" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no ads."""
        mock_client.get_ads.return_value = []

        result = await list_ads(mock_context)

        assert "No ads found" in result

    @pytest.mark.asyncio
    async def test_filters(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes all filters to client."""
        mock_client.get_ads.return_value = []

        await list_ads(
            mock_context,
            ad_set_id="adset_1",
            campaign_id="camp_1",
            status="ACTIVE",
            limit=20,
        )

        mock_client.get_ads.assert_called_once_with(
            account_id=None,
            ad_set_id="adset_1",
            campaign_id="camp_1",
            status_filter=["ACTIVE"],
            limit=20,
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ads.side_effect = MetaAdsError("API error")

        result = await list_ads(mock_context)

        assert "## Error" in result
        assert "API error" in result


class TestGetAd:
    """Tests for get_ad tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted ad detail."""
        mock_client.get_ad.return_value = {
            "id": "ad_123",
            "name": "Hero Image Ad",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "adset_id": "adset_456",
            "campaign_id": "camp_789",
            "creative": {"id": "cr_111"},
            "created_time": "2026-03-01T00:00:00",
        }

        result = await get_ad(mock_context, ad_id="ad_123")

        assert "## Ad: Hero Image Ad" in result
        assert "cr_111" in result
        assert "adset_456" in result
        mock_client.get_ad.assert_called_once_with("ad_123")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad.side_effect = MetaAdsError("Ad not found")

        result = await get_ad(mock_context, ad_id="ad_bad")

        assert "## Error" in result
        assert "Ad not found" in result
