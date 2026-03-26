"""Tests for MetaAdsClient asset (image/video) methods."""

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

    def remote_create(self, **kwargs: Any) -> None:
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


# ── Upload Ad Image ──────────────────────────────────────────────────────


class TestUploadAdImage:
    """Tests for client.upload_ad_image."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient, tmp_path: Any) -> None:
        """Uploads image and returns dict with hash."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"\xff\xd8\xff\xe0")

        with patch("meta_ads_mcp.client.AdImage") as MockAdImage:
            mock_image = FakeSDKObject(
                {"hash": "abc123hash", "url": "https://example.com/img.jpg"}
            )
            MockAdImage.return_value = mock_image

            result = await client.upload_ad_image(file_path=str(test_file))

        assert result["hash"] == "abc123hash"

    @pytest.mark.asyncio
    async def test_with_name(self, client: MetaAdsClient, tmp_path: Any) -> None:
        """Sets name field on image."""
        test_file = tmp_path / "banner.jpg"
        test_file.write_bytes(b"\xff\xd8\xff\xe0")

        with patch("meta_ads_mcp.client.AdImage") as MockAdImage:
            mock_image = FakeSDKObject({"hash": "xyz789"})
            MockAdImage.return_value = mock_image

            await client.upload_ad_image(file_path=str(test_file), name="My Banner")

        # The name is set via AdImage.Field.name (a mock key), so check values
        assert "My Banner" in mock_image.values()

    @pytest.mark.asyncio
    async def test_file_not_found(self, client: MetaAdsClient) -> None:
        """Raises MetaAdsError when file does not exist."""
        with pytest.raises(MetaAdsError, match="File not found"):
            await client.upload_ad_image(file_path="/nonexistent/image.jpg")

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient, tmp_path: Any) -> None:
        """Converts SDK error to MetaAdsError."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"\xff\xd8\xff\xe0")

        with patch("meta_ads_mcp.client.AdImage") as MockAdImage:
            mock_image = MagicMock()
            mock_image.remote_create.side_effect = _make_sdk_error("Upload failed")
            MockAdImage.return_value = mock_image

            with pytest.raises(MetaAdsError, match="Upload failed"):
                await client.upload_ad_image(file_path=str(test_file))


# ── Upload Ad Video ──────────────────────────────────────────────────────


class TestUploadAdVideo:
    """Tests for client.upload_ad_video."""

    @pytest.mark.asyncio
    async def test_success_file(self, client: MetaAdsClient, tmp_path: Any) -> None:
        """Uploads video from file path."""
        test_file = tmp_path / "video.mp4"
        test_file.write_bytes(b"\x00\x00\x00\x20")

        result_obj = FakeSDKObject({"id": "vid_new"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_video.return_value = result_obj
            mock_account.get_id.return_value = "act_123456"
            MockAdAccount.return_value = mock_account

            result = await client.upload_ad_video(file_path=str(test_file))

        assert result["id"] == "vid_new"
        call_params = mock_account.create_ad_video.call_args
        params = call_params.kwargs.get("params") or call_params[1].get("params", {})
        assert params.get("filepath") == str(test_file)

    @pytest.mark.asyncio
    async def test_success_url(self, client: MetaAdsClient) -> None:
        """Uploads video from URL."""
        result_obj = FakeSDKObject({"id": "vid_url"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_video.return_value = result_obj
            mock_account.get_id.return_value = "act_123456"
            MockAdAccount.return_value = mock_account

            result = await client.upload_ad_video(
                file_url="https://example.com/video.mp4"
            )

        assert result["id"] == "vid_url"
        call_params = mock_account.create_ad_video.call_args
        params = call_params.kwargs.get("params") or call_params[1].get("params", {})
        assert params.get("file_url") == "https://example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_no_source_error(self, client: MetaAdsClient) -> None:
        """Raises MetaAdsError when neither file_path nor file_url given."""
        with pytest.raises(MetaAdsError, match="file_path or file_url"):
            await client.upload_ad_video()

    @pytest.mark.asyncio
    async def test_file_not_found(self, client: MetaAdsClient) -> None:
        """Raises MetaAdsError when file does not exist."""
        with pytest.raises(MetaAdsError, match="File not found"):
            await client.upload_ad_video(file_path="/nonexistent/video.mp4")

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """Converts SDK error to MetaAdsError."""
        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.create_ad_video.side_effect = _make_sdk_error(
                "Video upload failed"
            )
            mock_account.get_id.return_value = "act_123456"
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="Video upload failed"):
                await client.upload_ad_video(file_url="https://example.com/video.mp4")


# ── Get Ad Images ────────────────────────────────────────────────────────


class TestGetAdImages:
    """Tests for client.get_ad_images."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns list of image dicts."""
        images = [
            FakeSDKObject({"hash": "h1", "name": "img1"}),
            FakeSDKObject({"hash": "h2", "name": "img2"}),
        ]

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_images.return_value = iter(images)
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_images()

        assert len(result) == 2
        assert result[0]["hash"] == "h1"
        assert result[1]["hash"] == "h2"

    @pytest.mark.asyncio
    async def test_empty(self, client: MetaAdsClient) -> None:
        """Returns empty list when no images."""
        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_images.return_value = iter([])
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_images()

        assert result == []


