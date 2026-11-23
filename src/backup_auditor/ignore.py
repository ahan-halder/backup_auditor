from fnmatch import fnmatch
from pathlib import Path


class IgnoreRules:
    def __init__(self, root: Path):
        self.patterns: list[str] = []
        self.patterns.append(".backupignore")
        ignore_file = root / ".backupignore"
        if ignore_file.is_file():
            for raw in ignore_file.read_text(encoding="utf-8", errors="replace").splitlines():
                pattern = raw.strip()
                if pattern and not pattern.startswith("#"):
                    self.patterns.append(pattern)

    def is_ignored(self, relative_path: str) -> bool:
        parts = relative_path.replace("\\", "/").strip("/").split("/")
        for pattern in self.patterns:
            normalized = pattern.replace("\\", "/").strip("/")
            directory_only = normalized.endswith("/")
            base = normalized.rstrip("/") if directory_only else normalized
            if directory_only:
                if any(fnmatch(part, base) or fnmatch("/".join(parts[:i + 1]), base) for i, part in enumerate(parts)):
                    return True
            elif fnmatch(relative_path.replace("\\", "/"), base):
                return True
            elif fnmatch(Path(relative_path).name, base):
                return True
            elif "/" not in base and any(fnmatch(part, base) for part in parts):
                return True
        return False
