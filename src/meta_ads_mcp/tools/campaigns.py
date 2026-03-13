"""Campaign management tools."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_campaign,
    format_campaign_list,
    format_diagnostics,
    format_error,
    format_update_result,
    format_write_result,
)
from meta_ads_mcp.models import CampaignDiagnosticsModel, CampaignModel
from meta_ads_mcp.tools import get_client
from meta_ads_mcp.tools._write_helpers import (
    cents_display,
    dollars_to_cents,
    fetch_and_update,
    format_write_error,
    merge_updates,
    parse_json_list_param,
    validate_status,
)


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
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


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
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def create_campaign(
    ctx: Context,
    name: str,
    objective: str,
    account_id: str | None = None,
    daily_budget: str | None = None,
    lifetime_budget: str | None = None,
    special_ad_categories: str | None = None,
    start_time: str | None = None,
    stop_time: str | None = None,
    bid_strategy: str | None = None,
    smart_promotion_type: str | None = None,
    spend_cap: str | None = None,
    budget_schedule_specs: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new campaign (defaults to PAUSED).

    Creates a campaign in the specified ad account. The campaign starts
    as PAUSED for safety. Use update_campaign to activate it.

    Args:
        name: Campaign name.
        objective: Campaign objective (e.g., OUTCOME_TRAFFIC).
        account_id: Ad account ID (e.g., act_123456789). Optional.
        daily_budget: Daily budget in dollars (e.g., "50.00"). Optional.
        lifetime_budget: Lifetime budget in dollars. Optional.
        special_ad_categories: Comma-separated categories.
            Defaults to "NONE".
        start_time: Campaign start time in ISO 8601 format. Optional.
        stop_time: Campaign stop time in ISO 8601 format. Optional.
        bid_strategy: Bid strategy (e.g., LOWEST_COST_WITHOUT_CAP). Optional.
        smart_promotion_type: Advantage+ type (e.g., GUIDED_CREATION). Optional.
        spend_cap: Campaign spend cap in dollars (e.g., "500.00"). Optional.
        budget_schedule_specs: Budget schedule as JSON string. Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        daily_cents = dollars_to_cents(daily_budget) if daily_budget else None
        lifetime_cents = dollars_to_cents(lifetime_budget) if lifetime_budget else None
        spend_cap_cents = dollars_to_cents(spend_cap) if spend_cap else None

        categories: list[str] | None = None
        if special_ad_categories:
            categories = [c.strip() for c in special_ad_categories.split(",")]

        schedule_specs: list[dict[str, Any]] | None = None
        if budget_schedule_specs:
            schedule_specs = parse_json_list_param(
                budget_schedule_specs, "budget_schedule_specs"
            )

        raw = await client.create_campaign(
            name=name,
            objective=objective,
            account_id=account_id,
            daily_budget=daily_cents,
            lifetime_budget=lifetime_cents,
            special_ad_categories=categories,
            start_time=start_time,
            stop_time=stop_time,
            bid_strategy=bid_strategy,
            smart_promotion_type=smart_promotion_type,
            spend_cap=spend_cap_cents,
            budget_schedule_specs=schedule_specs,
            dry_run=dry_run,
        )

        model = CampaignModel(
            id=raw.get("id", ""),
            name=name,
            status="PAUSED",
            objective=objective,
            daily_budget=str(daily_cents) if daily_cents else "0",
            lifetime_budget=str(lifetime_cents) if lifetime_cents else "0",
            start_time=start_time or "",
            stop_time=stop_time or "",
        )
        detail = format_campaign(model)
        return format_write_result("Created", "Campaign", detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def update_campaign(
    ctx: Context,
    campaign_id: str,
    name: str | None = None,
    status: str | None = None,
    daily_budget: str | None = None,
    lifetime_budget: str | None = None,
    start_time: str | None = None,
    stop_time: str | None = None,
    bid_strategy: str | None = None,
    smart_promotion_type: str | None = None,
    spend_cap: str | None = None,
    budget_schedule_specs: str | None = None,
    dry_run: bool = False,
) -> str:
    """Update an existing campaign.

    Modifies campaign properties such as name, status, budget, or schedule.
    Shows before/after comparison for changed fields.

    Args:
        campaign_id: The campaign ID to update.
        name: New campaign name. Optional.
        status: New status (ACTIVE, PAUSED, ARCHIVED). Optional.
        daily_budget: New daily budget in dollars (e.g., "75.00"). Optional.
        lifetime_budget: New lifetime budget in dollars. Optional.
        start_time: New start time in ISO 8601 format. Optional.
        stop_time: New stop time in ISO 8601 format. Optional.
        bid_strategy: New bid strategy. Optional.
        smart_promotion_type: Advantage+ type (e.g., GUIDED_CREATION). Optional.
        spend_cap: New campaign spend cap in dollars (e.g., "500.00"). Optional.
        budget_schedule_specs: New budget schedule as JSON string. Optional.
        dry_run: If True, validate without updating. Default False.
    """
    try:
        client = get_client(ctx)

        if status is not None:
            status = validate_status(status)

        daily_cents = dollars_to_cents(daily_budget) if daily_budget else None
        lifetime_cents = dollars_to_cents(lifetime_budget) if lifetime_budget else None
        spend_cap_cents = dollars_to_cents(spend_cap) if spend_cap else None

        schedule_specs: list[dict[str, Any]] | None = None
        if budget_schedule_specs:
            schedule_specs = parse_json_list_param(
                budget_schedule_specs, "budget_schedule_specs"
            )

        # Fetch current state and apply update concurrently
        current = await fetch_and_update(
            client.get_campaign(campaign_id),
            client.update_campaign(
                campaign_id=campaign_id,
                name=name,
                status=status,
                daily_budget=daily_cents,
                lifetime_budget=lifetime_cents,
                start_time=start_time,
                stop_time=stop_time,
                bid_strategy=bid_strategy,
                smart_promotion_type=smart_promotion_type,
                spend_cap=spend_cap_cents,
                budget_schedule_specs=schedule_specs,
                dry_run=dry_run,
            ),
        )

        # Build changes dict for display
        changes: dict[str, tuple[str, str]] = {}
        if name is not None:
            changes["Name"] = (current.get("name", ""), name)
        if status is not None:
            changes["Status"] = (current.get("status", ""), status)
        if daily_cents is not None:
            changes["Daily Budget"] = (
                cents_display(current.get("daily_budget", "0") or "0"),
                cents_display(daily_cents),
            )
        if lifetime_cents is not None:
            changes["Lifetime Budget"] = (
                cents_display(current.get("lifetime_budget", "0") or "0"),
                cents_display(lifetime_cents),
            )
        if start_time is not None:
            changes["Start Time"] = (
                current.get("start_time", "Not set"),
                start_time,
            )
        if stop_time is not None:
            changes["Stop Time"] = (
                current.get("stop_time", "Not set"),
                stop_time,
            )
        if bid_strategy is not None:
            changes["Bid Strategy"] = (
                current.get("bid_strategy", "Not set"),
                bid_strategy,
            )
        if spend_cap_cents is not None:
            changes["Spend Cap"] = (
                cents_display(current.get("spend_cap", "0") or "0"),
                cents_display(spend_cap_cents),
            )
        if smart_promotion_type is not None:
            changes["Smart Promotion Type"] = (
                current.get("smart_promotion_type", "Not set"),
                smart_promotion_type,
            )

        model = CampaignModel(
            **merge_updates(
                current,
                {
                    "name": name,
                    "status": status,
                    "daily_budget": (
                        str(daily_cents) if daily_cents is not None else None
                    ),
                    "lifetime_budget": (
                        str(lifetime_cents) if lifetime_cents is not None else None
                    ),
                    "start_time": start_time,
                    "stop_time": stop_time,
                },
            )
        )
        detail = format_campaign(model)
        return format_update_result(
            "Campaign", campaign_id, changes, detail, dry_run=dry_run
        )
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def get_campaign_diagnostics(ctx: Context, campaign_id: str) -> str:
    """Get diagnostic issues and recommendations for a campaign.

    Shows delivery issues with severity levels and Meta's optimization
    recommendations. Use this to troubleshoot poor campaign performance.

    Args:
        campaign_id: The campaign ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_campaign_diagnostics(campaign_id)
        model = CampaignDiagnosticsModel(**raw)
        return format_diagnostics(
            "Campaign", model.name, model.issues_info, model.recommendations
        )
    except MetaAdsError as e:
        return format_error(e.message)


def register(mcp: FastMCP) -> None:
    """Register campaign tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_campaigns)
    mcp.tool()(get_campaign)
    mcp.tool()(create_campaign)
    mcp.tool()(update_campaign)
    mcp.tool()(get_campaign_diagnostics)
