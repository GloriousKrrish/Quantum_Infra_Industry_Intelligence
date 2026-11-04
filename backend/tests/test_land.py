"""
Tests for Real Estate Land Intelligence & Deterministic Infrastructure Calculators.
"""

import pytest
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    get_parcels_within_budget,
    compute_utility_score,
)
from backend.app.engines.real_estate.infrastructure_calc import (
    generate_infrastructure_report,
    compute_infra_readiness_index,
    compute_water_demand,
    compute_sewage_output,
    compute_electricity_kva,
)


def test_get_all_parcels():
    parcels = get_all_parcels()
    assert len(parcels) == 8
    names = [p.name for p in parcels]
    assert "Wagholi East" in names
    assert "Hinjawadi Phase 3" in names
    assert "Chakan Industrial" in names


def test_get_parcels_within_budget():
    budget = 12.0
    parcels = get_parcels_within_budget(budget)
    assert len(parcels) > 0
    for p in parcels:
        assert p.price_crore <= budget


def test_compute_utility_score():
    parcels = get_all_parcels()
    for p in parcels:
        score = compute_utility_score(p)
        assert score > 0


def test_deterministic_infrastructure_calc():
    parcel = get_all_parcels()[0]
    report = generate_infrastructure_report(parcel)
    
    # IS 1172 Standard checks
    assert report.water_demand_lpd > 0
    assert report.sewage_output_lpd == pytest.approx(report.water_demand_lpd * 0.8, rel=1e-3)
    assert report.electricity_kva > 0
    assert 0 <= report.infra_readiness_index <= 1.0


def test_readiness_index_weights():
    parcel = get_all_parcels()[0]
    score = compute_infra_readiness_index(parcel)
    assert 0.0 <= score <= 1.0
