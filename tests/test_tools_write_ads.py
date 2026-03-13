"""Tests for ad write tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.ads import create_ad, update_ad_status


class TestCreateAd:
    """Tests for create_ad tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates ad and returns formatted result."""
        mock_client.create_ad.return_value = {"id": "ad_new"}

        result = await create_ad(
            mock_context,
            name="Test Ad",
            adset_id="adset_1",
            creative_id="cr_1",
        )

        assert "Ad Created" in result
        assert "PAUSED" in result
        assert "Test Ad" in result
        mock_client.create_ad.assert_called_once_with(
            name="Test Ad",
            adset_id="adset_1",
            creative_id="cr_1",
            account_id=None,
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_creative_id_in_result(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creative ID appears in formatted output."""
        mock_client.create_ad.return_value = {"id": "ad_new"}

        result = await create_ad(
            mock_context,
            name="Creative Ad",
            adset_id="adset_1",
            creative_id="cr_456",
        )

        assert "cr_456" in result

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_ad.return_value = {"id": ""}

        result = await create_ad(
            mock_context,
            name="Dry Run Ad",
            adset_id="adset_1",
            creative_id="cr_1",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.create_ad.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_with_account_id(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Account ID is passed to client."""
        mock_client.create_ad.return_value = {"id": "ad_new"}

        await create_ad(
            mock_context,
            name="Ad With Account",
            adset_id="adset_1",
            creative_id="cr_1",
            account_id="act_999",
        )

        call_kwargs = mock_client.create_ad.call_args.kwargs
        assert call_kwargs["account_id"] == "act_999"

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.create_ad.side_effect = MetaAdsError("Invalid creative")

        result = await create_ad(
            mock_context,
            name="Fail",
            adset_id="adset_1",
            creative_id="cr_bad",
        )

        assert "## Error" in result
        assert "Invalid creative" in result


class TestUpdateAdStatus:
    """Tests for update_ad_status tool."""

    @pytest.mark.asyncio
    async def test_pause(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Pausing an ad shows status change."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.return_value = {}

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="PAUSED",
        )

        assert "Ad Updated" in result
        assert "ACTIVE" in result
        assert "PAUSED" in result

    @pytest.mark.asyncio
    async def test_activate(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Activating an ad shows status change."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "PAUSED",
            "effective_status": "PAUSED",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.return_value = {}

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="ACTIVE",
        )

        assert "Ad Updated" in result
        mock_client.update_ad.assert_called_once_with(
            ad_id="ad_1",
            status="ACTIVE",
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_archive(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Archiving an ad works."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "PAUSED",
            "effective_status": "PAUSED",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.return_value = {}

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="ARCHIVED",
        )

        assert "ARCHIVED" in result

    @pytest.mark.asyncio
    async def test_invalid_status_rejected(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Invalid status returns error without calling API."""
        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="DELETED",
        )

        assert "## Error" in result
        assert "Invalid status" in result
        mock_client.update_ad.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.return_value = {}

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="PAUSED",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.update_ad.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_api_error(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """API error returns formatted error."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.side_effect = MetaAdsError("Ad not found")

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="PAUSED",
        )

        assert "## Error" in result
        assert "Ad not found" in result

    @pytest.mark.asyncio
    async def test_case_insensitive_status(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Status is case-insensitive."""
        mock_client.get_ad.return_value = {
            "id": "ad_1",
            "name": "My Ad",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "adset_id": "adset_1",
            "campaign_id": "camp_1",
            "creative": {"id": "cr_1"},
        }
        mock_client.update_ad.return_value = {}

        result = await update_ad_status(
            mock_context,
            ad_id="ad_1",
            status="paused",
        )

        assert "PAUSED" in result
        call_kwargs = mock_client.update_ad.call_args.kwargs
        assert call_kwargs["status"] == "PAUSED"
