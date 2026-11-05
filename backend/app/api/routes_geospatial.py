"""
API Router for the Real Geographic Intelligence Engine (RGIE) — Phase 1.8.

Exposes REST endpoints for:
- Data sources and statutory dataset catalog
- Administrative boundaries (PMRDA, PMC, PCMC)
- Infrastructure corridors (Expressways, Highways, Metro Lines)
- Spatial indexing and radius/nearest neighbor queries
- Comprehensive spatial analytics (straight-line vs road network distance & drive times)
- User GeoJSON parcel import with RFC 7946 validation
- Feature provenance and lineage inspection
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from backend.app.engines.geospatial.data_sources import (
    get_all_data_sources,
    get_data_source_by_id,
)
from backend.app.engines.geospatial.geographic_queries import (
    analyze_location_geospatial,
    get_spatial_index,
)
from backend.app.engines.geospatial.geometry_validation import (
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
from backend.app.models.schemas import ProvenanceRecord, VerificationStatus
from backend.app.schemas.geospatial import (
    GeoJSONImportRequest,
    GeoJSONImportResponse,
    GeospatialAnalyzeRequest,
    GeospatialQueryRequest,
    GeospatialSourcesResponse,
)

router = APIRouter(prefix="/api/geospatial", tags=["Real Geographic Intelligence Engine"])


@router.get(
    "/health",
    summary="Geospatial engine operational health",
    description="Returns operational status of the spatial index, road network graph, and projection engines.",
)
async def get_geospatial_health() -> Dict[str, Any]:
    """Return health and indexing metrics for RGIE."""
    spatial_idx = get_spatial_index()
    road_net = get_road_network()

    return {
        "status": "operational",
        "engine": "Real Geographic Intelligence Engine (RGIE)",
        "version": "1.8.0",
        "coordinate_reference_systems": {
            "geographic_crs": "EPSG:4326 (WGS-84)",
            "projected_metric_crs": "EPSG:32643 (UTM Zone 43N)",
        },
        "spatial_index": {
            "indexed_features_count": len(spatial_idx.features),
            "algorithm": "scipy.spatial.KDTree on Metric UTM Plane",
        },
        "network_graph": {
            "nodes_count": road_net.graph.number_of_nodes(),
            "edges_count": road_net.graph.number_of_edges(),
            "routing_algorithm": "Dijkstra Shortest Path with IRC-106 Speed Calibration",
        },
    }


@router.get(
    "/sources",
    response_model=GeospatialSourcesResponse,
    summary="Catalog of verified geographic data sources",
    description="Returns verified metadata for all integrated datasets (PMRDA, PMC, PCMC, MahaBhulekh, OSM, etc.).",
)
async def list_geospatial_sources() -> GeospatialSourcesResponse:
    """Return catalog of all verified regional geospatial sources."""
    sources = get_all_data_sources()
    return GeospatialSourcesResponse(sources_count=len(sources), sources=sources)


@router.get(
    "/datasets",
    summary="List available geographic datasets",
    description="Returns summary listing of available spatial layers in the platform.",
)
async def list_geospatial_datasets() -> List[Dict[str, Any]]:
    """Return summary list of available spatial layers."""
    sources = get_all_data_sources()
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "publisher": s["publisher"],
            "coverage": s["geographic_coverage"],
            "provenance_tier": s["provenance_tier"],
            "confidence_level": s["confidence_level"],
            "update_frequency": s["update_frequency"],
        }
        for s in sources
    ]


@router.get(
    "/datasets/{dataset_id}",
    summary="Get dataset details by ID",
    description="Returns complete metadata and provenance for a specific dataset ID.",
)
async def get_dataset_details(dataset_id: str = Path(...)) -> Dict[str, Any]:
    """Retrieve metadata for a single dataset ID."""
    ds = get_data_source_by_id(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return ds


@router.get(
    "/boundaries",
    summary="Administrative boundary GeoJSON features",
    description="Returns PMRDA regional limits, PMC municipal boundaries, and PCMC boundary polygons.",
)
async def get_boundaries() -> Dict[str, Any]:
    """Return administrative boundaries FeatureCollection."""
    return get_administrative_boundaries()


@router.get(
    "/infrastructure",
    summary="Regional infrastructure corridors and hydrological layers",
    description="Returns major road expressways, highways, metro lines, rivers, and planning zones.",
)
async def get_infrastructure_layers() -> Dict[str, Any]:
    """Return consolidated infrastructure GeoJSON layers."""
    return {
        "corridors": get_infrastructure_corridors(),
        "water_bodies": get_water_bodies(),
        "planning_zones": get_planning_zones(),
    }


@router.get(
    "/features/nearby",
    summary="Find geographic features near coordinates",
    description="Queries indexed features within radius (meters) of (lat, lng) with optional category filter.",
)
async def get_nearby_features(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    radius_meters: float = Query(default=5000.0, ge=100.0, le=50000.0),
    category: Optional[str] = Query(default=None),
) -> List[Dict[str, Any]]:
    """Query features within radius in meters using metric spatial index."""
    valid, msg = validate_wgs84_point(lat, lng)
    if not valid:
        raise HTTPException(status_code=422, detail=msg)

    spatial_idx = get_spatial_index()
    return spatial_idx.query_radius(
        lat=lat,
        lng=lng,
        radius_meters=radius_meters,
        category=category,
    )


@router.post(
    "/query",
    summary="Execute specific spatial or geometric query",
    description="Executes radius, nearest-neighbor, point-in-polygon, or bounding-box spatial queries.",
)
async def execute_spatial_query(req: GeospatialQueryRequest) -> Dict[str, Any]:
    """Execute spatial indexing or polygon containment query."""
    spatial_idx = get_spatial_index()

    if req.query_type == "radius":
        if req.lat is None or req.lng is None:
            raise HTTPException(status_code=422, detail="Query type 'radius' requires 'lat' and 'lng'.")
        results = spatial_idx.query_radius(
            lat=req.lat,
            lng=req.lng,
            radius_meters=req.radius_meters,
            category=req.category,
        )
        return {"query_type": "radius", "count": len(results), "features": results}

    elif req.query_type == "nearest":
        if req.lat is None or req.lng is None:
            raise HTTPException(status_code=422, detail="Query type 'nearest' requires 'lat' and 'lng'.")
        results = spatial_idx.query_nearest(
            lat=req.lat,
            lng=req.lng,
            k=req.k,
            category=req.category,
        )
        return {"query_type": "nearest", "count": len(results), "features": results}

    elif req.query_type == "point_in_polygon":
        if req.lat is None or req.lng is None or not req.polygon_coords:
            raise HTTPException(
                status_code=422,
                detail="Query type 'point_in_polygon' requires 'lat', 'lng', and 'polygon_coords'.",
            )
        is_inside = is_point_in_polygon(req.lat, req.lng, req.polygon_coords)
        return {
            "query_type": "point_in_polygon",
            "point": [req.lng, req.lat],
            "is_inside": is_inside,
        }

    else:
        raise HTTPException(status_code=422, detail=f"Unsupported query_type '{req.query_type}'.")


@router.post(
    "/analyze",
    summary="Comprehensive geographic intelligence analysis for a parcel or coordinates",
    description="Evaluates nearest infrastructure, road routing vs straight-line distance, suitability score, and constraints.",
)
async def analyze_geospatial_location(req: GeospatialAnalyzeRequest) -> Dict[str, Any]:
    """Execute deep spatial intelligence analysis for a coordinate location."""
    valid, msg = validate_wgs84_point(req.lat, req.lng)
    if not valid:
        raise HTTPException(status_code=422, detail=msg)

    return analyze_location_geospatial(
        lat=req.lat,
        lng=req.lng,
        parcel_id=req.parcel_id,
        parcel_name=req.parcel_name,
        custom_weights=req.custom_weights,
    )


@router.post(
    "/import/geojson",
    response_model=GeoJSONImportResponse,
    summary="Import, validate, and normalize user GeoJSON parcel geometry",
    description="Validates RFC 7946 compliance, calculates exact metric area (acres), computes centroid, and tags provenance.",
)
async def import_user_geojson(req: GeoJSONImportRequest) -> GeoJSONImportResponse:
    """Validate and ingest user-supplied GeoJSON polygon geometry."""
    is_valid, err_msg, normalized = validate_and_normalize_geojson(
        raw_data=req.geojson_data,
        check_pmrda_boundary=req.check_pmrda_boundary,
    )

    if not is_valid or not normalized:
        raise HTTPException(
            status_code=422,
            detail=f"GeoJSON validation failed: {err_msg}",
        )

    props = normalized.get("properties", {})
    centroid = props.get("centroid", [0.0, 0.0])
    area_acres = props.get("area_acres", 0.0)
    area_sq_m = props.get("area_sq_meters", 0.0)

    parcel_id = f"USER-{uuid.uuid4().hex[:6].upper()}"

    # Attach provenance tags
    props["parcel_id"] = parcel_id
    props["parcel_name"] = req.parcel_name or "Custom User Parcel"
    props["verification_status"] = VerificationStatus.USER_PROVIDED.value
    props["geometry_classification"] = "USER_PROVIDED"

    return GeoJSONImportResponse(
        is_valid=True,
        parcel_id=parcel_id,
        parcel_name=req.parcel_name or "Custom User Parcel",
        centroid=centroid,
        area_acres=area_acres,
        area_sq_meters=area_sq_m,
        normalized_geojson=normalized,
        provenance_tier=VerificationStatus.USER_PROVIDED.value,
        statutory_warning=(
            "User-supplied geometry is accepted for visualization and preliminary spatial analysis. "
            "It does NOT constitute official cadastral demarcation or title certification."
        ),
    )


@router.get(
    "/provenance/{feature_id}",
    response_model=ProvenanceRecord,
    summary="Get provenance record for a geographic feature",
    description="Returns formal lineage, publisher, and confidence metrics for any feature ID.",
)
async def get_geospatial_provenance_endpoint(feature_id: str = Path(...)) -> ProvenanceRecord:
    """Retrieve typed provenance record for a feature ID."""
    return get_feature_provenance(feature_id)
