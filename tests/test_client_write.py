"""Tests for MetaAdsClient write methods."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from meta_ads_mcp.client import MetaAdsClient, MetaAdsError
from meta_ads_mcp.config import MetaAdsConfig


class FakeSDKObject(dict):
    """Dict subclass that mimics facebook-business SDK objects."""

    def api_get(self, **kwargs: Any) -> None:
        pass

    def api_update(self, **kwargs: Any) -> "FakeSDKObject":
        return FakeSDKObject({"success": True})


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
        request_context={"method": "POST", "path": "/test"},
        http_status=400,
        http_headers={},
        body=json.dumps(body),
    )


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


class TestCreateCampaign:
    """Tests for client.create_campaign."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates campaign with correct params."""
        result_obj = FakeSDKObject({"id": "camp_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_campaign.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_campaign(
                name="Test Campaign",
                objective="OUTCOME_TRAFFIC",
                daily_budget=5000,
            )

        assert result["id"] == "camp_new"
        call_params = mock_account.create_campaign.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Test Campaign"
        assert params["objective"] == "OUTCOME_TRAFFIC"
        assert params["status"] == "PAUSED"
        assert params["daily_budget"] == 5000
        assert params["special_ad_categories"] == ["NONE"]

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only execution option."""
        result_obj = FakeSDKObject({"id": ""})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_campaign.return_value = result_obj
            MockAdAccount.return_value = mock_account

            await client.create_campaign(
                name="Test",
                objective="OUTCOME_TRAFFIC",
                dry_run=True,
            )

        call_params = mock_account.create_campaign.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Permission denied", code=200)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_campaign.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Permission denied"):
                await client.create_campaign(name="Fail", objective="OUTCOME_TRAFFIC")


class TestUpdateCampaign:
    """Tests for client.update_campaign."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Updates campaign with correct params."""
        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            mock_campaign = MagicMock()
            mock_campaign.api_update.return_value = FakeSDKObject({"success": True})
            MockCampaign.return_value = mock_campaign

            result = await client.update_campaign(
                campaign_id="camp_1",
                name="Updated Name",
                status="PAUSED",
            )

        assert result == {"success": True}
        call_params = mock_campaign.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Updated Name"
        assert params["status"] == "PAUSED"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            mock_campaign = MagicMock()
            mock_campaign.api_update.return_value = FakeSDKObject({})
            MockCampaign.return_value = mock_campaign

            await client.update_campaign(
                campaign_id="camp_1",
                name="Test",
                dry_run=True,
            )

        call_params = mock_campaign.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid campaign", code=100)

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            mock_campaign = MagicMock()
            mock_campaign.api_update.side_effect = error
            MockCampaign.return_value = mock_campaign

            with pytest.raises(MetaAdsError, match="Invalid campaign"):
                await client.update_campaign(campaign_id="camp_bad", name="Fail")


class TestCreateAdSet:
    """Tests for client.create_ad_set."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates ad set with correct params."""
        result_obj = FakeSDKObject({"id": "adset_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_set.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_ad_set(
                name="Test Ad Set",
                campaign_id="camp_1",
                billing_event="IMPRESSIONS",
                optimization_goal="LINK_CLICKS",
                targeting={"geo_locations": {"countries": ["US"]}},
                daily_budget=5000,
            )

        assert result["id"] == "adset_new"
        call_params = mock_account.create_ad_set.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["campaign_id"] == "camp_1"
        assert params["targeting"]["geo_locations"]["countries"] == ["US"]
        assert params["status"] == "PAUSED"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        result_obj = FakeSDKObject({"id": ""})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_set.return_value = result_obj
            MockAdAccount.return_value = mock_account

            await client.create_ad_set(
                name="Test",
                campaign_id="camp_1",
                billing_event="IMPRESSIONS",
                optimization_goal="LINK_CLICKS",
                targeting={"geo_locations": {"countries": ["US"]}},
                dry_run=True,
            )

        call_params = mock_account.create_ad_set.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid targeting", code=100)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_set.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Invalid targeting"):
                await client.create_ad_set(
                    name="Fail",
                    campaign_id="camp_1",
                    billing_event="IMPRESSIONS",
                    optimization_goal="LINK_CLICKS",
                    targeting={},
                )


class TestUpdateAdSet:
    """Tests for client.update_ad_set."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Updates ad set with correct params."""
        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            mock_adset = MagicMock()
            mock_adset.api_update.return_value = FakeSDKObject({"success": True})
            MockAdSet.return_value = mock_adset

            result = await client.update_ad_set(
                ad_set_id="adset_1",
                name="Updated Ad Set",
                daily_budget=7500,
            )

        assert result == {"success": True}
        call_params = mock_adset.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Updated Ad Set"
        assert params["daily_budget"] == 7500

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            mock_adset = MagicMock()
            mock_adset.api_update.return_value = FakeSDKObject({})
            MockAdSet.return_value = mock_adset

            await client.update_ad_set(
                ad_set_id="adset_1",
                name="Test",
                dry_run=True,
            )

        call_params = mock_adset.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid ad set", code=100)

        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            mock_adset = MagicMock()
            mock_adset.api_update.side_effect = error
            MockAdSet.return_value = mock_adset

            with pytest.raises(MetaAdsError, match="Invalid ad set"):
                await client.update_ad_set(ad_set_id="adset_bad", name="Fail")


class TestCreateAd:
    """Tests for client.create_ad."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates ad with correct params."""
        result_obj = FakeSDKObject({"id": "ad_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_ad(
                name="Test Ad",
                adset_id="adset_1",
                creative_id="cr_1",
            )

        assert result["id"] == "ad_new"
        call_params = mock_account.create_ad.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["creative"] == {"creative_id": "cr_1"}
        assert params["adset_id"] == "adset_1"
        assert params["status"] == "PAUSED"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        result_obj = FakeSDKObject({"id": ""})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad.return_value = result_obj
            MockAdAccount.return_value = mock_account

            await client.create_ad(
                name="Test",
                adset_id="adset_1",
                creative_id="cr_1",
                dry_run=True,
            )

        call_params = mock_account.create_ad.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid creative", code=100)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Invalid creative"):
                await client.create_ad(
                    name="Fail",
                    adset_id="adset_1",
                    creative_id="cr_bad",
                )


class TestUpdateAd:
    """Tests for client.update_ad."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Updates ad with correct params."""
        with patch("meta_ads_mcp.client.Ad") as MockAd:
            mock_ad = MagicMock()
            mock_ad.api_update.return_value = FakeSDKObject({"success": True})
            MockAd.return_value = mock_ad

            result = await client.update_ad(
                ad_id="ad_1",
                status="PAUSED",
            )

        assert result == {"success": True}
        call_params = mock_ad.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["status"] == "PAUSED"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        with patch("meta_ads_mcp.client.Ad") as MockAd:
            mock_ad = MagicMock()
            mock_ad.api_update.return_value = FakeSDKObject({})
            MockAd.return_value = mock_ad

            await client.update_ad(
                ad_id="ad_1",
                status="ACTIVE",
                dry_run=True,
            )

        call_params = mock_ad.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid ad", code=100)

        with patch("meta_ads_mcp.client.Ad") as MockAd:
            mock_ad = MagicMock()
            mock_ad.api_update.side_effect = error
            MockAd.return_value = mock_ad

            with pytest.raises(MetaAdsError, match="Invalid ad"):
                await client.update_ad(ad_id="ad_bad", status="PAUSED")


class TestCreateCustomAudience:
    """Tests for client.create_custom_audience."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates custom audience with correct params."""
        result_obj = FakeSDKObject({"id": "aud_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:  # noqa: N806
            mock_account = MagicMock()
            mock_account.create_custom_audience.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_custom_audience(
                name="Website Visitors",
                subtype="WEBSITE",
                pixel_id="px_123",
                retention_days=30,
            )

        assert result["id"] == "aud_new"
        call_params = mock_account.create_custom_audience.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Website Visitors"
        assert params["subtype"] == "WEBSITE"
        assert params["pixel_id"] == "px_123"
        assert params["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid audience", code=100)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:  # noqa: N806
            mock_account = MagicMock()
            mock_account.create_custom_audience.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Invalid audience"):
                await client.create_custom_audience(name="Fail", subtype="CUSTOM")


class TestCreateLookalikeAudience:
    """Tests for client.create_lookalike_audience."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates lookalike audience with correct params."""
        result_obj = FakeSDKObject({"id": "aud_lal"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:  # noqa: N806
            mock_account = MagicMock()
            mock_account.create_custom_audience.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_lookalike_audience(
                name="US Lookalike",
                origin_audience_id="aud_source",
                country="US",
                ratio=0.01,
            )

        assert result["id"] == "aud_lal"
        call_params = mock_account.create_custom_audience.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "US Lookalike"
        assert params["subtype"] == "LOOKALIKE"
        assert params["lookalike_spec"]["origin_audience_id"] == "aud_source"
        assert params["lookalike_spec"]["country"] == "US"
        assert params["lookalike_spec"]["ratio"] == 0.01

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Source not found", code=100)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:  # noqa: N806
            mock_account = MagicMock()
            mock_account.create_custom_audience.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Source not found"):
                await client.create_lookalike_audience(
                    name="Fail",
                    origin_audience_id="aud_bad",
                    country="US",
                    ratio=0.01,
                )
