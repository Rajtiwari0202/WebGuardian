import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from apps.backend.app.core.database import get_db
from apps.backend.app.models.models import (
    Scraper, Collector, CollectorRun, RepairAttempt, RepairCandidate, FailureEvent, ExtractionSchema
)
from apps.backend.app.services.worker_manager import local_task_queue, uuid_short

logger = logging.getLogger("webguardian")

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.post("/trigger-chaos")
async def trigger_chaos_mode(scraper_id: str, db: Session = Depends(get_db)):
    """
    Chaos Mode: Simulates a website redesign.
    Updates the target run to parse V2 DOM structure, forcing scraper failure,
    triggering the LangGraph agent self-healing repair, and recovering the pipeline.
    """
    scraper = db.query(Scraper).filter(Scraper.id == scraper_id).first()
    if not scraper:
        raise HTTPException(status_code=404, detail="Scraper not found")

    collector = db.query(Collector).filter(Collector.scraper_id == scraper.id).first()
    if not collector:
        # Create collector if missing
        collector = Collector(
            scraper_id=scraper.id,
            bright_data_id=f"c_col_{uuid_short()}",
            name=scraper.name
        )
        db.add(collector)
        db.commit()
        db.refresh(collector)

    # 1. Create PENDING Collector Run with v2 simulation flag
    run_id = f"run_{uuid_short()}"
    run = CollectorRun(
        id=run_id,
        collector_id=collector.id,
        status="PENDING",
    )
    # Inject flag telling mock parser to load HTML_V2
    setattr(run, "_use_v2_mock", True)
    db.add(run)
    db.commit()

    # 2. Enqueue task in worker queue
    await local_task_queue.put(run_id)
    
    return {
        "status": "QUEUED",
        "message": "Chaos mode triggered: simulating website redesign on DOM layout v2",
        "run_id": run_id,
        "collector_id": collector.bright_data_id
    }

@router.get("/incident/{run_id}")
def get_incident_trace(run_id: str, db: Session = Depends(get_db)):
    """
    Returns incident timeline data, repair attempts, HTML diffs,
    and ranked sandbox validation candidates.
    """
    run = db.query(CollectorRun).filter(CollectorRun.id == run_id).first()
    if not run:
        # Check in ScraperRuns
        pass
        
    attempt = db.query(RepairAttempt).filter(RepairAttempt.id == run_id).first()
    if not attempt:
        return {
            "status": "INCIDENT_DETECTED",
            "message": "AI self-healing agent is starting...",
            "timeline": [
                {"time": "10:02:01", "event": "Failure detected: Price extraction dropped to 0%", "status": "active"},
                {"time": "10:02:03", "event": "Failure triage: DOM_DRIFT confirmed", "status": "active"}
            ],
            "candidates": []
        }

    # Fetch candidates
    candidates = db.query(RepairCandidate).filter(RepairCandidate.repair_attempt_id == attempt.id).all()
    
    # Build timeline JSON payload
    timeline = [
        {
            "time": "10:02:01",
            "event": "Failure detected",
            "description": "Required field 'price' missing from all rows. Extraction rate dropped to 0%.",
            "status": "completed"
        },
        {
            "time": "10:02:03",
            "event": "Failure Triage",
            "description": f"Drift engine classified failure as: DOM_DRIFT. Severity: CRITICAL.",
            "status": "completed"
        },
        {
            "time": "10:02:06",
            "event": "DOM Analysis",
            "description": "Original selector '.price' is missing. Found '<span data-testid=\"price\">' wrapping currency text.",
            "status": "completed"
        },
        {
            "time": "10:02:10",
            "event": "Intent Recovery",
            "description": "Contract: 'price' requires currency type (examples: $1,299). Semantic region identified.",
            "status": "completed"
        },
        {
            "time": "10:02:15",
            "event": "Repair Planning & Candidates",
            "description": f"Generated {len(candidates)} candidate CSS selectors.",
            "status": "completed"
        },
        {
            "time": "10:02:20",
            "event": "Validation Sandbox",
            "description": f"Tested strategy outcomes. Best candidate: '{attempt.new_selectors.get('price')}' score: {attempt.confidence}%.",
            "status": "completed"
        },
        {
            "time": "10:02:25",
            "event": "Auto Deployment",
            "description": "Collector configuration updated in Bright Data Scraper Studio. Deployed version v2.",
            "status": "completed"
        },
        {
            "time": "10:02:32",
            "event": "Pipeline Restored",
            "description": "Recovery run completed. 3 products successfully extracted. Downtime prevented: 100%.",
            "status": "completed"
        }
    ]

    candidates_list = []
    for cand in candidates:
        candidates_list.append({
            "id": cand.id,
            "field_name": cand.field_name,
            "selector": cand.selector,
            "strategy": cand.strategy,
            "model_confidence": cand.model_confidence,
            "validation_score": cand.validation_score,
            "semantic_score": cand.semantic_score,
            "final_score": cand.final_score,
            "status": cand.status
        })

    # Sort candidates by final score descending
    candidates_list.sort(key=lambda x: x["final_score"], reverse=True)

    return {
        "status": attempt.status,  # SUCCESS, PENDING_REVIEW
        "confidence": attempt.confidence,
        "reasoning": attempt.reasoning,
        "old_selector": ".price",
        "new_selector": attempt.new_selectors.get("price") if attempt.new_selectors else None,
        "timeline": timeline,
        "candidates": candidates_list
    }


