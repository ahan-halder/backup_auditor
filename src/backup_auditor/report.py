import csv
import html
from pathlib import Path


def print_terminal(comparison, left_label: str, right_label: str, deep: bool):
    sections = [
        ("NEW", len(comparison.new)),
        ("MODIFIED", len(comparison.modified)),
        ("DELETED", len(comparison.deleted)),
        ("MOVED", len(comparison.moved)),
        ("UNCHANGED", len(comparison.unchanged)),
    ]
    print(f"\nBackup Audit: {left_label} vs {right_label}")
    print(f"Mode: {'deep (SHA-256)' if deep else 'fast (size + mtime)'}\n")
    for name, count in sections:
        print(f"{name:<10} {count:>6}")
    print()
    for name, items in (
        ("NEW", sorted(comparison.new)),
        ("MODIFIED", sorted(comparison.modified)),
        ("DELETED", sorted(comparison.deleted)),
    ):
        if items:
            print(name)
            for path in items:
                print(f"  {'+' if name == 'NEW' else '~' if name == 'MODIFIED' else '-'} {path}")
    if comparison.moved:
        print("MOVED")
        for old, new in comparison.moved:
            print(f"  > {old} -> {new}")


def export_report(comparison, destination: str, report_format: str | None = None):
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    format_name = (report_format or path.suffix.lstrip(".")).lower()
    rows = []
    for status, mapping in (
        ("NEW", comparison.new),
        ("MODIFIED", comparison.modified),
        ("DELETED", comparison.deleted),
        ("UNCHANGED", comparison.unchanged),
    ):
        if isinstance(mapping, dict):
            rows.extend((status, path_name) for path_name in mapping)
    rows.extend(("MOVED", f"{old} -> {new}") for old, new in comparison.moved)

    if format_name == "csv":
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["status", "path"])
            writer.writerows(rows)
    elif format_name == "html":
        body = "\n".join(
            f"<tr><td>{html.escape(status)}</td><td>{html.escape(path_name)}</td></tr>"
            for status, path_name in rows
        )
        path.write_text(
            "<html><body><h1>Backup Audit Report</h1><table><tr><th>Status</th><th>Path</th></tr>"
            + body
            + "</table></body></html>",
            encoding="utf-8",
        )
    elif format_name in ("md", "markdown"):
        lines = ["# Backup Audit Report", "", "| Status | Path |", "|---|---|"]
        lines.extend(f"| {status} | {path_name.replace('|', '\\|')} |" for status, path_name in rows)
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        raise ValueError("Report format must be html, csv, or md")
