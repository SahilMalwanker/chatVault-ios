# Publish checklist

1. Run the synthetic demo and tests locally.
2. Test a copy of your completed backup; compare scan/plan results carefully.
3. Preview text-only chats, unnamed chats, same-name chats, media links, and errors.
4. Confirm destination filesystem compatibility and available disk space.
5. Review README claims; label unsupported features and compatibility honestly.
6. Set the license copyright holder to the identity you want to publish under.
7. Inspect staged files for backups, exports, credentials, contact identifiers,
   personal paths, and real screenshots. Never stage private outputs.
8. Create an empty GitHub repository and push the reviewed source tree.
9. Wait for CI before adding a passing-test badge or announcing a tested release.
10. Use the synthetic demo for screenshots and a short scan-plan-export recording.

Suggested repository name: chatvault-ios

Suggested description:
Local-first WhatsApp iPhone backup archives with traceable media mapping,
verified copying, and exact local duplicate audits.

Suggested topics:
python, whatsapp, ios-backup, sqlite, data-portability, privacy,
local-first, digital-archiving

Do not publish the project's origin story with contact names. If you include
aggregate exploratory counts, call them attachment references rather than
unique files and describe the limitations of the original run.
