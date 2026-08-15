import os
import sys
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override database URL for test isolation
TEST_DB_FILE = "webguardian_bd_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_FILE}"

from apps.backend.app.core.database import Base, engine, SessionLocal
from apps.backend.app.models.models import (
    User, Project, Scraper, ExtractionSchema, Collector, CollectorVersion, CollectorRun, FailureEvent, RepairAttempt
)
from apps.backend.app.services.bright_data import (
    get_bright_data_service, MockBrightDataService, RealBrightDataService, BrightDataTimeoutError, BrightDataAPIError
)
from apps.backend.app.services.worker_manager import WorkerManager

@pytest.fixture(name="db_session")
def fixture_db_session():
    # Setup shared database file
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except Exception:
                pass

@pytest.mark.anyio
async def test_collector_creation_and_async_run(db_session):
    print("\n--- Running Bright Data Collector Lifecycle Test ---")
    
    # 1. Setup entities
    user = User(email="bd_judge@hackathon.com", hashed_password="hashed_password", full_name="Bright Data Judge")
    db_session.add(user)
    db_session.commit()
    
    project = Project(name="Market Intelligence", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    
    scraper = Scraper(project_id=project.id, name="Amazon Monitors", target_url="https://amazon.com/monitors")
    db_session.add(scraper)
    db_session.commit()

    schema = ExtractionSchema(
        scraper_id=scraper.id,
        fields=[{"field": "price", "description": "selling price", "type": "currency", "required": True}]
    )
    db_session.add(schema)
    db_session.commit()

    # Create Collector
    bd_service = MockBrightDataService()
    collector_info = await bd_service.create_collector({"name": scraper.name})
    
    collector = Collector(
        scraper_id=scraper.id,
        bright_data_id=collector_info["bright_data_id"],
        name=collector_info["name"]
    )
    db_session.add(collector)
    db_session.commit()
    
    # Verify collector linkages
    assert collector.bright_data_id.startswith("c_")
    assert scraper.collector.id == collector.id
    
    print("✓ DB Models established. Scraper linked to Collector ID:", collector.bright_data_id)

    # 2. Trigger async collection
    print("Step 2: Triggering async collector execution...")
    # Add active selectors mapping to mock state
    bd_service._active_selectors[collector.bright_data_id] = {"price": ".price"}
    
    run_res = await bd_service.trigger_run(collector.bright_data_id, [scraper.target_url])
    snapshot_id = run_res["snapshot_id"]
    
    assert run_res["status"] == "RUNNING"
    assert snapshot_id.startswith("snap_")
    
    # 3. Simulate polling run status progression
    print("Step 3: Checking run status progression...")
    # First poll should be running
    status_1 = await bd_service.get_run_status(snapshot_id)
    assert status_1["status"] == "running"
    assert status_1["progress"] == 50
    
    # Second poll should transition to ready
    status_2 = await bd_service.get_run_status(snapshot_id)
    assert status_2["status"] == "ready"
    assert status_2["progress"] == 100
    
    # Download results
    results = await bd_service.fetch_results(snapshot_id)
    assert len(results) == 3
    assert results[0]["price"] == "$1,299.00"
    
    print("✓ Async run simulated. Collector successfully transitioned: running -> ready.")


@pytest.mark.anyio
async def test_real_service_timeout_handling(db_session):
    print("\n--- Running Bright Data Error Handling Test ---")
    
    # Setup models
    user = User(email="err_judge@hackathon.com", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    
    project = Project(name="Error Test", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    
    scraper = Scraper(project_id=project.id, name="Error Scraper", target_url="https://timeout-site.com")
    db_session.add(scraper)
    db_session.commit()

    collector = Collector(scraper_id=scraper.id, bright_data_id="c_broken", name=scraper.name)
    db_session.add(collector)
    
    schema = ExtractionSchema(
        scraper_id=scraper.id,
        fields=[{"field": "price", "description": "selling price", "type": "currency", "required": True}]
    )
    db_session.add(schema)
    db_session.commit()

    run = CollectorRun(collector_id=collector.id, status="PENDING")
    db_session.add(run)
    db_session.commit()

    # Instantiate a RealBrightDataService configured to point to a local non-responsive endpoint to trigger timeout
    real_service = RealBrightDataService(api_key="mock_key", customer_id="mock_cust")
    real_service.base_url = "http://127.0.0.1:9999" # invalid port to guarantee quick fail/timeout
    
    # Override standard global service factory for testing
    import apps.backend.app.services.worker_manager
    original_factory = apps.backend.app.services.worker_manager.get_bright_data_service
    apps.backend.app.services.worker_manager.get_bright_data_service = lambda: real_service
    
    try:
        print("Step 2: Triggering worker run expecting connection failure...")
        # Invoke worker directly
        await WorkerManager.process_collector_run(run.id)
        
        # Reload models from DB
        db_session.expire_all()
        db_session.refresh(run)
        
        # Verify status is logged as FAILED
        assert run.status == "FAILED"
        
        # Verify FailureEvent is logged with RUNTIME_DRIFT classification
        fail = db_session.query(FailureEvent).filter(FailureEvent.scraper_id == scraper.id).first()
        assert fail is not None
        assert fail.failure_type == "RUNTIME_DRIFT"
        assert "failure" in fail.description or "timed out" in fail.description
        assert fail.severity == "CRITICAL"
        
        # Verify NO selector repairs were generated (prevents LLM hallucinations on network drops)
        repair = db_session.query(RepairAttempt).filter(RepairAttempt.scraper_id == scraper.id).first()
        assert repair is None
        
        print("✓ Real error correctly logged as RUNTIME_DRIFT. Selector repair was safely blocked.")
    finally:
        # Restore service factory
        apps.backend.app.services.worker_manager.get_bright_data_service = original_factory
