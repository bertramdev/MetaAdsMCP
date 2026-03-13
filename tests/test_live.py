"""Live integration tests against the real Meta Ads API.

These tests require a valid .env with META_ACCESS_TOKEN, META_APP_ID,
META_APP_SECRET, and optionally META_DEFAULT_AD_ACCOUNT_ID.

Run with:
    poetry run pytest tests/test_live.py -v -s

Skipped automatically in CI or when credentials are missing.
"""

import os

import pytest

from meta_ads_mcp.client import MetaAdsClient, MetaAdsError
from meta_ads_mcp.config import MetaAdsConfig
from meta_ads_mcp.formatting import (
    format_account,
    format_account_list,
    format_campaign_list,
    format_insights_table,
)
from meta_ads_mcp.models import AdAccountModel, CampaignModel, InsightRow


def _can_run_live() -> bool:
    """Check if live tests can run (credentials available, not in CI)."""
    if os.environ.get("CI"):
        return False
    try:
        MetaAdsConfig.from_env()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_run_live(),
    reason="Live tests require .env credentials and no CI environment",
)


@pytest.fixture(scope="module")
def config() -> MetaAdsConfig:
    """Load real config from .env."""
    return MetaAdsConfig.from_env()


@pytest.fixture(scope="module")
def client(config: MetaAdsConfig) -> MetaAdsClient:
    """Create and initialize a real API client."""
    c = MetaAdsClient(config)
    c.initialize()
    return c


@pytest.fixture(scope="module")
def require_default_account(config: MetaAdsConfig) -> None:
    """Skip test if no default account is configured."""
    if not config.default_account_id:
        pytest.skip("No default account configured")


_cached_accounts: list[dict] | None = None


async def _get_accounts(client: MetaAdsClient) -> list[dict]:
    """Fetch ad accounts once and cache for the module."""
    global _cached_accounts  # noqa: PLW0603
    if _cached_accounts is None:
        _cached_accounts = await client.get_ad_accounts()
    return _cached_accounts


class TestConnection:
    """Basic connectivity and authentication tests."""

    async def test_get_ad_accounts(self, client: MetaAdsClient) -> None:
        """Verify we can list ad accounts — proves token is valid."""
        accounts = await _get_accounts(client)
        assert len(accounts) > 0, "No ad accounts found — check token permissions"
        first = accounts[0]
        assert "id" in first
        assert first["id"].startswith("act_")
        print(f"\n  Found {len(accounts)} ad account(s)")
        for acc in accounts:
            print(f"    {acc['id']}: {acc.get('name', 'N/A')}")

    async def test_get_account_info(
        self,
        client: MetaAdsClient,
        require_default_account: None,
    ) -> None:
        """Verify detailed account info for the default account."""
        info = await client.get_account_info()
        assert "id" in info
        assert "name" in info
        print(f"\n  Account: {info['name']} ({info['id']})")
        print(f"  Currency: {info.get('currency', 'N/A')}")
        print(f"  Timezone: {info.get('timezone_name', 'N/A')}")


class TestModelsAndFormatting:
    """Test that real API data parses through models and formatters cleanly."""

    async def test_account_models(self, client: MetaAdsClient) -> None:
        """Verify raw account data parses into AdAccountModel."""
        raw_accounts = await _get_accounts(client)
        models = [AdAccountModel(**d) for d in raw_accounts]
        assert len(models) > 0
        for m in models:
            assert m.id.startswith("act_")
        print(f"\n  Parsed {len(models)} account model(s) successfully")

    async def test_account_formatting(self, client: MetaAdsClient) -> None:
        """Verify account list formats to markdown without errors."""
        raw_accounts = await _get_accounts(client)
        models = [AdAccountModel(**d) for d in raw_accounts]
        output = format_account_list(models)
        assert "## Ad Accounts" in output
        print(f"\n--- Account List ---\n{output}")

    async def test_account_detail_formatting(
        self,
        client: MetaAdsClient,
        require_default_account: None,
    ) -> None:
        """Verify single account detail formats correctly."""
        raw = await client.get_account_info()
        model = AdAccountModel(**raw)
        output = format_account(model)
        assert "## Ad Account:" in output
        print(f"\n--- Account Detail ---\n{output}")


class TestCampaigns:
    """Test campaign retrieval with real data."""

    async def test_list_campaigns(
        self,
        client: MetaAdsClient,
        require_default_account: None,
    ) -> None:
        """List campaigns and verify data structure."""
        raw = await client.get_campaigns(limit=10)
        assert len(raw) <= 10
        print(f"\n  Found {len(raw)} campaign(s)")
        if raw:
            models = [CampaignModel(**d) for d in raw]
            output = format_campaign_list(models)
            print(f"\n--- Campaigns ---\n{output}")
            for m in models:
                assert m.id
                assert m.name


class TestInsights:
    """Test insights retrieval with real data."""

    async def test_account_insights_last_30d(
        self,
        client: MetaAdsClient,
        require_default_account: None,
    ) -> None:
        """Get last 30 days account insights."""
        raw = await client.get_insights(date_preset="last_30d", level="account")
        print(f"\n  Got {len(raw)} insight row(s)")
        if raw:
            models = [InsightRow(**d) for d in raw]
            output = format_insights_table(models)
            print(f"\n--- Account Insights (last 30d) ---\n{output}")

    async def test_campaign_level_insights(
        self,
        client: MetaAdsClient,
        require_default_account: None,
    ) -> None:
        """Get campaign-level insights."""
        raw = await client.get_insights(
            date_preset="last_30d", level="campaign", limit=5
        )
        print(f"\n  Got {len(raw)} campaign insight row(s)")
        if raw:
            models = [InsightRow(**d) for d in raw]
            output = format_insights_table(models, title="Campaign Insights")
            print(f"\n{output}")


class TestErrorHandling:
    """Verify error handling with bad inputs."""

    async def test_invalid_account_id(self, client: MetaAdsClient) -> None:
        """Verify a bad account ID returns a clear error."""
        with pytest.raises(MetaAdsError) as exc_info:
            await client.get_account_info("act_000000000")
        print(f"\n  Error (expected): {exc_info.value.message}")
