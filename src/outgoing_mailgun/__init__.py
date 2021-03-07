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

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "outgoing-mailgun@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/outgoing-mailgun"

from datetime import datetime
from email.headerregistry import AddressHeader
from email.message import EmailMessage
from email.utils import format_datetime
import sys
from typing import Any, Dict, List, Optional, Set, Union
from outgoing import OpenClosable, Password, Path
from pydantic import Field, PrivateAttr
import requests

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

__all__ = ["MailgunSender"]


class MailgunPassword(Password):
    @staticmethod
    def host(values: Dict[str, Any]) -> str:
        return "api.mailgun.net"

    username = "domain"


class MailgunSender(OpenClosable):
    configpath: Optional[Path]
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

    def open(self) -> None:
        self._client = requests.Session()
        self._client.auth = ("api", self.api_key.get_secret_value())

    def close(self) -> None:
        if self._client is None:
            raise ValueError("MailgunSender is not open")
        self._client.close()
        self._client = None

    def send(self, msg: EmailMessage) -> None:
        with self:
            assert self._client is not None
            data: Dict[str, Union[str, List[str]]]
            data = {"to": ", ".join(extract_recipients(msg))}
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
            r = self._client.post(
                f"https://api.mailgun.net/v3/{self.domain}/messages.mime",
                data=data,
                files={"message": ("message.mime", str(msg))},
            )
            r.raise_for_status()


def extract_recipients(msg: EmailMessage) -> Set[str]:
    recipients = set()
    for key in ["To", "CC", "BCC"]:
        for header in msg.get_all(key):
            assert isinstance(header, AddressHeader)
            for addr in header.addresses:
                recipients.add(addr.addr_spec)
    return recipients


def yesno(b: Union[bool, str]) -> str:
    if isinstance(b, bool):
        return "yes" if b else "no"
    else:
        return b