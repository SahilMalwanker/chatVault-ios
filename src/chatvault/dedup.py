import hashlib
from collections import defaultdict
from pathlib import Path

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def audit(path):
    path = Path(path).expanduser().resolve()
    if not path.is_dir():
        raise ValueError("Duplicate audit input must be a directory")
    sizes = defaultdict(list)
    scanned = 0
    for file in sorted(path.rglob("*")):
        if file.is_file() and not file.is_symlink():
            sizes[file.stat().st_size].append(file)
            scanned += 1
    groups = []
    for size, files in sizes.items():
        if len(files) < 2:
            continue
        hashes = defaultdict(list)
        for file in files:
            hashes[sha256(file)].append(str(file.relative_to(path)))
        for digest, names in hashes.items():
            if len(names) > 1:
                groups.append({"sha256": digest, "bytes_each": size, "files": names,
                               "redundant_bytes": size * (len(names) - 1)})
    return {"files_scanned": scanned, "duplicate_groups": groups,
            "redundant_bytes": sum(g["redundant_bytes"] for g in groups),
            "scope": "Local byte-identical files only; no cloud-library comparison. No files deleted."}
