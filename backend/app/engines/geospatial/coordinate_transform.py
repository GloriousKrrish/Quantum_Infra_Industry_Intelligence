"""
Geodetic and Projected Coordinate Reference System Transformations.

Provides exact mathematical transformations between:
- WGS-84 Geographic Coordinates (EPSG:4326) [latitude, longitude in degrees]
- Universal Transverse Mercator (UTM) Zone 43N (EPSG:32643) [easting, northing in meters]

Geodetic Datum:
- WGS-84 Ellipsoid: semi-major axis a = 6,378,137.0 m, flattening f = 1 / 298.257223563
- UTM Zone 43N: Central Meridian = 75.0° E, False Easting = 500,000 m, False Northing = 0 m, Scale Factor k0 = 0.9996

Why UTM 43N for Pune:
Pune sits between 73.3° E and 74.5° E (within UTM Zone 43: 72° E to 78° E).
Projected coordinates eliminate spherical degree distortions when computing:
- True metric Euclidean distances (meters)
- Metric polygon surface areas (square meters / acres) without latitude-dependent cosine errors
- Concentric metric buffer envelopes (e.g., 500 m, 1,000 m, 5,000 m)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

# WGS-84 Ellipsoid constants
WGS84_A: float = 6378137.0  # semi-major axis in meters
WGS84_F: float = 1.0 / 298.257223563  # flattening
WGS84_B: float = WGS84_A * (1.0 - WGS84_F)  # semi-minor axis
WGS84_E2: float = 2.0 * WGS84_F - WGS84_F**2  # first eccentricity squared
WGS84_E_PRIME2: float = WGS84_E2 / (1.0 - WGS84_E2)  # second eccentricity squared

# UTM Zone 43N parameters
UTM43N_CENTRAL_MERIDIAN_DEG: float = 75.0  # 75° E
UTM_FALSE_EASTING: float = 500000.0  # meters
UTM_FALSE_NORTHING: float = 0.0  # meters (Northern Hemisphere)
UTM_SCALE_FACTOR: float = 0.9996  # k0

# Conversion constants
SQ_METERS_PER_ACRE: float = 4046.8564224


def wgs84_to_utm43n(lat: float, lng: float) -> Tuple[float, float]:
    """
    Project WGS-84 (lat, lng) to UTM Zone 43N (easting, northing) in meters.
    Uses exact Transverse Mercator series expansion.
    """
    lat_r = math.radians(lat)
    lon_r = math.radians(lng)
    lon0_r = math.radians(UTM43N_CENTRAL_MERIDIAN_DEG)

    sin_lat = math.sin(lat_r)
    cos_lat = math.cos(lat_r)
    tan_lat = math.tan(lat_r)

    # Radius of curvature in prime vertical
    N = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat**2)
    T = tan_lat**2
    C = WGS84_E_PRIME2 * cos_lat**2
    A = (lon_r - lon0_r) * cos_lat

    # Meridional distance from equator
    M = WGS84_A * (
        (1.0 - WGS84_E2 / 4.0 - 3.0 * WGS84_E2**2 / 64.0 - 5.0 * WGS84_E2**3 / 256.0) * lat_r
        - (3.0 * WGS84_E2 / 8.0 + 3.0 * WGS84_E2**2 / 32.0 + 45.0 * WGS84_E2**3 / 1024.0) * math.sin(2.0 * lat_r)
        + (15.0 * WGS84_E2**2 / 256.0 + 45.0 * WGS84_E2**3 / 1024.0) * math.sin(4.0 * lat_r)
        - (35.0 * WGS84_E2**3 / 3072.0) * math.sin(6.0 * lat_r)
    )

    # Transverse Mercator Easting
    easting = UTM_FALSE_EASTING + UTM_SCALE_FACTOR * N * (
        A
        + (1.0 - T + C) * A**3 / 6.0
        + (5.0 - 18.0 * T + T**2 + 72.0 * C - 58.0 * WGS84_E_PRIME2) * A**5 / 120.0
    )

    # Transverse Mercator Northing
    northing = UTM_FALSE_NORTHING + UTM_SCALE_FACTOR * (
        M
        + N * tan_lat * (
            A**2 / 2.0
            + (5.0 - T + 9.0 * C + 4.0 * C**2) * A**4 / 24.0
            + (61.0 - 58.0 * T + T**2 + 600.0 * C - 330.0 * WGS84_E_PRIME2) * A**6 / 720.0
        )
    )

    return easting, northing


def utm43n_to_wgs84(easting: float, northing: float) -> Tuple[float, float]:
    """
    Inverse Transverse Mercator: project UTM Zone 43N (easting, northing)
    back to WGS-84 (latitude, longitude) in decimal degrees.
    """
    e1 = (1.0 - math.sqrt(1.0 - WGS84_E2)) / (1.0 + math.sqrt(1.0 - WGS84_E2))
    lon0_r = math.radians(UTM43N_CENTRAL_MERIDIAN_DEG)

    x = easting - UTM_FALSE_EASTING
    y = northing - UTM_FALSE_NORTHING

    M = y / UTM_SCALE_FACTOR
    mu = M / (WGS84_A * (1.0 - WGS84_E2 / 4.0 - 3.0 * WGS84_E2**2 / 64.0 - 5.0 * WGS84_E2**3 / 256.0))

    # Footprint latitude phi1
    phi1 = (
        mu
        + (3.0 * e1 / 2.0 - 27.0 * e1**3 / 32.0) * math.sin(2.0 * mu)
        + (21.0 * e1**2 / 16.0 - 55.0 * e1**4 / 32.0) * math.sin(4.0 * mu)
        + (151.0 * e1**3 / 96.0) * math.sin(6.0 * mu)
        + (1097.0 * e1**4 / 512.0) * math.sin(8.0 * mu)
    )

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)

    N1 = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_phi1**2)
    T1 = tan_phi1**2
    C1 = WGS84_E_PRIME2 * cos_phi1**2
    R1 = WGS84_A * (1.0 - WGS84_E2) / ((1.0 - WGS84_E2 * sin_phi1**2)**1.5)
    D = x / (N1 * UTM_SCALE_FACTOR)

    lat_r = phi1 - (N1 * tan_phi1 / R1) * (
        D**2 / 2.0
        - (5.0 + 3.0 * T1 + 10.0 * C1 - 4.0 * C1**2 - 9.0 * WGS84_E_PRIME2) * D**4 / 24.0
        + (61.0 + 90.0 * T1 + 298.0 * C1 + 45.0 * T1**2 - 252.0 * WGS84_E_PRIME2 - 3.0 * C1**2) * D**6 / 720.0
    )

    lon_r = lon0_r + (
        D
        - (1.0 + 2.0 * T1 + C1) * D**3 / 6.0
        + (5.0 - 2.0 * C1 + 28.0 * T1 - 3.0 * C1**2 + 8.0 * WGS84_E_PRIME2 + 24.0 * T1**2) * D**5 / 120.0
    ) / cos_phi1

    return math.degrees(lat_r), math.degrees(lon_r)


def projected_euclidean_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate exact Euclidean distance in meters by projecting both
    coordinates to UTM Zone 43N plane.
    """
    e1, n1 = wgs84_to_utm43n(lat1, lng1)
    e2, n2 = wgs84_to_utm43n(lat2, lng2)
    return math.hypot(e2 - e1, n2 - n1)


