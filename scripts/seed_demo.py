import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datetime import datetime,timedelta
import json
from sqlalchemy import select
from apps.api.app.db import Base,engine,SessionLocal
from apps.api.app.models import *
from apps.api.app.security import hash_password
from apps.api.app.services.opportunity import compile_for_tenant
from apps.api.app.services.ledger import append_event
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    user=db.scalar(select(User).where(User.email=="owner@demandweave.local"))
    if user: print("Demo already seeded");raise SystemExit
    tenant=Tenant(name="Bac Ninh Circular Commerce Lab",slug="bac-ninh-lab");user=User(email="owner@demandweave.local",password_hash=hash_password("DemandWeave123!"));db.add_all([tenant,user]);db.flush();db.add(TenantMember(tenant_id=tenant.id,user_id=user.id,role="owner"))
    specs=[
      ("buyer","Cafe Hoa Sen","Bac Ninh",.78,["buyer"]),("buyer","Cafe Green","Bac Ninh",.75,["buyer"]),("buyer","Cafe Town","Bac Ninh",.72,["buyer"]),
      ("factory","PaperPack Factory","Bac Ninh",.91,["producer"]),("designer","Print Design Studio","Bac Ninh",.82,["specialist"]),("carrier","ReturnTrip Logistics","Bac Ninh",.87,["logistics_provider"]),("investor","Local Working Capital Fund","Bac Ninh",.8,["financier"]),
      ("buyer","Restaurant A","Thanh Hoa",.72,["buyer"]),("buyer","Restaurant B","Thanh Hoa",.74,["buyer"]),("factory","Eco Bowl Plant","Thanh Hoa",.88,["producer"])
    ];parts=[]
    for typ,name,loc,trust,caps in specs:
      p=Participant(tenant_id=tenant.id,participant_type=typ,display_name=name,location=loc,trust_score=trust,response_score=trust,delivery_score=trust,quality_score=trust,capabilities_json=json.dumps(caps));db.add(p);db.flush();parts.append(p)
    signals=[
      (parts[0],"demand","paper_cups",30000,"cup",.9),(parts[1],"conditional_demand","paper_cups",25000,"cup",.85),(parts[2],"preorder","paper_cups",20000,"cup",.8),
      (parts[3],"production_capacity","paper_cups",120000,"cup",.92),(parts[4],"skill","design",100,"hour",.85),(parts[5],"logistics_capacity","logistics",80000,"cup",.9),(parts[6],"capital","capital",200000000,"VND",.8),
      (parts[7],"demand","paper_bowls",40000,"bowl",.85),(parts[8],"demand","paper_bowls",35000,"bowl",.82),(parts[9],"production_capacity","paper_bowls",100000,"bowl",.9)
    ]
    for p,st,cat,q,u,c in signals:
      db.add(Signal(tenant_id=tenant.id,participant_id=p.id,signal_type=st,title=f"{p.display_name}: {st} {cat}",natural_language_input="Synthetic demo signal",normalized_category=cat,quantity=q,unit=u,location=p.location,confidence=c,verification_status="verified",visibility_scope="aggregated",source="demo",attributes_json="{}"))
    db.commit();opps=compile_for_tenant(db,tenant.id);append_event(db,tenant.id,"tenant",tenant.id,"demo_seeded",{"participants":len(parts),"opportunities":len(opps)},user.id)
    print(f"Seeded tenant={tenant.id}, participants={len(parts)}, opportunities={len(opps)}")
