"""Pydantic v2 models for all Meta Ads entities.

These models serve as the intermediate layer between SDK responses and
formatted output. All models use ``extra="ignore"`` to handle unexpected
fields from the API gracefully.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class AdAccountModel(BaseModel):
    """Model for a Meta Ad Account.

    Attributes:
        id: The ad account ID (e.g., act_123456789).
        name: The ad account name.
        account_status: Numeric status code (1=Active, 2=Disabled, 3=Unsettled, etc.).
        currency: Account currency code (e.g., USD).
        timezone_name: Account timezone (e.g., America/New_York).
        amount_spent: Total amount spent in cents.
        balance: Current balance in cents.
        spend_cap: Spending cap in cents.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    account_status: int = 0
    currency: str = ""
    timezone_name: str = ""
    amount_spent: str = "0"
    balance: str = "0"
    spend_cap: str = "0"

    @property
    def status_display(self) -> str:
        """Human-readable account status."""
        statuses = {
            1: "Active",
            2: "Disabled",
            3: "Unsettled",
            7: "Pending Review",
            8: "Pending Closure",
            9: "In Grace Period",
            100: "Pending Settlement",
            101: "Temporarily Unavailable",
        }
        return statuses.get(self.account_status, f"Unknown ({self.account_status})")

    @property
    def amount_spent_formatted(self) -> str:
        """Format amount_spent from cents string to dollar display."""
        try:
            cents = int(self.amount_spent)
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.amount_spent

    @property
    def balance_formatted(self) -> str:
        """Format balance from cents string to dollar display."""
        try:
            cents = int(self.balance)
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.balance

    @property
    def spend_cap_formatted(self) -> str:
        """Format spend_cap from cents string to dollar display."""
        try:
            cents = int(self.spend_cap)
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.spend_cap


