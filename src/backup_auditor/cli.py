import argparse
import sys

from .comparer import compare_scans
from .manifest import ManifestStore, manifest_to_scan
from .report import export_report, print_terminal
from .scanner import scan_folder
from .sync import sync_folders


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backup_auditor", description="Compare and safely sync folders")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="Compare a local folder to a backup or snapshot")
    audit.add_argument("local")
    audit.add_argument("backup", nargs="?")
    audit.add_argument("--deep", action="store_true")
    audit.add_argument("--against-last-snapshot", action="store_true")
    audit.add_argument("--report")

    snapshot = sub.add_parser("snapshot", help="Save a local folder snapshot")
    snapshot.add_argument("local")
    snapshot.add_argument("--name", default="snapshot")
    snapshot.add_argument("--deep", action="store_true")

    sub.add_parser("history", help="List saved snapshots")

    duplicates = sub.add_parser("duplicates", help="Find duplicate files")
    duplicates.add_argument("folder")

    integrity = sub.add_parser("integrity", help="Re-check backup files against a snapshot")
    integrity.add_argument("backup")
    integrity.add_argument("--manifest")

    sync = sub.add_parser("sync", help="Copy new or modified files")
    sync.add_argument("local")
    sync.add_argument("backup")
    sync.add_argument("--deep", action="store_true")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--confirm", action="store_true")
    sync.add_argument("--mirror", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            scan = scan_folder(args.local, deep=args.deep)
            path = ManifestStore().save(scan, args.name)
            print(f"Saved snapshot: {path}")
            return 0

        if args.command == "history":
            items = ManifestStore().list()
            if not items:
                print("No snapshots found")
            for item in items:
                print(f"{item['created_at']}  {item['name']}  {item['path']}")
            return 0

        if args.command == "duplicates":
            scan = scan_folder(args.folder, deep=True)
            seen: dict[str, list[str]] = {}
            for path, record in scan.files.items():
                seen.setdefault(record.sha256 or "", []).append(path)
            found = False
            for digest, paths in seen.items():
                if len(paths) > 1:
                    found = True
                    print(digest)
                    for path in paths:
                        print(f"  {path}")
            if not found:
                print("No duplicates found")
            return 0

        if args.command == "integrity":
            store = ManifestStore()
            payload = store.latest()
            if args.manifest:
                import json
                manifest_path = __import__("pathlib").Path(args.manifest)
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = manifest_to_scan(payload)
            actual = scan_folder(args.backup, deep=True)
            mismatched = []
            missing = []
            for path, record in expected.files.items():
                if path not in actual.files:
                    missing.append(path)
                elif actual.files[path].sha256 != record.sha256:
                    mismatched.append(path)
            if missing:
                print("MISSING")
                print("\n".join(f"  - {path}" for path in missing))
            if mismatched:
                print("CORRUPTED")
                print("\n".join(f"  ~ {path}" for path in mismatched))
            if not missing and not mismatched:
                print("Integrity check passed")
            return 1 if missing or mismatched else 0

        local = scan_folder(args.local, deep=args.deep)
        if args.command == "audit" and args.against_last_snapshot:
            backup = manifest_to_scan(ManifestStore().latest())
        elif args.backup:
            backup = scan_folder(args.backup, deep=args.deep)
        else:
            raise ValueError("Provide a backup folder or --against-last-snapshot")
        comparison = compare_scans(local, backup, deep=args.deep)

        if args.command == "audit":
            print_terminal(comparison, args.local, backup.root, args.deep)
            if args.report:
                export_report(comparison, args.report)
                print(f"\nReport saved: {args.report}")
        elif args.command == "sync":
            dry_run = not args.confirm
            if args.mirror and dry_run:
                raise ValueError("Mirror requires --confirm; sync never deletes in dry-run mode")
            actions = sync_folders(args.local, args.backup, comparison, dry_run=dry_run, mirror=args.mirror)
            print("\n".join(actions) if actions else "No changes")
            if dry_run:
                print("\nDry run only. Use --confirm to apply.")
        return 0
    except (ValueError, FileNotFoundError, NotADirectoryError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
