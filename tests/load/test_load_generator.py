from pathlib import Path

from tests.load.load_generator import _build_tag_pool, _persist_tag_pool


def test_build_tag_pool_defaults_to_deterministic_shared_tags():
    tags = _build_tag_pool(
        3,
        tag_prefix="TAG",
        tag_width=4,
        random_tags=False,
    )

    assert tags == ["TAG0000", "TAG0001", "TAG0002"]


def test_build_tag_pool_supports_random_mode():
    tags = _build_tag_pool(
        4,
        tag_prefix="TAG",
        tag_width=4,
        random_tags=True,
    )

    assert len(tags) == 4
    assert all(len(tag) == 6 for tag in tags)


def test_persist_tag_pool_writes_json_file(tmp_path: Path):
    path = tmp_path / "active_tags.json"

    _persist_tag_pool(str(path), ["TAG0000", "TAG0001"])

    assert path.exists()
    assert "TAG0000" in path.read_text(encoding="utf-8")
