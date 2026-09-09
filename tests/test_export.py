from pathlib import Path
import pytest
from chatvault.backup import Backup
from chatvault.export import collect, export_archive, verified_copy
from chatvault.dedup import sha256
from chatvault.cli import main


def snapshot(path):
    return {str(p.relative_to(path)): sha256(p) for p in path.rglob("*") if p.is_file()}


def test_export_all_chats_and_source_unchanged(backup_path, tmp_path):
    before = snapshot(backup_path)
    backup = Backup(backup_path)
    output = tmp_path / "archive"
    try:
        apps = collect(backup)
        result = export_archive(backup, apps, output, {"html", "json"})
        assert result["copy_status"]["copied"] == 4
        assert len(list(output.rglob("chat.html"))) == 8
        assert len(list(output.rglob("chat.json"))) == 8
        rendered = "".join(p.read_text() for p in output.rglob("chat.html"))
        assert "<script>alert" not in rendered
        assert "&lt;script&gt;" in rendered
        assert "Attachment unavailable: path_not_indexed" in rendered
        assert "orphaned message" in rendered
        result = export_archive(backup, collect(backup), output, {"html", "json"})
        assert result["copy_status"]["verified_existing"] == 4
    finally:
        backup.close()
    assert snapshot(backup_path) == before


def test_conflicting_copy_not_overwritten(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"correct")
    target.write_bytes(b"wrong!!")
    with pytest.raises(ValueError, match="conflict"):
        verified_copy(source, target)
    assert target.read_bytes() == b"wrong!!"


def test_source_overlap_refused(backup_path):
    backup = Backup(backup_path)
    try:
        with pytest.raises(ValueError, match="overlap"):
            export_archive(backup, collect(backup), backup_path / "archive", {"html"})
    finally:
        backup.close()


def test_scan_cli(backup_path, capsys):
    assert main(["scan", "--backup", str(backup_path)]) == 0
    assert '"resolved_references": 2' in capsys.readouterr().out


def test_symlink_destination_refused(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_bytes(b"safe")
    target.symlink_to(source)
    with pytest.raises(ValueError, match="symlink"):
        verified_copy(source, target)


def test_csv_formula_cells_neutralized():
    from chatvault.export import spreadsheet_safe
    assert spreadsheet_safe("=SUM(A1:A2)").startswith("'=")
    assert spreadsheet_safe("   @danger").startswith("'")
    assert spreadsheet_safe("ordinary text") == "ordinary text"


def test_portable_copy_fallback(tmp_path, monkeypatch):
    import errno
    import chatvault.export as exporter
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"portable")
    def unavailable(*args, **kwargs):
        raise OSError(errno.EOPNOTSUPP, "hard links unsupported")
    monkeypatch.setattr(exporter.os, "link", unavailable)
    status, digest = verified_copy(source, target)
    assert status == "copied"
    assert target.read_bytes() == b"portable"
    assert digest == sha256(source)
