"""
outgoing extension for Mailgun

``outgoing-mailgun`` is an extension for outgoing_ that adds the ability to
send e-mails via Mailgun_.  Simply install ``outgoing-mailgun`` alongside
``outgoing``, and you'll be able to specify "mailgun" as a sending method in
your ``outgoing`` configuration.

.. _outgoing: https://github.com/jwodder/outgoing
.. _Mailgun: https://www.mailgun.com

Visit <https://github.com/jwodder/outgoing-mailgun> for more information.
"""

__version__ = "0.2.0"
__author__ = "John Thorvald Wodder II"
__author_email__ = "outgoing-mailgun@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/outgoing-mailgun"

from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime
import logging
import sys
from typing import Any, Dict, List, Optional, Union, cast
from mailbits import recipient_addresses
from outgoing import OpenClosable, Password, Path
from pydantic import Field, HttpUrl, PrivateAttr, parse_obj_as, validator
import requests

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

__all__ = ["MailgunSender"]

log = logging.getLogger(__name__)


class MailgunPassword(Password):
    @staticmethod
    def host(values: Dict[str, Any]) -> str:
        return cast(str, values["base_url"].host)

    username = "domain"


class MailgunSender(OpenClosable):
    configpath: Optional[Path]
    base_url: HttpUrl = Field(
        parse_obj_as(HttpUrl, "https://api.mailgun.net"), alias="base-url"
    )
    domain: str
    api_key: MailgunPassword = Field(alias="api-key")
    tags: List[str] = Field(default_factory=list)
    deliverytime: Optional[datetime]
    dkim: Optional[bool]
    testmode: Optional[bool]
    tracking: Optional[bool]
    tracking_clicks: Optional[Literal[False, True, "htmlonly"]] = Field(
        alias="tracking-clicks"
    )
    tracking_opens: Optional[bool] = Field(alias="tracking-opens")
    headers: Dict[str, str] = Field(default_factory=dict)
    variables: Dict[str, str] = Field(default_factory=dict)
    _client: Optional[requests.Session] = PrivateAttr(None)

    @validator("deliverytime")
    def _make_deliverytime_aware(
        cls, v: Optional[datetime]  # noqa: B902, U100
    ) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            v = v.astimezone()
        return v

    def open(self) -> None:
        self._client = requests.Session()
        self._client.auth = ("api", self.api_key.get_secret_value())

    def close(self) -> None:
        if self._client is None:
            raise ValueError("MailgunSender is not open")
        self._client.close()
        self._client = None

    def send(self, msg: EmailMessage) -> str:
        with self:
            assert self._client is not None
            log.info(
                "Sending e-mail %r via Mailgun", msg.get("Subject", "<NO SUBJECT>")
            )
            data: Dict[str, Union[str, List[str]]]
            data = {"to": ", ".join(recipient_addresses(msg))}
            if self.tags:
                data["o:tag"] = self.tags
            if self.deliverytime is not None:
                data["o:deliverytime"] = format_datetime(self.deliverytime)
            if self.dkim is not None:
                data["o:dkim"] = yesno(self.dkim)
            if self.testmode is not None:
                data["o:testmode"] = yesno(self.testmode)
            if self.tracking is not None:
                data["o:tracking"] = yesno(self.tracking)
            if self.tracking_clicks is not None:
                data["o:tracking-clicks"] = yesno(self.tracking_clicks)
            if self.tracking_opens is not None:
                data["o:tracking-opens"] = yesno(self.tracking_opens)
            for k, v in self.headers.items():
                data[f"h:{k}"] = v
            for k, v in self.variables.items():
                data[f"v:{k}"] = v
            base_url = str(self.base_url).rstrip("/")
            r = self._client.post(
                f"{base_url}/v3/{self.domain}/messages.mime",
                data=data,
                files={"message": ("message.mime", str(msg))},
            )
            r.raise_for_status()
            msg_id = r.json()["id"]
            assert isinstance(msg_id, str)
            return msg_id.strip("<>")


def yesno(b: Union[bool, str]) -> str:
    if isinstance(b, bool):
        return "yes" if b else "no"
    else:
        return b
