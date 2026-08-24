from fastapi.testclient import TestClient
from app.main import app
from app.ai import normalize_filters
from app.models import Filters

client=TestClient(app)

def test_health():assert client.get("/health").json()=={"status":"ok"}

def test_multiturn_refinement():
    first=client.post("/v1/search/refine",json={"query":"Toyota SUVs in Texas","current_filters":{}}).json()["filters"]
    second=client.post("/v1/search/refine",json={"query":"2020 or newer under $25k","current_filters":first}).json()["filters"]
    assert second["makes"]==["Toyota"] and second["bodies"]==["SUV"] and second["states"]==["TX"]
    assert second["minYear"]==2020 and second["maxPrice"]==25000

def test_normalizes_model_values_for_inventory_search():
    normalized=normalize_filters(Filters(states=["Texas"],bodies=["suv"],fuels=["electric"],drives=["awd"]))
    assert normalized.states==["TX"] and normalized.bodies==["SUV"]
    assert normalized.fuels==["Electric"] and normalized.drives==["AWD"]
