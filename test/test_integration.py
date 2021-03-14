from email.message import EmailMessage
import os
from time import sleep, time
from mailbits import recipient_addresses
from outgoing import from_dict
import pytest
import requests
from outgoing_mailgun import MailgunSender


@pytest.mark.integration
def test_mailgun_integration() -> None:
    mailgun_domain = os.environ["MAILGUN_DOMAIN"]
    mailgun_api_key = os.environ["MAILGUN_API_KEY"]
    msg = EmailMessage()
    msg["Subject"] = "This is an integration test."
    # Mailgun requires the recipient addresses to look real, which seems to
    # mean that the TLDs must exist.
    msg["To"] = "no.one@nil.com"
    msg["CC"] = "cee.cee@shining.sea.com"
    msg["BCC"] = "before.cee.cee@ancient.spqr.com"
    msg["From"] = f"me@{mailgun_domain}"
    BODY = (
        'This e-mail is being "sent" as part of a Mailgun integration test.\n'
        "\n"
        "Is is being submitted in test mode, so it should not actually arrive"
        " anywhere.\n"
    )
    msg.set_content(BODY)
    deliverytime = int(time()) + 1800
    sender = from_dict(
        {
            "method": "mailgun",
            "domain": mailgun_domain,
            "api-key": mailgun_api_key,
            "tags": ["outgoing-integration"],
            "deliverytime": deliverytime,
            "testmode": True,
            "headers": {"User-Agent": "outgoing-mailgun"},
            "variables": {"foo": "bar"},
        }
    )
    assert isinstance(sender, MailgunSender)
    with sender:
        msg_id = sender.send(msg)
    recipients = recipient_addresses(msg)
    with requests.Session() as s:
        s.auth = ("api", mailgun_api_key)
        for _ in range(30):
            sleep(1)
            r = s.get(
                f"https://api.mailgun.net/v3/{mailgun_domain}/events",
                params={"message-id": msg_id, "event": "accepted"},
            )
            r.raise_for_status()
            events = r.json()["items"]
            if len(events) >= len(recipients):
                break
        else:
            raise AssertionError("Timed out waiting for events to appear in API")
        assert sorted(e["recipient"] for e in events) == recipients
        for e in events:
            assert e["flags"]["is-test-mode"]
            assert e["message"]["scheduled-for"] == deliverytime
            assert e["tags"] == ["outgoing-integration"]
            assert e["user-variables"] == {"foo": "bar"}
        r = s.get(events[0]["storage"]["url"])
        r.raise_for_status()
        msg_json = r.json()
        assert msg_json["User-Agent"] == "outgoing-mailgun"
        assert msg_json["body-plain"] == BODY
