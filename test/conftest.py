from typing import List
from _pytest.config import Config
from _pytest.config.argparsing import Parser
import pytest


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Enable integration tests",
    )


def pytest_collection_modifyitems(config: Config, items: List[pytest.Item]) -> None:
    if not config.getoption("--integration"):
        skip_no_int = pytest.mark.skip(reason="Only run when --integration is given")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_no_int)
