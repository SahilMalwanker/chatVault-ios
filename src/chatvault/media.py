from pathlib import Path
import re
import unicodedata

EXTENSIONS = {
    "Photos": {".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".tif", ".tiff"},
    "Videos": {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".3gp"},
    "Audio": {".opus", ".ogg", ".m4a", ".mp3", ".aac", ".wav", ".amr"},
    "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".zip"},
}

def category(path):
    suffix = Path(path or "").suffix.lower()
    if suffix == ".webp":
        return "WebP images"
    for name, suffixes in EXTENSIONS.items():
        if suffix in suffixes:
            return name
    return "Other"

def safe_name(value):
    value = unicodedata.normalize("NFKC", str(value))
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-_")
    return value[:64] or "chat"

def chat_folder(chat):
    identity = "none" if chat["id"] is None else str(chat["id"])
    return f"{safe_name(chat['name'])}--chat-{safe_name(identity)}"

def attachment_name(file_id, original):
    suffix = Path(original or "").suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,12}", suffix):
        suffix = ".bin"
    return file_id + suffix
