# PROJECT.md - Meta Ads MCP Server

## Vision

A locally-hosted MCP server wrapping the Meta (Facebook) Ads API for agency/multi-client ad management. Designed for use via Claude Desktop, Claude Code, and other MCP clients. Enables natural-language interaction with Meta Ads — reading performance data, managing campaigns, and controlling ad delivery across multiple client ad accounts.

## Goals by Version

### v1 — Read Tools
- Account info and listing across multiple ad accounts
- Full campaign structure browsing (campaigns, ad sets, ads)
- Insights with flexible date ranges, breakdowns, and levels
- Creative and audience listing
- Solid test coverage with mocked fixtures

### v2 — Write Tools
- Campaign, ad set, and ad CRUD (create, update, status management)
- Budget updates with confirmation
- All write ops default to PAUSED with dry_run support
- Archive instead of delete

### v3 — SDK v25 Features (Complete)
- Diagnostic tools for campaigns, ad sets, and ads
- Enriched Pydantic models with v25 API fields
- Creative create/update tools with dry_run support
- Advantage+ campaign support, frequency capping, attribution spec
- Audience creation (custom and lookalike)
- 30 total MCP tools, 363 tests passing

### v4 — Asset Upload (Complete)
- Image upload from local file, returns hash for use in creatives
- Video upload from local file or URL (Meta fetches directly)
- Image and video listing and detail views
- 36 total MCP tools, 506 tests passing

### v5 — Advanced
- Bulk operations
- Automated reporting and trend analysis

## Architecture

```
src/meta_ads_mcp/
├── __init__.py
├── server.py        # FastMCP server, lifespan, stdio transport
├── client.py        # Wraps facebook-business SDK, async-compatible
├── models.py        # Pydantic v2 models for all entities
├── config.py        # python-decouple config loading
├── formatting.py    # Markdown formatters for LLM output
└── tools/
    ├── __init__.py
    ├── accounts.py  # Account info and listing
    ├── campaigns.py # Campaign CRUD
    ├── adsets.py    # Ad set CRUD
    ├── ads.py       # Ad CRUD
    ├── insights.py  # Performance reporting and analytics
    ├── creatives.py # Creative management
    ├── audiences.py # Audience management
    └── assets.py    # Image and video asset upload/listing
```

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.14+ |
| MCP framework | mcp SDK v1 (FastMCP) |
| Meta API SDK | facebook-business |
| Data validation | Pydantic v2 |
| Configuration | python-decouple |
| Package manager | Poetry |
| Testing | pytest, pytest-asyncio, pytest-mock |
| Code quality | Black, Ruff, mypy |

## Key Design Decisions

### facebook-business SDK over raw httpx
The official SDK handles authentication, pagination, rate limiting, and field resolution. It also provides typed access to API objects, reducing boilerplate for constructing requests and parsing responses.

### Async wrapping via `asyncio.to_thread()`
The facebook-business SDK is synchronous. Rather than building a custom async HTTP layer, we wrap SDK calls with `asyncio.to_thread()` to maintain FastMCP's async interface without blocking the event loop.

### Read-first phasing
Read tools are lower risk and provide immediate value. They also exercise the full stack (config, client, models, formatting) before write operations add mutation complexity.

### No delete tools
Meta's API supports deletion, but it's irreversible. Archive (setting status to `ARCHIVED`) achieves the same practical result and can be undone. This protects against accidental data loss through LLM tool calls.

### Multi-account via `account_id` parameter
Agency use case requires managing multiple client ad accounts. Every tool accepts an optional `account_id` parameter, falling back to the configured default. This avoids server restarts when switching between clients.

## Scope Boundaries

### Out of scope (current)
- Conversions API (CAPI)
- Product Catalog management
- Lead form management
- Pixel/Events Manager
- Instagram-specific APIs (beyond what's exposed through Ads API)
- SSE transport (stdio only for local hosting)

## Tools (36 across 8 categories)

### Accounts (2)
| Tool | Description |
|---|---|
| `get_ad_accounts` | List all accessible ad accounts for the authenticated user |
| `get_account_info` | Get detailed info for a specific ad account |

### Campaigns (5)
| Tool | Description |
|---|---|
| `list_campaigns` | List campaigns with filtering by status |
| `get_campaign` | Get detailed campaign info including settings |
| `create_campaign` | Create a new campaign (defaults to PAUSED) |
| `update_campaign` | Update campaign name, budget, status, or schedule |
| `get_campaign_diagnostics` | Campaign-level diagnostic scores |

### Ad Sets (5)
| Tool | Description |
|---|---|
| `list_ad_sets` | List ad sets with optional campaign filter |
| `get_ad_set` | Get detailed ad set info including targeting |
| `create_ad_set` | Create a new ad set with targeting and budget |
| `update_ad_set` | Update ad set targeting, budget, status, or schedule |
| `get_ad_set_diagnostics` | Ad set quality/engagement/conversion scores |

### Ads (5)
| Tool | Description |
|---|---|
| `list_ads` | List ads with optional ad set or campaign filter |
| `get_ad` | Get detailed ad info including creative reference |
| `create_ad` | Create a new ad with creative reference |
| `update_ad` | Update ad status, name, or creative |
| `get_ad_diagnostics` | Ad relevance diagnostics |

### Insights (5)
| Tool | Description |
|---|---|
| `get_insights` | Flexible insights query with date range, breakdowns, and level |
| `get_campaign_insights` | Campaign performance with period comparison |
| `get_account_insights` | Get account-level performance metrics |
| `compare_performance` | Compare entities side-by-side |
| `get_breakdown_report` | Age, gender, placement, or device breakdowns |

### Creatives (4)
| Tool | Description |
|---|---|
| `list_creatives` | List ad creatives for an account |
| `get_creative` | Get creative details including thumbnail URL and body |
| `create_ad_creative` | Create a new ad creative with dry_run support |
| `update_ad_creative` | Update creative fields |

### Audiences (4)
| Tool | Description |
|---|---|
| `list_audiences` | List custom and lookalike audiences |
| `get_audience` | Get audience details including size and status |
| `create_custom_audience` | Create website/app/customer file audience |
| `create_lookalike_audience` | Create lookalike from source audience |

### Assets (6)
| Tool | Description |
|---|---|
| `upload_ad_image` | Upload an image file, returns hash for creatives |
| `upload_ad_video` | Upload a video from file or URL |
| `list_ad_images` | List ad images for an account |
| `get_ad_image` | Get image details by hash |
| `list_ad_videos` | List ad videos for an account |
| `get_ad_video` | Get video details by ID |
