# meister-export

> MindMeister lets you export maps one at a time unless you pay for a Business plan.
> This tool gives you bulk export using their own public API — available on all plan types including free.

## Quickstart

```bash
git clone https://github.com/gavinc/meister-export
cd meister-export
pip install -e .
echo "MINDMEISTER_API_TOKEN=your_token_here" > .env
meister-export
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
meister-export [OPTIONS]

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
meister-export

# Export as PDF into a custom directory
meister-export --format pdf --output ~/mindmaps

# List what maps would be exported without downloading
meister-export --dry-run

# Use a token directly without .env
meister-export --token YOUR_TOKEN_HERE
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
meister-export --token your_token_here
```

## Contributing

Pull requests welcome. Please:

- Add tests for new functionality (`tests/` directory, using `pytest` + `responses` for mocking)
- Never commit real API tokens — mock all HTTP in tests
- Follow conventional commit messages (`feat:`, `fix:`, `chore:`, `docs:`)

```bash
pip install -e .
pip install pytest pytest-mock responses
python -m pytest -v
```

## License

MIT
