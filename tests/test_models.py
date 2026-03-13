"""Tests for Pydantic v2 models."""

from meta_ads_mcp.models import (
    AdAccountModel,
    AdCreativeModel,
    AdModel,
    AdSetModel,
    CampaignModel,
    CustomAudienceModel,
    InsightRow,
)


class TestAdAccountModel:
    """Tests for AdAccountModel."""

    def test_construction_from_dict(self) -> None:
        """Model constructs from a typical API response dict."""
        data = {
            "id": "act_123456789",
            "name": "Test Account",
            "account_status": 1,
            "currency": "USD",
            "timezone_name": "America/New_York",
            "amount_spent": "150000",
            "balance": "5000",
            "spend_cap": "1000000",
        }
        model = AdAccountModel(**data)
        assert model.id == "act_123456789"
        assert model.name == "Test Account"
        assert model.currency == "USD"

    def test_extra_fields_ignored(self) -> None:
        """Extra fields from API are silently ignored."""
        data = {
            "id": "act_123",
            "name": "Test",
            "unknown_field": "should be ignored",
            "another_extra": 42,
        }
        model = AdAccountModel(**data)
        assert model.id == "act_123"
        assert not hasattr(model, "unknown_field")

    def test_status_display(self) -> None:
        """status_display returns human-readable status."""
        model = AdAccountModel(account_status=1)
        assert model.status_display == "Active"

        model = AdAccountModel(account_status=2)
        assert model.status_display == "Disabled"

        model = AdAccountModel(account_status=999)
        assert "Unknown" in model.status_display

    def test_amount_spent_formatted(self) -> None:
        """amount_spent_formatted converts cents to dollars."""
        model = AdAccountModel(amount_spent="150000")
        assert model.amount_spent_formatted == "$1,500.00"

    def test_balance_formatted(self) -> None:
        """balance_formatted converts cents to dollars."""
        model = AdAccountModel(balance="5000")
        assert model.balance_formatted == "$50.00"

    def test_balance_formatted_invalid(self) -> None:
        """balance_formatted falls back to raw value on invalid input."""
        model = AdAccountModel(balance="invalid")
        assert model.balance_formatted == "invalid"

    def test_spend_cap_formatted(self) -> None:
        """spend_cap_formatted converts cents to dollars."""
        model = AdAccountModel(spend_cap="1000000")
        assert model.spend_cap_formatted == "$10,000.00"

    def test_spend_cap_formatted_invalid(self) -> None:
        """spend_cap_formatted falls back to raw value on invalid input."""
        model = AdAccountModel(spend_cap="n/a")
        assert model.spend_cap_formatted == "n/a"

    def test_defaults(self) -> None:
        """Model has sensible defaults for all fields."""
        model = AdAccountModel()
        assert model.id == ""
        assert model.name == ""
        assert model.account_status == 0
        assert model.amount_spent == "0"


