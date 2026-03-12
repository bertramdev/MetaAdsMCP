"""MCP tool modules organized by Meta Ads entity type."""

from mcp.server.fastmcp import Context

from meta_ads_mcp.client import MetaAdsClient


def get_client(ctx: Context) -> MetaAdsClient:
    """Extract MetaAdsClient from MCP request context.

    Args:
        ctx: The MCP tool execution context.

    Returns:
        The initialized MetaAdsClient from the server lifespan.
    """
    return ctx.request_context.lifespan_context.client  # type: ignore[no-any-return]
