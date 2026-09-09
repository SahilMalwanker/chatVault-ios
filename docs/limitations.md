# Compatibility and limitations

## Validation status

The supplied test suite runs against generated synthetic SQLite backups.
The package has not been executed against the user's real iPhone backup.
The earlier exploratory mapping run is context, not a validation of this
packaged implementation. Cross-platform CI is configured, not yet observed
on GitHub. No certification or universal WhatsApp-version support is claimed.

## Supported input

- Completed, stable, unencrypted Finder/iTunes-style backup directories.
- Manifest.db with Files(fileID, domain, relativePath, flags).
- Supported WhatsApp and WhatsApp Business app-group domains.
- The explicitly checked ZWACHATSESSION / ZWAMESSAGE / ZWAMEDIAITEM columns.
- Hashed subdirectory files, with a flat-layout fallback.

## Deliberate exclusions

- Encrypted backup decryption, Android backups, and iCloud acquisition.
- Backups being written or synced while this program runs.
- Nonempty SQLite WAL/journal recovery; export stops rather than ignoring it.
- Restoring a generated archive into WhatsApp.
- Recovery of deleted data, inaccessible cloud-only attachments, or missing files.
- Full semantic rendering of replies, reactions, payments, polls, group events,
  calls, newsletters, and all schema-specific auxiliary tables.
- Contact-book merging or guaranteed real names for group senders.
- Google Photos API integration, cloud-library comparison, or deletion.
- Near-duplicate recognition and automatic duplicate cleanup.
- Shared content-addressed storage, hardlink deduplication across chats,
  embedded media previews, or audio transcription.

## Important details

All dates are UTC and may be missing or invalid. Original image EXIF is not
modified; filesystem copy timestamps come from the hashed backup files, not
necessarily the original camera date. WebP files are called WebP images, not
automatically labeled stickers. Audio files are not automatically distinguished
as voice notes versus music.

scan and plan currently share the same mapping pipeline; plan is not a second,
more accurate resolver. Both print JSON to stdout and do not create reports.
File reads can update OS access timestamps. Forensic preservation requires
separate acquisition practices beyond this project.

The exact duplicate audit covers every regular file in the supplied directory,
not only photos. Run it on a media-only directory when that is your goal. It
ignores symlink files and reports logical redundant bytes, not guaranteed disk
space recoverable on compressed, sparse, or hardlinked storage.

Memory use grows with the number and size of messages; this prototype loads
chat records and the app manifest index into memory. Path matching is case-
sensitive and conservative. Unknown prefixes, alternate app domains, auxiliary
media stores, and schema changes may remain unresolved.

Verified attachment finalization uses a hard link when supported, with a checked
rename fallback for filesystems such as exFAT. The fallback requires a single
writer and cannot prevent adversarial filesystem races. Test your actual
destination before a large export.

Archive exports contain personal data and are not encrypted by this tool.
