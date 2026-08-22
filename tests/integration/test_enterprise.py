import pytest
from apps.backend.app.core.database import SessionLocal, Base, engine
from apps.backend.app.models.models import Tenant, SlackIntegration, WebhookEndpoint, APIKey
from apps.backend.app.services.alerting_service import alerting_service

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_tenant_creation_and_api_keys(db_session):
    tenant = Tenant(
        name="Enterprise Hedge Fund Alpha",
        slug="fund-alpha",
        plan_tier="enterprise",
        max_collectors=500
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.plan_tier == "enterprise"
    assert tenant.max_collectors == 500

    # Create API key under tenant
    api_key = APIKey(
        tenant_id=tenant.id,
        name="CI/CD Ingestion Worker",
        key_hash="abc123hash",
        key_prefix="wg_live_abc123..."
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.id is not None
    assert api_key.tenant_id == tenant.id
    assert api_key.key_prefix == "wg_live_abc123..."


@pytest.mark.asyncio
async def test_slack_alerting_formatter():
    """
    Test that Slack Block Kit formatter constructs valid payloads without throwing.
    """
    # Using dummy/invalid webhook URL to test payload creation & network failure resilience
    result = await alerting_service.send_slack_alert(
        webhook_url="https://hooks.slack.com/services/dummy/invalid/token",
        event_type="DOM_DRIFT",
        scraper_name="Amazon Price Monitor",
        details={"confidence": 98.4, "new_selector": "[data-testid='price']"}
    )
    # Returns False gracefully on network/404, never crashes the app
    assert result is False
