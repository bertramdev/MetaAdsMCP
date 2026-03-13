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


def _quarter_start(d: date) -> date:
    """Return the first day of the quarter containing *d*."""
    quarter_month = ((d.month - 1) // 3) * 3 + 1
    return d.replace(month=quarter_month, day=1)


def _prev_quarter_start(d: date) -> date:
    """Return the first day of the previous quarter."""
    qs = _quarter_start(d)
    # Go back one day into previous quarter, then find its start
    return _quarter_start(qs - timedelta(days=1))


def _prev_quarter_end(d: date) -> date:
    """Return the last day of the previous quarter."""
    return _quarter_start(d) - timedelta(days=1)


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
        "last_3d": (today - timedelta(days=3), yesterday),
        "last_90d": (today - timedelta(days=90), yesterday),
        "this_year": (today.replace(month=1, day=1), today),
        "last_year": (
            today.replace(year=today.year - 1, month=1, day=1),
            today.replace(year=today.year - 1, month=12, day=31),
        ),
        "this_quarter": (_quarter_start(today), today),
        "last_quarter": (_prev_quarter_start(today), _prev_quarter_end(today)),
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
