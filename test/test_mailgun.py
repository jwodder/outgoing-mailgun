from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from typing import Iterator
from outgoing import from_dict
from pydantic import SecretStr
import pytest
from pytest_mock import MockerFixture
from outgoing_mailgun import MailgunSender


@pytest.fixture()
def pacific_timezone(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with monkeypatch.context() as m:
        m.setenv("TZ", "PST8PDT,M3.2.0,M11.1.0")
        time.tzset()
        yield
    time.tzset()


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
        "base_url": "https://api.mailgun.net",
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


def test_mailgun_construct_api_key_lookup(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "sentinel",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MailgunSender)
    assert sender.api_key == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host="api.mailgun.net",
        username="example.nil",
        configpath=tmp_path / "foo.txt",
    )


def test_mailgun_construct_api_key_lookup_custom_base_url(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    m = mocker.patch("outgoing.core.resolve_password", return_value="12345")
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "base-url": "https://api.eu.mailgun.net/",
            "api-key": "sentinel",
        },
        configpath=str(tmp_path / "foo.txt"),
    )
    assert isinstance(sender, MailgunSender)
    assert sender.api_key == SecretStr("12345")
    m.assert_called_once_with(
        "sentinel",
        host="api.eu.mailgun.net",
        username="example.nil",
        configpath=tmp_path / "foo.txt",
    )


def test_mailgun_construct_naive_deliverytime(pacific_timezone: None) -> None:
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "hunter2",
            "deliverytime": "2021-02-07 16:48:27",
        }
    )
    assert isinstance(sender, MailgunSender)
    assert sender.deliverytime == datetime(
        2021, 2, 7, 16, 48, 27, tzinfo=timezone(timedelta(hours=-8))
    )


def test_mailgun_construct_aware_deliverytime(pacific_timezone: None) -> None:
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "hunter2",
            "deliverytime": "2021-02-07 16:48:27-05:00",
        }
    )
    assert isinstance(sender, MailgunSender)
    assert sender.deliverytime == datetime(
        2021, 2, 7, 16, 48, 27, tzinfo=timezone(timedelta(hours=-5))
    )


def test_mailgun_construct_none_deliverytime(pacific_timezone: None) -> None:
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "hunter2",
            "deliverytime": None,
        }
    )
    assert isinstance(sender, MailgunSender)
    assert sender.deliverytime is None
