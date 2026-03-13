"""Tests for diagnostic tools, models, formatters, and client methods."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from meta_ads_mcp.client import MetaAdsClient, MetaAdsError
from meta_ads_mcp.config import MetaAdsConfig
from meta_ads_mcp.formatting import (
    format_ad_review_feedback,
    format_delivery_checks,
    format_diagnostics,
    format_learning_stage,
)
from meta_ads_mcp.models import (
    AdDiagnosticsModel,
    AdSetDiagnosticsModel,
    CampaignDiagnosticsModel,
)
from meta_ads_mcp.tools.ads import get_ad_diagnostics
from meta_ads_mcp.tools.adsets import get_ad_set_diagnostics
from meta_ads_mcp.tools.campaigns import get_campaign_diagnostics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeSDKObject(dict):
    """Dict subclass that mimics facebook-business SDK objects for dict() conversion."""

    def api_get(self, **kwargs: Any) -> None:
        pass


def _make_sdk_error(
    message: str = "Error",
    code: int = 100,
    subcode: int = 0,
) -> Exception:
    """Create a real FacebookRequestError for testing."""
    from facebook_business.exceptions import FacebookRequestError

    body = {"error": {"message": message, "code": code, "error_subcode": subcode}}
    return FacebookRequestError(
        message=message,
        request_context={"method": "GET", "path": "/test"},
        http_status=400,
        http_headers={},
        body=json.dumps(body),
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestCampaignDiagnosticsModel:
    """Tests for CampaignDiagnosticsModel."""

    def test_with_data(self) -> None:
        """Model populates fields from data."""
        model = CampaignDiagnosticsModel(
            id="camp_1",
            name="Test Campaign",
            status="ACTIVE",
            issues_info=[{"level": "warning", "summary": "Low budget"}],
            recommendations=[{"title": "Increase budget", "message": "Spend more"}],
        )
        assert model.id == "camp_1"
        assert model.name == "Test Campaign"
        assert model.status == "ACTIVE"
        assert len(model.issues_info) == 1
        assert model.issues_info[0]["level"] == "warning"
        assert len(model.recommendations) == 1

    def test_defaults(self) -> None:
        """Model uses empty defaults."""
        model = CampaignDiagnosticsModel()
        assert model.id == ""
        assert model.name == ""
        assert model.status == ""
        assert model.issues_info == []
        assert model.recommendations == []

    def test_extra_ignore(self) -> None:
        """Model ignores extra fields."""
        model = CampaignDiagnosticsModel(
            id="camp_1",
            unknown_field="should be ignored",
        )
        assert model.id == "camp_1"
        assert not hasattr(model, "unknown_field")


class TestAdSetDiagnosticsModel:
    """Tests for AdSetDiagnosticsModel."""

    def test_with_data(self) -> None:
        """Model populates fields from data."""
        model = AdSetDiagnosticsModel(
            id="adset_1",
            name="Test Ad Set",
            status="ACTIVE",
            issues_info=[{"level": "error", "summary": "Budget depleted"}],
            recommendations=[{"message": "Increase budget"}],
            learning_stage_info={"status": "LEARNING"},
        )
        assert model.id == "adset_1"
        assert model.learning_stage_info["status"] == "LEARNING"

    def test_defaults(self) -> None:
        """Model uses empty defaults."""
        model = AdSetDiagnosticsModel()
        assert model.learning_stage_info == {}
        assert model.issues_info == []

    def test_extra_ignore(self) -> None:
        """Model ignores extra fields."""
        model = AdSetDiagnosticsModel(
            id="adset_1",
            extra_field="ignored",
        )
        assert model.id == "adset_1"


class TestAdDiagnosticsModel:
    """Tests for AdDiagnosticsModel."""

    def test_with_data(self) -> None:
        """Model populates fields from data."""
        model = AdDiagnosticsModel(
            id="ad_1",
            name="Test Ad",
            status="DISAPPROVED",
            ad_review_feedback={"policy": "rejected"},
            failed_delivery_checks=[{"summary": "Payment failed"}],
            issues_info=[{"level": "error", "summary": "Policy violation"}],
            recommendations=[{"title": "Fix", "message": "Update creative"}],
        )
        assert model.id == "ad_1"
        assert model.ad_review_feedback["policy"] == "rejected"
        assert len(model.failed_delivery_checks) == 1
        assert len(model.issues_info) == 1
        assert len(model.recommendations) == 1

    def test_defaults(self) -> None:
        """Model uses empty defaults."""
        model = AdDiagnosticsModel()
        assert model.ad_review_feedback == {}
        assert model.failed_delivery_checks == []
        assert model.issues_info == []
        assert model.recommendations == []

    def test_extra_ignore(self) -> None:
        """Model ignores extra fields."""
        model = AdDiagnosticsModel(
            id="ad_1",
            something_extra=True,
        )
        assert model.id == "ad_1"


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------


class TestFormatDiagnostics:
    """Tests for format_diagnostics."""

    def test_with_issues_and_recommendations(self) -> None:
        """Formats issues and recommendations."""
        result = format_diagnostics(
            "Campaign",
            "Spring Sale",
            [
                {"level": "warning", "summary": "Low budget"},
                {"level": "error", "summary": "No targeting"},
            ],
            [
                {"title": "Increase budget", "message": "Spend at least $50/day"},
                {"message": "Add audience targeting"},
            ],
        )
        assert "## Campaign Diagnostics: Spring Sale" in result
        assert "**[WARNING]** Low budget" in result
        assert "**[ERROR]** No targeting" in result
        assert "**Increase budget**: Spend at least $50/day" in result
        assert "- Add audience targeting" in result

    def test_empty_issues(self) -> None:
        """Shows no-issues message when empty."""
        result = format_diagnostics("Campaign", "Test", [], [])
        assert "No issues found." in result
        assert "No recommendations." in result

    def test_missing_level_and_summary(self) -> None:
        """Handles missing keys gracefully."""
        result = format_diagnostics("Ad", "Test", [{}], [{}])
        assert "**[UNKNOWN]** No summary" in result
        assert "- No details" in result

    def test_recommendation_without_title(self) -> None:
        """Recommendations without title show just message."""
        result = format_diagnostics("Ad Set", "Test", [], [{"message": "Do this"}])
        assert "- Do this" in result


class TestFormatLearningStage:
    """Tests for format_learning_stage."""

    def test_empty_info(self) -> None:
        """Shows no-data message for empty dict."""
        result = format_learning_stage({})
        assert "No learning stage data available." in result

    def test_learning_status(self) -> None:
        """Displays LEARNING status with description."""
        result = format_learning_stage({"status": "LEARNING"})
        assert "Learning (gathering data)" in result

    def test_success_status(self) -> None:
        """Displays SUCCESS status."""
        result = format_learning_stage({"status": "SUCCESS"})
        assert "Learning Complete (exited learning)" in result

    def test_learning_limited_status(self) -> None:
        """Displays LEARNING_LIMITED status."""
        result = format_learning_stage({"status": "LEARNING_LIMITED"})
        assert "Learning Limited (not enough conversions)" in result

    def test_unknown_status(self) -> None:
        """Displays raw status for unknown values."""
        result = format_learning_stage({"status": "CUSTOM_STATUS"})
        assert "CUSTOM_STATUS" in result

    def test_with_info_field(self) -> None:
        """Includes info field when present."""
        result = format_learning_stage(
            {"status": "LEARNING", "info": "3 of 50 conversions"}
        )
        assert "3 of 50 conversions" in result


class TestFormatAdReviewFeedback:
    """Tests for format_ad_review_feedback."""

    def test_empty_feedback(self) -> None:
        """Shows no-feedback message for empty dict."""
        result = format_ad_review_feedback({})
        assert "No review feedback available." in result

    def test_with_feedback(self) -> None:
        """Formats feedback key-value pairs."""
        result = format_ad_review_feedback(
            {"policy_area": "Prohibited Content", "status": "REJECTED"}
        )
        assert "### Ad Review" in result
        assert "**policy_area**: Prohibited Content" in result
        assert "**status**: REJECTED" in result


class TestFormatDeliveryChecks:
    """Tests for format_delivery_checks."""

    def test_empty_checks(self) -> None:
        """Shows all-passed message for empty list."""
        result = format_delivery_checks([])
        assert "All delivery checks passed." in result

    def test_with_checks(self) -> None:
        """Formats failed delivery checks."""
        result = format_delivery_checks(
            [
                {
                    "summary": "Payment method invalid",
                    "description": "Update your payment method",
                },
                {"summary": "Account restricted"},
            ]
        )
        assert "**Payment method invalid**" in result
        assert "Update your payment method" in result
        assert "**Account restricted**" in result


# ---------------------------------------------------------------------------
# Client tests
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> MetaAdsConfig:
    """Create a test config."""
    return MetaAdsConfig(
        access_token="test_token_12345678",
        app_id="test_app_id",
        app_secret="test_app_secret",
        default_account_id="act_123456",
    )


@pytest.fixture
def client(config: MetaAdsConfig) -> MetaAdsClient:
    """Create an initialized test client with mocked API."""
    c = MetaAdsClient(config)
    with patch("meta_ads_mcp.client.FacebookAdsApi.init") as mock_init:
        mock_init.return_value = MagicMock()
        c.initialize()
    return c


class TestGetCampaignDiagnosticsClient:
    """Tests for client.get_campaign_diagnostics."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns campaign diagnostic data."""
        mock_campaign = FakeSDKObject(
            {
                "id": "camp_1",
                "name": "Test",
                "status": "ACTIVE",
                "issues_info": [],
                "recommendations": [],
            }
        )

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            MockCampaign.return_value = mock_campaign
            result = await client.get_campaign_diagnostics("camp_1")

        assert result["id"] == "camp_1"
        assert result["issues_info"] == []

    @pytest.mark.asyncio
    async def test_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error(message="Not found", code=100)

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            mock_obj = MagicMock()
            mock_obj.api_get.side_effect = error
            MockCampaign.return_value = mock_obj

            with pytest.raises(MetaAdsError, match="Not found"):
                await client.get_campaign_diagnostics("camp_bad")


