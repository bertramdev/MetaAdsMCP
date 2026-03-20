"""Ad set management tools."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_ad_set,
    format_ad_set_list,
    format_diagnostics,
    format_error,
    format_learning_stage,
    format_update_result,
    format_write_result,
)
from meta_ads_mcp.models import AdSetDiagnosticsModel, AdSetModel
from meta_ads_mcp.tools import (
    DESTRUCTIVE_ANNOTATIONS,
    READ_ANNOTATIONS,
    WRITE_ANNOTATIONS,
    get_client,
)
from meta_ads_mcp.tools._write_helpers import (
    cents_display,
    dollars_to_cents,
    fetch_and_update,
    format_write_error,
    merge_updates,
    parse_json_list_param,
    parse_json_param,
    validate_status,
)


async def list_ad_sets(
    ctx: Context,
    account_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> str:
    """List ad sets for an ad account or specific campaign.

    Returns a table of ad sets with ID, name, status, campaign, budget,
    and optimization goal. Filter by campaign_id or status.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        campaign_id: Filter to ad sets in this campaign. Optional.
        status: Filter by effective status (e.g., ACTIVE, PAUSED). Optional.
        limit: Maximum number of ad sets to return. Default 50.
    """
    try:
        client = get_client(ctx)
        status_filter = [status] if status else None
        raw = await client.get_ad_sets(
            account_id=account_id,
            campaign_id=campaign_id,
            status_filter=status_filter,
            limit=limit,
        )
        models = [AdSetModel(**d) for d in raw]
        return format_ad_set_list(models)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def get_ad_set(ctx: Context, ad_set_id: str) -> str:
    """Get detailed information for a specific ad set.

    Shows ad set name, status, campaign, budgets, billing,
    optimization, targeting, and schedule.

    Args:
        ad_set_id: The ad set ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_set(ad_set_id)
        model = AdSetModel(**raw)
        return format_ad_set(model)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def create_ad_set(
    ctx: Context,
    name: str,
    campaign_id: str,
    billing_event: str,
    optimization_goal: str,
    targeting: str,
    account_id: str | None = None,
    daily_budget: str | None = None,
    lifetime_budget: str | None = None,
    bid_strategy: str | None = None,
    bid_amount: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    promoted_object: str | None = None,
    frequency_control_specs: str | None = None,
    attribution_spec: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new ad set (defaults to PAUSED).

    Creates an ad set under the specified campaign. The ad set starts
    as PAUSED for safety. Use update_ad_set to activate it.

    Args:
        name: Ad set name.
        campaign_id: Parent campaign ID.
        billing_event: Billing event (e.g., IMPRESSIONS, LINK_CLICKS).
        optimization_goal: Optimization goal (e.g., LINK_CLICKS, CONVERSIONS).
        targeting: Targeting spec as JSON string
            (e.g., '{"geo_locations":{"countries":["US"]}}'). Required.
        account_id: Ad account ID (e.g., act_123456789). Optional.
        daily_budget: Daily budget in dollars (e.g., "50.00"). Optional.
        lifetime_budget: Lifetime budget in dollars. Optional.
        bid_strategy: Bid strategy. Optional.
        bid_amount: Bid amount in dollars (e.g., "1.50"). Optional.
        start_time: Start time in ISO 8601 format. Optional.
        end_time: End time in ISO 8601 format. Optional.
        promoted_object: Promoted object as JSON string. Optional.
        frequency_control_specs: Frequency cap as JSON string
            (e.g., '[{"event":"IMPRESSIONS","interval_days":7,"max_frequency":3}]').
            Optional.
        attribution_spec: Attribution spec as JSON string. Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        targeting_dict: dict[str, Any] = parse_json_param(targeting, "targeting")
        promoted_dict: dict[str, Any] | None = None
        if promoted_object:
            promoted_dict = parse_json_param(promoted_object, "promoted_object")

        freq_specs: list[dict[str, Any]] | None = None
        if frequency_control_specs:
            freq_specs = parse_json_list_param(
                frequency_control_specs, "frequency_control_specs"
            )

        attr_spec: list[dict[str, Any]] | None = None
        if attribution_spec:
            attr_spec = parse_json_list_param(attribution_spec, "attribution_spec")

        daily_cents = dollars_to_cents(daily_budget) if daily_budget else None
        lifetime_cents = dollars_to_cents(lifetime_budget) if lifetime_budget else None
        bid_cents = dollars_to_cents(bid_amount) if bid_amount else None

        raw = await client.create_ad_set(
            name=name,
            campaign_id=campaign_id,
            billing_event=billing_event,
            optimization_goal=optimization_goal,
            targeting=targeting_dict,
            account_id=account_id,
            daily_budget=daily_cents,
            lifetime_budget=lifetime_cents,
            bid_strategy=bid_strategy,
            bid_amount=bid_cents,
            start_time=start_time,
            end_time=end_time,
            promoted_object=promoted_dict,
            frequency_control_specs=freq_specs,
            attribution_spec=attr_spec,
            dry_run=dry_run,
        )

        model = AdSetModel(
            id=raw.get("id", ""),
            name=name,
            status="PAUSED",
            campaign_id=campaign_id,
            billing_event=billing_event,
            optimization_goal=optimization_goal,
            targeting=targeting_dict,
            daily_budget=str(daily_cents) if daily_cents else "0",
            lifetime_budget=str(lifetime_cents) if lifetime_cents else "0",
            start_time=start_time or "",
            end_time=end_time or "",
        )
        detail = format_ad_set(model)
        return format_write_result("Created", "Ad Set", detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def update_ad_set(
    ctx: Context,
    ad_set_id: str,
    name: str | None = None,
    status: str | None = None,
    daily_budget: str | None = None,
    lifetime_budget: str | None = None,
    targeting: str | None = None,
    bid_strategy: str | None = None,
    bid_amount: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    optimization_goal: str | None = None,
    frequency_control_specs: str | None = None,
    attribution_spec: str | None = None,
    dry_run: bool = False,
) -> str:
    """Update an existing ad set.

    Modifies ad set properties such as name, status, budget, targeting,
    or schedule. Shows before/after comparison for changed fields.

    Args:
        ad_set_id: The ad set ID to update.
        name: New ad set name. Optional.
        status: New status (ACTIVE, PAUSED, ARCHIVED). Optional.
        daily_budget: New daily budget in dollars (e.g., "75.00"). Optional.
        lifetime_budget: New lifetime budget in dollars. Optional.
        targeting: New targeting spec as JSON string. Optional.
        bid_strategy: New bid strategy. Optional.
        bid_amount: New bid amount in dollars. Optional.
        start_time: New start time in ISO 8601 format. Optional.
        end_time: New end time in ISO 8601 format. Optional.
        optimization_goal: New optimization goal. Optional.
        frequency_control_specs: Frequency cap as JSON string
            (e.g., '[{"event":"IMPRESSIONS","interval_days":7,"max_frequency":3}]').
            Optional.
        attribution_spec: Attribution spec as JSON string. Optional.
        dry_run: If True, validate without updating. Default False.
    """
    try:
        client = get_client(ctx)

        if status is not None:
            status = validate_status(status)

        targeting_dict: dict[str, Any] | None = None
        if targeting is not None:
            targeting_dict = parse_json_param(targeting, "targeting")

        freq_specs: list[dict[str, Any]] | None = None
        if frequency_control_specs:
            freq_specs = parse_json_list_param(
                frequency_control_specs, "frequency_control_specs"
            )

        attr_spec: list[dict[str, Any]] | None = None
        if attribution_spec:
            attr_spec = parse_json_list_param(attribution_spec, "attribution_spec")

        daily_cents = dollars_to_cents(daily_budget) if daily_budget else None
        lifetime_cents = dollars_to_cents(lifetime_budget) if lifetime_budget else None
        bid_cents = dollars_to_cents(bid_amount) if bid_amount else None

        # Fetch current state and apply update concurrently
        current = await fetch_and_update(
            client.get_ad_set(ad_set_id),
            client.update_ad_set(
                ad_set_id=ad_set_id,
                name=name,
                status=status,
                daily_budget=daily_cents,
                lifetime_budget=lifetime_cents,
                targeting=targeting_dict,
                bid_strategy=bid_strategy,
                bid_amount=bid_cents,
                start_time=start_time,
                end_time=end_time,
                optimization_goal=optimization_goal,
                frequency_control_specs=freq_specs,
                attribution_spec=attr_spec,
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
        if targeting is not None:
            changes["Targeting"] = ("(previous)", "(updated)")
        if optimization_goal is not None:
            changes["Optimization Goal"] = (
                current.get("optimization_goal", ""),
                optimization_goal,
            )
        if frequency_control_specs is not None:
            changes["Frequency Control"] = ("(previous)", "(updated)")
        if attribution_spec is not None:
            changes["Attribution Spec"] = ("(previous)", "(updated)")

        model = AdSetModel(
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
                    "targeting": targeting_dict,
                    "optimization_goal": optimization_goal,
                },
            )
        )
        detail = format_ad_set(model)
        return format_update_result(
            "Ad Set", ad_set_id, changes, detail, dry_run=dry_run
        )
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def get_ad_set_diagnostics(ctx: Context, ad_set_id: str) -> str:
    """Get diagnostic issues, recommendations, and learning stage for an ad set.

    Shows delivery issues, optimization recommendations, and learning
    stage status. Learning stage indicates whether the algorithm has
    enough data to optimize delivery.

    Args:
        ad_set_id: The ad set ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_set_diagnostics(ad_set_id)
        model = AdSetDiagnosticsModel(**raw)
        base = format_diagnostics(
            "Ad Set", model.name, model.issues_info, model.recommendations
        )
        learning = format_learning_stage(model.learning_stage_info)
        return base + "\n\n" + learning
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


def register(mcp: FastMCP) -> None:
    """Register ad set tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool(annotations=READ_ANNOTATIONS)(list_ad_sets)
    mcp.tool(annotations=READ_ANNOTATIONS)(get_ad_set)
    mcp.tool(annotations=WRITE_ANNOTATIONS)(create_ad_set)
    mcp.tool(annotations=DESTRUCTIVE_ANNOTATIONS)(update_ad_set)
    mcp.tool(annotations=READ_ANNOTATIONS)(get_ad_set_diagnostics)
