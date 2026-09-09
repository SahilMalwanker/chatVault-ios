REQUIRED = {
    "ZWACHATSESSION": {"Z_PK", "ZPARTNERNAME", "ZCONTACTJID"},
    "ZWAMESSAGE": {"Z_PK", "ZCHATSESSION", "ZMEDIAITEM", "ZMESSAGEDATE", "ZISFROMME", "ZTEXT", "ZFROMJID", "ZTOJID"},
    "ZWAMEDIAITEM": {"Z_PK", "ZMEDIALOCALPATH"},
}

def validate(conn):
    for table, required in REQUIRED.items():
        columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        missing = required - columns
        if missing:
            raise ValueError(f"Unsupported schema: {table} missing {', '.join(sorted(missing))}")
