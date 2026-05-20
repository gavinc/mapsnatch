# MindMeister Bulk Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A public Python CLI tool that bulk-exports all MindMeister maps for any account using only a personal API token — no Business plan required.

**Architecture:** Uses MindMeister's v1 REST API (with OAuth2 Bearer auth) to list all maps, then the v2 API to download each map in the selected format(s). Packaged as an installable Python CLI with `pip install -e .`.

**Tech Stack:** Python 3.9+, `requests`, `python-dotenv`, `tqdm` (progress), `pyproject.toml` packaging

---

## Pre-work: What we know

Confirmed working via live API testing:

| Endpoint | Result |
|---|---|
| `GET /services/rest/oauth2?method=mm.maps.getList` + Bearer token | Returns all maps as JSON |
| `GET /api/v2/maps/{id}.pdf` | PDF document ✓ |
| `GET /api/v2/maps/{id}.mm` | Zip containing FreeMind .mm ✓ |
| `GET /api/v2/maps/{id}.mind` | Zip containing MindMeister native ✓ |
| `GET /api/v2/maps/{id}.xmind` | Zip containing XMind format ✓ |
| `GET /api/v2/maps/{id}.rtf` | RTF document ✓ |
| `GET /api/v2/map_images/{id}.png` | Empty response (not useful) |
| `GET /api/v2/maps/{id}.docx` | Empty response (likely paid) |

Auth: `Authorization: Bearer <API_TOKEN>` header, API token from MindMeister account settings.

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/meister_export/__init__.py`
- Create: `src/meister_export/client.py`
- Create: `src/meister_export/cli.py`
- Create: `tests/__init__.py`

**Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "meister-export"
version = "0.1.0"
description = "Bulk-export all your MindMeister maps without a Business plan"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "requests>=2.31",
    "python-dotenv>=1.0",
    "tqdm>=4.66",
]

[project.scripts]
meister-export = "meister_export.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

**Step 2: Write requirements.txt**

```
requests>=2.31
python-dotenv>=1.0
tqdm>=4.66
pytest>=7.4
pytest-mock>=3.11
responses>=0.24
```

**Step 3: Write .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.env
exports/
*.pdf
*.mm
*.mind
*.xmind
*.rtf
.venv/
venv/
```

**Step 4: Write .env.example**

```
# Get your API token from https://www.mindmeister.com/api/settings
MINDMEISTER_API_TOKEN=your_token_here
```

**Step 5: Create package init files**

```bash
mkdir -p src/meister_export tests
touch src/meister_export/__init__.py tests/__init__.py
```

**Step 6: Install in dev mode**

```bash
pip install -e ".[dev]" 2>/dev/null || pip install -e . && pip install pytest pytest-mock responses
```

**Step 7: Commit**

```bash
git init
git add pyproject.toml requirements.txt .gitignore .env.example
git commit -m "chore: scaffold meister-export package"
```

---

### Task 2: MindMeister API client

**Files:**
- Create: `src/meister_export/client.py`
- Create: `tests/test_client.py`

**Step 1: Write the failing tests**

```python
# tests/test_client.py
import responses
import pytest
from meister_export.client import MindMeisterClient, MapInfo

LIST_MAPS_URL = "https://www.mindmeister.com/services/rest/oauth2"
EXPORT_BASE = "https://www.mindmeister.com/api/v2/maps"

SAMPLE_LIST_RESPONSE = {
    "rsp": {
        "stat": "ok",
        "maps": {
            "page": "1", "pages": "1", "perpage": "100", "total": "2",
            "map": [
                {"id": "111", "title": "My Map", "modified": "2026-01-01 10:00:00", "owner": "42"},
                {"id": "222", "title": "Another Map", "modified": "2026-01-02 10:00:00", "owner": "42"},
            ]
        }
    }
}

@responses.activate
def test_list_maps_returns_all_maps():
    responses.add(responses.GET, LIST_MAPS_URL, json=SAMPLE_LIST_RESPONSE)
    client = MindMeisterClient("test_token")
    maps = client.list_maps()
    assert len(maps) == 2
    assert maps[0].id == "111"
    assert maps[0].title == "My Map"

@responses.activate
def test_list_maps_sends_bearer_auth():
    responses.add(responses.GET, LIST_MAPS_URL, json=SAMPLE_LIST_RESPONSE)
    client = MindMeisterClient("my_token")
    client.list_maps()
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my_token"

@responses.activate
def test_export_map_returns_bytes():
    responses.add(responses.GET, f"{EXPORT_BASE}/111.pdf", body=b"%PDF-1.4 test")
    client = MindMeisterClient("test_token")
    data = client.export_map("111", "pdf")
    assert data == b"%PDF-1.4 test"

@responses.activate
def test_export_map_uses_map_images_for_png():
    responses.add(
        responses.GET,
        "https://www.mindmeister.com/api/v2/map_images/111.png",
        body=b"\x89PNG"
    )
    client = MindMeisterClient("test_token")
    data = client.export_map("111", "png")
    assert data == b"\x89PNG"

def test_client_requires_token():
    with pytest.raises(ValueError, match="API token"):
        MindMeisterClient("")
```

