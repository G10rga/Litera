"""Outbound email helpers for Litera.

Configured via MAIL_* environment variables. When MAIL_SERVER is unset,
emails are logged and discarded — useful in development and tests.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Send a plain-text (and optional HTML) email. Returns True on success."""
    server = current_app.config.get("MAIL_SERVER")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get(
        "CONTACT_EMAIL"
    )

    if not server or not sender:
        logger.info(
            "MAIL_SERVER unset — email to %s subject=%r not sent:\n%s",
            to,
            subject,
            text_body,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    port = int(current_app.config.get("MAIL_PORT") or 587)
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", True))
    username = current_app.config.get("MAIL_USERNAME") or ""
    password = current_app.config.get("MAIL_PASSWORD") or ""
    timeout = int(current_app.config.get("MAIL_TIMEOUT") or 20)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(server, port, timeout=timeout) as smtp:
            if use_tls:
                smtp.starttls(context=context)
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False

    return True
