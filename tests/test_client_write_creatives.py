"""Tests for MetaAdsClient creative write methods."""

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


class TestCreateAdCreative:
    """Tests for client.create_ad_creative."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Creates creative with correct params."""
        result_obj = FakeSDKObject({"id": "cr_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_creative.return_value = result_obj
            MockAdAccount.return_value = mock_account

            result = await client.create_ad_creative(
                name="Test Creative",
                object_story_spec={
                    "page_id": "page_123",
                    "link_data": {"link": "https://example.com"},
                },
                url_tags="utm_source=facebook",
            )

        assert result["id"] == "cr_new"
        call_params = mock_account.create_ad_creative.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Test Creative"
        assert params["object_story_spec"]["page_id"] == "page_123"
        assert params["url_tags"] == "utm_source=facebook"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only execution option."""
        result_obj = FakeSDKObject({"id": ""})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_creative.return_value = result_obj
            MockAdAccount.return_value = mock_account

            await client.create_ad_creative(
                name="Test",
                object_story_spec={"page_id": "page_123", "link_data": {}},
                dry_run=True,
            )

        call_params = mock_account.create_ad_creative.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Permission denied", code=200)

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_creative.side_effect = error
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Permission denied"):
                await client.create_ad_creative(
                    name="Fail",
                    object_story_spec={"page_id": "p", "link_data": {}},
                )


class TestUpdateAdCreative:
    """Tests for client.update_ad_creative."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Updates creative with correct params."""
        with patch("meta_ads_mcp.client.AdCreative") as MockAdCreative:
            mock_creative = MagicMock()
            mock_creative.api_update.return_value = FakeSDKObject({"success": True})
            MockAdCreative.return_value = mock_creative

            result = await client.update_ad_creative(
                creative_id="cr_1",
                name="Updated Creative",
                url_tags="utm_source=meta",
            )

        assert result == {"success": True}
        call_params = mock_creative.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["name"] == "Updated Creative"
        assert params["url_tags"] == "utm_source=meta"

    @pytest.mark.asyncio
    async def test_dry_run(self, client: MetaAdsClient) -> None:
        """Dry run adds validate_only."""
        with patch("meta_ads_mcp.client.AdCreative") as MockAdCreative:
            mock_creative = MagicMock()
            mock_creative.api_update.return_value = FakeSDKObject({})
            MockAdCreative.return_value = mock_creative

            await client.update_ad_creative(
                creative_id="cr_1",
                name="Test",
                dry_run=True,
            )

        call_params = mock_creative.api_update.call_args
        params = call_params.kwargs.get("params") or call_params[1]["params"]
        assert params["execution_options"] == ["validate_only"]

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """API errors are converted to MetaAdsError."""
        error = _make_sdk_error("Invalid creative", code=100)

        with patch("meta_ads_mcp.client.AdCreative") as MockAdCreative:
            mock_creative = MagicMock()
            mock_creative.api_update.side_effect = error
            MockAdCreative.return_value = mock_creative

            with pytest.raises(MetaAdsError, match="Invalid creative"):
                await client.update_ad_creative(creative_id="cr_bad", name="Fail")
