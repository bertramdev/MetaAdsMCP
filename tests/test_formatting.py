"""Tests for markdown formatters."""

from meta_ads_mcp.formatting import (
    format_account,
    format_account_list,
    format_ad,
    format_ad_image,
    format_ad_image_list,
    format_ad_list,
    format_ad_set,
    format_ad_set_list,
    format_ad_video,
    format_ad_video_list,
    format_audience,
    format_audience_list,
    format_campaign,
    format_campaign_list,
    format_creative,
    format_creative_list,
    format_error,
    format_insights_table,
)
from meta_ads_mcp.models import (
    AdAccountModel,
    AdCreativeModel,
    AdImageModel,
    AdModel,
    AdSetModel,
    AdVideoModel,
    CampaignModel,
    CustomAudienceModel,
    InsightRow,
)


class TestAccountFormatters:
    """Tests for account formatters."""

    def test_format_account(self) -> None:
        """Single account formatted as detail view."""
        account = AdAccountModel(
            id="act_123",
            name="Test Account",
            account_status=1,
            currency="USD",
            timezone_name="America/New_York",
            amount_spent="150000",
            balance="5000",
            spend_cap="1000000",
        )
        result = format_account(account)
        assert "## Ad Account: Test Account" in result
        assert "act_123" in result
        assert "Active" in result
        assert "$1,500.00" in result

    def test_format_account_list(self) -> None:
        """Account list formatted as table."""
        accounts = [
            AdAccountModel(
                id="act_1",
                name="Account 1",
                account_status=1,
                currency="USD",
                amount_spent="1000",
            ),
            AdAccountModel(
                id="act_2",
                name="Account 2",
                account_status=2,
                currency="EUR",
                amount_spent="2000",
            ),
        ]
        result = format_account_list(accounts)
        assert "## Ad Accounts" in result
        assert "act_1" in result
        assert "act_2" in result
        assert "Account 1" in result

    def test_format_account_list_empty(self) -> None:
        """Empty list returns appropriate message."""
        result = format_account_list([])
        assert "No ad accounts found" in result


class TestCampaignFormatters:
    """Tests for campaign formatters."""

    def test_format_campaign(self) -> None:
        """Single campaign formatted as detail view."""
        campaign = CampaignModel(
            id="camp_123",
            name="Spring Sale",
            status="ACTIVE",
            effective_status="ACTIVE",
            objective="OUTCOME_TRAFFIC",
            daily_budget="5000",
        )
        result = format_campaign(campaign)
        assert "## Campaign: Spring Sale" in result
        assert "OUTCOME_TRAFFIC" in result
        assert "$50.00" in result

    def test_format_campaign_list(self) -> None:
        """Campaign list formatted as table."""
        campaigns = [
            CampaignModel(
                id="c1", name="Campaign 1", status="ACTIVE", effective_status="ACTIVE"
            ),
            CampaignModel(
                id="c2", name="Campaign 2", status="PAUSED", effective_status="PAUSED"
            ),
        ]
        result = format_campaign_list(campaigns)
        assert "## Campaigns" in result
        assert "Campaign 1" in result
        assert "Campaign 2" in result

    def test_format_campaign_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No campaigns found" in format_campaign_list([])

    def test_format_campaign_with_new_fields(self) -> None:
        """Campaign formatter includes v25 fields."""
        campaign = CampaignModel(
            id="camp_v25",
            name="V25 Campaign",
            status="ACTIVE",
            effective_status="ACTIVE",
            objective="OUTCOME_SALES",
            configured_status="ACTIVE",
            buying_type="AUCTION",
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            spend_cap="100000",
            special_ad_categories=["HOUSING"],
        )
        result = format_campaign(campaign)
        assert "Configured Status" in result
        assert "Buying Type" in result
        assert "AUCTION" in result
        assert "Bid Strategy" in result
        assert "LOWEST_COST_WITHOUT_CAP" in result
        assert "Spend Cap" in result
        assert "$1,000.00" in result
        assert "Special Ad Categories" in result
        assert "HOUSING" in result


