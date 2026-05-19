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


def test_export_all_returns_summary(tmp_path):
    client = MagicMock()
    client.export_map.return_value = b"%PDF"
    exp = Exporter(client, output_dir=str(tmp_path))
    maps = [
        MapInfo(id="1", title="Map One", modified="", owner=""),
        MapInfo(id="2", title="Map Two", modified="", owner=""),
    ]
    results = exp.export_all(maps, "pdf")
    assert len(results["ok"]) == 2
    assert results["skipped"] == []
    assert results["failed"] == []


def test_export_all_tracks_failures(tmp_path):
    client = MagicMock()
    client.export_map.side_effect = [b"%PDF", RuntimeError("Network error")]
    exp = Exporter(client, output_dir=str(tmp_path))
    maps = [
        MapInfo(id="1", title="OK Map", modified="", owner=""),
        MapInfo(id="2", title="Bad Map", modified="", owner=""),
    ]
    results = exp.export_all(maps, "pdf")
    assert len(results["ok"]) == 1
    assert len(results["failed"]) == 1
    assert results["failed"][0][0] == "Bad Map"
