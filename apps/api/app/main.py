import json,re
from datetime import datetime
from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import Base,engine,get_db
from .models import *
from .schemas import *
from .security import hash_password,verify_password,create_token,current_context,require_roles
from .services.normalize import parse_natural_signal
from .services.opportunity import compile_for_tenant
from .services.coalition import form_greedy
from .services.simulation import simulate
from .services.ledger import append_event,verify_chain
from .services.mandates import sign,mandate_data,authorize
from .services.privacy import public_signal

Base.metadata.create_all(bind=engine)
app=FastAPI(title="DemandWeave",version="1.0.0",description="Human Opportunity Compiler")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',')],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

def slugify(v):return re.sub(r"[^a-z0-9]+","-",v.lower()).strip("-")

@app.get("/health")
def health():return {"ok":True,"version":"1.0.0"}
@app.get("/.well-known/agent-card.json")
def agent_card():return {"name":"DemandWeave Human Opportunity Compiler","version":"1.0.0","capabilities":["signal-intake","opportunity-compilation","coalition-formation","risk-simulation","bounded-mandates","learning-ledger"],"authorization":"JWT plus signed mandate for external actions"}

@app.post("/api/v1/auth/register",response_model=TokenOut)
def register(data:RegisterIn,db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email.lower())):raise HTTPException(409,"Email already exists")
    slug=slugify(data.tenant_name);base=slug;i=1
    while db.scalar(select(Tenant).where(Tenant.slug==slug)):i+=1;slug=f"{base}-{i}"
    tenant=Tenant(name=data.tenant_name,slug=slug);user=User(email=data.email.lower(),password_hash=hash_password(data.password));db.add_all([tenant,user]);db.flush();member=TenantMember(tenant_id=tenant.id,user_id=user.id,role="owner");db.add(member);db.commit()
    append_event(db,tenant.id,"tenant",tenant.id,"tenant_registered",{"email":user.email},user.id)
    return TokenOut(access_token=create_token(user.id,tenant.id,"owner"),tenant_id=tenant.id)
@app.post("/api/v1/auth/login",response_model=TokenOut)
def login(data:LoginIn,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==data.email.lower()))
    if not user or not verify_password(data.password,user.password_hash):raise HTTPException(401,"Invalid credentials")
    member=db.scalar(select(TenantMember).where(TenantMember.user_id==user.id))
    return TokenOut(access_token=create_token(user.id,member.tenant_id,member.role),tenant_id=member.tenant_id)
@app.get("/api/v1/auth/me")
def me(ctx=Depends(current_context)):return {"id":ctx["user"].id,"email":ctx["user"].email,"tenant_id":ctx["tenant_id"],"role":ctx["role"]}

@app.post("/api/v1/participants",response_model=ParticipantOut)
def create_participant(data:ParticipantIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    d=data.model_dump();contact=d.pop("contact");caps=d.pop("capabilities");row=Participant(tenant_id=ctx["tenant_id"],**d,contact_json=json.dumps(contact),capabilities_json=json.dumps(caps));db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"participant",row.id,"participant_created",{"type":row.participant_type},ctx["user"].id);return ParticipantOut(**data.model_dump(),id=row.id)
@app.get("/api/v1/participants")
def list_participants(ctx=Depends(current_context),db:Session=Depends(get_db)):
    rows=db.scalars(select(Participant).where(Participant.tenant_id==ctx["tenant_id"]).order_by(Participant.id)).all();return [{"id":r.id,"display_name":r.display_name,"participant_type":r.participant_type,"location":r.location,"trust_score":r.trust_score,"capabilities":json.loads(r.capabilities_json)} for r in rows]

@app.post("/api/v1/signals")
def create_signal(data:SignalIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    p=db.get(Participant,data.participant_id)
    if not p or p.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Participant not found")
    d=data.model_dump();attrs=d.pop("attributes");row=Signal(tenant_id=ctx["tenant_id"],**d,attributes_json=json.dumps(attrs,ensure_ascii=False));db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"signal",row.id,"signal_created",{"type":row.signal_type,"category":row.normalized_category},ctx["user"].id);return {"id":row.id,"parsed":d}
