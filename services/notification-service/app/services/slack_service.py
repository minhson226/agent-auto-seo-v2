"""Slack service for sending notifications."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SlackService:
    """Service for sending Slack notifications."""

    async def send_message(
        self,
        text: str,
        webhook_url: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Send a message to Slack via webhook."""
        url = webhook_url or settings.SLACK_WEBHOOK_URL

        if not url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            payload: Dict[str, Any] = {"text": text}

            if blocks:
                payload["blocks"] = blocks

            if attachments:
                payload["attachments"] = attachments

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    logger.info("Slack message sent successfully")
                    return True
                else:
                    logger.error(
                        f"Slack error: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",  # 'info', 'warning', 'error', 'success'
        webhook_url: Optional[str] = None,
    ) -> bool:
        """Send a formatted notification to Slack."""
        color_map = {
            "info": "#3498db",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "success": "#2ecc71",
        }

        color = color_map.get(level, "#3498db")

        attachments = [
            {
                "color": color,
                "title": title,
                "text": message,
                "footer": "Auto-SEO Platform",
            }
        ]

        return await self.send_message(
            text=f"{title}: {message}",
            webhook_url=webhook_url,
            attachments=attachments,
        )


# Global Slack service instance
slack_service = SlackService()
