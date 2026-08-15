# WebGuardian AI

**Tagline**: "The autonomous AI engineer that keeps web data pipelines alive."

WebGuardian AI is an autonomous web intelligence reliability platform. It observes data collection pipelines, detects CSS selector failures, semantically investigates DOM structure redesigns using a stateful LangGraph agent, validates repair strategies in a schema-compliant sandbox, and automatically deploys healed selector version updates to **Bright Data Scraper Studio**.

---

## 🚀 The Core Problem

Modern companies depend on web scraping for competitive intelligence, documentation audits, market pricing updates, and inventory tracking. However:
*   **Websites change constantly**: CSS classes shift, tag nesting rearranges, and selectors break.
*   **Quiet Failures**: Scraping scripts break silently, returning 0 records or empty fields, going unnoticed until downstream pipelines crash.
*   **Engineering Waste**: Software engineers waste hours debugging HTML trees, generating new selectors, and deploying fixes manually.

**WebGuardian AI solves this by introducing Autonomous Reliability Engineering for Web Data Infrastructure.**

---

## 🛠️ The Solution (How it Works)

Instead of hardcoding brittle CSS tags, WebGuardian operates on **Semantic Extraction Contracts**:
1.  **Observes**: Scrapers execute via Bright Data Scraper Studio. WebGuardian compares extracted data against expected schema formats.
2.  **Detects Drift**: Flags row-count drop-offs (Output Drift), missing required fields (Schema/DOM Drift), and latency surges (Runtime Drift).
3.  **Triages & Analyzes**: Wakes up a stateful **LangGraph Agent** to compare original successful HTML with the current broken DOM.
4.  **Recovers Intent**: Translates the failure into semantic intent (e.g., "Extract product price in currency format") rather than raw CSS terms.
5.  **Plans & Proposes**: Generates multiple candidate selector repairs with varied matching strategies (`attribute_match`, `structural_match`, `semantic_match`).
6.  **Validates in Sandbox**: Executes candidates in an isolated sandbox, ranking strategies using a multi-factor score:
    $$\text{Final Score} = 30\% \text{ Semantic Match} + 30\% \text{ Coverage} + 20\% \text{ Schema Validity} + 10\% \text{ Structural Similarity} + 10\% \text{ Confidence}$$
7.  **Auto Deploys**: If the Final Score exceeds **90%**, it automatically deployes version vN to Bright Data, runs a recovery collection, and restores pipeline health to 100%.

---

## 🤝 Bright Data Integration

WebGuardian AI works as the **intelligence and observability control plane** wrapping around **Bright Data Scraper Studio**:

```text
┌────────────────────────────────────────┐
│             WEBGUARDIAN AI             │
│  (Intelligence & Observability Layer)  │
│  - Observes Output & DOM Drift         │
│  - LangGraph self-healing graph        │
│  - Sandbox validation of selectors     │
│  - Collector version audits & rollback │
└───────────────────┬────────────────────┘
                    │
                    ▼  (Trigger Runs / Deploy healed versions)
┌────────────────────────────────────────┐
│       BRIGHT DATA SCRAPER STUDIO       │
│      (Collection Infrastructure)       │
│  - Fully managed browser execution     │
│  - High-scale concurrent proxy runs    │
│  - CAPTCHA bypass & unblocking         │
│  - Structured dataset delivery (JSON)  │
└────────────────────────────────────────┘
```

*   **Bright Data** handles the difficult scraping delivery: unblocking tools, rotating residential proxies, running headless browsers, and structuring dataset outputs.
*   **WebGuardian AI** ensures the scraping collector remains online, automatically fixing code configurations when target websites redesign.

---

## 🏗️ System Architecture

```text
                    Failure
                       │
                       ▼
              ┌─────────────────┐
              │ Failure Triage  │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        DOM Drift            Data Drift
             │                   │
             └─────────┬─────────┘
                       ▼
              Intent Recovery
                       │
                       ▼
              Repair Planning
                       │
                       ▼
             Candidate Repairs
                       │
                       ▼
              Validation Sandbox
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
           FAIL                 PASS
             │                   │
             ▼                   ▼
       Repair Again         Risk Evaluation
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                  High Confidence      Low Confidence
                       │                   │
                       ▼                   ▼
                  Auto Deploy         Human Review
                       │                   │
                       └─────────┬─────────┘
                                 ▼
                           Version + Audit
                                 │
                                 ▼
                              Monitor
```

---

## ⚡ Setup & Run Instructions

To evaluate WebGuardian AI locally with zero external configurations:

### 1. Clone & Set Up Python virtualenv
```bash
# Setup python venv
python -m venv venv

# Activate venv (Windows)
.\venv\Scripts\activate
# Activate venv (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment `.env`
Copy the environment variables:
```bash
copy .env.example .env
```
*(The default settings use SQLite and `LLM_PROVIDER=mock`, enabling the interactive demo mode to work instantly without OpenAI or Bright Data API keys).*

### 3. Launch Backend server
Run the FastAPI control plane:
```bash
python -m uvicorn apps.backend.app.main:app --reload
```
This triggers the backend at `http://127.0.0.1:8000` and starts our asynchronous background worker thread.

### 4. Launch Next.js SaaS Console
Open a new terminal window:
```bash
cd apps/frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## 🎬 Triggering the Cinematic Self-Healing Demo

1.  Open the Dashboard Console at `http://localhost:3000/dashboard`.
2.  Click **Run Scraper** to trigger a baseline, healthy collection run (simulating original DOM layout V1). Notice the health score shows **100%** and 3 laptops are successfully extracted.
3.  Click **🔥 Trigger Chaos Redesign**.
4.  WebGuardian immediately creates a pending run, forcing the mock scraper to load a redesigned HTML V2 layout (where `.price` is replaced with `data-testid="price"`).
5.  Watch the **AI Incident Visualizer** tab update in real-time as the agent:
    *   Flags the critical failure.
    *   Triages DOM drift.
    *   Recovers semantic intent.
    *   Generates 3 repair candidates.
    *   Validates candidates in the sandbox, choosing the `[data-testid='price']` strategy.
    *   Deploys version v2 and runs a recovery task.
6.  Once healed, inspect the **Version & Audits** tab to review selector diffs, rollback previous builds, or use the **Ask AI Engineer** conversational chat to ask: *"What happened to my Nvidia scraper?"*

---

## 📚 Repository Guides
For deeper technical documentation, review:
*   [Monorepo Architecture Details](docs/ARCHITECTURE.md)
*   [LangGraph AI Agent Workflows](docs/AI_AGENT.md)
*   [Bright Data Integration Mapping](docs/BRIGHT_DATA.md)
*   [API Endpoint Reference](docs/API_REFERENCE.md)
*   [Deployment Configurations](docs/DEPLOYMENT.md)
