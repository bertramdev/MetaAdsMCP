"""Markdown formatters for all Meta Ads entity types.

All functions return formatted markdown strings suitable for LLM output.
"""

from typing import Any

from meta_ads_mcp.models import (
    AdAccountModel,
    AdCreativeModel,
    AdModel,
    AdSetModel,
    CampaignModel,
    CustomAudienceModel,
    InsightRow,
)


def format_account(account: AdAccountModel) -> str:
    """Format a single ad account as markdown detail view.

    Args:
        account: The ad account model.

    Returns:
        Formatted markdown string.
    """
    return f"""## Ad Account: {account.name}

- **ID**: {account.id}
- **Status**: {account.status_display}
- **Currency**: {account.currency}
- **Timezone**: {account.timezone_name}
- **Amount Spent**: {account.amount_spent_formatted}
- **Balance**: {account.balance_formatted}
- **Spend Cap**: {account.spend_cap_formatted}"""


def format_account_list(accounts: list[AdAccountModel]) -> str:
    """Format a list of ad accounts as a markdown table.

    Args:
        accounts: List of ad account models.

    Returns:
        Formatted markdown table.
    """
    if not accounts:
        return "No ad accounts found."

    lines = [
        "## Ad Accounts",
        "",
        "| ID | Name | Status | Currency | Amount Spent |",
        "|---|---|---|---|---|",
    ]
    for acc in accounts:
        lines.append(
            f"| {acc.id} | {acc.name} | {acc.status_display} "
            f"| {acc.currency} | {acc.amount_spent_formatted} |"
        )
    return "\n".join(lines)


def format_campaign(campaign: CampaignModel) -> str:
    """Format a single campaign as markdown detail view.

    Args:
        campaign: The campaign model.

    Returns:
        Formatted markdown string.
    """
    categories = campaign.special_ad_categories
    categories_str = ", ".join(categories) if categories else "None"
    return f"""## Campaign: {campaign.name}

- **ID**: {campaign.id}
- **Status**: {campaign.status}
- **Effective Status**: {campaign.effective_status}
- **Configured Status**: {campaign.configured_status or 'N/A'}
- **Objective**: {campaign.objective}
- **Buying Type**: {campaign.buying_type or 'AUCTION'}
- **Bid Strategy**: {campaign.bid_strategy or 'Not set'}
- **Daily Budget**: {campaign.daily_budget_formatted}
- **Lifetime Budget**: {campaign.lifetime_budget_formatted}
- **Budget Remaining**: {campaign.budget_remaining_formatted}
- **Spend Cap**: {campaign.spend_cap_formatted}
- **Special Ad Categories**: {categories_str}
- **Start Time**: {campaign.start_time or 'Not set'}
- **Stop Time**: {campaign.stop_time or 'Not set'}
- **Created**: {campaign.created_time}
- **Updated**: {campaign.updated_time}"""


def format_campaign_list(campaigns: list[CampaignModel]) -> str:
    """Format a list of campaigns as a markdown table.

    Args:
        campaigns: List of campaign models.

    Returns:
        Formatted markdown table.
    """
    if not campaigns:
        return "No campaigns found."

    lines = [
        "## Campaigns",
        "",
        "| ID | Name | Status | Effective Status | Objective | Daily Budget |",
        "|---|---|---|---|---|---|",
    ]
    for c in campaigns:
        lines.append(
            f"| {c.id} | {c.name} | {c.status} | {c.effective_status} "
            f"| {c.objective} | {c.daily_budget_formatted} |"
        )
    return "\n".join(lines)


def format_ad_set(ad_set: AdSetModel) -> str:
    """Format a single ad set as markdown detail view.

    Args:
        ad_set: The ad set model.

    Returns:
        Formatted markdown string.
    """
    return f"""## Ad Set: {ad_set.name}

- **ID**: {ad_set.id}
- **Campaign ID**: {ad_set.campaign_id}
- **Status**: {ad_set.status}
- **Effective Status**: {ad_set.effective_status}
- **Daily Budget**: {ad_set.daily_budget_formatted}
- **Lifetime Budget**: {ad_set.lifetime_budget_formatted}
- **Budget Remaining**: {ad_set.budget_remaining_formatted}
- **Bid Strategy**: {ad_set.bid_strategy or 'Not set'}
- **Bid Amount**: {ad_set.bid_amount_formatted}
- **Billing Event**: {ad_set.billing_event}
- **Optimization Goal**: {ad_set.optimization_goal}
- **Destination Type**: {ad_set.destination_type or 'N/A'}
- **Frequency Cap**: {ad_set.frequency_cap_summary}
- **Dynamic Creative**: {'Yes' if ad_set.is_dynamic_creative else 'No'}
- **Targeting**: {ad_set.targeting_summary}
- **Start Time**: {ad_set.start_time or 'Not set'}
- **End Time**: {ad_set.end_time or 'Not set'}"""


