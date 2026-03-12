"""Tests for account tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.tools.accounts import get_account_info, get_ad_accounts


class TestGetAdAccounts:
    """Tests for get_ad_accounts tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted account list."""
        mock_client.get_ad_accounts.return_value = [
            {
                "id": "act_111",
                "name": "Account One",
                "account_status": 1,
                "currency": "USD",
                "timezone_name": "America/New_York",
                "amount_spent": "50000",
            },
            {
                "id": "act_222",
                "name": "Account Two",
                "account_status": 2,
                "currency": "EUR",
                "amount_spent": "10000",
            },
        ]

        result = await get_ad_accounts(mock_context)

        assert "## Ad Accounts" in result
        assert "act_111" in result
        assert "Account One" in result
        assert "act_222" in result

    @pytest.mark.asyncio
    async def test_empty(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns empty message when no accounts."""
        mock_client.get_ad_accounts.return_value = []

        result = await get_ad_accounts(mock_context)

        assert "No ad accounts found" in result

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_ad_accounts.side_effect = MetaAdsError("Invalid token")

        result = await get_ad_accounts(mock_context)

        assert "## Error" in result
        assert "Invalid token" in result


class TestGetAccountInfo:
    """Tests for get_account_info tool."""

    @pytest.mark.asyncio
    async def test_success(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Returns formatted account detail."""
        mock_client.get_account_info.return_value = {
            "id": "act_123",
            "name": "My Agency Account",
            "account_status": 1,
            "currency": "USD",
            "timezone_name": "America/New_York",
            "amount_spent": "150000",
            "balance": "5000",
            "spend_cap": "1000000",
        }

        result = await get_account_info(mock_context, account_id="act_123")

        assert "## Ad Account: My Agency Account" in result
        assert "act_123" in result
        assert "$1,500.00" in result
        mock_client.get_account_info.assert_called_once_with("act_123")

    @pytest.mark.asyncio
    async def test_default_account(
        self, mock_context: MagicMock, mock_client: AsyncMock
    ) -> None:
        """Passes None when no account_id given."""
        mock_client.get_account_info.return_value = {
            "id": "act_default",
            "name": "Default",
            "account_status": 1,
        }

        await get_account_info(mock_context)

        mock_client.get_account_info.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_error(self, mock_context: MagicMock, mock_client: AsyncMock) -> None:
        """Returns error on API failure."""
        mock_client.get_account_info.side_effect = MetaAdsError("Not found")

        result = await get_account_info(mock_context, account_id="act_bad")

        assert "## Error" in result
        assert "Not found" in result
