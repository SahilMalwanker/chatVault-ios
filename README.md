# ChatVault

Turn opaque iPhone backups into readable, organized WhatsApp archives.

ChatVault reconstructs conversations and their attachments from completed local
iPhone backups. Inspect the mapping before exporting, preserve text-only chats,
and keep a traceable archive without intentionally modifying the source files.

Version 0.1.0 is a runnable prototype with synthetic regression tests. It is not
yet validated against a real-device backup or every WhatsApp schema.

## Why this exists

A flat folder of recovered photos and videos loses the conversations they
belonged to. ChatVault restores that context and makes incomplete mappings and
exact local duplicates visible, rather than hiding them behind a success count.

## What works

- Discover personal WhatsApp and WhatsApp Business databases through Manifest.db.
- Preserve all chat sessions and orphaned messages; no top-25 export limit.
- Print scan and export-plan JSON without creating output files.
- Export escaped HTML, structured JSON, and optional spreadsheet-safe CSV.
- Organize attachments by chat with stable chat IDs and complete backup file IDs.
- Hash-verify copies, reject conflicts, and reuse verified files on rerun.
- Report unresolved paths explicitly and distinguish references from unique files.
- Audit local exact duplicates using SHA-256 without deleting anything.

This is not a WhatsApp restore tool or Google Photos duplicate remover.

## Quick start

Python 3.10 or newer is required. Runtime uses the Python standard library.
From the repository directory:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .

chatvault scan --backup "/path/to/completed/backup"
chatvault plan --backup "/path/to/completed/backup"
chatvault export --backup "/path/to/completed/backup" \
  --output "/path/to/archive" --format html,json,csv
```

Choose an output directory outside the backup. Verified copies use hard-link
finalization where supported and a checked rename fallback for formats such as
exFAT. Use only one writer and test your external drive first. See
[limitations](docs/limitations.md).
Do not run against a backup in progress. Encrypted backups and active journals
are rejected. Always test a working copy before a large export.

Export is an explicit writing operation. scan and plan only read the input and
print to the terminal. To save a plan, redirect stdout outside the backup:

```bash
chatvault plan --backup "/path/to/backup" > plan.json
```

## Try the synthetic demo

The fixture generator contains no personal data:

```bash
python tests/fixtures/synthetic_backup/build_fixture.py demo-backup
chatvault scan --backup demo-backup
chatvault export --backup demo-backup --output demo-archive --format html,json,csv
chatvault audit-duplicates --input demo-archive
```

Open demo-archive/index.html locally. A generated synthetic archive is also
bundled under docs/demo for an immediate preview. Never use private conversations
in public screenshots.

The duplicate audit checks all regular files under its input. Use a media-only
folder for a photo-focused audit. Identical filenames do not establish identical
content, and this command does not inspect Google Photos.

## Archive layout

```text
archive/
├── index.html
├── inventory.json
├── report.json
├── WhatsApp/
│   └── Weekend-Crew--chat-1/
│       ├── chat.html
│       ├── chat.json
│       ├── chat.csv
│       └── Documents/
│           └── <complete-backup-file-id>.txt
└── WhatsApp-Business/
    └── ...
```

HTML links to local attachments. Messages retain UTC dates, direction, sender
and recipient identifiers, text, and available media associations. Specialized
message semantics and full auxiliary database contents are not exported.

Rerunning an export regenerates conversation reports and verifies existing
attachment contents. A conflicting attachment aborts rather than being silently
overwritten. Keep one source backup per output directory.

## Engineering notes

Read the [architecture](docs/architecture.md),
[compatibility limits](docs/limitations.md),
[security guidance](SECURITY.md), and [publish checklist](docs/publishing.md).
The [pipeline illustration](docs/images/architecture.svg) is synthetic.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m build
```

GitHub Actions is configured for Python 3.10, 3.12, and 3.13 on Linux, macOS,
and Windows. This configuration is not a claim that those jobs have run yet.

## Roadmap

- Validate against independently consented real-device backups.
- Broader path and schema adapters with explicit version coverage.
- Stronger interrupted-export recovery and concurrent-write protection.
- More complete replies, reactions, and group-event rendering.
- Optional shared content-addressed attachment storage.
- Streaming large conversation exports and richer local media previews.

## Related work

WhatsApp extraction is an established area. See
[WhatsApp Chat Exporter](https://github.com/KnugiHK/WhatsApp-Chat-Exporter)
for broader Android/iOS parsing and export capabilities. ChatVault is an
independently written, narrower prototype focused on preview-first mapping,
verified source-preserving exports, and local duplicate visibility.
No code was copied from that project in this generated implementation.

## Privacy and license

Do not commit real backups or generated private archives. The bundled demo is
synthetic. MIT licensed; inspect LICENSE before publishing under your identity.
