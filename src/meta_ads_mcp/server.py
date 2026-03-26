"""FastMCP server skeleton with lifespan management.

Entry point for the Meta Ads MCP server. Initializes configuration
and the API client, then runs the MCP server over stdio transport.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from meta_ads_mcp.client import MetaAdsClient
from meta_ads_mcp.config import MetaAdsConfig
from meta_ads_mcp.tools import (
    accounts,
    ads,
    adsets,
    assets,
    audiences,
    campaigns,
    creatives,
    insights,
)

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context available during the server lifespan.

    Attributes:
        client: The initialized Meta Ads API client.
        config: The server configuration.
    """

    client: MetaAdsClient
    config: MetaAdsConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage the application lifecycle.

    Loads configuration from environment, initializes the Meta Ads client,
    and yields the application context.

    Args:
        server: The FastMCP server instance.

    Yields:
        The initialized AppContext.
    """
    try:
        config = MetaAdsConfig.from_env()
    except Exception as e:
        raise RuntimeError(
            f"Failed to load configuration: {e}. "
            "Ensure META_ACCESS_TOKEN, META_APP_ID, and META_APP_SECRET "
            "are set in your environment or .env file."
        ) from e
    try:
        client = MetaAdsClient(config)
        client.initialize()
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Meta Ads client: {e}. "
            "Check that your credentials are valid."
        ) from e
    logger.info("Meta Ads MCP server started")
    yield AppContext(client=client, config=config)
    logger.info("Meta Ads MCP server stopped")


mcp = FastMCP("Meta Ads MCP", lifespan=app_lifespan)

# Register all tool modules
accounts.register(mcp)
campaigns.register(mcp)
adsets.register(mcp)
ads.register(mcp)
insights.register(mcp)
creatives.register(mcp)
audiences.register(mcp)
assets.register(mcp)


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run(transport="stdio")