class CampaignModel(BaseModel):
    """Model for a Meta Ads Campaign.

    Attributes:
        id: The campaign ID.
        name: The campaign name.
        status: The configured status.
        effective_status: Status including inherited state from parent.
        objective: Campaign objective (e.g., OUTCOME_TRAFFIC).
        daily_budget: Daily budget in cents.
        lifetime_budget: Lifetime budget in cents.
        budget_remaining: Remaining budget in cents.
        start_time: Campaign start time.
        stop_time: Campaign stop time.
        created_time: Campaign creation time.
        updated_time: Last update time.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    effective_status: str = ""
    objective: str = ""
    daily_budget: str = "0"
    lifetime_budget: str = "0"
    budget_remaining: str = "0"
    start_time: str = ""
    stop_time: str = ""
    created_time: str = ""
    updated_time: str = ""
    bid_strategy: str = ""
    spend_cap: str = "0"
    pacing_type: list[str] = []
    buying_type: str = ""
    special_ad_categories: list[str] = []
    configured_status: str = ""

    @property
    def daily_budget_formatted(self) -> str:
        """Format daily budget from cents string to dollar display."""
        try:
            cents = int(self.daily_budget)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.daily_budget

    @property
    def lifetime_budget_formatted(self) -> str:
        """Format lifetime budget from cents string to dollar display."""
        try:
            cents = int(self.lifetime_budget)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.lifetime_budget

    @property
    def budget_remaining_formatted(self) -> str:
        """Format budget_remaining from cents string to dollar display."""
        try:
            cents = int(self.budget_remaining)
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.budget_remaining

    @property
    def spend_cap_formatted(self) -> str:
        """Format spend cap from cents string to dollar display."""
        try:
            cents = int(self.spend_cap)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.spend_cap


class AdSetModel(BaseModel):
    """Model for a Meta Ads Ad Set.

    Attributes:
        id: The ad set ID.
        name: The ad set name.
        status: The configured status.
        effective_status: Status including inherited state.
        campaign_id: Parent campaign ID.
        daily_budget: Daily budget in cents.
        lifetime_budget: Lifetime budget in cents.
        budget_remaining: Remaining budget in cents.
        billing_event: Billing event type (e.g., IMPRESSIONS).
        optimization_goal: Optimization goal (e.g., LINK_CLICKS).
        targeting: Targeting specification dictionary.
        start_time: Ad set start time.
        end_time: Ad set end time.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    effective_status: str = ""
    campaign_id: str = ""
    daily_budget: str = "0"
    lifetime_budget: str = "0"
    budget_remaining: str = "0"
    billing_event: str = ""
    optimization_goal: str = ""
    targeting: dict[str, Any] = {}
    start_time: str = ""
    end_time: str = ""
    bid_amount: str = "0"
    bid_strategy: str = ""
    destination_type: str = ""
    frequency_control_specs: list[dict[str, Any]] = []
    attribution_spec: list[dict[str, Any]] = []
    is_dynamic_creative: bool = False
    optimization_sub_event: str = ""
    pacing_type: list[str] = []

    @property
    def daily_budget_formatted(self) -> str:
        """Format daily budget from cents string to dollar display."""
        try:
            cents = int(self.daily_budget)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.daily_budget

    @property
    def lifetime_budget_formatted(self) -> str:
        """Format lifetime budget from cents string to dollar display."""
        try:
            cents = int(self.lifetime_budget)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.lifetime_budget

    @property
    def budget_remaining_formatted(self) -> str:
        """Format budget_remaining from cents string to dollar display."""
        try:
            cents = int(self.budget_remaining)
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.budget_remaining

    @property
    def bid_amount_formatted(self) -> str:
        """Format bid amount from cents string to dollar display."""
        try:
            cents = int(self.bid_amount)
            if cents == 0:
                return "Not set"
            return f"${cents / 100:,.2f}"
        except (ValueError, TypeError):
            return self.bid_amount

    @property
    def frequency_cap_summary(self) -> str:
        """Generate a human-readable summary of frequency capping settings."""
        if not self.frequency_control_specs:
            return "No frequency cap"
        parts: list[str] = []
        for spec in self.frequency_control_specs:
            event = spec.get("event", "IMPRESSIONS")
            interval = spec.get("interval_days", 0)
            max_freq = spec.get("max_frequency", 0)
            parts.append(f"{max_freq} {event.lower()} per {interval} days")
        return "; ".join(parts)

    @property
    def targeting_summary(self) -> str:
        """Generate a human-readable summary of targeting settings."""
        if not self.targeting:
            return "No targeting set"
        parts: list[str] = []
        if "geo_locations" in self.targeting:
            geo = self.targeting["geo_locations"]
            countries = geo.get("countries", [])
            if countries:
                parts.append(f"Countries: {', '.join(countries)}")
        if "age_min" in self.targeting or "age_max" in self.targeting:
            age_min = self.targeting.get("age_min", 18)
            age_max = self.targeting.get("age_max", 65)
            parts.append(f"Age: {age_min}-{age_max}")
        if "genders" in self.targeting:
            gender_map = {1: "Male", 2: "Female"}
            genders = [gender_map.get(g, str(g)) for g in self.targeting["genders"]]
            parts.append(f"Gender: {', '.join(genders)}")
        return "; ".join(parts) if parts else "Custom targeting"