# ── Get Ad Image ─────────────────────────────────────────────────────────


class TestGetAdImage:
    """Tests for client.get_ad_image."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns image dict by hash."""
        image = FakeSDKObject({"hash": "abc123", "name": "Banner"})

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_images.return_value = [image]
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_image(image_hash="abc123")

        assert result["hash"] == "abc123"
        call_params = mock_account.get_ad_images.call_args
        params = call_params.kwargs.get("params") or call_params[1].get("params", {})
        assert params["hashes"] == ["abc123"]

    @pytest.mark.asyncio
    async def test_not_found(self, client: MetaAdsClient) -> None:
        """Raises MetaAdsError when hash not found."""
        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_images.return_value = []
            MockAdAccount.return_value = mock_account

            with pytest.raises(MetaAdsError, match="No image found"):
                await client.get_ad_image(image_hash="nonexistent")


# ── Get Ad Videos ────────────────────────────────────────────────────────


class TestGetAdVideos:
    """Tests for client.get_ad_videos."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns list of video dicts."""
        videos = [
            FakeSDKObject({"id": "v1", "title": "Video 1"}),
            FakeSDKObject({"id": "v2", "title": "Video 2"}),
        ]

        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_videos.return_value = iter(videos)
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_videos()

        assert len(result) == 2
        assert result[0]["id"] == "v1"

    @pytest.mark.asyncio
    async def test_empty(self, client: MetaAdsClient) -> None:
        """Returns empty list when no videos."""
        with patch("meta_ads_mcp.client.AdAccount") as MockAdAccount:
            mock_account = MagicMock()
            mock_account.get_ad_videos.return_value = iter([])
            MockAdAccount.return_value = mock_account

            result = await client.get_ad_videos()

        assert result == []


# ── Get Ad Video ─────────────────────────────────────────────────────────


class TestGetAdVideo:
    """Tests for client.get_ad_video."""

    @pytest.mark.asyncio
    async def test_success(self, client: MetaAdsClient) -> None:
        """Returns video dict by ID."""
        with patch("meta_ads_mcp.client.AdVideo") as MockAdVideo:
            mock_video = FakeSDKObject(
                {"id": "vid_789", "title": "Promo", "length": 30.0}
            )
            MockAdVideo.return_value = mock_video

            result = await client.get_ad_video(video_id="vid_789")

        assert result["id"] == "vid_789"
        assert result["title"] == "Promo"

    @pytest.mark.asyncio
    async def test_api_error(self, client: MetaAdsClient) -> None:
        """Converts SDK error to MetaAdsError."""
        with patch("meta_ads_mcp.client.AdVideo") as MockAdVideo:
            mock_video = MagicMock()
            mock_video.api_get.side_effect = _make_sdk_error("Not found")
            MockAdVideo.return_value = mock_video

            with pytest.raises(MetaAdsError, match="Not found"):
                await client.get_ad_video(video_id="bad_id")