def haversine_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate great-circle spherical distance in kilometers using Haversine formula.
    Includes clamping for antipodal / identical coordinate numerical stability.
    """
    r_earth = 6371.0088  # Mean Earth radius (IUGG) in km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a_clamped = min(1.0, max(0.0, a))
    return 2.0 * r_earth * math.asin(math.sqrt(a_clamped))


def calculate_polygon_geodesic_area(
    coordinates: List[List[float]],
) -> Tuple[float, float]:
    """
    Compute true surface area of a polygon ring by projecting coordinates
    to UTM Zone 43N and applying the surveyor's shoelace formula.

    Args:
        coordinates: List of [lng, lat] coordinate pairs (GeoJSON convention).

    Returns:
        (area_sq_meters, area_acres)
    """
    if len(coordinates) < 3:
        return 0.0, 0.0

    # Project all vertices to UTM Zone 43N (Easting, Northing in meters)
    projected = [wgs84_to_utm43n(pt[1], pt[0]) for pt in coordinates]

    # Shoelace formula on metric Cartesian coordinates
    n = len(projected)
    area2 = 0.0
    for i in range(n):
        j = (i + 1) % n
        area2 += projected[i][0] * projected[j][1] - projected[j][0] * projected[i][1]

    sq_meters = abs(area2) / 2.0
    acres = sq_meters / SQ_METERS_PER_ACRE
    return round(sq_meters, 2), round(acres, 4)


def calculate_polygon_centroid(
    coordinates: List[List[float]],
) -> Tuple[float, float]:
    """
    Compute centroid [lat, lng] of a polygon ring via area-weighted Cartesian center.
    Returns (centroid_lat, centroid_lng).
    """
    if not coordinates:
        return 0.0, 0.0

    if len(coordinates) < 3:
        # Fallback to arithmetic mean of points
        avg_lng = sum(pt[0] for pt in coordinates) / len(coordinates)
        avg_lat = sum(pt[1] for pt in coordinates) / len(coordinates)
        return round(avg_lat, 6), round(avg_lng, 6)

    # In UTM 43N plane
    projected = [wgs84_to_utm43n(pt[1], pt[0]) for pt in coordinates]
    n = len(projected)

    cx = 0.0
    cy = 0.0
    signed_area = 0.0

    for i in range(n):
        j = (i + 1) % n
        factor = projected[i][0] * projected[j][1] - projected[j][0] * projected[i][1]
        signed_area += factor
        cx += (projected[i][0] + projected[j][0]) * factor
        cy += (projected[i][1] + projected[j][1]) * factor

    signed_area *= 0.5
    if abs(signed_area) < 1e-5:
        # Collinear or degenerate: fallback to mean
        avg_lng = sum(pt[0] for pt in coordinates) / len(coordinates)
        avg_lat = sum(pt[1] for pt in coordinates) / len(coordinates)
        return round(avg_lat, 6), round(avg_lng, 6)

    cx /= (6.0 * signed_area)
    cy /= (6.0 * signed_area)

    # Unproject back to WGS-84
    c_lat, c_lng = utm43n_to_wgs84(cx, cy)
    return round(c_lat, 6), round(c_lng, 6)


def create_bounding_box(coordinates: List[List[float]]) -> Dict[str, float]:
    """Extract axis-aligned bounding box from a list of [lng, lat] coordinates."""
    if not coordinates:
        return {"min_lat": 0.0, "max_lat": 0.0, "min_lng": 0.0, "max_lng": 0.0}

    lngs = [pt[0] for pt in coordinates]
    lats = [pt[1] for pt in coordinates]

    return {
        "min_lat": round(min(lats), 6),
        "max_lat": round(max(lats), 6),
        "min_lng": round(min(lngs), 6),
        "max_lng": round(max(lngs), 6),
    }
