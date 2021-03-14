from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import logging
from pathlib import Path
import time
from typing import Any, Dict, Iterator, NamedTuple
from unittest.mock import MagicMock
from outgoing import from_dict
from pydantic import SecretStr
import pytest
from pytest_mock import MockerFixture
import requests
from outgoing_mailgun import MailgunSender

msg = EmailMessage()
msg["Subject"] = "Meet me"
msg["To"] = "my.beloved@love.love"
msg["From"] = "me@here.qq"
msg.set_content(
    "Oh my beloved!\n"
    "\n"
    "Wilt thou dine with me on the morrow?\n"
    "\n"
    "We're having hot pockets.\n"
    "\n"
    "Love, Me\n"
)


@pytest.fixture()
def pacific_timezone(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with monkeypatch.context() as m:
        m.setenv("TZ", "PST8PDT,M3.2.0,M11.1.0")
        time.tzset()
        yield
    time.tzset()


class PostMock(NamedTuple):
    mock: MagicMock
    msg_id: str


@pytest.fixture()
def post_mock(mocker: MockerFixture) -> Iterator[PostMock]:
    msg_id = "20210308184521.1.9AE5400C1FA672B2@example.nil"
    m = mocker.patch.object(
        requests.Session,
        "post",
        **{  # type: ignore[arg-type]
            "return_value.json.return_value": {
                "id": f"<{msg_id}>",
                "message": "Queued. Thank you.",
            }
        },
    )
    yield PostMock(mock=m, msg_id=msg_id)


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


@pytest.mark.usefixtures("pacific_timezone")
def test_mailgun_construct_naive_deliverytime() -> None:
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


@pytest.mark.usefixtures("pacific_timezone")
def test_mailgun_construct_aware_deliverytime() -> None:
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


def test_mailgun_construct_none_deliverytime() -> None:
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


def test_mailgun_auth() -> None:
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "hunter2",
        },
    )
    assert isinstance(sender, MailgunSender)
    with sender:
        assert isinstance(sender._client, requests.Session)
        assert sender._client.auth == ("api", "hunter2")
    assert sender._client is None


@pytest.mark.parametrize(
    "config,data",
    [
        ({}, {}),
        (
            {
                "tags": ["foo"],
                "deliverytime": datetime(
                    2021, 3, 8, 10, 36, 31, tzinfo=timezone(timedelta(hours=-5))
                ),
                "dkim": True,
                "testmode": True,
                "tracking": True,
                "tracking-clicks": True,
                "tracking-opens": True,
                "headers": {
                    "Reply-To": "reply.hole@over.there",
                    "User-Agent": "outgoing-mailgun",
                },
                "variables": {"foo": "bar", "gnusto": "cleesh"},
            },
            {
                "o:tag": ["foo"],
                "o:deliverytime": "Mon, 08 Mar 2021 10:36:31 -0500",
                "o:dkim": "yes",
                "o:testmode": "yes",
                "o:tracking": "yes",
                "o:tracking-clicks": "yes",
                "o:tracking-opens": "yes",
                "h:Reply-To": "reply.hole@over.there",
                "h:User-Agent": "outgoing-mailgun",
                "v:foo": "bar",
                "v:gnusto": "cleesh",
            },
        ),
        (
            {
                "tags": ["foo", "bar"],
                "dkim": False,
                "testmode": False,
                "tracking": False,
                "tracking-clicks": False,
                "tracking-opens": False,
            },
            {
                "o:tag": ["foo", "bar"],
                "o:dkim": "no",
                "o:testmode": "no",
                "o:tracking": "no",
                "o:tracking-clicks": "no",
                "o:tracking-opens": "no",
            },
        ),
        ({"tracking-clicks": "htmlonly"}, {"o:tracking-clicks": "htmlonly"}),
    ],
)
def test_send_payload(
    caplog: pytest.LogCaptureFixture,
    config: Dict[str, Any],
    data: Dict[str, Any],
    post_mock: PostMock,
) -> None:
    caplog.set_level(logging.DEBUG, logger="outgoing_mailgun")
    sender = from_dict(
        {"method": "mailgun", "domain": "example.nil", "api-key": "hunter2", **config}
    )
    with sender as s:
        assert sender is s
        mid = sender.send(msg)
    assert mid == post_mock.msg_id
    post_mock.mock.assert_called_once_with(
        "https://api.mailgun.net/v3/example.nil/messages.mime",
        data={"to": "my.beloved@love.love", **data},
        files={"message": ("message.mime", str(msg))},
    )
    assert caplog.record_tuples == [
        (
            "outgoing_mailgun",
            logging.INFO,
            f"Sending e-mail {msg['Subject']!r} via Mailgun",
        ),
    ]


def test_send_payload_base_url_trailing_slash(post_mock: PostMock) -> None:
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": "example.nil",
            "api-key": "hunter2",
            "base-url": "https://api.eu.mailgun.net/",
        }
    )
    with sender:
        mid = sender.send(msg)
    assert mid == post_mock.msg_id
    post_mock.mock.assert_called_once_with(
        "https://api.eu.mailgun.net/v3/example.nil/messages.mime",
        data={"to": "my.beloved@love.love"},
        files={"message": ("message.mime", str(msg))},
    )


def test_mailgun_send_no_context(post_mock: PostMock) -> None:
    sender = from_dict(
        {"method": "mailgun", "domain": "example.nil", "api-key": "hunter2"}
    )
    mid = sender.send(msg)
    assert mid == post_mock.msg_id
    post_mock.mock.assert_called_once_with(
        "https://api.mailgun.net/v3/example.nil/messages.mime",
        data={"to": "my.beloved@love.love"},
        files={"message": ("message.mime", str(msg))},
    )


def test_mailgun_close_unopened() -> None:
    sender = from_dict(
        {"method": "mailgun", "domain": "example.nil", "api-key": "hunter2"}
    )
    assert isinstance(sender, MailgunSender)
    with pytest.raises(ValueError) as excinfo:
        sender.close()
    assert str(excinfo.value) == "MailgunSender is not open"
