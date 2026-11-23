import shutil
from pathlib import Path


def sync_folders(local: str | Path, backup: str | Path, comparison, dry_run: bool = True, mirror: bool = False) -> list[str]:
    source = Path(local).expanduser().resolve()
    destination = Path(backup).expanduser().resolve()
    actions: list[str] = []
    if dry_run:
        for path in comparison.new:
            actions.append(f"COPY {path}")
        for path in comparison.modified:
            actions.append(f"COPY {path}")
        if mirror:
            for path in comparison.deleted:
                actions.append(f"DELETE {path}")
        for old, new in comparison.moved:
            actions.append(f"MOVED: copy as {new}; remove {old}")
        return actions

    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(set(comparison.new) | set(comparison.modified)):
        source_path = source / path
        destination_path = destination / path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        actions.append(f"COPY {path}")
    if mirror:
        for path in comparison.deleted:
            target = destination / path
            if target.is_file():
                target.unlink()
                actions.append(f"DELETE {path}")
    for old, new in comparison.moved:
        source_path = source / new
        destination_path = destination / new
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        actions.append(f"COPY moved file {new}")
        if mirror:
            old_target = destination / old
            if old_target.is_file():
                old_target.unlink()
                actions.append(f"DELETE {old}")
    return actions