@app.post("/api/v1/signals/natural")
def create_natural_signal(data:NaturalSignalIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    p=db.get(Participant,data.participant_id)
    if not p or p.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Participant not found")
    parsed=parse_natural_signal(data.text);row=Signal(tenant_id=ctx["tenant_id"],participant_id=p.id,natural_language_input=data.text,visibility_scope=data.visibility_scope,price_min=0,price_max=0,currency="VND",verification_status="unverified",source="natural-language",attributes_json=json.dumps(parsed.pop("attributes")),**parsed);db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"signal",row.id,"natural_signal_parsed",{"type":row.signal_type,"category":row.normalized_category},ctx["user"].id);return {"id":row.id,"parsed":{"signal_type":row.signal_type,"category":row.normalized_category,"quantity":row.quantity,"location":row.location,"confidence":row.confidence}}
@app.get("/api/v1/signals")
def list_signals(ctx=Depends(current_context),db:Session=Depends(get_db)):
    rows=db.scalars(select(Signal).where(Signal.tenant_id==ctx["tenant_id"]).order_by(Signal.id.desc())).all();return [public_signal(r) for r in rows]

@app.post("/api/v1/opportunities/compile")
def compile_opportunities(ctx=Depends(current_context),db:Session=Depends(get_db)):
    rows=compile_for_tenant(db,ctx["tenant_id"])
    for r in rows:append_event(db,ctx["tenant_id"],"opportunity",r.id,"opportunity_compiled",{"score":r.opportunity_score},ctx["user"].id)
    return [{"id":r.id,"title":r.title,"score":r.opportunity_score} for r in rows]
@app.get("/api/v1/opportunities")
def list_opportunities(ctx=Depends(current_context),db:Session=Depends(get_db)):
    rows=db.scalars(select(Opportunity).where(Opportunity.tenant_id==ctx["tenant_id"]).order_by(Opportunity.opportunity_score.desc())).all();return [{"id":r.id,"title":r.title,"category":r.category,"location":r.location,"demand_volume":r.demand_volume,"supply_capacity":r.supply_capacity,"score":r.opportunity_score,"scores":json.loads(r.score_json),"missing_resources":json.loads(r.missing_resources_json),"status":r.status} for r in rows]
@app.get("/api/v1/opportunities/{opportunity_id}")
def opportunity_detail(opportunity_id:int,ctx=Depends(current_context),db:Session=Depends(get_db)):
    r=db.get(Opportunity,opportunity_id)
    if not r or r.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Opportunity not found")
    return {"id":r.id,"title":r.title,"description":r.description,"score":r.opportunity_score,"scores":json.loads(r.score_json),"evidence":json.loads(r.evidence_json),"required_roles":json.loads(r.required_roles_json),"missing_resources":json.loads(r.missing_resources_json)}
@app.post("/api/v1/opportunities/{opportunity_id}/coalitions")
def create_coalition(opportunity_id:int,ctx=Depends(current_context),db:Session=Depends(get_db)):
    o=db.get(Opportunity,opportunity_id)
    if not o or o.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Opportunity not found")
    c=form_greedy(db,o);members=db.scalars(select(CoalitionMember).where(CoalitionMember.coalition_id==c.id)).all();append_event(db,ctx["tenant_id"],"coalition",c.id,"coalition_proposed",{"coverage":c.coverage_score},ctx["user"].id);return {"id":c.id,"algorithm":c.algorithm,"coverage_score":c.coverage_score,"trust_score":c.trust_score,"missing_roles":json.loads(c.missing_roles_json),"members":[{"participant_id":m.participant_id,"role":m.role,"benefit_share":m.benefit_share,"rationale":m.rationale} for m in members]}
@app.post("/api/v1/opportunities/{opportunity_id}/simulate")
def run_simulation(opportunity_id:int,data:SimulationIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    o=db.get(Opportunity,opportunity_id)
    if not o or o.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Opportunity not found")
    result=simulate(o.demand_volume,data);row=Simulation(tenant_id=ctx["tenant_id"],opportunity_id=o.id,assumptions_json=data.model_dump_json(),results_json=json.dumps(result));db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"simulation",row.id,"simulation_completed",result,ctx["user"].id);return {"id":row.id,**result}

@app.post("/api/v1/experiments")
def create_experiment(data:ExperimentIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    o=db.get(Opportunity,data.opportunity_id)
    if not o or o.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Opportunity not found")
    d=data.model_dump();plan=d.pop("action_plan");row=Experiment(tenant_id=ctx["tenant_id"],**d,action_plan_json=json.dumps(plan));db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"experiment",row.id,"experiment_created",{"budget":row.budget_limit},ctx["user"].id);return {"id":row.id,"status":row.status}
