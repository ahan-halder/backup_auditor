from backup_auditor.comparer import compare_scans
from backup_auditor.scanner import scan_folder


def test_new_modified_deleted_unchanged(tmp_path):
    local = tmp_path / "local"
    backup = tmp_path / "backup"
    local.mkdir()
    backup.mkdir()
    (local / "same.txt").write_text("same")
    (backup / "same.txt").write_text("same")
    (local / "changed.txt").write_text("local")
    (backup / "changed.txt").write_text("backup")
    (local / "new.txt").write_text("new")
    (backup / "deleted.txt").write_text("deleted")

    result = compare_scans(scan_folder(local), scan_folder(backup), deep=True)

    assert set(result.new) == {"new.txt"}
    assert set(result.modified) == {"changed.txt"}
    assert set(result.deleted) == {"deleted.txt"}
    assert set(result.unchanged) == {"same.txt"}


def test_move_detection(tmp_path):
    local = tmp_path / "local"
    backup = tmp_path / "backup"
    local.mkdir()
    backup.mkdir()
    (local / "notes").mkdir()
    (local / "notes" / "ideas.txt").write_text("ideas")
    (backup / "old-ideas.txt").write_text("ideas")

    result = compare_scans(scan_folder(local), scan_folder(backup), deep=True)

    assert result.moved == [("old-ideas.txt", "notes/ideas.txt")]
    assert not result.new
    assert not result.deleted


def test_fast_comparison_does_not_hash_files(tmp_path):
    local = tmp_path / "local"
    backup = tmp_path / "backup"
    local.mkdir()
    backup.mkdir()
    (local / "new.txt").write_text("new")
    (backup / "old.txt").write_text("old")
    local_scan = scan_folder(local)
    backup_scan = scan_folder(backup)

    result = compare_scans(local_scan, backup_scan, deep=False)

    assert result.moved == []
    assert all(record.sha256 is None for record in local_scan.files.values())
    assert all(record.sha256 is None for record in backup_scan.files.values())