class TestGetAdSetDiagnosticsClient:
    """Tests for client.get_ad_set_diagnostics."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns ad set diagnostic data."""
        mock_adset = FakeSDKObject(
            {
                "id": "adset_1",
                "name": "Test Ad Set",
                "status": "ACTIVE",
                "issues_info": [],
                "recommendations": [],
                "learning_stage_info": {"status": "LEARNING"},
            }
        )

        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            MockAdSet.return_value = mock_adset
            result = await client.get_ad_set_diagnostics("adset_1")

        assert result["id"] == "adset_1"
        assert result["learning_stage_info"]["status"] == "LEARNING"

    @pytest.mark.asyncio
    async def test_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error(message="Permission denied", code=200)

        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            mock_obj = MagicMock()
            mock_obj.api_get.side_effect = error
            MockAdSet.return_value = mock_obj

            with pytest.raises(MetaAdsError, match="Permission denied"):
                await client.get_ad_set_diagnostics("adset_bad")


class TestGetAdDiagnosticsClient:
    """Tests for client.get_ad_diagnostics."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns ad diagnostic data."""
        mock_ad = FakeSDKObject(
            {
                "id": "ad_1",
                "name": "Test Ad",
                "status": "ACTIVE",
                "ad_review_feedback": {},
                "failed_delivery_checks": [],
                "issues_info": [],
                "recommendations": [],
            }
        )

        with patch("meta_ads_mcp.client.Ad") as MockAd:
            MockAd.return_value = mock_ad
            result = await client.get_ad_diagnostics("ad_1")

        assert result["id"] == "ad_1"
        assert result["ad_review_feedback"] == {}

    @pytest.mark.asyncio
    async def test_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error(message="Invalid token", code=190)

        with patch("meta_ads_mcp.client.Ad") as MockAd:
            mock_obj = MagicMock()
            mock_obj.api_get.side_effect = error
            MockAd.return_value = mock_obj

            with pytest.raises(MetaAdsError, match="Invalid token"):
                await client.get_ad_diagnostics("ad_bad")


