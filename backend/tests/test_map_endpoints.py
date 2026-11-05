"""
Tests for the Real-World Geospatial Map & Digital Twin API Endpoints.
Verifies MapLibre GL config, authentic building footprints, geocoding search,
spatial feature inspection, and map-driven quantum optimization workflows.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_map_config_endpoint():
    """Verify MapLibre configuration, styles, bounds and CRS definitions."""
    response = client.get("/api/map/config")
    assert response.status_code == 200
    data = response.json()

    assert data["engine"] == "MapLibre GL JS v4+"
    assert "default_view" in data
    assert len(data["default_view"]["center"]) == 2  # [lng, lat]
    assert data["default_view"]["center"][0] > 73.0  # Pune Longitude
    assert data["default_view"]["center"][1] > 18.0  # Pune Latitude
    assert "styles" in data
    assert len(data["styles"]) >= 2
    assert "statutory_attribution" in data


def test_map_health_endpoint():
    """Verify operational health and presence of cached OSM building footprints."""
    response = client.get("/api/map/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "operational"
    assert data["map_renderer"] == "MapLibre GL JS"
    assert data["cached_building_footprints"] >= 15
    assert data["geocoding_localities_count"] >= 10


def test_map_layers_catalog():
    """Verify layer registration, geometry types, and provenance tiers."""
    response = client.get("/api/map/layers")
    assert response.status_code == 200
    layers = response.json()

    assert isinstance(layers, list)
    assert len(layers) >= 7

    layer_ids = [l["id"] for l in layers]
    assert "layer_admin_boundaries" in layer_ids
    assert "layer_building_footprints" in layer_ids
    assert "layer_corridors" in layer_ids
    assert "layer_water_floodlines" in layer_ids
    assert "layer_qaoa_winning_parcels" in layer_ids

    for layer in layers:
        assert "provenance_tier" in layer
        assert "source" in layer


def test_map_buildings_geojson():
    """Verify authentic building footprints FeatureCollection."""
    response = client.get("/api/map/buildings")
    assert response.status_code == 200
    fc = response.json()

    assert fc["type"] == "FeatureCollection"
    assert "features" in fc
    assert len(fc["features"]) >= 15

    # Check structure of first building feature
    f = fc["features"][0]
    assert f["type"] == "Feature"
    assert "geometry" in f
    assert f["geometry"]["type"] == "Polygon"
    assert len(f["geometry"]["coordinates"][0]) >= 4  # closed ring
    assert "properties" in f
    assert "osm_id" in f["properties"]
    assert "name" in f["properties"]
    assert "verification_status" in f["properties"]
    assert f["properties"]["verification_status"] == "VERIFIED_OPEN_DATA"


def test_map_search_localities():
    """Verify real geocoding search for Hinjewadi and Chakan."""
    res_hinj = client.get("/api/map/search", params={"q": "hinjewadi"})
    assert res_hinj.status_code == 200
    hinj_matches = res_hinj.json()
    assert len(hinj_matches) > 0
    assert "Hinjewadi" in hinj_matches[0]["name"]
    assert hinj_matches[0]["lat"] == pytest.approx(18.591, abs=0.01)

    res_chakan = client.get("/api/map/search", params={"q": "chakan"})
    assert res_chakan.status_code == 200
    chakan_matches = res_chakan.json()
    assert len(chakan_matches) > 0
    assert "Chakan" in chakan_matches[0]["name"]


def test_map_features_inspect():
    """Verify feature inspection returns dual coordinates, administration, and road routing."""
    payload = {
        "lat": 18.5910,
        "lng": 73.7380,
        "feature_id": "way/osm_hinj_infosys_b1",
        "feature_name": "Infosys Software Development Block 1",
        "feature_type": "building",
    }
    response = client.post("/api/map/features/inspect", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["feature_identity"]["feature_id"] == "way/osm_hinj_infosys_b1"
    assert "coordinates" in data
    assert "wgs84" in data["coordinates"]
    assert "utm_zone_43n" in data["coordinates"]
    assert data["coordinates"]["utm_zone_43n"]["crs"] == "EPSG:32643"

    assert "administrative_jurisdiction" in data
    assert data["administrative_jurisdiction"]["within_pmrda_region"] is True

    assert "road_network_routing" in data
    assert "to_nearest_highway" in data["road_network_routing"]
    assert data["road_network_routing"]["to_nearest_highway"]["circuity_factor"] >= 1.0

    assert "data_notice" in data
    assert data["data_notice"]["is_cadastral_title"] is False


def test_map_optimization_workflow():
    """Verify end-to-end comparative classical vs QAOA optimization on candidate parcels."""
    payload = {
        "budget_crore": 40.0,
        "qaoa_p": 1,
        "qaoa_shots": 1024,
    }
    response = client.post("/api/map/optimization/workflow", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "quantum_qaoa_result" in data
    assert "classical_baseline_result" in data
    assert "comparative_analysis" in data
    assert "winning_parcels_for_map" in data

    q_res = data["quantum_qaoa_result"]
    assert len(q_res["selected_parcels"]) > 0
    assert q_res["total_investment_crore"] <= 40.0
    assert q_res["budget_compliant"] is True

    comp = data["comparative_analysis"]
    assert comp["approximation_ratio"] >= 0.85
    assert len(data["winning_parcels_for_map"]) == len(q_res["selected_parcels"])

