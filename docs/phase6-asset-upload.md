# Plan: Creative Asset Upload (Image & Video) — Phase 6

> **First step after approval:** Save this plan as `docs/phase6-asset-upload.md` in the project.

## Context

The user tried to upload an ad image and discovered the MCP has no asset upload capability. The `create_ad_creative` tool accepts `image_hash` and `image_url` parameters, but there's no way to upload an image to get a hash. The Meta Marketing API and the facebook-business SDK (v25.0) both fully support image and video upload via `AdImage` and `AdVideo` classes. This is listed under v4 Advanced in PROJECT.md.

This adds 6 new tools (41 total), a new `tools/assets.py` module, and completes the "Creative asset upload (image/video)" backlog item.

---

## GitHub Issues (#65–#70)

### #65 — `AdImageModel` and `AdVideoModel` Pydantic models
**Labels:** `phase:asset-upload`, `area:assets`

Add to `src/meta_ads_mcp/models.py`:

**`AdImageModel`:** `id`, `hash`, `name`, `account_id`, `url`, `url_128`, `width`, `height`, `original_width`, `original_height`, `status`, `permalink_url`, `created_time`, `updated_time` + `dimensions_display` property

**`AdVideoModel`:** `id`, `name`, `title`, `description`, `length` (float), `source`, `created_time`, `updated_time` + `duration_display` property

Both use `ConfigDict(extra="ignore")`, all fields with defaults.

### #66 — Client methods for image/video operations
**Labels:** `phase:asset-upload`, `area:core`

Add to `src/meta_ads_mcp/client.py` (6 methods):

| Method | SDK Usage | Notes |
|---|---|---|
| `upload_ad_image(file_path, name?, account_id?)` | `AdImage(parent_id=account_id)` + `remote_create()` with filename field | Validate file exists; returns dict with `hash` |
| `upload_ad_video(file_path?, file_url?, name?, title?, description?, account_id?)` | `account.create_ad_video(params)` | Accept file path OR URL; SDK handles chunked upload |
| `get_ad_images(account_id?, limit=50)` | `account.get_ad_images(fields, params)` | Standard list pattern with `islice` |
| `get_ad_image(image_hash, account_id?)` | `account.get_ad_images(params={"hashes": [hash]})` | Lookup by hash (not composite ID) |
| `get_ad_videos(account_id?, limit=50)` | `account.get_ad_videos(fields, params)` | Standard list pattern |
| `get_ad_video(video_id)` | `AdVideo(id).api_get(fields)` | Standard get pattern |

Import `AdImage` from `facebook_business.adobjects.adimage` and `AdVideo` from `facebook_business.adobjects.advideo`.

**No `dry_run`** — Meta's upload endpoints don't support `validate_only`.

**No video encoding polling** — `waitUntilEncodingReady()` blocks up to 10min. Return immediately with video ID; user can check status via `get_ad_video`.

### #67 — Formatters for image/video display
**Labels:** `phase:asset-upload`, `area:assets`

Add to `src/meta_ads_mcp/formatting.py`:

