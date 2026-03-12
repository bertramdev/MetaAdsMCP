# Phase 1: Foundation Build (Issues #1-#7)

## Context
The Meta Ads MCP project has docs and GitHub issues but zero code. All 37 issues are open. Phase 1 builds the foundation: project scaffold, config, client, models, server skeleton, and formatters. This unblocks Phase 2 (read tools).

## Implementation Order

### 1. Project Scaffold + Poetry (#1, #2)
**Files to create:**
- `pyproject.toml` -- Poetry config with dependencies, entry point, tool config (Black, Ruff, mypy, pytest)
- `src/meta_ads_mcp/__init__.py` -- Package init with `__version__`
- `src/meta_ads_mcp/__main__.py` -- `python -m meta_ads_mcp` support
- `src/meta_ads_mcp/tools/__init__.py` -- Tools package init
- `src/meta_ads_mcp/tools/{accounts,campaigns,adsets,ads,insights,creatives,audiences}.py` -- Placeholder modules with docstrings
- `tests/__init__.py`, `tests/fixtures/` -- Test infrastructure

**Dependencies:**
- `mcp ^1.26`, `facebook-business ^21.0`, `pydantic ^2.0`, `python-decouple ^3.8`
- Dev: `pytest ^8.0`, `pytest-asyncio ^0.24`, `pytest-mock ^3.14`, `black ^24.0`, `ruff ^0.8`, `mypy ^1.13`, `pytest-cov ^6.0`

**Then:** `poetry install` to verify resolution

### 2. Config (#3)
**File:** `src/meta_ads_mcp/config.py`
- Frozen `dataclass` `MetaAdsConfig` with fields: `access_token`, `app_id`, `app_secret`, `default_account_id` (optional), `api_version` (default `v21.0`)
- `from_env()` classmethod using `python-decouple` `config()`
- `resolve_account_id(account_id)` -- resolves explicit or default, ensures `act_` prefix
- `masked_token` property for safe logging

**Test:** `tests/test_config.py` -- env loading, defaults, resolve logic, masking, frozen check

### 3. Models (#5)
**File:** `src/meta_ads_mcp/models.py`
- 7 Pydantic v2 models, all with `ConfigDict(extra="ignore")` and empty-string/zero defaults:
  - `AdAccountModel` -- id, name, account_status, currency, timezone, amounts + `status_display`, `amount_spent_formatted` properties
  - `CampaignModel` -- id, name, status, effective_status, objective, budgets, times + budget formatting properties
  - `AdSetModel` -- id, name, status, campaign_id, budgets, billing_event, optimization_goal, targeting dict + `targeting_summary` property
  - `AdModel` -- id, name, status, adset_id, campaign_id, creative dict + `creative_id` property
  - `AdCreativeModel` -- id, name, title, body, image_url, thumbnail_url, CTA, link_url
  - `InsightRow` -- metrics (impressions, clicks, spend, ctr, cpc, cpm, reach), breakdown fields + `get_action_value()`, `get_cost_per_action()` helpers
  - `CustomAudienceModel` -- id, name, subtype, size bounds, delivery/operation status + `size_display` property

**Test:** `tests/test_models.py` -- construction from fixture dicts, extra="ignore", computed properties, minimal data defaults

### 4. Client (#4)
**File:** `src/meta_ads_mcp/client.py`
- `MetaAdsError` exception with `message`, `error_code`, `error_subcode`
- `MetaAdsClient` class:
  - `__init__(config)` -- stores config, `_api = None`
  - `initialize()` -- calls `FacebookAdsApi.init()`
  - `_ensure_initialized()`, `_get_account(account_id)`, `_handle_api_error(e)`
  - **All public methods async**, using `asyncio.to_thread(_fetch)` pattern, returning `dict[str, Any]` or `list[dict[str, Any]]`
  - Methods: `get_ad_accounts()`, `get_account_info(account_id)`, `get_campaigns(account_id, status_filter, limit)`, `get_campaign(campaign_id)`, `get_ad_sets(account_id, campaign_id, status_filter, limit)`, `get_ad_set(ad_set_id)`, `get_ads(account_id, ad_set_id, campaign_id, status_filter, limit)`, `get_ad(ad_id)`, `get_insights(account_id, date_preset, level, breakdowns, fields, time_range, limit)`, `get_creatives(account_id, limit)`, `get_creative(creative_id)`, `get_audiences(account_id, limit)`, `get_audience(audience_id)`

**Test:** `tests/test_client.py` -- mock all SDK classes, test each method returns dicts, test error handling, test uninitialized guard

### 5. Formatting (#7)
**File:** `src/meta_ads_mcp/formatting.py`
- 14 formatter functions (single + list for each entity, plus insights table and error):
  - `format_account` / `format_account_list` -- detail view / table
  - `format_campaign` / `format_campaign_list`
  - `format_ad_set` / `format_ad_set_list`
  - `format_ad` / `format_ad_list`
  - `format_creative` / `format_creative_list`
  - `format_insights_table(rows, title)` -- auto-detects level and breakdowns, builds dynamic columns
  - `format_audience` / `format_audience_list`
  - `format_error(message)`
- All return markdown strings with `##` headers, bullet lists for detail views, tables for lists

**Test:** `tests/test_formatting.py` -- sample models in, markdown out, empty list handling, breakdown variations

### 6. Server Skeleton (#6)
**File:** `src/meta_ads_mcp/server.py`
- `AppContext` dataclass holding `client: MetaAdsClient` and `config: MetaAdsConfig`
- `app_lifespan(server)` async context manager -- loads config, initializes client, yields `AppContext`
- `mcp = FastMCP("Meta Ads MCP", lifespan=app_lifespan)`
- `main()` function -- calls `mcp.run(transport="stdio")`

**Entry point in pyproject.toml:** `meta-ads-mcp = "meta_ads_mcp.server:main"`

**Test:** `tests/test_server.py` -- mocked lifespan, server instance checks

## Commit Strategy
- `feat: project scaffold with pyproject.toml and directory structure (#1, #2)` -- after poetry install verified
- `feat: add config.py with MetaAdsConfig and env var loading (#3)` -- with tests passing
- `feat: add Pydantic v2 models for all Meta Ads entities (#5)` -- with tests passing
- `feat: add MetaAdsClient with async SDK wrapper and error handling (#4)` -- with tests passing
- `feat: add markdown formatters for all entity types (#7)` -- with tests passing
- `feat: add server.py skeleton with FastMCP lifespan and entry point (#6)` -- with tests passing

## Verification
1. `poetry run python -c "from meta_ads_mcp.server import mcp; print('OK')"`
2. `poetry run mypy src/`
3. `poetry run ruff check .`
4. `poetry run black --check .`
5. `poetry run pytest -v`
6. `poetry run meta-ads-mcp` starts and hangs on stdio (correct behavior)
