"""Meta Ads API client wrapping the facebook-business SDK.

All public methods are async, using ``asyncio.to_thread()`` to wrap
synchronous SDK calls without blocking the event loop.
"""

import asyncio
import itertools
import logging
from typing import Any

from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.customaudience import CustomAudience
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from meta_ads_mcp.config import MetaAdsConfig

logger = logging.getLogger(__name__)

META_ERROR_HINTS: dict[int, str] = {
    2: "Temporary issue with the Meta API. Try again in a few minutes.",
    4: "Temporary issue with the Meta API. Try again in a few minutes.",
    10: "Permission denied. Ensure the token has ads_read "
    "and ads_management permissions.",
    17: "Rate limit reached. Wait a few minutes and try again.",
    32: "Rate limit reached. Wait a few minutes and try again.",
    100: "Invalid parameter. Check the parameters and try again.",
    190: "Access token has expired or is invalid. Generate a new token.",
    200: "Permission denied. Ensure the token has ads_read "
    "and ads_management permissions.",
    613: "Rate limit reached. Wait a few minutes and try again.",
}


class MetaAdsError(Exception):
    """Exception for Meta Ads API errors.

    Attributes:
        message: Human-readable error message.
        error_code: Meta API error code.
        error_subcode: Meta API error subcode.
    """

    def __init__(
        self,
        message: str,
        error_code: int | None = None,
        error_subcode: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.error_subcode = error_subcode

    @property
    def hint(self) -> str:
        """Return an actionable hint for this error code, if available."""
        if self.error_code is None:
            return ""
        return META_ERROR_HINTS.get(self.error_code, "")


class MetaAdsClient:
    """Async wrapper around the facebook-business SDK.

    This is the single API interface for the MCP server. Tools should never
    call the facebook-business SDK directly.

    Args:
        config: The server configuration.
    """

    def __init__(self, config: MetaAdsConfig) -> None:
        self._config = config
        self._api: FacebookAdsApi | None = None

    def initialize(self) -> None:
        """Initialize the Facebook Ads API.

        Must be called before any API methods.
        """
        self._api = FacebookAdsApi.init(
            app_id=self._config.app_id,
            app_secret=self._config.app_secret,
            access_token=self._config.access_token,
            api_version=self._config.api_version,
        )
        logger.info(
            "Meta Ads API initialized (token: %s, version: %s)",
            self._config.masked_token,
            self._config.api_version,
        )

    def _ensure_initialized(self) -> None:
        """Verify the API has been initialized."""
        if self._api is None:
            raise MetaAdsError("Client not initialized. Call initialize() first.")

    def _get_account(self, account_id: str | None = None) -> AdAccount:
        """Get an AdAccount object for the given or default account.

        Args:
            account_id: Explicit account ID, or None for default.

        Returns:
            An AdAccount SDK object.
        """
        resolved = self._config.resolve_account_id(account_id)
        return AdAccount(resolved)

    @staticmethod
    def _handle_api_error(error: FacebookRequestError) -> MetaAdsError:
        """Convert a Facebook API error to a MetaAdsError.

        Args:
            error: The SDK error.

        Returns:
            A MetaAdsError with extracted details.
        """
        body = error.body() or {}
        err_info = body.get("error", {})
        return MetaAdsError(
            message=err_info.get("message", str(error)),
            error_code=err_info.get("code"),
            error_subcode=err_info.get("error_subcode"),
        )

    async def get_ad_accounts(self) -> list[dict[str, Any]]:
        """List all accessible ad accounts for the authenticated user.

        Returns:
            A list of ad account data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                me = User(fbid="me")
                accounts = me.get_ad_accounts(
                    fields=[
                        AdAccount.Field.id,
                        AdAccount.Field.name,
                        AdAccount.Field.account_status,
                        AdAccount.Field.currency,
                        AdAccount.Field.timezone_name,
                        AdAccount.Field.amount_spent,
                        AdAccount.Field.balance,
                        AdAccount.Field.spend_cap,
                    ]
                )
                return [dict(acc) for acc in accounts]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_account_info(self, account_id: str | None = None) -> dict[str, Any]:
        """Get detailed info for a specific ad account.

        Args:
            account_id: The ad account ID, or None for default.

        Returns:
            Account data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                account.api_get(
                    fields=[
                        AdAccount.Field.id,
                        AdAccount.Field.name,
                        AdAccount.Field.account_status,
                        AdAccount.Field.currency,
                        AdAccount.Field.timezone_name,
                        AdAccount.Field.amount_spent,
                        AdAccount.Field.balance,
                        AdAccount.Field.spend_cap,
                    ]
                )
                return dict(account)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_campaigns(
        self,
        account_id: str | None = None,
        status_filter: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List campaigns for an ad account.

        Args:
            account_id: The ad account ID, or None for default.
            status_filter: List of status values to filter by.
            limit: Maximum number of campaigns to return.

        Returns:
            A list of campaign data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {"limit": limit}
                if status_filter:
                    params["filtering"] = [
                        {
                            "field": "effective_status",
                            "operator": "IN",
                            "value": status_filter,
                        }
                    ]
                campaigns = account.get_campaigns(
                    fields=[
                        Campaign.Field.id,
                        Campaign.Field.name,
                        Campaign.Field.status,
                        Campaign.Field.effective_status,
                        Campaign.Field.objective,
                        Campaign.Field.daily_budget,
                        Campaign.Field.lifetime_budget,
                        Campaign.Field.budget_remaining,
                        Campaign.Field.start_time,
                        Campaign.Field.stop_time,
                        Campaign.Field.created_time,
                        Campaign.Field.updated_time,
                        Campaign.Field.bid_strategy,
                        Campaign.Field.spend_cap,
                        Campaign.Field.pacing_type,
                        Campaign.Field.buying_type,
                        Campaign.Field.special_ad_categories,
                        Campaign.Field.configured_status,
                    ],
                    params=params,
                )
                return [dict(c) for c in itertools.islice(campaigns, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Get detailed info for a specific campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            Campaign data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                campaign = Campaign(campaign_id)
                campaign.api_get(
                    fields=[
                        Campaign.Field.id,
                        Campaign.Field.name,
                        Campaign.Field.status,
                        Campaign.Field.effective_status,
                        Campaign.Field.objective,
                        Campaign.Field.daily_budget,
                        Campaign.Field.lifetime_budget,
                        Campaign.Field.budget_remaining,
                        Campaign.Field.start_time,
                        Campaign.Field.stop_time,
                        Campaign.Field.created_time,
                        Campaign.Field.updated_time,
                        Campaign.Field.bid_strategy,
                        Campaign.Field.spend_cap,
                        Campaign.Field.pacing_type,
                        Campaign.Field.buying_type,
                        Campaign.Field.special_ad_categories,
                        Campaign.Field.configured_status,
                    ]
                )
                return dict(campaign)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_sets(
        self,
        account_id: str | None = None,
        campaign_id: str | None = None,
        status_filter: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List ad sets for an account or campaign.

        Args:
            account_id: The ad account ID, or None for default.
            campaign_id: Filter to a specific campaign.
            status_filter: List of status values to filter by.
            limit: Maximum number of ad sets to return.

        Returns:
            A list of ad set data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                fields = [
                    AdSet.Field.id,
                    AdSet.Field.name,
                    AdSet.Field.status,
                    AdSet.Field.effective_status,
                    AdSet.Field.campaign_id,
                    AdSet.Field.daily_budget,
                    AdSet.Field.lifetime_budget,
                    AdSet.Field.budget_remaining,
                    AdSet.Field.billing_event,
                    AdSet.Field.optimization_goal,
                    AdSet.Field.targeting,
                    AdSet.Field.start_time,
                    AdSet.Field.end_time,
                    AdSet.Field.bid_amount,
                    AdSet.Field.bid_strategy,
                    AdSet.Field.destination_type,
                    AdSet.Field.frequency_control_specs,
                    AdSet.Field.attribution_spec,
                    AdSet.Field.is_dynamic_creative,
                    AdSet.Field.optimization_sub_event,
                    AdSet.Field.pacing_type,
                ]
                params: dict[str, Any] = {"limit": limit}
                if status_filter:
                    params["filtering"] = [
                        {
                            "field": "effective_status",
                            "operator": "IN",
                            "value": status_filter,
                        }
                    ]
                if campaign_id:
                    parent = Campaign(campaign_id)
                    ad_sets = parent.get_ad_sets(fields=fields, params=params)
                else:
                    account = self._get_account(account_id)
                    ad_sets = account.get_ad_sets(fields=fields, params=params)
                return [dict(a) for a in itertools.islice(ad_sets, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_set(self, ad_set_id: str) -> dict[str, Any]:
        """Get detailed info for a specific ad set.

        Args:
            ad_set_id: The ad set ID.

        Returns:
            Ad set data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                ad_set = AdSet(ad_set_id)
                ad_set.api_get(
                    fields=[
                        AdSet.Field.id,
                        AdSet.Field.name,
                        AdSet.Field.status,
                        AdSet.Field.effective_status,
                        AdSet.Field.campaign_id,
                        AdSet.Field.daily_budget,
                        AdSet.Field.lifetime_budget,
                        AdSet.Field.budget_remaining,
                        AdSet.Field.billing_event,
                        AdSet.Field.optimization_goal,
                        AdSet.Field.targeting,
                        AdSet.Field.start_time,
                        AdSet.Field.end_time,
                        AdSet.Field.bid_amount,
                        AdSet.Field.bid_strategy,
                        AdSet.Field.destination_type,
                        AdSet.Field.frequency_control_specs,
                        AdSet.Field.attribution_spec,
                        AdSet.Field.is_dynamic_creative,
                        AdSet.Field.optimization_sub_event,
                        AdSet.Field.pacing_type,
                    ]
                )
                return dict(ad_set)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ads(
        self,
        account_id: str | None = None,
        ad_set_id: str | None = None,
        campaign_id: str | None = None,
        status_filter: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List ads for an account, campaign, or ad set.

        Args:
            account_id: The ad account ID, or None for default.
            ad_set_id: Filter to a specific ad set.
            campaign_id: Filter to a specific campaign.
            status_filter: List of status values to filter by.
            limit: Maximum number of ads to return.

        Returns:
            A list of ad data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                fields = [
                    Ad.Field.id,
                    Ad.Field.name,
                    Ad.Field.status,
                    Ad.Field.effective_status,
                    Ad.Field.adset_id,
                    Ad.Field.campaign_id,
                    Ad.Field.creative,
                    Ad.Field.created_time,
                    Ad.Field.updated_time,
                    Ad.Field.configured_status,
                    Ad.Field.tracking_specs,
                    Ad.Field.conversion_specs,
                    Ad.Field.preview_shareable_link,
                ]
                params: dict[str, Any] = {"limit": limit}
                if status_filter:
                    params["filtering"] = [
                        {
                            "field": "effective_status",
                            "operator": "IN",
                            "value": status_filter,
                        }
                    ]
                if ad_set_id:
                    parent = AdSet(ad_set_id)
                    ads = parent.get_ads(fields=fields, params=params)
                elif campaign_id:
                    parent = Campaign(campaign_id)
                    ads = parent.get_ads(fields=fields, params=params)
                else:
                    account = self._get_account(account_id)
                    ads = account.get_ads(fields=fields, params=params)
                return [dict(a) for a in itertools.islice(ads, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad(self, ad_id: str) -> dict[str, Any]:
        """Get detailed info for a specific ad.

        Args:
            ad_id: The ad ID.

        Returns:
            Ad data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                ad = Ad(ad_id)
                ad.api_get(
                    fields=[
                        Ad.Field.id,
                        Ad.Field.name,
                        Ad.Field.status,
                        Ad.Field.effective_status,
                        Ad.Field.adset_id,
                        Ad.Field.campaign_id,
                        Ad.Field.creative,
                        Ad.Field.created_time,
                        Ad.Field.updated_time,
                        Ad.Field.configured_status,
                        Ad.Field.tracking_specs,
                        Ad.Field.conversion_specs,
                        Ad.Field.preview_shareable_link,
                    ]
                )
                return dict(ad)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_insights(
        self,
        account_id: str | None = None,
        date_preset: str | None = None,
        level: str = "account",
        breakdowns: list[str] | None = None,
        fields: list[str] | None = None,
        time_range: dict[str, str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get performance insights for an ad account.

        Args:
            account_id: The ad account ID, or None for default.
            date_preset: Date preset (e.g., last_7d, last_30d).
            level: Aggregation level (account, campaign, adset, ad).
            breakdowns: List of breakdown dimensions.
            fields: List of metric fields to retrieve.
            time_range: Dict with 'since' and 'until' date strings.
            limit: Maximum number of rows to return.

        Returns:
            A list of insight data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                default_fields = [
                    "impressions",
                    "clicks",
                    "spend",
                    "ctr",
                    "cpc",
                    "cpm",
                    "reach",
                    "actions",
                    "cost_per_action_type",
                ]
                insight_fields = fields or default_fields
                params: dict[str, Any] = {
                    "level": level,
                    "limit": limit,
                }
                if date_preset:
                    params["date_preset"] = date_preset
                if breakdowns:
                    params["breakdowns"] = breakdowns
                if time_range:
                    params["time_range"] = time_range
                insights = account.get_insights(
                    fields=insight_fields,
                    params=params,
                )
                return [dict(row) for row in itertools.islice(insights, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_creatives(
        self,
        account_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List ad creatives for an account.

        Args:
            account_id: The ad account ID, or None for default.
            limit: Maximum number of creatives to return.

        Returns:
            A list of creative data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                creatives = account.get_ad_creatives(
                    fields=[
                        AdCreative.Field.id,
                        AdCreative.Field.name,
                        AdCreative.Field.title,
                        AdCreative.Field.body,
                        AdCreative.Field.image_url,
                        AdCreative.Field.thumbnail_url,
                        AdCreative.Field.call_to_action_type,
                        AdCreative.Field.link_url,
                        AdCreative.Field.status,
                        AdCreative.Field.object_story_spec,
                        AdCreative.Field.url_tags,
                        AdCreative.Field.image_hash,
                    ],
                    params={"limit": limit},
                )
                return [dict(c) for c in itertools.islice(creatives, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_creative(self, creative_id: str) -> dict[str, Any]:
        """Get detailed info for a specific ad creative.

        Args:
            creative_id: The creative ID.

        Returns:
            Creative data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                creative = AdCreative(creative_id)
                creative.api_get(
                    fields=[
                        AdCreative.Field.id,
                        AdCreative.Field.name,
                        AdCreative.Field.title,
                        AdCreative.Field.body,
                        AdCreative.Field.image_url,
                        AdCreative.Field.thumbnail_url,
                        AdCreative.Field.call_to_action_type,
                        AdCreative.Field.link_url,
                        AdCreative.Field.status,
                        AdCreative.Field.object_story_spec,
                        AdCreative.Field.url_tags,
                        AdCreative.Field.image_hash,
                    ]
                )
                return dict(creative)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_audiences(
        self,
        account_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List custom audiences for an account.

        Args:
            account_id: The ad account ID, or None for default.
            limit: Maximum number of audiences to return.

        Returns:
            A list of audience data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                audiences = account.get_custom_audiences(
                    fields=[
                        CustomAudience.Field.id,
                        CustomAudience.Field.name,
                        CustomAudience.Field.subtype,
                        CustomAudience.Field.approximate_count_lower_bound,
                        CustomAudience.Field.approximate_count_upper_bound,
                        CustomAudience.Field.delivery_status,
                        CustomAudience.Field.operation_status,
                        CustomAudience.Field.description,
                        CustomAudience.Field.lookalike_spec,
                        CustomAudience.Field.rule,
                        CustomAudience.Field.data_source,
                        CustomAudience.Field.retention_days,
                        CustomAudience.Field.is_value_based,
                        CustomAudience.Field.sharing_status,
                        CustomAudience.Field.time_created,
                        CustomAudience.Field.time_updated,
                    ],
                    params={"limit": limit},
                )
                return [dict(a) for a in itertools.islice(audiences, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_audience(self, audience_id: str) -> dict[str, Any]:
        """Get detailed info for a specific custom audience.

        Args:
            audience_id: The audience ID.

        Returns:
            Audience data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                audience = CustomAudience(audience_id)
                audience.api_get(
                    fields=[
                        CustomAudience.Field.id,
                        CustomAudience.Field.name,
                        CustomAudience.Field.subtype,
                        CustomAudience.Field.approximate_count_lower_bound,
                        CustomAudience.Field.approximate_count_upper_bound,
                        CustomAudience.Field.delivery_status,
                        CustomAudience.Field.operation_status,
                        CustomAudience.Field.description,
                        CustomAudience.Field.lookalike_spec,
                        CustomAudience.Field.rule,
                        CustomAudience.Field.data_source,
                        CustomAudience.Field.retention_days,
                        CustomAudience.Field.is_value_based,
                        CustomAudience.Field.sharing_status,
                        CustomAudience.Field.time_created,
                        CustomAudience.Field.time_updated,
                    ]
                )
                return dict(audience)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    # ------------------------------------------------------------------
    # Diagnostic methods
    # ------------------------------------------------------------------

    async def get_campaign_diagnostics(self, campaign_id: str) -> dict[str, Any]:
        """Get diagnostic info for a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            Campaign diagnostic data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                campaign = Campaign(campaign_id)
                campaign.api_get(
                    fields=[
                        Campaign.Field.id,
                        Campaign.Field.name,
                        Campaign.Field.status,
                        Campaign.Field.issues_info,
                        Campaign.Field.recommendations,
                    ]
                )
                return dict(campaign)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_set_diagnostics(self, ad_set_id: str) -> dict[str, Any]:
        """Get diagnostic info for an ad set.

        Args:
            ad_set_id: The ad set ID.

        Returns:
            Ad set diagnostic data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                ad_set = AdSet(ad_set_id)
                ad_set.api_get(
                    fields=[
                        AdSet.Field.id,
                        AdSet.Field.name,
                        AdSet.Field.status,
                        AdSet.Field.issues_info,
                        AdSet.Field.recommendations,
                        AdSet.Field.learning_stage_info,
                    ]
                )
                return dict(ad_set)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_diagnostics(self, ad_id: str) -> dict[str, Any]:
        """Get diagnostic info for an ad.

        Args:
            ad_id: The ad ID.

        Returns:
            Ad diagnostic data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                ad = Ad(ad_id)
                ad.api_get(
                    fields=[
                        Ad.Field.id,
                        Ad.Field.name,
                        Ad.Field.status,
                        Ad.Field.ad_review_feedback,
                        Ad.Field.failed_delivery_checks,
                        Ad.Field.issues_info,
                        Ad.Field.recommendations,
                    ]
                )
                return dict(ad)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_fetch)

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def create_campaign(
        self,
        name: str,
        objective: str,
        account_id: str | None = None,
        status: str = "PAUSED",
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        special_ad_categories: list[str] | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        bid_strategy: str | None = None,
        smart_promotion_type: str | None = None,
        spend_cap: int | None = None,
        budget_schedule_specs: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new campaign.

        Args:
            name: Campaign name.
            objective: Campaign objective (e.g., OUTCOME_TRAFFIC).
            account_id: Ad account ID, or None for default.
            status: Initial status (default PAUSED).
            daily_budget: Daily budget in cents.
            lifetime_budget: Lifetime budget in cents.
            special_ad_categories: List of special ad categories.
            start_time: Campaign start time (ISO 8601).
            stop_time: Campaign stop time (ISO 8601).
            bid_strategy: Bid strategy (e.g., LOWEST_COST_WITHOUT_CAP).
            smart_promotion_type: Advantage+ type (e.g., GUIDED_CREATION).
            spend_cap: Campaign spend cap in cents.
            budget_schedule_specs: Budget schedule specifications.
            dry_run: If True, validate only without creating.

        Returns:
            Created campaign data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "objective": objective,
                    "status": status,
                    "special_ad_categories": special_ad_categories or ["NONE"],
                }
                if daily_budget is not None:
                    params["daily_budget"] = daily_budget
                if lifetime_budget is not None:
                    params["lifetime_budget"] = lifetime_budget
                if start_time:
                    params["start_time"] = start_time
                if stop_time:
                    params["stop_time"] = stop_time
                if bid_strategy:
                    params["bid_strategy"] = bid_strategy
                if smart_promotion_type:
                    params["smart_promotion_type"] = smart_promotion_type
                if spend_cap is not None:
                    params["spend_cap"] = spend_cap
                if budget_schedule_specs:
                    params["budget_schedule_specs"] = budget_schedule_specs
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_campaign(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_create)

    async def update_campaign(
        self,
        campaign_id: str,
        name: str | None = None,
        status: str | None = None,
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        bid_strategy: str | None = None,
        smart_promotion_type: str | None = None,
        spend_cap: int | None = None,
        budget_schedule_specs: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update an existing campaign.

        Args:
            campaign_id: The campaign ID to update.
            name: New campaign name.
            status: New status (ACTIVE, PAUSED, ARCHIVED).
            daily_budget: New daily budget in cents.
            lifetime_budget: New lifetime budget in cents.
            start_time: New start time (ISO 8601).
            stop_time: New stop time (ISO 8601).
            bid_strategy: New bid strategy.
            smart_promotion_type: Advantage+ type (e.g., GUIDED_CREATION).
            spend_cap: New campaign spend cap in cents.
            budget_schedule_specs: New budget schedule specifications.
            dry_run: If True, validate only without updating.

        Returns:
            Update result dictionary.
        """
        self._ensure_initialized()

        def _update() -> dict[str, Any]:
            try:
                campaign = Campaign(campaign_id)
                params: dict[str, Any] = {}
                if name is not None:
                    params["name"] = name
                if status is not None:
                    params["status"] = status
                if daily_budget is not None:
                    params["daily_budget"] = daily_budget
                if lifetime_budget is not None:
                    params["lifetime_budget"] = lifetime_budget
                if start_time is not None:
                    params["start_time"] = start_time
                if stop_time is not None:
                    params["stop_time"] = stop_time
                if bid_strategy is not None:
                    params["bid_strategy"] = bid_strategy
                if smart_promotion_type:
                    params["smart_promotion_type"] = smart_promotion_type
                if spend_cap is not None:
                    params["spend_cap"] = spend_cap
                if budget_schedule_specs:
                    params["budget_schedule_specs"] = budget_schedule_specs
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = campaign.api_update(params=params)
                return dict(result) if result else {}
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_update)

    async def create_ad_set(
        self,
        name: str,
        campaign_id: str,
        billing_event: str,
        optimization_goal: str,
        targeting: dict[str, Any],
        account_id: str | None = None,
        status: str = "PAUSED",
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        bid_strategy: str | None = None,
        bid_amount: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        promoted_object: dict[str, Any] | None = None,
        frequency_control_specs: list[dict[str, Any]] | None = None,
        attribution_spec: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new ad set.

        Args:
            name: Ad set name.
            campaign_id: Parent campaign ID.
            billing_event: Billing event (e.g., IMPRESSIONS).
            optimization_goal: Optimization goal (e.g., LINK_CLICKS).
            targeting: Targeting specification dictionary.
            account_id: Ad account ID, or None for default.
            status: Initial status (default PAUSED).
            daily_budget: Daily budget in cents.
            lifetime_budget: Lifetime budget in cents.
            bid_strategy: Bid strategy.
            bid_amount: Bid amount in cents.
            start_time: Start time (ISO 8601).
            end_time: End time (ISO 8601).
            promoted_object: Promoted object dictionary.
            frequency_control_specs: Frequency cap specifications.
            attribution_spec: Attribution window specifications.
            dry_run: If True, validate only without creating.

        Returns:
            Created ad set data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "campaign_id": campaign_id,
                    "billing_event": billing_event,
                    "optimization_goal": optimization_goal,
                    "targeting": targeting,
                    "status": status,
                }
                if daily_budget is not None:
                    params["daily_budget"] = daily_budget
                if lifetime_budget is not None:
                    params["lifetime_budget"] = lifetime_budget
                if bid_strategy:
                    params["bid_strategy"] = bid_strategy
                if bid_amount is not None:
                    params["bid_amount"] = bid_amount
                if start_time:
                    params["start_time"] = start_time
                if end_time:
                    params["end_time"] = end_time
                if promoted_object:
                    params["promoted_object"] = promoted_object
                if frequency_control_specs:
                    params["frequency_control_specs"] = frequency_control_specs
                if attribution_spec:
                    params["attribution_spec"] = attribution_spec
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_ad_set(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_create)

    async def update_ad_set(
        self,
        ad_set_id: str,
        name: str | None = None,
        status: str | None = None,
        daily_budget: int | None = None,
        lifetime_budget: int | None = None,
        targeting: dict[str, Any] | None = None,
        bid_strategy: str | None = None,
        bid_amount: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        optimization_goal: str | None = None,
        frequency_control_specs: list[dict[str, Any]] | None = None,
        attribution_spec: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update an existing ad set.

        Args:
            ad_set_id: The ad set ID to update.
            name: New ad set name.
            status: New status (ACTIVE, PAUSED, ARCHIVED).
            daily_budget: New daily budget in cents.
            lifetime_budget: New lifetime budget in cents.
            targeting: New targeting specification.
            bid_strategy: New bid strategy.
            bid_amount: New bid amount in cents.
            start_time: New start time (ISO 8601).
            end_time: New end time (ISO 8601).
            optimization_goal: New optimization goal.
            frequency_control_specs: New frequency cap specifications.
            attribution_spec: New attribution window specifications.
            dry_run: If True, validate only without updating.

        Returns:
            Update result dictionary.
        """
        self._ensure_initialized()

        def _update() -> dict[str, Any]:
            try:
                ad_set = AdSet(ad_set_id)
                params: dict[str, Any] = {}
                if name is not None:
                    params["name"] = name
                if status is not None:
                    params["status"] = status
                if daily_budget is not None:
                    params["daily_budget"] = daily_budget
                if lifetime_budget is not None:
                    params["lifetime_budget"] = lifetime_budget
                if targeting is not None:
                    params["targeting"] = targeting
                if bid_strategy is not None:
                    params["bid_strategy"] = bid_strategy
                if bid_amount is not None:
                    params["bid_amount"] = bid_amount
                if start_time is not None:
                    params["start_time"] = start_time
                if end_time is not None:
                    params["end_time"] = end_time
                if optimization_goal is not None:
                    params["optimization_goal"] = optimization_goal
                if frequency_control_specs:
                    params["frequency_control_specs"] = frequency_control_specs
                if attribution_spec:
                    params["attribution_spec"] = attribution_spec
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = ad_set.api_update(params=params)
                return dict(result) if result else {}
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_update)

    async def create_ad(
        self,
        name: str,
        adset_id: str,
        creative_id: str,
        account_id: str | None = None,
        status: str = "PAUSED",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new ad.

        Args:
            name: Ad name.
            adset_id: Parent ad set ID.
            creative_id: Creative ID to use.
            account_id: Ad account ID, or None for default.
            status: Initial status (default PAUSED).
            dry_run: If True, validate only without creating.

        Returns:
            Created ad data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "adset_id": adset_id,
                    "creative": {"creative_id": creative_id},
                    "status": status,
                }
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_ad(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_create)

    async def update_ad(
        self,
        ad_id: str,
        name: str | None = None,
        status: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update an existing ad.

        Args:
            ad_id: The ad ID to update.
            name: New ad name.
            status: New status (ACTIVE, PAUSED, ARCHIVED).
            dry_run: If True, validate only without updating.

        Returns:
            Update result dictionary.
        """
        self._ensure_initialized()

        def _update() -> dict[str, Any]:
            try:
                ad = Ad(ad_id)
                params: dict[str, Any] = {}
                if name is not None:
                    params["name"] = name
                if status is not None:
                    params["status"] = status
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = ad.api_update(params=params)
                return dict(result) if result else {}
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_update)

    async def create_ad_creative(
        self,
        name: str,
        object_story_spec: dict[str, Any],
        account_id: str | None = None,
        url_tags: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new ad creative.

        Args:
            name: Creative name.
            object_story_spec: Object story specification dictionary.
            account_id: Ad account ID, or None for default.
            url_tags: URL tags for tracking.
            dry_run: If True, validate only without creating.

        Returns:
            Created creative data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "object_story_spec": object_story_spec,
                }
                if url_tags:
                    params["url_tags"] = url_tags
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_ad_creative(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_create)

    async def update_ad_creative(
        self,
        creative_id: str,
        name: str | None = None,
        url_tags: str | None = None,
        status: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update an existing ad creative.

        Note: Meta does not allow updating object_story_spec on existing creatives.

        Args:
            creative_id: The creative ID to update.
            name: New creative name.
            url_tags: New URL tags.
            status: New status.
            dry_run: If True, validate only without updating.

        Returns:
            Update result dictionary.
        """
        self._ensure_initialized()

        def _update() -> dict[str, Any]:
            try:
                creative = AdCreative(creative_id)
                params: dict[str, Any] = {}
                if name is not None:
                    params["name"] = name
                if url_tags is not None:
                    params["url_tags"] = url_tags
                if status is not None:
                    params["status"] = status
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = creative.api_update(params=params)
                return dict(result) if result else {}
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_update)

    async def create_custom_audience(
        self,
        name: str,
        subtype: str,
        account_id: str | None = None,
        description: str | None = None,
        rule: dict[str, Any] | None = None,
        pixel_id: str | None = None,
        retention_days: int | None = None,
        customer_file_source: str | None = None,
        prefill: bool | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new custom audience.

        Args:
            name: Audience name.
            subtype: Audience subtype (CUSTOM, WEBSITE, APP).
            account_id: Ad account ID, or None for default.
            description: Audience description.
            rule: Audience rule dictionary.
            pixel_id: Pixel ID for website audiences.
            retention_days: Number of days to retain audience members.
            customer_file_source: Source for customer file audiences.
            prefill: Whether to prefill the audience with existing data.
            dry_run: If True, validate only without creating.

        Returns:
            Created audience data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "subtype": subtype,
                }
                if description:
                    params["description"] = description
                if rule:
                    params["rule"] = rule
                if pixel_id:
                    params["pixel_id"] = pixel_id
                if retention_days is not None:
                    params["retention_days"] = retention_days
                if customer_file_source:
                    params["customer_file_source"] = customer_file_source
                if prefill is not None:
                    params["prefill"] = prefill
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_custom_audience(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_create)

    async def create_lookalike_audience(
        self,
        name: str,
        origin_audience_id: str,
        country: str,
        ratio: float,
        account_id: str | None = None,
        description: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new lookalike audience.

        Args:
            name: Audience name.
            origin_audience_id: Source audience ID.
            country: Target country code (e.g., "US").
            ratio: Lookalike ratio (0.01-0.20, where 0.01=1%).
            account_id: Ad account ID, or None for default.
            description: Audience description.
            dry_run: If True, validate only without creating.

        Returns:
            Created audience data dictionary.
        """
        self._ensure_initialized()

        def _create() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {
                    "name": name,
                    "subtype": "LOOKALIKE",
                    "lookalike_spec": {
                        "origin_audience_id": origin_audience_id,
                        "country": country,
                        "ratio": ratio,
                    },
                }
                if description:
                    params["description"] = description
                if dry_run:
                    params["execution_options"] = ["validate_only"]
                result = account.create_custom_audience(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_create)

    # ── Asset (Image/Video) Methods ──────────────────────────────

    async def upload_ad_image(
        self,
        file_path: str,
        name: str | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload an image to the ad account.

        Args:
            file_path: Local file path to the image.
            name: Optional name for the image.
            account_id: Ad account ID, or None for default.

        Returns:
            Image data dictionary containing the image hash.
        """
        self._ensure_initialized()

        import os

        if not os.path.isfile(file_path):
            raise MetaAdsError(
                message=f"File not found: {file_path}",
            )

        def _upload() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                image = AdImage(parent_id=account.get_id())
                image[AdImage.Field.filename] = file_path
                if name:
                    image[AdImage.Field.name] = name
                image.remote_create()
                return dict(image)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_upload)

    async def upload_ad_video(
        self,
        file_path: str | None = None,
        file_url: str | None = None,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload a video to the ad account.

        Accepts either a local file path or a URL that Meta will fetch.

        Args:
            file_path: Local file path to the video.
            file_url: URL for Meta to fetch the video from.
            name: Optional name for the video.
            title: Optional title for the video.
            description: Optional description for the video.
            account_id: Ad account ID, or None for default.

        Returns:
            Video data dictionary containing the video ID.
        """
        self._ensure_initialized()

        if not file_path and not file_url:
            raise MetaAdsError(
                message="Either file_path or file_url must be provided.",
            )

        import os

        if file_path and not os.path.isfile(file_path):
            raise MetaAdsError(
                message=f"File not found: {file_path}",
            )

        def _upload() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                params: dict[str, Any] = {}
                if name:
                    params["name"] = name
                if title:
                    params["title"] = title
                if description:
                    params["description"] = description
                if file_url:
                    params["file_url"] = file_url
                if file_path:
                    params["filepath"] = file_path
                result = account.create_ad_video(params=params)
                return dict(result)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_upload)

    async def get_ad_images(
        self,
        account_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List ad images for an account.

        Args:
            account_id: The ad account ID, or None for default.
            limit: Maximum number of images to return.

        Returns:
            A list of image data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                images = account.get_ad_images(
                    fields=[
                        AdImage.Field.id,
                        AdImage.Field.hash,
                        AdImage.Field.name,
                        AdImage.Field.account_id,
                        AdImage.Field.url,
                        AdImage.Field.url_128,
                        AdImage.Field.width,
                        AdImage.Field.height,
                        AdImage.Field.original_width,
                        AdImage.Field.original_height,
                        AdImage.Field.status,
                        AdImage.Field.permalink_url,
                        AdImage.Field.created_time,
                        AdImage.Field.updated_time,
                    ],
                    params={"limit": limit},
                )
                return [dict(img) for img in itertools.islice(images, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_image(
        self,
        image_hash: str,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a specific ad image by its hash.

        Args:
            image_hash: The image hash.
            account_id: The ad account ID, or None for default.

        Returns:
            Image data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                account = self._get_account(account_id)
                images = account.get_ad_images(
                    fields=[
                        AdImage.Field.id,
                        AdImage.Field.hash,
                        AdImage.Field.name,
                        AdImage.Field.account_id,
                        AdImage.Field.url,
                        AdImage.Field.url_128,
                        AdImage.Field.width,
                        AdImage.Field.height,
                        AdImage.Field.original_width,
                        AdImage.Field.original_height,
                        AdImage.Field.status,
                        AdImage.Field.permalink_url,
                        AdImage.Field.created_time,
                        AdImage.Field.updated_time,
                    ],
                    params={"hashes": [image_hash]},
                )
                results = list(images)
                if not results:
                    raise MetaAdsError(
                        message=f"No image found with hash: {image_hash}",
                    )
                return dict(results[0])
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_videos(
        self,
        account_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List ad videos for an account.

        Args:
            account_id: The ad account ID, or None for default.
            limit: Maximum number of videos to return.

        Returns:
            A list of video data dictionaries.
        """
        self._ensure_initialized()

        def _fetch() -> list[dict[str, Any]]:
            try:
                account = self._get_account(account_id)
                videos = account.get_ad_videos(
                    fields=[
                        AdVideo.Field.id,
                        AdVideo.Field.name,
                        AdVideo.Field.title,
                        AdVideo.Field.description,
                        AdVideo.Field.length,
                        AdVideo.Field.source,
                        AdVideo.Field.picture,
                        AdVideo.Field.permalink_url,
                        AdVideo.Field.created_time,
                        AdVideo.Field.updated_time,
                    ],
                    params={"limit": limit},
                )
                return [dict(v) for v in itertools.islice(videos, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)

    async def get_ad_video(self, video_id: str) -> dict[str, Any]:
        """Get detailed info for a specific ad video.

        Args:
            video_id: The video ID.

        Returns:
            Video data dictionary.
        """
        self._ensure_initialized()

        def _fetch() -> dict[str, Any]:
            try:
                video = AdVideo(video_id)
                video.api_get(
                    fields=[
                        AdVideo.Field.id,
                        AdVideo.Field.name,
                        AdVideo.Field.title,
                        AdVideo.Field.description,
                        AdVideo.Field.length,
                        AdVideo.Field.source,
                        AdVideo.Field.picture,
                        AdVideo.Field.permalink_url,
                        AdVideo.Field.created_time,
                        AdVideo.Field.updated_time,
                    ]
                )
                return dict(video)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e
            except (ConnectionError, TimeoutError, OSError) as e:
                raise MetaAdsError(message=f"Network error: {e}") from e

        return await asyncio.to_thread(_fetch)
