"""Tests for audience tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.audiences import get_audience, list_audiences


class TestListAudiences:
    """Tests for list_audiences tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted audience list."""
        mock_client.get_audiences.return_value = [
            {
                "id": "aud_1",
                "name": "Website Visitors",
                "subtype": "CUSTOM",
                "approximate_count_lower_bound": 10000,
                "approximate_count_upper_bound": 15000,
                "description": "Last 30 day visitors",
            },
        ]

        result = await list_audiences(mock_context)

        assert "## Custom Audiences" in result
        assert "Website Visitors" in result
        assert "CUSTOM" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no audiences."""
        mock_client.get_audiences.return_value = []

        result = await list_audiences(mock_context)

        assert "No audiences found" in result

    @pytest.mark.asyncio
    async def test_params(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes parameters to client."""
        mock_client.get_audiences.return_value = []

        await list_audiences(mock_context, account_id="act_123", limit=10)

        mock_client.get_audiences.assert_called_once_with(
            account_id="act_123", limit=10
        )

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_audiences.side_effect = MetaAdsError("Forbidden")

        result = await list_audiences(mock_context)

        assert "## Error" in result
        assert "Forbidden" in result


class TestGetAudience:
    """Tests for get_audience tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted audience detail."""
        mock_client.get_audience.return_value = {
            "id": "aud_123",
            "name": "Lookalike US 1%",
            "subtype": "LOOKALIKE",
            "approximate_count_lower_bound": 2000000,
            "approximate_count_upper_bound": 2500000,
            "delivery_status": {"status": "ready"},
            "operation_status": {"status": "normal"},
            "description": "Top 1% lookalike from website visitors",
        }

        result = await get_audience(mock_context, audience_id="aud_123")

        assert "## Audience: Lookalike US 1%" in result
        assert "LOOKALIKE" in result
        assert "2,000,000 - 2,500,000" in result
        assert "ready" in result
        mock_client.get_audience.assert_called_once_with("aud_123")

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_audience.side_effect = MetaAdsError("Audience not found")

        result = await get_audience(mock_context, audience_id="aud_bad")

        assert "## Error" in result
        assert "Audience not found" in result
