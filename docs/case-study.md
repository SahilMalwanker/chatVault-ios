# Origin: from recovered files to conversational context

On September 20, 2026, an exploratory script mapped a completed iPhone backup's
WhatsApp databases to indexed media files. The problem was not finding images
alone: it was recovering which conversations those attachments belonged to.

## Exploratory results

Personal WhatsApp: 34,257 media-linked rows, of which 29,417 resolved to an
existing backup file. WhatsApp Business: 2,086 media-linked rows, of which
2,041 resolved. Combined: 31,458 matched attachment references and 4,885
unresolved references.

These counts describe the earlier exploratory script, not this package's
real-device validation. They are references, not established unique-file
counts. Unresolved paths do not prove the file was deleted. A limited resolver
can miss alternate storage paths.

## Lessons incorporated

- Print a compact summary without limiting the actual export to top chats.
- Export text-only conversations as well as media-rich chats.
- Identify chats by stable keys, not display names alone.
- Separate matched references, unique backup files, and output copies.
- Verify content rather than trusting equal destination sizes.
- Keep media resolution local, transparent, and source-preserving.

No personal chat names, identifiers, source paths, or media are included in
this public case study. The packaged test and demo data are entirely synthetic.
