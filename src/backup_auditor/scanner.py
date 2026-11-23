from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .hasher import sha256_file
from .ignore import IgnoreRules


@dataclass
class FileRecord:
    relative_path: str
    size: int
    mtime: float
    sha256: str | None = None


@dataclass
class Scan:
    root: str
    files: dict[str, FileRecord]


def scan_folder(root: str | Path, deep: bool = False) -> Scan:
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a folder: {root_path}")
    ignore = IgnoreRules(root_path)
    files: dict[str, FileRecord] = {}
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root_path).as_posix()
        if ignore.is_ignored(relative):
            continue
        stat = path.stat()
        record = FileRecord(relative, stat.st_size, stat.st_mtime)
        if deep:
            record.sha256 = sha256_file(path)
        files[relative] = record
    return Scan(str(root_path), files)


def ensure_hashes(scan: Scan) -> None:
    root = Path(scan.root)
    for record in scan.files.values():
        if record.sha256 is None:
            record.sha256 = sha256_file(root / record.relative_path)


def records_as_dict(scan: Scan) -> dict:
    return {
        "root": scan.root,
        "files": {path: asdict(record) for path, record in scan.files.items()},
    }
