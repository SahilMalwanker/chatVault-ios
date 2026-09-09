# Security and privacy

ChatVault processes local files. Its runtime performs no network requests,
loads no remote fonts or scripts, and sends no telemetry. Installing dependencies
or running GitHub Actions is a separate network-enabled activity.

## Private data

Never publish real backups, message databases, archives, mapping reports,
contact identifiers, or screenshots of private conversations. Use synthetic
fixtures for issues and demonstrations. GitHub credential scanning is not a
privacy scrubber for chat contents.

## Source-preserving operation

SQLite is opened with mode=ro, immutable=1 and query_only protection. The input
must be a stable, completed backup. Do not run on a directory being written by
Finder, iTunes, another exporter, or a synchronization tool.

Nonempty journal files are rejected rather than silently ignored. Encrypted
backups require separate decryption tooling and are unsupported here.

Attachments are copied to temporary destination files, hashed, and finalized
without overwriting an existing conflicting file. Source files are never
intentionally modified. File reads may update access times depending on the OS.
Do not regard this program as a forensic acquisition tool.

## Export safety

HTML escapes message content and contains no JavaScript. Attachments can still
be malicious documents or executables: inspect them and use trusted viewers.
Exported HTML and JSON contain sensitive information in plain text. Protect the
output disk and avoid placing it in a public web server or public repository.

An export directory should be owned by you and not concurrently edited.
Concurrent writes and adversarial filesystem races are outside this release's
support scope.

## Reporting vulnerabilities

Do not attach real chats or backups. If this repository has GitHub private
vulnerability reporting enabled, use it. Otherwise contact the repository
owner privately before disclosing sensitive details. No maintainer contact
address is fabricated in this template.
