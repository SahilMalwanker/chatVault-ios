"""Resolve logical backup paths without writing to the source."""
import plistlib
import sqlite3
from pathlib import Path
from .schema import validate

APPS = {
    "WhatsApp": "AppDomainGroup-group.net.whatsapp.WhatsApp.shared",
    "WhatsApp Business": "AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared",
}

class BackupError(ValueError):
    pass

def connect_readonly(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise BackupError(f"Database not found: {path}")
    for suffix in ("-wal", "-journal"):
        companion = Path(str(path) + suffix)
        if companion.exists() and companion.stat().st_size:
            raise BackupError(f"Active journal requires a separate working snapshot: {companion}")
    # Immutable avoids journal/SHM writes. Input must be a stable, completed backup.
    conn = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn

def normalize(value):
    return str(value or "").replace("\\", "/").removeprefix("./").lstrip("/")

class Backup:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        manifest_plist = self.path / "Manifest.plist"
        if manifest_plist.exists():
            with manifest_plist.open("rb") as stream:
                if plistlib.load(stream).get("IsEncrypted"):
                    raise BackupError("Encrypted backups are not supported. Use a separately decrypted working copy.")
        self.manifest = connect_readonly(self.path / "Manifest.db")

    def close(self):
        self.manifest.close()

    def file(self, file_id):
        if len(file_id) != 40 or any(c not in "0123456789abcdefABCDEF" for c in file_id):
            raise BackupError(f"Invalid backup file ID: {file_id!r}")
        for candidate in (self.path / file_id[:2] / file_id, self.path / file_id):
            if candidate.is_file():
                if not candidate.resolve().is_relative_to(self.path):
                    raise BackupError("Backup file symlink escapes source directory")
                return candidate
        return None

    def index(self, domain):
        return {normalize(r["relativePath"]): r["fileID"] for r in self.manifest.execute(
            "SELECT fileID, relativePath FROM Files WHERE domain=? AND flags=1", (domain,)
        ) if r["relativePath"]}

    def open_app(self, index):
        db_id = index.get("ChatStorage.sqlite")
        if not db_id:
            return None
        db = self.file(db_id)
        if db is None:
            raise BackupError("ChatStorage.sqlite is indexed but its backup file is missing")
        for suffix in ("-wal", "-journal"):
            companion_id = index.get("ChatStorage.sqlite" + suffix)
            companion = self.file(companion_id) if companion_id else None
            if companion_id and companion is None:
                raise BackupError("An indexed ChatStorage journal is missing; incomplete backup")
            if companion and companion.stat().st_size:
                raise BackupError("Hashed ChatStorage journal found. Refusing to ignore uncheckpointed data.")
        conn = connect_readonly(db)
        try:
            validate(conn)
        except Exception:
            conn.close()
            raise
        return conn

    def resolve(self, index, local_path):
        path = normalize(local_path)
        if not path:
            return None, "no_local_path"
        candidates = [path, "Message/" + path]
        if "/Message/" in path:
            candidates.append("Message/" + path.split("/Message/", 1)[1])
        matches = {index[c] for c in candidates if c in index}
        if not matches:
            return None, "path_not_indexed"
        if len(matches) > 1:
            return None, "ambiguous_path"
        file_id = matches.pop()
        return (file_id, "resolved") if self.file(file_id) else (file_id, "indexed_file_missing")
