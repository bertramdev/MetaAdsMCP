"""Shared utilities for write tools."""

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from meta_ads_mcp.client import MetaAdsError
from meta_ads_mcp.formatting import format_error


def dollars_to_cents(value: str) -> int:
    """Convert a dollar string to cents integer.

    Args:
        value: Dollar amount as string (e.g., "50.00").

    Returns:
        Amount in cents as integer (e.g., 5000).

    Raises:
        ValueError: If the value is not a valid dollar amount.
    """
    try:
        amount = Decimal(value)
        if amount < 0:
            raise ValueError(f"Budget cannot be negative: {value}")
        return int(amount * 100)
    except InvalidOperation:
        raise ValueError(f"Invalid dollar amount: {value!r}")


_VALID_STATUSES = {"ACTIVE", "PAUSED", "ARCHIVED"}


def validate_status(status: str) -> str:
    """Validate that a status value is allowed for write operations.

    Args:
        status: The status string to validate.

    Returns:
        The validated status string (uppercased).

    Raises:
        ValueError: If the status is not ACTIVE, PAUSED, or ARCHIVED.
    """
    upper = status.upper()
    if upper not in _VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status!r}. Must be one of: ACTIVE, PAUSED, ARCHIVED"
        )
    return upper


def parse_json_param(value: str, param_name: str) -> dict[str, Any]:
    """Parse a JSON string parameter into a dictionary.

    Args:
        value: JSON string to parse.
        param_name: Parameter name for error messages.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If the string is not valid JSON or not a JSON object.
    """
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {param_name}: {e}")
    if not isinstance(parsed, dict):
        raise ValueError(
            f"{param_name} must be a JSON object, got {type(parsed).__name__}"
        )
    return parsed


def cents_display(cents: int | str) -> str:
    """Format a cents value as a dollar string.

    Args:
        cents: Amount in cents (int or string from API).

    Returns:
        Formatted string like "$50.00".
    """
    return f"${int(cents) / 100:,.2f}"


def merge_updates(current: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Merge non-None update values into a current-state dict.

    Args:
        current: Base dictionary from API fetch.
        updates: Field-value pairs; None values are skipped.

    Returns:
        Merged dictionary ready for model instantiation.
    """
    merged = {**current}
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


def format_write_error(e: Exception) -> str:
    """Format a write operation error as markdown.

    Handles both MetaAdsError (with .message) and plain exceptions.

    Args:
        e: The caught exception.

    Returns:
        Formatted error markdown string.
    """
    msg = e.message if isinstance(e, MetaAdsError) else str(e)
    return format_error(msg)


async def fetch_and_update(
    fetch_coro: Any,
    update_coro: Any,
) -> dict[str, Any]:
    """Fetch current state before applying an update.

    The fetch runs first to guarantee the returned dict reflects pre-update
    values, which are used for before/after comparisons in tool output.

    Args:
        fetch_coro: Coroutine that fetches current entity state.
        update_coro: Coroutine that performs the update.

    Returns:
        The fetched current state dictionary (pre-update).
    """
    current = await fetch_coro
    await update_coro
    return current  # type: ignore[no-any-return]
