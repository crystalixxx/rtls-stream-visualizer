from __future__ import annotations

import json
import random
from pathlib import Path


def build_sequential_tag_pool(
    count: int,
    *,
    prefix: str = "TAG",
    width: int = 4,
    start: int = 0,
) -> list[str]:
    if count < 1:
        raise ValueError("count must be >= 1")
    if width < 1:
        raise ValueError("width must be >= 1")
    return [f"{prefix}{index:0{width}d}" for index in range(start, start + count)]


def build_random_hex_tag_pool(count: int, *, length: int = 6) -> list[str]:
    if count < 1:
        raise ValueError("count must be >= 1")
    if length < 1:
        raise ValueError("length must be >= 1")
    return ["".join(random.choices("0123456789ABCDEF", k=length)) for _ in range(count)]


def write_tag_pool(path: str | Path, tags: list[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(tags, ensure_ascii=True, indent=2), encoding="utf-8")


def read_tag_pool(path: str | Path) -> list[str]:
    target = Path(path)
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError("tag pool file must contain a JSON array of strings")
    if not data:
        raise ValueError("tag pool file must not be empty")
    return data
