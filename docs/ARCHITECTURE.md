# System Architecture — WebGuardian AI

WebGuardian AI is built as a highly modular monorepo system, separating visual telemetry from background scheduling tasks and AI state machines.

---

## 🏗️ Folder Structure

```text
/
├── apps/
│   ├── frontend/            # Next.js 15 Dark SaaS UI Dashboard
│   ├── backend/             # FastAPI API backend engine
│   ├── worker/              # Background Task Worker (Celery tasks wrapper)
│   └── ai_agent/            # LangGraph Self-Healing Agent Graph
├── docs/                    # Architectural Guides & API Specs
├── tests/                   # Pytest integration tests suites
└── requirements.txt         # Root Python packages definition
```

---

## 🔄 Core Loop Architecture

```text
                           [ SaaS Web Dashboard ]
                                     │
                             (API Requests & Chat)
                                     ▼
                          [ FastAPI Control Plane ]
                                     │
                         (Background Worker Trigger)
                                     ▼
                         [ Scraper Observatory ]
                                     │
                (Drift Audit: Health, Latency, Output Drops)
                                     ▼
                      [ Failure Intelligence Agent ]
                                     │
                 (DOM Diff, Schema Check, Intent Recovery)
                                     ▼
                       [ LangGraph Selector Heals ]
                                     │
                     (Sandbox Validation Candidates)
                                     ▼
                     [ Bright Data Scraper Studio ]
                                     │
                           (Recovered Dataset)
```

---

## 🗄️ Database Design (Entity Relationship)

*   **`User` $\rightarrow$ `Project` $\rightarrow$ `Scraper`**: Root account mapping.
*   **`Scraper` $\rightarrow$ `ExtractionSchema`**: Stores **Semantic Extraction Contracts** defining what elements are wanted (required flags, examples, description metadata) instead of selectors.
*   **`Scraper` $\rightarrow$ `Collector` $\rightarrow$ `CollectorVersion`**: Collector configuration tracking, enabling selector updates, historical version audit logs, and version rollbacks.
*   **`Collector` $\rightarrow$ `CollectorRun`**: Captures scraper runs, execution latencies, status values, and unique Bright Data snapshot IDs.
*   **`Scraper` $\rightarrow$ `FailureEvent` $\rightarrow$ `RepairAttempt` $\rightarrow$ `RepairCandidate`**: Captures scraper drifts, agent states, evaluated strategies, and sandbox scores.
*   **`Scraper` $\rightarrow$ `DriftMetric` / `AuditLog`**: Stores telemetry logs.

---

## 🛡️ Scraper Observatory Health Engine

Evaluates runs using baseline historical logs (averaging the last 10 successful run results):
1.  **Output Drift**: Row counts drop by 30% (Warning) or 80%+ (Critical failure).
2.  **Schema / DOM Drift**: Missing required fields.
3.  **Runtime Drift**: Latency surges exceeding 100%+ baseline thresholds.
4.  **Health Score calculation**:
    $$\text{Health} = 0.35 \times \text{Extraction Quality} + 0.25 \times \text{Success Rate} + 0.15 \times \text{Schema Completeness} + 0.10 \times \text{Latency Score} + 0.15 \times \text{Stability Score}$$

---

## ⚡ Async Execution Queue

WebGuardian deploys a dual-mode background worker queue:
*   **Local mode (Default)**: Uses standard Python `asyncio.Queue` thread loops running concurrently inside the FastAPI uvicorn process. Requires no secondary services or database systems, making it portable and easy to run on Windows.
*   **Celery mode**: Configured inside `apps/worker/tasks.py` to route background execution payloads via Redis queue workers for production scaling.
