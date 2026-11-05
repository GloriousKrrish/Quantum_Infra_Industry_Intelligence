"""
Quantum Estate X — Real Geographic Intelligence Engine (RGIE) Package.
"""

from backend.app.engines.geospatial.coordinate_transform import (
    calculate_polygon_centroid,
    calculate_polygon_geodesic_area,
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
    generate_metric_buffer_polygon,
    is_point_in_polygon,
    validate_and_normalize_geojson,
    validate_wgs84_point,
)
from backend.app.engines.geospatial.geospatial_provenance import get_feature_provenance
from backend.app.engines.geospatial.government_data_ingestion import (
    get_administrative_boundaries,
    get_infrastructure_corridors,
    get_planning_zones,
    get_water_bodies,
)
from backend.app.engines.geospatial.network_analysis import get_road_network
from backend.app.engines.geospatial.osm_ingestion import query_osm_features
from backend.app.engines.geospatial.suitability_scoring import evaluate_geographic_suitability

__all__ = [
    "wgs84_to_utm43n",
    "utm43n_to_wgs84",
    "projected_euclidean_distance",
    "haversine_distance",
    "calculate_polygon_geodesic_area",
    "calculate_polygon_centroid",
    "validate_wgs84_point",
    "validate_and_normalize_geojson",
    "is_point_in_polygon",
    "generate_metric_buffer_polygon",
    "get_road_network",
    "get_spatial_index",
    "get_all_data_sources",
    "get_data_source_by_id",
    "get_administrative_boundaries",
    "get_infrastructure_corridors",
    "get_water_bodies",
    "get_planning_zones",
    "query_osm_features",
    "evaluate_geographic_suitability",
    "analyze_location_geospatial",
    "check_administrative_containment",
    "check_environmental_and_zoning_constraints",
    "get_feature_provenance",
]
