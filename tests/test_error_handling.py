"""Tests for error handling enhancements."""

from unittest.mock import MagicMock, patch

import pytest

from meta_ads_mcp.client import META_ERROR_HINTS, MetaAdsError
from meta_ads_mcp.formatting import format_error
from meta_ads_mcp.tools._write_helpers import format_write_error


class TestMetaAdsErrorHint:
    """Tests for MetaAdsError.hint property."""

    def test_known_rate_limit_code(self) -> None:
        """Error code 17 returns rate limit hint."""
        err = MetaAdsError("Too many calls", error_code=17)
        assert "Rate limit" in err.hint

    def test_known_token_expired_code(self) -> None:
        """Error code 190 returns token hint."""
        err = MetaAdsError("Invalid token", error_code=190)
        assert "expired" in err.hint or "invalid" in err.hint

    def test_known_permission_code(self) -> None:
        """Error code 200 returns permission hint."""
        err = MetaAdsError("No permission", error_code=200)
        assert "Permission denied" in err.hint

    def test_known_invalid_param_code(self) -> None:
        """Error code 100 without error_user_msg returns generic hint."""
        err = MetaAdsError("Bad param", error_code=100)
        assert "Invalid parameter" in err.hint

    def test_known_temporary_code(self) -> None:
        """Error code 2 returns temporary issue hint."""
        err = MetaAdsError("API issue", error_code=2)
        assert "Temporary" in err.hint

    def test_unknown_code_returns_empty(self) -> None:
        """Unknown error code returns empty hint."""
        err = MetaAdsError("Unknown", error_code=99999)
        assert err.hint == ""

    def test_no_code_returns_empty(self) -> None:
        """No error code returns empty hint."""
        err = MetaAdsError("No code")
        assert err.hint == ""

    def test_all_hint_codes_covered(self) -> None:
        """Every code in META_ERROR_HINTS produces a non-empty hint."""
        for code in META_ERROR_HINTS:
            err = MetaAdsError("test", error_code=code)
            assert err.hint, f"No hint for code {code}"

    def test_error_user_msg_takes_priority(self) -> None:
        """error_user_msg is preferred over generic hint lookup."""
        err = MetaAdsError(
            "Invalid parameter",
            error_code=100,
            error_user_msg="Ad set requires a daily or lifetime budget.",
        )
        assert err.hint == "Ad set requires a daily or lifetime budget."

    def test_error_user_msg_empty_falls_back(self) -> None:
        """Empty error_user_msg falls back to META_ERROR_HINTS."""
        err = MetaAdsError("Invalid parameter", error_code=100, error_user_msg="")
        assert "Invalid parameter" in err.hint

    def test_blame_field_specs_stored(self) -> None:
        """blame_field_specs are stored on the error."""
        err = MetaAdsError(
            "Bad param",
            error_code=100,
            blame_field_specs=["daily_budget", "lifetime_budget"],
        )
        assert err.blame_field_specs == ["daily_budget", "lifetime_budget"]


class TestFormatError:
    """Tests for enhanced format_error function."""

    def test_basic_message_only(self) -> None:
        """Backward-compatible: message only."""
        result = format_error("Something went wrong")
        assert "## Error" in result
        assert "Something went wrong" in result
        assert "Error Code" not in result
        assert "Suggestion" not in result

    def test_with_error_code(self) -> None:
        """Includes error code when provided."""
        result = format_error("Bad request", error_code=100)
        assert "**Error Code**: 100" in result

    def test_with_hint(self) -> None:
        """Includes suggestion when provided."""
        result = format_error("Rate limit", hint="Wait and retry.")
        assert "**Suggestion**: Wait and retry." in result

    def test_with_code_and_hint(self) -> None:
        """Includes both code and suggestion."""
        result = format_error("Rate limit", error_code=17, hint="Wait a few minutes.")
        assert "**Error Code**: 17" in result
        assert "**Suggestion**: Wait a few minutes." in result

    def test_with_blame_fields(self) -> None:
        """Includes blame fields when provided."""
        result = format_error(
            "Invalid parameter",
            error_code=100,
            blame_fields=["daily_budget", "lifetime_budget"],
        )
        assert "**Problem Fields**: daily_budget, lifetime_budget" in result

    def test_with_error_subcode(self) -> None:
        """Includes subcode when provided."""
        result = format_error("Bad param", error_code=100, error_subcode=1885024)
        assert "**Error Code**: 100 (subcode: 1885024)" in result

    def test_no_blame_fields_when_none(self) -> None:
        """No Problem Fields line when blame_fields is None."""
        result = format_error("Bad request", error_code=100)
        assert "Problem Fields" not in result


