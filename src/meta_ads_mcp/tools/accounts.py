"""Account listing and info tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import format_account, format_account_list, format_error
from meta_ads_mcp.models import AdAccountModel
from meta_ads_mcp.tools import READ_ONLY, get_client


async def get_ad_accounts(ctx: Context) -> str:
    """List all accessible ad accounts for the authenticated user.

    Returns a table of ad accounts with ID, name, status, currency, and amount spent.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_accounts()
        models = [AdAccountModel(**d) for d in raw]
        return format_account_list(models)
    except MetaAdsError as e:
        return format_error(
            e.message,
            error_code=e.error_code,
            hint=e.hint,
            blame_fields=e.blame_field_specs,
            error_subcode=e.error_subcode,
        )


async def get_account_info(ctx: Context, account_id: str | None = None) -> str:
    """Get detailed information for a specific ad account.

    Shows account name, status, currency, timezone, spend, balance, and spend cap.
    If no account_id is provided, uses the default configured account.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_account_info(account_id)
        model = AdAccountModel(**raw)
        return format_account(model)
    except MetaAdsError as e:
        return format_error(
            e.message,
            error_code=e.error_code,
            hint=e.hint,
            blame_fields=e.blame_field_specs,
            error_subcode=e.error_subcode,
        )


def register(mcp: FastMCP) -> None:
    """Register account tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool(annotations=READ_ONLY)(get_ad_accounts)
    mcp.tool(annotations=READ_ONLY)(get_account_info)
