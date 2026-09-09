import csv
import errno
import html
import io
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from .backup import APPS
from .messages import load_chats
from .media import category, chat_folder, attachment_name
from .dedup import sha256


def collect(backup):
    apps = []
    for name, domain in APPS.items():
        index = backup.index(domain)
        conn = backup.open_app(index)
        if conn is None:
            continue
        try:
            chats = load_chats(conn)
        finally:
            conn.close()
        reasons = Counter()
        categories = Counter()
        unique = set()
        destinations = set()
        output_bytes = 0
        refs = 0
        for chat in chats:
            for message in chat["messages"]:
                if message["media_id"] is None and not message["media_path"]:
                    continue
                refs += 1
                file_id, status = backup.resolve(index, message["media_path"])
                message["attachment"] = {"file_id": file_id, "status": status,
                    "original_path": message["media_path"], "category": category(message["media_path"])}
                reasons[status] += 1
                if status == "resolved":
                    unique.add(file_id)
                    categories[category(message["media_path"])] += 1
                    destination = (chat_folder(chat), category(message["media_path"]), attachment_name(file_id, message["media_path"]))
                    if destination not in destinations:
                        destinations.add(destination)
                        output_bytes += backup.file(file_id).stat().st_size
        apps.append({"name": name, "domain": domain, "chats": chats, "summary": {
            "chats": len(chats), "messages": sum(len(c["messages"]) for c in chats),
            "attachment_references": refs, "resolved_references": reasons["resolved"],
            "unique_resolved_backup_files": len(unique), "planned_attachment_copies": len(destinations),
            "planned_attachment_bytes": output_bytes, "resolution_status": dict(reasons),
            "categories_by_reference": dict(categories),
        }})
    if not apps:
        raise ValueError("No supported WhatsApp ChatStorage.sqlite entries found")
    return apps


def summaries(apps):
    return {"apps": [{"name": a["name"], **a["summary"]} for a in apps],
            "estimated_attachment_bytes": sum(a["summary"]["planned_attachment_bytes"] for a in apps),
            "note": "Estimate excludes HTML/JSON/CSV overhead. References are not unique files."}


