"""Asset management tools for image and video upload and listing."""

from mcp.server.fastmcp import Context, FastMCP

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import (
    format_ad_image,
    format_ad_image_list,
    format_ad_video,
    format_ad_video_list,
    format_error,
    format_write_result,
)
from meta_ads_mcp.models import AdImageModel, AdVideoModel
from meta_ads_mcp.tools import (
    CREATE,
    READ_ONLY,
    get_client,
)


async def upload_ad_image(
    ctx: Context,
    file_path: str,
    name: str | None = None,
    account_id: str | None = None,
) -> str:
    """Upload an image file to a Meta ad account.

    Returns the image hash needed for creating ad creatives. The image
    must be a local file accessible to the MCP server.

    Args:
        file_path: Local file path to the image (e.g., /path/to/image.jpg).
        name: Optional name for the uploaded image.
        account_id: The ad account ID (e.g., act_123456789). Optional.
    """
    try:
        client = get_client(ctx)
        raw = await client.upload_ad_image(
            file_path=file_path,
            name=name,
            account_id=account_id,
        )
        model = AdImageModel(**raw)
        detail = format_ad_image(model)
        return format_write_result("Uploaded", "Ad Image", detail)
    except (MetaAdsError, ValueError) as e:
        if isinstance(e, MetaAdsError):
            return format_error(e.message, error_code=e.error_code, hint=e.hint)
        return format_error(str(e))


async def upload_ad_video(
    ctx: Context,
    file_path: str | None = None,
    file_url: str | None = None,
    name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    account_id: str | None = None,
) -> str:
    """Upload a video to a Meta ad account.

    Accepts either a local file path or a URL that Meta will fetch directly.
    Returns the video ID needed for creating video ad creatives. Video
    encoding happens asynchronously — use get_ad_video to check status.

    Args:
        file_path: Local file path to the video. Provide this OR file_url.
        file_url: URL for Meta to fetch the video from. Provide this OR file_path.
        name: Optional name for the video.
        title: Optional title for the video.
        description: Optional description for the video.
        account_id: The ad account ID (e.g., act_123456789). Optional.
    """
    if not file_path and not file_url:
        return format_error("Either file_path or file_url must be provided.")

    try:
        client = get_client(ctx)
        raw = await client.upload_ad_video(
            file_path=file_path,
            file_url=file_url,
            name=name,
            title=title,
            description=description,
            account_id=account_id,
        )
        model = AdVideoModel(**raw)
        detail = format_ad_video(model)
        return format_write_result("Uploaded", "Ad Video", detail)
    except (MetaAdsError, ValueError) as e:
        if isinstance(e, MetaAdsError):
            return format_error(e.message, error_code=e.error_code, hint=e.hint)
        return format_error(str(e))


async def list_ad_images(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List ad images for an ad account.

    Returns a table of images with hash, name, dimensions, and status.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of images to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_images(account_id=account_id, limit=limit)
        models = [AdImageModel(**d) for d in raw]
        return format_ad_image_list(models)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def get_ad_image(
    ctx: Context,
    image_hash: str,
    account_id: str | None = None,
) -> str:
    """Get detailed information for a specific ad image by its hash.

    Shows image hash, dimensions, URLs, and status.

    Args:
        image_hash: The image hash (returned by upload_ad_image).
        account_id: The ad account ID (e.g., act_123456789). Optional.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_image(image_hash=image_hash, account_id=account_id)
        model = AdImageModel(**raw)
        return format_ad_image(model)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def list_ad_videos(
    ctx: Context,
    account_id: str | None = None,
    limit: int = 50,
) -> str:
    """List ad videos for an ad account.

    Returns a table of videos with ID, name, title, and duration.

    Args:
        account_id: The ad account ID (e.g., act_123456789). Optional.
        limit: Maximum number of videos to return. Default 50.
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_videos(account_id=account_id, limit=limit)
        models = [AdVideoModel(**d) for d in raw]
        return format_ad_video_list(models)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


async def get_ad_video(ctx: Context, video_id: str) -> str:
    """Get detailed information for a specific ad video.

    Shows video ID, title, duration, source URL, and thumbnail.

    Args:
        video_id: The video ID (returned by upload_ad_video).
    """
    try:
        client = get_client(ctx)
        raw = await client.get_ad_video(video_id)
        model = AdVideoModel(**raw)
        return format_ad_video(model)
    except MetaAdsError as e:
        return format_error(e.message, error_code=e.error_code, hint=e.hint)


def register(mcp: FastMCP) -> None:
    """Register asset tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool(annotations=CREATE)(upload_ad_image)
    mcp.tool(annotations=CREATE)(upload_ad_video)
    mcp.tool(annotations=READ_ONLY)(list_ad_images)
    mcp.tool(annotations=READ_ONLY)(get_ad_image)
    mcp.tool(annotations=READ_ONLY)(list_ad_videos)
    mcp.tool(annotations=READ_ONLY)(get_ad_video)
