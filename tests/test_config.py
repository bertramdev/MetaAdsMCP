"""Tests for MetaAdsConfig."""

from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest

from meta_ads_mcp.config import MetaAdsConfig


class TestMetaAdsConfig:
    """Tests for MetaAdsConfig construction and behavior."""

    def test_from_env_loads_required_vars(self) -> None:
        """Config loads required environment variables."""
        env = {
            "META_ACCESS_TOKEN": "test_token_12345678",
            "META_APP_ID": "app123",
            "META_APP_SECRET": "secret456",
        }
        with patch(
            "meta_ads_mcp.config.decouple_config",
            side_effect=lambda k, **kw: env.get(k, kw.get("default", "")),
        ):
            config = MetaAdsConfig.from_env()

        assert config.access_token == "test_token_12345678"
        assert config.app_id == "app123"
        assert config.app_secret == "secret456"

    def test_from_env_loads_optional_vars(self) -> None:
        """Config loads optional environment variables with defaults."""
        env = {
            "META_ACCESS_TOKEN": "test_token_12345678",
            "META_APP_ID": "app123",
            "META_APP_SECRET": "secret456",
            "META_DEFAULT_AD_ACCOUNT_ID": "act_999",
            "META_API_VERSION": "v22.0",
        }
        with patch(
            "meta_ads_mcp.config.decouple_config",
            side_effect=lambda k, **kw: env.get(k, kw.get("default", "")),
        ):
            config = MetaAdsConfig.from_env()

        assert config.default_account_id == "act_999"
        assert config.api_version == "v22.0"

    def test_from_env_defaults(self) -> None:
        """Config uses defaults for optional vars when not set."""
        env = {
            "META_ACCESS_TOKEN": "test_token_12345678",
            "META_APP_ID": "app123",
            "META_APP_SECRET": "secret456",
        }
        with patch(
            "meta_ads_mcp.config.decouple_config",
            side_effect=lambda k, **kw: env.get(k, kw.get("default", "")),
        ):
            config = MetaAdsConfig.from_env()

        assert config.default_account_id is None
        assert config.api_version == "v25.0"

    def test_frozen(self) -> None:
        """Config is immutable."""
        config = MetaAdsConfig(access_token="tok", app_id="id", app_secret="sec")
        with pytest.raises(FrozenInstanceError):
            config.access_token = "new"  # type: ignore[misc]


class TestResolveAccountId:
    """Tests for resolve_account_id."""

    def test_explicit_id_with_prefix(self) -> None:
        """Explicit ID with act_ prefix passes through."""
        config = MetaAdsConfig(access_token="tok", app_id="id", app_secret="sec")
        assert config.resolve_account_id("act_123") == "act_123"

    def test_explicit_id_without_prefix(self) -> None:
        """Explicit ID without act_ prefix gets it added."""
        config = MetaAdsConfig(access_token="tok", app_id="id", app_secret="sec")
        assert config.resolve_account_id("123") == "act_123"

    def test_falls_back_to_default(self) -> None:
        """None falls back to default account."""
        config = MetaAdsConfig(
            access_token="tok",
            app_id="id",
            app_secret="sec",
            default_account_id="act_default",
        )
        assert config.resolve_account_id(None) == "act_default"

    def test_no_id_no_default_raises(self) -> None:
        """ValueError raised when no ID and no default."""
        config = MetaAdsConfig(access_token="tok", app_id="id", app_secret="sec")
        with pytest.raises(ValueError, match="No account_id provided"):
            config.resolve_account_id(None)

    def test_default_without_prefix(self) -> None:
        """Default account ID without prefix gets it added."""
        config = MetaAdsConfig(
            access_token="tok",
            app_id="id",
            app_secret="sec",
            default_account_id="456",
        )
        assert config.resolve_account_id(None) == "act_456"


class TestMaskedToken:
    """Tests for masked_token property."""

    def test_long_token_masked(self) -> None:
        """Long tokens show first 4 and last 4 chars."""
        config = MetaAdsConfig(
            access_token="abcdefghijklmnop",
            app_id="id",
            app_secret="sec",
        )
        assert config.masked_token == "abcd...mnop"

    def test_short_token_fully_masked(self) -> None:
        """Short tokens are fully masked."""
        config = MetaAdsConfig(
            access_token="short",
            app_id="id",
            app_secret="sec",
        )
        assert config.masked_token == "***"
