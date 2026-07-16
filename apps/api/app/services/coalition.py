import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Participant,Signal,Coalition,CoalitionMember,Opportunity
ROLE_TYPES={"buyer":{"demand","conditional_demand","preorder"},"producer":{"production_capacity"},"supplier":{"supply","inventory"},"specialist":{"skill"},"logistics_provider":{"logistics_capacity"},"financier":{"capital"}}
def form_greedy(db:Session,opp:Opportunity):
    signals=db.scalars(select(Signal).where(Signal.tenant_id==opp.tenant_id,Signal.normalized_category.in_([opp.category,"logistics","design","capital"]))).all()
    participants={p.id:p for p in db.scalars(select(Participant).where(Participant.tenant_id==opp.tenant_id)).all()}
    selected=[];covered=set()
    for role,types in ROLE_TYPES.items():
        candidates=[]
        for s in signals:
            if s.signal_type in types and s.participant_id in participants:
                p=participants[s.participant_id]
                value=.5*p.trust_score+.2*p.delivery_score+.2*p.quality_score+.1*s.confidence
                candidates.append((value,p,s))
        if candidates:
            _,p,s=max(candidates,key=lambda x:x[0]);selected.append((p,role,s));covered.add(role)
    required=json.loads(opp.required_roles_json);missing=[r for r in required if r not in covered]
    coverage=len(set(required)-set(missing))/max(len(required),1)*100
    trust=sum(x[0].trust_score for x in selected)/max(len(selected),1)*100
    coalition=Coalition(tenant_id=opp.tenant_id,opportunity_id=opp.id,algorithm="greedy-v1",coverage_score=round(coverage,2),trust_score=round(trust,2),missing_roles_json=json.dumps(missing));db.add(coalition);db.commit();db.refresh(coalition)
    share=1/max(len(selected),1)
    for p,role,s in selected:
        db.add(CoalitionMember(coalition_id=coalition.id,participant_id=p.id,role=role,contribution=s.quantity,benefit_share=round(share,4),rationale=f"Selected for {role}: trust={p.trust_score:.2f}, signal confidence={s.confidence:.2f}"))
    db.commit();return coalition
