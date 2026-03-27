"""Tests for MetaAdsClient."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from meta_ads_mcp.client import MetaAdsClient, MetaAdsError
from meta_ads_mcp.config import MetaAdsConfig


class FakeSDKObject(dict):
    """Dict subclass that mimics facebook-business SDK objects for dict() conversion."""

    def api_get(self, **kwargs: Any) -> None:
        pass


def _make_sdk_error(
    message: str = "Error",
    code: int = 100,
    subcode: int = 0,
    error_user_msg: str = "",
    blame_field_specs: list[list[str]] | None = None,
) -> Exception:
    """Create a real FacebookRequestError for testing."""
    from facebook_business.exceptions import FacebookRequestError

    error_dict: dict[str, Any] = {
        "message": message,
        "code": code,
        "error_subcode": subcode,
    }
    if error_user_msg:
        error_dict["error_user_msg"] = error_user_msg
    if blame_field_specs is not None:
        error_dict["error_data"] = {"blame_field_specs": blame_field_specs}
    body = {"error": error_dict}
    return FacebookRequestError(
        message=message,
        request_context={"method": "GET", "path": "/test"},
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


class TestMetaAdsError:
    """Tests for MetaAdsError."""

    def test_basic_error(self) -> None:
        """Error stores message and optional codes."""
        err = MetaAdsError("Something failed", error_code=100, error_subcode=33)
        assert str(err) == "Something failed"
        assert err.message == "Something failed"
        assert err.error_code == 100
        assert err.error_subcode == 33

    def test_error_defaults(self) -> None:
        """Error codes default to None."""
        err = MetaAdsError("fail")
        assert err.error_code is None
        assert err.error_subcode is None


class TestClientInitialization:
    """Tests for client initialization."""

    def test_uninitialized_guard(self, config: MetaAdsConfig) -> None:
        """Methods raise error before initialization."""
        c = MetaAdsClient(config)
        with pytest.raises(MetaAdsError, match="not initialized"):
            c._ensure_initialized()

    def test_initialize(self, config: MetaAdsConfig) -> None:
        """initialize() calls FacebookAdsApi.init()."""
        c = MetaAdsClient(config)
        with patch("meta_ads_mcp.client.FacebookAdsApi.init") as mock_init:
            mock_init.return_value = MagicMock()
            c.initialize()
            mock_init.assert_called_once_with(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="test_token_12345678",
                api_version="v25.0",
            )
        assert c._api is not None


class TestClientMethods:
    """Tests for client API methods."""

    @pytest.mark.asyncio
    async def test_get_ad_accounts(self, client: MetaAdsClient) -> None:
        """get_ad_accounts returns list of dicts."""
        mock_account = FakeSDKObject({"id": "act_123", "name": "Test"})

        with patch("meta_ads_mcp.client.User") as MockUser:
            mock_user = MagicMock()
            mock_user.get_ad_accounts.return_value = [mock_account]
            MockUser.return_value = mock_user

            result = await client.get_ad_accounts()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "act_123"

    @pytest.mark.asyncio
    async def test_get_account_info(self, client: MetaAdsClient) -> None:
        """get_account_info returns a dict."""
        mock_account = FakeSDKObject({"id": "act_123", "name": "Test"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            MockAdAccount.return_value = mock_account
            result = await client.get_account_info("act_123")

        assert isinstance(result, dict)
        assert result["id"] == "act_123"

    @pytest.mark.asyncio
    async def test_get_campaigns(self, client: MetaAdsClient) -> None:
        """get_campaigns returns list of dicts."""
        mock_campaign = FakeSDKObject({"id": "camp_1", "name": "Campaign 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_campaigns.return_value = [mock_campaign]
            MockAdAccount.return_value = mock_account

            result = await client.get_campaigns("act_123")

        assert len(result) == 1
        assert result[0]["name"] == "Campaign 1"

    @pytest.mark.asyncio
    async def test_get_campaigns_with_filter(self, client: MetaAdsClient) -> None:
        """get_campaigns passes status filter."""
        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_campaigns.return_value = []
            MockAdAccount.return_value = mock_account

            await client.get_campaigns("act_123", status_filter=["ACTIVE"])

            call_params = mock_account.get_campaigns.call_args
            params = call_params.kwargs.get("params") or call_params[1].get(
                "params", {}
            )
            assert "filtering" in params

    @pytest.mark.asyncio
    async def test_get_campaign(self, client: MetaAdsClient) -> None:
        """get_campaign returns a dict."""
        mock_campaign = FakeSDKObject({"id": "camp_1", "name": "My Campaign"})

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            MockCampaign.return_value = mock_campaign
            result = await client.get_campaign("camp_1")

        assert result["name"] == "My Campaign"

    @pytest.mark.asyncio
    async def test_get_ad_sets(self, client: MetaAdsClient) -> None:
        """get_ad_sets returns list of dicts."""
        mock_adset = FakeSDKObject({"id": "adset_1", "name": "Ad Set 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_sets.return_value = [mock_adset]
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_sets("act_123")

        assert len(result) == 1
        assert result[0]["name"] == "Ad Set 1"

    @pytest.mark.asyncio
    async def test_get_ad_sets_by_campaign(self, client: MetaAdsClient) -> None:
        """get_ad_sets can filter by campaign_id."""
        mock_adset = FakeSDKObject({"id": "adset_1"})

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            mock_campaign = MagicMock()
            mock_campaign.get_ad_sets.return_value = [mock_adset]
            MockCampaign.return_value = mock_campaign

            result = await client.get_ad_sets(campaign_id="camp_1")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_ad_set(self, client: MetaAdsClient) -> None:
        """get_ad_set returns a dict."""
        mock_adset = FakeSDKObject({"id": "adset_1", "name": "Test Ad Set"})

        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            MockAdSet.return_value = mock_adset
            result = await client.get_ad_set("adset_1")

        assert result["name"] == "Test Ad Set"

    @pytest.mark.asyncio
    async def test_get_ads(self, client: MetaAdsClient) -> None:
        """get_ads returns list of dicts."""
        mock_ad = FakeSDKObject({"id": "ad_1", "name": "Ad 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ads.return_value = [mock_ad]
            MockAdAccount.return_value = mock_account

            result = await client.get_ads("act_123")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_ad(self, client: MetaAdsClient) -> None:
        """get_ad returns a dict."""
        mock_ad = FakeSDKObject({"id": "ad_1", "name": "Test Ad"})

        with patch("meta_ads_mcp.client.Ad") as MockAd:
            MockAd.return_value = mock_ad
            result = await client.get_ad("ad_1")

        assert result["name"] == "Test Ad"

    @pytest.mark.asyncio
    async def test_get_insights(self, client: MetaAdsClient) -> None:
        """get_insights returns list of dicts."""
        mock_row = FakeSDKObject({"impressions": "1000", "clicks": "50"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_insights.return_value = [mock_row]
            MockAdAccount.return_value = mock_account

            result = await client.get_insights("act_123", date_preset="last_7d")

        assert len(result) == 1
        assert result[0]["impressions"] == "1000"

    @pytest.mark.asyncio
    async def test_get_creatives(self, client: MetaAdsClient) -> None:
        """get_creatives returns list of dicts."""
        mock_creative = FakeSDKObject({"id": "cr_1", "name": "Creative 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_creatives.return_value = [mock_creative]
            MockAdAccount.return_value = mock_account

            result = await client.get_creatives("act_123")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_creative(self, client: MetaAdsClient) -> None:
        """get_creative returns a dict."""
        mock_creative = FakeSDKObject({"id": "cr_1", "name": "Test Creative"})

        with patch("meta_ads_mcp.client.AdCreative") as MockAdCreative:
            MockAdCreative.return_value = mock_creative
            result = await client.get_creative("cr_1")

        assert result["name"] == "Test Creative"

    @pytest.mark.asyncio
    async def test_get_audiences(self, client: MetaAdsClient) -> None:
        """get_audiences returns list of dicts."""
        mock_audience = FakeSDKObject({"id": "aud_1", "name": "Audience 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_custom_audiences.return_value = [mock_audience]
            MockAdAccount.return_value = mock_account

            result = await client.get_audiences("act_123")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_audience(self, client: MetaAdsClient) -> None:
        """get_audience returns a dict."""
        mock_audience = FakeSDKObject({"id": "aud_1", "name": "Test Audience"})

        with patch("meta_ads_mcp.client.CustomAudience") as MockCustomAudience:
            MockCustomAudience.return_value = mock_audience
            result = await client.get_audience("aud_1")

        assert result["name"] == "Test Audience"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error(message="Invalid token", code=190, subcode=463)

        with patch("meta_ads_mcp.client.User") as MockUser:
            mock_user = MagicMock()
            mock_user.get_ad_accounts.side_effect = error
            MockUser.return_value = mock_user

            with pytest.raises(MetaAdsError) as exc_info:
                await client.get_ad_accounts()

            assert exc_info.value.error_code == 190
            assert exc_info.value.error_subcode == 463

    @pytest.mark.asyncio
    async def test_api_error_extracts_user_msg_and_blame_fields(
        self, client: MetaAdsClient
    ) -> None:
        """API errors extract error_user_msg and blame_field_specs."""
        error = _make_sdk_error(
            message="Invalid parameter",
            code=100,
            subcode=1885024,
            error_user_msg="Ad set requires a daily or lifetime budget.",
            blame_field_specs=[["daily_budget"], ["lifetime_budget"]],
        )

        with patch("meta_ads_mcp.client.User") as MockUser:
            mock_user = MagicMock()
            mock_user.get_ad_accounts.side_effect = error
            MockUser.return_value = mock_user

            with pytest.raises(MetaAdsError) as exc_info:
                await client.get_ad_accounts()

            assert exc_info.value.error_code == 100
            assert exc_info.value.error_subcode == 1885024
            assert exc_info.value.error_user_msg == (
                "Ad set requires a daily or lifetime budget."
            )
            assert exc_info.value.blame_field_specs == [
                "daily_budget",
                "lifetime_budget",
            ]

    @pytest.mark.asyncio
    async def test_api_error_handles_missing_user_msg(
        self, client: MetaAdsClient
    ) -> None:
        """API errors gracefully handle missing error_user_msg."""
        error = _make_sdk_error(message="Bad param", code=100)

        with patch("meta_ads_mcp.client.User") as MockUser:
            mock_user = MagicMock()
            mock_user.get_ad_accounts.side_effect = error
            MockUser.return_value = mock_user

            with pytest.raises(MetaAdsError) as exc_info:
                await client.get_ad_accounts()

            assert exc_info.value.error_user_msg == ""
            assert exc_info.value.blame_field_specs is None

    @pytest.mark.asyncio
    async def test_get_creatives_includes_v25_fields(
        self, client: MetaAdsClient
    ) -> None:
        """get_creatives requests v25 creative fields."""
        mock_creative = FakeSDKObject({"id": "cr_1", "name": "Creative 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_creatives.return_value = [mock_creative]
            MockAdAccount.return_value = mock_account

            await client.get_creatives("act_123")

            call_args = mock_account.get_ad_creatives.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in ["status", "object_story_spec", "url_tags", "image_hash"]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in fields"

    @pytest.mark.asyncio
    async def test_get_creative_includes_v25_fields(
        self, client: MetaAdsClient
    ) -> None:
        """get_creative requests v25 creative fields."""
        mock = FakeSDKObject({"id": "cr_1", "name": "Creative 1"})
        mock.api_get = MagicMock()

        with patch("meta_ads_mcp.client.AdCreative") as MockAdCreative:
            MockAdCreative.return_value = mock
            await client.get_creative("cr_1")

            call_args = mock.api_get.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in ["status", "object_story_spec", "url_tags", "image_hash"]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in fields"

    @pytest.mark.asyncio
    async def test_get_audiences_includes_v25_fields(
        self, client: MetaAdsClient
    ) -> None:
        """get_audiences requests v25 audience fields."""
        mock_audience = FakeSDKObject({"id": "aud_1", "name": "Audience 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_custom_audiences.return_value = [mock_audience]
            MockAdAccount.return_value = mock_account

            await client.get_audiences("act_123")

            call_args = mock_account.get_custom_audiences.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "lookalike_spec",
                "rule",
                "data_source",
                "retention_days",
                "is_value_based",
                "sharing_status",
                "time_created",
                "time_updated",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in fields"

    @pytest.mark.asyncio
    async def test_get_audience_includes_v25_fields(
        self, client: MetaAdsClient
    ) -> None:
        """get_audience requests v25 audience fields."""
        mock = FakeSDKObject({"id": "aud_1", "name": "Audience 1"})
        mock.api_get = MagicMock()

        with patch("meta_ads_mcp.client.CustomAudience") as MockCustomAudience:
            MockCustomAudience.return_value = mock
            await client.get_audience("aud_1")

            call_args = mock.api_get.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "lookalike_spec",
                "rule",
                "data_source",
                "retention_days",
                "is_value_based",
                "sharing_status",
                "time_created",
                "time_updated",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in fields"

    @pytest.mark.asyncio
    async def test_get_campaigns_v25_fields(self, client: MetaAdsClient) -> None:
        """get_campaigns requests v25 campaign fields."""
        mock_campaign = FakeSDKObject({"id": "camp_1", "name": "Campaign 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_campaigns.return_value = [mock_campaign]
            MockAdAccount.return_value = mock_account

            await client.get_campaigns("act_123")

            call_args = mock_account.get_campaigns.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "bid_strategy",
                "spend_cap",
                "pacing_type",
                "buying_type",
                "special_ad_categories",
                "configured_status",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in campaign fields"

    @pytest.mark.asyncio
    async def test_get_campaign_v25_fields(self, client: MetaAdsClient) -> None:
        """get_campaign requests v25 campaign fields."""
        mock = FakeSDKObject({"id": "camp_1", "name": "Campaign 1"})
        mock.api_get = MagicMock()

        with patch("meta_ads_mcp.client.Campaign") as MockCampaign:
            MockCampaign.return_value = mock
            await client.get_campaign("camp_1")

            call_args = mock.api_get.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "bid_strategy",
                "spend_cap",
                "pacing_type",
                "buying_type",
                "special_ad_categories",
                "configured_status",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in campaign fields"

    @pytest.mark.asyncio
    async def test_get_ad_sets_v25_fields(self, client: MetaAdsClient) -> None:
        """get_ad_sets requests v25 ad set fields."""
        mock_adset = FakeSDKObject({"id": "adset_1", "name": "Ad Set 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_sets.return_value = [mock_adset]
            MockAdAccount.return_value = mock_account

            await client.get_ad_sets("act_123")

            call_args = mock_account.get_ad_sets.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "bid_amount",
                "bid_strategy",
                "destination_type",
                "frequency_control_specs",
                "attribution_spec",
                "is_dynamic_creative",
                "optimization_sub_event",
                "pacing_type",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in ad set fields"

    @pytest.mark.asyncio
    async def test_get_ad_set_v25_fields(self, client: MetaAdsClient) -> None:
        """get_ad_set requests v25 ad set fields."""
        mock = FakeSDKObject({"id": "adset_1", "name": "Ad Set 1"})
        mock.api_get = MagicMock()

        with patch("meta_ads_mcp.client.AdSet") as MockAdSet:
            MockAdSet.return_value = mock
            await client.get_ad_set("adset_1")

            call_args = mock.api_get.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "bid_amount",
                "bid_strategy",
                "destination_type",
                "frequency_control_specs",
                "attribution_spec",
                "is_dynamic_creative",
                "optimization_sub_event",
                "pacing_type",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in ad set fields"

    @pytest.mark.asyncio
    async def test_get_ads_v25_fields(self, client: MetaAdsClient) -> None:
        """get_ads requests v25 ad fields."""
        mock_ad = FakeSDKObject({"id": "ad_1", "name": "Ad 1"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ads.return_value = [mock_ad]
            MockAdAccount.return_value = mock_account

            await client.get_ads("act_123")

            call_args = mock_account.get_ads.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "configured_status",
                "tracking_specs",
                "conversion_specs",
                "preview_shareable_link",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in ad fields"

    @pytest.mark.asyncio
    async def test_get_ad_v25_fields(self, client: MetaAdsClient) -> None:
        """get_ad requests v25 ad fields."""
        mock = FakeSDKObject({"id": "ad_1", "name": "Ad 1"})
        mock.api_get = MagicMock()

        with patch("meta_ads_mcp.client.Ad") as MockAd:
            MockAd.return_value = mock
            await client.get_ad("ad_1")

            call_args = mock.api_get.call_args
            field_names = [str(f) for f in call_args.kwargs.get("fields", [])]
            for expected in [
                "configured_status",
                "tracking_specs",
                "conversion_specs",
                "preview_shareable_link",
            ]:
                assert any(
                    expected in name for name in field_names
                ), f"{expected} not in ad fields"
