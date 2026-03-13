"""Configuration management for the Meta Ads MCP server.

Loads configuration from environment variables using python-decouple.
"""

from dataclasses import dataclass

from decouple import config as decouple_config


@dataclass(frozen=True)
class MetaAdsConfig:
    """Immutable configuration for the Meta Ads MCP server.

    Attributes:
        access_token: Meta API access token.
        app_id: Meta App ID.
        app_secret: Meta App Secret.
        default_account_id: Default ad account ID (with act_ prefix).
        api_version: Meta Graph API version.
    """

    access_token: str
    app_id: str
    app_secret: str
    default_account_id: str | None = None
    api_version: str = "v25.0"

    @classmethod
    def from_env(cls) -> "MetaAdsConfig":
        """Create a config instance from environment variables.

        Returns:
            A MetaAdsConfig instance populated from env vars.

        Raises:
            UndefinedValueError: If a required env var is missing.
        """
        return cls(
            access_token=str(decouple_config("META_ACCESS_TOKEN")),
            app_id=str(decouple_config("META_APP_ID")),
            app_secret=str(decouple_config("META_APP_SECRET")),
            default_account_id=str(
                decouple_config("META_DEFAULT_AD_ACCOUNT_ID", default="")
            )
            or None,
            api_version=str(decouple_config("META_API_VERSION", default="v25.0")),
        )

    def resolve_account_id(self, account_id: str | None = None) -> str:
        """Resolve an account ID, falling back to default.

        Ensures the returned ID has the ``act_`` prefix.

        Args:
            account_id: Explicit account ID, or None to use default.

        Returns:
            The resolved account ID with ``act_`` prefix.

        Raises:
            ValueError: If no account ID is provided and no default is set.
        """
        resolved = account_id or self.default_account_id
        if not resolved:
            raise ValueError(
                "No account_id provided and no default account configured. "
                "Set META_DEFAULT_AD_ACCOUNT_ID or pass account_id explicitly."
            )
        if not resolved.startswith("act_"):
            resolved = f"act_{resolved}"
        return resolved

    @property
    def masked_token(self) -> str:
        """Return the access token with most characters masked for safe logging."""
        if len(self.access_token) <= 8:
            return "***"
        return f"{self.access_token[:4]}...{self.access_token[-4:]}"
