import logging
from pathlib import Path

import pytest

from core.logging_config import setup_logging


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    setup_logging(level=logging.DEBUG)


@pytest.fixture
def static_file(request):
    test_dir = Path(request.fspath).parent
    test_name = request.node.name

    def get_path(filename: str) -> Path:
        test_specific = test_dir / "static" / test_name / filename
        if test_specific.exists():
            return test_specific

        common = test_dir / "static" / filename
        if common.exists():
            return common

        raise FileNotFoundError(
            f"File '{filename}' not found in:\n"
            f"  - {test_specific}\n"
            f"  - {common}"
        )

    return get_path
