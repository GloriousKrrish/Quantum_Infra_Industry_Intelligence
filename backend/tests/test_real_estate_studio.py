"""
Unit and Integration Tests for Real Estate Intelligence Studio (Phase 1.6).

Tests:
- Haversine distance and drive-time calculations
- Multi-sector infrastructure proximity analysis
- Modular development feasibility calculations
- Financial scenario modeling and cash flow projections
- API endpoint integration:
    - GET /api/parcels (with search, category, and sorting)
    - GET /api/parcels/{id} (full master profile)
    - GET /api/parcels/{id}/infrastructure (proximity breakdown)
    - POST /api/parcels/{id}/feasibility (custom & default assumptions)
    - POST /api/parcels/{id}/financial (multi-scenario projections)
    - 404 response handling for invalid IDs
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    get_parcel_by_id,
    search_and_filter_parcels,
    get_parcel_detailed_profile,
)
from backend.app.engines.real_estate.infrastructure_analysis import (
    compute_haversine_distance_km,
    estimate_drive_time_minutes,
    analyze_parcel_infrastructure,
)
from backend.app.engines.real_estate.development_feasibility import (
    evaluate_feasibility,
    SQFT_PER_ACRE,
)
from backend.app.engines.real_estate.financial_analysis import evaluate_financial_scenarios
from backend.app.models.schemas import FeasibilityScenarioRequest

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# 1. GEOSPATIAL & HAVERSINE MATHEMATICS
# ═══════════════════════════════════════════════════════════════════════

def test_haversine_distance_zero():
    """Same coordinates must yield zero distance."""
    d = compute_haversine_distance_km(18.5204, 73.8567, 18.5204, 73.8567)
    assert d == 0.0


def test_haversine_known_pune_distance():
    """
    Distance between Pune Junction (18.5289, 73.8744) and
    Hinjawadi Phase 1 (18.5910, 73.7380) is approximately 16-17 km straight-line.
    """
    d = compute_haversine_distance_km(18.5289, 73.8744, 18.5910, 73.7380)
    assert 14.0 < d < 18.0


def test_drive_time_estimation():
    """Drive time must be positive and scale with distance."""
    t_short = estimate_drive_time_minutes(5.0, 35.0)
    t_long = estimate_drive_time_minutes(25.0, 35.0)
    assert t_short >= 2
    assert t_long > t_short


# ═══════════════════════════════════════════════════════════════════════
# 2. INFRASTRUCTURE PROXIMITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def test_parcel_infrastructure_analysis():
    """Verify proximity analysis for Hinjawadi Phase 3."""
    parcel = get_parcel_by_id("PUNE-003")
    assert parcel is not None
    assert parcel.name == "Hinjawadi Phase 3"

    analysis = analyze_parcel_infrastructure(parcel)
    assert analysis.parcel_id == "PUNE-003"
    assert len(analysis.all_proximity_points) == 6
    assert analysis.nearest_highway.distance_km > 0
    assert analysis.nearest_hospital.distance_km > 0
    assert analysis.nearest_commercial_hub.distance_km < 5.0  # Very close to Rajiv Gandhi Infotech Park!
    assert 0 <= analysis.accessibility_score <= 100
    assert "OpenStreetMap" in analysis.data_source


# ═══════════════════════════════════════════════════════════════════════
# 3. DEVELOPMENT FEASIBILITY
# ═══════════════════════════════════════════════════════════════════════

def test_feasibility_residential_defaults():
    """Verify default residential feasibility metrics."""
    parcel = get_parcel_by_id("PUNE-004")  # Talegaon Dabhade (9.0 acres, residential)
    assert parcel is not None

    result = evaluate_feasibility(parcel)
    expected_area_sqft = round(9.0 * SQFT_PER_ACRE, 2)
    assert math.isclose(result.land_area_sqft, expected_area_sqft, rel_tol=1e-3)
    assert result.permissible_fsi == 1.75
    assert result.built_up_area_sqft == round(expected_area_sqft * 1.75, 2)
    assert result.total_project_cost_crore > parcel.price_crore
    assert result.projected_gdv_crore > 0
    assert len(result.infrastructure_requirements) >= 3
    assert len(result.development_constraints) >= 2


def test_feasibility_custom_assumptions():
    """Verify custom FSI and construction cost overrides."""
    parcel = get_parcel_by_id("PUNE-001")
    assert parcel is not None

    custom_req = FeasibilityScenarioRequest(
        development_type="commercial",
        custom_target_fsi=2.5,
        custom_construction_cost_sqft=4000.0,
        projected_selling_price_sqft=10000.0,
    )
    result = evaluate_feasibility(parcel, custom_req)
    assert result.development_type == "commercial"
    assert result.permissible_fsi == 2.5
    assert result.construction_cost_per_sqft == 4000.0
    assert result.projected_selling_price_sqft == 10000.0
    assert result.roi_pct > 0


# ═══════════════════════════════════════════════════════════════════════
# 4. FINANCIAL SCENARIOS & CASH FLOW
# ═══════════════════════════════════════════════════════════════════════

def test_financial_scenarios():
    """Verify three-tier scenarios (conservative, baseline, optimistic)."""
    parcel = get_parcel_by_id("PUNE-007")  # Kharadi IT Hub
    assert parcel is not None

    fin = evaluate_financial_scenarios(parcel)
    assert fin.parcel_id == "PUNE-007"
    assert "conservative" in fin.scenarios
    assert "baseline" in fin.scenarios
    assert "optimistic" in fin.scenarios

    # Optimistic should have higher GDV and ROI than Conservative
    assert fin.scenarios["optimistic"].projected_gdv_crore > fin.scenarios["conservative"].projected_gdv_crore
    assert fin.scenarios["optimistic"].roi_pct > fin.scenarios["conservative"].roi_pct

    # 3-year cash flow
    assert len(fin.cashflow_timeline) == 3
    assert fin.cashflow_timeline[0].year == 1
    assert fin.cashflow_timeline[1].year == 2
    assert fin.cashflow_timeline[2].year == 3
    assert 0 < fin.break_even_sales_pct <= 100.0


# ═══════════════════════════════════════════════════════════════════════
# 5. FASTAPI REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

def test_api_list_parcels_search_and_filters():
    """Test search, category filter, and sorting query parameters."""
    # Search by keyword
    r1 = client.get("/api/parcels?search=Kharadi")
    assert r1.status_code == 200
    items1 = r1.json()
    assert len(items1) == 1
    assert items1[0]["id"] == "PUNE-007"

    # Filter by zone
    r2 = client.get("/api/parcels?zone_type=commercial")
    assert r2.status_code == 200
    items2 = r2.json()
    assert all(p["zone_type"] == "commercial" for p in items2)

    # Sort by price ascending
    r3 = client.get("/api/parcels?sort_by=price_asc")
    assert r3.status_code == 200
    items3 = r3.json()
    assert items3[0]["price_crore"] <= items3[-1]["price_crore"]


def test_api_get_parcel_profile():
    """Test detailed profile endpoint GET /api/parcels/{id}."""
    resp = client.get("/api/parcels/PUNE-001")
    assert resp.status_code == 200
    data = resp.json()

    assert data["parcel"]["id"] == "PUNE-001"
    assert data["price_per_acre_crore"] > 0
    assert "verification_status" in data
    assert "geographic_summary" in data
    assert "infrastructure_analysis" in data
    assert "feasibility" in data
    assert "financials" in data
    assert "quantum_participation" in data
    assert data["quantum_participation"]["is_eligible"] is True


def test_api_get_parcel_infrastructure():
    """Test GET /api/parcels/{id}/infrastructure."""
    resp = client.get("/api/parcels/PUNE-002/infrastructure")
    assert resp.status_code == 200
    data = resp.json()
    assert data["parcel_id"] == "PUNE-002"
    assert data["nearest_highway"]["facility_type"] == "Highway"
    assert data["nearest_commercial_hub"]["distance_km"] < 2.0  # Chakan MIDC


def test_api_post_feasibility():
    """Test POST /api/parcels/{id}/feasibility."""
    payload = {
        "development_type": "industrial",
        "custom_target_fsi": 1.2,
        "custom_construction_cost_sqft": 2200.0,
    }
    resp = client.post("/api/parcels/PUNE-002/feasibility", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["development_type"] == "industrial"
    assert data["permissible_fsi"] == 1.2
    assert data["total_project_cost_crore"] > 0


def test_api_post_financial():
    """Test POST /api/parcels/{id}/financial."""
    resp = client.post("/api/parcels/PUNE-003/financial", json={"development_type": "commercial"})
    assert resp.status_code == 200
    data = resp.json()
    assert "scenarios" in data
    assert "cashflow_timeline" in data
    assert len(data["cashflow_timeline"]) == 3


def test_api_invalid_parcel_id():
    """Non-existent parcel ID must return 404."""
    resp = client.get("/api/parcels/INVALID-999")
    assert resp.status_code == 404
