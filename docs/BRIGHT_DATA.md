# Bright Data Scraper Studio Integration Guide

WebGuardian AI is designed to wrap around **Bright Data Scraper Studio**, acting as the autonomous intelligence, monitoring, and self-healing control plane.

---

## 🤝 Division of Labor

```text
┌────────────────────────────────────────┐
│             WEBGUARDIAN AI             │
│  (Intelligence & Observability Layer)  │
│  - Monitors data & structural drift    │
│  - LangGraph self-healing agent        │
│  - Sandbox validation of selectors     │
│  - Version history & rollback audits   │
└───────────────────┬────────────────────┘
                    │
                    ▼  (Trigger Run / Deploy Code)
┌────────────────────────────────────────┐
│       BRIGHT DATA SCRAPER STUDIO       │
│      (Collection Infrastructure)       │
│  - Fully managed browser execution     │
│  - Residential proxies & unblocking    │
│  - High-scale concurrent runs          │
│  - Structured CSV/JSON data delivery   │
└────────────────────────────────────────┘
```

*   **Bright Data** handles the heavy lifting of the collection fabric: rotating proxies, rendering JS-heavy sites, bypassing CAPTCHAs, scheduling tasks, and storing dataset results.
*   **WebGuardian AI** ensures the scraping pipeline remains unbroken. It watches the quality of output, triages structural anomalies, generates healed selector candidates, tests them in isolated sandboxes, and automatically bumps code versions inside Scraper Studio.

---

## 🗄️ Database Schemas (decoupled versioned control plane)

To prevent code conflicts and trace collection runs, WebGuardian decouples scraper configs into three version control tables:

1.  **`Collector`**: Maps a WebGuardian scraper to its target Scraper Studio Published Collector ID (e.g., `c_laptop_monitor_812`).
2.  **`CollectorVersion`**: Stores version configurations (e.g., active CSS selectors logic, version index, and deployment reason audit text).
3.  **`CollectorRun`**: Tracks Bright Data job executions, referencing unique `snapshot_id` values, status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), data sizes, and latencies.

---

## 🔌 API Mappings

`RealBrightDataService` communicates directly with Bright Data's Web Scraper / DCA API endpoints:

### 1. Trigger Scraper Collection Job
*   **HTTP POST**: `https://api.brightdata.com/dca/trigger?collector={bright_data_id}`
*   **Auth**: `Authorization: Bearer {BRIGHT_DATA_API_KEY}`
*   **Request Body**: `[{"url": "https://target-website.com/products"}]`
*   **Returns**: `{"snapshot_id": "s_xxxxxx"}`

### 2. Poll progress
*   **HTTP GET**: `https://api.brightdata.com/datasets/v3/progress/{snapshot_id}`
*   **Returns**:
    ```json
    {
      "snapshot_id": "s_xxxxxx",
      "status": "running" | "ready" | "failed",
      "progress": 100
    }
    ```

### 3. Fetch structured datasets
*   **HTTP GET**: `https://api.brightdata.com/dca/dataset?id={snapshot_id}`
*   **Returns**: JSON Array of extracted objects matching target configurations.

### 4. Deploy healed selectors configuration
*   **HTTP POST**: `https://api.brightdata.com/scrapers/update`
*   **Returns**: Confirmation success details.

---

## ⚡ Asynchronous Event Cycle

WebGuardian processes runs asynchronously via background workers, preventing API request blocking:
1.  **Trigger**: API initiates a run, adding a `CollectorRun` record set to `PENDING`.
2.  **Enqueue**: Enqueues the run ID to the worker queue.
3.  **Collection**: Background worker calls `trigger_run()` on `BrightDataService` and records the returned `snapshot_id`.
4.  **Polling**: Worker polls `get_run_status()` until it transitions to `ready`.
5.  **Audit**: Worker downloads results, passing them to the Observatory `DriftEngine` to check for anomalies.
6.  **Self-Healing**: If quality drops, worker launches the LangGraph agent, validates candidates in the Sandbox, and deploys `CollectorVersion` vN.
7.  **Recovery**: Worker runs a recovery collection job using the updated code to reclaim missing fields.
