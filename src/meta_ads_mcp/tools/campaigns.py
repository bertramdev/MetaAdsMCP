"""Campaign management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_campaign,
    format_campaign_list,
    format_error,
)
from meta_ads_mcp.models import CampaignModel
from meta_ads_mcp.tools import get_client


async def list_campaigns(
    ctx: Context,
    account_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> str:
    """List campaigns for an ad account.

    Returns a table of campaigns with ID, name, status, objective, and budget.
    Optionally filter by status (ACTIVE, PAUSED, ARCHIVED).

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        status: Filter by effective status (e.g., ACTIVE, PAUSED). Optional.
        limit: Maximum number of campaigns to return. Default 50.
    """
    try:
        client = get_client(ctx)
        status_filter = [status] if status else None
        raw = await client.get_campaigns(
            account_id=account_id, status_filter=status_filter, limit=limit
        )
        models = [CampaignModel(**d) for d in raw]
        return format_campaign_list(models)
    except MetaAdsError as e:
        return format_error(e.message)


async def get_campaign(ctx: Context, campaign_id: str) -> str:
    """Get detailed information for a specific campaign.

    Shows campaign name, status, objective, budgets, and schedule.

    Args:
        campaign_id: The campaign ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_campaign(campaign_id)
        model = CampaignModel(**raw)
        return format_campaign(model)
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register campaign tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_campaigns)
    mcp.tool()(get_campaign)
