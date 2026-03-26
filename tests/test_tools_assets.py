"""Tests for asset management tools (image and video upload/listing)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.assets import (
    get_ad_image,
    get_ad_video,
    list_ad_images,
    list_ad_videos,
    upload_ad_image,
    upload_ad_video,
)

# ── Upload Ad Image ──────────────────────────────────────────────────────


class TestUploadAdImage:
    """Tests for upload_ad_image tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Uploads image and returns formatted result with hash."""
        mock_client.upload_ad_image.return_value = {
            "id": "act_123:abc123hash",
            "hash": "abc123hash",
            "name": "banner.jpg",
            "url": "https://scontent.xx.fbcdn.net/image.jpg",
            "width": 1200,
            "height": 628,
            "status": "active",
        }

        result = await upload_ad_image(
            mock_context,
            file_path="/tmp/banner.jpg",
            name="banner.jpg",
        )

        assert "Ad Image Uploaded" in result
        assert "abc123hash" in result
        assert "1200x628" in result
        assert "create_ad_creative" in result
        mock_client.upload_ad_image.assert_called_once_with(
            file_path="/tmp/banner.jpg",
            name="banner.jpg",
            account_id=None,
        )

    @pytest.mark.asyncio
    async def test_with_account_id(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes account_id to client."""
        mock_client.upload_ad_image.return_value = {
            "hash": "xyz789",
            "name": "test.png",
        }

        await upload_ad_image(
            mock_context,
            file_path="/tmp/test.png",
            account_id="act_999",
        )

        mock_client.upload_ad_image.assert_called_once_with(
            file_path="/tmp/test.png",
            name=None,
            account_id="act_999",
        )

    @pytest.mark.asyncio
    async def test_file_not_found(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error when file not found."""
        mock_client.upload_ad_image.side_effect = MetaAdsError(
            "File not found: /tmp/missing.jpg"
        )

        result = await upload_ad_image(mock_context, file_path="/tmp/missing.jpg")

        assert "## Error" in result
        assert "File not found" in result

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error on API failure."""
        mock_client.upload_ad_image.side_effect = MetaAdsError("Permission denied")

        result = await upload_ad_image(mock_context, file_path="/tmp/test.jpg")

        assert "## Error" in result
        assert "Permission denied" in result


# ── Upload Ad Video ──────────────────────────────────────────────────────


class TestUploadAdVideo:
    """Tests for upload_ad_video tool."""

    @pytest.mark.asyncio
    async def test_success_file_path(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Uploads video from file path and returns formatted result."""
        mock_client.upload_ad_video.return_value = {
            "id": "vid_123",
            "name": "promo.mp4",
            "title": "Spring Promo",
            "length": 30.5,
        }

        result = await upload_ad_video(
            mock_context,
            file_path="/tmp/promo.mp4",
            name="promo.mp4",
            title="Spring Promo",
        )

        assert "Ad Video Uploaded" in result
        assert "vid_123" in result
        assert "30s" in result
        mock_client.upload_ad_video.assert_called_once_with(
            file_path="/tmp/promo.mp4",
            file_url=None,
            name="promo.mp4",
            title="Spring Promo",
            description=None,
            account_id=None,
        )

    @pytest.mark.asyncio
    async def test_success_file_url(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Uploads video from URL."""
        mock_client.upload_ad_video.return_value = {
            "id": "vid_456",
            "title": "URL Video",
        }

        result = await upload_ad_video(
            mock_context,
            file_url="https://example.com/video.mp4",
        )

        assert "Ad Video Uploaded" in result
        assert "vid_456" in result
        mock_client.upload_ad_video.assert_called_once_with(
            file_path=None,
            file_url="https://example.com/video.mp4",
            name=None,
            title=None,
            description=None,
            account_id=None,
        )

    @pytest.mark.asyncio
    async def test_no_source_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error when neither file_path nor file_url provided."""
        mock_client.upload_ad_video.side_effect = MetaAdsError(
            "Either file_path or file_url must be provided."
        )

        result = await upload_ad_video(mock_context)

        assert "## Error" in result
        assert "file_path" in result
        assert "file_url" in result

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns error on API failure."""
        mock_client.upload_ad_video.side_effect = MetaAdsError("Upload failed")

        result = await upload_ad_video(mock_context, file_path="/tmp/video.mp4")

        assert "## Error" in result
        assert "Upload failed" in result


# ── List Ad Images ───────────────────────────────────────────────────────


class TestListAdImages:
    """Tests for list_ad_images tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted image list."""
        mock_client.get_ad_images.return_value = [
            {
                "hash": "hash1",
                "name": "Banner",
                "width": 1200,
                "height": 628,
                "status": "active",
                "created_time": "2025-01-01T00:00:00+0000",
            },
            {
                "hash": "hash2",
                "name": "Logo",
                "width": 512,
                "height": 512,
                "status": "active",
                "created_time": "2025-01-02T00:00:00+0000",
            },
        ]

        result = await list_ad_images(mock_context)

        assert "## Ad Images" in result
        assert "hash1" in result
        assert "Banner" in result
        assert "1200x628" in result
        assert "hash2" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns message when no images found."""
        mock_client.get_ad_images.return_value = []

        result = await list_ad_images(mock_context)

        assert "No ad images found" in result

    @pytest.mark.asyncio
    async def test_params(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes parameters to client."""
        mock_client.get_ad_images.return_value = []

        await list_ad_images(mock_context, account_id="act_123", limit=10)

        mock_client.get_ad_images.assert_called_once_with(
            account_id="act_123", limit=10
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_images.side_effect = MetaAdsError("Access denied")

        result = await list_ad_images(mock_context)

        assert "## Error" in result
        assert "Access denied" in result


# ── Get Ad Image ─────────────────────────────────────────────────────────


class TestGetAdImage:
    """Tests for get_ad_image tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted image detail."""
        mock_client.get_ad_image.return_value = {
            "id": "act_123:abc123",
            "hash": "abc123",
            "name": "Banner Ad",
            "width": 1200,
            "height": 628,
            "status": "active",
            "url": "https://scontent.xx.fbcdn.net/image.jpg",
        }

        result = await get_ad_image(mock_context, image_hash="abc123")

        assert "abc123" in result
        assert "Banner Ad" in result
        assert "1200x628" in result
        mock_client.get_ad_image.assert_called_once_with(
            image_hash="abc123", account_id=None
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_image.side_effect = MetaAdsError(
            "No image found with hash: bad_hash"
        )

        result = await get_ad_image(mock_context, image_hash="bad_hash")

        assert "## Error" in result
        assert "No image found" in result


# ── List Ad Videos ───────────────────────────────────────────────────────


class TestListAdVideos:
    """Tests for list_ad_videos tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted video list."""
        mock_client.get_ad_videos.return_value = [
            {
                "id": "vid_1",
                "name": "Spring Ad",
                "title": "Spring Sale",
                "length": 30.0,
                "created_time": "2025-01-01T00:00:00+0000",
            },
            {
                "id": "vid_2",
                "name": "Summer Ad",
                "title": "Summer Deal",
                "length": 90.0,
                "created_time": "2025-02-01T00:00:00+0000",
            },
        ]

        result = await list_ad_videos(mock_context)

        assert "## Ad Videos" in result
        assert "vid_1" in result
        assert "Spring Sale" in result
        assert "vid_2" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns message when no videos found."""
        mock_client.get_ad_videos.return_value = []

        result = await list_ad_videos(mock_context)

        assert "No ad videos found" in result

    @pytest.mark.asyncio
    async def test_params(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes parameters to client."""
        mock_client.get_ad_videos.return_value = []

        await list_ad_videos(mock_context, account_id="act_456", limit=25)

        mock_client.get_ad_videos.assert_called_once_with(
            account_id="act_456", limit=25
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_videos.side_effect = MetaAdsError("Rate limit")

        result = await list_ad_videos(mock_context)

        assert "## Error" in result
        assert "Rate limit" in result


# ── Get Ad Video ─────────────────────────────────────────────────────────


class TestGetAdVideo:
    """Tests for get_ad_video tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted video detail."""
        mock_client.get_ad_video.return_value = {
            "id": "vid_789",
            "name": "Promo Video",
            "title": "Big Promo",
            "description": "Our biggest promo yet",
            "length": 65.0,
            "source": "https://video.xx.fbcdn.net/video.mp4",
            "picture": "https://scontent.xx.fbcdn.net/thumb.jpg",
        }

        result = await get_ad_video(mock_context, video_id="vid_789")

        assert "vid_789" in result
        assert "Promo Video" in result
        assert "1m 5s" in result
        assert "object_story_spec" in result
        mock_client.get_ad_video.assert_called_once_with("vid_789")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_video.side_effect = MetaAdsError("Not found")

        result = await get_ad_video(mock_context, video_id="bad_id")

        assert "## Error" in result
        assert "Not found" in result
