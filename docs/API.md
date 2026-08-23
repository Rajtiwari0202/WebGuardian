# 📡 WebGuardian AI — REST API & Event Stream Reference

All endpoints are hosted by FastAPI at `http://127.0.0.1:8000` (interactive Swagger UI available at `/docs`).

---

## 1. Scrapers & Collectors (`/api/scrapers`)

### `GET /api/scrapers`
Returns all monitored data collectors with live health scores and statuses.

#### Response (`200 OK`):
```json
[
  {
    "id": "sc_7f8a9b",
    "name": "Laptop Price Monitor",
    "target_url": "https://laptops-r-us.com/products",
    "status": "ACTIVE",
    "health_score": 100.0,
    "current_version": 1,
    "last_run": "2026-08-22T10:00:00Z"
  }
]
```

### `POST /api/scrapers`
Registers a new collector with a required semantic schema contract.

#### Request:
```json
{
  "name": "E-Commerce Catalog",
  "target_url": "https://store.example.com",
  "fields": [
    {
      "field": "price",
      "type": "currency",
      "required": true,
      "examples": ["$99.00", "$149.00"]
    }
  ]
}
```

---

## 2. Platform Analytics (`/api/analytics`)

### `GET /api/analytics/dashboard`
Returns executive telemetry and business downtime metrics.

#### Response (`200 OK`):
```json
{
  "active_collectors": 1,
  "overall_health_score": 100.0,
  "active_incidents": 0,
  "auto_healed": 18,
  "downtime_prevented_hours": 18.4,
  "manual_fixes_avoided": 142,
  "avg_recovery_time_seconds": 28,
  "engineering_hours_saved_monthly": 76
}
```

---

## 3. Demo & Chaos Simulation (`/api/demo`)

### `POST /api/demo/trigger-chaos`
Simulates website layout redesign (DOM Drift: `.price` $\rightarrow$ `[data-testid='price']`).

### `POST /api/demo/trigger-timeout-drift`
Simulates proxy latency drop and request timeouts.

### `POST /api/demo/trigger-unsafe-drift`
Simulates an unsafe candidate selector to demonstrate **Validation Sandbox Rejection**.

### `GET /api/demo/incident/{run_id}`
Returns root-cause analysis, old vs new selector diffs, and ranked sandbox candidate audits.

### `GET /api/demo/incident/{run_id}/stream`
**Server-Sent Events (SSE)** endpoint streaming live LangGraph agent execution steps:
```text
data: {"type": "AGENT_STEP", "node": "DETECTION", "message": "Extraction dropped to 0%"}
data: {"type": "AGENT_STEP", "node": "DOM_DRIFT", "message": "DOM structural redesign confirmed"}
data: {"type": "AGENT_STEP", "node": "INTENT_RECOVERY", "message": "Field 'price' requires currency format"}
data: {"type": "AGENT_STEP", "node": "REPAIR_PLANNING", "message": "Generated 3 candidate selectors"}
data: {"type": "AGENT_STEP", "node": "VALIDATION_SANDBOX", "message": "Best candidate: [data-testid='price'] score: 98.4%"}
data: {"type": "AGENT_STEP", "node": "AUTO_DEPLOY", "message": "Collector updated in Scraper Studio"}
data: {"type": "AGENT_STEP", "node": "RECOVERY_RUN", "message": "Pipeline health restored to 100%"}
```

---

## 4. Enterprise Integrations (`/api/integrations`)

### `GET /api/integrations/tenants`
Returns current organization subscription tier (`Scale`) and collector quotas.

### `POST /api/integrations/slack`
Configures an incoming Slack webhook for Block Kit incident cards and test alerts.

### `POST /api/integrations/webhooks`
Registers an external HTTP webhook subscriber for events (`failure.detected`, `repair.completed`).

### `POST /api/integrations/api-keys`
Generates a new developer API key (`wg_live_...`).
