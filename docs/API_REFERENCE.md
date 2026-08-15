# API Reference Guide — WebGuardian AI

The WebGuardian AI Control Plane exposes standard REST endpoints and GenAI conversational routing interfaces.

---

## 📋 Scrapers Router (`/api/scrapers`)

### 1. List Scrapers
*   **Method**: `GET`
*   **Endpoint**: `/api/scrapers`
*   **Description**: Returns a list of all scrapers, their status, health scores, and current selector configurations. (If database is empty, automatically pre-populates a default Laptop prices collector).
*   **Response (200 OK)**:
    ```json
    [
      {
        "id": "c_laptop_monitor_812",
        "name": "Laptop Price Monitor",
        "target_url": "https://laptops-r-us.com/products",
        "status": "ACTIVE",
        "health_score": 99.8,
        "bright_data_id": "c_laptop_monitor_812",
        "active_version": 1,
        "selectors": {
          "price": ".price"
        }
      }
    ]
    ```

### 2. Create Scraper
*   **Method**: `POST`
*   **Endpoint**: `/api/scrapers`
*   **Request Body**:
    ```json
    {
      "name": "Nvidia GPU Monitor",
      "target_url": "https://newegg.com/gpu",
      "schema_fields": [
        {
          "field": "price",
          "description": "selling price",
          "type": "currency",
          "required": true,
          "examples": ["$999.00"]
        }
      ]
    }
    ```
*   **Response (200 OK)**:
    ```json
    {
      "status": "SUCCESS",
      "scraper_id": "8f3a92-...",
      "collector_id": "c_col_8e2910"
    }
    ```

### 3. Get Scraper Details
*   **Method**: `GET`
*   **Endpoint**: `/api/scrapers/{id}`
*   **Description**: Retrieves detailed historical telemetry, collector versions, background runs, and audited action logs.

### 4. Trigger Scraper Run
*   **Method**: `POST`
*   **Endpoint**: `/api/scrapers/{id}/run`
*   **Description**: Enqueues a scraping job on the current active configuration (HTML v1).

### 5. Rollback Selector Version
*   **Method**: `POST`
*   **Endpoint**: `/api/scrapers/{id}/rollback`
*   **Query Parameters**: `version_number` (int)
*   **Description**: Deprecates active configurations and restores a previous selector setup.

---

## ⚡ Demo / Chaos Router (`/api/demo`)

### 1. Trigger Chaos Redesign
*   **Method**: `POST`
*   **Endpoint**: `/api/demo/trigger-chaos`
*   **Query Parameters**: `scraper_id` (string)
*   **Description**: Simulates a website redesign by forcing the background worker to load HTML v2, causing selector failure, launching the self-healing agent, and auto-deploying updates.
*   **Response (200 OK)**:
    ```json
    {
      "status": "QUEUED",
      "run_id": "run_8a2d9b",
      "collector_id": "c_laptop_monitor_812"
    }
    ```

### 2. Fetch Incident Trace
*   **Method**: `GET`
*   **Endpoint**: `/api/demo/incident/{run_id}`
*   **Description**: Returns live agent trace timeline updates, HTML code diff changes, and ranked sandbox strategy candidates.

---

## 💬 Conversational Chat Router (`/api/chat`)

### 1. Ask AI Engineer
*   **Method**: `POST`
*   **Endpoint**: `/api/chat`
*   **Request Body**:
    ```json
    {
      "message": "What happened to my Nvidia scraper?"
    }
    ```
*   **Response (200 OK)**:
    ```json
    {
      "response": "Your Nvidia GPU Scraper failed at 10:32 AM... Generated repair: [data-product-price]...",
      "suggested_actions": ["View Incident #10482", "Inspect Version History"]
    }
    ```
