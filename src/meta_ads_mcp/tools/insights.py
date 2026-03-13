"""Performance reporting and analytics tools."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_error,
    format_insights_comparison,
    format_insights_table,
    format_performance_comparison,
)
from meta_ads_mcp.models import InsightRow
from meta_ads_mcp.tools import get_client
from meta_ads_mcp.tools._insights_helpers import (
    VALID_BREAKDOWNS,
    get_previous_range,
    resolve_date_preset,
)


async def get_insights(
    ctx: Context,
    account_id: str | None = None,
    date_preset: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    level: str = "account",
    breakdowns: str | None = None,
    fields: str | None = None,
    limit: int = 50,
) -> str:
    """Get performance insights with flexible options.

    Query ad account insights at any aggregation level with
    optional breakdowns. Provide either date_preset or
    start_date + end_date.

    Args:
        account_id: Ad account ID (e.g., act_123456789).
        date_preset: Date preset (today, yesterday, last_7d,
            last_14d, last_30d, this_month, last_month).
        start_date: Start date YYYY-MM-DD, use with end_date.
        end_date: End date YYYY-MM-DD, use with start_date.
        level: Aggregation level: account, campaign, adset, ad.
        breakdowns: Comma-separated breakdowns (age, gender,
            country, placement, device_platform,
            publisher_platform).
        fields: Comma-separated metric fields to retrieve.
        limit: Maximum rows to return. Default 50.
    """
    try:
        client = get_client(ctx)
        time_range = None
        if start_date and end_date:
            time_range = {"since": start_date, "until": end_date}
        breakdown_list = (
            [b.strip() for b in breakdowns.split(",")] if breakdowns else None
        )
        field_list = [f.strip() for f in fields.split(",")] if fields else None
        raw = await client.get_insights(
            account_id=account_id,
            date_preset=date_preset if not time_range else None,
            level=level,
            breakdowns=breakdown_list,
            fields=field_list,
            time_range=time_range,
            limit=limit,
        )
        models = [InsightRow(**d) for d in raw]
        return format_insights_table(models)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def get_account_insights(
    ctx: Context,
    account_id: str | None = None,
    date_preset: str = "last_30d",
) -> str:
    """Get account-level performance summary.

    Returns key metrics (impressions, clicks, spend, CTR, CPC,
    CPM, reach) for the entire ad account.

    Args:
        account_id: Ad account ID (e.g., act_123456789).
        date_preset: Date preset (e.g., last_7d, last_30d).
    """
    return await get_insights(
        ctx, account_id=account_id, date_preset=date_preset, level="account"
    )


async def get_campaign_insights(
    ctx: Context,
    campaign_id: str,
    date_preset: str = "last_30d",
    compare: bool = False,
    account_id: str | None = None,
) -> str:
    """Get campaign performance with optional period comparison.

    Without compare: returns metrics for the date range.
    With compare=True: shows current vs. previous period
    side-by-side with change amounts and percentages.

    Args:
        campaign_id: The campaign ID to get insights for.
        date_preset: Date preset (e.g., last_7d, last_30d).
        compare: Compare current to previous period.
        account_id: Ad account ID (e.g., act_123456789).
    """
    try:
        client = get_client(ctx)
        since, until = resolve_date_preset(date_preset)
        time_range = {"since": since, "until": until}

        raw = await client.get_insights(
            account_id=account_id,
            level="campaign",
            time_range=time_range,
            limit=100,
        )
        current = [InsightRow(**d) for d in raw if d.get("campaign_id") == campaign_id]

        if not compare:
            if not current:
                return f"No insights found for campaign {campaign_id}."
            return format_insights_table(
                current, title=f"Campaign {campaign_id} Insights"
            )

        prev_since, prev_until = get_previous_range(since, until)
        prev_time_range = {"since": prev_since, "until": prev_until}

        raw_prev = await client.get_insights(
            account_id=account_id,
            level="campaign",
            time_range=prev_time_range,
            limit=100,
        )
        previous = [
            InsightRow(**d) for d in raw_prev if d.get("campaign_id") == campaign_id
        ]

        current_label = f"{since} to {until}"
        previous_label = f"{prev_since} to {prev_until}"

        return format_insights_comparison(
            current=current[0] if current else None,
            previous=previous[0] if previous else None,
            current_label=current_label,
            previous_label=previous_label,
        )
    except (MetaAdsError, ValueError) as e:
        code = e.error_code if isinstance(e, MetaAdsError) else None
        hint = e.hint if isinstance(e, MetaAdsError) else ""
        return format_error(str(e), error_code=code, hint=hint)


async def compare_performance(
    ctx: Context,
    entity_ids: str,
    entity_type: str = "campaign",
    date_preset: str = "last_30d",
    account_id: str | None = None,
) -> str:
    """Compare performance across multiple entities side-by-side.

    Fetches insights for each entity and displays them in a
    comparison table.

    Args:
        entity_ids: Comma-separated IDs (e.g., "123,456,789").
        entity_type: campaign, adset, or ad. Default campaign.
        date_preset: Date preset (e.g., last_7d, last_30d).
        account_id: Ad account ID (e.g., act_123456789).
    """
    try:
        client = get_client(ctx)
        ids = [eid.strip() for eid in entity_ids.split(",")]

        level_map = {
            "campaign": "campaign",
            "adset": "adset",
            "ad": "ad",
        }
        level = level_map.get(entity_type)
        if not level:
            return format_error(
                f"Invalid entity_type '{entity_type}'. "
                f"Must be campaign, adset, or ad."
            )

        id_field = f"{entity_type}_id"
        name_field = f"{entity_type}_name"

        since, until = resolve_date_preset(date_preset)
        time_range = {"since": since, "until": until}

        raw = await client.get_insights(
            account_id=account_id,
            level=level,
            time_range=time_range,
            limit=200,
        )
        all_rows = [InsightRow(**d) for d in raw]

        rows_by_entity: dict[str, InsightRow] = {}
        for row in all_rows:
            row_id = getattr(row, id_field, "")
            if row_id in ids:
                label = getattr(row, name_field, "") or row_id
                rows_by_entity[label] = row

        if not rows_by_entity:
            return f"No insights found for the specified {entity_type}s."

        return format_performance_comparison(rows_by_entity, entity_type)
    except (MetaAdsError, ValueError) as e:
        code = e.error_code if isinstance(e, MetaAdsError) else None
        hint = e.hint if isinstance(e, MetaAdsError) else ""
        return format_error(str(e), error_code=code, hint=hint)


async def get_breakdown_report(
    ctx: Context,
    breakdown: str,
    account_id: str | None = None,
    date_preset: str = "last_30d",
    level: str = "account",
    limit: int = 50,
) -> str:
    """Get a performance report broken down by a dimension.

    Breaks down metrics by age, gender, country, placement,
    device_platform, or publisher_platform.

    Args:
        breakdown: Breakdown dimension (age, gender, country,
            placement, device_platform, publisher_platform).
        account_id: Ad account ID (e.g., act_123456789).
        date_preset: Date preset (e.g., last_7d, last_30d).
        level: Aggregation level: account, campaign, adset, ad.
        limit: Maximum rows to return. Default 50.
    """
    if breakdown not in VALID_BREAKDOWNS:
        return format_error(
            f"Invalid breakdown '{breakdown}'. "
            f"Valid options: {', '.join(sorted(VALID_BREAKDOWNS))}"
        )

    try:
        client = get_client(ctx)
        raw = await client.get_insights(
            account_id=account_id,
            date_preset=date_preset,
            level=level,
            breakdowns=[breakdown],
            limit=limit,
        )
        models = [InsightRow(**d) for d in raw]
        title = f"Breakdown by {breakdown.replace('_', ' ').title()}"
        return format_insights_table(models, title=title)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


def register(mcp: FastMCP) -> None:
    """Register insights tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(get_insights)
    mcp.tool()(get_account_insights)
    mcp.tool()(get_campaign_insights)
    mcp.tool()(compare_performance)
    mcp.tool()(get_breakdown_report)