def format_ad_set_list(ad_sets: list[AdSetModel]) -> str:
    """Format a list of ad sets as a markdown table.

    Args:
        ad_sets: List of ad set models.

    Returns:
        Formatted markdown table.
    """
    if not ad_sets:
        return "No ad sets found."

    lines = [
        "## Ad Sets",
        "",
        "| ID | Name | Status | Campaign ID | Daily Budget | Optimization |",
        "|---|---|---|---|---|---|",
    ]
    for a in ad_sets:
        lines.append(
            f"| {a.id} | {a.name} | {a.effective_status} | {a.campaign_id} "
            f"| {a.daily_budget_formatted} | {a.optimization_goal} |"
        )
    return "\n".join(lines)


def format_ad(ad: AdModel) -> str:
    """Format a single ad as markdown detail view.

    Args:
        ad: The ad model.

    Returns:
        Formatted markdown string.
    """
    lines = [f"## Ad: {ad.name}", ""]
    lines.append(f"- **ID**: {ad.id}")
    lines.append(f"- **Status**: {ad.status}")
    lines.append(f"- **Effective Status**: {ad.effective_status}")
    if ad.configured_status:
        lines.append(f"- **Configured Status**: {ad.configured_status}")
    lines.append(f"- **Ad Set ID**: {ad.adset_id}")
    lines.append(f"- **Campaign ID**: {ad.campaign_id}")
    lines.append(f"- **Creative ID**: {ad.creative_id}")
    if ad.preview_shareable_link:
        lines.append(f"- **Preview Link**: {ad.preview_shareable_link}")
    lines.append(f"- **Created**: {ad.created_time}")
    lines.append(f"- **Updated**: {ad.updated_time}")
    return "\n".join(lines)


def format_ad_list(ads: list[AdModel]) -> str:
    """Format a list of ads as a markdown table.

    Args:
        ads: List of ad models.

    Returns:
        Formatted markdown table.
    """
    if not ads:
        return "No ads found."

    lines = [
        "## Ads",
        "",
        "| ID | Name | Status | Effective Status | Ad Set ID | Creative ID |",
        "|---|---|---|---|---|---|",
    ]
    for ad in ads:
        lines.append(
            f"| {ad.id} | {ad.name} | {ad.status} | {ad.effective_status} "
            f"| {ad.adset_id} | {ad.creative_id} |"
        )
    return "\n".join(lines)


def format_creative(creative: AdCreativeModel) -> str:
    """Format a single ad creative as markdown detail view.

    Args:
        creative: The ad creative model.

    Returns:
        Formatted markdown string.
    """
    lines = [f"## Creative: {creative.name}", ""]
    lines.append(f"- **ID**: {creative.id}")
    if creative.status:
        lines.append(f"- **Status**: {creative.status}")
    lines.append(f"- **Title**: {creative.title or 'Not set'}")
    lines.append(f"- **Body**: {creative.body or 'Not set'}")
    lines.append(f"- **CTA**: {creative.call_to_action_type or 'Not set'}")
    lines.append(f"- **Link URL**: {creative.link_url or 'Not set'}")
    lines.append(f"- **Image URL**: {creative.image_url or 'Not set'}")
    if creative.image_hash:
        lines.append(f"- **Image Hash**: {creative.image_hash}")
    lines.append(f"- **Thumbnail URL**: {creative.thumbnail_url or 'Not set'}")
    if creative.url_tags:
        lines.append(f"- **URL Tags**: {creative.url_tags}")
    if creative.object_story_spec:
        lines.append(f"- **Object Story**: {creative.object_story_summary}")
    return "\n".join(lines)


def format_creative_list(creatives: list[AdCreativeModel]) -> str:
    """Format a list of ad creatives as a markdown table.

    Args:
        creatives: List of ad creative models.

    Returns:
        Formatted markdown table.
    """
    if not creatives:
        return "No creatives found."

    lines = [
        "## Ad Creatives",
        "",
        "| ID | Name | Title | CTA | Link URL |",
        "|---|---|---|---|---|",
    ]
    for c in creatives:
        link = c.link_url[:40] + "..." if len(c.link_url) > 40 else c.link_url
        lines.append(
            f"| {c.id} | {c.name} | {c.title} " f"| {c.call_to_action_type} | {link} |"
        )
    return "\n".join(lines)


