# TASKS.md - Meta Ads MCP Server

## Status Legend

- `[ ]` — Not started (Backlog / Ready)
- `[~]` — In progress
- `[x]` — Done
- `[!]` — Blocked

GitHub Project: [Meta Ads MCP](https://github.com/users/tomleelong/projects/2)

---

## Phase 1: Foundation

- [x] #1 Project scaffold — pyproject.toml, directory structure, .gitignore, .env.example
- [x] #2 Poetry environment with all dependencies
- [x] #3 `config.py` — MetaAdsConfig, env var loading, multi-account support
- [x] #4 `client.py` — MetaAdsClient wrapping SDK, async-compatible via `to_thread`, error handling
- [x] #5 `models.py` — Pydantic v2 models (AdAccount, Campaign, AdSet, Ad, AdCreative, InsightRow, CustomAudience)
- [x] #6 `server.py` skeleton — FastMCP init, lifespan, stdio transport, main entry point
- [x] #7 `formatting.py` — base markdown formatters for all entity types

## Phase 2: Read Tools

### Accounts
- [x] #8 `get_ad_accounts` — list accessible ad accounts
- [x] #9 `get_account_info` — detailed account info

### Campaigns
- [x] #10 `list_campaigns` — list with status filtering
- [x] #11 `get_campaign` — detailed campaign info

### Ad Sets
- [x] #12 `list_ad_sets` — list with campaign filter
- [x] #13 `get_ad_set` — detailed ad set info with targeting

### Ads
- [x] #14 `list_ads` — list with ad set/campaign filter
- [x] #15 `get_ad` — detailed ad info with creative reference

### Insights
- [x] #16 `get_insights` — flexible date/breakdowns/level query
- [x] #17 `get_campaign_insights` — campaign performance with period comparison
- [x] #18 `get_account_insights` — account-level performance metrics
- [x] #19 `compare_performance` — compare entities side-by-side
- [x] #20 `get_breakdown_report` — age/gender/placement/device breakdowns

### Creatives
- [x] #21 `list_creatives` — list ad creatives
- [x] #22 `get_creative` — creative details with thumbnail and body

### Audiences
- [x] #23 `list_audiences` — custom and lookalike audiences
- [x] #24 `get_audience` — audience details, size, status

### Testing
- [x] #25 Unit tests for all read tools with mocked fixtures

## Phase 3: Write Tools

- [x] #26 `create_campaign` — defaults PAUSED, dry_run support
- [x] #27 `update_campaign` — name, budget, status, schedule
- [x] #28 `create_ad_set` — targeting, budget, schedule, bid strategy
- [x] #29 `update_ad_set` — targeting, budget, status, schedule
- [x] #30 `create_ad` — with creative reference
- [x] #31 `update_ad_status` — pause/activate/archive
- [x] #32 Unit tests for all write tools

## Phase 5: SDK v25 Features

### Diagnostics
- [x] #42 `get_campaign_diagnostics` — campaign-level diagnostic scores
- [x] #43 `get_ad_set_diagnostics` — ad set quality/engagement/conversion scores
- [x] #44 `get_ad_diagnostics` — ad relevance diagnostics

### Enriched Models
- [x] #45 Enrich `CampaignModel` with v25 fields (smart_promotion_type, budget_schedule_specs, etc.)
- [x] #46 Enrich `AdSetModel` with v25 fields (frequency_control_specs, attribution_spec, etc.)
- [x] #47 Enrich `AdModel` with v25 fields (conversion_specs, tracking_specs, etc.)
- [x] #48 Enrich `AdCreativeModel` with v25 fields (asset_feed_spec, degrees_of_freedom_spec, etc.)
- [x] #49 Enrich `CustomAudienceModel` with v25 fields (rule, data_source, retention_days, etc.)

### Creative Write Tools
- [x] #50 `create_ad_creative` — create ad creative with dry_run support
- [x] #51 `update_ad_creative` — update creative fields

### Advanced Features
- [x] #52 Advantage+ campaign support (smart_promotion_type, spend_cap)
- [x] #53 Frequency capping (frequency_control_specs on ad sets)
- [x] #54 Attribution spec support on ad sets

### Audience Creation Tools
- [x] #55 `create_custom_audience` — website/app/customer file audiences
- [x] #56 `create_lookalike_audience` — lookalike from source audience
- [x] #57 Unit tests for all Phase 5 tools and models

## Phase 4: Polish

- [x] #33 Comprehensive error handling for Meta API errors (rate limits, permissions, invalid params)
- [ ] #34 Pagination support across all list tools (skipped)
- [x] #35 Date range presets for insights
- [x] #36 End-to-end testing (Claude Desktop config, MCP Inspector)
- [x] #37 README finalization with usage examples

## Backlog / Future

- [x] #40 Persistent Meta access token — system user token (non-expiring)
- [ ] Creative upload tools (image/video asset upload)
- [ ] Bulk operations (batch status changes, batch budget updates)
- [ ] Trend analysis / ROAS tracking tools
- [ ] SSE transport for remote hosting
- [ ] Automated reporting (scheduled insight summaries)