**Step 2: Run tests to confirm they fail**

```bash
cd /home/heavygee/coding/meister-export
python -m pytest tests/test_client.py -v 2>&1 | head -30
```
Expected: ImportError or ModuleNotFoundError

**Step 3: Implement client.py**

```python
# src/meister_export/client.py
from dataclasses import dataclass
from typing import Optional
import time
import requests

LIST_URL = "https://www.mindmeister.com/services/rest/oauth2"
API_V2 = "https://www.mindmeister.com/api/v2"


@dataclass
class MapInfo:
    id: str
    title: str
    modified: str
    owner: str


class MindMeisterClient:
    def __init__(self, token: str, rate_limit_delay: float = 0.5):
        if not token:
            raise ValueError("API token is required")
        self._token = token
        self._delay = rate_limit_delay
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"

    def list_maps(self) -> list[MapInfo]:
        resp = self._session.get(LIST_URL, params={
            "method": "mm.maps.getList",
            "output": "json",
        })
        resp.raise_for_status()
        data = resp.json()
        if data["rsp"]["stat"] != "ok":
            raise RuntimeError(f"API error: {data['rsp']}")
        maps_data = data["rsp"]["maps"]["map"]
        if isinstance(maps_data, dict):  # single map edge case
            maps_data = [maps_data]
        return [
            MapInfo(
                id=m["id"],
                title=m["title"],
                modified=m.get("modified", ""),
                owner=m.get("owner", ""),
            )
            for m in maps_data
        ]

    def export_map(self, map_id: str, fmt: str) -> bytes:
        if fmt == "png":
            url = f"{API_V2}/map_images/{map_id}.png"
        elif fmt == "jpeg":
            url = f"{API_V2}/map_images/{map_id}.jpeg"
        else:
            url = f"{API_V2}/maps/{map_id}.{fmt}"
        resp = self._session.get(url)
        resp.raise_for_status()
        time.sleep(self._delay)
        return resp.content
```

**Step 4: Run tests again — expect PASS**

```bash
python -m pytest tests/test_client.py -v
```
Expected: all 5 tests PASS

**Step 5: Commit**

```bash
git add src/meister_export/client.py tests/test_client.py
git commit -m "feat: add MindMeister API client with list and export"
```

---

### Task 3: Exporter — zip handling and file saving

**Files:**
- Create: `src/meister_export/exporter.py`
- Create: `tests/test_exporter.py`

**Step 1: Write failing tests**

```python
# tests/test_exporter.py
import zipfile, io, os
import pytest
from unittest.mock import MagicMock, patch
from meister_export.client import MapInfo
from meister_export.exporter import Exporter, ZIPPED_FORMATS

def make_zip(inner_name: str, inner_content: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(inner_name, inner_content)
    return buf.getvalue()

def test_zipped_formats_set():
    assert "mm" in ZIPPED_FORMATS
    assert "mind" in ZIPPED_FORMATS
    assert "xmind" in ZIPPED_FORMATS
    assert "pdf" not in ZIPPED_FORMATS

def test_export_pdf_writes_file(tmp_path):
    client = MagicMock()
    client.export_map.return_value = b"%PDF-1.4"
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="1", title="My Test Map", modified="", owner="")
    exp.export_one(m, "pdf")
    out = tmp_path / "My_Test_Map.pdf"
    assert out.exists()
    assert out.read_bytes() == b"%PDF-1.4"

def test_export_mm_unzips(tmp_path):
    client = MagicMock()
    zip_data = make_zip("inner.mm", b"<map><node/></map>")
    client.export_map.return_value = zip_data
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="2", title="Mind Map", modified="", owner="")
    exp.export_one(m, "mm")
    out = tmp_path / "Mind_Map.mm"
    assert out.exists()
    assert b"<map>" in out.read_bytes()

def test_export_sanitises_filename(tmp_path):
    client = MagicMock()
    client.export_map.return_value = b"%PDF"
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="3", title="Map: with/slashes & stuff", modified="", owner="")
    exp.export_one(m, "pdf")
    files = list(tmp_path.glob("*.pdf"))
    assert len(files) == 1
    assert "/" not in files[0].name
    assert ":" not in files[0].name

def test_export_skips_empty_response(tmp_path):
    client = MagicMock()
    client.export_map.return_value = b""
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="4", title="Empty", modified="", owner="")
    result = exp.export_one(m, "png")
    assert result is False
    assert not list(tmp_path.glob("*"))
```

