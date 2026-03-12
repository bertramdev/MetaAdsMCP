"""Tests for insight tools and helpers."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools._insights_helpers import (
    VALID_BREAKDOWNS,
    get_previous_range,
    resolve_date_preset,
)
from meta_ads_mcp.tools.insights import (
    compare_performance,
    get_account_insights,
    get_breakdown_report,
    get_campaign_insights,
    get_insights,
)

# --- Date helper tests ---


class TestResolveDatePreset:
    """Tests for resolve_date_preset."""

    def test_today(self) -> None:
        """today maps to today's date for both."""
        since, until = resolve_date_preset("today")
        today = date.today().isoformat()
        assert since == today
        assert until == today

    def test_yesterday(self) -> None:
        """yesterday maps to yesterday's date for both."""
        since, until = resolve_date_preset("yesterday")
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        assert since == yesterday
        assert until == yesterday

    def test_last_7d(self) -> None:
        """last_7d covers 7 days ending yesterday."""
        since, until = resolve_date_preset("last_7d")
        today = date.today()
        assert until == (today - timedelta(days=1)).isoformat()
        assert since == (today - timedelta(days=7)).isoformat()

    def test_last_30d(self) -> None:
        """last_30d covers 30 days ending yesterday."""
        since, until = resolve_date_preset("last_30d")
        today = date.today()
        assert until == (today - timedelta(days=1)).isoformat()
        assert since == (today - timedelta(days=30)).isoformat()

    def test_invalid_preset(self) -> None:
        """Unknown preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown date preset"):
            resolve_date_preset("last_999d")


class TestGetPreviousRange:
    """Tests for get_previous_range."""

    def test_week_range(self) -> None:
        """7-day range shifts back by 7 days."""
        prev_since, prev_until = get_previous_range("2026-03-08", "2026-03-14")
        assert prev_since == "2026-03-01"
        assert prev_until == "2026-03-07"

    def test_single_day(self) -> None:
        """Single day shifts back by 1 day."""
        prev_since, prev_until = get_previous_range("2026-03-10", "2026-03-10")
        assert prev_since == "2026-03-09"
        assert prev_until == "2026-03-09"

    def test_month_range(self) -> None:
        """30-day range shifts back by 30 days."""
        prev_since, prev_until = get_previous_range("2026-02-01", "2026-03-02")
        # Duration = 30 days, so previous ends day before start
        assert prev_until == "2026-01-31"


class TestValidBreakdowns:
    """Tests for VALID_BREAKDOWNS constant."""

    def test_contains_expected(self) -> None:
        """All expected breakdowns present."""
        assert "age" in VALID_BREAKDOWNS
        assert "gender" in VALID_BREAKDOWNS
        assert "country" in VALID_BREAKDOWNS
        assert "placement" in VALID_BREAKDOWNS
        assert "device_platform" in VALID_BREAKDOWNS
        assert "publisher_platform" in VALID_BREAKDOWNS


# --- Tool tests ---


class TestGetInsights:
    """Tests for get_insights tool."""

    @pytest.mark.asyncio
    async def test_success_with_preset(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted insights table."""
        mock_client.get_insights.return_value = [
            {
                "impressions": "10000",
                "clicks": "250",
                "spend": "75.50",
                "ctr": "2.5",
                "cpc": "0.302",
                "cpm": "7.55",
                "reach": "8000",
                "date_start": "2026-03-01",
                "date_stop": "2026-03-07",
            },
        ]

        result = await get_insights(mock_context, date_preset="last_7d")

        assert "## Performance Insights" in result
        assert "10,000" in result
        assert "$75.50" in result

    @pytest.mark.asyncio
    async def test_success_with_date_range(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Custom date range passes time_range to client."""
        mock_client.get_insights.return_value = []

        await get_insights(mock_context, start_date="2026-03-01", end_date="2026-03-07")

        call_kwargs = mock_client.get_insights.call_args.kwargs
        assert call_kwargs["time_range"] == {
            "since": "2026-03-01",
            "until": "2026-03-07",
        }
        assert call_kwargs["date_preset"] is None

    @pytest.mark.asyncio
    async def test_breakdowns_parsed(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Comma-separated breakdowns passed as list."""
        mock_client.get_insights.return_value = []

        await get_insights(mock_context, breakdowns="age,gender")

        call_kwargs = mock_client.get_insights.call_args.kwargs
        assert call_kwargs["breakdowns"] == ["age", "gender"]

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no data."""
        mock_client.get_insights.return_value = []

        result = await get_insights(mock_context)

        assert "No insights data found" in result

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_insights.side_effect = MetaAdsError("Rate limit")

        result = await get_insights(mock_context)

        assert "## Error" in result
        assert "Rate limit" in result


class TestGetAccountInsights:
    """Tests for get_account_insights tool."""

    @pytest.mark.asyncio
    async def test_delegates_to_get_insights(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Calls get_insights with account level."""
        mock_client.get_insights.return_value = [
            {
                "impressions": "5000",
                "clicks": "100",
                "spend": "30.00",
                "ctr": "2.0",
                "cpc": "0.30",
                "cpm": "6.00",
                "reach": "4000",
                "date_start": "2026-02-10",
                "date_stop": "2026-03-11",
            },
        ]

        result = await get_account_insights(mock_context, date_preset="last_30d")

        assert "## Performance Insights" in result
        call_kwargs = mock_client.get_insights.call_args.kwargs
        assert call_kwargs["level"] == "account"


class TestGetCampaignInsights:
    """Tests for get_campaign_insights tool."""

    @pytest.mark.asyncio
    async def test_single_period(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns insights for single period."""
        mock_client.get_insights.return_value = [
            {
                "campaign_id": "camp_1",
                "campaign_name": "Spring Sale",
                "impressions": "10000",
                "clicks": "500",
                "spend": "100.00",
                "ctr": "5.0",
                "cpc": "0.20",
                "cpm": "10.00",
                "reach": "8000",
                "date_start": "2026-02-10",
                "date_stop": "2026-03-11",
            },
        ]

        result = await get_campaign_insights(
            mock_context, campaign_id="camp_1", date_preset="last_30d"
        )

        assert "Campaign camp_1 Insights" in result
        assert "Spring Sale" in result

    @pytest.mark.asyncio
    async def test_no_data(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns message when campaign has no data."""
        mock_client.get_insights.return_value = []

        result = await get_campaign_insights(mock_context, campaign_id="camp_999")

        assert "No insights found" in result

    @pytest.mark.asyncio
    async def test_comparison(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Compare mode makes two API calls and returns comparison."""
        mock_client.get_insights.side_effect = [
            # Current period
            [
                {
                    "campaign_id": "camp_1",
                    "impressions": "10000",
                    "clicks": "500",
                    "spend": "100.00",
                    "ctr": "5.0",
                    "cpc": "0.20",
                    "cpm": "10.00",
                    "reach": "8000",
                    "date_start": "2026-02-10",
                    "date_stop": "2026-03-11",
                },
            ],
            # Previous period
            [
                {
                    "campaign_id": "camp_1",
                    "impressions": "8000",
                    "clicks": "300",
                    "spend": "80.00",
                    "ctr": "3.75",
                    "cpc": "0.267",
                    "cpm": "10.00",
                    "reach": "6000",
                    "date_start": "2026-01-11",
                    "date_stop": "2026-02-09",
                },
            ],
        ]

        result = await get_campaign_insights(
            mock_context,
            campaign_id="camp_1",
            date_preset="last_30d",
            compare=True,
        )

        assert "## Period Comparison" in result
        assert "Impressions" in result
        assert mock_client.get_insights.call_count == 2

    @pytest.mark.asyncio
    async def test_comparison_no_previous(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Comparison with no previous data still produces output."""
        mock_client.get_insights.side_effect = [
            [
                {
                    "campaign_id": "camp_1",
                    "impressions": "10000",
                    "clicks": "500",
                    "spend": "100.00",
                    "ctr": "5.0",
                    "cpc": "0.20",
                    "cpm": "10.00",
                    "reach": "8000",
                    "date_start": "2026-02-10",
                    "date_stop": "2026-03-11",
                },
            ],
            [],  # No previous data
        ]

        result = await get_campaign_insights(
            mock_context, campaign_id="camp_1", compare=True
        )

        assert "## Period Comparison" in result

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_insights.side_effect = MetaAdsError("Server error")

        result = await get_campaign_insights(mock_context, campaign_id="camp_1")

        assert "## Error" in result


class TestComparePerformance:
    """Tests for compare_performance tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns comparison table for multiple entities."""
        mock_client.get_insights.return_value = [
            {
                "campaign_id": "camp_1",
                "campaign_name": "Spring Sale",
                "impressions": "10000",
                "clicks": "500",
                "spend": "100.00",
                "ctr": "5.0",
                "cpc": "0.20",
                "cpm": "10.00",
                "reach": "8000",
            },
            {
                "campaign_id": "camp_2",
                "campaign_name": "Summer Push",
                "impressions": "8000",
                "clicks": "200",
                "spend": "80.00",
                "ctr": "2.5",
                "cpc": "0.40",
                "cpm": "10.00",
                "reach": "6000",
            },
        ]

        result = await compare_performance(mock_context, entity_ids="camp_1,camp_2")

        assert "## Campaign Performance Comparison" in result
        assert "Spring Sale" in result
        assert "Summer Push" in result

    @pytest.mark.asyncio
    async def test_no_data(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns message when no matching entities."""
        mock_client.get_insights.return_value = []

        result = await compare_performance(mock_context, entity_ids="camp_999")

        assert "No insights found" in result

    @pytest.mark.asyncio
    async def test_invalid_entity_type(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error for invalid entity type."""
        result = await compare_performance(
            mock_context, entity_ids="123", entity_type="invalid"
        )

        assert "## Error" in result
        assert "Invalid entity_type" in result

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_insights.side_effect = MetaAdsError("Timeout")

        result = await compare_performance(mock_context, entity_ids="camp_1")

        assert "## Error" in result


class TestGetBreakdownReport:
    """Tests for get_breakdown_report tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns breakdown table."""
        mock_client.get_insights.return_value = [
            {
                "age": "25-34",
                "impressions": "5000",
                "clicks": "200",
                "spend": "40.00",
                "ctr": "4.0",
                "cpc": "0.20",
                "cpm": "8.00",
                "reach": "4000",
                "date_start": "2026-02-10",
                "date_stop": "2026-03-11",
            },
            {
                "age": "35-44",
                "impressions": "3000",
                "clicks": "100",
                "spend": "30.00",
                "ctr": "3.33",
                "cpc": "0.30",
                "cpm": "10.00",
                "reach": "2500",
                "date_start": "2026-02-10",
                "date_stop": "2026-03-11",
            },
        ]

        result = await get_breakdown_report(mock_context, breakdown="age")

        assert "Breakdown by Age" in result
        assert "25-34" in result
        assert "35-44" in result

    @pytest.mark.asyncio
    async def test_invalid_breakdown(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error for invalid breakdown."""
        result = await get_breakdown_report(mock_context, breakdown="invalid_field")

        assert "## Error" in result
        assert "Invalid breakdown" in result

    @pytest.mark.asyncio
    async def test_passes_params(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes all parameters to client."""
        mock_client.get_insights.return_value = []

        await get_breakdown_report(
            mock_context,
            breakdown="gender",
            account_id="act_123",
            date_preset="last_7d",
            level="campaign",
            limit=10,
        )

        mock_client.get_insights.assert_called_once_with(
            account_id="act_123",
            date_preset="last_7d",
            level="campaign",
            breakdowns=["gender"],
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_insights.side_effect = MetaAdsError("API error")

        result = await get_breakdown_report(mock_context, breakdown="age")

        assert "## Error" in result
