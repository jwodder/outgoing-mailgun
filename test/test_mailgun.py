from pathlib import Path
from outgoing import from_dict
from pydantic import SecretStr
import pytest
from outgoing_mailgun import MailgunSender


def test_mailgun_construct_basic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MY_API_KEY", "hunter2")
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": {"env": "MY_API_KEY"},
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MailgunSender)
    assert sender.dict() == {
        "configpath": tmp_path / "foo.txt",
        "domain": "example.nil",
        "api_key": SecretStr("hunter2"),
        "tags": [],
        "deliverytime": None,
        "dkim": None,
        "testmode": None,
        "tracking": None,
        "tracking_clicks": None,
        "tracking_opens": None,
        "headers": {},
        "variables": {},
    }
    assert sender._client is None
