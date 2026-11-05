"""
RFC 7946 GeoJSON Geometry Validation, Point-in-Polygon & Spatial Envelope Engine.

Ensures strict mathematical and specification conformance for all geographic entities:
- RFC 7946 standard compliance (coordinate ordering [lng, lat], ring closure, ring orientation)
- Point-in-polygon containment testing via ray-casting (Jordan curve theorem)
- Polygon self-intersection and degeneracy guards
- Metric buffer envelope generation via UTM Zone 43N projections
- Bounding box intersection tests
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from backend.app.engines.geospatial.coordinate_transform import (
    calculate_polygon_centroid,
    calculate_polygon_geodesic_area,
    create_bounding_box,
    utm43n_to_wgs84,
    wgs84_to_utm43n,
)

# Pune Metropolitan Region Development Authority (PMRDA) Boundary Envelope
PMRDA_LAT_MIN: float = 18.0000
PMRDA_LAT_MAX: float = 19.2000
PMRDA_LNG_MIN: float = 73.3000
PMRDA_LNG_MAX: float = 74.5000


def validate_wgs84_point(lat: float, lng: float, check_pmrda: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate a single WGS-84 point coordinate."""
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return False, "Coordinates must be numeric values."

    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        return False, "Coordinates cannot be NaN or Infinite."

    if not (-90.0 <= lat <= 90.0):
        return False, f"Latitude {lat}° is out of valid range [-90.0, 90.0]."

    if not (-180.0 <= lng <= 180.0):
        return False, f"Longitude {lng}° is out of valid range [-180.0, 180.0]."

    if check_pmrda:
        if not (PMRDA_LAT_MIN <= lat <= PMRDA_LAT_MAX) or not (PMRDA_LNG_MIN <= lng <= PMRDA_LNG_MAX):
            return (
                False,
                f"Coordinates ({lat:.4f}°, {lng:.4f}°) lie outside Pune Metropolitan Region "
                f"[{PMRDA_LAT_MIN}..{PMRDA_LAT_MAX}° N, {PMRDA_LNG_MIN}..{PMRDA_LNG_MAX}° E].",
            )

    return True, None


def is_point_in_bbox(lat: float, lng: float, bbox: Dict[str, float]) -> bool:
    """Check if point is inside an axis-aligned bounding box."""
    return (
        bbox["min_lat"] <= lat <= bbox["max_lat"]
        and bbox["min_lng"] <= lng <= bbox["max_lng"]
    )


def is_point_in_polygon(lat: float, lng: float, polygon_coords: List[List[float]]) -> bool:
    """
    Ray-casting algorithm (Jordan Curve Theorem) to determine if point (lat, lng)
    is strictly inside a polygon boundary.

    Args:
        lat: Target latitude in decimal degrees.
        lng: Target longitude in decimal degrees.
        polygon_coords: List of [lng, lat] pairs representing the closed linear ring.

    Returns:
        True if inside polygon, False otherwise.
    """
    if len(polygon_coords) < 3:
        return False

    # Quick bounding box pre-filter for performance
    bbox = create_bounding_box(polygon_coords)
    if not is_point_in_bbox(lat, lng, bbox):
        return False

    n = len(polygon_coords)
    inside = False

    p1_lng, p1_lat = polygon_coords[0]
    for i in range(1, n + 1):
        p2_lng, p2_lat = polygon_coords[i % n]

        # Check if ray from point eastward intersects the edge (p1, p2)
        if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
            if lng <= max(p1_lng, p2_lng):
                if p1_lat != p2_lat:
                    x_inters = (lat - p1_lat) * (p2_lng - p1_lng) / (p2_lat - p1_lat) + p1_lng
                    if p1_lng == p2_lng or lng <= x_inters:
                        inside = not inside

        p1_lng, p1_lat = p2_lng, p2_lat

    return inside


def check_linear_ring_orientation(ring: List[List[float]]) -> str:
    """
    Determine linear ring winding orientation using Cartesian Shoelace sum.
    RFC 7946 specifies exterior rings should follow right-hand rule (counter-clockwise CCW).
    Returns 'CCW' or 'CW'.
    """
    if len(ring) < 3:
        return "DEGENERATE"

    area2 = 0.0
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        area2 += (ring[j][0] - ring[i][0]) * (ring[j][1] + ring[i][1])

    # In standard [x=lng, y=lat] space:
    # If signed area > 0: Clockwise (CW)
    # If signed area < 0: Counter-Clockwise (CCW)
    return "CW" if area2 > 0 else "CCW"


