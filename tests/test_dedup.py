from chatvault.dedup import audit, sha256


def test_exact_duplicates_ignore_filename(tmp_path):
    (tmp_path / "first.txt").write_bytes(b"same bytes")
    (tmp_path / "renamed.bin").write_bytes(b"same bytes")
    (tmp_path / "other.txt").write_bytes(b"different bytes")
    before = {p.name: sha256(p) for p in tmp_path.iterdir()}
    report = audit(tmp_path)
    assert report["files_scanned"] == 3
    assert len(report["duplicate_groups"]) == 1
    assert report["redundant_bytes"] == len(b"same bytes")
    assert before == {p.name: sha256(p) for p in tmp_path.iterdir()}


def test_same_name_different_content_not_duplicate(tmp_path):
    for name, content in (("a", b"one"), ("b", b"two")):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "IMG_001.txt").write_bytes(content)
    assert not audit(tmp_path)["duplicate_groups"]
