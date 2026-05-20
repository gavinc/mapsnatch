# MapSnatch

[![CI](https://github.com/gavinc/mapsnatch/actions/workflows/ci.yml/badge.svg)](https://github.com/gavinc/mapsnatch/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](./LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-purple)](https://gavinc.github.io/mapsnatch/)

> MindMeister lets you export maps one at a time unless you pay for a Business plan.
> This tool gives you bulk export using their own public API — available on all plan types including free.

**Hosted version (no CLI):** [mapsnatch.com](https://mapsnatch.com) — pay once, export in the browser.

| | |
|---|---|
| [Contributing](./CONTRIBUTING.md) | [Security](./SECURITY.md) |
| [Support](./SUPPORT.md) | [Docs](https://gavinc.github.io/mapsnatch/) |
| [Code of Conduct](./CODE_OF_CONDUCT.md) | [Report a bug](https://github.com/gavinc/mapsnatch/issues/new?template=bug_report.yml) |

## Quickstart

```bash
git clone https://github.com/gavinc/mapsnatch
cd mapsnatch
pip install -e .
echo "MINDMEISTER_API_TOKEN=your_token_here" > .env
mapsnatch
```

Get your API token at: https://www.mindmeister.com/api/settings

## Supported formats

| Flag | Format | Notes |
|------|--------|-------|
| `mm` | FreeMind | **Recommended** — best portability, opens in FreeMind and Freeplane |
| `pdf` | PDF | Good for sharing and archiving |
| `mind` | MindMeister native | For re-import back into MindMeister |
| `xmind` | XMind | For use in the XMind app |
| `rtf` | Rich Text Format | Text-based outline |

**Not supported:** `png` and `docx` return empty responses from the API — these appear to require a Business plan subscription.

## Usage

```
mapsnatch [OPTIONS]

Options:
  --format, -f    Export format: mm, pdf, mind, xmind, rtf  (default: mm)
  --output, -o    Output directory                           (default: ./exports)
  --token, -t     API token (or set MINDMEISTER_API_TOKEN env var / .env file)
  --dry-run       List maps without downloading
  --list-formats  Show supported formats and exit
```

### Examples

```bash
# Export all maps as FreeMind format (default)
mapsnatch

# Export as PDF into a custom directory
mapsnatch --format pdf --output ~/mindmaps

# List what maps would be exported without downloading
mapsnatch --dry-run

# Use a token directly without .env
mapsnatch --token YOUR_TOKEN_HERE
```

## How it works

MindMeister provides a public REST API (v1 + v2) that allows any authenticated user to list and export their maps. This tool:

1. Fetches your full map list from `GET /services/rest/oauth2?method=mm.maps.getList`
2. Downloads each map via `GET /api/v2/maps/{id}.{format}`
3. Extracts the file from its zip container (for `mm`, `mind`, `xmind` formats)
4. Saves it with a sanitised filename into your output directory

Auth uses a personal Bearer token — no OAuth dance required.

## Opening exported files

- **FreeMind (.mm)** — Open with [FreeMind](https://freemind.sourceforge.io/) or [Freeplane](https://www.freeplane.org/) (recommended — free, cross-platform)
- **XMind (.xmind)** — Open with [XMind](https://www.xmind.net/)
- **PDF** — Any PDF viewer
- **RTF** — Any word processor

## Setup

### Get your API token

1. Log in to MindMeister
2. Go to https://www.mindmeister.com/api/settings
3. Copy your personal API token

### Configure

Either:

```bash
# Option A: .env file (recommended)
echo "MINDMEISTER_API_TOKEN=your_token_here" > .env

# Option B: environment variable
export MINDMEISTER_API_TOKEN=your_token_here

# Option C: command line flag
mapsnatch --token your_token_here
```

## Contributing

See **[CONTRIBUTING.md](./CONTRIBUTING.md)**. Pull requests welcome — run `python -m pytest -v` before opening a PR.

## License

[AGPL-3.0-or-later](./LICENSE)
