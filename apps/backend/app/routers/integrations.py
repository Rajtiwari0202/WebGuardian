"""
Enterprise Integrations Router
Manages Multi-Tenancy, Slack Webhooks, Custom Webhook Endpoints, and API Keys.
"""

import uuid
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any

from apps.backend.app.core.database import get_db
from apps.backend.app.models.models import (
    Tenant, TenantMembership, SlackIntegration, WebhookEndpoint, APIKey, User
)
from apps.backend.app.services.alerting_service import alerting_service

logger = logging.getLogger("webguardian.integrations")

router = APIRouter(prefix="/api/integrations", tags=["Enterprise Integrations"])


# --- Schemas ---
class SlackConfigRequest(BaseModel):
    channel_name: str
    webhook_url: str
    team_name: Optional[str] = "Workspace"
    test_dispatch: Optional[bool] = False

class WebhookCreateRequest(BaseModel):
    url: str
    secret: Optional[str] = None
    events: Optional[List[str]] = ["failure.detected", "repair.completed"]

class APIKeyCreateRequest(BaseModel):
    name: str


# --- Multi-Tenant Endpoints ---
@router.get("/tenants")
def get_current_tenant(db: Session = Depends(get_db)):
    """
    Returns current organization/tenant profile and subscription tier.
    """
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(
            name="Acme Data Labs",
            slug="acme-data",
            plan_tier="scale",
            max_collectors=150
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "plan_tier": tenant.plan_tier,
        "max_collectors": tenant.max_collectors,
        "created_at": tenant.created_at
    }


# --- Slack Integration Endpoints ---
@router.get("/slack")
def get_slack_integration(db: Session = Depends(get_db)):
    """
    Retrieves the active Slack integration status.
    """
    slack = db.query(SlackIntegration).filter(SlackIntegration.is_active == 1).first()
    if not slack:
        return {"connected": False}

    return {
        "connected": True,
        "channel_name": slack.channel_name,
        "team_name": slack.team_name,
        "notify_on_failure": bool(slack.notify_on_failure),
        "notify_on_recovery": bool(slack.notify_on_recovery),
        "created_at": slack.created_at
    }


@router.post("/slack")
async def configure_slack_integration(req: SlackConfigRequest, db: Session = Depends(get_db)):
    """
    Connects or updates a Slack Incoming Webhook and optionally sends a test ping.
    """
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(name="Acme Data Labs", slug="acme-data", plan_tier="scale")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    slack = db.query(SlackIntegration).filter(SlackIntegration.tenant_id == tenant.id).first()
    if not slack:
        slack = SlackIntegration(
            tenant_id=tenant.id,
            channel_name=req.channel_name,
            team_name=req.team_name,
            webhook_url=req.webhook_url
        )
        db.add(slack)
    else:
        slack.channel_name = req.channel_name
        slack.team_name = req.team_name
        slack.webhook_url = req.webhook_url
        slack.is_active = 1

    db.commit()

    if req.test_dispatch:
        await alerting_service.send_slack_alert(
            webhook_url=req.webhook_url,
            event_type="TEST_INTEGRATION",
            scraper_name="Laptop Price Monitor",
            details={"confidence": 99.8, "status": "CONNECTED"}
        )

    return {"status": "SUCCESS", "message": f"Slack alert channel #{req.channel_name} connected successfully."}


# --- Custom Webhook Endpoints ---
@router.get("/webhooks")
def list_webhooks(db: Session = Depends(get_db)):
    webhooks = db.query(WebhookEndpoint).all()
    return [
        {
            "id": w.id,
            "url": w.url,
            "events": w.events or [],
            "is_active": bool(w.is_active),
            "created_at": w.created_at
        }
        for w in webhooks
    ]


@router.post("/webhooks")
def create_webhook(req: WebhookCreateRequest, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(name="Acme Data Labs", slug="acme-data", plan_tier="scale")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    webhook = WebhookEndpoint(
        tenant_id=tenant.id,
        url=req.url,
        secret=req.secret,
        events=req.events or ["failure.detected", "repair.completed"]
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return {"status": "SUCCESS", "id": webhook.id, "url": webhook.url}


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)):
    webhook = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()
    return {"status": "SUCCESS", "message": "Webhook deleted"}


# --- API Key Management ---
@router.get("/api-keys")
def list_api_keys(db: Session = Depends(get_db)):
    keys = db.query(APIKey).all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "is_active": bool(k.is_active),
            "created_at": k.created_at,
            "last_used_at": k.last_used_at
        }
        for k in keys
    ]


@router.post("/api-keys")
def create_api_key(req: APIKeyCreateRequest, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(name="Acme Data Labs", slug="acme-data", plan_tier="scale")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    raw_token = f"wg_live_{uuid.uuid4().hex[:24]}"
    prefix = raw_token[:12] + "..."
    key_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    api_key = APIKey(
        tenant_id=tenant.id,
        name=req.name,
        key_hash=key_hash,
        key_prefix=prefix
    )
    db.add(api_key)
    db.commit()

    return {
        "status": "SUCCESS",
        "name": req.name,
        "api_key": raw_token,  # Only shown once
        "key_prefix": prefix
    }
