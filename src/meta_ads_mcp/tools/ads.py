"""Ad management tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_ad,
    format_ad_list,
    format_ad_review_feedback,
    format_delivery_checks,
    format_diagnostics,
    format_error,
    format_update_result,
    format_write_result,
)
from meta_ads_mcp.models import AdDiagnosticsModel, AdModel
from meta_ads_mcp.tools import get_client
from meta_ads_mcp.tools._write_helpers import (
    fetch_and_update,
    format_write_error,
    validate_status,
)


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
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


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
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def create_ad(
    ctx: Context,
    name: str,
    adset_id: str,
    creative_id: str,
    account_id: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new ad (defaults to PAUSED).

    Creates an ad in the specified ad set using an existing creative.
    The ad starts as PAUSED for safety. Use update_ad_status to activate it.

    Args:
        name: Ad name.
        adset_id: Parent ad set ID.
        creative_id: ID of the creative to use.
        account_id: The ad account ID (e.g., act_123456789). Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        raw = await client.create_ad(
            name=name,
            adset_id=adset_id,
            creative_id=creative_id,
            account_id=account_id,
            dry_run=dry_run,
        )

        model = AdModel(
            id=raw.get("id", ""),
            name=name,
            status="PAUSED",
            adset_id=adset_id,
            creative={"id": creative_id},
        )
        detail = format_ad(model)
        return format_write_result("Created", "Ad", detail, dry_run=dry_run)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def update_ad_status(
    ctx: Context,
    ad_id: str,
    status: str,
    dry_run: bool = False,
) -> str:
    """Update an ad's status (pause, activate, or archive).

    Changes the status of an existing ad. Shows before/after comparison.

    Args:
        ad_id: The ad ID to update.
        status: New status (ACTIVE, PAUSED, ARCHIVED).
        dry_run: If True, validate without updating. Default False.
    """
    try:
        client = get_client(ctx)
        status = validate_status(status)

        # Fetch current state and apply update concurrently
        current = await fetch_and_update(
            client.get_ad(ad_id),
            client.update_ad(ad_id=ad_id, status=status, dry_run=dry_run),
        )

        changes: dict[str, tuple[str, str]] = {
            "Status": (current.get("status", ""), status),
        }

        model = AdModel(**{**current, "status": status})
        detail = format_ad(model)
        return format_update_result("Ad", ad_id, changes, detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def get_ad_diagnostics(ctx: Context, ad_id: str) -> str:
    """Get diagnostic info for an ad including review feedback and delivery checks.

    Shows ad review feedback (policy rejection details), failed delivery
    checks, issues, and recommendations. Critical for troubleshooting
    rejected or underperforming ads.

    Args:
        ad_id: The ad ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_diagnostics(ad_id)
        model = AdDiagnosticsModel(**raw)
        base = format_diagnostics(
            "Ad", model.name, model.issues_info, model.recommendations
        )
        review = format_ad_review_feedback(model.ad_review_feedback)
        checks = format_delivery_checks(model.failed_delivery_checks)
        return base + "\n\n" + review + "\n\n" + checks
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register ad tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_ads)
    mcp.tool()(get_ad)
    mcp.tool()(create_ad)
    mcp.tool()(update_ad_status)
    mcp.tool()(get_ad_diagnostics)
