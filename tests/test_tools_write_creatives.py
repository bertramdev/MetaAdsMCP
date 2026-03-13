"""Tests for creative write tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.creatives import create_ad_creative, update_ad_creative


class TestCreateAdCreative:
    """Tests for create_ad_creative tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates creative and returns formatted result."""
        mock_client.create_ad_creative.return_value = {"id": "cr_new"}

        result = await create_ad_creative(
            mock_context,
            name="Spring Ad Creative",
            page_id="page_123",
            link="https://example.com/spring",
            message="Check out our spring sale!",
            headline="Spring Sale",
            call_to_action_type="LEARN_MORE",
        )

        assert "Creative Created" in result
        assert "Spring Ad Creative" in result
        assert "LEARN_MORE" in result
        mock_client.create_ad_creative.assert_called_once()
        call_kwargs = mock_client.create_ad_creative.call_args.kwargs
        assert call_kwargs["name"] == "Spring Ad Creative"
        spec = call_kwargs["object_story_spec"]
        assert spec["page_id"] == "page_123"
        assert spec["link_data"]["link"] == "https://example.com/spring"
        assert spec["link_data"]["message"] == "Check out our spring sale!"
        assert spec["link_data"]["name"] == "Spring Sale"
        assert spec["link_data"]["call_to_action"]["type"] == "LEARN_MORE"

    @pytest.mark.asyncio
    async def test_with_image_hash(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Image hash is included in link_data."""
        mock_client.create_ad_creative.return_value = {"id": "cr_new"}

        await create_ad_creative(
            mock_context,
            name="Image Hash Creative",
            page_id="page_123",
            link="https://example.com",
            image_hash="abc123hash",
        )

        call_kwargs = mock_client.create_ad_creative.call_args.kwargs
        spec = call_kwargs["object_story_spec"]
        assert spec["link_data"]["image_hash"] == "abc123hash"
        assert "picture" not in spec["link_data"]

    @pytest.mark.asyncio
    async def test_with_image_url(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Image URL is included as picture in link_data."""
        mock_client.create_ad_creative.return_value = {"id": "cr_new"}

        await create_ad_creative(
            mock_context,
            name="Image URL Creative",
            page_id="page_123",
            link="https://example.com",
            image_url="https://example.com/image.jpg",
        )

        call_kwargs = mock_client.create_ad_creative.call_args.kwargs
        spec = call_kwargs["object_story_spec"]
        assert spec["link_data"]["picture"] == "https://example.com/image.jpg"
        assert "image_hash" not in spec["link_data"]

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_ad_creative.return_value = {"id": ""}

        result = await create_ad_creative(
            mock_context,
            name="Test",
            page_id="page_123",
            link="https://example.com",
            dry_run=True,
        )

        assert "Dry run" in result
        mock_client.create_ad_creative.assert_called_once()
        call_kwargs = mock_client.create_ad_creative.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """API error returns formatted error."""
        mock_client.create_ad_creative.side_effect = MetaAdsError("Permission denied")

        result = await create_ad_creative(
            mock_context,
            name="Fail",
            page_id="page_123",
            link="https://example.com",
        )

        assert "## Error" in result
        assert "Permission denied" in result


class TestUpdateAdCreative:
    """Tests for update_ad_creative tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Name change shows before/after in changes table."""
        mock_client.get_creative.return_value = {
            "id": "cr_1",
            "name": "Old Creative",
            "title": "Old Title",
            "body": "Old Body",
            "call_to_action_type": "LEARN_MORE",
            "link_url": "https://example.com",
        }
        mock_client.update_ad_creative.return_value = {}

        result = await update_ad_creative(
            mock_context,
            creative_id="cr_1",
            name="New Creative",
        )

        assert "Creative Updated" in result
        assert "Old Creative" in result
        assert "New Creative" in result

    @pytest.mark.asyncio
    async def test_status_validation(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid status returns error without calling API."""
        result = await update_ad_creative(
            mock_context,
            creative_id="cr_1",
            status="DELETED",
        )

        assert "## Error" in result
        assert "Invalid status" in result
        mock_client.update_ad_creative.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.get_creative.return_value = {
            "id": "cr_1",
            "name": "My Creative",
            "title": "",
            "body": "",
            "call_to_action_type": "",
            "link_url": "https://example.com",
        }
        mock_client.update_ad_creative.return_value = {}

        result = await update_ad_creative(
            mock_context,
            creative_id="cr_1",
            name="Updated",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.update_ad_creative.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """API error returns formatted error."""
        mock_client.get_creative.return_value = {
            "id": "cr_1",
            "name": "My Creative",
            "title": "",
            "body": "",
            "call_to_action_type": "",
            "link_url": "https://example.com",
        }
        mock_client.update_ad_creative.side_effect = MetaAdsError("Creative not found")

        result = await update_ad_creative(
            mock_context,
            creative_id="cr_1",
            name="Fail",
        )

        assert "## Error" in result
        assert "Creative not found" in result
