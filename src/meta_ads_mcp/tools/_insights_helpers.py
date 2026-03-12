"""Date range resolution and period comparison helpers for insights tools."""

from datetime import date, datetime, timedelta

VALID_BREAKDOWNS = frozenset(
    {
        "age",
        "gender",
        "country",
        "placement",
        "device_platform",
        "publisher_platform",
    }
)


def resolve_date_preset(preset: str) -> tuple[str, str]:
    """Map a date preset like 'last_7d' to (since, until) date strings.

    Args:
        preset: A Meta Ads date preset string.

    Returns:
        Tuple of (since, until) in YYYY-MM-DD format.

    Raises:
        ValueError: If the preset is not recognized.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    presets: dict[str, tuple[date, date]] = {
        "today": (today, today),
        "yesterday": (yesterday, yesterday),
        "last_7d": (today - timedelta(days=7), yesterday),
        "last_14d": (today - timedelta(days=14), yesterday),
        "last_30d": (today - timedelta(days=30), yesterday),
        "this_month": (today.replace(day=1), today),
        "last_month": (
            (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            today.replace(day=1) - timedelta(days=1),
        ),
    }

    if preset not in presets:
        raise ValueError(
            f"Unknown date preset '{preset}'. "
            f"Valid presets: {', '.join(sorted(presets))}"
        )

    since, until = presets[preset]
    return since.isoformat(), until.isoformat()


def get_previous_range(since: str, until: str) -> tuple[str, str]:
    """Shift a date range back by its duration for period-over-period comparison.

    Args:
        since: Start date in YYYY-MM-DD format.
        until: End date in YYYY-MM-DD format.

    Returns:
        Tuple of (previous_since, previous_until) in YYYY-MM-DD format.
    """
    start = datetime.strptime(since, "%Y-%m-%d").date()
    end = datetime.strptime(until, "%Y-%m-%d").date()
    duration = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=duration - 1)
    return prev_start.isoformat(), prev_end.isoformat()