# ---------------------------------------------------------------------------
# Tool tests
# ---------------------------------------------------------------------------


class TestGetCampaignDiagnosticsTool:
    """Tests for get_campaign_diagnostics tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted diagnostics."""
        mock_client.get_campaign_diagnostics.return_value = {
            "id": "camp_1",
            "name": "Spring Sale",
            "status": "ACTIVE",
            "issues_info": [{"level": "warning", "summary": "Low budget"}],
            "recommendations": [{"title": "Boost", "message": "Increase spend"}],
        }

        result = await get_campaign_diagnostics(mock_context, campaign_id="camp_1")

        assert "## Campaign Diagnostics: Spring Sale" in result
        assert "**[WARNING]** Low budget" in result
        assert "**Boost**: Increase spend" in result
        mock_client.get_campaign_diagnostics.assert_called_once_with("camp_1")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_campaign_diagnostics.side_effect = MetaAdsError(
            "Campaign not found"
        )

        result = await get_campaign_diagnostics(mock_context, campaign_id="camp_bad")

        assert "## Error" in result
        assert "Campaign not found" in result


class TestGetAdSetDiagnosticsTool:
    """Tests for get_ad_set_diagnostics tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted diagnostics with learning stage."""
        mock_client.get_ad_set_diagnostics.return_value = {
            "id": "adset_1",
            "name": "US Audience",
            "status": "ACTIVE",
            "issues_info": [],
            "recommendations": [],
            "learning_stage_info": {"status": "LEARNING"},
        }

        result = await get_ad_set_diagnostics(mock_context, ad_set_id="adset_1")

        assert "## Ad Set Diagnostics: US Audience" in result
        assert "No issues found." in result
        assert "Learning (gathering data)" in result
        mock_client.get_ad_set_diagnostics.assert_called_once_with("adset_1")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_set_diagnostics.side_effect = MetaAdsError("Not found")

        result = await get_ad_set_diagnostics(mock_context, ad_set_id="adset_bad")

        assert "## Error" in result
        assert "Not found" in result


