import time
import logging
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from apps.backend.app.models.models import (
    Scraper, ScraperVersion, ExtractionSchema, ScraperRun, FailureEvent, RepairAttempt
)
from apps.backend.app.services.bright_data import get_bright_data_service
from apps.backend.app.services.drift_engine import DriftEngine
from apps.ai_agent.graph import repair_agent

logger = logging.getLogger("webguardian")

class ScraperExecutor:
    @staticmethod
    def run_scraper_pipeline(db: Session, scraper_id: str, use_v2_dom: bool = False) -> Dict[str, Any]:
        """
        Executes a scraper run, audits data quality, detects drift,
        triggers LangGraph self-healing if needed, and runs recovery collections.
        """
        logger.info(f"Pipeline: Starting pipeline run for Scraper {scraper_id}")
        
        # 1. Load scraper and configuration
        scraper = db.query(Scraper).filter(Scraper.id == scraper_id).first()
        if not scraper:
            raise ValueError(f"Scraper {scraper_id} not found")

        schema_model = db.query(ExtractionSchema).filter(ExtractionSchema.scraper_id == scraper_id).first()
        if not schema_model:
            raise ValueError(f"Extraction Schema for scraper {scraper_id} is missing")
            
        schema_fields = schema_model.fields

        # 2. Retrieve or create Active ScraperVersion v1
        active_version = db.query(ScraperVersion).filter(
            ScraperVersion.scraper_id == scraper_id,
            ScraperVersion.status == "ACTIVE"
        ).first()

        if not active_version:
            # Generate default selector map based on schema contract
            default_selectors = {}
            for field in schema_fields:
                field_name = field["field"]
                # Default v1 is .field_name or class tag
                default_selectors[field_name] = f".{field_name}"
                
            active_version = ScraperVersion(
                scraper_id=scraper_id,
                version_number=1,
                selector_logic=default_selectors,
                status="ACTIVE"
            )
            db.add(active_version)
            db.commit()
            db.refresh(active_version)
            
            scraper.current_version_id = active_version.id
            db.commit()

        # 3. Trigger Scraper via Bright Data Service
        bd_service = get_bright_data_service()
        
        start_time = time.time()
        run_res = bd_service.run_scraper(
            scraper_id=scraper.id, 
            selectors=active_version.selector_logic,
            use_v2_dom=use_v2_dom
        )
        latency = int((time.time() - start_time) * 1000)

        # In mock, run_scraper is synchronous and populates data instantly.
        # Download results
        extracted_data = bd_service.get_results(run_res["run_id"])
        
        # Compute run quality score and schema validation
        total_rows = len(extracted_data)
        has_critical_failure = False
        error_msg = None
        
        # For simplicity, if any required field is missing in 100% of rows, flag run as FAILED/PARTIAL
        required_fields = [f["field"] for f in schema_fields if f.get("required", False)]
        missing_required = False
        
        if total_rows == 0:
            has_critical_failure = True
            error_msg = "Scraper returned 0 records."
        else:
            for req in required_fields:
                non_empty = [r for r in extracted_data if r.get(req) is not None and str(r.get(req)).strip() != ""]
                if not non_empty:
                    missing_required = True
                    has_critical_failure = True
                    error_msg = f"Required semantic field '{req}' missing from all rows."

        # Create ScraperRun Record
        scraper_run = ScraperRun(
            scraper_id=scraper.id,
            version_id=active_version.id,
            status="FAILED" if has_critical_failure else "SUCCESS",
            rows_scraped=total_rows,
            latency_ms=run_res.get("latency_ms", latency),
            quality_score=100.0 if not has_critical_failure else 0.0,
            error_message=error_msg
        )
        db.add(scraper_run)
        db.commit()
        db.refresh(scraper_run)

        # 4. Evaluate run against Observatory baseline metrics for Drift
        should_heal, failures = DriftEngine.evaluate_run(
            db=db,
            scraper=scraper,
            run=scraper_run,
            extracted_data=extracted_data,
            schema_fields=schema_fields
        )

        pipeline_result = {
            "initial_run": {
                "run_id": scraper_run.id,
                "version_number": active_version.version_number,
                "status": scraper_run.status,
                "rows_scraped": scraper_run.rows_scraped,
                "latency_ms": scraper_run.latency_ms,
                "error_message": scraper_run.error_message
            },
            "failures_detected": [f.failure_type for f in failures],
            "self_healing_triggered": False,
            "recovered": False,
            "health_score": scraper.health_score
        }

        # 5. Self-Healing Agent Trigger
        if should_heal:
            logger.info("Pipeline: Triggering LangGraph Self-Healing Agent")
            scraper.status = "REPAIRING"
            db.commit()
            
            # Select critical failure event to attach to attempt
            crit_fail = next((f for f in failures if f.severity == "CRITICAL"), failures[0] if failures else None)
            
            repair_id = str(uuid.uuid4())
            attempt = RepairAttempt(
                id=repair_id,
                failure_event_id=crit_fail.id if crit_fail else scraper_run.id,
                scraper_id=scraper.id,
                status="RUNNING",
                old_selectors=active_version.selector_logic
            )
            db.add(attempt)
            db.commit()

            # Compile LangGraph payload
            from apps.backend.app.services.bright_data import HTML_V1, HTML_V2
            
            initial_state = {
                "scraper_id": scraper.id,
                "failure_event_id": repair_id,
                "target_url": scraper.target_url,
                "original_selectors": active_version.selector_logic,
                "schema_contracts": schema_fields,
                "old_html": HTML_V1,
                "current_html": HTML_V2,
                
                "failure_triage": {},
                "dom_drift": {},
                "data_drift": {},
                "intent_recovery": {},
                
                "candidates": [],
                "best_candidate": None,
                
                "confidence": 0.0,
                "risk_evaluation": "DO_NOT_DEPLOY",
                "reasoning": "",
                
                "validation_passed": False,
                "validation_errors": [],
                "validation_runs": 0
            }

            # Invoke LangGraph
            agent_res = repair_agent.invoke(initial_state)
            
            # Refresh session to inspect updates written by agent
            db.expire_all()
            
            # Re-fetch scraper status
            db.refresh(scraper)
            
            pipeline_result["self_healing_triggered"] = True
            pipeline_result["repair_attempt_id"] = repair_id
            pipeline_result["agent_decision"] = agent_res.get("risk_evaluation")
            pipeline_result["agent_confidence"] = agent_res.get("confidence")
            pipeline_result["agent_reasoning"] = agent_res.get("reasoning")
            
            # If auto-deployed, run recovery check!
            if agent_res.get("risk_evaluation") == "AUTO_DEPLOY":
                logger.info("Pipeline: Auto-deployed repaired version. Executing recovery run.")
                db.refresh(scraper)
                
                new_version = db.query(ScraperVersion).filter(
                    ScraperVersion.scraper_id == scraper.id,
                    ScraperVersion.status == "ACTIVE"
                ).first()
                
                # Run scraper again using the updated active version selectors
                rec_start = time.time()
                recovery_res = bd_service.run_scraper(
                    scraper_id=scraper.id,
                    selectors=new_version.selector_logic,
                    use_v2_dom=use_v2_dom
                )
                rec_latency = int((time.time() - rec_start) * 1000)
                
                recovered_data = bd_service.get_results(recovery_res["run_id"])
                rec_rows = len(recovered_data)
                
                # Check recovery success
                rec_success = rec_rows > 0 and not any(
                    recovered_data[0].get(req) is None or str(recovered_data[0].get(req)).strip() == ""
                    for req in required_fields
                )
                
                rec_run = ScraperRun(
                    scraper_id=scraper.id,
                    version_id=new_version.id,
                    status="SUCCESS" if rec_success else "FAILED",
                    rows_scraped=rec_rows,
                    latency_ms=recovery_res.get("latency_ms", rec_latency),
                    quality_score=100.0 if rec_success else 0.0
                )
                db.add(rec_run)
                db.commit()
                
                # Re-calculate health score with the successful recovery
                DriftEngine.evaluate_run(
                    db=db,
                    scraper=scraper,
                    run=rec_run,
                    extracted_data=recovered_data,
                    schema_fields=schema_fields
                )
                
                pipeline_result["recovered"] = True
                pipeline_result["recovery_run"] = {
                    "run_id": rec_run.id,
                    "version_number": new_version.version_number,
                    "status": rec_run.status,
                    "rows_scraped": rec_run.rows_scraped,
                    "latency_ms": rec_run.latency_ms
                }
                
                # Update scraper status to active after recovery
                scraper.status = "ACTIVE"
                db.commit()
                
            pipeline_result["health_score"] = scraper.health_score

        return pipeline_result
