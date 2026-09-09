"""Create fake backup data only. Contains no real contacts or messages."""
import argparse
import hashlib
import plistlib
import sqlite3
from pathlib import Path

DOMAINS = (
    "AppDomainGroup-group.net.whatsapp.WhatsApp.shared",
    "AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared",
)

def build_fixture(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "Manifest.db").exists():
        raise ValueError("Refusing to overwrite existing fixture")
    with (directory / "Manifest.plist").open("wb") as stream:
        plistlib.dump({"IsEncrypted": False, "SyntheticFixture": True}, stream)
    manifest = sqlite3.connect(directory / "Manifest.db")
    manifest.execute("CREATE TABLE Files (fileID TEXT PRIMARY KEY, domain TEXT, relativePath TEXT, flags INTEGER)")
    def store(domain, path, content):
        file_id = hashlib.sha1((domain + "-" + path).encode()).hexdigest()
        file = directory / file_id[:2] / file_id
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        manifest.execute("INSERT INTO Files VALUES (?,?,?,1)", (file_id, domain, path))
        return file_id
    for domain in DOMAINS:
        database = directory / "temporary-fixture.sqlite"
        conn = sqlite3.connect(database)
        conn.executescript("""
            CREATE TABLE ZWACHATSESSION (Z_PK INTEGER PRIMARY KEY, ZPARTNERNAME TEXT, ZCONTACTJID TEXT);
            CREATE TABLE ZWAMEDIAITEM (Z_PK INTEGER PRIMARY KEY, ZMEDIALOCALPATH TEXT);
            CREATE TABLE ZWAMESSAGE (Z_PK INTEGER PRIMARY KEY, ZCHATSESSION INTEGER,
                ZMEDIAITEM INTEGER, ZMESSAGEDATE REAL, ZISFROMME INTEGER,
                ZTEXT TEXT, ZFROMJID TEXT, ZTOJID TEXT);
        """)
        conn.executemany("INSERT INTO ZWACHATSESSION VALUES (?,?,?)", [
            (1, "Weekend Crew", "synthetic-group@g.us"),
            (2, "Weekend Crew", "synthetic-other@g.us"),
            (3, "Project Notes", "synthetic-person@s.whatsapp.net"),
        ])
        conn.executemany("INSERT INTO ZWAMEDIAITEM VALUES (?,?)", [
            (1, "Media/first.txt"), (2, "Media/second.txt"),
            (3, "Media/missing.jpg"), (4, None),
        ])
        rows = [
            (1, 1, None, 800000000, 0, "Hello from a synthetic conversation.", "Demo participant", "You"),
            (2, 1, 1, 800000001, 1, "Here is the demo attachment.", "You", "Demo participant"),
            (3, 1, 2, 800000002, 0, "Same bytes, different filename.", "Demo participant", "You"),
            (4, 1, 3, 800000003, 0, "This attachment was deliberately not included.", "Demo participant", "You"),
            (5, 2, None, 800000004, 1, "<script>alert('escaped, not executed')</script>", "You", "Demo participant"),
            (6, 3, 4, 800000005, 1, "Media record without a local file path.", "You", "Demo participant"),
            (7, 999, None, None, 0, "An orphaned message is preserved, not dropped.", "Demo participant", "You"),
        ]
        conn.executemany("INSERT INTO ZWAMESSAGE VALUES (?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        conn.close()
        store(domain, "ChatStorage.sqlite", database.read_bytes())
        database.unlink()
        for path in ("Message/Media/first.txt", "Message/Media/second.txt"):
            store(domain, path, b"Synthetic attachment. No personal data.\n")
    manifest.commit()
    manifest.close()
    return directory

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    print(build_fixture(args.output))