@router.get("/incident/{run_id}/stream")
async def stream_incident_trace(run_id: str):
    """
    Server-Sent Events (SSE) streaming endpoint yielding real-time LangGraph agent step updates.
    """
    import json
    import asyncio
    from fastapi.responses import StreamingResponse
    from apps.backend.app.services.event_broker import event_broker

    async def event_generator():
        # Yield initial connect event
        yield "data: {\"type\": \"CONNECT\", \"message\": \"SSE connection established\"}\n\n"
        
        queue = event_broker.subscribe(run_id)
        try:
            while True:
                # Wait for published events
                event_data = await queue.get()
                yield f"data: {json.dumps(event_data)}\n\n"
                queue.task_done()
        except asyncio.CancelledError:
            logger.info(f"SSE: Client connection cancelled for run {run_id}")
        finally:
            event_broker.unsubscribe(run_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/reset")
def reset_demo_database(db: Session = Depends(get_db)):
    """
    Resets the database, clearing all runs, failures, memories, and audit logs.
    Restores Laptop Price Monitor to Version 1, ACTIVE, and pre-populates clean runs.
    """
    from datetime import datetime
    from apps.backend.app.models.models import (
        Scraper, Collector, CollectorVersion, CollectorRun, ScraperRun, FailureEvent, RepairAttempt, RepairCandidate, AuditLog, AgentMemory, ExtractionSchema
    )
    
    # Delete everything
    db.query(AgentMemory).delete()
    db.query(AuditLog).delete()
    db.query(RepairCandidate).delete()
    db.query(RepairAttempt).delete()
    db.query(FailureEvent).delete()
    db.query(ScraperRun).delete()
    db.query(CollectorRun).delete()
    db.query(CollectorVersion).delete()
    db.query(Collector).delete()
    db.query(ExtractionSchema).delete()
    db.query(Scraper).delete()
    db.commit()

    # Pre-populate default laptop monitor scraper
    from apps.backend.app.models.models import User, Project
    default_user = db.query(User).filter(User.email == "demo@webguardian.ai").first()
    if not default_user:
        default_user = User(
            email="demo@webguardian.ai",
            hashed_password="demo_hashed_password",
            full_name="Demo Operator"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
    default_project = db.query(Project).filter(Project.owner_id == default_user.id).first()
    if not default_project:
        default_project = Project(
            name="Demo Workspaces",
            owner_id=default_user.id
        )
        db.add(default_project)
        db.commit()
        db.refresh(default_project)

    scraper = Scraper(
        project_id=default_project.id,
        name="Laptop Price Monitor",
        target_url="https://laptops-r-us.com/products",
        status="ACTIVE",
        health_score=99.8
    )
    db.add(scraper)
    db.commit()
    db.refresh(scraper)

    schema = ExtractionSchema(
        scraper_id=scraper.id,
        fields=[
            {
                "field": "price",
                "description": "Current selling price of the laptop",
                "type": "currency",
                "required": True,
                "examples": ["$999.00", "$1,299.00"]
            }
        ]
    )
    db.add(schema)

    collector = Collector(
        scraper_id=scraper.id,
        bright_data_id="c_laptop_monitor_812",
        name=scraper.name
    )
    db.add(collector)
    db.commit()
    db.refresh(collector)

    v1 = CollectorVersion(
        collector_id=collector.id,
        version=1,
        configuration={"selectors": {"price": ".price"}},
        status="ACTIVE",
        deployment_reason="Initial production deployment"
    )
    db.add(v1)

    # 10 healthy historical runs
    for i in range(10):
        run = ScraperRun(
            scraper_id=scraper.id,
            status="SUCCESS",
            rows_scraped=3,
            latency_ms=450 + (i * 5),
            quality_score=100.0,
            created_at=datetime.utcnow()
        )
        db.add(run)

    db.commit()
    return {"status": "SUCCESS", "message": "Demo environment reset: Collector v1 active, health = 100%"}


@router.post("/trigger-timeout-drift")
async def trigger_timeout_drift(scraper_id: str, db: Session = Depends(get_db)):
    """
    Scenario 2: Bright Data Outage (Infrastructure Timeout).
    Generates a runtime drift failure trace showing WebGuardian blocking selector repairs on infrastructure drops.
    """
    import asyncio
    from datetime import datetime
    from apps.backend.app.services.event_broker import event_broker
    from apps.backend.app.models.models import (
        Scraper, Collector, CollectorRun, FailureEvent, ScraperRun
    )
    
    scraper = db.query(Scraper).filter(Scraper.id == scraper_id).first()
    if not scraper:
        raise HTTPException(status_code=404, detail="Scraper not found")

    collector = db.query(Collector).filter(Collector.scraper_id == scraper.id).first()
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")

    run_id = f"run_timeout_{uuid_short()}"
    
    # Create failure run in DB
    run = CollectorRun(
        id=run_id,
        collector_id=collector.id,
        status="FAILED",
        rows=0,
        latency=5000,
        completed_at=datetime.utcnow()
    )
    db.add(run)
    
    scraper_run = ScraperRun(
        scraper_id=scraper.id,
        status="FAILED",
        rows_scraped=0,
        latency_ms=5000,
        quality_score=0.0
    )
    db.add(scraper_run)
    db.commit()
    
    fail = FailureEvent(
        scraper_id=scraper.id,
        run_id=run_id,
        failure_type="RUNTIME_DRIFT",
        description="Timeout connecting to Bright Data DCA API (All connection attempts failed)",
        severity="CRITICAL"
    )
    db.add(fail)
    db.commit()

    # Stream real-time failure triage logs
    async def simulate_logging():
        await asyncio.sleep(0.5)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "DETECTION",
            "status": "completed",
            "message": "Scraper Observatory flagged runtime availability drop: Response timeout"
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "TRIAGE",
            "status": "completed",
            "message": "Drift engine classified failure as: RUNTIME_DRIFT. Severity: CRITICAL."
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "REPAIR_PLANNING",
            "status": "completed",
            "message": "Triage Action: Blocked selector repair triggers. Reason: Infrastructure failure, not DOM layout drift."
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "RECOVERY_RUN",
            "status": "completed",
            "message": "Scheduled retry policy checks. Awaiting connection restoration..."
        })

    asyncio.create_task(simulate_logging())

    return {"status": "SUCCESS", "run_id": run_id}


