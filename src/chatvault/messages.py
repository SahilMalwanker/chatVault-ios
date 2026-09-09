from datetime import datetime, timedelta, timezone

EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

def timestamp(value):
    if value is None:
        return None
    try:
        return (EPOCH + timedelta(seconds=float(value))).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None

def load_chats(conn):
    chats = {}
    for row in conn.execute("SELECT Z_PK, ZPARTNERNAME, ZCONTACTJID FROM ZWACHATSESSION ORDER BY Z_PK"):
        chats[row["Z_PK"]] = {
            "id": row["Z_PK"], "name": row["ZPARTNERNAME"] or "Unnamed chat",
            "jid": row["ZCONTACTJID"] or "", "messages": [],
        }
    query = """
        SELECT m.Z_PK AS id, m.ZCHATSESSION AS chat_id, m.ZMEDIAITEM AS media_id,
               m.ZMESSAGEDATE AS raw_date, m.ZISFROMME AS outgoing,
               m.ZTEXT AS text, m.ZFROMJID AS sender, m.ZTOJID AS recipient,
               mi.ZMEDIALOCALPATH AS media_path
        FROM ZWAMESSAGE m LEFT JOIN ZWAMEDIAITEM mi ON mi.Z_PK=m.ZMEDIAITEM
        ORDER BY m.ZMESSAGEDATE, m.Z_PK
    """
    for row in conn.execute(query):
        message = dict(row)
        message["timestamp"] = timestamp(message.pop("raw_date"))
        message["direction"] = "sent" if message.pop("outgoing") else "received"
        key = message["chat_id"]
        if key not in chats:
            chats[key] = {"id": key, "name": "Unassigned conversation", "jid": "", "messages": []}
        chats[key]["messages"].append(message)
    return list(chats.values())
