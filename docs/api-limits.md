# MindMeister API limits

MapSnatch only uses endpoints that work with a **personal access token** from [mindmeister.com/api](https://www.mindmeister.com/api) on standard plans. Behavior can change if Meister updates their API.

## Supported export formats

| Format | Extension | API path | Notes |
|--------|-----------|----------|-------|
| FreeMind | `.mm` | `/api/v2/maps/{id}.mm` | Zip container; recommended for portability |
| PDF | `.pdf` | `/api/v2/maps/{id}.pdf` | Raw PDF bytes |
| MindMeister | `.mind` | `/api/v2/maps/{id}.mind` | Zip container |
| XMind | `.xmind` | `/api/v2/maps/{id}.xmind` | Zip container |
| RTF | `.rtf` | `/api/v2/maps/{id}.rtf` | Text outline |

## Not supported (CLI)

| Format | Why |
|--------|-----|
| PNG / JPEG | `map_images` endpoints often empty or plan-gated |
| DOCX | Empty responses observed on non-Business accounts |

If you need Markdown or OPML, export as **FreeMind (`.mm`)** and convert with [Pandoc](https://pandoc.org/) or similar.

## Rate limiting

The client sleeps **0.5s** between export downloads by default to avoid hammering the API. Large libraries (hundreds of maps) can take several minutes.

## Authentication

- Personal access token from [mindmeister.com/api](https://www.mindmeister.com/api)
- Sent as `Authorization: Bearer <token>`
- **Never** commit tokens; revoke at Meister if leaked

## Business plan vs this tool

MindMeister reserves **bulk export in the product UI** for Business. The **public API** still allows per-map export for authenticated users — MapSnatch automates that loop.

## Upstream references

- [MindMeister API overview](https://www.mindmeister.com/api)
- Report API bugs to Meister; report MapSnatch CLI bugs on [GitHub Issues](https://github.com/gavinc/mapsnatch/issues)
