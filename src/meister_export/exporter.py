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
