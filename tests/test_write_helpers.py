"""Tests for write helper utilities."""

import pytest

from meta_ads_mcp.tools._write_helpers import (
    dollars_to_cents,
    parse_json_param,
    validate_status,
)


class TestDollarsToCents:
    """Tests for dollars_to_cents."""

    def test_whole_dollars(self) -> None:
        """Converts whole dollar amounts."""
        assert dollars_to_cents("50") == 5000

    def test_dollars_and_cents(self) -> None:
        """Converts dollars with cents."""
        assert dollars_to_cents("50.00") == 5000
        assert dollars_to_cents("25.50") == 2550

    def test_fractional_cents(self) -> None:
        """Handles sub-cent precision by truncating."""
        assert dollars_to_cents("10.999") == 1099

    def test_zero(self) -> None:
        """Zero is a valid amount."""
        assert dollars_to_cents("0") == 0
        assert dollars_to_cents("0.00") == 0

    def test_large_amount(self) -> None:
        """Handles large budget values."""
        assert dollars_to_cents("10000.00") == 1000000

    def test_negative_raises(self) -> None:
        """Negative values are rejected."""
        with pytest.raises(ValueError, match="negative"):
            dollars_to_cents("-50.00")

    def test_invalid_string_raises(self) -> None:
        """Non-numeric strings are rejected."""
        with pytest.raises(ValueError, match="Invalid dollar amount"):
            dollars_to_cents("abc")

    def test_empty_string_raises(self) -> None:
        """Empty strings are rejected."""
        with pytest.raises(ValueError, match="Invalid dollar amount"):
            dollars_to_cents("")


class TestValidateStatus:
    """Tests for validate_status."""

    def test_active(self) -> None:
        """ACTIVE is valid."""
        assert validate_status("ACTIVE") == "ACTIVE"

    def test_paused(self) -> None:
        """PAUSED is valid."""
        assert validate_status("PAUSED") == "PAUSED"

    def test_archived(self) -> None:
        """ARCHIVED is valid."""
        assert validate_status("ARCHIVED") == "ARCHIVED"

    def test_case_insensitive(self) -> None:
        """Status is normalized to uppercase."""
        assert validate_status("active") == "ACTIVE"
        assert validate_status("Paused") == "PAUSED"

    def test_deleted_rejected(self) -> None:
        """DELETED is not an allowed status."""
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status("DELETED")

    def test_invalid_rejected(self) -> None:
        """Arbitrary strings are rejected."""
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status("RUNNING")


class TestParseJsonParam:
    """Tests for parse_json_param."""

    def test_valid_object(self) -> None:
        """Parses valid JSON object."""
        result = parse_json_param('{"key": "value"}', "targeting")
        assert result == {"key": "value"}

    def test_nested_object(self) -> None:
        """Parses nested JSON object."""
        result = parse_json_param(
            '{"geo_locations": {"countries": ["US"]}}',
            "targeting",
        )
        assert result["geo_locations"]["countries"] == ["US"]

    def test_invalid_json_raises(self) -> None:
        """Invalid JSON string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON for targeting"):
            parse_json_param("not json", "targeting")

    def test_json_array_raises(self) -> None:
        """JSON arrays are rejected (must be object)."""
        with pytest.raises(ValueError, match="must be a JSON object"):
            parse_json_param("[1, 2, 3]", "targeting")

    def test_json_string_raises(self) -> None:
        """JSON strings are rejected (must be object)."""
        with pytest.raises(ValueError, match="must be a JSON object"):
            parse_json_param('"just a string"', "targeting")
