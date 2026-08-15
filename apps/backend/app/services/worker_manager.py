import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from apps.backend.app.core.database import SessionLocal
from apps.backend.app.models.models import (
    Collector, CollectorVersion, CollectorRun, Scraper, ExtractionSchema, ScraperRun, FailureEvent, RepairAttempt
)
from apps.backend.app.services.bright_data import get_bright_data_service, BrightDataTimeoutError, BrightDataAPIError
from apps.backend.app.services.drift_engine import DriftEngine
from apps.ai_agent.graph import repair_agent

logger = logging.getLogger("webguardian")

# In-memory queue for local execution fallback (zero-dependency async running)
local_task_queue = asyncio.Queue()

class WorkerManager:
    @staticmethod
    async def process_collector_run(run_id: str):
        """
        Background task worker: triggers scraper, polls status, fetches results,
        audits drift, and initiates self-healing if needed.
        """
        logger.info(f"Worker: Processing CollectorRun {run_id}")
        
        db = SessionLocal()
        try:
            # 1. Load run and collector
            run_model = db.query(CollectorRun).filter(CollectorRun.id == run_id).first()
            if not run_model:
                logger.error(f"Worker: Run {run_id} not found")
                return
                
            collector = db.query(Collector).filter(Collector.id == run_model.collector_id).first()
            if not collector:
                logger.error(f"Worker: Collector not found for run {run_id}")
                run_model.status = "FAILED"
                db.commit()
                return

            scraper = db.query(Scraper).filter(Scraper.id == collector.scraper_id).first()
            schema_model = db.query(ExtractionSchema).filter(ExtractionSchema.scraper_id == scraper.id).first()
            schema_fields = schema_model.fields if schema_model else []

            # Determine DOM version to simulate in mock (read from extra flags in mock)
            bd_service = get_bright_data_service()
            use_v2 = getattr(run_model, "_use_v2_mock", False)
            if hasattr(bd_service, "_v2_flags"):
                bd_service._v2_flags[collector.bright_data_id] = use_v2

            # Get active selectors from latest version config
            active_version = db.query(CollectorVersion).filter(
                CollectorVersion.collector_id == collector.id,
                CollectorVersion.status == "ACTIVE"
            ).order_by(CollectorVersion.version.desc()).first()

            if not active_version:
                # Setup default selector config
                default_sel = {f["field"]: f".{f['field']}" for f in schema_fields}
                active_version = CollectorVersion(
                    collector_id=collector.id,
                    version=1,
                    configuration={"selectors": default_sel},
                    status="ACTIVE"
                )
                db.add(active_version)
                db.commit()
                db.refresh(active_version)
                
            selectors = active_version.configuration.get("selectors", {})
            if hasattr(bd_service, "_active_selectors"):
                bd_service._active_selectors[collector.bright_data_id] = selectors

            # 2. Trigger run on Bright Data Scraper Studio
            run_model.status = "RUNNING"
            db.commit()
            
            logger.info(f"Worker: Triggering Bright Data execution for collector {collector.bright_data_id}")
            start_time = time_now()
            
            try:
                trigger_res = await bd_service.trigger_run(collector.bright_data_id, [scraper.target_url])
                snapshot_id = trigger_res["snapshot_id"]
                run_model.snapshot_id = snapshot_id
                db.commit()
            except BrightDataTimeoutError as e:
                # Catch timeouts, record runtime/connection failures
                logger.error(f"Worker: Timeout triggering run: {str(e)}")
                run_model.status = "FAILED"
                run_model.completed_at = datetime.utcnow()
                db.commit()
                
                # Log Runtime Drift Event
                fail = FailureEvent(
                    scraper_id=scraper.id,
                    run_id=run_id,
                    failure_type="RUNTIME_DRIFT",
                    description=f"Bright Data request timed out: {str(e)}",
                    severity="CRITICAL"
                )
                db.add(fail)
                db.commit()
                return
            except BrightDataAPIError as e:
                logger.error(f"Worker: API error triggering run: {str(e)}")
                run_model.status = "FAILED"
                run_model.completed_at = datetime.utcnow()
                db.commit()
                
                # Log Runtime Drift Event for API failures
                fail = FailureEvent(
                    scraper_id=scraper.id,
                    run_id=run_id,
                    failure_type="RUNTIME_DRIFT",
                    description=f"Bright Data API error: {str(e)}",
                    severity="CRITICAL"
                )
                db.add(fail)
                db.commit()
                return

            # 3. Poll progress until complete
            logger.info(f"Worker: Polling status for snapshot {snapshot_id}")
            max_polls = 10
            poll_interval = 0.5 if isinstance(bd_service, bd_service.__class__) else 2.0  # Poll faster in mock
            
            for _ in range(max_polls):
                status_res = await bd_service.get_run_status(snapshot_id)
                status = status_res["status"]
                
                if status == "ready":
                    break
                elif status == "failed":
                    run_model.status = "FAILED"
                    db.commit()
                    return
                    
                await asyncio.sleep(poll_interval)
                
            # 4. Fetch results
            extracted_data = await bd_service.fetch_results(snapshot_id)
            latency = int((time_now() - start_time) * 1000)
            
            # Map extraction rows count
            total_rows = len(extracted_data)
            
            # Update collector run model
            run_model.status = "COMPLETED"
            run_model.rows = total_rows
            run_model.latency = latency
            run_model.completed_at = datetime.utcnow()
            collector.last_run = datetime.utcnow()
            db.commit()

            # 5. Build ScraperRun equivalent record for Observatory health checks
            scraper_run = ScraperRun(
                scraper_id=scraper.id,
                version_id=None, # version maps via collector versions
                status="SUCCESS" if total_rows > 0 else "FAILED",
                rows_scraped=total_rows,
                latency_ms=latency,
                quality_score=100.0 if total_rows > 0 else 0.0
            )
            db.add(scraper_run)
            db.commit()
            db.refresh(scraper_run)

            # Evaluate run drift
            should_heal, failures = DriftEngine.evaluate_run(
                db=db,
                scraper=scraper,
                run=scraper_run,
                extracted_data=extracted_data,
                schema_fields=schema_fields
            )
            
            # 6. Self-Healing trigger
            if should_heal:
                logger.info("Worker: Self-healing triggered asynchronously")
                scraper.status = "REPAIRING"
                db.commit()

                from apps.backend.app.services.event_broker import event_broker
                event_broker.publish(run_id, {
                    "type": "AGENT_STEP",
                    "node": "DETECTION",
                    "status": "completed",
                    "message": "Scraper Observatory flagged quality validation drift: Extraction dropped to 0%"
                })

                # Trigger LangGraph agent
                repair_id = run_id # attach candidate logs to this run ID
                attempt = RepairAttempt(
                    id=repair_id,
                    failure_event_id=failures[0].id if failures else run_id,
                    scraper_id=scraper.id,
                    status="RUNNING",
                    old_selectors=selectors
                )
                db.add(attempt)
                db.commit()

                from apps.backend.app.services.bright_data import HTML_V1, HTML_V2
                
                initial_state = {
                    "scraper_id": scraper.id,
                    "failure_event_id": repair_id,
                    "target_url": scraper.target_url,
                    "original_selectors": selectors,
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

                # Invoke repair agent graph
                agent_res = await asyncio.to_thread(repair_agent.invoke, initial_state)
                
                db.expire_all()
                db.refresh(scraper)
                
                # Map LangGraph deployment updates to CollectorVersion and deploy to RealBrightData if AutoDeploy approved
                if agent_res.get("risk_evaluation") == "AUTO_DEPLOY" and agent_res.get("best_candidate"):
                    best_sel = agent_res["best_candidate"]["selector"]
                    
                    # Deprecate previous collector version
                    db.query(CollectorVersion).filter(
                        CollectorVersion.collector_id == collector.id
                    ).update({"status": "DEPRECATED"})
                    
                    # Deploy new version config
                    new_version = CollectorVersion(
                        collector_id=collector.id,
                        version=active_version.version + 1,
                        configuration={"selectors": {"price": best_sel}},
                        status="ACTIVE",
                        deployment_reason=agent_res.get("reasoning")
                    )
                    db.add(new_version)
                    db.commit()

                    # Recovery Collection run
                    logger.info("Worker: Starting recovery run after auto-deploy")
                    rec_run_id = f"rec_run_{uuid_short()}"
                    rec_run = CollectorRun(
                        id=rec_run_id,
                        collector_id=collector.id,
                        status="PENDING"
                    )
                    # Tell mock parser to run on v2 HTML DOM
                    setattr(rec_run, "_use_v2_mock", use_v2)
                    db.add(rec_run)
                    db.commit()
                    
                    # Enqueue recovery run
                    await local_task_queue.put(rec_run_id)

        except Exception as e:
            logger.error(f"Worker exception: {str(e)}")
        finally:
            db.close()

    @staticmethod
    async def start_local_worker_loop():
        """
        Background execution loop executing tasks in the local queue sequentially.
        """
        logger.info("Worker: Starting local queue event loop")
        while True:
            try:
                run_id = await local_task_queue.get()
                await WorkerManager.process_collector_run(run_id)
                local_task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {str(e)}")
                await asyncio.sleep(1)

def time_now() -> float:
    return time.time()

def uuid_short() -> str:
    import uuid
    return str(uuid.uuid4())[:8]

import time
