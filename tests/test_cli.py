from unittest.mock import MagicMock, patch

import pytest

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


def test_cli_dry_run_lists_maps(monkeypatch, capsys):
    monkeypatch.setenv("MINDMEISTER_API_TOKEN", "fake_token")
    mock_map = MagicMock()
    mock_map.id = "42"
    mock_map.title = "Test Map"
    mock_client = MagicMock()
    mock_client.list_maps.return_value = [mock_map]
    with patch("meister_export.cli.MindMeisterClient", return_value=mock_client):
        main(["--dry-run"])
    out = capsys.readouterr().out
    assert "42" in out
    assert "Test Map" in out


def test_cli_token_flag_overrides_env(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("MINDMEISTER_API_TOKEN", raising=False)
    mock_client = MagicMock()
    mock_client.list_maps.return_value = []
    mock_exporter = MagicMock()
    mock_exporter.export_all.return_value = {"ok": [], "skipped": [], "failed": []}
    with patch("meister_export.cli.MindMeisterClient", return_value=mock_client) as mock_cls, \
         patch("meister_export.cli.Exporter", return_value=mock_exporter):
        main(["--token", "my_cli_token", "--output", str(tmp_path)])
    mock_cls.assert_called_once_with("my_cli_token")
