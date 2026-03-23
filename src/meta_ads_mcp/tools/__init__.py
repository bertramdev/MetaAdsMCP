"""MCP tool modules organized by Meta Ads entity type."""

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from meta_ads_mcp.client import MetaAdsClient

# --- Read-only tools (20) — query the Meta Ads API but never mutate ---
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=True,
)

# --- Create tools (6) — create new resources; NOT idempotent ---
CREATE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

# --- Update tools (3) — modify existing resources; idempotent ---
UPDATE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# --- Destructive tools (1) — change status (pause/archive); idempotent ---
DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=True,
)


def get_client(ctx: Context) -> MetaAdsClient:
    """Extract MetaAdsClient from MCP request context.

    Args:
        ctx: The MCP tool execution context.

    Returns:
        The initialized MetaAdsClient from the server lifespan.
    """
    return ctx.request_context.lifespan_context.client  # type: ignore[no-any-return]
