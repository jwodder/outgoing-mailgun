.. image:: http://www.repostatus.org/badges/latest/wip.svg
    :target: http://www.repostatus.org/#wip
    :alt: Project Status: WIP — Initial development is in progress, but there
          has not yet been a stable, usable release suitable for the public.

.. image:: https://github.com/jwodder/outgoing-mailgun/workflows/Test/badge.svg?branch=master
    :target: https://github.com/jwodder/outgoing-mailgun/actions?workflow=Test
    :alt: CI Status

.. image:: https://codecov.io/gh/jwodder/outgoing-mailgun/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/outgoing-mailgun

.. image:: https://img.shields.io/github/license/jwodder/outgoing-mailgun.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/outgoing-mailgun>`_
| `Issues <https://github.com/jwodder/outgoing-mailgun/issues>`_

``outgoing-mailgun`` is an extension for outgoing_ that adds the ability to
send e-mails via Mailgun_.  Simply install ``outgoing-mailgun`` alongside
``outgoing``, and you'll be able to specify "mailgun" as a sending method in
your ``outgoing`` configuration.

.. _outgoing: https://github.com/jwodder/outgoing
.. _Mailgun: https://www.mailgun.com

Installation
============
``outgoing-mailgun`` requires Python 3.6 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``outgoing-mailgun`` and its dependencies (including ``outgoing``)::

    python3 -m pip install https://github.com/jwodder/outgoing-mailgun


Configuration
=============

When using "mailgun" as the sending method in an ``outgoing`` configuration,
the following configuration fields are recognized:

``domain`` : string (required)
    The domain name you registered with Mailgun

``api-key`` : password (required)
    A Mailgun API key for your domain; see |the outgoing documentation on
    passwords|_ for ways to write this field

.. |the outgoing documentation on passwords|
   replace:: the ``outgoing`` documentation on passwords
.. _the outgoing documentation on passwords:
   https://outgoing.readthedocs.io/en/latest/configuration.html#passwords

``base-url`` : HTTP URL (optional)
    The base URL to use for Mailgun API requests.  This should be either
    ``"https://api.mailgun.net"`` (the default) for domains in Mailgun's US
    region or ``"https://api.eu.mailgun.net"`` for domains in Mailgun's EU
    region.  Trailing slashes on the URL are optional.

``tags`` : list of strings (optional)
    A set of tags to apply to sent e-mails

``deliverytime`` : datetime (optional)
    Desired time of delivery for sent e-mails; if no timezone offset is given,
    it is assumed to be in the local system timezone

``dkim`` : boolean (optional)
    Enable/disable DKIM signatures on sent e-mails

``testmode`` : boolean (optional)
    Whether to send in `test mode`_

    .. _test mode: https://documentation.mailgun.com/en/latest/user_manual.html
                   #sending-in-test-mode

``tracking`` : boolean (optional)
    Whether to enable `message tracking`_

    .. _message tracking: https://documentation.mailgun.com/en/latest
                          /user_manual.html#tracking-messages

``tracking-clicks`` : boolean or ``"htmlonly"`` (optional)
    Whether to enable clicks tracking in e-mails

``tracking-opens`` : boolean (optional)
    Whether to enable opens tracking in e-mails

``headers`` : table with string values (optional)
    A collection of custom MIME headers to append to sent e-mails

``variables`` : table with string values (optional)
    A collection of `Mailgun variables`_ to attach to sent e-mails

    .. _Mailgun variables: https://documentation.mailgun.com/en/latest
                           /user_manual.html#attaching-data-to-messages


Example Configuration
=====================

.. code:: toml

    [outgoing]
    method = "mailgun"
    domain = "mydomain.nil"
    api-key = { file = "~/secrets/mailgun.key" }
    dkim = true
    tags = [ "sent-with-outgoing", "my-campaign" ]
    tracking-clicks = "htmlonly"
    headers = { Reply-To = "me@mydomain.nil" }
    variables = { sender = "outgoing", foo = "bar" }
