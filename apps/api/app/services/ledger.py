import hashlib,json
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import LedgerEvent

def append_event(db:Session,tenant_id:int,aggregate_type:str,aggregate_id:int,event_type:str,payload:dict,actor_id:int|None=None,actor_type:str="user"):
    prev=db.scalar(select(LedgerEvent).where(LedgerEvent.tenant_id==tenant_id).order_by(LedgerEvent.id.desc()))
    previous_hash=prev.current_hash if prev else ""
    canonical=json.dumps({"tenant_id":tenant_id,"aggregate_type":aggregate_type,"aggregate_id":aggregate_id,"event_type":event_type,"payload":payload,"actor_type":actor_type,"actor_id":actor_id,"previous_hash":previous_hash},sort_keys=True,separators=(",",":"),ensure_ascii=False)
    current_hash=hashlib.sha256(canonical.encode()).hexdigest()
    row=LedgerEvent(tenant_id=tenant_id,aggregate_type=aggregate_type,aggregate_id=aggregate_id,event_type=event_type,payload_json=json.dumps(payload,ensure_ascii=False,sort_keys=True),actor_type=actor_type,actor_id=actor_id,previous_hash=previous_hash,current_hash=current_hash)
    db.add(row);db.commit();db.refresh(row);return row

def verify_chain(db:Session,tenant_id:int):
    rows=db.scalars(select(LedgerEvent).where(LedgerEvent.tenant_id==tenant_id).order_by(LedgerEvent.id)).all();prev=""
    for row in rows:
        payload=json.loads(row.payload_json)
        canonical=json.dumps({"tenant_id":tenant_id,"aggregate_type":row.aggregate_type,"aggregate_id":row.aggregate_id,"event_type":row.event_type,"payload":payload,"actor_type":row.actor_type,"actor_id":row.actor_id,"previous_hash":prev},sort_keys=True,separators=(",",":"),ensure_ascii=False)
        expected=hashlib.sha256(canonical.encode()).hexdigest()
        if row.previous_hash!=prev or row.current_hash!=expected:return {"valid":False,"broken_event_id":row.id,"events":len(rows)}
        prev=row.current_hash
    return {"valid":True,"events":len(rows),"head":prev}
