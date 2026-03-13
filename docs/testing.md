# Testing Guide

This guide covers how to test the Meta Ads MCP server at every level: unit tests, integration workflows, live API tests, and manual verification via MCP Inspector.

## Unit Tests

Run the full test suite:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=meta_ads_mcp --cov-report=term-missing
```

Run a specific test file:

```bash
poetry run pytest tests/test_tools_campaigns.py -v
```

## Integration Workflow Tests

`tests/test_integration_workflows.py` contains mocked multi-step workflow tests that verify tool interactions without hitting the real API:

```bash
poetry run pytest tests/test_integration_workflows.py -v
```

These cover:
- Campaign creation workflow (create -> get -> update -> insights)
- Full funnel setup (campaign -> ad set -> creative -> ad)
- Diagnosis workflow (list -> diagnostics chain)
- Audience workflow (create custom -> create lookalike -> list)

## Live API Tests

`tests/test_live.py` runs against the real Meta Ads API. These require valid credentials in `.env` and are automatically skipped in CI.

```bash
poetry run pytest tests/test_live.py -v -s
```

Prerequisites:
- Valid `.env` file with `META_ACCESS_TOKEN`, `META_APP_ID`, `META_APP_SECRET`
- `META_DEFAULT_AD_ACCOUNT_ID` set for account-specific tests
- Network access to the Meta Graph API

## MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) provides a web UI for testing tools interactively.

### Start the Inspector

```bash
npx @modelcontextprotocol/inspector poetry run python -m meta_ads_mcp
```

This opens a browser at `http://localhost:5173` where you can:
1. See all 35 registered tools in the left panel
2. Click any tool to view its schema and parameters
3. Execute tools with test parameters and see formatted markdown output

### Tool Registration Verification

After starting the Inspector, verify all tools appear:

**Accounts (2)**: `get_ad_accounts`, `get_account_info`
**Campaigns (5)**: `list_campaigns`, `get_campaign`, `create_campaign`, `update_campaign`, `get_campaign_diagnostics`
**Ad Sets (5)**: `list_ad_sets`, `get_ad_set`, `create_ad_set`, `update_ad_set`, `get_ad_set_diagnostics`
**Ads (5)**: `list_ads`, `get_ad`, `create_ad`, `update_ad_status`, `get_ad_diagnostics`
**Insights (5)**: `get_insights`, `get_account_insights`, `get_campaign_insights`, `compare_performance`, `get_breakdown_report`
**Creatives (4)**: `list_creatives`, `get_creative`, `create_ad_creative`, `update_ad_creative`
**Audiences (4)**: `list_audiences`, `get_audience`, `create_custom_audience`, `create_lookalike_audience`

### Suggested Manual Tests

1. **Read flow**: `get_ad_accounts` -> pick an account -> `list_campaigns` -> `get_campaign` -> `get_campaign_insights`
2. **Write flow (dry run)**: `create_campaign` with `dry_run=true` -> verify PAUSED status in output
3. **Error handling**: `get_campaign` with an invalid ID -> verify error code and suggestion appear
4. **Date presets**: `get_insights` with `date_preset=this_quarter` -> verify date range is correct

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "poetry",
      "args": ["run", "python", "-m", "meta_ads_mcp"],
      "cwd": "/path/to/MetaAdsMCP",
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

## Claude Code Configuration

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "poetry",
      "args": ["run", "python", "-m", "meta_ads_mcp"],
      "cwd": "/path/to/MetaAdsMCP"
    }
  }
}
```

Credentials are loaded from the `.env` file in the MetaAdsMCP directory.

## Code Quality Checks

Run all quality checks before submitting changes:

```bash
poetry run ruff check .       # Lint
poetry run black --check .    # Format check
poetry run mypy src/          # Type check
poetry run pytest             # Tests
```
