# 🚀 Monday Morning Onboarding Guide

Welcome to the **WebGuardian AI** engineering codebase. This guide is written so that any software engineer, devops lead, or judge can pull this repository and be fully productive within 5 minutes.

---

## 🧠 1. The 3-Minute Mental Model

```text
       ┌────────────────────────────────────────────────────────┐
       │               BRIGHT DATA SCRAPER STUDIO               │
       │    (Heavy Lifting: Proxies, Unblocking, Execution)     │
       └───────────────────────────┬────────────────────────────┘
                                   │ Raw Dataset Output
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                           WEBGUARDIAN AI                              │
│                                                                       │
│  1. OBSERVATORY (Drift Engine)                                        │
│     Checks: Output Rows == 0? Missing Fields? Latency Surge?          │
│                                                                       │
│  2. DUAL-TIER SELF-HEALING                                            │
│     Tier 1: Fast AST Heuristics (<100ms, $0 cost)                     │
│     Tier 2: LangGraph LLM Agent (Gemini / OpenAI / Mock)              │
│                                                                       │
│  3. VALIDATION SANDBOX                                                │
│     Multi-factor formula: Semantic (30%) + Coverage (30%) + ...       │
│     Gate: If Score >= 90% -> Auto Deploy | Else -> Human Escalate     │
│                                                                       │
│  4. ZERO-DOWNTIME DEPLOYMENT                                          │
│     Updates Bright Data collector config & verifies recovery run.     │
└───────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ 2. 60-Second Quickstart

### Prerequisites
* **Python**: 3.10+ (Recommended: Python 3.12)
* **Node.js**: 18+ (Recommended: Node.js 20+)
* **Git**

### Step 1: Clone Repository
```bash
git clone https://github.com/Rajtiwari0202/WebGuardian.git
cd WebGuardian
```

### Step 2: Start the FastAPI Backend
```bash
# Windows PowerShell
.\venv\Scripts\activate
# Linux / macOS: source venv/bin/activate

# Start server on http://127.0.0.1:8000
python -m uvicorn apps.backend.app.main:app --reload
```

### Step 3: Start the Next.js Frontend
```bash
cd apps/frontend
npm install
npm run dev
```

### Step 4: Open Console
Visit **`http://localhost:3000/dashboard`** in your browser.
* Toggle **Judge Mode** on the top bar to inspect architecture summaries and scenario buttons.
* Click **`DOM Drift`** to trigger an autonomous website redesign self-healing cycle.
* Click **`Settings & Integrations`** to configure Slack alerts and API keys.

---

## 📂 3. Codebase Directory Map

```text
WebGuardian/
├── apps/
│   ├── ai_agent/                 # LangGraph Autonomous Self-Healing Graph
│   │   └── graph.py              # State machine nodes & transition edges
│   │
│   ├── backend/                  # FastAPI Control Plane & Observatory
│   │   ├── app/
│   │   │   ├── core/             # Configuration, Database Session, Settings
│   │   │   ├── models/           # SQLAlchemy 2.0 ORM Models & Multi-Tenancy
│   │   │   ├── routers/          # REST Endpoints (scrapers, demo, analytics, integrations, chat)
│   │   │   └── services/         # Domain Services
│   │   │       ├── fast_heuristic_engine.py  # Tier 1 Fast AST Solver
│   │   │       ├── validation_sandbox.py     # Multi-Factor Candidate Scoring
│   │   │       ├── bright_data.py            # Bright Data API & Mock Simulator
│   │   │       ├── drift_engine.py           # Quality & Output Drift Detector
│   │   │       ├── alerting_service.py       # Slack Block Kit & Webhook Dispatcher
│   │   │       └── llm_provider.py           # Gemini, OpenAI, Mock Factories
│   │   └── main.py               # FastAPI Entrypoint & Middleware
│   │
│   └── frontend/                 # Next.js 15 Dark-Mode SaaS UI (Tailwind CSS)
│       └── src/
│           ├── app/              # App Router (/dashboard, /incidents/[id], /architecture, /settings)
│           └── config/api.ts     # Dynamic Centralized API Base URL
│
├── docs/                         # Architecture, Design Patterns, API Specs
├── tests/
│   ├── unit/                     # Fast Heuristics & Utility Unit Tests
│   └── integration/              # Bright Data, Enterprise, Self-Healing Tests
├── requirements.txt              # Python Dependency Manifest
└── README.md                     # Main Project Documentation
```

---

## 🧪 4. Running Quality Gates & Tests

### Execute Python Backend Test Suite (100% PASS)
```bash
.\venv\Scripts\pytest.exe tests/ -v
```

### Execute Frontend Production Build
```bash
cd apps/frontend
npm run build
```

---

## 🛠️ 5. How to Add a New Feature

### Adding a New Heuristic Repair Pattern
1. Open `apps/backend/app/services/fast_heuristic_engine.py`.
2. Add your pattern template to `COMMON_ATTRIBUTE_PATTERNS` (e.g. `"[data-qa-field='{field}']"`).
3. Run `pytest tests/unit/test_fast_heuristics.py` to verify match accuracy.

### Adding a Custom Outbound Alert Provider
1. Open `apps/backend/app/services/alerting_service.py`.
2. Implement your notification method (e.g. `send_discord_alert` or `send_pagerduty_event`).
3. Wire the dispatcher into `apps/ai_agent/graph.py` inside `deployment_node`.
