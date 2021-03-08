from email.message import EmailMessage
from typing import Dict, List, Union
import pytest
from outgoing_mailgun import extract_recipients, yesno


@pytest.mark.parametrize(
    "b,out",
    [
        (True, "yes"),
        (False, "no"),
        ("htmlonly", "htmlonly"),
    ],
)
def test_yesno(b: Union[bool, str], out: str) -> None:
    assert yesno(b) == out


@pytest.mark.parametrize(
    "headers,addresses",
    [
        ({}, []),
        (
            {"To": "Some User <luser@example.nil>"},
            ["luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>",
                "From": "not-listed@nowhere.nil",
            },
            ["luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>, extra@somewhere.there",
            },
            ["extra@somewhere.there", "luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>",
                "CC": "extra@somewhere.there",
            },
            ["extra@somewhere.there", "luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>",
                "CC": "Some User Again <luser@example.nil>",
            },
            ["luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>",
                "BCC": "extra@somewhere.there",
            },
            ["extra@somewhere.there", "luser@example.nil"],
        ),
        (
            {
                "To": "Some User <luser@example.nil>",
                "CC": "extra@somewhere.there",
                "BCC": "surplus@nowhere.here",
            },
            ["extra@somewhere.there", "luser@example.nil", "surplus@nowhere.here"],
        ),
        (
            {
                "To": (
                    "friends: luser@example.nil, extra@somewhere.there;,"
                    " enemies:loozr@eggsample.null, surplus@nowhere.here;"
                ),
            },
            [
                "extra@somewhere.there",
                "loozr@eggsample.null",
                "luser@example.nil",
                "surplus@nowhere.here",
            ],
        ),
    ],
)
def test_extract_recipients(headers: Dict[str, str], addresses: List[str]) -> None:
    msg = EmailMessage()
    for k, v in headers.items():
        msg[k] = v
    assert extract_recipients(msg) == addresses
