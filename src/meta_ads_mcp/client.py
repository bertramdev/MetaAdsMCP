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
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.customaudience import CustomAudience
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from meta_ads_mcp.config import MetaAdsConfig

logger = logging.getLogger(__name__)


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
                    ],
                    params=params,
                )
                return [dict(c) for c in itertools.islice(campaigns, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ]
                )
                return dict(campaign)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ]
                )
                return dict(ad_set)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ]
                )
                return dict(ad)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ],
                    params={"limit": limit},
                )
                return [dict(c) for c in itertools.islice(creatives, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ]
                )
                return dict(creative)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ],
                    params={"limit": limit},
                )
                return [dict(a) for a in itertools.islice(audiences, limit)]
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

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
                    ]
                )
                return dict(audience)
            except FacebookRequestError as e:
                raise self._handle_api_error(e) from e

        return await asyncio.to_thread(_fetch)