class TestGetAdDiagnosticsTool:
    """Tests for get_ad_diagnostics tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted diagnostics with review and checks."""
        mock_client.get_ad_diagnostics.return_value = {
            "id": "ad_1",
            "name": "Banner Ad",
            "status": "DISAPPROVED",
            "ad_review_feedback": {"policy_area": "Prohibited Content"},
            "failed_delivery_checks": [
                {"summary": "Payment failed", "description": "Update payment"}
            ],
            "issues_info": [{"level": "error", "summary": "Policy violation"}],
            "recommendations": [{"title": "Fix", "message": "Update creative"}],
        }

        result = await get_ad_diagnostics(mock_context, ad_id="ad_1")

        assert "## Ad Diagnostics: Banner Ad" in result
        assert "**[ERROR]** Policy violation" in result
        assert "**Fix**: Update creative" in result
        assert "**policy_area**: Prohibited Content" in result
        assert "**Payment failed**" in result
        assert "Update payment" in result
        mock_client.get_ad_diagnostics.assert_called_once_with("ad_1")

    @pytest.mark.asyncio
    async def test_success_no_issues(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns clean diagnostics when no issues found."""
        mock_client.get_ad_diagnostics.return_value = {
            "id": "ad_2",
            "name": "Good Ad",
            "status": "ACTIVE",
            "ad_review_feedback": {},
            "failed_delivery_checks": [],
            "issues_info": [],
            "recommendations": [],
        }

        result = await get_ad_diagnostics(mock_context, ad_id="ad_2")

        assert "No issues found." in result
        assert "No review feedback available." in result
        assert "All delivery checks passed." in result

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_diagnostics.side_effect = MetaAdsError("Ad not found")

        result = await get_ad_diagnostics(mock_context, ad_id="ad_bad")

        assert "## Error" in result
        assert "Ad not found" in result
