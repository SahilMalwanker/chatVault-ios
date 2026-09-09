# Architecture

## Pipeline

1. Read a completed local backup's Manifest.plist and Manifest.db.
2. Resolve app domains and the ChatStorage.sqlite backup file ID dynamically.
3. Validate minimum schema columns and reject known nonempty journals.
4. Load every chat session, including text-only or empty sessions.
5. Join messages to media and preserve messages whose chat session is absent.
6. Resolve logical media paths by conservative exact candidates within the app domain.
7. Produce counts that distinguish references, unique backup files, and output copies.
8. On explicit export, copy and hash-verify attachments and render local conversations.

```text
Manifest.db                         ChatStorage.sqlite
  domain + relativePath                ZWACHATSESSION
          |                                  |
          v                              ZWAMESSAGE
       fileID                                |
          |                              ZWAMEDIAITEM
          v                                  |
   backup/<prefix>/<fileID> <-------- ZMEDIALOCALPATH
          |
          v
   per-chat attachment copies + HTML / JSON / CSV + inventory
```

## Module boundaries

- backup.py: manifest indexes, read-only connections, conservative path resolution.
- schema.py: explicit required-column validation.
- messages.py: messages, chat membership, UTC conversion from the Apple epoch.
- media.py: categories and safe deterministic names.
- dedup.py: local SHA-256 audit using size groups before hashing.
- export.py: planning, verified copies, escaped HTML, JSON, safe CSV, inventory.
- cli.py: command parsing and error reporting.

## Copy semantics

Finalization uses a hard link when supported and a checked rename fallback
otherwise. The fallback assumes no concurrent destination writers.

Destination filenames use complete backup IDs; chat folders append database
chat primary keys. A verified existing attachment is reused on rerun. A
conflicting file is never silently overwritten. Temporary output files are
removed after successful finalization or a caught failure. Hard termination
may leave a .chatvault-* temporary file in the destination; review these
manually before deleting them. Source files are not removed.

HTML/JSON/CSV reports are regenerated on rerun. Existing attachment conflicts
stop the export. This is not a multi-process transactional exporter. Use one
export process per output directory and one backup per archive.

## Storage accounting

An attachment reference is not a unique file. The plan reports both. A single
backup file referenced by different chats can be copied into each chat folder.
Cross-chat content deduplication is not implemented. audit-duplicates reports
potential local redundancy without changing any file.

## HTML behavior

The renderer uses a bundled template with inline CSS, no JavaScript, and no
remote assets. It escapes chat titles and message content. Media is linked,
not transcribed, decoded, or automatically opened. Group sender identifiers
are preserved rather than guessed into contact names.

## SQLite connection references

See [SQLite URI parameters](https://sqlite.org/uri.html) for mode=ro and
immutable=1. Immutable mode assumes the file cannot change; a backup being
modified concurrently is not a valid input.