class TestAdSetFormatters:
    """Tests for ad set formatters."""

    def test_format_ad_set(self) -> None:
        """Single ad set formatted as detail view."""
        ad_set = AdSetModel(
            id="adset_123",
            name="Test Ad Set",
            status="ACTIVE",
            campaign_id="camp_456",
            daily_budget="2500",
            billing_event="IMPRESSIONS",
            optimization_goal="LINK_CLICKS",
            targeting={"geo_locations": {"countries": ["US"]}},
        )
        result = format_ad_set(ad_set)
        assert "## Ad Set: Test Ad Set" in result
        assert "camp_456" in result
        assert "$25.00" in result
        assert "LINK_CLICKS" in result

    def test_format_ad_set_list(self) -> None:
        """Ad set list formatted as table."""
        ad_sets = [AdSetModel(id="as1", name="Ad Set 1", effective_status="ACTIVE")]
        result = format_ad_set_list(ad_sets)
        assert "## Ad Sets" in result
        assert "Ad Set 1" in result

    def test_format_ad_set_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No ad sets found" in format_ad_set_list([])

    def test_format_ad_set_with_new_fields(self) -> None:
        """Ad set formatter includes v25 fields."""
        ad_set = AdSetModel(
            id="adset_v25",
            name="V25 Ad Set",
            status="ACTIVE",
            effective_status="ACTIVE",
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            bid_amount="1500",
            destination_type="WEBSITE",
            frequency_control_specs=[
                {"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}
            ],
            is_dynamic_creative=True,
        )
        result = format_ad_set(ad_set)
        assert "Bid Strategy" in result
        assert "LOWEST_COST_WITHOUT_CAP" in result
        assert "Bid Amount" in result
        assert "$15.00" in result
        assert "Destination Type" in result
        assert "WEBSITE" in result
        assert "Frequency Cap" in result
        assert "3 impressions per 7 days" in result
        assert "Dynamic Creative" in result
        assert "Yes" in result


class TestAdFormatters:
    """Tests for ad formatters."""

    def test_format_ad(self) -> None:
        """Single ad formatted as detail view."""
        ad = AdModel(
            id="ad_123",
            name="Test Ad",
            status="ACTIVE",
            effective_status="ACTIVE",
            adset_id="adset_456",
            campaign_id="camp_789",
            creative={"id": "cr_111"},
        )
        result = format_ad(ad)
        assert "## Ad: Test Ad" in result
        assert "cr_111" in result
        assert "adset_456" in result

    def test_format_ad_list(self) -> None:
        """Ad list formatted as table."""
        ads = [
            AdModel(id="ad_1", name="Ad 1", status="ACTIVE", effective_status="ACTIVE")
        ]
        result = format_ad_list(ads)
        assert "## Ads" in result

    def test_format_ad_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No ads found" in format_ad_list([])

    def test_format_ad_with_new_fields(self) -> None:
        """Ad formatter includes v25 fields when present."""
        ad = AdModel(
            id="ad_v25",
            name="V25 Ad",
            status="ACTIVE",
            effective_status="ACTIVE",
            configured_status="ACTIVE",
            preview_shareable_link="https://www.facebook.com/ads/preview/123",
        )
        result = format_ad(ad)
        assert "Configured Status" in result
        assert "Preview Link" in result
        assert "facebook.com" in result

    def test_format_ad_without_optional_fields(self) -> None:
        """Ad formatter omits optional fields when not set."""
        ad = AdModel(
            id="ad_basic",
            name="Basic Ad",
            status="ACTIVE",
            effective_status="ACTIVE",
        )
        result = format_ad(ad)
        assert "Configured Status" not in result
        assert "Preview Link" not in result


class TestCreativeFormatters:
    """Tests for creative formatters."""

    def test_format_creative(self) -> None:
        """Single creative formatted as detail view."""
        creative = AdCreativeModel(
            id="cr_123",
            name="My Creative",
            title="Buy Now",
            body="Great deals!",
            call_to_action_type="LEARN_MORE",
            link_url="https://example.com",
        )
        result = format_creative(creative)
        assert "## Creative: My Creative" in result
        assert "Buy Now" in result
        assert "LEARN_MORE" in result

    def test_format_creative_with_new_fields(self) -> None:
        """Creative formatter includes enriched v25 fields."""
        creative = AdCreativeModel(
            id="cr_456",
            name="Enriched Creative",
            title="Shop Now",
            body="Amazing products!",
            call_to_action_type="SHOP_NOW",
            link_url="https://shop.example.com",
            status="ACTIVE",
            image_hash="abc123hash",
            url_tags="utm_source=meta&utm_medium=cpc",
            object_story_spec={
                "page_id": "12345",
                "link_data": {"link": "https://shop.example.com"},
            },
        )
        result = format_creative(creative)
        assert "**Status**: ACTIVE" in result
        assert "**Image Hash**: abc123hash" in result
        assert "**URL Tags**: utm_source=meta&utm_medium=cpc" in result
        assert "**Object Story**:" in result
        assert "Page: 12345" in result

    def test_format_creative_without_optional_fields(self) -> None:
        """Creative formatter omits empty optional v25 fields."""
        creative = AdCreativeModel(
            id="cr_789",
            name="Basic Creative",
        )
        result = format_creative(creative)
        assert "Status" not in result
        assert "Image Hash" not in result
        assert "URL Tags" not in result
        assert "Object Story" not in result

    def test_format_creative_list(self) -> None:
        """Creative list formatted as table."""
        creatives = [AdCreativeModel(id="cr_1", name="Creative 1")]
        result = format_creative_list(creatives)
        assert "## Ad Creatives" in result

    def test_format_creative_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No creatives found" in format_creative_list([])


class TestInsightsFormatter:
    """Tests for insights table formatter."""

    def test_format_insights_table(self) -> None:
        """Insights formatted as dynamic table."""
        rows = [
            InsightRow(
                campaign_name="Campaign 1",
                impressions="10000",
                clicks="250",
                spend="75.50",
                ctr="2.5",
                cpc="0.302",
                cpm="7.55",
                reach="8000",
                date_start="2026-03-01",
                date_stop="2026-03-07",
            ),
        ]
        result = format_insights_table(rows)
        assert "## Performance Insights" in result
        assert "Campaign 1" in result
        assert "10,000" in result
        assert "$75.50" in result

    def test_format_insights_with_breakdowns(self) -> None:
        """Insights with breakdown columns detected."""
        rows = [
            InsightRow(
                age="25-34",
                gender="male",
                impressions="5000",
                clicks="100",
                spend="30.00",
                ctr="2.0",
                cpc="0.30",
                cpm="6.00",
                reach="4000",
                date_start="2026-03-01",
                date_stop="2026-03-07",
            ),
        ]
        result = format_insights_table(rows, title="Age/Gender Report")
        assert "## Age/Gender Report" in result
        assert "25-34" in result
        assert "male" in result
        assert "Age" in result
        assert "Gender" in result

    def test_format_insights_empty(self) -> None:
        """Empty list returns message."""
        assert "No insights data found" in format_insights_table([])

    def test_custom_title(self) -> None:
        """Custom title appears in output."""
        rows = [
            InsightRow(
                impressions="100",
                clicks="10",
                spend="5.00",
                ctr="10.0",
                cpc="0.50",
                cpm="50.0",
                reach="90",
                date_start="2026-03-01",
                date_stop="2026-03-01",
            ),
        ]
        result = format_insights_table(rows, title="My Custom Report")
        assert "## My Custom Report" in result


class TestAudienceFormatters:
    """Tests for audience formatters."""

    def test_format_audience(self) -> None:
        """Single audience formatted as detail view."""
        audience = CustomAudienceModel(
            id="aud_123",
            name="Website Visitors",
            subtype="CUSTOM",
            approximate_count_lower_bound=50000,
            approximate_count_upper_bound=75000,
            delivery_status={"status": "ready"},
            operation_status={"status": "normal"},
            description="All website visitors last 30 days",
        )
        result = format_audience(audience)
        assert "## Audience: Website Visitors" in result
        assert "50,000 - 75,000" in result
        assert "ready" in result

    def test_format_audience_with_new_fields(self) -> None:
        """Audience formatter includes enriched v25 fields."""
        audience = CustomAudienceModel(
            id="aud_456",
            name="Lookalike Audience",
            subtype="LOOKALIKE",
            approximate_count_lower_bound=100000,
            approximate_count_upper_bound=200000,
            delivery_status={"status": "ready"},
            operation_status={"status": "normal"},
            description="1% lookalike of website visitors",
            retention_days=30,
            is_value_based=True,
            sharing_status="shared",
            lookalike_spec={
                "country": "US",
                "ratio": 0.01,
                "origin": [{"id": "123", "name": "Website Visitors"}],
            },
            data_source={"type": "PIXEL", "sub_type": "WEBSITE_VISITORS"},
            time_created="2026-01-15T10:00:00+0000",
            time_updated="2026-03-01T12:00:00+0000",
        )
        result = format_audience(audience)
        assert "**Retention Days**: 30" in result
        assert "**Value-Based**: Yes" in result
        assert "**Sharing Status**: shared" in result
        assert "**Lookalike**:" in result
        assert "Country: US" in result
        assert "**Data Source**:" in result
        assert "Type: PIXEL" in result
        assert "**Created**: 2026-01-15T10:00:00+0000" in result
        assert "**Updated**: 2026-03-01T12:00:00+0000" in result

    def test_format_audience_without_optional_fields(self) -> None:
        """Audience formatter omits empty optional v25 fields."""
        audience = CustomAudienceModel(
            id="aud_789",
            name="Basic Audience",
            subtype="CUSTOM",
            delivery_status={"status": "ready"},
            operation_status={"status": "normal"},
        )
        result = format_audience(audience)
        assert "Retention Days" not in result
        assert "Value-Based" not in result
        assert "Sharing Status" not in result
        assert "Lookalike" not in result
        assert "Data Source" not in result
        assert "Created" not in result
        assert "Updated" not in result

    def test_format_audience_list(self) -> None:
        """Audience list formatted as table."""
        audiences = [
            CustomAudienceModel(id="aud_1", name="Audience 1", subtype="CUSTOM"),
        ]
        result = format_audience_list(audiences)
        assert "## Custom Audiences" in result

    def test_format_audience_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No audiences found" in format_audience_list([])


class TestErrorFormatter:
    """Tests for error formatter."""

    def test_format_error(self) -> None:
        """Error formatted as markdown."""
        result = format_error("Something went wrong")
        assert "## Error" in result
        assert "Something went wrong" in result


class TestAdImageFormatter:
    """Tests for ad image formatters."""

    def test_format_ad_image(self) -> None:
        """Image detail shows hash prominently."""
        image = AdImageModel(
            hash="abc123",
            name="Banner",
            width=1200,
            height=628,
            status="active",
            url="https://example.com/img.jpg",
        )
        result = format_ad_image(image)
        assert "abc123" in result
        assert "Banner" in result
        assert "1200x628" in result
        assert "create_ad_creative" in result

    def test_format_ad_image_unnamed(self) -> None:
        """Image with no name shows Unnamed."""
        image = AdImageModel(hash="xyz")
        result = format_ad_image(image)
        assert "Unnamed" in result

    def test_format_ad_image_list(self) -> None:
        """Image list table has correct columns."""
        images = [
            AdImageModel(
                hash="h1", name="Img1", width=800, height=600, status="active"
            ),
            AdImageModel(
                hash="h2", name="Img2", width=512, height=512, status="active"
            ),
        ]
        result = format_ad_image_list(images)
        assert "## Ad Images" in result
        assert "h1" in result
        assert "h2" in result
        assert "800x600" in result

    def test_format_ad_image_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No ad images found" in format_ad_image_list([])


class TestAdVideoFormatter:
    """Tests for ad video formatters."""

    def test_format_ad_video(self) -> None:
        """Video detail shows ID prominently."""
        video = AdVideoModel(
            id="vid_123",
            name="Promo",
            title="Spring Sale",
            length=65.0,
            source="https://example.com/video.mp4",
        )
        result = format_ad_video(video)
        assert "vid_123" in result
        assert "Promo" in result
        assert "1m 5s" in result
        assert "object_story_spec" in result

    def test_format_ad_video_unnamed(self) -> None:
        """Video with no name or title shows Unnamed."""
        video = AdVideoModel(id="vid_456")
        result = format_ad_video(video)
        assert "Unnamed" in result

    def test_format_ad_video_list(self) -> None:
        """Video list table has correct columns."""
        videos = [
            AdVideoModel(id="v1", name="Ad 1", title="Title 1", length=30.0),
            AdVideoModel(id="v2", name="Ad 2", title="Title 2", length=90.0),
        ]
        result = format_ad_video_list(videos)
        assert "## Ad Videos" in result
        assert "v1" in result
        assert "v2" in result
        assert "30s" in result
        assert "1m 30s" in result

    def test_format_ad_video_list_empty(self) -> None:
        """Empty list returns message."""
        assert "No ad videos found" in format_ad_video_list([])
