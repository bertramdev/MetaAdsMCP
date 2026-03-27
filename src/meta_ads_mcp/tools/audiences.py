"""Audience management tools."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_audience,
    format_audience_list,
    format_error,
    format_write_result,
)
from meta_ads_mcp.models import CustomAudienceModel
from meta_ads_mcp.tools import CREATE, READ_ONLY, get_client
from meta_ads_mcp.tools._write_helpers import format_write_error, parse_json_param


async def list_audiences(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List custom and lookalike audiences for an ad account.

    Returns a table of audiences with ID, name, subtype, size, and description.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of audiences to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_audiences(account_id=account_id, limit=limit)
        models = [CustomAudienceModel(**d) for d in raw]
        return format_audience_list(models)
    except MetaAdsError as e:
        return format_error(
            e.message,
            error_code=e.error_code,
            hint=e.hint,
            blame_fields=e.blame_field_specs,
            error_subcode=e.error_subcode,
        )


async def get_audience(ctx: Context, audience_id: str) -> str:
    """Get detailed information for a specific custom audience.

    Shows audience name, subtype, size range, delivery status,
    operation status, and description.

    Args:
        audience_id: The audience ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_audience(audience_id)
        model = CustomAudienceModel(**raw)
        return format_audience(model)
    except MetaAdsError as e:
        return format_error(
            e.message,
            error_code=e.error_code,
            hint=e.hint,
            blame_fields=e.blame_field_specs,
            error_subcode=e.error_subcode,
        )


async def create_custom_audience(
    ctx: Context,
    name: str,
    subtype: str,
    description: str | None = None,
    rule: str | None = None,
    pixel_id: str | None = None,
    retention_days: int | None = None,
    customer_file_source: str | None = None,
    prefill: bool | None = None,
    account_id: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new custom audience.

    Creates a custom audience for targeting. Supports website audiences
    (with pixel_id and rule), customer list audiences, and app audiences.

    Args:
        name: Audience name.
        subtype: Audience subtype (CUSTOM, WEBSITE, APP).
        description: Audience description. Optional.
        rule: Audience rule as JSON string (for WEBSITE subtype). Optional.
        pixel_id: Pixel ID for website audiences. Optional.
        retention_days: Days to retain audience members. Optional.
        customer_file_source: Source for customer file audiences. Optional.
        prefill: Whether to prefill with existing data. Optional.
        account_id: Ad account ID (e.g., act_123456789). Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        rule_dict: dict[str, Any] | None = None
        if rule:
            rule_dict = parse_json_param(rule, "rule")

        raw = await client.create_custom_audience(
            name=name,
            subtype=subtype,
            account_id=account_id,
            description=description,
            rule=rule_dict,
            pixel_id=pixel_id,
            retention_days=retention_days,
            customer_file_source=customer_file_source,
            prefill=prefill,
            dry_run=dry_run,
        )

        model = CustomAudienceModel(
            id=raw.get("id", ""),
            name=name,
            subtype=subtype,
            description=description or "",
            retention_days=retention_days or 0,
        )
        detail = format_audience(model)
        return format_write_result("Created", "Audience", detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def create_lookalike_audience(
    ctx: Context,
    name: str,
    origin_audience_id: str,
    country: str,
    ratio: float = 0.01,
    description: str | None = None,
    account_id: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new lookalike audience from an existing audience.

    Creates a lookalike audience that targets people similar to the
    source audience in the specified country.

    Args:
        name: Audience name.
        origin_audience_id: Source audience ID to base the lookalike on.
        country: Target country code (e.g., "US").
        ratio: Lookalike ratio from 0.01 to 0.20 (1%% to 20%%). Default 0.01.
        description: Audience description. Optional.
        account_id: Ad account ID (e.g., act_123456789). Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        if not 0.01 <= ratio <= 0.20:
            raise ValueError(f"Ratio must be between 0.01 and 0.20, got {ratio}")

        raw = await client.create_lookalike_audience(
            name=name,
            origin_audience_id=origin_audience_id,
            country=country,
            ratio=ratio,
            account_id=account_id,
            description=description,
            dry_run=dry_run,
        )

        model = CustomAudienceModel(
            id=raw.get("id", ""),
            name=name,
            subtype="LOOKALIKE",
            description=description or "",
            lookalike_spec={
                "origin_audience_id": origin_audience_id,
                "country": country,
                "ratio": ratio,
            },
        )
        detail = format_audience(model)
        return format_write_result("Created", "Audience", detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


def register(mcp: FastMCP) -> None:
    """Register audience tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool(annotations=READ_ONLY)(list_audiences)
    mcp.tool(annotations=READ_ONLY)(get_audience)
    mcp.tool(annotations=CREATE)(create_custom_audience)
    mcp.tool(annotations=CREATE)(create_lookalike_audience)
