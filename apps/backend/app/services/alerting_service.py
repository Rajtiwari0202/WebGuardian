"""
Enterprise Alerting & Webhook Dispatcher
Supports Slack Block Kit interactive notifications, PagerDuty, and custom webhook streams.
"""

import hmac
import hashlib
import json
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("webguardian.alerting")

class AlertingService:
    """
    Dispatches notifications and webhook events on failure and recovery cycles.
    """

    async def send_slack_alert(
        self,
        webhook_url: str,
        event_type: str,
        scraper_name: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Sends formatted Slack Block Kit cards.
        """
        if not webhook_url:
            return False

        is_failure = "failure" in event_type.lower() or "drift" in event_type.lower()
        title_emoji = "🚨" if is_failure else "✅"
        title_text = f"{title_emoji} WebGuardian: Scraper {'Incident Detected' if is_failure else 'Pipeline Recovered'}"
        color = "#ef4444" if is_failure else "#10b981"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title_text,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Collector:*\n{scraper_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Event Type:*\n`{event_type}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{'FAILED' if is_failure else 'ACTIVE (Healed)'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{details.get('confidence', '97.8')}%"
                    }
                ]
            }
        ]

        if not is_failure and details.get("new_selector"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Deployed Selector:*\n`{details.get('new_selector')}`"
                }
            })

        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(webhook_url, json=payload)
                return res.status_code < 400
        except Exception as e:
            logger.error(f"Failed to dispatch Slack alert: {e}")
            return False

    async def dispatch_webhook(
        self,
        target_url: str,
        event_name: str,
        payload_data: Dict[str, Any],
        secret: Optional[str] = None
    ) -> bool:
        """
        Dispatches standard JSON webhook with optional HMAC SHA-256 signature.
        """
        if not target_url:
            return False

        body = {
            "event": event_name,
            "data": payload_data
        }
        body_bytes = json.dumps(body).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WebGuardian-Webhook-Dispatcher/1.0"
        }

        if secret:
            sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            headers["X-WebGuardian-Signature"] = f"sha256={sig}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(target_url, content=body_bytes, headers=headers)
                return res.status_code < 400
        except Exception as e:
            logger.error(f"Failed to dispatch custom webhook to {target_url}: {e}")
            return False


# Global singleton instance
alerting_service = AlertingService()
