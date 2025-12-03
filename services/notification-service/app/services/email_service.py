"""Email service for sending notifications."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import aiosmtplib
import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        # Initialize Jinja2 for email templates
        self.template_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """Send an email using SMTP or SendGrid."""
        if settings.SENDGRID_API_KEY:
            return await self._send_via_sendgrid(
                to_email, subject, html_content, text_content, cc, bcc
            )
        else:
            return await self._send_via_smtp(
                to_email, subject, html_content, text_content, cc, bcc
            )

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)

            # Add text part
            if text_content:
                message.attach(MIMEText(text_content, "plain"))

            # Add HTML part
            message.attach(MIMEText(html_content, "html"))

            # Collect all recipients
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_TLS,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """Send email via SendGrid API."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "personalizations": [
                        {
                            "to": [{"email": to_email}],
                            "cc": [{"email": e} for e in cc] if cc else None,
                            "bcc": [{"email": e} for e in bcc] if bcc else None,
                        }
                    ],
                    "from": {
                        "email": settings.SMTP_FROM_EMAIL,
                        "name": settings.SMTP_FROM_NAME,
                    },
                    "subject": subject,
                    "content": [
                        {"type": "text/html", "value": html_content},
                    ],
                }

                if text_content:
                    payload["content"].insert(
                        0, {"type": "text/plain", "value": text_content}
                    )

                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code in [200, 202]:
                    logger.info(f"Email sent via SendGrid to {to_email}")
                    return True
                else:
                    logger.error(
                        f"SendGrid error: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False

    def render_template(self, template_name: str, **context) -> str:
        """Render an email template."""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise


# Global email service instance
email_service = EmailService()
