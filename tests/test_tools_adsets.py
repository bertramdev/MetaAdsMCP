"""Tests for ad set tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.adsets import get_ad_set, list_ad_sets


class TestListAdSets:
    """Tests for list_ad_sets tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted ad set list."""
        mock_client.get_ad_sets.return_value = [
            {
                "id": "adset_1",
                "name": "US Targeting",
                "status": "ACTIVE",
                "effective_status": "ACTIVE",
                "campaign_id": "camp_1",
                "daily_budget": "2500",
                "optimization_goal": "LINK_CLICKS",
            },
        ]

        result = await list_ad_sets(mock_context)

        assert "## Ad Sets" in result
        assert "US Targeting" in result
        assert "LINK_CLICKS" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no ad sets."""
        mock_client.get_ad_sets.return_value = []

        result = await list_ad_sets(mock_context)

        assert "No ad sets found" in result

    @pytest.mark.asyncio
    async def test_campaign_filter(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes campaign_id and status filter to client."""
        mock_client.get_ad_sets.return_value = []

        await list_ad_sets(
            mock_context, campaign_id="camp_1", status="PAUSED", limit=25
        )

        mock_client.get_ad_sets.assert_called_once_with(
            account_id=None,
            campaign_id="camp_1",
            status_filter=["PAUSED"],
            limit=25,
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_sets.side_effect = MetaAdsError("Rate limit reached")

        result = await list_ad_sets(mock_context)

        assert "## Error" in result
        assert "Rate limit reached" in result


class TestGetAdSet:
    """Tests for get_ad_set tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted ad set detail."""
        mock_client.get_ad_set.return_value = {
            "id": "adset_123",
            "name": "Age 25-34",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "campaign_id": "camp_456",
            "daily_budget": "3000",
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "REACH",
            "targeting": {"geo_locations": {"countries": ["US", "CA"]}},
        }

        result = await get_ad_set(mock_context, ad_set_id="adset_123")

        assert "## Ad Set: Age 25-34" in result
        assert "camp_456" in result
        assert "$30.00" in result
        assert "REACH" in result
        mock_client.get_ad_set.assert_called_once_with("adset_123")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_set.side_effect = MetaAdsError("Ad set not found")

        result = await get_ad_set(mock_context, ad_set_id="adset_bad")

        assert "## Error" in result
        assert "Ad set not found" in result
