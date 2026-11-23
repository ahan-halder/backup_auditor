from backup_auditor.manifest import ManifestStore, manifest_to_scan
from backup_auditor.scanner import scan_folder


def test_save_load_and_latest(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("data")
    scan = scan_folder(source)
    store = ManifestStore(tmp_path / "manifests")

    path = store.save(scan, "test backup")
    payload = store.latest()
    restored = manifest_to_scan(payload)

    assert path.exists()
    assert payload["name"] == "test backup"
    assert set(restored.files) == {"file.txt"}
    assert restored.files["file.txt"].sha256
