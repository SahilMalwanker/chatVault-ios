import argparse
import json
import sys
from .backup import Backup
from .export import collect, summaries, export_archive
from .dedup import audit

def main(argv=None):
    parser = argparse.ArgumentParser(prog="chatvault", description="Local-first WhatsApp iPhone backup archive")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "plan", "export"):
        command = sub.add_parser(name)
        command.add_argument("--backup", required=True, help="Completed, unencrypted Finder/iTunes backup directory")
        if name == "export":
            command.add_argument("--output", required=True)
            command.add_argument("--format", default="html,json", help="Comma-separated html, json, csv (default: html,json)")
    duplicate = sub.add_parser("audit-duplicates")
    duplicate.add_argument("--input", required=True, help="Local directory; never modified")
    args = parser.parse_args(argv)
    backup = None
    try:
        if args.command == "audit-duplicates":
            result = audit(args.input)
        else:
            backup = Backup(args.backup)
            apps = collect(backup)
            result = summaries(apps)
            if args.command == "export":
                formats = set(args.format.split(","))
                if not formats or not formats <= {"html", "json", "csv"}:
                    raise ValueError("Supported formats: html, json, csv")
                result = export_archive(backup, apps, args.output, formats)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"chatvault: {exc}", file=sys.stderr)
        return 1
    finally:
        if backup:
            backup.close()
