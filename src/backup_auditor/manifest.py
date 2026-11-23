import json
from datetime import datetime, timezone
from pathlib import Path

from .scanner import Scan, records_as_dict
from .scanner import ensure_hashes


class ManifestStore:
    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory).expanduser() if directory else Path.home() / ".backup_auditor" / "manifests"
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, scan: Scan, name: str) -> Path:
        ensure_hashes(scan)
        safe_name = "".join(ch if ch.isalnum() or ch in "-_. " else "_" for ch in name).strip() or "snapshot"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{stamp}-{safe_name}.json"
        payload = {
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "root": scan.root,
            "files": records_as_dict(scan)["files"],
        }
        path = self.directory / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (self.directory / "latest.json").write_text(json.dumps({"path": str(path)}), encoding="utf-8")
        return path

    def latest(self) -> dict:
        pointer = self.directory / "latest.json"
        if not pointer.exists():
            raise FileNotFoundError("No saved snapshots found")
        path = Path(json.loads(pointer.read_text(encoding="utf-8"))["path"])
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict]:
        items = []
        for path in sorted(self.directory.glob("*.json"), reverse=True):
            if path.name == "latest.json":
                continue
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")) | {"path": str(path)})
            except json.JSONDecodeError:
                continue
        return items


def manifest_to_scan(payload: dict) -> Scan:
    from .scanner import FileRecord, Scan
    files = {
        path: FileRecord(
            relative_path=data["relative_path"],
            size=data["size"],
            mtime=data["mtime"],
            sha256=data.get("sha256"),
        )
        for path, data in payload["files"].items()
    }
    return Scan(payload["root"], files)