class TestCampaignModel:
    """Tests for CampaignModel."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "id": "camp_123",
            "name": "Spring Sale",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": "5000",
            "lifetime_budget": "0",
        }
        model = CampaignModel(**data)
        assert model.name == "Spring Sale"
        assert model.objective == "OUTCOME_TRAFFIC"

    def test_budget_formatting(self) -> None:
        """Budget properties format cents to dollars."""
        model = CampaignModel(daily_budget="5000", lifetime_budget="0")
        assert model.daily_budget_formatted == "$50.00"
        assert model.lifetime_budget_formatted == "Not set"

    def test_budget_remaining_formatted(self) -> None:
        """budget_remaining_formatted converts cents to dollars."""
        model = CampaignModel(budget_remaining="7500")
        assert model.budget_remaining_formatted == "$75.00"

    def test_budget_remaining_formatted_invalid(self) -> None:
        """budget_remaining_formatted falls back to raw value on invalid input."""
        model = CampaignModel(budget_remaining="unknown")
        assert model.budget_remaining_formatted == "unknown"

    def test_extra_ignored(self) -> None:
        """Extra fields are ignored."""
        model = CampaignModel(id="123", extra_field="ignored")  # type: ignore[call-arg]
        assert model.id == "123"

    def test_new_fields_defaults(self) -> None:
        """New v25 fields have sensible defaults."""
        model = CampaignModel()
        assert model.bid_strategy == ""
        assert model.spend_cap == "0"
        assert model.pacing_type == []
        assert model.buying_type == ""
        assert model.special_ad_categories == []
        assert model.configured_status == ""

    def test_spend_cap_formatted_zero(self) -> None:
        """spend_cap_formatted returns 'Not set' for zero."""
        model = CampaignModel(spend_cap="0")
        assert model.spend_cap_formatted == "Not set"

    def test_spend_cap_formatted_valid(self) -> None:
        """spend_cap_formatted converts cents to dollars."""
        model = CampaignModel(spend_cap="50000")
        assert model.spend_cap_formatted == "$500.00"

    def test_spend_cap_formatted_invalid(self) -> None:
        """spend_cap_formatted falls back to raw value on invalid input."""
        model = CampaignModel(spend_cap="n/a")
        assert model.spend_cap_formatted == "n/a"


class TestAdSetModel:
    """Tests for AdSetModel."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "id": "adset_123",
            "name": "Test Ad Set",
            "status": "ACTIVE",
            "campaign_id": "camp_456",
            "daily_budget": "2500",
            "targeting": {
                "geo_locations": {"countries": ["US", "CA"]},
                "age_min": 25,
                "age_max": 45,
                "genders": [1, 2],
            },
        }
        model = AdSetModel(**data)
        assert model.name == "Test Ad Set"
        assert model.campaign_id == "camp_456"

    def test_budget_remaining_formatted(self) -> None:
        """budget_remaining_formatted converts cents to dollars."""
        model = AdSetModel(budget_remaining="3000")
        assert model.budget_remaining_formatted == "$30.00"

    def test_budget_remaining_formatted_invalid(self) -> None:
        """budget_remaining_formatted falls back to raw value on invalid input."""
        model = AdSetModel(budget_remaining="bad")
        assert model.budget_remaining_formatted == "bad"

    def test_targeting_summary(self) -> None:
        """targeting_summary generates human-readable text."""
        model = AdSetModel(
            targeting={
                "geo_locations": {"countries": ["US"]},
                "age_min": 18,
                "age_max": 35,
                "genders": [2],
            }
        )
        summary = model.targeting_summary
        assert "US" in summary
        assert "18-35" in summary
        assert "Female" in summary

    def test_targeting_summary_empty(self) -> None:
        """Empty targeting returns appropriate message."""
        model = AdSetModel()
        assert model.targeting_summary == "No targeting set"

    def test_targeting_summary_custom(self) -> None:
        """Unrecognized targeting keys return generic message."""
        model = AdSetModel(targeting={"custom_audiences": [{"id": "123"}]})
        assert model.targeting_summary == "Custom targeting"

    def test_new_fields_defaults(self) -> None:
        """New v25 fields have sensible defaults."""
        model = AdSetModel()
        assert model.bid_amount == "0"
        assert model.bid_strategy == ""
        assert model.destination_type == ""
        assert model.frequency_control_specs == []
        assert model.attribution_spec == []
        assert model.is_dynamic_creative is False
        assert model.optimization_sub_event == ""
        assert model.pacing_type == []

    def test_bid_amount_formatted_zero(self) -> None:
        """bid_amount_formatted returns 'Not set' for zero."""
        model = AdSetModel(bid_amount="0")
        assert model.bid_amount_formatted == "Not set"

    def test_bid_amount_formatted_valid(self) -> None:
        """bid_amount_formatted converts cents to dollars."""
        model = AdSetModel(bid_amount="1500")
        assert model.bid_amount_formatted == "$15.00"

    def test_bid_amount_formatted_invalid(self) -> None:
        """bid_amount_formatted falls back to raw value on invalid input."""
        model = AdSetModel(bid_amount="bad")
        assert model.bid_amount_formatted == "bad"

    def test_frequency_cap_summary_empty(self) -> None:
        """frequency_cap_summary returns 'No frequency cap' when empty."""
        model = AdSetModel()
        assert model.frequency_cap_summary == "No frequency cap"

    def test_frequency_cap_summary_single(self) -> None:
        """frequency_cap_summary formats a single spec."""
        model = AdSetModel(
            frequency_control_specs=[
                {"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}
            ]
        )
        assert model.frequency_cap_summary == "3 impressions per 7 days"

    def test_frequency_cap_summary_multiple(self) -> None:
        """frequency_cap_summary formats multiple specs."""
        model = AdSetModel(
            frequency_control_specs=[
                {"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3},
                {"event": "CLICKS", "interval_days": 1, "max_frequency": 1},
            ]
        )
        summary = model.frequency_cap_summary
        assert "3 impressions per 7 days" in summary
        assert "1 clicks per 1 days" in summary
        assert "; " in summary


class TestAdModel:
    """Tests for AdModel."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "id": "ad_123",
            "name": "Test Ad",
            "status": "ACTIVE",
            "creative": {"id": "creative_789"},
        }
        model = AdModel(**data)
        assert model.name == "Test Ad"

    def test_creative_id(self) -> None:
        """creative_id extracts ID from creative dict."""
        model = AdModel(creative={"id": "creative_789"})
        assert model.creative_id == "creative_789"

    def test_creative_id_empty(self) -> None:
        """creative_id returns empty string when no creative."""
        model = AdModel()
        assert model.creative_id == ""

    def test_new_fields_defaults(self) -> None:
        """New v25 fields have sensible defaults."""
        model = AdModel()
        assert model.configured_status == ""
        assert model.tracking_specs == []
        assert model.conversion_specs == []
        assert model.preview_shareable_link == ""

    def test_new_fields_populated(self) -> None:
        """New v25 fields accept data correctly."""
        model = AdModel(
            configured_status="ACTIVE",
            tracking_specs=[{"action.type": ["offsite_conversion"]}],
            conversion_specs=[{"action.type": ["offsite_conversion"]}],
            preview_shareable_link="https://www.facebook.com/ads/preview/123",
        )
        assert model.configured_status == "ACTIVE"
        assert len(model.tracking_specs) == 1
        assert len(model.conversion_specs) == 1
        assert "facebook.com" in model.preview_shareable_link


class TestAdCreativeModel:
    """Tests for AdCreativeModel."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "id": "cr_123",
            "name": "My Creative",
            "title": "Buy Now",
            "body": "Great deals!",
            "call_to_action_type": "LEARN_MORE",
            "link_url": "https://example.com",
        }
        model = AdCreativeModel(**data)
        assert model.title == "Buy Now"
        assert model.call_to_action_type == "LEARN_MORE"

    def test_defaults(self) -> None:
        """All fields default to empty strings."""
        model = AdCreativeModel()
        assert model.id == ""
        assert model.title == ""

    def test_new_fields_defaults(self) -> None:
        """New v25 fields have sensible defaults."""
        model = AdCreativeModel()
        assert model.status == ""
        assert model.object_story_spec == {}
        assert model.url_tags == ""
        assert model.image_hash == ""

    def test_object_story_summary_empty(self) -> None:
        """object_story_summary returns default when no spec."""
        model = AdCreativeModel()
        assert model.object_story_summary == "No object story"

    def test_object_story_summary_with_link_data(self) -> None:
        """object_story_summary extracts link data."""
        model = AdCreativeModel(
            object_story_spec={
                "page_id": "12345",
                "link_data": {
                    "link": "https://example.com",
                    "message": "Check this out!",
                },
            }
        )
        summary = model.object_story_summary
        assert "Page: 12345" in summary
        assert "Link: https://example.com" in summary
        assert "Message: Check this out!" in summary

    def test_object_story_summary_with_video_data(self) -> None:
        """object_story_summary identifies video creatives."""
        model = AdCreativeModel(
            object_story_spec={
                "page_id": "12345",
                "video_data": {"video_id": "999"},
            }
        )
        summary = model.object_story_summary
        assert "Page: 12345" in summary
        assert "Type: Video" in summary

    def test_object_story_summary_page_only(self) -> None:
        """object_story_summary with just a page_id."""
        model = AdCreativeModel(object_story_spec={"page_id": "12345"})
        assert model.object_story_summary == "Page: 12345"

    def test_object_story_summary_custom(self) -> None:
        """object_story_summary falls back to custom label."""
        model = AdCreativeModel(object_story_spec={"unknown_key": "value"})
        assert model.object_story_summary == "Custom object story"

    def test_object_story_summary_long_message_truncated(self) -> None:
        """object_story_summary truncates long messages."""
        long_msg = "A" * 60
        model = AdCreativeModel(
            object_story_spec={
                "link_data": {"message": long_msg},
            }
        )
        summary = model.object_story_summary
        assert "..." in summary
        assert len(summary) < len(long_msg) + 30


class TestInsightRow:
    """Tests for InsightRow."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "impressions": "10000",
            "clicks": "250",
            "spend": "75.50",
            "ctr": "2.5",
            "cpc": "0.302",
            "campaign_name": "Spring Campaign",
            "date_start": "2026-03-01",
            "date_stop": "2026-03-07",
            "actions": [
                {"action_type": "link_click", "value": "200"},
                {"action_type": "purchase", "value": "15"},
            ],
            "cost_per_action_type": [
                {"action_type": "link_click", "value": "0.38"},
                {"action_type": "purchase", "value": "5.03"},
            ],
        }
        model = InsightRow(**data)
        assert model.impressions == "10000"
        assert model.campaign_name == "Spring Campaign"

    def test_get_action_value(self) -> None:
        """get_action_value returns correct value."""
        model = InsightRow(
            actions=[
                {"action_type": "link_click", "value": "200"},
                {"action_type": "purchase", "value": "15"},
            ]
        )
        assert model.get_action_value("link_click") == "200"
        assert model.get_action_value("purchase") == "15"
        assert model.get_action_value("nonexistent") is None

    def test_get_cost_per_action(self) -> None:
        """get_cost_per_action returns correct value."""
        model = InsightRow(
            cost_per_action_type=[
                {"action_type": "link_click", "value": "0.38"},
            ]
        )
        assert model.get_cost_per_action("link_click") == "0.38"
        assert model.get_cost_per_action("nonexistent") is None

    def test_breakdown_fields(self) -> None:
        """Breakdown fields work correctly."""
        model = InsightRow(age="25-34", gender="male", country="US")
        assert model.age == "25-34"
        assert model.gender == "male"
        assert model.country == "US"


class TestCustomAudienceModel:
    """Tests for CustomAudienceModel."""

    def test_construction(self) -> None:
        """Model constructs from typical data."""
        data = {
            "id": "aud_123",
            "name": "Website Visitors",
            "subtype": "CUSTOM",
            "approximate_count_lower_bound": 50000,
            "approximate_count_upper_bound": 75000,
            "delivery_status": {"status": "ready"},
            "operation_status": {"status": "normal"},
        }
        model = CustomAudienceModel(**data)
        assert model.name == "Website Visitors"
        assert model.subtype == "CUSTOM"

    def test_size_display_range(self) -> None:
        """size_display formats range correctly."""
        model = CustomAudienceModel(
            approximate_count_lower_bound=50000,
            approximate_count_upper_bound=75000,
        )
        assert model.size_display == "50,000 - 75,000"

    def test_size_display_exact(self) -> None:
        """size_display shows single number when bounds match."""
        model = CustomAudienceModel(
            approximate_count_lower_bound=10000,
            approximate_count_upper_bound=10000,
        )
        assert model.size_display == "10,000"

    def test_size_display_unavailable(self) -> None:
        """size_display handles zero bounds."""
        model = CustomAudienceModel()
        assert model.size_display == "Size unavailable"

    def test_new_fields_defaults(self) -> None:
        """New v25 fields have sensible defaults."""
        model = CustomAudienceModel()
        assert model.lookalike_spec == {}
        assert model.rule == ""
        assert model.data_source == {}
        assert model.retention_days == 0
        assert model.is_value_based is False
        assert model.sharing_status == ""
        assert model.time_created == ""
        assert model.time_updated == ""

    def test_lookalike_summary_not_lookalike(self) -> None:
        """lookalike_summary returns default when no spec."""
        model = CustomAudienceModel()
        assert model.lookalike_summary == "Not a lookalike audience"

    def test_lookalike_summary_with_data(self) -> None:
        """lookalike_summary formats full spec."""
        model = CustomAudienceModel(
            lookalike_spec={
                "country": "US",
                "ratio": 0.01,
                "origin": [{"id": "123", "name": "Website Visitors"}],
            }
        )
        summary = model.lookalike_summary
        assert "Country: US" in summary
        assert "Ratio: 1%" in summary
        assert "Source: Website Visitors" in summary

    def test_lookalike_summary_empty_origin(self) -> None:
        """lookalike_summary handles empty origin list."""
        model = CustomAudienceModel(
            lookalike_spec={"country": "US", "ratio": 0.05, "origin": []}
        )
        summary = model.lookalike_summary
        assert "Country: US" in summary
        assert "Source" not in summary

    def test_lookalike_summary_minimal(self) -> None:
        """lookalike_summary with minimal data."""
        model = CustomAudienceModel(lookalike_spec={"other": "data"})
        assert model.lookalike_summary == "Lookalike audience"

    def test_data_source_summary_empty(self) -> None:
        """data_source_summary returns default when no source."""
        model = CustomAudienceModel()
        assert model.data_source_summary == "No data source"

    def test_data_source_summary_with_data(self) -> None:
        """data_source_summary formats type and sub-type."""
        model = CustomAudienceModel(
            data_source={"type": "PIXEL", "sub_type": "WEBSITE_VISITORS"}
        )
        summary = model.data_source_summary
        assert "Type: PIXEL" in summary
        assert "Sub-type: WEBSITE_VISITORS" in summary

    def test_data_source_summary_custom(self) -> None:
        """data_source_summary falls back to custom label."""
        model = CustomAudienceModel(data_source={"unknown": "field"})
        assert model.data_source_summary == "Custom data source"