def format_insights_table(
    rows: list[InsightRow], title: str = "Performance Insights"
) -> str:
    """Format insight rows as a dynamic markdown table.

    Automatically detects the reporting level and breakdowns from the data
    to build appropriate columns.

    Args:
        rows: List of insight row models.
        title: Table title.

    Returns:
        Formatted markdown table.
    """
    if not rows:
        return "No insights data found."

    # Detect level and breakdowns from first row
    first = rows[0]

    # Build dynamic columns based on data level
    columns: list[tuple[str, str]] = []

    if first.campaign_name:
        columns.append(("Campaign", "campaign_name"))
    if first.adset_name:
        columns.append(("Ad Set", "adset_name"))
    if first.ad_name:
        columns.append(("Ad", "ad_name"))

    # Add breakdown columns
    breakdown_fields = [
        ("Age", "age"),
        ("Gender", "gender"),
        ("Country", "country"),
        ("Placement", "placement"),
        ("Device", "device_platform"),
        ("Publisher", "publisher_platform"),
    ]
    for label, field in breakdown_fields:
        if getattr(first, field, ""):
            columns.append((label, field))

    # Add date range
    columns.append(("Period", "_period"))

    # Add metric columns
    metric_columns = [
        ("Impressions", "impressions"),
        ("Clicks", "clicks"),
        ("Spend", "spend"),
        ("CTR", "ctr"),
        ("CPC", "cpc"),
        ("CPM", "cpm"),
        ("Reach", "reach"),
    ]
    columns.extend(metric_columns)

    # Build header
    headers = [col[0] for col in columns]
    lines = [
        f"## {title}",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]

    # Build rows
    for row in rows:
        cells: list[str] = []
        for _, field in columns:
            if field == "_period":
                cells.append(f"{row.date_start} to {row.date_stop}")
            elif field == "spend":
                cells.append(f"${float(row.spend):,.2f}")
            elif field in ("ctr", "cpc", "cpm"):
                val = getattr(row, field)
                cells.append(f"{float(val):,.2f}" if val else "0.00")
            elif field in ("impressions", "clicks", "reach"):
                val = getattr(row, field)
                cells.append(f"{int(val):,}" if val else "0")
            else:
                cells.append(str(getattr(row, field, "")))
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def format_audience(audience: CustomAudienceModel) -> str:
    """Format a single custom audience as markdown detail view.

    Args:
        audience: The custom audience model.

    Returns:
        Formatted markdown string.
    """
    delivery = audience.delivery_status.get("status", "Unknown")
    operation = audience.operation_status.get("status", "Unknown")

    lines = [f"## Audience: {audience.name}", ""]
    lines.append(f"- **ID**: {audience.id}")
    lines.append(f"- **Subtype**: {audience.subtype}")
    lines.append(f"- **Size**: {audience.size_display}")
    lines.append(f"- **Delivery Status**: {delivery}")
    lines.append(f"- **Operation Status**: {operation}")
    lines.append(f"- **Description**: {audience.description or 'No description'}")
    if audience.retention_days:
        lines.append(f"- **Retention Days**: {audience.retention_days}")
    if audience.is_value_based:
        lines.append("- **Value-Based**: Yes")
    if audience.sharing_status:
        lines.append(f"- **Sharing Status**: {audience.sharing_status}")
    if audience.lookalike_spec:
        lines.append(f"- **Lookalike**: {audience.lookalike_summary}")
    if audience.data_source:
        lines.append(f"- **Data Source**: {audience.data_source_summary}")
    if audience.time_created:
        lines.append(f"- **Created**: {audience.time_created}")
    if audience.time_updated:
        lines.append(f"- **Updated**: {audience.time_updated}")
    return "\n".join(lines)


def format_audience_list(audiences: list[CustomAudienceModel]) -> str:
    """Format a list of custom audiences as a markdown table.

    Args:
        audiences: List of custom audience models.

    Returns:
        Formatted markdown table.
    """
    if not audiences:
        return "No audiences found."

    lines = [
        "## Custom Audiences",
        "",
        "| ID | Name | Subtype | Size | Description |",
        "|---|---|---|---|---|",
    ]
    for a in audiences:
        desc = a.description[:30] + "..." if len(a.description) > 30 else a.description
        lines.append(
            f"| {a.id} | {a.name} | {a.subtype} "
            f"| {a.size_display} | {desc or 'N/A'} |"
        )
    return "\n".join(lines)


