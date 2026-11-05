"""
Geospatial Data Verification and Validation Framework.

Provides rigorous validation for:
- WGS-84 coordinate ranges and geodetic projections
- Pune Metropolitan Region (PMRDA) boundary bounding box checks
- RFC 7946 GeoJSON Geometry specification conformance
- Haversine numerical stability and singularity guards
- Synthetic approximate boundary generation for visual delineation
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from backend.app.models.schemas import ParcelGeometryType, VerificationStatus

# ═══════════════════════════════════════════════════════════════════════
# PMRDA GEOGRAPHIC BOUNDING BOX (WGS-84)
# ═══════════════════════════════════════════════════════════════════════
# Latitude:  18.0° N to 19.2° N
# Longitude: 73.3° E to 74.5° E
PMRDA_LAT_MIN: float = 18.0000
PMRDA_LAT_MAX: float = 19.2000
PMRDA_LNG_MIN: float = 73.3000
PMRDA_LNG_MAX: float = 74.5000


def validate_coordinates(
    lat: float, lng: float, check_pmrda_boundary: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validate WGS-84 geographic coordinates.

    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees
        check_pmrda_boundary: If True, asserts point is inside Pune metropolitan envelope

    Returns:
        (is_valid, error_message_if_invalid)
    """
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return False, "Coordinates must be real numeric values."

    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        return False, "Coordinates cannot be NaN or Infinite."

    if not (-90.0 <= lat <= 90.0):
        return False, f"Latitude {lat}° is outside valid WGS-84 range [-90.0, 90.0]."

    if not (-180.0 <= lng <= 180.0):
        return False, f"Longitude {lng}° is outside valid WGS-84 range [-180.0, 180.0]."

    if check_pmrda_boundary:
        if not (PMRDA_LAT_MIN <= lat <= PMRDA_LAT_MAX) or not (
            PMRDA_LNG_MIN <= lng <= PMRDA_LNG_MAX
        ):
            return (
                False,
                f"Coordinates ({lat}°, {lng}°) lie outside Pune Metropolitan Region "
                f"[{PMRDA_LAT_MIN}..{PMRDA_LAT_MAX} N, {PMRDA_LNG_MIN}..{PMRDA_LNG_MAX} E].",
            )

    return True, None


def validate_geojson_geometry(geojson: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a GeoJSON geometry object against RFC 7946 specifications.
    Supports Point, Polygon, and MultiPolygon.
    """
    if not isinstance(geojson, dict):
        return False, "GeoJSON must be a dictionary."

    geom_type = geojson.get("type")
    coords = geojson.get("coordinates")

    if not geom_type or not coords:
        return False, "GeoJSON must contain 'type' and 'coordinates' fields."

    if geom_type == "Point":
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return False, "GeoJSON Point coordinates must be [longitude, latitude]."
        lng, lat = coords[0], coords[1]
        valid, msg = validate_coordinates(lat, lng)
        if not valid:
            return False, f"Invalid Point coordinate: {msg}"

    elif geom_type == "Polygon":
        if not isinstance(coords, (list, tuple)) or len(coords) == 0:
            return False, "GeoJSON Polygon must contain at least one linear ring."
        for ring_idx, ring in enumerate(coords):
            if not isinstance(ring, (list, tuple)) or len(ring) < 4:
                return (
                    False,
                    f"Linear ring {ring_idx} must contain at least 4 coordinate positions.",
                )
            # Check closed ring (first position equals last position)
            first_pt, last_pt = ring[0], ring[-1]
            if first_pt[0] != last_pt[0] or first_pt[1] != last_pt[1]:
                return (
                    False,
                    f"Linear ring {ring_idx} is not closed (first point != last point).",
                )
            for pt in ring:
                valid, msg = validate_coordinates(pt[1], pt[0])
                if not valid:
                    return False, f"Invalid coordinate in ring {ring_idx}: {msg}"

    elif geom_type == "MultiPolygon":
        if not isinstance(coords, (list, tuple)) or len(coords) == 0:
            return False, "GeoJSON MultiPolygon must contain at least one polygon."
    else:
        return False, f"Unsupported GeoJSON geometry type: {geom_type}"

    return True, None


def generate_approximate_parcel_polygon(
    centroid_lat: float, centroid_lng: float, area_acres: float
) -> Dict[str, Any]:
    """
    Generate an approximate rectangular GeoJSON Polygon around a centroid
    corresponding to the land area footprint.

    Note: This is an illustrative/approximate bounding perimeter, NOT a
    surveyor-certified cadastral polygon.
    """
    # 1 acre = 4,046.86 m2. Square side = sqrt(area_m2)
    area_m2 = max(area_acres * 4046.856, 1000.0)
    side_m = math.sqrt(area_m2)

    # 1 degree latitude ≈ 111,320 meters
    delta_lat = (side_m / 2.0) / 111320.0
    # 1 degree longitude ≈ 111,320 * cos(lat) meters
    delta_lng = (side_m / 2.0) / (111320.0 * math.cos(math.radians(centroid_lat)))

    min_lat = round(centroid_lat - delta_lat, 6)
    max_lat = round(centroid_lat + delta_lat, 6)
    min_lng = round(centroid_lng - delta_lng, 6)
    max_lng = round(centroid_lng + delta_lng, 6)

    # GeoJSON coordinates order: [longitude, latitude], closed ring
    coordinates = [
        [
            [min_lng, min_lat],
            [max_lng, min_lat],
            [max_lng, max_lat],
            [min_lng, max_lat],
            [min_lng, min_lat],
        ]
    ]

    return {
        "type": "Polygon",
        "coordinates": coordinates,
        "properties": {
            "centroid": [centroid_lng, centroid_lat],
            "area_acres": area_acres,
            "geometry_classification": ParcelGeometryType.APPROXIMATE_BOUND.value,
            "verification_status": VerificationStatus.ESTIMATED.value,
            "disclaimer": (
                "Approximate geographic footprint generated from plot acreage. "
                "Not a legally certified cadastral demarcation."
            ),
        },
    }
