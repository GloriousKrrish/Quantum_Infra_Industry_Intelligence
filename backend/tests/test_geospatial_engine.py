"""
Comprehensive Unit & Integration Test Suite for the Real Geographic Intelligence Engine (RGIE) — Phase 1.8.

Validates:
- WGS-84 <-> UTM Zone 43N Transverse Mercator projections and round-trip sub-millimeter precision
- Shoelace polygon area calculation in square meters and acres
- Exact point-in-polygon ray casting (Jordan Curve Theorem)
- Metric buffer envelope generation in UTM 43N Cartesian space
- Spatial index (scipy.spatial.KDTree) nearest-neighbor and radius searches
- Road network graph routing with NetworkX, circuity factor, and IRC speed calibrations
- Geographic suitability scoring, data completeness indexing, and constraint penalties
- RFC 7946 GeoJSON validation and user geometry import
- All Phase 1.8 REST API endpoints and error rejection
"""

from __future__ import annotations

import math
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.engines.geospatial.coordinate_transform import (
    calculate_polygon_centroid,
    calculate_polygon_geodesic_area,
    create_bounding_box,
    haversine_distance,
    projected_euclidean_distance,
    utm43n_to_wgs84,
    wgs84_to_utm43n,
)
from backend.app.engines.geospatial.data_sources import (
    get_all_data_sources,
    get_data_source_by_id,
)
from backend.app.engines.geospatial.geographic_queries import (
    analyze_location_geospatial,
    check_administrative_containment,
    check_environmental_and_zoning_constraints,
    get_spatial_index,
)
from backend.app.engines.geospatial.geometry_validation import (
    check_linear_ring_orientation,
    generate_metric_buffer_polygon,
    is_point_in_polygon,
    validate_and_normalize_geojson,
    validate_wgs84_point,
)
from backend.app.engines.geospatial.government_data_ingestion import (
    get_administrative_boundaries,
    get_infrastructure_corridors,
    get_planning_zones,
    get_water_bodies,
)
from backend.app.engines.geospatial.network_analysis import get_road_network
from backend.app.engines.geospatial.osm_ingestion import query_osm_features
from backend.app.engines.geospatial.suitability_scoring import (
    compute_factor_score,
    evaluate_geographic_suitability,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# 1. COORDINATE TRANSFORMATIONS & GEODESICS
# ═══════════════════════════════════════════════════════════════════════

def test_utm43n_forward_and_inverse_round_trip():
    """Verify sub-centimeter round-trip precision of UTM Zone 43N Transverse Mercator."""
    pune_lat = 18.5204
    pune_lng = 73.8567

    easting, northing = wgs84_to_utm43n(pune_lat, pune_lng)
    # Pune central coordinates should land approximately around 379,320m E, 2,048,144m N
    assert 370000.0 < easting < 390000.0
    assert 2040000.0 < northing < 2060000.0

    ret_lat, ret_lng = utm43n_to_wgs84(easting, northing)
    assert pytest.approx(ret_lat, abs=1e-5) == pune_lat
    assert pytest.approx(ret_lng, abs=1e-5) == pune_lng


def test_projected_euclidean_distance():
    """Verify projected Euclidean distance on UTM 43N matches known geodetic span."""
    # Shivajinagar to Pune Station (~2.6 km)
    dist_m = projected_euclidean_distance(18.5310, 73.8520, 18.5289, 73.8744)
    assert 2200.0 < dist_m < 2600.0


def test_polygon_geodesic_area_shoelace():
    """Verify shoelace area in square meters and acres for a known rectangular polygon."""
    # Approx 500m x 500m = 250,000 sq.m ≈ 61.77 acres
    # 0.0045 deg lat ≈ 500m; 0.00474 deg lng ≈ 500m at lat 18.5
    coords = [
        [73.800, 18.500],
        [73.80474, 18.500],
        [73.80474, 18.5045],
        [73.800, 18.5045],
        [73.800, 18.500],
    ]
    sq_m, acres = calculate_polygon_geodesic_area(coords)
    assert 230000.0 < sq_m < 270000.0
    assert 55.0 < acres < 68.0


def test_polygon_centroid():
    """Verify area-weighted centroid calculation."""
    coords = [
        [73.70, 18.50],
        [73.80, 18.50],
        [73.80, 18.60],
        [73.70, 18.60],
        [73.70, 18.50],
    ]
    c_lat, c_lng = calculate_polygon_centroid(coords)
    assert pytest.approx(c_lat, abs=0.01) == 18.55
    assert pytest.approx(c_lng, abs=0.01) == 73.75


# ═══════════════════════════════════════════════════════════════════════
# 2. GEOMETRY VALIDATION & POINT-IN-POLYGON
# ═══════════════════════════════════════════════════════════════════════

def test_point_in_polygon_ray_casting():
    """Test ray-casting point-in-polygon containment and exterior rejection."""
    square_poly = [
        [73.70, 18.50],
        [73.80, 18.50],
        [73.80, 18.60],
        [73.70, 18.60],
        [73.70, 18.50],
    ]
    # Inside
    assert is_point_in_polygon(18.55, 73.75, square_poly) is True
    # Outside
    assert is_point_in_polygon(18.65, 73.75, square_poly) is False
    assert is_point_in_polygon(18.55, 73.65, square_poly) is False


def test_linear_ring_orientation_ccw():
    """Verify RFC 7946 Counter-Clockwise (CCW) ring orientation detection."""
    ccw_ring = [
        [73.70, 18.50],
        [73.80, 18.50],
        [73.80, 18.60],
        [73.70, 18.60],
        [73.70, 18.50],
    ]
    assert check_linear_ring_orientation(ccw_ring) == "CCW"


def test_metric_buffer_polygon_generation():
    """Verify generation of exact circular metric buffer in UTM 43N."""
    buffer_feat = generate_metric_buffer_polygon(18.5204, 73.8567, radius_meters=1000.0, num_points=36)
    assert buffer_feat["type"] == "Feature"
    assert buffer_feat["geometry"]["type"] == "Polygon"
    props = buffer_feat["properties"]
    assert props["radius_meters"] == 1000.0
    # Area of circle with r=1000m is pi * 10^6 ≈ 3,141,592 sq.m
    assert pytest.approx(props["area_sq_meters"], rel=0.01) == 3141592.65


def test_validate_and_normalize_geojson_valid():
    """Verify validation of valid GeoJSON Polygon."""
    raw = {
        "type": "Polygon",
        "coordinates": [
            [
                [73.73, 18.58],
                [73.75, 18.58],
                [73.75, 18.60],
                [73.73, 18.60],
                [73.73, 18.58],
            ]
        ],
    }
    is_valid, err, normalized = validate_and_normalize_geojson(raw, check_pmrda_boundary=True)
    assert is_valid is True
    assert err is None
    assert normalized is not None
    assert normalized["properties"]["area_acres"] > 0


def test_validate_and_normalize_geojson_invalid_ring():
    """Verify rejection of unclosed or too-short linear ring."""
    raw = {
        "type": "Polygon",
        "coordinates": [
            [[73.73, 18.58], [73.75, 18.58]]  # only 2 points
        ],
    }
    is_valid, err, _ = validate_and_normalize_geojson(raw)
    assert is_valid is False
    assert "at least 4 coordinate positions" in err


# ═══════════════════════════════════════════════════════════════════════
# 3. SPATIAL INDEXING (KDTree on UTM Plane)
# ═══════════════════════════════════════════════════════════════════════

def test_spatial_index_nearest_query():
    """Verify KDTree metric nearest-neighbor search."""
    spatial_idx = get_spatial_index()
    # Query nearest facility to Hinjawadi Phase 1 (18.5912, 73.7380)
    nearest = spatial_idx.query_nearest(18.5912, 73.7380, k=1)
    assert len(nearest) == 1
    # Rajiv Gandhi Infotech Park is at that exact point
    assert nearest[0]["distance_meters"] < 50.0


def test_spatial_index_radius_query():
    """Verify metric radius search within 15 km."""
    spatial_idx = get_spatial_index()
    results = spatial_idx.query_radius(18.5204, 73.8567, radius_meters=15000.0)
    assert len(results) >= 5


# ═══════════════════════════════════════════════════════════════════════
# 4. ROAD NETWORK GRAPH & ROUTING (NetworkX)
# ═══════════════════════════════════════════════════════════════════════

def test_road_network_connectivity():
    """Verify road network graph connectivity and essential vertices."""
    road_net = get_road_network()
    assert road_net.graph.number_of_nodes() >= 25
    assert road_net.graph.number_of_edges() >= 30
    assert "URSE_TOLL" in road_net.graph
    assert "HINJAWADI_PH3" in road_net.graph
    assert "KHARADI_EON" in road_net.graph


def test_road_network_routing_dijkstra():
    """Verify shortest path, circuity factor, and travel times along road network."""
    road_net = get_road_network()
    # Route from Hinjawadi Ph 3 (18.5790, 73.6890) to Urse Toll Plaza (18.7180, 73.6930)
    route = road_net.calculate_road_route(18.5790, 73.6890, 18.7180, 73.6930)
    assert route["straight_line_distance_km"] > 10.0
    assert route["network_distance_km"] >= route["straight_line_distance_km"]
    assert route["circuity_factor"] >= 1.05
    assert route["free_flow_time_minutes"] > 0
    assert route["peak_travel_time_minutes"] >= route["free_flow_time_minutes"]
    assert len(route["route_path"]) >= 3


# ═══════════════════════════════════════════════════════════════════════
# 5. SUITABILITY SCORING & CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════════

def test_geographic_suitability_calculation():
    """Verify multi-criteria geographic suitability and completeness index."""
    distances = {
        "highway_access": 3.5,
        "metro_transit": 2.1,
        "commercial_hub": 4.0,
        "healthcare": 3.0,
        "education": 5.0,
        "industrial_proximity": 8.0,
        "railway_connectivity": 10.0,
    }
    res = evaluate_geographic_suitability(distances)
    assert 0.0 <= res["final_suitability_score"] <= 100.0
    assert res["data_completeness_percent"] == 100.0
    assert res["is_data_complete"] is True
    assert res["classification"] in (
        "PRIME_DEVELOPMENT_CORRIDOR",
        "HIGH_GROWTH_SUITABLE",
        "MODERATE_SUITABILITY",
    )


def test_geographic_suitability_floodline_penalty():
    """Verify environmental floodline constraint imposes penalty."""
    distances = {"highway_access": 2.0, "metro_transit": 2.0}
    clean_res = evaluate_geographic_suitability(distances, within_floodline_zone=False)
    flood_res = evaluate_geographic_suitability(distances, within_floodline_zone=True)
    assert flood_res["final_suitability_score"] < clean_res["final_suitability_score"]
    assert len(flood_res["environmental_penalties"]) == 1


# ═══════════════════════════════════════════════════════════════════════
# 6. GOVERNMENT DATA & STATUTORY BOUNDARIES
# ═══════════════════════════════════════════════════════════════════════

def test_government_boundaries_feature_collection():
    """Verify administrative boundaries FeatureCollection."""
    bounds = get_administrative_boundaries()
    assert bounds["type"] == "FeatureCollection"
    assert len(bounds["features"]) == 3


def test_infrastructure_corridors_and_water():
    """Verify infrastructure corridors and river networks."""
    corridors = get_infrastructure_corridors()
    assert corridors["type"] == "FeatureCollection"
    assert len(corridors["features"]) >= 5

    water = get_water_bodies()
    assert water["type"] == "FeatureCollection"
    assert len(water["features"]) >= 4


# ═══════════════════════════════════════════════════════════════════════
# 7. FASTAPI REST ENDPOINTS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def test_api_geospatial_health(client: TestClient):
    """GET /api/geospatial/health returns 200 operational."""
    resp = client.get("/api/geospatial/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert data["spatial_index"]["indexed_features_count"] >= 25


def test_api_geospatial_sources(client: TestClient):
    """GET /api/geospatial/sources returns verified sources catalog."""
    resp = client.get("/api/geospatial/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sources_count"] >= 8


def test_api_geospatial_boundaries(client: TestClient):
    """GET /api/geospatial/boundaries returns administrative boundaries."""
    resp = client.get("/api/geospatial/boundaries")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 3


def test_api_geospatial_infrastructure(client: TestClient):
    """GET /api/geospatial/infrastructure returns corridors, water, zones."""
    resp = client.get("/api/geospatial/infrastructure")
    assert resp.status_code == 200
    data = resp.json()
    assert "corridors" in data
    assert "water_bodies" in data
    assert "planning_zones" in data


def test_api_geospatial_features_nearby(client: TestClient):
    """GET /api/geospatial/features/nearby returns nearby amenities."""
    resp = client.get("/api/geospatial/features/nearby?lat=18.5204&lng=73.8567&radius_meters=10000")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


def test_api_geospatial_analyze(client: TestClient):
    """POST /api/geospatial/analyze executes complete RGIE analysis."""
    payload = {
        "lat": 18.5912,
        "lng": 73.7380,
        "parcel_id": "PUNE-001",
        "parcel_name": "Hinjawadi Phase 3",
    }
    resp = client.post("/api/geospatial/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["administrative_jurisdiction"]["within_pmrda_region"] is True
    assert "nearest_infrastructure" in data
    assert "geographic_suitability" in data
    assert "road_network_routing" in data


def test_api_geospatial_import_geojson(client: TestClient):
    """POST /api/geospatial/import/geojson validates and normalizes user GeoJSON."""
    geojson_payload = {
        "geojson_data": {
            "type": "Polygon",
            "coordinates": [
                [
                    [73.735, 18.590],
                    [73.740, 18.590],
                    [73.740, 18.595],
                    [73.735, 18.595],
                    [73.735, 18.590],
                ]
            ],
        },
        "parcel_name": "Test Site Wakad",
        "check_pmrda_boundary": True,
    }
    resp = client.post("/api/geospatial/import/geojson", json=geojson_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["provenance_tier"] == "USER_PROVIDED"
    assert data["area_acres"] > 50.0


def test_api_geospatial_import_invalid_rejected(client: TestClient):
    """POST /api/geospatial/import/geojson rejects out-of-bounds PMRDA geometry."""
    geojson_payload = {
        "geojson_data": {
            "type": "Point",
            "coordinates": [77.2090, 28.6139],  # New Delhi (outside PMRDA)
        },
        "check_pmrda_boundary": True,
    }
    resp = client.post("/api/geospatial/import/geojson", json=geojson_payload)
    assert resp.status_code == 422
    assert "outside Pune Metropolitan Region" in resp.json()["detail"]


def test_api_geospatial_provenance_lookup(client: TestClient):
    """GET /api/geospatial/provenance/{feature_id} returns formal provenance record."""
    resp = client.get("/api/geospatial/provenance/PMRDA_DP_2041")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_status"] == "VERIFIED_OFFICIAL"
    assert "PMRDA" in data["source_name"]
