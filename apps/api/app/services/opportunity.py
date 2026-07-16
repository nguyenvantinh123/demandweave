import json,math
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Signal,Opportunity,Participant
DEMAND={"demand","conditional_demand","preorder","service_need"}
SUPPLY={"supply","production_capacity","idle_asset","inventory"}
ROLE_MAP={"production_capacity":"producer","supply":"supplier","skill":"specialist","logistics_capacity":"logistics_provider","capital":"financier","demand":"buyer","conditional_demand":"buyer","preorder":"buyer"}

def score_cluster(signals,participants):
    demand=sum(s.quantity*s.confidence for s in signals if s.signal_type in DEMAND)
    supply=sum(s.quantity*s.confidence for s in signals if s.signal_type in SUPPLY)
    buyers=len({s.participant_id for s in signals if s.signal_type in DEMAND})
    roles={ROLE_MAP.get(s.signal_type) for s in signals}-{None}
    trust=sum(participants[s.participant_id].trust_score for s in signals)/max(len(signals),1)
    coverage=min(supply/max(demand,1),1)
    demand_strength=min(100,20+12*math.log10(max(demand,1))+buyers*4)
    supply_readiness=coverage*100
    completeness=min(100,len(roles)/5*100)
    confidence=sum(s.confidence for s in signals)/max(len(signals),1)*100
    novelty=min(100,len({s.signal_type for s in signals})*12+len({s.participant_id for s in signals})*3)
    coordination=max(0,100-len({s.participant_id for s in signals})*3)
    overall=.27*demand_strength+.23*supply_readiness+.15*completeness+.15*confidence+.10*novelty+.10*trust*100
    return {"demand_strength":round(demand_strength,2),"supply_readiness":round(supply_readiness,2),"capability_completeness":round(completeness,2),"confidence":round(confidence,2),"novelty":round(novelty,2),"trust":round(trust*100,2),"coordination_fit":round(coordination,2),"overall":round(min(overall,100),2),"demand":round(demand,2),"supply":round(supply,2),"roles":sorted(roles)}

def compile_for_tenant(db:Session,tenant_id:int):
    signals=db.scalars(select(Signal).where(Signal.tenant_id==tenant_id)).all()
    participants={p.id:p for p in db.scalars(select(Participant).where(Participant.tenant_id==tenant_id)).all()}
    groups=defaultdict(list)
    for s in signals:
        if s.visibility_scope=="private":continue
        groups[(s.normalized_category,s.location.lower())].append(s)
    result=[]
    for (category,loc),cluster in groups.items():
        demand=[s for s in cluster if s.signal_type in DEMAND]
        if len(demand)<2 and not any(s.verification_status=="verified" for s in demand):continue
        score=score_cluster(cluster,participants)
        required=["buyer","producer","logistics_provider","specialist","financier"]
        missing=[r for r in required if r not in score["roles"]]
        evidence=[{"signal_id":s.id,"type":s.signal_type,"confidence":s.confidence} for s in cluster]
        existing=db.scalar(select(Opportunity).where(Opportunity.tenant_id==tenant_id,Opportunity.category==category,Opportunity.location==loc.title()))
        values=dict(title=f"Emerging {category.replace('_',' ')} opportunity in {loc.title() or 'multi-location market'}",category=category,description=f"Compiled from {len(cluster)} consented economic signals.",location=loc.title(),demand_volume=score["demand"],supply_capacity=score["supply"],unit=demand[0].unit,required_roles_json=json.dumps(required),missing_resources_json=json.dumps(missing),score_json=json.dumps(score),evidence_json=json.dumps(evidence),opportunity_score=score["overall"])
        if existing:
            for k,v in values.items():setattr(existing,k,v)
            row=existing
        else: row=Opportunity(tenant_id=tenant_id,**values);db.add(row)
        db.commit();db.refresh(row);result.append(row)
    return sorted(result,key=lambda x:x.opportunity_score,reverse=True)
