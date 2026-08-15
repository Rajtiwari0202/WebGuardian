# LangGraph Self-Healing Agent — WebGuardian AI

WebGuardian AI implements a stateful reliability agent using the **LangGraph** framework. The agent acts as an autonomous engineer: investigating failures, planning repairs, validating strategies in a sandbox, and deploying updates.

---

## 🔄 Agent State Graph Workflow

```text
       START
         │
         ▼
  [ Failure Triage ]
         │
         ▼
  [ DOM/Data Drift ]  (Parallel logic simulated sequentially)
         │
         ▼
  [ Intent Recovery ]
         │
         ▼
  [ Repair Planning ]  (Generates multiple candidates)
         │
         ▼
[ Validation Sandbox ]  (Extracts and scores candidates)
         │
         ▼
  [ Risk Decision ]
    ├───> AUTO_DEPLOY    ──> Version Audit ──> Deployment ──> Monitor ──> END
    ├───> PENDING_REVIEW ──> Version Audit ──> Monitor ──> END
    └───> DO_NOT_DEPLOY  ──> END
```

---

## 🗂️ Stateful Agent Schema

The state schema (`AgentState` typed dict) tracks inputs, outputs, and validation metrics:
*   `scraper_id` / `failure_event_id`: Identifiers for the target pipeline.
*   `original_selectors` / `schema_contracts`: Selectors and required target schema parameters.
*   `old_html` / `current_html`: Layout snippets before and after layout changes.
*   `failure_triage` / `dom_drift` / `data_drift` / `intent_recovery`: Analysis logs.
*   `candidates` / `best_candidate`: Strategies scored inside the Sandbox.
*   `confidence` / `risk_evaluation` / `reasoning`: Deployment risk assessments.

---

## 🛠️ Graph Node Responsibilities

1.  **Failure Triage**: Classifies failure types and severity.
2.  **DOM/Data Drift**: Maps layout changes and text formatting differences.
3.  **Intent Recovery**: Recovers field semantic profiles (data type constraints and examples).
4.  **Repair Planning**: Generates at least three candidate CSS selector strategies:
    *   `attribute_match` (based on attributes like data-testid).
    *   `structural_match` (based on card layouts).
    *   `semantic_match` (based on textual contents).
5.  **Validation Sandbox**: Runs each candidate selector on the broken DOM and computes a final score:
    $$\text{Final Score} = 0.30 \times \text{Semantic Match} + 0.30 \times \text{Validation Coverage} + 0.20 \times \text{Schema Validity} + 0.10 \times \text{Structural Similarity} + 0.10 \times \text{Model Confidence}$$
6.  **Risk Evaluation**:
    *   **Score > 90%** $\rightarrow$ `AUTO_DEPLOY`.
    *   **Score 70–90%** $\rightarrow$ `PENDING_REVIEW` (Human confirmation required).
    *   **Score < 70%** $\rightarrow$ `DO_NOT_DEPLOY` (Immediate failure block).
7.  **Versioning & Audit**: Saves candidates and log entries in the database.
8.  **Deployment**: Updates versions and calls `BrightDataService.deploy_version()`.
9.  **Monitor**: Enqueues recovery collection runs.

---

## 🤖 LLM Swapping and Fallbacks

Configured via `.env` parameters `LLM_PROVIDER` and `LLM_MODEL`:
*   `MockProvider`: Returns deterministic, validated candidate scripts matching the target laptop monitor simulation scenarios. Enables out-of-the-box local testing.
*   `OpenAIProvider` / `GeminiProvider` / `GroqProvider`: Swappable production providers calling real LLMs (e.g. `gpt-4o-mini`).
