# Local validation

Date: October 5, 2026
Python: 3.12.8
Environment: hosted execution sandbox; not the user's Mac or GitHub Actions.

## Tests

................                                                         [100%]
16 passed in 0.32s

## CLI smoke tests

scan, plan, export, and audit-duplicates all completed successfully against a
fresh generated synthetic backup. Export produced all eight synthetic chat
folders (four per app), including a text-only session and an orphaned message
bucket, with HTML/JSON/CSV outputs and four attachment copies.

All Python source files were compiled for syntax validation. The source backup
content-invariance assertion is part of the test suite. A simulated unsupported
hard-link filesystem exercised the checked rename fallback; no physical exFAT
drive was tested.

## Not validated

- The user's real iPhone backup.
- Encrypted backups or journal recovery.
- Actual macOS/Windows hardware and external-drive filesystems.
- GitHub Actions runs, installation on a fresh machine, or a published release.
- Google Photos cloud comparison or duplicate prevention.

The bundled docs/demo archive is generated synthetic output, not a personal
backup and not a proof of universal WhatsApp compatibility.