- `format_ad_image(AdImageModel)` — detail view, **hash prominently displayed** (it's the key output users need for `create_ad_creative`)
- `format_ad_image_list(list[AdImageModel])` — table: Hash | Name | Dimensions | Status
- `format_ad_video(AdVideoModel)` — detail view, **video ID prominently displayed**
- `format_ad_video_list(list[AdVideoModel])` — table: ID | Name | Title | Duration

### #68 — Asset upload and listing tools
**Labels:** `phase:asset-upload`, `area:assets`

**New file: `src/meta_ads_mcp/tools/assets.py`**

| Tool | Annotation | Key params |
|---|---|---|
| `upload_ad_image` | `CREATE` | `file_path`, `name?`, `account_id?` |
| `upload_ad_video` | `CREATE` | `file_path?`, `file_url?`, `name?`, `title?`, `description?`, `account_id?` |
| `list_ad_images` | `READ_ONLY` | `account_id?`, `limit=50` |
| `get_ad_image` | `READ_ONLY` | `image_hash`, `account_id?` |
| `list_ad_videos` | `READ_ONLY` | `account_id?`, `limit=50` |
| `get_ad_video` | `READ_ONLY` | `video_id` |

Plus `register(mcp)` function.

**Update `server.py`:** Add `from meta_ads_mcp.tools import assets` + `assets.register(mcp)`.

**Upload tool output must include usage hint:** e.g., "Use this hash with `create_ad_creative`'s `image_hash` parameter"

### #69 — Unit tests for asset tools
**Labels:** `phase:asset-upload`, `area:assets`

**New files:**
- `tests/test_tools_assets.py` — tool function tests (success, error, params for all 6 tools)
- `tests/test_client_assets.py` — client method tests (mock SDK objects)

**Update existing:**
- `tests/test_models.py` — AdImageModel/AdVideoModel defaults, properties, extra="ignore"
- `tests/test_formatting.py` — format_ad_image/video, list formatters, empty lists
- `tests/test_annotations.py` — verify annotations for 6 new tools

### #70 — Update project docs and metadata
**Labels:** `phase:asset-upload`, `area:core`

- `PROJECT.md` — update tool count (35→41), add Assets category, add `assets.py` to architecture diagram, move asset upload from v4 to completed
- `TASKS.md` — add Phase 6 section with issues #58–#63
- `CLAUDE.md` — add `assets.py` to tools listing
- `README.md` — add asset tools to tool table

---

## Implementation Order

```
#65 (models) → #66 (client) → #67 (formatters) → #68 (tools + registration) → #69 (tests) → #70 (docs)
```

Issues #65–#68 are tightly coupled — implement as a single PR. Tests (#69) can be a second PR or bundled together. Docs (#70) as final PR.

**Recommended: 1–2 PRs total** to avoid merge overhead.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| `file_path` only for images (no base64) | MCP server runs locally with filesystem access; base64 is wasteful. Users with URLs can use `create_ad_creative`'s `image_url` directly |
| `file_path` OR `file_url` for videos | Videos are large — `file_url` lets Meta fetch directly without local download |
| `image_hash` as lookup key (not composite ID) | Hash is what upload returns and what `create_ad_creative` consumes — more natural workflow |
| No `dry_run` for uploads | Meta API doesn't support `validate_only` on upload endpoints |
| No encoding polling for video | Blocking 10min is unacceptable for MCP tool; return immediately, check via `get_ad_video` |
| New `tools/assets.py` module | Assets span images and videos — distinct from creatives which are ad-level objects |

---

## Key Files to Modify

| File | Change |
|---|---|
| `src/meta_ads_mcp/models.py` | Add `AdImageModel`, `AdVideoModel` |
| `src/meta_ads_mcp/client.py` | Add 6 async methods, import `AdImage`/`AdVideo` |
| `src/meta_ads_mcp/formatting.py` | Add 4 formatter functions |
| `src/meta_ads_mcp/tools/assets.py` | **New** — 6 tools + `register()` |
| `src/meta_ads_mcp/server.py` | Import + register assets module |
| `tests/test_tools_assets.py` | **New** — tool tests |
| `tests/test_client_assets.py` | **New** — client tests |
| `tests/test_models.py` | Add model tests |
| `tests/test_formatting.py` | Add formatter tests |
| `tests/test_annotations.py` | Add annotation checks |

---

## Verification

1. **Unit tests:** `uv run pytest` — all existing 390+ tests still pass, new tests pass
2. **Type checking:** `uv run mypy src/` — clean
3. **Linting:** `uv run ruff check src/` + `uv run black --check src/` — clean
4. **MCP Inspector:** `npx @modelcontextprotocol/inspector uv run python -m meta_ads_mcp` — verify 6 new tools appear
5. **Live test (manual):** Upload a test image via `upload_ad_image`, confirm hash returned, use hash in `create_ad_creative`
6. **Live test (manual):** Upload a test video via `upload_ad_video` with `file_url`, confirm video ID returned
