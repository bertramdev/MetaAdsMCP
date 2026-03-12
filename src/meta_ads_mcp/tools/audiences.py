"""Audience management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_audience,
    format_audience_list,
    format_error,
)
from meta_ads_mcp.models import CustomAudienceModel
from meta_ads_mcp.tools import get_client


async def list_audiences(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List custom and lookalike audiences for an ad account.

    Returns a table of audiences with ID, name, subtype, size, and description.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of audiences to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_audiences(account_id=account_id, limit=limit)
        models = [CustomAudienceModel(**d) for d in raw]
        return format_audience_list(models)
    except MetaAdsError as e:
        return format_error(e.message)


async def get_audience(ctx: Context, audience_id: str) -> str:
    """Get detailed information for a specific custom audience.

    Shows audience name, subtype, size range, delivery status,
    operation status, and description.

    Args:
        audience_id: The audience ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_audience(audience_id)
        model = CustomAudienceModel(**raw)
        return format_audience(model)
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register audience tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_audiences)
    mcp.tool()(get_audience)