def atomic_write(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Refusing symlink destination: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".chatvault-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def verified_copy(source, destination):
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError(f"Refusing symlink destination: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256(source)
    if destination.exists():
        if not destination.is_file() or sha256(destination) != digest:
            raise ValueError(f"Destination content conflict; no overwrite: {destination}")
        return "verified_existing", digest
    fd, name = tempfile.mkstemp(prefix=".chatvault-", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, name)
        if sha256(name) != digest:
            raise IOError(f"Copy verification failed: {destination}")
        # Exclusive final creation prevents overwriting a concurrent destination.
        try:
            os.link(name, destination)
        except OSError as exc:
            unsupported = {errno.EXDEV, errno.EPERM, errno.ENOSYS, errno.EOPNOTSUPP}
            if exc.errno not in unsupported:
                raise
            # Portable fallback for exFAT. Supported only with a single writer.
            if destination.exists() or destination.is_symlink():
                raise ValueError(f"Destination appeared during copy: {destination}") from exc
            os.rename(name, destination)
        return "copied", digest
    finally:
        if os.path.exists(name):
            os.unlink(name)


def render(chat, template):
    entries = []
    for message in chat["messages"]:
        direction = message["direction"]
        sender = "You" if direction == "sent" else (message["sender"] or "Unknown sender")
        content = html.escape(message["text"] or "")
        attachment = message.get("attachment")
        if attachment:
            if attachment.get("href"):
                url = html.escape(quote(attachment["href"], safe="/"), quote=True)
                label = html.escape(Path(attachment["original_path"] or "Attachment").name)
                content += f'<p><a href="{url}">{label}</a></p>'
            else:
                content += '<p class="missing">Attachment unavailable: ' + html.escape(attachment["status"]) + '</p>'
        entries.append(f'<article class="message {direction}"><header>{html.escape(sender)} <time>{html.escape(message["timestamp"] or "Unknown date")}</time></header><div class="body">{content}</div></article>')
    return template.replace("{{TITLE}}", html.escape(chat["name"])).replace("{{MESSAGES}}", "\n".join(entries))


def spreadsheet_safe(value):
    value = "" if value is None else str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def conversation_csv(chat):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["message_id", "timestamp_utc", "direction", "sender", "recipient", "text", "attachment_status", "attachment_path"])
    for message in chat["messages"]:
        attachment = message.get("attachment", {})
        writer.writerow([spreadsheet_safe(value) for value in (
            message["id"], message["timestamp"], message["direction"], message["sender"],
            message["recipient"], message["text"], attachment.get("status"), attachment.get("href"),
        )])
    return stream.getvalue()


def export_archive(backup, apps, output, formats):
    output = Path(output).expanduser().resolve()
    if output.is_relative_to(backup.path) or backup.path.is_relative_to(output):
        raise ValueError("Archive output must not overlap the source backup directory")
    if output.exists() and any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("Archive directory contains symlinks; choose a clean directory")
    output.mkdir(parents=True, exist_ok=True)
    required = sum(a["summary"]["planned_attachment_bytes"] for a in apps)
    if shutil.disk_usage(output).free < required:
        raise ValueError("Insufficient free space for the full planned attachment set (conservative rerun estimate)")
    template = (Path(__file__).parent / "templates" / "conversation.html").read_text(encoding="utf-8")
    inventory = []
    completed = set()
    counts = Counter()
    for app in apps:
        app_dir = output / safe_app(app["name"])
        for chat in app["chats"]:
            directory = app_dir / chat_folder(chat)
            directory.mkdir(parents=True, exist_ok=True)
            for message in chat["messages"]:
                attachment = message.get("attachment")
                if not attachment or attachment["status"] != "resolved":
                    continue
                relative = Path(attachment["category"]) / attachment_name(attachment["file_id"], attachment["original_path"])
                destination = directory / relative
                attachment["href"] = relative.as_posix()
                key = str(destination)
                if key in completed:
                    continue
                status, digest = verified_copy(backup.file(attachment["file_id"]), destination)
                completed.add(key)
                counts[status] += 1
                inventory.append({"app": app["name"], "chat_id": chat["id"],
                    "file_id": attachment["file_id"], "sha256": digest,
                    "destination": destination.relative_to(output).as_posix(), "status": status})
            if "html" in formats:
                atomic_write(directory / "chat.html", render(chat, template))
            if "csv" in formats:
                atomic_write(directory / "chat.csv", conversation_csv(chat))
            if "json" in formats:
                atomic_write(directory / "chat.json", json.dumps(chat, ensure_ascii=False, indent=2))
    atomic_write(output / "inventory.json", json.dumps(inventory, indent=2))
    report = {**summaries(apps), "copy_status": dict(counts), "timestamps": "UTC", "formats": sorted(formats)}
    atomic_write(output / "report.json", json.dumps(report, indent=2))
    links = []
    for app in apps:
        for chat in app["chats"]:
            relative = Path(safe_app(app["name"])) / chat_folder(chat) / ("chat.html" if "html" in formats else ("chat.json" if "json" in formats else "chat.csv"))
            links.append('<li><a href="' + html.escape(quote(relative.as_posix(), safe="/"), quote=True) + '">' + html.escape(app["name"] + " / " + chat["name"]) + '</a></li>')
    atomic_write(output / "index.html", '<!doctype html><meta charset="utf-8"><title>ChatVault archive</title><h1>ChatVault archive</h1><p>Private local export. Dates are UTC.</p><ul>' + "".join(links) + '</ul>')
    return report


def safe_app(name):
    return "WhatsApp-Business" if name == "WhatsApp Business" else "WhatsApp"
