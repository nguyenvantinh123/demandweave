import hashlib,hmac,json
from datetime import datetime
from ..config import settings

def canonical_payload(data:dict)->str:return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sign(data:dict)->str:return hmac.new(settings.mandate_secret.encode(),canonical_payload(data).encode(),hashlib.sha256).hexdigest()
def valid(data:dict,signature:str)->bool:return hmac.compare_digest(sign(data),signature)
def mandate_data(row):
    return {"tenant_id":row.tenant_id,"opportunity_id":row.opportunity_id,"allowed_actions":json.loads(row.allowed_actions_json),"forbidden_actions":json.loads(row.forbidden_actions_json),"approved_participants":json.loads(row.approved_participants_json),"budget_limit":row.budget_limit,"max_actions":row.max_actions,"expires_at":row.expires_at.isoformat()}
def authorize(row,action:str,amount:float=0,participant_id:int|None=None):
    data=mandate_data(row)
    if row.revoked:return False,"revoked"
    if row.expires_at<=datetime.utcnow():return False,"expired"
    if not valid(data,row.signature):return False,"invalid_signature"
    if action not in data["allowed_actions"] or action in data["forbidden_actions"]:return False,"action_not_allowed"
    if row.action_count>=row.max_actions:return False,"action_limit"
    if row.spent_amount+amount>row.budget_limit:return False,"budget_limit"
    if data["approved_participants"] and participant_id not in data["approved_participants"]:return False,"participant_not_approved"
    return True,"authorized"
