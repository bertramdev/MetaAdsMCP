"""Ad set management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import format_ad_set, format_ad_set_list, format_error
from meta_ads_mcp.models import AdSetModel
from meta_ads_mcp.tools import get_client


async def list_ad_sets(
    ctx: Context,
    account_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> str:
    """List ad sets for an ad account or specific campaign.

    Returns a table of ad sets with ID, name, status, campaign, budget,
    and optimization goal. Filter by campaign_id or status.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        campaign_id: Filter to ad sets in this campaign. Optional.
        status: Filter by effective status (e.g., ACTIVE, PAUSED). Optional.
        limit: Maximum number of ad sets to return. Default 50.
    """
    try:
        client = get_client(ctx)
        status_filter = [status] if status else None
        raw = await client.get_ad_sets(
            account_id=account_id,
            campaign_id=campaign_id,
            status_filter=status_filter,
            limit=limit,
        )
        models = [AdSetModel(**d) for d in raw]
        return format_ad_set_list(models)
    except MetaAdsError as e:
        return format_error(e.message)


async def get_ad_set(ctx: Context, ad_set_id: str) -> str:
    """Get detailed information for a specific ad set.

    Shows ad set name, status, campaign, budgets, billing,
    optimization, targeting, and schedule.

    Args:
        ad_set_id: The ad set ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_set(ad_set_id)
        model = AdSetModel(**raw)
        return format_ad_set(model)
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register ad set tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_ad_sets)
    mcp.tool()(get_ad_set)