**Step 2: Run tests to confirm fail**

```bash
python -m pytest tests/test_exporter.py -v 2>&1 | head -20
```
Expected: ImportError

**Step 3: Implement exporter.py**

```python
# src/meister_export/exporter.py
import io
import os
import re
import zipfile
from pathlib import Path
from meister_export.client import MindMeisterClient, MapInfo

ZIPPED_FORMATS = {"mm", "mind", "xmind", "mmind"}


def _safe_filename(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe or "untitled"


class Exporter:
    def __init__(self, client: MindMeisterClient, output_dir: str = "exports"):
        self._client = client
        self._out = Path(output_dir)
        self._out.mkdir(parents=True, exist_ok=True)

    def export_one(self, map_info: MapInfo, fmt: str) -> bool:
        data = self._client.export_map(map_info.id, fmt)
        if not data:
            return False

        stem = _safe_filename(map_info.title)

        if fmt in ZIPPED_FORMATS:
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    inner = zf.namelist()[0]
                    data = zf.read(inner)
            except zipfile.BadZipFile:
                pass  # not a zip after all, save as-is

        dest = self._out / f"{stem}.{fmt}"
        dest.write_bytes(data)
        return True

    def export_all(self, maps: list[MapInfo], fmt: str, progress=None) -> dict:
        results = {"ok": [], "skipped": [], "failed": []}
        for m in maps:
            try:
                ok = self.export_one(m, fmt)
                if ok:
                    results["ok"].append(m.title)
                else:
                    results["skipped"].append(m.title)
            except Exception as e:
                results["failed"].append((m.title, str(e)))
            if progress:
                progress.update(1)
        return results
```

**Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_exporter.py -v
```
Expected: all 4 tests PASS

**Step 5: Commit**

```bash
git add src/meister_export/exporter.py tests/test_exporter.py
git commit -m "feat: add exporter with zip extraction and filename sanitisation"
```

---

### Task 4: CLI interface

**Files:**
- Create: `src/meister_export/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write failing test**

```python
# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock
from meister_export.cli import main

def test_cli_requires_token(monkeypatch, capsys):
    monkeypatch.delenv("MINDMEISTER_API_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        main(["--format", "pdf"])
    out = capsys.readouterr()
    assert "token" in out.err.lower() or "token" in out.out.lower()

def test_cli_lists_formats(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--list-formats"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "pdf" in out
    assert "mm" in out

def test_cli_runs_export(monkeypatch, tmp_path):
    monkeypatch.setenv("MINDMEISTER_API_TOKEN", "fake_token")
    mock_client = MagicMock()
    mock_client.list_maps.return_value = [MagicMock(id="1", title="T", modified="", owner="")]
    mock_exporter = MagicMock()
    mock_exporter.export_all.return_value = {"ok": ["T"], "skipped": [], "failed": []}
    with patch("meister_export.cli.MindMeisterClient", return_value=mock_client), \
         patch("meister_export.cli.Exporter", return_value=mock_exporter):
        main(["--format", "pdf", "--output", str(tmp_path)])
    mock_exporter.export_all.assert_called_once()
```

**Step 2: Run to confirm fail**

```bash
python -m pytest tests/test_cli.py -v 2>&1 | head -20
```

**Step 3: Implement cli.py**

```python
# src/meister_export/cli.py
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from meister_export.client import MindMeisterClient
from meister_export.exporter import Exporter

SUPPORTED_FORMATS = ["pdf", "mm", "mind", "xmind", "rtf"]
FORMAT_DESC = {
    "pdf":   "PDF document",
    "mm":    "FreeMind format (open source)",
    "mind":  "MindMeister native format",
    "xmind": "XMind format",
    "rtf":   "Rich Text Format",
}


def main(argv=None):
    import argparse
    from tqdm import tqdm

    parser = argparse.ArgumentParser(
        prog="meister-export",
        description="Bulk-export all your MindMeister maps without a Business plan.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=SUPPORTED_FORMATS,
        default="mm",
        help="Export format (default: mm / FreeMind)",
    )
    parser.add_argument(
        "--output", "-o",
        default="exports",
        help="Output directory (default: ./exports)",
    )
    parser.add_argument(
        "--token", "-t",
        default=None,
        help="API token (or set MINDMEISTER_API_TOKEN env var / .env file)",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="Show available export formats and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List maps that would be exported without downloading",
    )

    args = parser.parse_args(argv)

    if args.list_formats:
        print("Supported export formats:")
        for f, desc in FORMAT_DESC.items():
            print(f"  {f:8s}  {desc}")
        sys.exit(0)

    token = args.token or os.environ.get("MINDMEISTER_API_TOKEN")
    if not token:
        print(
            "Error: no API token found.\n"
            "Set MINDMEISTER_API_TOKEN in your environment or .env file,\n"
            "or pass --token YOUR_TOKEN\n\n"
            "Get your token at: https://www.mindmeister.com/api/settings",
            file=sys.stderr,
        )
        sys.exit(1)

    client = MindMeisterClient(token)

    print("Fetching map list...", flush=True)
    maps = client.list_maps()
    print(f"Found {len(maps)} maps.")

    if args.dry_run:
        for m in maps:
            print(f"  [{m.id}] {m.title}")
        return

    exporter = Exporter(client, output_dir=args.output)
    print(f"Exporting to {args.output}/ as .{args.format} ...")

    with tqdm(total=len(maps), unit="map") as bar:
        results = exporter.export_all(maps, args.format, progress=bar)

    print(f"\nDone: {len(results['ok'])} exported, "
          f"{len(results['skipped'])} skipped, "
          f"{len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed maps:")
        for title, err in results["failed"]:
            print(f"  {title}: {err}")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_cli.py -v
```