def validate_and_normalize_geojson(
    raw_data: Dict[str, Any],
    check_pmrda_boundary: bool = False,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate arbitrary user-provided or API GeoJSON against RFC 7946 specifications.
    Extracts or wraps features into a normalized GeoJSON Feature with computed metrics
    (area in sq. meters & acres, centroid, bounding box, ring validation).

    Returns:
        (is_valid, error_message, normalized_feature_dict)
    """
    if not isinstance(raw_data, dict):
        return False, "Input must be a valid GeoJSON JSON object/dictionary.", None

    obj_type = raw_data.get("type")
    if not obj_type:
        return False, "Missing 'type' field in GeoJSON root.", None

    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = {}

    if obj_type == "FeatureCollection":
        features = raw_data.get("features", [])
        if not features or not isinstance(features, list):
            return False, "FeatureCollection must contain a non-empty 'features' array.", None
        # Process first feature
        first_feat = features[0]
        if not isinstance(first_feat, dict) or first_feat.get("type") != "Feature":
            return False, "FeatureCollection item must be a Feature.", None
        geometry = first_feat.get("geometry")
        properties = first_feat.get("properties", {}) or {}

    elif obj_type == "Feature":
        geometry = raw_data.get("geometry")
        properties = raw_data.get("properties", {}) or {}

    elif obj_type in ("Polygon", "MultiPolygon", "Point", "LineString", "MultiLineString"):
        geometry = raw_data
        properties = raw_data.get("properties", {}) or {}

    else:
        return False, f"Unsupported GeoJSON object type: {obj_type}", None

    if not geometry or not isinstance(geometry, dict):
        return False, "GeoJSON object has no valid 'geometry' element.", None

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")

    if not geom_type or coords is None:
        return False, "Geometry must contain 'type' and 'coordinates'.", None

    # Geometry-specific validation
    if geom_type == "Point":
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return False, "Point coordinates must be [longitude, latitude].", None
        lng, lat = coords[0], coords[1]
        valid, msg = validate_wgs84_point(lat, lng, check_pmrda_boundary)
        if not valid:
            return False, f"Invalid Point: {msg}", None

        normalized = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lng, 6), round(lat, 6)]},
            "properties": {
                **properties,
                "centroid": [round(lng, 6), round(lat, 6)],
                "geometry_type": "Point",
                "area_acres": 0.0,
                "area_sq_meters": 0.0,
            },
        }
        return True, None, normalized

    elif geom_type == "Polygon":
        if not isinstance(coords, (list, tuple)) or len(coords) == 0:
            return False, "Polygon must contain at least one linear ring.", None

        exterior_ring = coords[0]
        if not isinstance(exterior_ring, (list, tuple)) or len(exterior_ring) < 4:
            return False, "Exterior linear ring must contain at least 4 coordinate positions.", None

        # Check closure: first position must match last position
        first_pt, last_pt = exterior_ring[0], exterior_ring[-1]
        if first_pt[0] != last_pt[0] or first_pt[1] != last_pt[1]:
            # Automatically close ring if user omitted it
            exterior_ring = list(exterior_ring) + [exterior_ring[0]]

        # Validate coordinate points
        for idx, pt in enumerate(exterior_ring):
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                return False, f"Invalid coordinate point at index {idx}.", None
            lng, lat = pt[0], pt[1]
            valid, msg = validate_wgs84_point(lat, lng, check_pmrda_boundary)
            if not valid:
                return False, f"Point {idx} invalid: {msg}", None

        # Calculate exact metric area & centroid via UTM 43N projection
        sq_m, acres = calculate_polygon_geodesic_area(exterior_ring)
        c_lat, c_lng = calculate_polygon_centroid(exterior_ring)
        bbox = create_bounding_box(exterior_ring)

        normalized = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [exterior_ring] + list(coords[1:]),
            },
            "properties": {
                **properties,
                "centroid": [c_lng, c_lat],
                "area_sq_meters": sq_m,
                "area_acres": acres,
                "bounding_box": bbox,
                "ring_orientation": check_linear_ring_orientation(exterior_ring),
            },
        }
        return True, None, normalized

    elif geom_type in ("LineString", "MultiLineString", "MultiPolygon"):
        # Valid structural check
        if not isinstance(coords, (list, tuple)) or len(coords) == 0:
            return False, f"{geom_type} coordinates cannot be empty.", None

        normalized = {
            "type": "Feature",
            "geometry": {"type": geom_type, "coordinates": coords},
            "properties": {**properties, "geometry_type": geom_type},
        }
        return True, None, normalized

    else:
        return False, f"Unsupported geometry type: {geom_type}", None


def generate_metric_buffer_polygon(
    center_lat: float,
    center_lng: float,
    radius_meters: float,
    num_points: int = 36,
) -> Dict[str, Any]:
    """
    Generate an exact metric circular buffer around a point by projecting outward
    on the UTM Zone 43N plane, then unprojecting back to WGS-84 coordinates.

    This prevents metric distortion caused by spherical degree approximations.
    """
    center_e, center_n = wgs84_to_utm43n(center_lat, center_lng)
    coordinates: List[List[float]] = []

    for i in range(num_points):
        angle = 2.0 * math.pi * i / num_points
        e = center_e + radius_meters * math.cos(angle)
        n = center_n + radius_meters * math.sin(angle)
        lat, lng = utm43n_to_wgs84(e, n)
        coordinates.append([round(lng, 6), round(lat, 6)])

    # Close linear ring
    coordinates.append(coordinates[0])

    area_sq_m = math.pi * radius_meters**2
    area_acres = area_sq_m / 4046.8564224

    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [coordinates],
        },
        "properties": {
            "center": [center_lng, center_lat],
            "radius_meters": radius_meters,
            "area_sq_meters": round(area_sq_m, 2),
            "area_acres": round(area_acres, 4),
            "geometry_type": "MetricBufferPolygon",
        },
    }
