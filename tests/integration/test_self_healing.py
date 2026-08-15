import os
import sys

# Override database URL for tests to a shared local SQLite file so imports and agent nodes use the same DB
TEST_DB_FILE = "webguardian_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_FILE}"

import pytest
from sqlalchemy import create_engine
from apps.backend.app.core.database import Base, engine, SessionLocal
from apps.backend.app.models.models import (
    User, Project, Scraper, ScraperVersion, ExtractionSchema,
    ScraperRun, FailureEvent, RepairAttempt, RepairCandidate, AuditLog
)
from apps.backend.app.services.scraper_executor import ScraperExecutor

@pytest.fixture(name="db_session")
def fixture_db_session():
    # Ensure database tables are created in the test file db
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up database tables
        Base.metadata.drop_all(bind=engine)
        # Safely remove the test database file
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except Exception:
                pass

def test_self_healing_after_dom_change(db_session):
    print("\n--- Running Core Self-Healing Test ---")
    
    # 1. Setup User and Project
    test_user = User(email="judge@hackathon.com", hashed_password="hashed_judge_password", full_name="Hackathon Judge")
    db_session.add(test_user)
    db_session.commit()
    
    test_project = Project(name="Laptop Price Monitor", owner_id=test_user.id)
    db_session.add(test_project)
    db_session.commit()
    
    # 2. Setup Scraper with Extraction Schema (Semantic Contract)
    scraper = Scraper(
        project_id=test_project.id,
        name="Laptop Prices Scraper",
        target_url="https://laptops-r-us.com/products",
        status="ACTIVE"
    )
    db_session.add(scraper)
    db_session.commit()
    
    # Define semantic contract for extraction
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
    db_session.add(schema)
    db_session.commit()
    
    # 3. Simulate Scraper Run 1: Normal Website (HTML v1)
    print("Step 1: Running Scraper on original HTML v1...")
    res_v1 = ScraperExecutor.run_scraper_pipeline(db_session, scraper.id, use_v2_dom=False)
    
    assert res_v1["initial_run"]["status"] == "SUCCESS"
    assert res_v1["initial_run"]["rows_scraped"] == 3
    assert res_v1["self_healing_triggered"] is False
    assert res_v1["health_score"] == 100.0
    
    # Verify Scraper Version v1 exists and is active
    v1 = db_session.query(ScraperVersion).filter(ScraperVersion.scraper_id == scraper.id).first()
    assert v1 is not None
    assert v1.version_number == 1
    assert v1.selector_logic == {"price": ".price"}
    assert v1.status == "ACTIVE"
    assert scraper.current_version_id == v1.id
    
    print("✓ Initial run successful. Extracted 3 laptops with '.price' class.")

    # 4. Simulate Scraper Run 2: Website Redesigns (HTML v2)
    # The '.price' element has shifted to '<span data-testid="price">'
    print("\nStep 2: Triggering website structure change (HTML v2) and running scraper...")
    res_v2 = ScraperExecutor.run_scraper_pipeline(db_session, scraper.id, use_v2_dom=True)
    
    # The initial run should fail due to missing required price field
    assert res_v2["initial_run"]["status"] == "FAILED"
    assert res_v2["self_healing_triggered"] is True
    assert res_v2["agent_decision"] == "AUTO_DEPLOY"
    assert res_v2["agent_confidence"] > 90.0
    
    # Verify Failure Event was recorded
    fail_event = db_session.query(FailureEvent).filter(FailureEvent.scraper_id == scraper.id).first()
    assert fail_event is not None
    assert fail_event.failure_type == "DOM_DRIFT"
    assert fail_event.severity == "CRITICAL"
    
    # Verify Repair Attempt was created and successfully processed
    repair = db_session.query(RepairAttempt).filter(RepairAttempt.scraper_id == scraper.id).first()
    assert repair is not None
    assert repair.status == "SUCCESS"
    assert repair.new_selectors == {"price": "[data-testid='price']"}
    
    # Verify Repair Candidates were generated and evaluated in sandbox
    candidates = db_session.query(RepairCandidate).filter(RepairCandidate.repair_attempt_id == repair.id).all()
    assert len(candidates) >= 3
    
    selected_cand = next(c for c in candidates if c.status == "SELECTED")
    assert selected_cand.selector == "[data-testid='price']"
    assert selected_cand.strategy == "attribute_match"
    assert selected_cand.final_score > 90.0
    
    # Verify Version Control deployed new version
    v2 = db_session.query(ScraperVersion).filter(
        ScraperVersion.scraper_id == scraper.id,
        ScraperVersion.version_number == 2
    ).first()
    assert v2 is not None
    assert v2.status == "ACTIVE"
    assert v2.selector_logic == {"price": "[data-testid='price']"}
    
    # Verify v1 is now deprecated
    db_session.refresh(v1)
    assert v1.status == "DEPRECATED"
    
    # Verify Scraper updated current version
    db_session.refresh(scraper)
    assert scraper.current_version_id == v2.id
    assert scraper.status == "ACTIVE"
    
    # Verify Audit Logs were stored
    audit_logs = db_session.query(AuditLog).filter(AuditLog.scraper_id == scraper.id).all()
    assert len(audit_logs) >= 2
    assert any(log.event_type == "REPAIR_PROPOSAL_GENERATED" for log in audit_logs)
    assert any(log.event_type == "AUTO_DEPLOYED" for log in audit_logs)
    
    # Verify Recovery Run succeeded
    assert res_v2["recovered"] is True
    assert res_v2["recovery_run"]["status"] == "SUCCESS"
    assert res_v2["recovery_run"]["rows_scraped"] == 3
    assert res_v2["recovery_run"]["version_number"] == 2
    
    # Verify health score is restored (should be back to high status)
    assert res_v2["health_score"] > 80.0
    
    print("✓ Pipeline healed autonomously!")
    print(f"  Old Selector: {v1.selector_logic['price']}")
    print(f"  New Selector: {v2.selector_logic['price']}")
    print(f"  Confidence: {selected_cand.final_score}%")
    print(f"  Rows Recovered: {res_v2['recovery_run']['rows_scraped']}")
    print(f"  New Health Score: {res_v2['health_score']}%")
    print("--- Integration Test Successful ---")