**Step 5: Run all tests**

```bash
python -m pytest -v
```
Expected: all tests pass

**Step 6: Smoke test the CLI**

```bash
MINDMEISTER_API_TOKEN=test meister-export --list-formats
meister-export --dry-run  # uses .env
```

**Step 7: Commit**

```bash
git add src/meister_export/cli.py tests/test_cli.py
git commit -m "feat: add CLI with --format, --output, --dry-run, --list-formats"
```

---

### Task 5: README and final packaging

**Files:**
- Create: `README.md`

Write a README.md that:
1. Opens with the problem (MindMeister charges Business plan for bulk export)
2. Shows a 3-step quickstart (clone, add token, run)
3. Lists supported formats
4. Notes which formats are NOT supported and why (PNG/DOCX — likely paid/broken API)
5. Links to MindMeister API settings page for getting a token
6. Has a Contributing section

Key content:

```markdown
# meister-export

> MindMeister lets you export maps one at a time unless you pay for a Business plan.
> This tool gives you bulk export using their own public API — available on all plan types.

## Quickstart

\`\`\`bash
git clone https://github.com/gavinc/meister-export
cd meister-export
pip install -e .
echo "MINDMEISTER_API_TOKEN=your_token_here" > .env
meister-export --format mm
\`\`\`

Get your token at: https://www.mindmeister.com/api/settings

## Supported formats

| Flag | Format | Notes |
|---|---|---|
| `mm` | FreeMind | Best for portability, opens in many apps |
| `pdf` | PDF | Good for sharing/archiving |
| `mind` | MindMeister native | For re-import back into MindMeister |
| `xmind` | XMind | For use in XMind app |
| `rtf` | Rich Text Format | Text-based outline |

## Usage

\`\`\`
meister-export [OPTIONS]

Options:
  --format, -f    Export format: mm, pdf, mind, xmind, rtf  (default: mm)
  --output, -o    Output directory                           (default: ./exports)
  --token, -t     API token (or MINDMEISTER_API_TOKEN env)
  --dry-run       List maps without downloading
  --list-formats  Show supported formats
\`\`\`
```

**Step 1: Write README.md** (full content as above, expanded)

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quickstart and format reference"
```

---

### Task 6: Create GitHub repo under gavinc and push

**Step 1: Verify gavinc identity**

```bash
ssh -T github-gc
/home/heavygee/bin/gh-whoami
```
Expected: `gavinc` identity confirmed

**Step 2: Set remote with correct host alias**

```bash
git remote add origin git@github-gc:gavinc/meister-export.git
```

**Step 3: Create repo on GitHub as gavinc**

```bash
eval "$(ssh-agent -s)" && ssh-add /home/heavygee/.ssh/id_rsa_gavinc
gh-ll repo create gavinc/meister-export \
  --public \
  --description "Bulk-export all your MindMeister maps without a Business plan" \
  --push \
  --source .
```

**Step 4: Verify**

```bash
gh-ll repo view gavinc/meister-export
```

---

## Summary of API findings

| Thing | Detail |
|---|---|
| List maps | `GET /services/rest/oauth2?method=mm.maps.getList&output=json` + Bearer header |
| Export | `GET /api/v2/maps/{id}.{format}` + Bearer header |
| Image export | `GET /api/v2/map_images/{id}.{format}` |
| Auth | `Authorization: Bearer YOUR_TOKEN` |
| Zip formats | `mm`, `mind`, `xmind` come as zip — must unzip to get the file |
| Not working | `png`/`jpeg` return empty; `docx` returns empty (likely Business plan only) |
| Token source | https://www.mindmeister.com/api/settings |