def format_insights_comparison(
    current: InsightRow | None,
    previous: InsightRow | None,
    current_label: str,
    previous_label: str,
) -> str:
    """Format a period-over-period comparison of insight metrics.

    Shows metrics as rows with columns for Current, Previous, Change, and Change %.

    Args:
        current: Current period insight row, or None if no data.
        previous: Previous period insight row, or None if no data.
        current_label: Label for the current period (e.g., date range).
        previous_label: Label for the previous period.

    Returns:
        Formatted markdown comparison table.
    """
    if not current and not previous:
        return "No insights data found for either period."

    metrics = [
        ("Impressions", "impressions", "int"),
        ("Clicks", "clicks", "int"),
        ("Spend", "spend", "dollar"),
        ("CTR", "ctr", "pct"),
        ("CPC", "cpc", "dollar"),
        ("CPM", "cpm", "dollar"),
        ("Reach", "reach", "int"),
    ]

    lines = [
        "## Period Comparison",
        "",
        f"| Metric | {current_label} | {previous_label} | Change | Change % |",
        "|---|---|---|---|---|",
    ]

    for label, field, fmt in metrics:
        cur_val = float(getattr(current, field, "0")) if current else 0.0
        prev_val = float(getattr(previous, field, "0")) if previous else 0.0
        delta = cur_val - prev_val
        pct = (delta / prev_val * 100) if prev_val != 0 else 0.0

        if fmt == "dollar":
            cur_str = f"${cur_val:,.2f}"
            prev_str = f"${prev_val:,.2f}"
            delta_str = f"${delta:+,.2f}"
        elif fmt == "pct":
            cur_str = f"{cur_val:.2f}%"
            prev_str = f"{prev_val:.2f}%"
            delta_str = f"{delta:+.2f}%"
        else:
            cur_str = f"{int(cur_val):,}"
            prev_str = f"{int(prev_val):,}"
            delta_str = f"{int(delta):+,}"

        pct_str = f"{pct:+.1f}%" if prev_val != 0 else "N/A"
        lines.append(f"| {label} | {cur_str} | {prev_str} | {delta_str} | {pct_str} |")

    return "\n".join(lines)


def format_performance_comparison(
    rows_by_entity: dict[str, InsightRow],
    entity_type: str,
) -> str:
    """Format a side-by-side performance comparison across multiple entities.

    Shows metrics as rows with one column per entity.

    Args:
        rows_by_entity: Mapping of entity name/label to insight row.
        entity_type: Type of entity being compared (campaign, adset, ad).

    Returns:
        Formatted markdown comparison table.
    """
    if not rows_by_entity:
        return f"No data to compare for {entity_type}s."

    entities = list(rows_by_entity.keys())
    rows = list(rows_by_entity.values())

    metrics = [
        ("Impressions", "impressions", "int"),
        ("Clicks", "clicks", "int"),
        ("Spend", "spend", "dollar"),
        ("CTR", "ctr", "pct"),
        ("CPC", "cpc", "dollar"),
        ("CPM", "cpm", "dollar"),
        ("Reach", "reach", "int"),
    ]

    header = "| Metric | " + " | ".join(entities) + " |"
    separator = "|---|" + "|".join(["---"] * len(entities)) + "|"
    lines = [
        f"## {entity_type.title()} Performance Comparison",
        "",
        header,
        separator,
    ]

    for label, field, fmt in metrics:
        cells = [label]
        for row in rows:
            val = float(getattr(row, field, "0"))
            if fmt == "dollar":
                cells.append(f"${val:,.2f}")
            elif fmt == "pct":
                cells.append(f"{val:.2f}%")
            else:
                cells.append(f"{int(val):,}")
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


_PAUSED_ON_CREATE_TYPES: frozenset[str] = frozenset({"Campaign", "Ad Set", "Ad"})


def format_write_result(
    action: str,
    entity_type: str,
    detail: str,
    dry_run: bool = False,
) -> str:
    """Format the result of a create operation as markdown.

    Prepends a success/dry-run header to existing entity detail output.

    Args:
        action: The action performed (e.g., "Created", "Updated").
        entity_type: The entity type (e.g., "Campaign", "Ad Set", "Ad").
        detail: The formatted entity detail string.
        dry_run: Whether this was a dry run (validation only).

    Returns:
        Formatted markdown string with header and entity detail.
    """
    is_paused = action == "Created" and entity_type in _PAUSED_ON_CREATE_TYPES
    status_note = "PAUSED" if is_paused else ""
    header = f"> **{entity_type} {action}**"
    if status_note:
        header += f" | Status: {status_note}"
    lines = [header]
    if dry_run:
        lines.append("> _Dry run — no changes were made._")
    lines.append("")
    lines.append(detail)
    return "\n".join(lines)


