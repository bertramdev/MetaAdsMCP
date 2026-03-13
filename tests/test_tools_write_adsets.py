"""Tests for ad set write tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.adsets import create_ad_set, update_ad_set


class TestCreateAdSet:
    """Tests for create_ad_set tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates ad set and returns formatted result."""
        mock_client.create_ad_set.return_value = {"id": "adset_new"}

        result = await create_ad_set(
            mock_context,
            name="Test Ad Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            daily_budget="50.00",
        )

        assert "Ad Set Created" in result
        assert "PAUSED" in result
        assert "Test Ad Set" in result

        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["targeting"] == {"geo_locations": {"countries": ["US"]}}
        assert call_kwargs["daily_budget"] == 5000

    @pytest.mark.asyncio
    async def test_targeting_json_parsed(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Targeting JSON string is parsed to dict."""
        mock_client.create_ad_set.return_value = {"id": "adset_new"}

        await create_ad_set(
            mock_context,
            name="Targeted Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"age_min": 25, "age_max": 55, "genders": [1]}',
        )

        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["targeting"]["age_min"] == 25
        assert call_kwargs["targeting"]["genders"] == [1]

    @pytest.mark.asyncio
    async def test_budget_conversion(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Budgets and bid amounts are converted to cents."""
        mock_client.create_ad_set.return_value = {"id": "adset_new"}

        await create_ad_set(
            mock_context,
            name="Budget Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            daily_budget="75.50",
            bid_amount="1.25",
        )

        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["daily_budget"] == 7550
        assert call_kwargs["bid_amount"] == 125

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_ad_set.return_value = {"id": ""}

        result = await create_ad_set(
            mock_context,
            name="Dry Run Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_invalid_targeting_json(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid targeting JSON returns error."""
        result = await create_ad_set(
            mock_context,
            name="Bad Targeting",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting="not valid json",
        )

        assert "## Error" in result
        assert "Invalid JSON" in result
        mock_client.create_ad_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_promoted_object_parsed(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Promoted object JSON string is parsed."""
        mock_client.create_ad_set.return_value = {"id": "adset_new"}

        await create_ad_set(
            mock_context,
            name="Page Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            promoted_object='{"page_id": "12345"}',
        )

        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["promoted_object"] == {"page_id": "12345"}

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.create_ad_set.side_effect = MetaAdsError("Invalid targeting")

        result = await create_ad_set(
            mock_context,
            name="Fail",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
        )

        assert "## Error" in result
        assert "Invalid targeting" in result


class TestUpdateAdSet:
    """Tests for update_ad_set tool."""

    @pytest.mark.asyncio
    async def test_targeting_change(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Targeting update shows change in result."""
        mock_client.get_ad_set.return_value = {
            "id": "adset_1",
            "name": "My Ad Set",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "campaign_id": "camp_1",
            "daily_budget": "5000",
            "optimization_goal": "LINK_CLICKS",
            "targeting": {"geo_locations": {"countries": ["US"]}},
        }
        mock_client.update_ad_set.return_value = {}

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            targeting='{"geo_locations": {"countries": ["US", "CA"]}}',
        )

        assert "Ad Set Updated" in result
        assert "Targeting" in result

        call_kwargs = mock_client.update_ad_set.call_args.kwargs
        assert call_kwargs["targeting"]["geo_locations"]["countries"] == [
            "US",
            "CA",
        ]

    @pytest.mark.asyncio
    async def test_budget_before_after(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Budget changes show dollar-formatted before/after."""
        mock_client.get_ad_set.return_value = {
            "id": "adset_1",
            "name": "My Ad Set",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "campaign_id": "camp_1",
            "daily_budget": "5000",
            "optimization_goal": "LINK_CLICKS",
        }
        mock_client.update_ad_set.return_value = {}

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            daily_budget="100.00",
        )

        assert "$50.00" in result
        assert "$100.00" in result

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.get_ad_set.return_value = {
            "id": "adset_1",
            "name": "My Ad Set",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "campaign_id": "camp_1",
            "daily_budget": "5000",
            "optimization_goal": "LINK_CLICKS",
        }
        mock_client.update_ad_set.return_value = {}

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            name="Updated",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.update_ad_set.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_status_validation(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid status returns error without calling API."""
        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            status="DELETED",
        )

        assert "## Error" in result
        assert "Invalid status" in result
        mock_client.update_ad_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_targeting_json(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid targeting JSON returns error."""
        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            targeting="bad json",
        )

        assert "## Error" in result
        assert "Invalid JSON" in result
        mock_client.update_ad_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.get_ad_set.return_value = {
            "id": "adset_1",
            "name": "My Ad Set",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "campaign_id": "camp_1",
            "daily_budget": "5000",
            "optimization_goal": "LINK_CLICKS",
        }
        mock_client.update_ad_set.side_effect = MetaAdsError("Ad set not found")

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            name="Fail",
        )

        assert "## Error" in result
        assert "Ad set not found" in result
