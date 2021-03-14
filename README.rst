.. image:: http://www.repostatus.org/badges/latest/active.svg
    :target: http://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. image:: https://github.com/jwodder/outgoing-mailgun/workflows/Test/badge.svg?branch=master
    :target: https://github.com/jwodder/outgoing-mailgun/actions?workflow=Test
    :alt: CI Status

.. image:: https://codecov.io/gh/jwodder/outgoing-mailgun/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/outgoing-mailgun

.. image:: https://img.shields.io/pypi/pyversions/outgoing-mailgun.svg
    :target: https://pypi.org/project/outgoing-mailgun/

.. image:: https://img.shields.io/github/license/jwodder/outgoing-mailgun.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/outgoing-mailgun>`_
| `PyPI <https://pypi.org/project/outgoing-mailgun/>`_
| `Issues <https://github.com/jwodder/outgoing-mailgun/issues>`_
| `Changelog <https://github.com/jwodder/outgoing-mailgun/blob/master/CHANGELOG.md>`_

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

    python3 -m pip install outgoing-mailgun


Configuration
=============

When using "mailgun" as the sending method in an ``outgoing`` configuration,
the following configuration fields are recognized:

``base-url`` : HTTP URL (optional)
    The base URL to use for Mailgun API requests.  This should be either
    ``"https://api.mailgun.net"`` (the default) for domains in Mailgun's US
    region or ``"https://api.eu.mailgun.net"`` for domains in Mailgun's EU
    region.  Trailing slashes on the URL are optional.

``domain`` : string (required)
    The domain name you registered with Mailgun for sending e-mail

``api-key`` : password (required)
    A Mailgun API key for your domain; see |the outgoing documentation on
    passwords|_ for ways to write this field.

    .. |the outgoing documentation on passwords|
       replace:: the ``outgoing`` documentation on passwords
    .. _the outgoing documentation on passwords:
       https://outgoing.readthedocs.io/en/latest/configuration.html#passwords

    When using the ``keyring`` password scheme or another scheme that takes
    optional host/service and username fields, if the service and/or username
    is not supplied in the password specifier, then the service defaults to the
    domain name of the ``base-url`` field, and the username defaults to the
    value of the ``domain`` field.

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


Sender-Specific Behavior
========================

The ``MailgunSender`` class provided by this extension is a reentrant__ and
reusable__ context manager, and its ``send()`` method can be called outside of
a context.  In addition, on success, the ``send()`` method returns the message
ID of the newly-sent e-mail (without enclosing angle brackets).

__ https://docs.python.org/3/library/contextlib.html#reentrant-context-managers
__ https://docs.python.org/3/library/contextlib.html#reusable-context-managers