class TestFormatWriteError:
    """Tests for enhanced format_write_error function."""

    def test_meta_ads_error_with_code(self) -> None:
        """MetaAdsError passes code and hint to format_error."""
        err = MetaAdsError("Rate limit hit", error_code=17)
        result = format_write_error(err)
        assert "Rate limit hit" in result
        assert "**Error Code**: 17" in result
        assert "**Suggestion**" in result

    def test_meta_ads_error_without_code(self) -> None:
        """MetaAdsError without code has no extras."""
        err = MetaAdsError("Generic error")
        result = format_write_error(err)
        assert "Generic error" in result
        assert "Error Code" not in result

    def test_plain_value_error(self) -> None:
        """Plain ValueError shows message without code/hint."""
        err = ValueError("Invalid budget")
        result = format_write_error(err)
        assert "Invalid budget" in result
        assert "Error Code" not in result

    def test_meta_ads_error_with_blame_fields(self) -> None:
        """MetaAdsError with blame_field_specs renders Problem Fields."""
        err = MetaAdsError(
            "Invalid parameter",
            error_code=100,
            error_user_msg="Ad set requires a daily or lifetime budget.",
            blame_field_specs=["daily_budget"],
        )
        result = format_write_error(err)
        assert "**Problem Fields**: daily_budget" in result
        assert "Ad set requires a daily or lifetime budget." in result

    def test_meta_ads_error_with_subcode(self) -> None:
        """MetaAdsError with subcode renders in output."""
        err = MetaAdsError(
            "Invalid parameter",
            error_code=100,
            error_subcode=1885024,
        )
        result = format_write_error(err)
        assert "(subcode: 1885024)" in result


class TestNetworkErrorHandling:
    """Tests for network error conversion in client."""

    @pytest.mark.asyncio
    async def test_connection_error_becomes_meta_ads_error(self) -> None:
        """ConnectionError during API call raises MetaAdsError."""
        from meta_ads_mcp.client import MetaAdsClient
        from meta_ads_mcp.config import MetaAdsConfig

        config = MetaAdsConfig(
            access_token="test_token",
            app_id="test_app_id",
            app_secret="test_secret",
        )
        client = MetaAdsClient(config)
        client._api = MagicMock()  # Mark as initialized

        with patch("meta_ads_mcp.client.User") as MockUser:
            MockUser.return_value.get_ad_accounts.side_effect = ConnectionError(
                "Connection refused"
            )
            with pytest.raises(MetaAdsError, match="Network error"):
                await client.get_ad_accounts()

    @pytest.mark.asyncio
    async def test_timeout_error_becomes_meta_ads_error(self) -> None:
        """TimeoutError during API call raises MetaAdsError."""
        from meta_ads_mcp.client import MetaAdsClient
        from meta_ads_mcp.config import MetaAdsConfig

        config = MetaAdsConfig(
            access_token="test_token",
            app_id="test_app_id",
            app_secret="test_secret",
        )
        client = MetaAdsClient(config)
        client._api = MagicMock()

        with patch("meta_ads_mcp.client.User") as MockUser:
            MockUser.return_value.get_ad_accounts.side_effect = TimeoutError(
                "Timed out"
            )
            with pytest.raises(MetaAdsError, match="Network error"):
                await client.get_ad_accounts()


class TestServerLifespan:
    """Tests for server startup error handling."""

    @pytest.mark.asyncio
    async def test_missing_config_raises_runtime_error(self) -> None:
        """Missing env vars produce a RuntimeError with guidance."""
        from meta_ads_mcp.server import app_lifespan

        mock_server = MagicMock()

        with patch(
            "meta_ads_mcp.server.MetaAdsConfig.from_env",
            side_effect=Exception("META_ACCESS_TOKEN not found"),
        ):
            with pytest.raises(RuntimeError, match="Failed to load configuration"):
                async with app_lifespan(mock_server) as _ctx:
                    pass

    @pytest.mark.asyncio
    async def test_bad_credentials_raises_runtime_error(self) -> None:
        """Invalid credentials produce a RuntimeError with guidance."""
        from meta_ads_mcp.config import MetaAdsConfig
        from meta_ads_mcp.server import app_lifespan

        mock_server = MagicMock()
        fake_config = MetaAdsConfig(access_token="bad", app_id="bad", app_secret="bad")

        with patch(
            "meta_ads_mcp.server.MetaAdsConfig.from_env", return_value=fake_config
        ):
            with patch(
                "meta_ads_mcp.server.MetaAdsClient.initialize",
                side_effect=Exception("Invalid credentials"),
            ):
                with pytest.raises(RuntimeError, match="Failed to initialize"):
                    async with app_lifespan(mock_server) as _ctx:
                        pass
