from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now(): return datetime.utcnow()

class Tenant(Base):
    __tablename__="tenants"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(200))
    slug: Mapped[str]=mapped_column(String(100),unique=True,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class TenantMember(Base):
    __tablename__="tenant_members"
    __table_args__=(UniqueConstraint("tenant_id","user_id"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    role: Mapped[str]=mapped_column(String(40),default="participant")

class Participant(Base):
    __tablename__="participants"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    participant_type: Mapped[str]=mapped_column(String(50),index=True)
    display_name: Mapped[str]=mapped_column(String(200))
    legal_name: Mapped[str]=mapped_column(String(250),default="")
    location: Mapped[str]=mapped_column(String(200),default="",index=True)
    latitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    longitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    verification_level: Mapped[str]=mapped_column(String(30),default="unverified")
    trust_score: Mapped[float]=mapped_column(Float,default=0.5)
    response_score: Mapped[float]=mapped_column(Float,default=0.5)
    delivery_score: Mapped[float]=mapped_column(Float,default=0.5)
    quality_score: Mapped[float]=mapped_column(Float,default=0.5)
    financial_capacity: Mapped[float]=mapped_column(Float,default=0)
    contact_json: Mapped[str]=mapped_column(Text,default="{}")
    capabilities_json: Mapped[str]=mapped_column(Text,default="[]")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=now,onupdate=now)

class Signal(Base):
    __tablename__="signals"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    participant_id: Mapped[int]=mapped_column(ForeignKey("participants.id"),index=True)
    signal_type: Mapped[str]=mapped_column(String(50),index=True)
    title: Mapped[str]=mapped_column(String(300))
    natural_language_input: Mapped[str]=mapped_column(Text,default="")
    normalized_category: Mapped[str]=mapped_column(String(120),index=True)
    attributes_json: Mapped[str]=mapped_column(Text,default="{}")
    quantity: Mapped[float]=mapped_column(Float,default=0)
    unit: Mapped[str]=mapped_column(String(40),default="unit")
    price_min: Mapped[float]=mapped_column(Float,default=0)
    price_max: Mapped[float]=mapped_column(Float,default=0)
    currency: Mapped[str]=mapped_column(String(10),default="VND")
    location: Mapped[str]=mapped_column(String(200),default="",index=True)
    confidence: Mapped[float]=mapped_column(Float,default=0.7)
    verification_status: Mapped[str]=mapped_column(String(30),default="unverified")
    visibility_scope: Mapped[str]=mapped_column(String(30),default="aggregated")
    source: Mapped[str]=mapped_column(String(50),default="manual")
    expires_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class Opportunity(Base):
    __tablename__="opportunities"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    title: Mapped[str]=mapped_column(String(300))
    category: Mapped[str]=mapped_column(String(120),index=True)
    description: Mapped[str]=mapped_column(Text,default="")
    location: Mapped[str]=mapped_column(String(200),default="")
    demand_volume: Mapped[float]=mapped_column(Float,default=0)
    supply_capacity: Mapped[float]=mapped_column(Float,default=0)
    unit: Mapped[str]=mapped_column(String(40),default="unit")
    required_roles_json: Mapped[str]=mapped_column(Text,default="[]")
    missing_resources_json: Mapped[str]=mapped_column(Text,default="[]")
    score_json: Mapped[str]=mapped_column(Text,default="{}")
    evidence_json: Mapped[str]=mapped_column(Text,default="[]")
    opportunity_score: Mapped[float]=mapped_column(Float,default=0,index=True)
    status: Mapped[str]=mapped_column(String(30),default="hypothesis")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=now,onupdate=now)

class Coalition(Base):
    __tablename__="coalitions"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    opportunity_id: Mapped[int]=mapped_column(ForeignKey("opportunities.id"),index=True)
    algorithm: Mapped[str]=mapped_column(String(40),default="greedy")
    coverage_score: Mapped[float]=mapped_column(Float,default=0)
    trust_score: Mapped[float]=mapped_column(Float,default=0)
    missing_roles_json: Mapped[str]=mapped_column(Text,default="[]")
    status: Mapped[str]=mapped_column(String(30),default="proposed")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class CoalitionMember(Base):
    __tablename__="coalition_members"
    id: Mapped[int]=mapped_column(primary_key=True)
    coalition_id: Mapped[int]=mapped_column(ForeignKey("coalitions.id"),index=True)
    participant_id: Mapped[int]=mapped_column(ForeignKey("participants.id"),index=True)
    role: Mapped[str]=mapped_column(String(50))
    contribution: Mapped[float]=mapped_column(Float,default=0)
    benefit_share: Mapped[float]=mapped_column(Float,default=0)
    rationale: Mapped[str]=mapped_column(Text,default="")

class Simulation(Base):
    __tablename__="simulations"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    opportunity_id: Mapped[int]=mapped_column(ForeignKey("opportunities.id"),index=True)
    assumptions_json: Mapped[str]=mapped_column(Text)
    results_json: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class Experiment(Base):
    __tablename__="experiments"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    opportunity_id: Mapped[int]=mapped_column(ForeignKey("opportunities.id"),index=True)
    title: Mapped[str]=mapped_column(String(250))
    hypothesis: Mapped[str]=mapped_column(Text)
    success_metric: Mapped[str]=mapped_column(String(250))
    failure_metric: Mapped[str]=mapped_column(String(250),default="")
    budget_limit: Mapped[float]=mapped_column(Float,default=0)
    time_limit_days: Mapped[int]=mapped_column(Integer,default=14)
    action_plan_json: Mapped[str]=mapped_column(Text,default="[]")
    status: Mapped[str]=mapped_column(String(30),default="draft")
    observations_json: Mapped[str]=mapped_column(Text,default="[]")
    result_json: Mapped[str]=mapped_column(Text,default="{}")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class Mandate(Base):
    __tablename__="mandates"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    opportunity_id: Mapped[int|None]=mapped_column(ForeignKey("opportunities.id"),nullable=True)
    allowed_actions_json: Mapped[str]=mapped_column(Text)
    forbidden_actions_json: Mapped[str]=mapped_column(Text,default="[]")
    approved_participants_json: Mapped[str]=mapped_column(Text,default="[]")
    budget_limit: Mapped[float]=mapped_column(Float,default=0)
    spent_amount: Mapped[float]=mapped_column(Float,default=0)
    max_actions: Mapped[int]=mapped_column(Integer,default=20)
    action_count: Mapped[int]=mapped_column(Integer,default=0)
    expires_at: Mapped[datetime]=mapped_column(DateTime)
    signature: Mapped[str]=mapped_column(String(128))
    revoked: Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class LedgerEvent(Base):
    __tablename__="ledger_events"
    id: Mapped[int]=mapped_column(primary_key=True)
    tenant_id: Mapped[int]=mapped_column(ForeignKey("tenants.id"),index=True)
    aggregate_type: Mapped[str]=mapped_column(String(60))
    aggregate_id: Mapped[int]=mapped_column(Integer)
    event_type: Mapped[str]=mapped_column(String(80),index=True)
    payload_json: Mapped[str]=mapped_column(Text)
    actor_type: Mapped[str]=mapped_column(String(30),default="user")
    actor_id: Mapped[int|None]=mapped_column(Integer,nullable=True)
    previous_hash: Mapped[str]=mapped_column(String(64),default="")
    current_hash: Mapped[str]=mapped_column(String(64),unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