class AdModel(BaseModel):
    """Model for a Meta Ad.

    Attributes:
        id: The ad ID.
        name: The ad name.
        status: The configured status.
        effective_status: Status including inherited state.
        adset_id: Parent ad set ID.
        campaign_id: Parent campaign ID.
        creative: Creative reference dictionary.
        created_time: Ad creation time.
        updated_time: Last update time.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    effective_status: str = ""
    adset_id: str = ""
    campaign_id: str = ""
    creative: dict[str, Any] = {}
    created_time: str = ""
    updated_time: str = ""
    configured_status: str = ""
    tracking_specs: list[dict[str, Any]] = []
    conversion_specs: list[dict[str, Any]] = []
    preview_shareable_link: str = ""

    @property
    def creative_id(self) -> str:
        """Extract the creative ID from the creative reference."""
        return str(self.creative.get("id", ""))


class AdCreativeModel(BaseModel):
    """Model for a Meta Ad Creative.

    Attributes:
        id: The creative ID.
        name: The creative name.
        title: The creative title/headline.
        body: The creative body/description text.
        image_url: URL of the creative image.
        thumbnail_url: URL of the creative thumbnail.
        call_to_action_type: CTA button type (e.g., LEARN_MORE).
        link_url: Destination URL for the creative.
        status: The creative status.
        object_story_spec: Object story specification dictionary.
        url_tags: URL tags for tracking.
        image_hash: Hash of the creative image.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    title: str = ""
    body: str = ""
    image_url: str = ""
    thumbnail_url: str = ""
    call_to_action_type: str = ""
    link_url: str = ""
    status: str = ""
    object_story_spec: dict[str, Any] = {}
    url_tags: str = ""
    image_hash: str = ""

    @property
    def object_story_summary(self) -> str:
        """Extract a human-readable summary from the object story spec."""
        if not self.object_story_spec:
            return "No object story"
        parts: list[str] = []
        page_id = self.object_story_spec.get("page_id", "")
        if page_id:
            parts.append(f"Page: {page_id}")
        link_data = self.object_story_spec.get("link_data", {})
        if link_data:
            link = link_data.get("link", "")
            message = link_data.get("message", "")
            if link:
                parts.append(f"Link: {link}")
            if message:
                parts.append(
                    f"Message: {message[:50]}{'...' if len(message) > 50 else ''}"
                )
        video_data = self.object_story_spec.get("video_data", {})
        if video_data:
            parts.append("Type: Video")
        return "; ".join(parts) if parts else "Custom object story"


class InsightRow(BaseModel):
    """Model for a single row of Meta Ads insights data.

    Attributes:
        account_id: The ad account ID.
        campaign_id: Campaign ID (when level is campaign or lower).
        campaign_name: Campaign name.
        adset_id: Ad set ID (when level is adset or lower).
        adset_name: Ad set name.
        ad_id: Ad ID (when level is ad).
        ad_name: Ad name.
        impressions: Total impressions.
        clicks: Total clicks.
        spend: Total spend as string.
        ctr: Click-through rate as string.
        cpc: Cost per click as string.
        cpm: Cost per mille as string.
        reach: Total reach.
        actions: List of action dictionaries.
        cost_per_action_type: List of cost-per-action dictionaries.
        date_start: Start date of the reporting period.
        date_stop: End date of the reporting period.
        age: Age breakdown value.
        gender: Gender breakdown value.
        country: Country breakdown value.
        placement: Placement breakdown value.
        device_platform: Device platform breakdown value.
        publisher_platform: Publisher platform breakdown value.
    """

    model_config = ConfigDict(extra="ignore")

    account_id: str = ""
    campaign_id: str = ""
    campaign_name: str = ""
    adset_id: str = ""
    adset_name: str = ""
    ad_id: str = ""
    ad_name: str = ""
    impressions: str = "0"
    clicks: str = "0"
    spend: str = "0"
    ctr: str = "0"
    cpc: str = "0"
    cpm: str = "0"
    reach: str = "0"
    actions: list[dict[str, Any]] = []
    cost_per_action_type: list[dict[str, Any]] = []
    date_start: str = ""
    date_stop: str = ""
    # Breakdown fields
    age: str = ""
    gender: str = ""
    country: str = ""
    placement: str = ""
    device_platform: str = ""
    publisher_platform: str = ""

    def get_action_value(self, action_type: str) -> str | None:
        """Get the value for a specific action type.

        Args:
            action_type: The action type to look up (e.g., 'link_click').

        Returns:
            The action value as a string, or None if not found.
        """
        for action in self.actions:
            if action.get("action_type") == action_type:
                return str(action.get("value", "0"))
        return None

    def get_cost_per_action(self, action_type: str) -> str | None:
        """Get the cost per action for a specific action type.

        Args:
            action_type: The action type to look up.

        Returns:
            The cost per action as a string, or None if not found.
        """
        for cost in self.cost_per_action_type:
            if cost.get("action_type") == action_type:
                return str(cost.get("value", "0"))
        return None


