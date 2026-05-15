# api/v1/utils/email_utils.py

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

import anyio
from jinja2 import FileSystemLoader, Environment, select_autoescape
from pydantic import EmailStr

from api.v1.models import Email
from api.v1.utils import AppException
from config import env

logger = logging.getLogger(__name__)


async def push_email(req: Email):
    html_body = render_email_template(title=req.title, content=req.content or "")
    await send_email(req.email, req.title, html_body)


async def send_email(recipient: EmailStr, subject: str, body: str):
    def _sync_send():
        try:
            # Port 587 requires SMTP + starttls, NOT SMTP_SSL
            with smtplib.SMTP(env.SMTP_SERVER, env.SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(env.GMAIL_USER, env.GMAIL_APP_PASS)

                msg = MIMEMultipart()
                msg["From"] = formataddr(("Cognexus Management", env.GMAIL_USER))
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "html"))

                server.sendmail(env.GMAIL_USER, recipient, msg.as_string())
                logger.info(f"Email sent to {recipient}")

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP auth failed — check GMAIL_USER and GMAIL_APP_PASS")
            raise AppException("Email authentication failed")

        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection error: {e}")
            raise AppException("Could not connect to email server")

        except OSError as e:
            logger.error(f"Network error during SMTP: {e}")
            raise AppException("Network unreachable — cannot send email")

        except Exception as e:
            logger.error(f"Unexpected email error: {e}")
            raise AppException("Failed to send email")

    await anyio.to_thread.run_sync(_sync_send)


BASE_DIR = Path(__file__).resolve().parents[3]

email_templates = Environment(
    loader=FileSystemLoader(BASE_DIR / "api" / "v1" / "static" / "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_email_template(title: str, content: str) -> str:
    template = email_templates.get_template("email_template.html")
    return template.render(
        title=title,
        content=content or "",
    )
