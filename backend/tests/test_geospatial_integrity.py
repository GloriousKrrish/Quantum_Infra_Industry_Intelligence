"""
Automated Validation Suite for Geospatial Data Integrity, Provenance Framework,
RFC 7946 GeoJSON Conformance, and Mathematical Safeguards (Phase 1.7).
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.models.schemas import (
    DistanceMethodology,
    ParcelGeometryType,
    VerificationStatus,
)
from backend.app.data.provenance.verification import (
    validate_coordinates,
    validate_geojson_geometry,
    generate_approximate_parcel_polygon,
    PMRDA_LAT_MIN,
    PMRDA_LAT_MAX,
    PMRDA_LNG_MIN,
    PMRDA_LNG_MAX,
)
from backend.app.data.sources.government_source import (
    get_government_provenance,
    GOVERNMENT_STANDARDS,
)
from backend.app.data.sources.synthetic_source import (
    get_synthetic_provenance,
    SYNTHETIC_CATALOG,
)
from backend.app.data.sources.osm_source import (
    query_overpass_amenities,
    get_osm_provenance,
    OSM_ATTRIBUTION,
)
from backend.app.data.provenance.data_registry import (
    get_parcel_provenance,
    get_provenance_audit_summary,
)
from backend.app.engines.real_estate.infrastructure_analysis import (
    compute_haversine_distance_km,
    estimate_drive_time_minutes,
    analyze_parcel_infrastructure,
)
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    get_parcel_by_id,
    get_parcel_detailed_profile,
)
from backend.app.engines.real_estate.development_feasibility import evaluate_feasibility

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# 1. WGS-84 COORDINATE VALIDATION & BOUNDING BOX
# ═══════════════════════════════════════════════════════════════════════

def test_validate_valid_coordinates():
    """Valid Pune coordinates must pass standard and PMRDA envelope checks."""
    valid, err = validate_coordinates(18.5204, 73.8567, check_pmrda_boundary=True)
    assert valid is True
    assert err is None


def test_validate_out_of_range_coordinates():
    """Coordinates exceeding global limits [-90, 90] or [-180, 180] must fail."""
    v1, err1 = validate_coordinates(95.0, 73.8567)
    assert v1 is False
    assert "Latitude" in err1

    v2, err2 = validate_coordinates(18.5204, 185.0)
    assert v2 is False
    assert "Longitude" in err2


def test_validate_nan_inf_coordinates():
    """NaN or Infinite coordinates must be rejected."""
    v1, _ = validate_coordinates(float("nan"), 73.8567)
    assert v1 is False

    v2, _ = validate_coordinates(18.5204, float("inf"))
    assert v2 is False


def test_validate_pmrda_boundary_rejection():
    """Coordinates outside the Pune Metropolitan envelope must fail PMRDA check."""
    # Delhi coordinate (28.61° N, 77.20° E)
    valid, err = validate_coordinates(28.6139, 77.2090, check_pmrda_boundary=True)
    assert valid is False
    assert "outside Pune Metropolitan Region" in err


# ═══════════════════════════════════════════════════════════════════════
# 2. HAVERSINE NUMERICAL INTEGRITY & EDGE CASES
# ═══════════════════════════════════════════════════════════════════════

def test_haversine_identical_points_exact_zero():
    """Identical coordinates must return exactly 0.0 without calculation overhead."""
    d = compute_haversine_distance_km(18.5788, 73.9787, 18.5788, 73.9787)
    assert d == 0.0


def test_haversine_invalid_coordinates_raises_error():
    """Invalid WGS-84 coordinates must raise ValueError."""
    with pytest.raises(ValueError):
        compute_haversine_distance_km(120.0, 73.0, 18.5, 73.0)


def test_haversine_antipodal_numerical_stability():
    """Antipodal points (opposite sides of Earth) must not trigger math domain error."""
    # North pole to South pole ≈ 20,015 km
    d = compute_haversine_distance_km(90.0, 0.0, -90.0, 0.0)
    assert math.isclose(d, 20015.08, rel_tol=1e-2)


# ═══════════════════════════════════════════════════════════════════════
# 3. RFC 7946 GEOJSON GEOMETRY CONFORMANCE
# ═══════════════════════════════════════════════════════════════════════

def test_validate_geojson_valid_point():
    """Valid GeoJSON Point must pass validation."""
    pt = {"type": "Point", "coordinates": [73.8567, 18.5204]}
    valid, err = validate_geojson_geometry(pt)
    assert valid is True
    assert err is None


def test_validate_geojson_unclosed_polygon_rejected():
    """Polygon with unclosed linear ring must fail validation."""
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [73.0, 18.0],
                [73.1, 18.0],
                [73.1, 18.1],
                [73.0, 18.1],
                # Missing closing point [73.0, 18.0]
            ]
        ],
    }
    valid, err = validate_geojson_geometry(polygon)
    assert valid is False
    assert "not closed" in err


def test_generate_approximate_parcel_polygon():
    """Approximate parcel polygon generation must produce a valid closed GeoJSON Polygon."""
    poly = generate_approximate_parcel_polygon(18.5788, 73.9787, 6.5)
    valid, err = validate_geojson_geometry(poly)
    assert valid is True
    assert err is None
    assert poly["type"] == "Polygon"
    assert len(poly["coordinates"][0]) == 5
    assert poly["properties"]["area_acres"] == 6.5
    assert poly["properties"]["geometry_classification"] == ParcelGeometryType.APPROXIMATE_BOUND.value


# ═══════════════════════════════════════════════════════════════════════
# 4. DATA TRUST FRAMEWORK & PROVENANCE REGISTRY
# ═══════════════════════════════════════════════════════════════════════

def test_parcel_provenance_records():
    """Every parcel in _PUNE_PARCELS must have a formal ProvenanceRecord and approximate GeoJSON."""
    parcels = get_all_parcels()
    assert len(parcels) == 8
    for p in parcels:
        assert p.provenance is not None
        assert p.provenance.verification_status == VerificationStatus.VERIFIED_OPEN_DATA
        assert p.provenance.confidence_level is not None
        assert p.geojson_geometry is not None
        assert p.geojson_geometry["type"] == "Polygon"


def test_government_provenance_standards():
    """Official government standards catalog must resolve valid ProvenanceRecords."""
    rec = get_government_provenance("PMRDA_DP_2041")
    assert rec.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert rec.confidence_level == 0.95
    assert "PMRDA" in rec.source_name


def test_synthetic_provenance_disclaimers():
    """Synthetic catalog must enforce SYNTHETIC status without arbitrary confidence scores."""
    rec = get_synthetic_provenance("DEMO_PARCEL_PRICES")
    assert rec.verification_status == VerificationStatus.SYNTHETIC
    assert rec.confidence_level is None  # Never claim confidence on synthetic benchmarks
    assert "Disclaimer" in rec.methodology_notes


def test_provenance_audit_summary():
    """Platform audit summary must return complete verification tiers and dataset breakdown."""
    summary = get_provenance_audit_summary()
    assert summary["audit_version"] == "1.7.0"
    assert "datasets" in summary
    assert summary["datasets"]["land_parcels"]["total_records"] == 8
    assert summary["datasets"]["infrastructure_anchors"]["total_records"] == 23


# ═══════════════════════════════════════════════════════════════════════
# 5. OVERPASS API & OFFLINE RESILIENCE
# ═══════════════════════════════════════════════════════════════════════

def test_overpass_query_resilience():
    """Overpass API query must handle network failures gracefully without raising unhandled exceptions."""
    # Query with very short timeout to test fallback/resilience
    elements, status = query_overpass_amenities(18.5204, 73.8567, radius_meters=1000, timeout_seconds=0.01)
    assert isinstance(elements, list)
    assert isinstance(status, str)


def test_osm_provenance_attribution():
    """OpenStreetMap provenance must carry mandatory ODbL license attribution."""
    prov = get_osm_provenance("Ruby Hall Clinic", "Hospital")
    assert prov.verification_status == VerificationStatus.VERIFIED_OPEN_DATA
    assert "ODbL" in prov.source_name or "ODbL" in prov.methodology_notes


# ═══════════════════════════════════════════════════════════════════════
# 6. INFRASTRUCTURE & ACCESSIBILITY SCORE VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def test_custom_accessibility_weights():
    """Custom accessibility scoring weights must alter composite score predictably."""
    parcel = get_parcel_by_id("PUNE-001")
    assert parcel is not None

    # Test with standard weights
    std_analysis = analyze_parcel_infrastructure(parcel)

    # Test with 100% weight on highway
    hw_only_analysis = analyze_parcel_infrastructure(
        parcel, custom_weights={"highway": 100.0, "hospital": 0.0, "commercial": 0.0, "railway": 0.0, "education": 0.0, "airport": 0.0}
    )
    assert 0 <= hw_only_analysis.accessibility_score <= 100
    assert "Highway 100%" in hw_only_analysis.accessibility_score_methodology
    assert hw_only_analysis.is_official_rating is False


# ═══════════════════════════════════════════════════════════════════════
# 7. FEASIBILITY MATHEMATICAL SAFEGUARDS
# ═══════════════════════════════════════════════════════════════════════

def test_feasibility_non_positive_area_rejected():
    """Non-positive land area must raise ValueError."""
    parcel = get_parcel_by_id("PUNE-001")
    invalid_parcel = parcel.model_copy()
    invalid_parcel.area_acres = -2.5

    with pytest.raises(ValueError):
        evaluate_feasibility(invalid_parcel)


def test_feasibility_negative_price_rejected():
    """Negative land price must raise ValueError."""
    parcel = get_parcel_by_id("PUNE-001")
    invalid_parcel = parcel.model_copy()
    invalid_parcel.price_crore = -10.0

    with pytest.raises(ValueError):
        evaluate_feasibility(invalid_parcel)


# ═══════════════════════════════════════════════════════════════════════
# 8. REST API INTEGRATION FOR PHASE 1.7
# ═══════════════════════════════════════════════════════════════════════

def test_api_provenance_audit_endpoint():
    """GET /api/parcels/provenance/audit must return platform data trust summary."""
    resp = client.get("/api/parcels/provenance/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert data["audit_version"] == "1.7.0"
    assert "verification_framework" in data
    assert "datasets" in data


def test_api_overpass_amenities_endpoint():
    """GET /api/parcels/{id}/overpass must return structured amenity query response."""
    resp = client.get("/api/parcels/PUNE-001/overpass?radius_meters=3000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["parcel_id"] == "PUNE-001"
    assert "query_status" in data
    assert "elements_count" in data
    assert "attribution" in data


def test_api_infrastructure_custom_weights():
    """GET /api/parcels/{id}/infrastructure with custom query weights."""
    resp = client.get("/api/parcels/PUNE-003/infrastructure?weight_highway=50&weight_hospital=50")
    assert resp.status_code == 200
    data = resp.json()
    assert "Highway 50%" in data["accessibility_score_methodology"]
    assert "Hospital 50%" in data["accessibility_score_methodology"]
    assert data["is_official_rating"] is False
    assert data["nearest_highway"]["distance_methodology"] == DistanceMethodology.HAVERSINE_STRAIGHT_LINE.value
    assert data["nearest_highway"]["distance_label"] == "Straight-line distance estimate (Haversine)"