@app.post("/api/v1/experiments/{experiment_id}/start")
def start_experiment(experiment_id:int,ctx=Depends(current_context),db:Session=Depends(get_db)):
    e=db.get(Experiment,experiment_id)
    if not e or e.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Experiment not found")
    e.status="running";db.commit();append_event(db,ctx["tenant_id"],"experiment",e.id,"experiment_started",{},ctx["user"].id);return {"id":e.id,"status":e.status}
@app.post("/api/v1/experiments/{experiment_id}/complete")
def complete_experiment(experiment_id:int,data:ExperimentResultIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    e=db.get(Experiment,experiment_id)
    if not e or e.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Experiment not found")
    e.status="completed";e.observations_json=json.dumps(data.observations);e.result_json=json.dumps(data.result);db.commit();append_event(db,ctx["tenant_id"],"experiment",e.id,"experiment_completed",data.result,ctx["user"].id);return {"id":e.id,"status":e.status,"learning":{"forecast_error":data.result.get("forecast_error"),"recommendation":"Recompile opportunities with measured conversion and cost data."}}

@app.post("/api/v1/mandates")
def create_mandate(data:MandateIn,ctx=Depends(require_roles("owner","administrator")),db:Session=Depends(get_db)):
    if data.expires_at<=datetime.utcnow():raise HTTPException(400,"Expiry must be in the future")
    row=Mandate(tenant_id=ctx["tenant_id"],opportunity_id=data.opportunity_id,allowed_actions_json=json.dumps(data.allowed_actions),forbidden_actions_json=json.dumps(data.forbidden_actions),approved_participants_json=json.dumps(data.approved_participants),budget_limit=data.budget_limit,max_actions=data.max_actions,expires_at=data.expires_at,signature="");row.signature=sign(mandate_data(row));db.add(row);db.commit();db.refresh(row);append_event(db,ctx["tenant_id"],"mandate",row.id,"mandate_signed",{"budget":row.budget_limit},ctx["user"].id);return {"id":row.id,"signature":row.signature}
@app.post("/api/v1/mandates/{mandate_id}/actions")
def execute_mandate_action(mandate_id:int,data:MandateActionIn,ctx=Depends(current_context),db:Session=Depends(get_db)):
    m=db.get(Mandate,mandate_id)
    if not m or m.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Mandate not found")
    ok,reason=authorize(m,data.action,data.amount,data.participant_id)
    if not ok:raise HTTPException(403,reason)
    m.action_count+=1;m.spent_amount+=data.amount;db.commit();append_event(db,ctx["tenant_id"],"mandate",m.id,"mandated_action_recorded",data.model_dump(),ctx["user"].id,"agent");return {"authorized":True,"action_count":m.action_count,"spent_amount":m.spent_amount}
@app.post("/api/v1/mandates/{mandate_id}/revoke")
def revoke_mandate(mandate_id:int,ctx=Depends(require_roles("owner","administrator")),db:Session=Depends(get_db)):
    m=db.get(Mandate,mandate_id)
    if not m or m.tenant_id!=ctx["tenant_id"]:raise HTTPException(404,"Mandate not found")
    m.revoked=True;db.commit();append_event(db,ctx["tenant_id"],"mandate",m.id,"mandate_revoked",{},ctx["user"].id);return {"revoked":True}
@app.get("/api/v1/ledger/verify")
def ledger(ctx=Depends(current_context),db:Session=Depends(get_db)):return verify_chain(db,ctx["tenant_id"])
@app.get("/api/v1/dashboard")
def dashboard(ctx=Depends(current_context),db:Session=Depends(get_db)):
    def count(model):return len(db.scalars(select(model).where(model.tenant_id==ctx["tenant_id"])).all())
    opps=db.scalars(select(Opportunity).where(Opportunity.tenant_id==ctx["tenant_id"])).all()
    return {"participants":count(Participant),"signals":count(Signal),"opportunities":len(opps),"coalitions":count(Coalition),"experiments":count(Experiment),"average_opportunity_score":round(sum(o.opportunity_score for o in opps)/max(len(opps),1),2),"ledger":verify_chain(db,ctx["tenant_id"])}
