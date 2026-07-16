import time
from .db import SessionLocal
from .models import Tenant
from .services.opportunity import compile_for_tenant
from sqlalchemy import select

def main():
    while True:
        with SessionLocal() as db:
            for tenant in db.scalars(select(Tenant)).all(): compile_for_tenant(db,tenant.id)
        time.sleep(300)
if __name__=="__main__":main()
