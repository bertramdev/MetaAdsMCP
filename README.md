# Meta Ads MCP Server

A locally-hosted MCP server for managing Meta (Facebook) Ads across multiple client ad accounts via Claude Desktop, Claude Code, and other MCP clients.

## Features

- Browse and inspect ad account structure (campaigns, ad sets, ads)
- Query performance insights with flexible date ranges and breakdowns
- Create and manage campaigns, ad sets, ads, creatives, and audiences
- Diagnose delivery issues with campaign, ad set, and ad diagnostics
- Compare performance across entities side-by-side
- Multi-account support for agency workflows
- All output formatted as markdown for LLM readability

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Meta developer account with Marketing API access (see setup guide below)

## Installation

```bash
git clone https://github.com/tomleelong/MetaAdsMCP.git
cd MetaAdsMCP
uv sync
```

## Getting a Meta Access Token

If you don't have Meta developer credentials yet, follow these steps:

### 1. Create a Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com/) and log in
2. Click **My Apps** > **Create App**
3. Select **Other** as the use case, then **Business** as the app type
4. Name your app and click **Create App**

### 2. Add Marketing API

1. In your app dashboard, click **Add Product**
2. Find **Marketing API** and click **Set Up**

### 3. Generate a User Access Token (for development)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click **Generate Access Token**
4. Grant the required permissions: `ads_read`, `ads_management`
5. Copy the token — this is a short-lived token (expires in ~1 hour)

### 4. Exchange for a Long-Lived Token (60 days)

```bash
curl -X GET "https://graph.facebook.com/v25.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

The response contains a `access_token` field with your long-lived token (valid for 60 days).

### 5. (Recommended) Create a System User Token

For a non-expiring token suitable for production use:

1. Go to [Business Manager](https://business.facebook.com/) > **Business Settings**
2. Navigate to **Users** > **System Users**
3. Click **Add** to create a new system user
4. Assign the system user to your ad accounts with appropriate permissions
5. Click **Generate New Token**, select your app, and grant `ads_read` and `ads_management`
6. This token does not expire

### Required Permissions

| Permission | Purpose |
|---|---|
| `ads_read` | Read campaigns, ad sets, ads, insights, audiences, creatives |
| `ads_management` | Create and update campaigns, ad sets, ads, creatives, audiences |

## Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `META_ACCESS_TOKEN` | Yes | — | Meta API access token |
| `META_APP_ID` | Yes | — | Meta App ID from app dashboard |
| `META_APP_SECRET` | Yes | — | Meta App Secret from app dashboard |
| `META_DEFAULT_AD_ACCOUNT_ID` | No | — | Default ad account ID (with `act_` prefix) |
| `META_API_VERSION` | No | `v25.0` | Meta Graph API version |

## Usage

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "uv",
      "args": ["--directory", "/path/to/MetaAdsMCP", "run", "python", "-m", "meta_ads_mcp"],
      "env": {
        "META_ACCESS_TOKEN": "your_token_here",
        "META_APP_ID": "your_app_id",
        "META_APP_SECRET": "your_app_secret",
        "META_DEFAULT_AD_ACCOUNT_ID": "act_your_account_id"
      }
    }
  }
}
```

### Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "uv",
      "args": ["run", "python", "-m", "meta_ads_mcp"],
      "cwd": "/path/to/MetaAdsMCP"
    }
  }
}
```

## Available Tools (35)

### Accounts (2)
| Tool | Description |
|---|---|
| `get_ad_accounts` | List all accessible ad accounts |
| `get_account_info` | Get detailed info for a specific ad account |

### Campaigns (5)
| Tool | Description |
|---|---|
| `list_campaigns` | List campaigns with status filtering |
| `get_campaign` | Get detailed campaign info |
| `create_campaign` | Create a new campaign (defaults to PAUSED) |
| `update_campaign` | Update campaign name, budget, status, or schedule |
| `get_campaign_diagnostics` | Diagnose delivery issues and get recommendations |

### Ad Sets (5)
| Tool | Description |
|---|---|
| `list_ad_sets` | List ad sets with optional campaign filter |
| `get_ad_set` | Get detailed ad set info including targeting |
| `create_ad_set` | Create ad set with targeting, budget, schedule |
| `update_ad_set` | Update ad set settings |
| `get_ad_set_diagnostics` | Diagnose issues with learning stage info |

### Ads (5)
| Tool | Description |
|---|---|
| `list_ads` | List ads with optional filters |
| `get_ad` | Get detailed ad info with creative reference |
| `create_ad` | Create a new ad with creative reference |
| `update_ad_status` | Pause, activate, or archive an ad |
| `get_ad_diagnostics` | Review feedback, delivery checks, and issues |

### Insights (5)
| Tool | Description |
|---|---|
| `get_insights` | Flexible insights query with date range, breakdowns, level |
| `get_account_insights` | Account-level performance summary |
| `get_campaign_insights` | Campaign performance with period comparison |
| `compare_performance` | Compare entities side-by-side |
| `get_breakdown_report` | Age, gender, placement, or device breakdowns |

### Creatives (4)
| Tool | Description |
|---|---|
| `list_creatives` | List ad creatives for an account |
| `get_creative` | Get creative details including thumbnail and body |
| `create_ad_creative` | Create a link ad creative with page, image, CTA |
| `update_ad_creative` | Update creative name, URL tags, or status |

### Audiences (4)
| Tool | Description |
|---|---|
| `list_audiences` | List custom and lookalike audiences |
| `get_audience` | Get audience details including size and status |
| `create_custom_audience` | Create website, customer list, or app audiences |
| `create_lookalike_audience` | Create a lookalike from an existing audience |

## Safety Patterns

All write operations follow these safety conventions:

- **PAUSED by default** — newly created campaigns, ad sets, and ads start as PAUSED
- **Dry run support** — pass `dry_run=True` to validate parameters without making changes
- **Archive, not delete** — use status `ARCHIVED` instead of deleting entities
- **Budget display** — update operations show before/after values for budget changes
- **Budgets in dollars** — pass budgets as dollar strings (e.g., `"50.00"`); conversion to cents is handled internally

## Troubleshooting

Common Meta API errors and how to resolve them:

| Error Code | Cause | Fix |
|---|---|---|
| 17, 32, 613 | Rate limit exceeded | Wait a few minutes and retry |
| 190 | Token expired or invalid | Generate a new access token |
| 200, 10 | Insufficient permissions | Ensure token has `ads_read` and `ads_management` |
| 100 | Invalid parameter | Check parameter values and formats |
| 2, 4 | Temporary Meta API issue | Retry after a few minutes |

When errors occur, the server includes the error code and an actionable suggestion in the output.

## Architecture

```
src/meta_ads_mcp/
  __init__.py
  __main__.py          # Entry point
  server.py            # FastMCP server with lifespan management
  config.py            # Environment-based configuration
  client.py            # Async Meta API client (single SDK interface)
  models.py            # Pydantic v2 models for all entity types
  formatting.py        # Markdown formatters for LLM output
  tools/
    __init__.py        # get_client() context helper
    _write_helpers.py  # Shared write utilities (budget, validation, etc.)
    _insights_helpers.py  # Date preset resolution, period comparison
    accounts.py        # Account listing and info
    campaigns.py       # Campaign CRUD + diagnostics
    adsets.py          # Ad set CRUD + diagnostics
    ads.py             # Ad CRUD + diagnostics
    insights.py        # Performance reporting and analytics
    creatives.py       # Creative CRUD
    audiences.py       # Audience creation and listing
```

Key design decisions:
- **Tools return markdown** — never raw JSON or SDK objects
- **Single API client** — `MetaAdsClient` is the only SDK interface; tools never call the SDK directly
- **Async wrapping** — `asyncio.to_thread()` wraps synchronous SDK calls
- **Pydantic models** — intermediate layer between SDK responses and formatted output
- **Multi-account** — tools accept `account_id`; server has a configurable default

## Example Queries

Once configured, you can ask Claude things like:

- "Show me all active campaigns for account act_123456789"
- "What's the ROAS for Campaign X over the last 30 days?"
- "Compare performance between Campaign A and Campaign B this quarter"
- "Break down ad set performance by age and gender"
- "Create a new traffic campaign called 'Spring Sale 2026' with a $50/day budget"
- "Pause all ads in the 'Test Campaign' ad set"
- "List all custom audiences with more than 10,000 people"
- "What diagnostics issues does my campaign have?"
- "Create a lookalike audience based on my website visitors in the US"
- "Create a link ad creative with a SHOP_NOW CTA"
- "Show this quarter's insights compared to last quarter"

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=meta_ads_mcp

# Lint
uv run ruff check .

# Format
uv run black .

# Type check
uv run mypy src/
```

See [docs/testing.md](docs/testing.md) for the full testing guide including live tests and MCP Inspector usage.

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run python -m meta_ads_mcp
```

## License

MIT
