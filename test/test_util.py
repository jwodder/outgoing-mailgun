from __future__ import annotations
import pytest
from outgoing_mailgun import yesno


@pytest.mark.parametrize(
    "b,out",
    [
        (True, "yes"),
        (False, "no"),
        ("htmlonly", "htmlonly"),
    ],
)
def test_yesno(b: bool | str, out: str) -> None:
    assert yesno(b) == out
