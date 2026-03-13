"""Tests for campaign write tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.campaigns import create_campaign, update_campaign


class TestCreateCampaign:
    """Tests for create_campaign tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates campaign and returns formatted result."""
        mock_client.create_campaign.return_value = {"id": "camp_new"}

        result = await create_campaign(
            mock_context,
            name="Spring Sale",
            objective="OUTCOME_TRAFFIC",
            daily_budget="50.00",
        )

        assert "Campaign Created" in result
        assert "PAUSED" in result
        assert "Spring Sale" in result
        assert "$50.00" in result
        mock_client.create_campaign.assert_called_once_with(
            name="Spring Sale",
            objective="OUTCOME_TRAFFIC",
            account_id=None,
            daily_budget=5000,
            lifetime_budget=None,
            special_ad_categories=None,
            start_time=None,
            stop_time=None,
            bid_strategy=None,
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_campaign.return_value = {"id": ""}

        result = await create_campaign(
            mock_context,
            name="Test",
            objective="OUTCOME_TRAFFIC",
            dry_run=True,
        )

        assert "Dry run" in result
        mock_client.create_campaign.assert_called_once()
        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_budget_conversion(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Budgets are converted from dollars to cents."""
        mock_client.create_campaign.return_value = {"id": "camp_new"}

        await create_campaign(
            mock_context,
            name="Budget Test",
            objective="OUTCOME_SALES",
            daily_budget="75.50",
            lifetime_budget="1000.00",
        )

        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["daily_budget"] == 7550
        assert call_kwargs["lifetime_budget"] == 100000

    @pytest.mark.asyncio
    async def test_special_ad_categories_parsed(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Comma-separated categories are parsed to list."""
        mock_client.create_campaign.return_value = {"id": "camp_new"}

        await create_campaign(
            mock_context,
            name="Housing Campaign",
            objective="OUTCOME_LEADS",
            special_ad_categories="HOUSING, EMPLOYMENT",
        )

        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["special_ad_categories"] == [
            "HOUSING",
            "EMPLOYMENT",
        ]

    @pytest.mark.asyncio
    async def test_special_ad_categories_default(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Default None is passed when no categories specified."""
        mock_client.create_campaign.return_value = {"id": "camp_new"}

        await create_campaign(
            mock_context,
            name="Normal Campaign",
            objective="OUTCOME_TRAFFIC",
        )

        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["special_ad_categories"] is None

    @pytest.mark.asyncio
    async def test_invalid_budget_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid budget returns error."""
        result = await create_campaign(
            mock_context,
            name="Bad Budget",
            objective="OUTCOME_TRAFFIC",
            daily_budget="not_a_number",
        )

        assert "## Error" in result
        assert "Invalid dollar amount" in result
        mock_client.create_campaign.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.create_campaign.side_effect = MetaAdsError("Permission denied")

        result = await create_campaign(
            mock_context,
            name="Fail",
            objective="OUTCOME_TRAFFIC",
        )

        assert "## Error" in result
        assert "Permission denied" in result


class TestUpdateCampaign:
    """Tests for update_campaign tool."""

    @pytest.mark.asyncio
    async def test_name_change(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Name change shows before/after."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "Old Name",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            name="New Name",
        )

        assert "Campaign Updated" in result
        assert "Old Name" in result
        assert "New Name" in result

    @pytest.mark.asyncio
    async def test_budget_before_after(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Budget changes show dollar-formatted before/after."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            daily_budget="75.00",
        )

        assert "$50.00" in result
        assert "$75.00" in result

        call_kwargs = mock_client.update_campaign.call_args.kwargs
        assert call_kwargs["daily_budget"] == 7500

    @pytest.mark.asyncio
    async def test_status_change(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Status change shows before/after."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            status="PAUSED",
        )

        assert "ACTIVE" in result
        assert "PAUSED" in result

    @pytest.mark.asyncio
    async def test_status_validation(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid status returns error without calling API."""
        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            status="DELETED",
        )

        assert "## Error" in result
        assert "Invalid status" in result
        mock_client.update_campaign.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            name="Updated",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.update_campaign.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.side_effect = MetaAdsError("Campaign not found")

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            name="Fail",
        )

        assert "## Error" in result
        assert "Campaign not found" in result
