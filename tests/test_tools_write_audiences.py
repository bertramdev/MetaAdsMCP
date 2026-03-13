"""Tests for audience write tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.audiences import (
    create_custom_audience,
    create_lookalike_audience,
)


class TestCreateCustomAudience:
    """Tests for create_custom_audience tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates custom audience and returns formatted result."""
        mock_client.create_custom_audience.return_value = {"id": "aud_new"}

        result = await create_custom_audience(
            mock_context,
            name="Website Visitors",
            subtype="WEBSITE",
        )

        assert "Audience Created" in result
        assert "Website Visitors" in result
        assert "WEBSITE" in result
        mock_client.create_custom_audience.assert_called_once_with(
            name="Website Visitors",
            subtype="WEBSITE",
            account_id=None,
            description=None,
            rule=None,
            pixel_id=None,
            retention_days=None,
            customer_file_source=None,
            prefill=None,
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_with_rule(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Parses JSON rule string and passes as dict."""
        mock_client.create_custom_audience.return_value = {"id": "aud_new"}

        result = await create_custom_audience(
            mock_context,
            name="Rule Audience",
            subtype="WEBSITE",
            rule='{"inclusions": {"operator": "or"}}',
        )

        assert "Rule Audience" in result
        call_kwargs = mock_client.create_custom_audience.call_args.kwargs
        assert call_kwargs["rule"] == {"inclusions": {"operator": "or"}}

    @pytest.mark.asyncio
    async def test_with_pixel_and_retention(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes pixel_id and retention_days to client."""
        mock_client.create_custom_audience.return_value = {"id": "aud_new"}

        await create_custom_audience(
            mock_context,
            name="Pixel Audience",
            subtype="WEBSITE",
            pixel_id="px_123",
            retention_days=30,
        )

        call_kwargs = mock_client.create_custom_audience.call_args.kwargs
        assert call_kwargs["pixel_id"] == "px_123"
        assert call_kwargs["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_custom_audience.return_value = {"id": ""}

        result = await create_custom_audience(
            mock_context,
            name="Dry Run Audience",
            subtype="CUSTOM",
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.create_custom_audience.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """API error returns formatted error."""
        mock_client.create_custom_audience.side_effect = MetaAdsError(
            "Invalid audience"
        )

        result = await create_custom_audience(
            mock_context,
            name="Fail",
            subtype="CUSTOM",
        )

        assert "## Error" in result
        assert "Invalid audience" in result


class TestCreateLookalikeAudience:
    """Tests for create_lookalike_audience tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Creates lookalike audience and returns formatted result."""
        mock_client.create_lookalike_audience.return_value = {"id": "aud_lal"}

        result = await create_lookalike_audience(
            mock_context,
            name="US Lookalike",
            origin_audience_id="aud_source",
            country="US",
            ratio=0.01,
        )

        assert "Audience Created" in result
        assert "US Lookalike" in result
        assert "LOOKALIKE" in result
        mock_client.create_lookalike_audience.assert_called_once_with(
            name="US Lookalike",
            origin_audience_id="aud_source",
            country="US",
            ratio=0.01,
            account_id=None,
            description=None,
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_ratio_validation_too_low(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Ratio below 0.01 returns error."""
        result = await create_lookalike_audience(
            mock_context,
            name="Bad Ratio",
            origin_audience_id="aud_source",
            country="US",
            ratio=0.005,
        )

        assert "## Error" in result
        assert "Ratio must be between" in result
        mock_client.create_lookalike_audience.assert_not_called()

    @pytest.mark.asyncio
    async def test_ratio_validation_too_high(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Ratio above 0.20 returns error."""
        result = await create_lookalike_audience(
            mock_context,
            name="Bad Ratio",
            origin_audience_id="aud_source",
            country="US",
            ratio=0.25,
        )

        assert "## Error" in result
        assert "Ratio must be between" in result
        mock_client.create_lookalike_audience.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Dry run shows dry run message."""
        mock_client.create_lookalike_audience.return_value = {"id": ""}

        result = await create_lookalike_audience(
            mock_context,
            name="Dry Run LAL",
            origin_audience_id="aud_source",
            country="US",
            ratio=0.05,
            dry_run=True,
        )

        assert "Dry run" in result
        call_kwargs = mock_client.create_lookalike_audience.call_args.kwargs
        assert call_kwargs["dry_run"] is True

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """API error returns formatted error."""
        mock_client.create_lookalike_audience.side_effect = MetaAdsError(
            "Source audience not found"
        )

        result = await create_lookalike_audience(
            mock_context,
            name="Fail",
            origin_audience_id="aud_bad",
            country="US",
            ratio=0.01,
        )

        assert "## Error" in result
        assert "Source audience not found" in result
