from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.app.db import Base, engine
from apps.api.app.main import app


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


client = TestClient(app)


def register(email="test@example.com", tenant="Test Tenant"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "tenant_name": tenant},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_complete_product_flow():
    token = register()
    headers = auth_header(token)
    assert client.get("/health").json()["ok"] is True
    assert client.get("/.well-known/agent-card.json").status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "owner"

    participants = []
    for participant_type, name, capabilities in [
        ("buyer", "Buyer A", ["buyer"]),
        ("buyer", "Buyer B", ["buyer"]),
        ("factory", "Factory", ["producer"]),
        ("carrier", "Carrier", ["logistics_provider"]),
        ("designer", "Designer", ["specialist"]),
        ("investor", "Investor", ["financier"]),
    ]:
        response = client.post(
            "/api/v1/participants",
            headers=headers,
            json={
                "participant_type": participant_type,
                "display_name": name,
                "location": "Bac Ninh",
                "capabilities": capabilities,
                "trust_score": 0.85,
                "delivery_score": 0.82,
                "quality_score": 0.88,
            },
        )
        assert response.status_code == 200
        participants.append(response.json())

    assert len(client.get("/api/v1/participants", headers=headers).json()) == 6

    signal_specs = [
        (0, "demand", "paper_cups", 10000),
        (1, "conditional_demand", "paper_cups", 12000),
        (2, "production_capacity", "paper_cups", 50000),
        (3, "logistics_capacity", "logistics", 50000),
        (4, "skill", "design", 100),
        (5, "capital", "capital", 100000000),
    ]
    for idx, signal_type, category, quantity in signal_specs:
        response = client.post(
            "/api/v1/signals",
            headers=headers,
            json={
                "participant_id": participants[idx]["id"],
                "signal_type": signal_type,
                "title": f"{signal_type} {category}",
                "normalized_category": category,
                "quantity": quantity,
                "unit": "cup",
                "location": "Bac Ninh",
                "confidence": 0.9,
                "verification_status": "verified",
                "visibility_scope": "public",
            },
        )
        assert response.status_code == 200

    natural = client.post(
        "/api/v1/signals/natural",
        headers=headers,
        json={
            "participant_id": participants[2]["id"],
            "text": "Xưởng cốc giấy tại Bắc Ninh dư 30% công suất cuối tuần",
            "visibility_scope": "aggregated",
        },
    )
    assert natural.status_code == 200
    assert natural.json()["parsed"]["category"] == "paper_cups"
    assert len(client.get("/api/v1/signals", headers=headers).json()) == 7

    compiled = client.post("/api/v1/opportunities/compile", headers=headers)
    assert compiled.status_code == 200
    assert len(compiled.json()) == 1
    opportunity_id = compiled.json()[0]["id"]

    opportunity = client.get(f"/api/v1/opportunities/{opportunity_id}", headers=headers)
    assert opportunity.status_code == 200
    assert opportunity.json()["score"] > 0
    assert len(client.get("/api/v1/opportunities", headers=headers).json()) == 1

    coalition = client.post(
        f"/api/v1/opportunities/{opportunity_id}/coalitions", headers=headers
    )
    assert coalition.status_code == 200
    assert coalition.json()["coverage_score"] >= 40

    simulation = client.post(
        f"/api/v1/opportunities/{opportunity_id}/simulate",
        headers=headers,
        json={
            "unit_sale_price": 2000,
            "unit_variable_cost": 1200,
            "fixed_cost": 1000000,
            "iterations": 500,
        },
    )
    assert simulation.status_code == 200
    assert simulation.json()["p90"] >= simulation.json()["p10"]

    experiment = client.post(
        "/api/v1/experiments",
        headers=headers,
        json={
            "opportunity_id": opportunity_id,
            "title": "14-day preorder",
            "hypothesis": "At least 100 buyers will commit",
            "success_metric": "100 deposits",
            "budget_limit": 5000000,
            "action_plan": ["landing page", "buyer interviews"],
        },
    ).json()
    assert client.post(
        f"/api/v1/experiments/{experiment['id']}/start", headers=headers
    ).json()["status"] == "running"
    completed = client.post(
        f"/api/v1/experiments/{experiment['id']}/complete",
        headers=headers,
        json={"observations": [{"deposits": 120}], "result": {"forecast_error": 0.08}},
    )
    assert completed.json()["status"] == "completed"

    mandate = client.post(
        "/api/v1/mandates",
        headers=headers,
        json={
            "opportunity_id": opportunity_id,
            "allowed_actions": ["contact_supplier"],
            "forbidden_actions": ["send_payment"],
            "approved_participants": [participants[2]["id"]],
            "budget_limit": 1000000,
            "max_actions": 2,
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        },
    )
    assert mandate.status_code == 200
    mandate_id = mandate.json()["id"]
    action = client.post(
        f"/api/v1/mandates/{mandate_id}/actions",
        headers=headers,
        json={
            "action": "contact_supplier",
            "amount": 1000,
            "participant_id": participants[2]["id"],
        },
    )
    assert action.status_code == 200 and action.json()["authorized"] is True
    denied = client.post(
        f"/api/v1/mandates/{mandate_id}/actions",
        headers=headers,
        json={"action": "send_payment", "amount": 1},
    )
    assert denied.status_code == 403
    assert client.post(
        f"/api/v1/mandates/{mandate_id}/revoke", headers=headers
    ).json()["revoked"] is True

    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    assert dashboard["participants"] == 6
    assert dashboard["ledger"]["valid"] is True
    assert client.get("/api/v1/ledger/verify", headers=headers).json()["valid"] is True


def test_auth_failures_and_tenant_isolation():
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    assert login.status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    ).status_code == 401

    second_token = register("second@example.com", "Second")
    second_headers = auth_header(second_token)
    assert client.get("/api/v1/participants", headers=second_headers).json() == []
    assert client.get("/api/v1/opportunities", headers=second_headers).json() == []
    assert client.get("/api/v1/dashboard", headers=second_headers).json()["signals"] == 0
    assert client.get("/api/v1/participants").status_code == 401
