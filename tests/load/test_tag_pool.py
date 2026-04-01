from pathlib import Path

import pytest

from tests.load.tag_pool import (
    build_random_hex_tag_pool,
    build_sequential_tag_pool,
    read_tag_pool,
    write_tag_pool,
)


def test_build_sequential_tag_pool_uses_shared_prefix_and_width():
    tags = build_sequential_tag_pool(3, prefix="TAG", width=4)

    assert tags == ["TAG0000", "TAG0001", "TAG0002"]


def test_build_random_hex_tag_pool_uses_requested_length():
    tags = build_random_hex_tag_pool(5, length=8)

    assert len(tags) == 5
    assert all(len(tag) == 8 for tag in tags)


def test_write_and_read_tag_pool_roundtrip(tmp_path: Path):
    path = tmp_path / "active_tags.json"
    tags = ["TAG0000", "TAG0001"]

    write_tag_pool(path, tags)

    assert read_tag_pool(path) == tags


def test_read_tag_pool_rejects_empty_list(tmp_path: Path):
    path = tmp_path / "active_tags.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must not be empty"):
        read_tag_pool(path)