def format_update_result(
    entity_type: str,
    entity_id: str,
    changes: dict[str, tuple[str, str]],
    detail: str,
    dry_run: bool = False,
) -> str:
    """Format the result of an update operation as markdown.

    Shows a before/after changes table followed by entity detail.

    Args:
        entity_type: The entity type (e.g., "Campaign", "Ad Set", "Ad").
        entity_id: The entity ID.
        changes: Mapping of field name to (before, after) tuples.
        detail: The formatted entity detail string.
        dry_run: Whether this was a dry run (validation only).

    Returns:
        Formatted markdown string with changes table and entity detail.
    """
    header = f"> **{entity_type} Updated** | ID: {entity_id}"
    lines = [header]
    if dry_run:
        lines.append("> _Dry run — no changes were made._")
    lines.append("")

    if changes:
        lines.append("### Changes Applied")
        lines.append("")
        lines.append("| Field | Before | After |")
        lines.append("|---|---|---|")
        for field, (before, after) in changes.items():
            lines.append(f"| {field} | {before} | {after} |")
        lines.append("")

    lines.append(detail)
    return "\n".join(lines)


def format_error(
    message: str,
    error_code: int | None = None,
    hint: str = "",
) -> str:
    """Format an error message as markdown.

    Args:
        message: The error message.
        error_code: Optional Meta API error code.
        hint: Optional actionable suggestion.

    Returns:
        Formatted markdown error string.
    """
    lines = [f"## Error\n\n{message}"]
    if error_code is not None:
        lines.append(f"\n**Error Code**: {error_code}")
    if hint:
        lines.append(f"\n**Suggestion**: {hint}")
    return "".join(lines)


def format_diagnostics(
    entity_type: str,
    name: str,
    issues: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> str:
    """Format diagnostic issues and recommendations as markdown.

    Args:
        entity_type: The entity type (e.g., "Campaign", "Ad Set", "Ad").
        name: The entity name.
        issues: List of issue dictionaries with level and summary keys.
        recommendations: List of recommendation dictionaries.

    Returns:
        Formatted markdown string with issues and recommendations.
    """
    lines = [f"## {entity_type} Diagnostics: {name}", ""]

    lines.append("### Issues")
    if not issues:
        lines.append("No issues found.")
    else:
        for issue in issues:
            level = issue.get("level", "unknown")
            summary = issue.get("summary", "No summary")
            lines.append(f"- **[{level.upper()}]** {summary}")
    lines.append("")

    lines.append("### Recommendations")
    if not recommendations:
        lines.append("No recommendations.")
    else:
        for rec in recommendations:
            title = rec.get("title", "")
            message = rec.get("message", "No details")
            if title:
                lines.append(f"- **{title}**: {message}")
            else:
                lines.append(f"- {message}")

    return "\n".join(lines)


def format_learning_stage(info: dict[str, Any]) -> str:
    """Format learning stage info as a markdown section.

    Args:
        info: Learning stage info dictionary with status key.

    Returns:
        Formatted markdown section for learning stage.
    """
    if not info:
        return "### Learning Stage\n\nNo learning stage data available."

    status = info.get("status", "UNKNOWN")
    status_display = {
        "LEARNING": "Learning (gathering data)",
        "SUCCESS": "Learning Complete (exited learning)",
        "LEARNING_LIMITED": "Learning Limited (not enough conversions)",
    }
    display = status_display.get(status, status)

    lines = ["### Learning Stage", "", f"- **Status**: {display}"]
    if "info" in info:
        lines.append(f"- **Info**: {info['info']}")
    return "\n".join(lines)


def format_ad_review_feedback(feedback: dict[str, Any]) -> str:
    """Format ad review feedback as a markdown section.

    Args:
        feedback: Ad review feedback dictionary.

    Returns:
        Formatted markdown section for ad review.
    """
    if not feedback:
        return "### Ad Review\n\nNo review feedback available."

    lines = ["### Ad Review", ""]
    for key, value in feedback.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def format_delivery_checks(checks: list[dict[str, Any]]) -> str:
    """Format failed delivery checks as a markdown section.

    Args:
        checks: List of failed delivery check dictionaries.

    Returns:
        Formatted markdown section for delivery checks.
    """
    if not checks:
        return "### Delivery Checks\n\nAll delivery checks passed."

    lines = ["### Delivery Checks", ""]
    for check in checks:
        check_name = check.get("summary", "Unknown check")
        description = check.get("description", "")
        lines.append(f"- **{check_name}**")
        if description:
            lines.append(f"  {description}")
    return "\n".join(lines)
