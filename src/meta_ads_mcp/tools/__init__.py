"""MCP tool modules organized by Meta Ads entity type."""

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from meta_ads_mcp.client import MetaAdsClient

# Shared tool annotations for permission hinting.
# Clients use these to auto-approve read-only tools
# while prompting for confirmation on write operations.
READ_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
WRITE_ANNOTATIONS = ToolAnnotations(readOnlyHint=False, destructiveHint=False)
DESTRUCTIVE_ANNOTATIONS = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def get_client(ctx: Context) -> MetaAdsClient:
    """Extract MetaAdsClient from MCP request context.

    Args:
        ctx: The MCP tool execution context.

    Returns:
        The initialized MetaAdsClient from the server lifespan.
    """
    return ctx.request_context.lifespan_context.client  # type: ignore[no-any-return]
