from functools import lru_cache
from pathlib import Path

_SQL_DIR = Path(__file__).parent / "sql"


@lru_cache(maxsize=None)
def load_sql(name: str) -> str:
    """Load a .sql file by name from the sql/ directory. Cached after first read."""
    path = _SQL_DIR / f"{name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
