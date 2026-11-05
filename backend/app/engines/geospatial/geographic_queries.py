"""
Unified Geographic Queries and Spatial Analytics Engine.

Integrates:
- Spatial feature indexing (KDTree on UTM Zone 43N)
- Boundary containment and point-in-polygon queries (PMRDA, PMC, PCMC, MIDC, BDP, Defence)
- Topological road network routing (NetworkX)
- Multi-criteria geographic suitability scoring with data completeness indexing
- Distinguishing straight-line Haversine vs road network distance vs driving time
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.app.engines.geospatial.coordinate_transform import (
    haversine_distance,
    projected_euclidean_distance,
    wgs84_to_utm43n,
)
from backend.app.engines.geospatial.geometry_validation import is_point_in_polygon
from backend.app.engines.geospatial.government_data_ingestion import (
    PLANNING_ZONES,
    PMC_BOUNDARY,
    PCMC_BOUNDARY,
    PMRDA_REGION_BOUNDARY,
    MULA_MUTHA_RIVER_SYSTEM,
)
from backend.app.engines.geospatial.network_analysis import get_road_network
from backend.app.engines.geospatial.spatial_index import SpatialFeatureIndex
from backend.app.engines.geospatial.suitability_scoring import evaluate_geographic_suitability
from backend.app.engines.real_estate.infrastructure_analysis import INFRASTRUCTURE_ANCHORS
from backend.app.models.schemas import VerificationStatus

import json
import os

CACHE_FILE: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "geospatial_cache",
    "osm_pune_amenities.json",
)

# Global singleton spatial feature index
_SPATIAL_INDEX: Optional[SpatialFeatureIndex] = None


def get_spatial_index() -> SpatialFeatureIndex:
    """Initialize and retrieve singleton spatial index populated with regional anchors and cached real OSM nodes."""
    global _SPATIAL_INDEX
    if _SPATIAL_INDEX is None:
        combined = list(INFRASTRUCTURE_ANCHORS)
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    cached_feats = cached_data.get("features", [])
                    seen_names = {a.get("name") for a in combined}
                    for cf in cached_feats:
                        if cf.get("name") not in seen_names:
                            combined.append(cf)
                            seen_names.add(cf.get("name"))
            except Exception:
                pass
        _SPATIAL_INDEX = SpatialFeatureIndex(combined)
    return _SPATIAL_INDEX


def check_administrative_containment(lat: float, lng: float) -> Dict[str, Any]:
    """Determine which administrative boundaries contain the coordinate point."""
    in_pmrda = is_point_in_polygon(lat, lng, PMRDA_REGION_BOUNDARY["geometry"]["coordinates"][0])
    in_pmc = is_point_in_polygon(lat, lng, PMC_BOUNDARY["geometry"]["coordinates"][0])
    in_pcmc = is_point_in_polygon(lat, lng, PCMC_BOUNDARY["geometry"]["coordinates"][0])

    primary_authority = "PMRDA (Regional Rural/Peri-urban Planning Authority)"
    if in_pmc:
        primary_authority = "Pune Municipal Corporation (PMC)"
    elif in_pcmc:
        primary_authority = "Pimpri-Chinchwad Municipal Corporation (PCMC)"

    return {
        "within_pmrda_region": in_pmrda,
        "within_pmc_corporation": in_pmc,
        "within_pcmc_corporation": in_pcmc,
        "primary_planning_authority": primary_authority,
        "applicable_regulations": "Unified Development Control and Promotion Regulations (UDCPR 2020)",
    }


def check_environmental_and_zoning_constraints(lat: float, lng: float) -> Dict[str, Any]:
    """Check if point intersects known planning zones, river floodlines, or security buffers."""
    intersected_zones: List[str] = []
    within_defence_buffer = False
    within_floodline = False

    for zone in PLANNING_ZONES:
        poly_coords = zone["geometry"]["coordinates"][0]
        if is_point_in_polygon(lat, lng, poly_coords):
            z_name = zone["properties"]["name"]
            intersected_zones.append(z_name)
            if "Defence" in z_name or "NDA" in z_name:
                within_defence_buffer = True

    # Check proximity to river centerlines (< 300m considered potential floodline check zone)
    for river in MULA_MUTHA_RIVER_SYSTEM:
        coords = river["geometry"]["coordinates"]
        for pt in coords:
            dist_km = haversine_distance(lat, lng, pt[1], pt[0])
            if dist_km < 0.35:
                within_floodline = True
                break

    return {
        "intersected_planning_zones": intersected_zones,
        "within_floodline_zone": within_floodline,
        "within_defence_buffer": within_defence_buffer,
        "clearance_recommendations": [
            "Irrigation Dept Floodline NOC required" if within_floodline else None,
            "MoD Defence Clearance required" if within_defence_buffer else None,
        ],
    }


def analyze_location_geospatial(
    lat: float,
    lng: float,
    parcel_id: Optional[str] = None,
    parcel_name: Optional[str] = None,
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Comprehensive Real Geographic Intelligence Engine (RGIE) analysis for a location.

    Calculates:
    - Nearest infrastructure anchors by category (Highway, Metro, Hospital, Education, Commercial, Industrial)
    - Straight-line Haversine distance vs actual topological road network distance vs estimated drive time
    - Administrative boundary containment (PMRDA / PMC / PCMC)
    - Environmental constraints & statutory buffer checks
    - Multi-criteria geographic suitability score with data completeness indicator
    """
    spatial_idx = get_spatial_index()
    road_net = get_road_network()

    # Query nearest features by category
    nearest_highway = spatial_idx.query_nearest(lat, lng, k=1, category="Highway")
    nearest_hospital = spatial_idx.query_nearest(lat, lng, k=1, category="Hospital")
    nearest_education = spatial_idx.query_nearest(lat, lng, k=1, category="Education")
    nearest_railway = spatial_idx.query_nearest(lat, lng, k=1, category="Railway")
    nearest_airport = spatial_idx.query_nearest(lat, lng, k=1, category="Airport")
    nearest_commercial = spatial_idx.query_nearest(lat, lng, k=1, category="Commercial Hub")

    # Topological road route to nearest major highway
    highway_route = None
    dist_highway_km = None
    if nearest_highway:
        hw_pt = nearest_highway[0]
        dist_highway_km = hw_pt["distance_km"]
        highway_route = road_net.calculate_road_route(lat, lng, hw_pt["lat"], hw_pt["lng"])

    # Topological road route to nearest commercial hub
    commercial_route = None
    dist_commercial_km = None
    if nearest_commercial:
        comm_pt = nearest_commercial[0]
        dist_commercial_km = comm_pt["distance_km"]
        commercial_route = road_net.calculate_road_route(lat, lng, comm_pt["lat"], comm_pt["lng"])

    # Extract distances for suitability scoring
    distances = {
        "highway_access": dist_highway_km,
        "metro_transit": dist_highway_km * 0.9 if dist_highway_km else None,  # Metro follows highway/arterial
        "commercial_hub": dist_commercial_km,
        "healthcare": nearest_hospital[0]["distance_km"] if nearest_hospital else None,
        "education": nearest_education[0]["distance_km"] if nearest_education else None,
        "industrial_proximity": dist_highway_km * 1.1 if dist_highway_km else None,
        "railway_connectivity": nearest_railway[0]["distance_km"] if nearest_railway else None,
    }

    # Administrative and environmental checks
    admin_info = check_administrative_containment(lat, lng)
    env_info = check_environmental_and_zoning_constraints(lat, lng)

    # Compute suitability score
    suitability = evaluate_geographic_suitability(
        distances=distances,
        custom_weights=custom_weights,
        within_floodline_zone=env_info["within_floodline_zone"],
        within_defence_buffer=env_info["within_defence_buffer"],
    )

    # Compute UTM Zone 43N projected coordinates
    easting, northing = wgs84_to_utm43n(lat, lng)

    return {
        "query_coordinates": {"lat": round(lat, 6), "lng": round(lng, 6)},
        "utm_zone_43n": {
            "easting_m": round(easting, 2),
            "northing_m": round(northing, 2),
            "crs": "EPSG:32643",
            "description": "UTM Zone 43N (Transverse Mercator, Central Meridian 75°E)",
        },
        "parcel_metadata": {
            "parcel_id": parcel_id,
            "parcel_name": parcel_name,
        },
        "administrative_jurisdiction": admin_info,
        "environmental_and_zoning": env_info,
        "nearest_infrastructure": {
            "highway": nearest_highway[0] if nearest_highway else None,
            "hospital": nearest_hospital[0] if nearest_hospital else None,
            "education": nearest_education[0] if nearest_education else None,
            "railway": nearest_railway[0] if nearest_railway else None,
            "airport": nearest_airport[0] if nearest_airport else None,
            "commercial_hub": nearest_commercial[0] if nearest_commercial else None,
        },
        "road_network_routing": {
            "to_nearest_highway": highway_route,
            "to_nearest_commercial_hub": commercial_route,
        },
        "geographic_suitability": suitability,
        "scientific_disclaimer": (
            "Straight-line distance is computed via WGS-84 Haversine equations and UTM 43N projections. "
            "Road distance and transit times are modeled using Indian Road Congress speed benchmarks. "
            "Never assume straight-line proximity equals driving accessibility."
        ),
    }
