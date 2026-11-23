from backup_auditor.ignore import IgnoreRules
from backup_auditor.scanner import scan_folder


def test_scanner_recurses_and_skips_ignored(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "keep.txt").write_text("keep")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "skip.txt").write_text("skip")
    (tmp_path / ".backupignore").write_text("node_modules/\n")

    scan = scan_folder(tmp_path)

    assert set(scan.files) == {"docs/keep.txt"}


def test_ignore_globs(tmp_path):
    rules = IgnoreRules(tmp_path)
    rules.patterns = ["*.tmp", ".git/", "Thumbs.db"]

    assert rules.is_ignored("cache.tmp")
    assert rules.is_ignored(".git/config")
    assert rules.is_ignored("photos/Thumbs.db")
    assert not rules.is_ignored("photos/photo.jpg")
