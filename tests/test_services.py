from datetime import datetime,timedelta
from apps.api.app.services.normalize import normalize_text,parse_natural_signal
from apps.api.app.services.simulation import simulate
from apps.api.app.services.mandates import sign,valid
from apps.api.app.schemas import SimulationIn

def test_natural_parser():
    r=parse_natural_signal("Tôi có xưởng cốc giấy ở Bắc Ninh, dư 30% công suất và làm được 20000 chiếc")
    assert r["signal_type"]=="production_capacity" and r["normalized_category"]=="paper_cups"
def test_simulation():
    a=SimulationIn(unit_sale_price=2000,unit_variable_cost=1200,fixed_cost=1_000_000,iterations=500)
    r=simulate(10000,a);assert r["probability_profit"]>.8 and r["p90"]>=r["p10"]
def test_signature():
    d={"x":1,"expires_at":(datetime.utcnow()+timedelta(days=1)).isoformat()};s=sign(d);assert valid(d,s);assert not valid({"x":2},s)
def test_normalize():assert normalize_text("Cốc giấy 12oz") == "coc giay 12oz"
