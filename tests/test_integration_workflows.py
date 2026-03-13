"""Mocked multi-step workflow tests.

These tests verify that tools compose correctly in realistic sequences
without hitting the real Meta API.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestCampaignCreationWorkflow:
    """Create -> get -> update -> insights workflow."""

    @pytest.mark.asyncio
    async def test_create_then_get(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Created campaign can be retrieved."""
        from meta_ads_mcp.tools.campaigns import create_campaign, get_campaign

        mock_client.create_campaign.return_value = {"id": "camp_new"}
        result = await create_campaign(
            mock_context, name="Test Campaign", objective="OUTCOME_TRAFFIC"
        )
        assert "Created" in result
        assert "PAUSED" in result

        mock_client.get_campaign.return_value = {
            "id": "camp_new",
            "name": "Test Campaign",
            "status": "PAUSED",
            "objective": "OUTCOME_TRAFFIC",
        }
        result = await get_campaign(mock_context, campaign_id="camp_new")
        assert "Test Campaign" in result
        assert "PAUSED" in result

    @pytest.mark.asyncio
    async def test_create_then_update_status(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Created campaign can be activated via update."""
        from meta_ads_mcp.tools.campaigns import create_campaign, update_campaign

        mock_client.create_campaign.return_value = {"id": "camp_new"}
        await create_campaign(
            mock_context, name="Test Campaign", objective="OUTCOME_TRAFFIC"
        )

        mock_client.get_campaign.return_value = {
            "id": "camp_new",
            "name": "Test Campaign",
            "status": "PAUSED",
            "objective": "OUTCOME_TRAFFIC",
        }
        mock_client.update_campaign.return_value = {"success": True}
        result = await update_campaign(
            mock_context, campaign_id="camp_new", status="ACTIVE"
        )
        assert "Updated" in result
        assert "ACTIVE" in result

    @pytest.mark.asyncio
    async def test_create_then_insights(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Insights can be fetched for a created campaign."""
        from meta_ads_mcp.tools.campaigns import create_campaign
        from meta_ads_mcp.tools.insights import get_campaign_insights

        mock_client.create_campaign.return_value = {"id": "camp_new"}
        await create_campaign(mock_context, name="Test", objective="OUTCOME_TRAFFIC")

        mock_client.get_insights.return_value = [
            {
                "campaign_id": "camp_new",
                "campaign_name": "Test",
                "impressions": "5000",
                "clicks": "100",
                "spend": "25.00",
                "ctr": "2.0",
                "cpc": "0.25",
                "cpm": "5.00",
                "reach": "4000",
                "date_start": "2026-03-01",
                "date_stop": "2026-03-07",
            }
        ]
        result = await get_campaign_insights(
            mock_context, campaign_id="camp_new", date_preset="last_7d"
        )
        assert "5,000" in result


class TestFullFunnelSetup:
    """Campaign -> ad set -> creative -> ad workflow."""

    @pytest.mark.asyncio
    async def test_full_funnel(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Full funnel from campaign to ad can be created."""
        from meta_ads_mcp.tools.ads import create_ad
        from meta_ads_mcp.tools.adsets import create_ad_set
        from meta_ads_mcp.tools.campaigns import create_campaign
        from meta_ads_mcp.tools.creatives import create_ad_creative

        # 1. Create campaign
        mock_client.create_campaign.return_value = {"id": "camp_100"}
        result = await create_campaign(
            mock_context, name="Funnel Campaign", objective="OUTCOME_SALES"
        )
        assert "camp_100" in result

        # 2. Create ad set under campaign
        mock_client.create_ad_set.return_value = {"id": "adset_200"}
        result = await create_ad_set(
            mock_context,
            name="Funnel Ad Set",
            campaign_id="camp_100",
            billing_event="IMPRESSIONS",
            optimization_goal="CONVERSIONS",
            targeting='{"geo_locations": {"countries": ["US"]}}',
            daily_budget="50.00",
        )
        assert "adset_200" in result
        assert "PAUSED" in result

        # 3. Create creative
        mock_client.create_ad_creative.return_value = {"id": "cre_300"}
        result = await create_ad_creative(
            mock_context,
            name="Funnel Creative",
            page_id="page_1",
            link="https://example.com",
            headline="Buy Now",
        )
        assert "cre_300" in result

        # 4. Create ad linking ad set + creative
        mock_client.create_ad.return_value = {"id": "ad_400"}
        result = await create_ad(
            mock_context,
            name="Funnel Ad",
            adset_id="adset_200",
            creative_id="cre_300",
        )
        assert "ad_400" in result
        assert "PAUSED" in result


class TestDiagnosisWorkflow:
    """List -> diagnostics chain workflow."""

    @pytest.mark.asyncio
    async def test_list_then_diagnose_campaign(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """List campaigns then diagnose one with issues."""
        from meta_ads_mcp.tools.campaigns import (
            get_campaign_diagnostics,
            list_campaigns,
        )

        mock_client.get_campaigns.return_value = [
            {"id": "camp_1", "name": "Active Campaign", "status": "ACTIVE"},
        ]
        result = await list_campaigns(mock_context)
        assert "camp_1" in result

        mock_client.get_campaign_diagnostics.return_value = {
            "id": "camp_1",
            "name": "Active Campaign",
            "issues_info": [
                {"level": "warning", "summary": "Low budget may limit delivery"}
            ],
            "recommendations": [
                {"title": "Increase Budget", "message": "Consider raising daily budget"}
            ],
        }
        result = await get_campaign_diagnostics(mock_context, campaign_id="camp_1")
        assert "Low budget" in result
        assert "Increase Budget" in result

    @pytest.mark.asyncio
    async def test_diagnose_ad_set_with_learning(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Ad set diagnostics include learning stage info."""
        from meta_ads_mcp.tools.adsets import get_ad_set_diagnostics

        mock_client.get_ad_set_diagnostics.return_value = {
            "id": "adset_1",
            "name": "Test Ad Set",
            "issues_info": [],
            "recommendations": [],
            "learning_stage_info": {"status": "LEARNING_LIMITED"},
        }
        result = await get_ad_set_diagnostics(mock_context, ad_set_id="adset_1")
        assert "Learning Limited" in result

    @pytest.mark.asyncio
    async def test_diagnose_ad_with_review_feedback(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Ad diagnostics include review feedback and delivery checks."""
        from meta_ads_mcp.tools.ads import get_ad_diagnostics

        mock_client.get_ad_diagnostics.return_value = {
            "id": "ad_1",
            "name": "Test Ad",
            "issues_info": [{"level": "error", "summary": "Ad rejected by review"}],
            "recommendations": [],
            "ad_review_feedback": {"policy": "Restricted content"},
            "failed_delivery_checks": [
                {"summary": "Creative issue", "description": "Image text too high"}
            ],
        }
        result = await get_ad_diagnostics(mock_context, ad_id="ad_1")
        assert "Ad rejected" in result
        assert "Restricted content" in result
        assert "Image text too high" in result


class TestAudienceWorkflow:
    """Create custom -> create lookalike -> list workflow."""

    @pytest.mark.asyncio
    async def test_create_custom_then_lookalike(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Create a custom audience, then a lookalike based on it."""
        from meta_ads_mcp.tools.audiences import (
            create_custom_audience,
            create_lookalike_audience,
        )

        mock_client.create_custom_audience.return_value = {"id": "aud_100"}
        result = await create_custom_audience(
            mock_context,
            name="Website Visitors",
            subtype="WEBSITE",
            description="All site visitors last 30 days",
        )
        assert "aud_100" in result
        assert "Website Visitors" in result

        mock_client.create_lookalike_audience.return_value = {"id": "aud_200"}
        result = await create_lookalike_audience(
            mock_context,
            name="Lookalike US 1%",
            origin_audience_id="aud_100",
            country="US",
            ratio=0.01,
        )
        assert "aud_200" in result
        assert "Lookalike" in result

    @pytest.mark.asyncio
    async def test_create_then_list(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Created audiences appear in list."""
        from meta_ads_mcp.tools.audiences import (
            create_custom_audience,
            list_audiences,
        )

        mock_client.create_custom_audience.return_value = {"id": "aud_100"}
        await create_custom_audience(
            mock_context, name="Test Audience", subtype="CUSTOM"
        )

        mock_client.get_audiences.return_value = [
            {
                "id": "aud_100",
                "name": "Test Audience",
                "subtype": "CUSTOM",
                "approximate_count_lower_bound": 1000,
                "approximate_count_upper_bound": 5000,
            }
        ]
        result = await list_audiences(mock_context)
        assert "aud_100" in result
        assert "Test Audience" in result


class TestErrorPropagation:
    """Verify error handling works across workflows."""

    @pytest.mark.asyncio
    async def test_api_error_with_hint(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API errors include error code and hint in output."""
        from meta_ads_mcp.client import MetaAdsError
        from meta_ads_mcp.tools.campaigns import list_campaigns

        mock_client.get_campaigns.side_effect = MetaAdsError(
            "Rate limit exceeded", error_code=17
        )
        result = await list_campaigns(mock_context)
        assert "Rate limit exceeded" in result
        assert "**Error Code**: 17" in result
        assert "**Suggestion**" in result

    @pytest.mark.asyncio
    async def test_write_error_with_hint(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Write operation errors include hints when available."""
        from meta_ads_mcp.client import MetaAdsError
        from meta_ads_mcp.tools.campaigns import create_campaign

        mock_client.create_campaign.side_effect = MetaAdsError(
            "Access token expired", error_code=190
        )
        result = await create_campaign(
            mock_context, name="Test", objective="OUTCOME_TRAFFIC"
        )
        assert "Access token expired" in result
        assert "**Error Code**: 190" in result
        assert "Generate a new token" in result
