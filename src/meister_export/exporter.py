import io
import re
import zipfile
from pathlib import Path

from meister_export.client import MapInfo, MindMeisterClient

ZIPPED_FORMATS = {"mm", "mind", "xmind", "mmind"}

# Expected content type per format (after unzipping where applicable)
_EXPECTED_TYPE: dict[str, tuple[str, ...]] = {
    "mm": ("xml",),
    "mind": ("xml",),
    "xmind": ("xml", "zip"),  # XMind files are themselves zip containers
    "mmind": ("xml", "zip"),
    "pdf": ("pdf",),
    "rtf": ("rtf",),
}


def detect_content_type(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"\x89PNG":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        return "zip"
    if data[:5] in (b"{\\rtf", b"{\\RTF"):
        return "rtf"
    if data[:1] == b"<":
        return "xml"
    return "unknown"


def validate_directory(directory: Path, fmt: str) -> dict:
    """Check every .{fmt} file in directory for correct content type.
    Returns {"ok": int, "bad": [{"file": str, "detected": str}, ...]}
    """
    expected = _EXPECTED_TYPE.get(fmt, ())
    results: dict = {"ok": 0, "bad": []}
    for f in sorted(directory.glob(f"*.{fmt}")):
        detected = detect_content_type(f.read_bytes())
        if detected in expected:
            results["ok"] += 1
        else:
            results["bad"].append({"file": f.name, "detected": detected})
    return results


def _safe_filename(title: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe or "untitled"


def _extract_from_zip(data: bytes, fmt: str) -> bytes:
    """Extract the target-format file from a zip, ignoring embedded images etc."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        # Prefer the file that matches the requested extension
        target = next((n for n in names if n.lower().endswith(f".{fmt}")), None)
        # Fall back to first entry if none matched (shouldn't happen, but safe)
        if target is None:
            target = names[0]
        return zf.read(target)


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
                data = _extract_from_zip(data, fmt)
            except (zipfile.BadZipFile, IndexError):
                pass  # not a zip — save raw bytes and let validation catch it

        dest = self._out / f"{stem}.{fmt}"
        dest.write_bytes(data)

        # Warn if saved content doesn't match the expected type
        expected = _EXPECTED_TYPE.get(fmt, ())
        detected = detect_content_type(data)
        if expected and detected not in expected:
            print(
                f"  WARNING: {map_info.title!r} — saved as .{fmt} but content "
                f"detected as {detected!r}. File: {dest.name}"
            )

        return True

    def export_all(self, maps: list, fmt: str, progress=None) -> dict:
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
