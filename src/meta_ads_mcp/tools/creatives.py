"""Creative management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_creative,
    format_creative_list,
    format_error,
)
from meta_ads_mcp.models import AdCreativeModel
from meta_ads_mcp.tools import get_client


async def list_creatives(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List ad creatives for an ad account.

    Returns a table of creatives with ID, name, title, CTA, and link URL.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of creatives to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_creatives(account_id=account_id, limit=limit)
        models = [AdCreativeModel(**d) for d in raw]
        return format_creative_list(models)
    except MetaAdsError as e:
        return format_error(e.message)


async def get_creative(ctx: Context, creative_id: str) -> str:
    """Get detailed information for a specific ad creative.

    Shows creative name, title, body, CTA, link URL, image URL, and thumbnail.

    Args:
        creative_id: The creative ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_creative(creative_id)
        model = AdCreativeModel(**raw)
        return format_creative(model)
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register creative tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_creatives)
    mcp.tool()(get_creative)
