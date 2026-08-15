import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from apps.backend.app.models.models import Scraper, ScraperRun, DriftMetric, FailureEvent

logger = logging.getLogger("webguardian")

class DriftEngine:
    @staticmethod
    def calculate_health_score(
        extraction_quality: float,   # 0 - 100
        success_rate: float,         # 0 - 100
        schema_completeness: float,  # 0 - 100
        latency_ms: float,           # average latency in ms
        has_recent_repairs: bool
    ) -> float:
        """
        Calculates health score using formula:
        Health = 35% extraction_quality + 25% success_rate + 15% schema_completeness + 10% latency_score + 15% structural_stability
        """
        # Latency score: 100 base, drops by 10 points for every 1000ms above 1500ms (min 0)
        if latency_ms <= 1500:
            latency_score = 100.0
        else:
            excess = latency_ms - 1500
            latency_score = max(0.0, 100.0 - (excess / 100.0))

        # Structural stability score: 100, drops to 70 if repaired recently
        stability_score = 70.0 if has_recent_repairs else 100.0

        health = (
            (0.35 * extraction_quality) +
            (0.25 * success_rate) +
            (0.15 * schema_completeness) +
            (0.10 * latency_score) +
            (0.15 * stability_score)
        )
        return round(health, 2)

    @staticmethod
    def evaluate_run(
        db: Session,
        scraper: Scraper,
        run: ScraperRun,
        extracted_data: List[Dict[str, Any]],
        schema_fields: List[Dict[str, Any]]
    ) -> Tuple[bool, List[FailureEvent]]:
        """
        Audits current run against previous successful baseline metrics.
        Returns:
            should_heal: bool
            failures: List[FailureEvent]
        """
        failures = []
        should_heal = False

        # 1. Fetch historical successful runs for comparison
        prev_successful_runs = db.query(ScraperRun).filter(
            ScraperRun.scraper_id == scraper.id,
            ScraperRun.status == "SUCCESS"
        ).order_by(ScraperRun.created_at.desc())
        
        # Take up to 10 previous runs
        past_runs = prev_successful_runs.limit(10).all()
        
        # Calculate baselines
        avg_rows = sum(r.rows_scraped for r in past_runs) / len(past_runs) if past_runs else None
        avg_latency = sum(r.latency_ms for r in past_runs) / len(past_runs) if past_runs else None

        # 2. Check for Output Drift (Row Count Drop)
        row_count = len(extracted_data)
        
        # Log drift metrics
        db.add(DriftMetric(scraper_id=scraper.id, metric_type="output_count", metric_value=float(row_count)))
        db.add(DriftMetric(scraper_id=scraper.id, metric_type="latency", metric_value=float(run.latency_ms)))

        if avg_rows is not None and avg_rows > 0:
            drop_percentage = (avg_rows - row_count) / avg_rows
            if drop_percentage >= 0.30:  # 30% drop is a Warning, 90% is Critical
                severity = "CRITICAL" if drop_percentage >= 0.80 or row_count == 0 else "WARNING"
                failure_type = "OUTPUT_DRIFT"
                desc = f"Output drifted: Row count dropped by {round(drop_percentage * 100, 1)}% (Baseline: {int(avg_rows)} rows, Current: {row_count} rows)"
                
                failures.append(FailureEvent(
                    scraper_id=scraper.id,
                    run_id=run.id,
                    failure_type=failure_type,
                    description=desc,
                    severity=severity
                ))
                if severity == "CRITICAL":
                    should_heal = True

        # 3. Check for Schema Drift / DOM Drift (Field presence & types)
        total_fields_expected = len(schema_fields)
        missing_fields = []
        required_missing = False
        
        # Track presence rate
        presence_sum = 0.0
        
        for field in schema_fields:
            name = field["field"]
            required = field.get("required", False)
            
            # Count how many times field is extracted and not None/empty
            non_empty_count = sum(1 for row in extracted_data if row.get(name) is not None and str(row.get(name)).strip() != "")
            
            presence_rate = non_empty_count / row_count if row_count > 0 else 0.0
            presence_sum += presence_rate
            
            db.add(DriftMetric(scraper_id=scraper.id, metric_type=f"field_presence_{name}", metric_value=presence_rate))
            
            if presence_rate == 0.0:
                missing_fields.append(name)
                if required:
                    required_missing = True

        # Calculate completeness and quality
        schema_completeness = ((total_fields_expected - len(missing_fields)) / total_fields_expected) * 100.0 if total_fields_expected > 0 else 100.0
        extraction_quality = (presence_sum / total_fields_expected) * 100.0 if total_fields_expected > 0 else 100.0

        run.quality_score = extraction_quality

        # Record field-level drift failures
        if missing_fields:
            severity = "CRITICAL" if required_missing or row_count == 0 else "WARNING"
            desc = f"Schema fields missing: {', '.join(missing_fields)}"
            failures.append(FailureEvent(
                scraper_id=scraper.id,
                run_id=run.id,
                failure_type="SCHEMA_DRIFT" if not required_missing else "DOM_DRIFT",
                description=desc,
                severity=severity
            ))
            if severity == "CRITICAL":
                should_heal = True

        # 4. Check Runtime Drift (Latency climbs)
        if avg_latency is not None and avg_latency > 0:
            latency_increase = (run.latency_ms - avg_latency) / avg_latency
            if latency_increase >= 1.0:  # Latency doubled
                failures.append(FailureEvent(
                    scraper_id=scraper.id,
                    run_id=run.id,
                    failure_type="RUNTIME_DRIFT",
                    description=f"Latency surged by {round(latency_increase * 100, 1)}% (Baseline: {int(avg_latency)}ms, Current: {run.latency_ms}ms)",
                    severity="WARNING"
                ))

        # Save all failures to db
        for fail in failures:
            db.add(fail)

        # 5. Compute new health score
        # Fetch success rate in last 20 runs
        recent_runs = db.query(ScraperRun).filter(
            ScraperRun.scraper_id == scraper.id
        ).order_by(ScraperRun.created_at.desc()).limit(20).all()
        
        success_runs = sum(1 for r in recent_runs if r.status == "SUCCESS")
        success_rate = (success_runs / len(recent_runs)) * 100.0 if recent_runs else 100.0
        
        # Check if there was any successful repair in the last 7 days
        has_recent_repairs = scraper.status == "DEGRADED" or scraper.status == "REPAIRING"

        new_health = DriftEngine.calculate_health_score(
            extraction_quality=extraction_quality,
            success_rate=success_rate,
            schema_completeness=schema_completeness,
            latency_ms=run.latency_ms,
            has_recent_repairs=has_recent_repairs
        )
        
        scraper.health_score = new_health
        db.commit()

        return should_heal, failures
