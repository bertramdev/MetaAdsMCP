"""Markdown formatters for all Meta Ads entity types.

All functions return formatted markdown strings suitable for LLM output.
"""

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
    return f"""## Campaign: {campaign.name}

- **ID**: {campaign.id}
- **Status**: {campaign.status}
- **Effective Status**: {campaign.effective_status}
- **Objective**: {campaign.objective}
- **Daily Budget**: {campaign.daily_budget_formatted}
- **Lifetime Budget**: {campaign.lifetime_budget_formatted}
- **Budget Remaining**: {campaign.budget_remaining_formatted}
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
- **Billing Event**: {ad_set.billing_event}
- **Optimization Goal**: {ad_set.optimization_goal}
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
    return f"""## Ad: {ad.name}

- **ID**: {ad.id}
- **Status**: {ad.status}
- **Effective Status**: {ad.effective_status}
- **Ad Set ID**: {ad.adset_id}
- **Campaign ID**: {ad.campaign_id}
- **Creative ID**: {ad.creative_id}
- **Created**: {ad.created_time}
- **Updated**: {ad.updated_time}"""


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
    return f"""## Creative: {creative.name}

- **ID**: {creative.id}
- **Title**: {creative.title or 'Not set'}
- **Body**: {creative.body or 'Not set'}
- **CTA**: {creative.call_to_action_type or 'Not set'}
- **Link URL**: {creative.link_url or 'Not set'}
- **Image URL**: {creative.image_url or 'Not set'}
- **Thumbnail URL**: {creative.thumbnail_url or 'Not set'}"""


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

    return f"""## Audience: {audience.name}

- **ID**: {audience.id}
- **Subtype**: {audience.subtype}
- **Size**: {audience.size_display}
- **Delivery Status**: {delivery}
- **Operation Status**: {operation}
- **Description**: {audience.description or 'No description'}"""


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


def format_error(message: str) -> str:
    """Format an error message as markdown.

    Args:
        message: The error message.

    Returns:
        Formatted markdown error string.
    """
    return f"## Error\n\n{message}"
