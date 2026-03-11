# TASKS.md - Meta Ads MCP Server

## Status Legend

- `[ ]` — Not started (Backlog / Ready)
- `[~]` — In progress
- `[x]` — Done
- `[!]` — Blocked

GitHub Issues: each task maps to a GitHub Issue (`#N`). Issue numbers will be added after creation.

---

## Phase 1: Foundation

- [ ] Project scaffold — pyproject.toml, directory structure, .gitignore, .env.example
- [ ] Poetry environment with all dependencies
- [ ] `config.py` — MetaAdsConfig dataclass, env var loading, multi-account support
- [ ] `client.py` — MetaAdsClient wrapping SDK, async-compatible via `to_thread`, error handling
- [ ] `models.py` — Pydantic v2 models (AdAccount, Campaign, AdSet, Ad, AdCreative, InsightRow, CustomAudience)
- [ ] `server.py` skeleton — FastMCP init, lifespan, stdio transport, main entry point
- [ ] `formatting.py` — base markdown formatters for all entity types

## Phase 2: Read Tools

### Accounts
- [ ] `get_ad_accounts` — list accessible ad accounts
- [ ] `get_account_info` — detailed account info

### Campaigns
- [ ] `list_campaigns` — list with status filtering
- [ ] `get_campaign` — detailed campaign info

### Ad Sets
- [ ] `list_ad_sets` — list with campaign filter
- [ ] `get_ad_set` — detailed ad set info with targeting

### Ads
- [ ] `list_ads` — list with ad set/campaign filter
- [ ] `get_ad` — detailed ad info with creative reference

### Insights
- [ ] `get_insights` — flexible date/breakdowns/level query
- [ ] `get_campaign_insights` — campaign performance with period comparison
- [ ] `get_account_insights` — account-level performance metrics
- [ ] `compare_performance` — compare entities side-by-side
- [ ] `get_breakdown_report` — age/gender/placement/device breakdowns

### Creatives
- [ ] `list_creatives` — list ad creatives
- [ ] `get_creative` — creative details with thumbnail and body

### Audiences
- [ ] `list_audiences` — custom and lookalike audiences
- [ ] `get_audience` — audience details, size, status

### Testing
- [ ] Unit tests for all read tools with mocked fixtures

## Phase 3: Write Tools

- [ ] `create_campaign` — defaults PAUSED, dry_run support
- [ ] `update_campaign` — name, budget, status, schedule
- [ ] `create_ad_set` — targeting, budget, schedule, bid strategy
- [ ] `update_ad_set` — targeting, budget, status, schedule
- [ ] `create_ad` — with creative reference
- [ ] `update_ad_status` — pause/activate/archive
- [ ] Unit tests for all write tools

## Phase 4: Polish

- [ ] Comprehensive error handling for Meta API errors (rate limits, permissions, invalid params)
- [ ] Pagination support across all list tools
- [ ] Date range presets for insights
- [ ] End-to-end testing (Claude Desktop config, MCP Inspector)
- [ ] README finalization with usage examples

## Backlog / Future

- [ ] Creative upload tools
- [ ] Audience creation (custom, lookalike)
- [ ] Bulk operations (batch status changes, batch budget updates)
- [ ] Trend analysis / ROAS tracking tools
- [ ] Advantage+ campaign support
- [ ] SSE transport for remote hosting
- [ ] Automated reporting (scheduled insight summaries)
