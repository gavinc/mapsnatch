import io
import zipfile
from unittest.mock import MagicMock

from meister_export.client import MapInfo
from meister_export.exporter import (
    ZIPPED_FORMATS,
    Exporter,
    detect_content_type,
    validate_directory,
)


def make_zip(*entries: tuple) -> bytes:
    """entries: list of (filename, content_bytes)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries:
            zf.writestr(name, content)
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
    zip_data = make_zip(("inner.mm", b"<map><node/></map>"))
    client.export_map.return_value = zip_data
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="2", title="Mind Map", modified="", owner="")
    exp.export_one(m, "mm")
    out = tmp_path / "Mind_Map.mm"
    assert out.exists()
    assert b"<map>" in out.read_bytes()


def test_export_mm_with_embedded_images_extracts_mm_not_image(tmp_path):
    """Maps with embedded images: zip contains JPEGs first, then the .mm file.
    Exporter must find the .mm file, not blindly take the first entry."""
    client = MagicMock()
    jpeg_bytes = b'\xff\xd8\xff' + b'\x00' * 100   # fake JPEG magic
    mm_xml = b"<map><node TEXT='Projects'/></map>"
    zip_data = make_zip(
        ("1000006705.jpg", jpeg_bytes),
        ("1000006706.jpg", jpeg_bytes),
        ("Projects___Todos.mm", mm_xml),
    )
    client.export_map.return_value = zip_data
    exp = Exporter(client, output_dir=str(tmp_path))
    m = MapInfo(id="2897821606", title="Projects / Todos", modified="", owner="")
    exp.export_one(m, "mm")
    out = tmp_path / "Projects___Todos.mm"
    assert out.exists(), "Output file should exist"
    content = out.read_bytes()
    assert content == mm_xml, "Should have saved the .mm XML, not JPEG bytes"


# --- detect_content_type tests ---

def test_detect_content_type_xml():
    assert detect_content_type(b"<map><node/></map>") == "xml"
    assert detect_content_type(b"<?xml version") == "xml"

def test_detect_content_type_png():
    assert detect_content_type(b"\x89PNG\r\n\x1a\n") == "png"

def test_detect_content_type_jpeg():
    assert detect_content_type(b"\xff\xd8\xff") == "jpeg"

def test_detect_content_type_pdf():
    assert detect_content_type(b"%PDF-1.4") == "pdf"

def test_detect_content_type_zip():
    assert detect_content_type(b"PK\x03\x04") == "zip"

def test_detect_content_type_rtf():
    assert detect_content_type(b"{\\rtf1") == "rtf"


# --- validate_directory tests ---

def test_validate_directory_all_ok(tmp_path):
    (tmp_path / "Map_One.mm").write_bytes(b"<map><node/></map>")
    (tmp_path / "Map_Two.mm").write_bytes(b"<?xml version='1.0'?><map/>")
    results = validate_directory(tmp_path, "mm")
    assert results["ok"] == 2
    assert results["bad"] == []

def test_validate_directory_catches_wrong_type(tmp_path):
    (tmp_path / "Good.mm").write_bytes(b"<map><node/></map>")
    (tmp_path / "Bad.mm").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    results = validate_directory(tmp_path, "mm")
    assert results["ok"] == 1
    assert len(results["bad"]) == 1
    assert results["bad"][0]["file"] == "Bad.mm"
    assert results["bad"][0]["detected"] == "png"


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
