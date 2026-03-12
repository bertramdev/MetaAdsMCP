# CLAUDE.md - Meta Ads MCP Server

## Project Overview

Meta Ads MCP server — a locally-hosted MCP server wrapping the Meta (Facebook) Ads API for agency/multi-client ad management. Built with Python 3.12+, FastMCP, facebook-business SDK, Pydantic v2, and Poetry.

## Architecture Rules

- Tools live in `src/meta_ads_mcp/tools/` organized by entity: `accounts.py`, `campaigns.py`, `adsets.py`, `ads.py`, `insights.py`, `creatives.py`, `audiences.py`
- Tools return **formatted markdown strings**, never raw JSON or SDK objects
- `MetaAdsClient` in `client.py` is the single API interface — tools never call the facebook-business SDK directly
- Use `asyncio.to_thread()` to wrap synchronous facebook-business SDK calls for async compatibility
- Pydantic v2 models with `extra="ignore"` serve as the intermediate layer between SDK responses and formatted output
- Multi-account support: tools accept an `account_id` parameter; server has a default account from config

## Naming Conventions

- **Tool functions**: `get_`, `list_`, `create_`, `update_` prefixes (e.g., `get_campaign`, `list_ad_sets`)
- **Pydantic models**: PascalCase (e.g., `Campaign`, `AdSet`, `InsightRow`)
- **Formatters**: `format_` prefix (e.g., `format_campaign`, `format_insights_table`)
- **Files**: snake_case module names matching entity names

## Meta API Conventions

- **Entity hierarchy**: Ad Account > Campaign > Ad Set > Ad
- **Account ID prefix**: always `act_` (e.g., `act_123456789`)
- **Objectives**: use `OUTCOME_*` values (e.g., `OUTCOME_TRAFFIC`, `OUTCOME_LEADS`, `OUTCOME_SALES`)
- **Status values**: `ACTIVE`, `PAUSED`, `ARCHIVED`, `DELETED`
- **Effective status**: includes inherited status from parent entities (e.g., ad is ACTIVE but campaign is PAUSED)
- **Date presets**: `today`, `yesterday`, `last_7d`, `last_30d`, `this_month`, `last_month`, etc.
- **Breakdowns**: `age`, `gender`, `country`, `placement`, `device_platform`, `publisher_platform`
- **Budgets**: specified in cents (e.g., $50.00 = 5000)

## Safety Rules for Write Operations

- **Default to PAUSED**: all newly created campaigns, ad sets, and ads start as PAUSED
- **`dry_run` parameter**: write tools accept `dry_run=True` to validate without executing
- **No delete tools**: use archive instead of delete — status set to `ARCHIVED`
- **Budget confirmation**: budget changes should be clearly surfaced in tool output with before/after values

## Testing

- Mock all API calls — never hit real Meta API in tests
- Test fixtures in `tests/fixtures/`
- Use `pytest-asyncio` for async test support
- Test both success and error paths for every tool
- Use `pytest-mock` or `unittest.mock` for SDK mocking

## Configuration

Environment variables (loaded via `python-decouple`):

| Variable | Required | Description |
|---|---|---|
| `META_ACCESS_TOKEN` | Yes | Meta API access token |
| `META_APP_ID` | Yes | Meta App ID |
| `META_APP_SECRET` | Yes | Meta App Secret |
| `META_DEFAULT_AD_ACCOUNT_ID` | No | Default ad account (with `act_` prefix) |
| `META_API_VERSION` | No | API version (default: `v21.0`) |

**Never log or expose tokens in output.**

## Code Quality

- **Formatter**: Black
- **Linter**: Ruff
- **Type checker**: mypy
- **Docstrings**: Google-style for all public functions, classes, and modules
- **Type hints**: required for all function parameters and return values
- **Commits**: conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`)

## Project Management

- GitHub Issues + GitHub Projects board for all trackable work
- TASKS.md mirrors issue status; reference `#N` in commits and PRs
- Use `gh` CLI for issue/board management
- Phase labels: `phase:foundation`, `phase:read-tools`, `phase:write-tools`, `phase:polish`
- Area labels: `area:insights`, `area:campaigns`, `area:adsets`, `area:ads`, `area:accounts`, `area:creatives`, `area:audiences`, `area:core`
- PRs reference issues with "Closes #N" for auto-closing
