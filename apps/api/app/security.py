import base64, hashlib, hmac, os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, TenantMember

bearer=HTTPBearer(auto_error=False)

def hash_password(password:str)->str:
    salt=os.urandom(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,210_000)
    return base64.b64encode(salt+digest).decode()

def verify_password(password:str, encoded:str)->bool:
    raw=base64.b64decode(encoded.encode()); salt,digest=raw[:16],raw[16:]
    candidate=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,210_000)
    return hmac.compare_digest(candidate,digest)

def create_token(user_id:int,tenant_id:int,role:str)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub":str(user_id),"tenant_id":tenant_id,"role":role,"exp":exp},settings.jwt_secret,algorithm="HS256")

def current_context(credentials:HTTPAuthorizationCredentials|None=Depends(bearer),db:Session=Depends(get_db)):
    if not credentials: raise HTTPException(401,"Authentication required")
    try: payload=jwt.decode(credentials.credentials,settings.jwt_secret,algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(401,"Invalid or expired token")
    user=db.get(User,int(payload["sub"]))
    if not user or not user.is_active: raise HTTPException(401,"Inactive user")
    member=db.scalar(select(TenantMember).where(TenantMember.user_id==user.id,TenantMember.tenant_id==int(payload["tenant_id"])))
    if not member: raise HTTPException(403,"Tenant access denied")
    return {"user":user,"tenant_id":member.tenant_id,"role":member.role}

def require_roles(*roles):
    def dep(ctx=Depends(current_context)):
        if ctx["role"] not in roles: raise HTTPException(403,"Insufficient role")
        return ctx
    return dep
