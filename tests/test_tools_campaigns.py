"""Tests for campaign tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.campaigns import get_campaign, list_campaigns


class TestListCampaigns:
    """Tests for list_campaigns tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted campaign list."""
        mock_client.get_campaigns.return_value = [
            {
                "id": "camp_1",
                "name": "Spring Sale",
                "status": "ACTIVE",
                "effective_status": "ACTIVE",
                "objective": "OUTCOME_TRAFFIC",
                "daily_budget": "5000",
            },
        ]

        result = await list_campaigns(mock_context)

        assert "## Campaigns" in result
        assert "Spring Sale" in result
        assert "OUTCOME_TRAFFIC" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no campaigns."""
        mock_client.get_campaigns.return_value = []

        result = await list_campaigns(mock_context)

        assert "No campaigns found" in result

    @pytest.mark.asyncio
    async def test_status_filter(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes status filter to client."""
        mock_client.get_campaigns.return_value = []

        await list_campaigns(mock_context, status="ACTIVE", limit=10)

        mock_client.get_campaigns.assert_called_once_with(
            account_id=None, status_filter=["ACTIVE"], limit=10
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_campaigns.side_effect = MetaAdsError("Permission denied")

        result = await list_campaigns(mock_context)

        assert "## Error" in result
        assert "Permission denied" in result


class TestGetCampaign:
    """Tests for get_campaign tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted campaign detail."""
        mock_client.get_campaign.return_value = {
            "id": "camp_123",
            "name": "Summer Push",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_SALES",
            "daily_budget": "10000",
            "start_time": "2026-03-01T00:00:00",
        }

        result = await get_campaign(mock_context, campaign_id="camp_123")

        assert "## Campaign: Summer Push" in result
        assert "OUTCOME_SALES" in result
        assert "$100.00" in result
        mock_client.get_campaign.assert_called_once_with("camp_123")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_campaign.side_effect = MetaAdsError("Campaign not found")

        result = await get_campaign(mock_context, campaign_id="camp_bad")

        assert "## Error" in result
        assert "Campaign not found" in result
