"""Tests for Advantage+, budget scheduling, frequency capping, and attribution."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.tools._write_helpers import parse_json_list_param
from meta_ads_mcp.tools.adsets import create_ad_set, update_ad_set
from meta_ads_mcp.tools.campaigns import create_campaign, update_campaign


class TestParseJsonListParam:
    """Tests for parse_json_list_param."""

    def test_valid_json_list(self) -> None:
        """Parses valid JSON array of objects."""
        result = parse_json_list_param(
            '[{"event": "IMPRESSIONS", "interval_days": 7}]',
            "frequency_control_specs",
        )
        assert result == [{"event": "IMPRESSIONS", "interval_days": 7}]

    def test_invalid_json_raises(self) -> None:
        """Invalid JSON string raises ValueError."""
        with pytest.raises(
            ValueError, match="Invalid JSON for frequency_control_specs"
        ):
            parse_json_list_param("not json", "frequency_control_specs")

    def test_non_list_type_raises(self) -> None:
        """Non-list JSON raises ValueError."""
        with pytest.raises(ValueError, match="must be a JSON array"):
            parse_json_list_param('{"key": "value"}', "frequency_control_specs")


class TestCreateCampaignAdvantage:
    """Tests for Advantage+ and budget scheduling in create_campaign."""

    @pytest.mark.asyncio
    async def test_smart_promotion_type(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Smart promotion type is passed to client."""
        mock_client.create_campaign.return_value = {"id": "camp_adv"}

        result = await create_campaign(
            mock_context,
            name="Advantage+ Campaign",
            objective="OUTCOME_SALES",
            smart_promotion_type="GUIDED_CREATION",
        )

        assert "Campaign Created" in result
        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["smart_promotion_type"] == "GUIDED_CREATION"

    @pytest.mark.asyncio
    async def test_spend_cap_dollars_to_cents(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Spend cap is converted from dollars to cents."""
        mock_client.create_campaign.return_value = {"id": "camp_cap"}

        await create_campaign(
            mock_context,
            name="Cap Campaign",
            objective="OUTCOME_TRAFFIC",
            spend_cap="500.00",
        )

        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["spend_cap"] == 50000

    @pytest.mark.asyncio
    async def test_budget_schedule_specs(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Budget schedule specs JSON string is parsed to list."""
        mock_client.create_campaign.return_value = {"id": "camp_sched"}
        schedule_json = (
            '[{"time_start": "2025-01-01",'
            ' "time_stop": "2025-01-31",'
            ' "budget_value": "1000"}]'
        )

        await create_campaign(
            mock_context,
            name="Scheduled Campaign",
            objective="OUTCOME_TRAFFIC",
            budget_schedule_specs=schedule_json,
        )

        call_kwargs = mock_client.create_campaign.call_args.kwargs
        assert call_kwargs["budget_schedule_specs"] == [
            {
                "time_start": "2025-01-01",
                "time_stop": "2025-01-31",
                "budget_value": "1000",
            }
        ]


class TestUpdateCampaignAdvantage:
    """Tests for Advantage+ and budget scheduling in update_campaign."""

    @pytest.mark.asyncio
    async def test_spend_cap_changes_displayed(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Spend cap change shows before/after in result."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
            "spend_cap": "100000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            spend_cap="2000.00",
        )

        assert "Campaign Updated" in result
        assert "$1,000.00" in result
        assert "$2,000.00" in result

        call_kwargs = mock_client.update_campaign.call_args.kwargs
        assert call_kwargs["spend_cap"] == 200000

    @pytest.mark.asyncio
    async def test_smart_promotion_type(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Smart promotion type change shows in result."""
        mock_client.get_campaign.return_value = {
            "id": "camp_1",
            "name": "My Campaign",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_SALES",
            "daily_budget": "5000",
        }
        mock_client.update_campaign.return_value = {}

        result = await update_campaign(
            mock_context,
            campaign_id="camp_1",
            smart_promotion_type="GUIDED_CREATION",
        )

        assert "Campaign Updated" in result
        assert "GUIDED_CREATION" in result

        call_kwargs = mock_client.update_campaign.call_args.kwargs
        assert call_kwargs["smart_promotion_type"] == "GUIDED_CREATION"


class TestCreateAdSetFrequency:
    """Tests for frequency capping and attribution in create_ad_set."""

    @pytest.mark.asyncio
    async def test_frequency_control_specs(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Frequency control specs JSON string is parsed and passed."""
        mock_client.create_ad_set.return_value = {"id": "adset_freq"}
        freq_json = '[{"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}]'

        result = await create_ad_set(
            mock_context,
            name="Freq Ad Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            frequency_control_specs=freq_json,
        )

        assert "Ad Set Created" in result
        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["frequency_control_specs"] == [
            {"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}
        ]

    @pytest.mark.asyncio
    async def test_attribution_spec(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Attribution spec JSON string is parsed and passed."""
        mock_client.create_ad_set.return_value = {"id": "adset_attr"}
        attr_json = '[{"event_type": "CLICK_THROUGH", "window_days": 7}]'

        result = await create_ad_set(
            mock_context,
            name="Attr Ad Set",
            campaign_id="camp_1",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            attribution_spec=attr_json,
        )

        assert "Ad Set Created" in result
        call_kwargs = mock_client.create_ad_set.call_args.kwargs
        assert call_kwargs["attribution_spec"] == [
            {"event_type": "CLICK_THROUGH", "window_days": 7}
        ]


class TestUpdateAdSetFrequency:
    """Tests for frequency capping and attribution in update_ad_set."""

    @pytest.mark.asyncio
    async def test_frequency_control_specs_changes(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Frequency control specs change shows in result."""
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
        freq_json = '[{"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 5}]'

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            frequency_control_specs=freq_json,
        )

        assert "Ad Set Updated" in result
        assert "Frequency Control" in result

        call_kwargs = mock_client.update_ad_set.call_args.kwargs
        assert call_kwargs["frequency_control_specs"] == [
            {"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 5}
        ]

    @pytest.mark.asyncio
    async def test_attribution_spec_changes(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Attribution spec change shows in result."""
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
        attr_json = '[{"event_type": "CLICK_THROUGH", "window_days": 1}]'

        result = await update_ad_set(
            mock_context,
            ad_set_id="adset_1",
            attribution_spec=attr_json,
        )

        assert "Ad Set Updated" in result
        assert "Attribution Spec" in result

        call_kwargs = mock_client.update_ad_set.call_args.kwargs
        assert call_kwargs["attribution_spec"] == [
            {"event_type": "CLICK_THROUGH", "window_days": 1}
        ]
