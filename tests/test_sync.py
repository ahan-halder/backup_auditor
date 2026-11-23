from backup_auditor.comparer import compare_scans
from backup_auditor.scanner import scan_folder
from backup_auditor.sync import sync_folders


def test_dry_run_does_not_modify(tmp_path):
    local = tmp_path / "local"
    backup = tmp_path / "backup"
    local.mkdir()
    backup.mkdir()
    (local / "new.txt").write_text("new")
    (backup / "deleted.txt").write_text("old")
    comparison = compare_scans(scan_folder(local), scan_folder(backup), deep=True)

    actions = sync_folders(local, backup, comparison, dry_run=True, mirror=False)

    assert actions == ["COPY new.txt"]
    assert not (backup / "new.txt").exists()
    assert (backup / "deleted.txt").exists()


def test_confirm_copies_and_mirror_deletes(tmp_path):
    local = tmp_path / "local"
    backup = tmp_path / "backup"
    local.mkdir()
    backup.mkdir()
    (local / "new.txt").write_text("new")
    (backup / "deleted.txt").write_text("old")
    comparison = compare_scans(scan_folder(local), scan_folder(backup), deep=True)

    sync_folders(local, backup, comparison, dry_run=False, mirror=True)

    assert (backup / "new.txt").read_text() == "new"
    assert not (backup / "deleted.txt").exists()
