"""
Pydantic v2 Request & Response Schemas for the Real Geographic Intelligence Engine (RGIE).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GeospatialSourcesResponse(BaseModel):
    """Response containing catalog of registered geographic data sources."""
    model_config = ConfigDict(from_attributes=True)

    sources_count: int
    sources: List[Dict[str, Any]]


class GeospatialAnalyzeRequest(BaseModel):
    """Request for comprehensive spatial intelligence analysis."""
    model_config = ConfigDict(from_attributes=True)

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude (WGS-84)")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude (WGS-84)")
    parcel_id: Optional[str] = None
    parcel_name: Optional[str] = None
    custom_weights: Optional[Dict[str, float]] = None


class GeospatialQueryRequest(BaseModel):
    """Request for specific spatial indexing or geometric query."""
    model_config = ConfigDict(from_attributes=True)

    query_type: str = Field(
        default="radius",
        description="'radius', 'nearest', 'point_in_polygon', or 'bbox'",
    )
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    radius_meters: float = Field(default=3000.0, ge=100.0, le=50000.0)
    category: Optional[str] = None
    k: int = Field(default=3, ge=1, le=20)
    polygon_coords: Optional[List[List[float]]] = None
    bbox: Optional[Dict[str, float]] = None


class GeoJSONImportRequest(BaseModel):
    """Request to import and validate user-supplied GeoJSON parcel geometry."""
    model_config = ConfigDict(from_attributes=True)

    geojson_data: Dict[str, Any] = Field(..., description="RFC 7946 GeoJSON Object")
    parcel_name: Optional[str] = Field(default="Custom Imported Parcel")
    asking_price_crore: Optional[float] = Field(default=None, gt=0)
    check_pmrda_boundary: bool = Field(default=True)


class GeoJSONImportResponse(BaseModel):
    """Result of user GeoJSON geometry validation and ingestion."""
    model_config = ConfigDict(from_attributes=True)

    is_valid: bool
    parcel_id: str
    parcel_name: str
    centroid: List[float]
    area_acres: float
    area_sq_meters: float
    normalized_geojson: Dict[str, Any]
    provenance_tier: str
    statutory_warning: str
