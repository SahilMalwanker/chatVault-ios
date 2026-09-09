import plistlib
import sqlite3
import pytest
from chatvault.backup import Backup, BackupError, APPS
from chatvault.export import collect
from chatvault.messages import timestamp
from chatvault.media import chat_folder


def test_maps_both_apps_and_all_chats(backup_path):
    backup = Backup(backup_path)
    try:
        apps = collect(backup)
        assert len(apps) == 2
        for app in apps:
            assert app["summary"]["chats"] == 4
            assert app["summary"]["messages"] == 7
            assert app["summary"]["attachment_references"] == 4
            assert app["summary"]["resolved_references"] == 2
            assert app["summary"]["unique_resolved_backup_files"] == 2
            assert app["summary"]["resolution_status"]["path_not_indexed"] == 1
            assert app["summary"]["resolution_status"]["no_local_path"] == 1
    finally:
        backup.close()


def test_duplicate_chat_names_have_distinct_folders():
    assert chat_folder({"id": 1, "name": "Same"}) != chat_folder({"id": 2, "name": "Same"})


def test_read_only_connection(backup_path):
    backup = Backup(backup_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            backup.manifest.execute("DELETE FROM Files")
    finally:
        backup.close()


def test_encrypted_backup_rejected(backup_path):
    with (backup_path / "Manifest.plist").open("wb") as stream:
        plistlib.dump({"IsEncrypted": True}, stream)
    with pytest.raises(BackupError, match="Encrypted"):
        Backup(backup_path)


def test_hashed_wal_rejected(backup_path):
    manifest = sqlite3.connect(backup_path / "Manifest.db")
    file_id = "a" * 40
    file = backup_path / "aa" / file_id
    file.parent.mkdir(exist_ok=True)
    file.write_bytes(b"uncheckpointed journal")
    manifest.execute("INSERT INTO Files VALUES (?,?,?,1)", (file_id, APPS["WhatsApp"], "ChatStorage.sqlite-wal"))
    manifest.commit()
    manifest.close()
    backup = Backup(backup_path)
    try:
        with pytest.raises(BackupError, match="journal"):
            collect(backup)
    finally:
        backup.close()


def test_timestamp_is_utc():
    assert timestamp(0) == "2001-01-01T00:00:00+00:00"
    assert timestamp(None) is None


def test_unsupported_schema_rejected(backup_path):
    backup = Backup(backup_path)
    index = backup.index(APPS["WhatsApp"])
    database = backup.file(index["ChatStorage.sqlite"])
    backup.close()
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE ZWAMESSAGE")
    connection.commit()
    connection.close()
    backup = Backup(backup_path)
    try:
        with pytest.raises(ValueError, match="Unsupported schema"):
            collect(backup)
    finally:
        backup.close()
