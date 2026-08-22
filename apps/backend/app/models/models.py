import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from apps.backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    scrapers = relationship("Scraper", back_populates="project", cascade="all, delete-orphan")


class Scraper(Base):
    __tablename__ = "scrapers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    target_url = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, DEGRADED, BROKEN, REPAIRING
    health_score = Column(Float, default=100.0)
    current_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="scrapers")
    versions = relationship("ScraperVersion", back_populates="scraper", cascade="all, delete-orphan")
    schema_contracts = relationship("ExtractionSchema", back_populates="scraper", cascade="all, delete-orphan")
    runs = relationship("ScraperRun", back_populates="scraper", cascade="all, delete-orphan")
    failure_events = relationship("FailureEvent", back_populates="scraper", cascade="all, delete-orphan")
    repair_attempts = relationship("RepairAttempt", back_populates="scraper", cascade="all, delete-orphan")
    drift_metrics = relationship("DriftMetric", back_populates="scraper", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="scraper", cascade="all, delete-orphan")
    collector = relationship("Collector", uselist=False, back_populates="scraper", cascade="all, delete-orphan")
    memories = relationship("AgentMemory", back_populates="scraper", cascade="all, delete-orphan")


class ScraperVersion(Base):
    __tablename__ = "scraper_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    selector_logic = Column(JSON, nullable=False)  # JSON mapping field names to selectors
    status = Column(String(50), default="ACTIVE")  # ACTIVE, DEPRECATED
    deployed_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="versions")
    runs = relationship("ScraperRun", back_populates="version")


class ExtractionSchema(Base):
    __tablename__ = "extraction_schemas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    fields = Column(JSON, nullable=False)  # JSON list of dicts: name, type, required, description, examples
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="schema_contracts")


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(String(36), ForeignKey("scraper_versions.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False)  # SUCCESS, PARTIAL, FAILED
    rows_scraped = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    quality_score = Column(Float, default=100.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="runs")
    version = relationship("ScraperVersion", back_populates="runs")
    failure_events = relationship("FailureEvent", back_populates="run", cascade="all, delete-orphan")


class FailureEvent(Base):
    __tablename__ = "failure_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String(36), ForeignKey("scraper_runs.id", ondelete="CASCADE"), nullable=False)
    failure_type = Column(String(100), nullable=False)  # OUTPUT_DRIFT, SCHEMA_DRIFT, DOM_DRIFT, SEMANTIC_DRIFT, RUNTIME_DRIFT
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="CRITICAL")  # CRITICAL, WARNING
    detected_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="failure_events")
    run = relationship("ScraperRun", back_populates="failure_events")
    repair_attempts = relationship("RepairAttempt", back_populates="failure_event", cascade="all, delete-orphan")


class RepairAttempt(Base):
    __tablename__ = "repair_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    failure_event_id = Column(String(36), ForeignKey("failure_events.id", ondelete="CASCADE"), nullable=False)
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="RUNNING")  # RUNNING, SUCCESS, FAILED, PENDING_REVIEW
    old_selectors = Column(JSON, nullable=True)
    new_selectors = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="repair_attempts")
    failure_event = relationship("FailureEvent", back_populates="repair_attempts")
    candidates = relationship("RepairCandidate", back_populates="repair_attempt", cascade="all, delete-orphan")


class RepairCandidate(Base):
    __tablename__ = "repair_candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repair_attempt_id = Column(String(36), ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(255), nullable=False)
    selector = Column(String(500), nullable=False)
    strategy = Column(String(100), nullable=False)  # attribute_match, structural_match, semantic_match
    model_confidence = Column(Float, default=0.0)
    validation_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    coverage_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    status = Column(String(50), default="PENDING")  # PENDING, VALIDATED, SELECTED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

    repair_attempt = relationship("RepairAttempt", back_populates="candidates")


class DriftMetric(Base):
    __tablename__ = "drift_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    metric_type = Column(String(100), nullable=False)  # output_count, latency, field_presence, dom_changes
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="drift_metrics")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)  # REPAIR_PROPOSAL_GENERATED, AUTO_DEPLOYED, MANUALLY_APPROVED, ROLLBACK
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="audit_logs")


class Collector(Base):
    __tablename__ = "collectors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    bright_data_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="ACTIVE")
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="collector")
    versions = relationship("CollectorVersion", back_populates="collector", cascade="all, delete-orphan")
    runs = relationship("CollectorRun", back_populates="collector", cascade="all, delete-orphan")


class CollectorVersion(Base):
    __tablename__ = "collector_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collector_id = Column(String(36), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    configuration = Column(JSON, nullable=False)  # JSON configuration including selectors
    status = Column(String(50), default="ACTIVE")  # ACTIVE, DEPRECATED
    deployment_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    collector = relationship("Collector", back_populates="versions")


class CollectorRun(Base):
    __tablename__ = "collector_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collector_id = Column(String(36), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = Column(String(255), unique=True, index=True, nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    rows = Column(Integer, default=0)
    latency = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    collector = relationship("Collector", back_populates="runs")


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_id = Column(String(36), ForeignKey("scrapers.id", ondelete="CASCADE"), nullable=False)
    failure_pattern = Column(String(255), nullable=False)  # e.g., "DOM_DRIFT:price"
    solution = Column(Text, nullable=False)  # JSON selector solution
    success_rate = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    scraper = relationship("Scraper", back_populates="memories")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    plan_tier = Column(String(50), default="growth")  # starter, growth, scale, enterprise
    max_collectors = Column(Integer, default=25)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("TenantMembership", back_populates="tenant", cascade="all, delete-orphan")
    slack_integrations = relationship("SlackIntegration", back_populates="tenant", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEndpoint", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    heuristic_rules = relationship("HeuristicRule", back_populates="tenant", cascade="all, delete-orphan")


class TenantMembership(Base):
    __tablename__ = "tenant_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="operator")  # owner, admin, operator, viewer
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="members")
    user = relationship("User")


class SlackIntegration(Base):
    __tablename__ = "slack_integrations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    team_name = Column(String(255), nullable=True)
    channel_name = Column(String(255), nullable=False)
    webhook_url = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)  # 1 = True, 0 = False
    notify_on_failure = Column(Integer, default=1)
    notify_on_recovery = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="slack_integrations")


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    secret = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)
    events = Column(JSON, default=list)  # ["failure.detected", "repair.completed", "collector.deployed"]
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="webhooks")


class HeuristicRule(Base):
    __tablename__ = "heuristic_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    domain_pattern = Column(String(255), nullable=False)  # e.g., "*.shopify.com" or "laptops-r-us.com"
    target_field = Column(String(100), nullable=False)
    pattern_type = Column(String(50), default="attribute_shift")  # attribute_shift, class_alias, wrapper_collapse
    source_pattern = Column(String(255), nullable=False)
    target_pattern = Column(String(255), nullable=False)
    confidence_score = Column(Float, default=95.0)
    times_applied = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="heuristic_rules")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)  # e.g., "wg_live_abc..."
    is_active = Column(Integer, default=1)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="api_keys")