class CustomAudienceModel(BaseModel):
    """Model for a Meta Custom Audience.

    Attributes:
        id: The audience ID.
        name: The audience name.
        subtype: Audience subtype (e.g., CUSTOM, LOOKALIKE).
        approximate_count_lower_bound: Lower bound of audience size.
        approximate_count_upper_bound: Upper bound of audience size.
        delivery_status: Delivery status dictionary.
        operation_status: Operation status dictionary.
        description: Audience description.
        lookalike_spec: Lookalike audience specification dictionary.
        rule: Audience rule definition.
        data_source: Data source specification dictionary.
        retention_days: Audience retention period in days.
        is_value_based: Whether this is a value-based audience.
        sharing_status: Audience sharing status.
        time_created: Audience creation timestamp.
        time_updated: Audience last update timestamp.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    subtype: str = ""
    approximate_count_lower_bound: int = 0
    approximate_count_upper_bound: int = 0
    delivery_status: dict[str, Any] = {}
    operation_status: dict[str, Any] = {}
    description: str = ""
    lookalike_spec: dict[str, Any] = {}
    rule: str = ""
    data_source: dict[str, Any] = {}
    retention_days: int = 0
    is_value_based: bool = False
    sharing_status: str = ""
    time_created: str = ""
    time_updated: str = ""

    @property
    def size_display(self) -> str:
        """Format audience size as a human-readable range."""
        lower = self.approximate_count_lower_bound
        upper = self.approximate_count_upper_bound
        if lower == 0 and upper == 0:
            return "Size unavailable"
        if lower == upper:
            return f"{lower:,}"
        return f"{lower:,} - {upper:,}"

    @property
    def lookalike_summary(self) -> str:
        """Generate a human-readable summary of lookalike spec."""
        if not self.lookalike_spec:
            return "Not a lookalike audience"
        country = self.lookalike_spec.get("country", "")
        ratio = self.lookalike_spec.get("ratio", 0)
        origin_id = self.lookalike_spec.get("origin", [{}])
        origin_name = ""
        if isinstance(origin_id, list) and origin_id:
            origin_name = origin_id[0].get("name", "")
        parts: list[str] = []
        if country:
            parts.append(f"Country: {country}")
        if ratio:
            parts.append(f"Ratio: {ratio:.0%}")
        if origin_name:
            parts.append(f"Source: {origin_name}")
        return "; ".join(parts) if parts else "Lookalike audience"

    @property
    def data_source_summary(self) -> str:
        """Generate a human-readable summary of the data source."""
        if not self.data_source:
            return "No data source"
        source_type = self.data_source.get("type", "")
        sub_type = self.data_source.get("sub_type", "")
        parts: list[str] = []
        if source_type:
            parts.append(f"Type: {source_type}")
        if sub_type:
            parts.append(f"Sub-type: {sub_type}")
        return "; ".join(parts) if parts else "Custom data source"


class CampaignDiagnosticsModel(BaseModel):
    """Diagnostics for a campaign including issues and recommendations.

    Attributes:
        id: The campaign ID.
        name: The campaign name.
        status: The campaign status.
        issues_info: List of issue dictionaries with level and summary.
        recommendations: List of recommendation dictionaries.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    issues_info: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []


class AdSetDiagnosticsModel(BaseModel):
    """Diagnostics for an ad set including issues, recommendations, and learning stage.

    Attributes:
        id: The ad set ID.
        name: The ad set name.
        status: The ad set status.
        issues_info: List of issue dictionaries with level and summary.
        recommendations: List of recommendation dictionaries.
        learning_stage_info: Learning stage status dictionary.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    issues_info: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    learning_stage_info: dict[str, Any] = {}


class AdDiagnosticsModel(BaseModel):
    """Diagnostics for an ad including review feedback, delivery checks, and issues.

    Attributes:
        id: The ad ID.
        name: The ad name.
        status: The ad status.
        ad_review_feedback: Ad review feedback dictionary.
        failed_delivery_checks: List of failed delivery check dictionaries.
        issues_info: List of issue dictionaries with level and summary.
        recommendations: List of recommendation dictionaries.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    status: str = ""
    ad_review_feedback: dict[str, Any] = {}
    failed_delivery_checks: list[dict[str, Any]] = []
    issues_info: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
