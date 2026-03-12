"""Ad management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import format_ad, format_ad_list, format_error
from meta_ads_mcp.models import AdModel
from meta_ads_mcp.tools import get_client


async def list_ads(
    ctx: Context,
    account_id: str | None = None,
    ad_set_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> str:
    """List ads for an ad account, campaign, or ad set.

    Returns a table of ads with ID, name, status, ad set, and creative reference.
    Filter by ad_set_id or campaign_id to narrow results, or by status.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        ad_set_id: Filter to ads in this ad set. Optional.
        campaign_id: Filter to ads in this campaign. Optional.
        status: Filter by effective status (e.g., ACTIVE, PAUSED). Optional.
        limit: Maximum number of ads to return. Default 50.
    """
    try:
        client = get_client(ctx)
        status_filter = [status] if status else None
        raw = await client.get_ads(
            account_id=account_id,
            ad_set_id=ad_set_id,
            campaign_id=campaign_id,
            status_filter=status_filter,
            limit=limit,
        )
        models = [AdModel(**d) for d in raw]
        return format_ad_list(models)
    except MetaAdsError as e:
        return format_error(e.message)


async def get_ad(ctx: Context, ad_id: str) -> str:
    """Get detailed information for a specific ad.

    Shows ad name, status, parent ad set and campaign,
    creative reference, and timestamps.

    Args:
        ad_id: The ad ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad(ad_id)
        model = AdModel(**raw)
        return format_ad(model)
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register ad tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_ads)
    mcp.tool()(get_ad)
