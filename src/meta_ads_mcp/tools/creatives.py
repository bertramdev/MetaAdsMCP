"""Creative management tools."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_creative,
    format_creative_list,
    format_error,
    format_update_result,
    format_write_result,
)
from meta_ads_mcp.models import AdCreativeModel
from meta_ads_mcp.tools import get_client
from meta_ads_mcp.tools._write_helpers import (
    fetch_and_update,
    format_write_error,
    merge_updates,
    validate_status,
)


async def list_creatives(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List ad creatives for an ad account.

    Returns a table of creatives with ID, name, title, CTA, and link URL.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of creatives to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_creatives(account_id=account_id, limit=limit)
        models = [AdCreativeModel(**d) for d in raw]
        return format_creative_list(models)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def get_creative(ctx: Context, creative_id: str) -> str:
    """Get detailed information for a specific ad creative.

    Shows creative name, title, body, CTA, link URL, image URL, and thumbnail.

    Args:
        creative_id: The creative ID.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_creative(creative_id)
        model = AdCreativeModel(**raw)
        return format_creative(model)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def create_ad_creative(
    ctx: Context,
    name: str,
    page_id: str,
    link: str,
    message: str = "",
    headline: str = "",
    description: str = "",
    image_hash: str | None = None,
    image_url: str | None = None,
    call_to_action_type: str | None = None,
    url_tags: str | None = None,
    account_id: str | None = None,
    dry_run: bool = False,
) -> str:
    """Create a new link ad creative.

    Builds an object_story_spec from user-friendly parameters. The creative
    is created under the specified ad account.

    Args:
        name: Creative name.
        page_id: Facebook Page ID to post from.
        link: Destination URL for the ad.
        message: Post text shown above the ad. Optional.
        headline: Ad headline. Optional.
        description: Ad description text. Optional.
        image_hash: Hash of a previously uploaded image. Optional.
        image_url: URL of the image to use. Optional.
        call_to_action_type: CTA button type (e.g., LEARN_MORE, SHOP_NOW). Optional.
        url_tags: URL tags for tracking (e.g., utm_source=facebook). Optional.
        account_id: Ad account ID (e.g., act_123456789). Optional.
        dry_run: If True, validate without creating. Default False.
    """
    try:
        client = get_client(ctx)

        # Build link_data for object_story_spec
        link_data: dict[str, Any] = {"link": link}
        if message:
            link_data["message"] = message
        if headline:
            link_data["name"] = headline
        if description:
            link_data["description"] = description
        if image_hash:
            link_data["image_hash"] = image_hash
        elif image_url:
            link_data["picture"] = image_url
        if call_to_action_type:
            link_data["call_to_action"] = {
                "type": call_to_action_type,
                "value": {"link": link},
            }

        object_story_spec: dict[str, Any] = {
            "page_id": page_id,
            "link_data": link_data,
        }

        raw = await client.create_ad_creative(
            name=name,
            object_story_spec=object_story_spec,
            account_id=account_id,
            url_tags=url_tags,
            dry_run=dry_run,
        )

        model = AdCreativeModel(
            id=raw.get("id", ""),
            name=name,
            link_url=link,
            call_to_action_type=call_to_action_type or "",
        )
        detail = format_creative(model)
        return format_write_result("Created", "Creative", detail, dry_run=dry_run)
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


async def update_ad_creative(
    ctx: Context,
    creative_id: str,
    name: str | None = None,
    url_tags: str | None = None,
    status: str | None = None,
    dry_run: bool = False,
) -> str:
    """Update an existing ad creative's metadata.

    Can update name, URL tags, and status. Note: Meta does not allow
    updating the object_story_spec on existing creatives — create a new
    creative instead.

    Args:
        creative_id: The creative ID to update.
        name: New creative name. Optional.
        url_tags: New URL tags for tracking. Optional.
        status: New status (ACTIVE, ARCHIVED). Optional.
        dry_run: If True, validate without updating. Default False.
    """
    try:
        client = get_client(ctx)

        if status is not None:
            status = validate_status(status)

        current = await fetch_and_update(
            client.get_creative(creative_id),
            client.update_ad_creative(
                creative_id=creative_id,
                name=name,
                url_tags=url_tags,
                status=status,
                dry_run=dry_run,
            ),
        )

        changes: dict[str, tuple[str, str]] = {}
        if name is not None:
            changes["Name"] = (current.get("name", ""), name)
        if url_tags is not None:
            changes["URL Tags"] = (current.get("url_tags", ""), url_tags)
        if status is not None:
            changes["Status"] = (current.get("status", ""), status)

        model = AdCreativeModel(
            **merge_updates(
                current, {"name": name, "url_tags": url_tags, "status": status}
            )
        )
        detail = format_creative(model)
        return format_update_result(
            "Creative", creative_id, changes, detail, dry_run=dry_run
        )
    except (MetaAdsError, ValueError) as e:
        return format_write_error(e)


def register(mcp: FastMCP) -> None:
    """Register creative tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(list_creatives)
    mcp.tool()(get_creative)
    mcp.tool()(create_ad_creative)
    mcp.tool()(update_ad_creative)