@router.post("/trigger-unsafe-drift")
async def trigger_unsafe_drift(scraper_id: str, db: Session = Depends(get_db)):
    """
    Scenario 3: Unsafe selector checks (AI Proposes, Sandbox Proves, WebGuardian Deploys).
    Displays rejections of faulty selector strategies.
    """
    import asyncio
    from datetime import datetime
    from apps.backend.app.services.event_broker import event_broker
    from apps.backend.app.models.models import (
        Scraper, Collector, CollectorRun, FailureEvent, RepairAttempt, RepairCandidate, ScraperRun
    )
    
    scraper = db.query(Scraper).filter(Scraper.id == scraper_id).first()
    if not scraper:
        raise HTTPException(status_code=404, detail="Scraper not found")

    collector = db.query(Collector).filter(Collector.scraper_id == scraper.id).first()
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")

    run_id = f"run_unsafe_{uuid_short()}"
    
    # Save traces in DB
    run = CollectorRun(
        id=run_id,
        collector_id=collector.id,
        status="COMPLETED",
        rows=3,
        latency=450,
        completed_at=datetime.utcnow()
    )
    db.add(run)
    
    fail = FailureEvent(
        scraper_id=scraper.id,
        run_id=run_id,
        failure_type="DOM_DRIFT",
        description="Required field 'price' missing from DOM nodes",
        severity="CRITICAL"
    )
    db.add(fail)
    db.commit()

    attempt = RepairAttempt(
        id=run_id,
        failure_event_id=fail.id,
        scraper_id=scraper.id,
        status="SUCCESS",
        confidence=97.8,
        reasoning="AI rejected 2 unsafe selector candidates. Only the validated strategy passed schema constraints.",
        new_selectors={"price": "[data-testid='price']"}
    )
    db.add(attempt)
    db.commit()

    cand_a = RepairCandidate(
        repair_attempt_id=run_id,
        field_name="price",
        selector=".price-old",
        strategy="attribute_match",
        model_confidence=55.0,
        validation_score=0.0,
        semantic_score=12.5,
        final_score=12.5,
        status="REJECTED"
    )
    cand_b = RepairCandidate(
        repair_attempt_id=run_id,
        field_name="price",
        selector="[data-testid='price']",
        strategy="semantic_match",
        model_confidence=95.0,
        validation_score=100.0,
        semantic_score=97.8,
        final_score=97.8,
        status="SELECTED"
    )
    cand_c = RepairCandidate(
        repair_attempt_id=run_id,
        field_name="price",
        selector=".product .amount",
        strategy="structural_match",
        model_confidence=75.0,
        validation_score=65.2,
        semantic_score=65.2,
        final_score=65.2,
        status="REJECTED"
    )
    db.add(cand_a)
    db.add(cand_b)
    db.add(cand_c)
    db.commit()

    # Stream real-time logs
    async def simulate_logging():
        await asyncio.sleep(0.5)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "DETECTION",
            "status": "completed",
            "message": "Scraper Observatory flagged DOM drift: price container element changed layout structure"
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "REPAIR_PLANNING",
            "status": "completed",
            "message": "Generated 3 candidate repair selectors"
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "VALIDATION",
            "status": "completed",
            "message": "Validation Sandbox results: candidate '.price-old' failed. candidate '.product .amount' scored 65.2% (unsafe). Deployed only validated repair '[data-testid=price]'"
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "DEPLOYMENT",
            "status": "completed",
            "message": "Version v2 config auto-deployed to Bright Data Scraper Studio"
        })
        await asyncio.sleep(0.8)
        event_broker.publish(run_id, {
            "type": "AGENT_STEP",
            "node": "RECOVERY_RUN",
            "status": "completed",
            "message": "Recovery collection finished. Pipeline restored"
        })

    asyncio.create_task(simulate_logging())

    return {"status": "SUCCESS", "run_id": run_id}
