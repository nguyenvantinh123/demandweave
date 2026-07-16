import asyncio

from apps.api.app.plugins import MockAIAdapter
from apps.api.app.services.privacy import public_signal


class Row:
    id = 1
    participant_id = 2
    signal_type = "demand"
    normalized_category = "paper_cups"
    quantity = 100
    unit = "cup"
    location = "Bac Ninh"
    confidence = 0.8
    created_at = "now"
    title = "Need cups"
    attributes_json = "{}"


def test_privacy_scopes():
    row = Row()
    row.visibility_scope = "public"
    assert public_signal(row)["participant_id"] == 2
    row.visibility_scope = "aggregated"
    assert public_signal(row)["title"] == "Aggregated signal"
    row.visibility_scope = "coalition"
    assert "coalition" in public_signal(row)["title"].lower()
    row.visibility_scope = "private"
    assert public_signal(row) == {"id": 1, "visibility_scope": "private"}


def test_mock_ai_adapter():
    adapter = MockAIAdapter()
    extracted = asyncio.run(adapter.extract_signal("Need paper cups"))
    explained = asyncio.run(adapter.explain_opportunity({"evidence": [1, 2]}))
    assert extracted["confidence"] == 0.5
    assert "2 evidence" in explained
