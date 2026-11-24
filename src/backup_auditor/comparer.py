from dataclasses import dataclass, field
from collections import defaultdict

from .scanner import Scan, ensure_hashes


@dataclass
class Comparison:
    new: dict = field(default_factory=dict)
    modified: dict = field(default_factory=dict)
    deleted: dict = field(default_factory=dict)
    moved: list = field(default_factory=list)
    unchanged: dict = field(default_factory=dict)


def compare_scans(local: Scan, backup: Scan, deep: bool = False, mtime_tolerance: float = 2.0) -> Comparison:
    result = Comparison()
    local_paths = set(local.files)
    backup_paths = set(backup.files)

    for path in sorted(local_paths & backup_paths):
        left = local.files[path]
        right = backup.files[path]
        if deep:
            ensure_hashes(local)
            ensure_hashes(backup)
            same = left.sha256 == right.sha256
        else:
            same = left.size == right.size and abs(left.mtime - right.mtime) <= mtime_tolerance
        if same:
            result.unchanged[path] = (left, right)
        else:
            result.modified[path] = (left, right)

    for path in sorted(local_paths - backup_paths):
        result.new[path] = local.files[path]
    for path in sorted(backup_paths - local_paths):
        result.deleted[path] = backup.files[path]

    if not deep:
        return result

    ensure_hashes(local)
    ensure_hashes(backup)
    new_by_hash: dict[str, list[str]] = defaultdict(list)
    deleted_by_hash: dict[str, list[str]] = defaultdict(list)
    for path in result.new:
        new_by_hash[local.files[path].sha256].append(path)
    for path in result.deleted:
        deleted_by_hash[backup.files[path].sha256].append(path)

    matched_deleted: set[str] = set()
    matched_new: set[str] = set()
    for digest, old_paths in deleted_by_hash.items():
        for old_path, new_path in zip(sorted(old_paths), sorted(new_by_hash.get(digest, []))):
            result.moved.append((old_path, new_path))
            matched_deleted.add(old_path)
            matched_new.add(new_path)
    for path in matched_deleted:
        del result.deleted[path]
    for path in matched_new:
        del result.new[path]
    return result
