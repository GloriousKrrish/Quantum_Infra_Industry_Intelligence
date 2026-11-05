"""
API routes for real estate land parcel intelligence, geospatial infrastructure
proximity analysis, development feasibility, financial scenario modeling, and
Phase 1.7 Data Trust Framework provenance audits.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from backend.app.engines.real_estate.development_feasibility import evaluate_feasibility
from backend.app.engines.real_estate.financial_analysis import evaluate_financial_scenarios
from backend.app.engines.real_estate.infrastructure_analysis import analyze_parcel_infrastructure
from backend.app.engines.real_estate.infrastructure_calc import generate_infrastructure_report
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    get_parcel_by_id,
    get_parcel_detailed_profile,
    get_parcels_within_budget,
    search_and_filter_parcels,
)
from backend.app.models.schemas import (
    FeasibilityScenarioRequest,
    FeasibilityScenarioResult,
    FinancialAnalysisResponse,
    InfrastructureReport,
    LandParcel,
    ParcelDetailedProfile,
    ParcelInfrastructureAnalysis,
)
from backend.app.data.provenance.data_registry import get_provenance_audit_summary
from backend.app.data.sources.osm_source import query_overpass_amenities

router = APIRouter(prefix="/api/parcels", tags=["Land Parcels & Real Estate Intelligence"])


@router.get(
    "",
    response_model=List[LandParcel],
    summary="List, search, and filter Pune parcels",
    description="Returns Pune parcels with optional keyword search, zone filtering, price/area ranges, and sorting.",
)
async def list_parcels(
    search: Optional[str] = Query(default=None, description="Search by parcel ID or name"),
    zone_type: Optional[str] = Query(default=None, description="Filter by zone: residential, commercial, industrial, mixed"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price in ₹ Crore"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price in ₹ Crore"),
    min_area: Optional[float] = Query(default=None, ge=0, description="Minimum area in acres"),
    max_area: Optional[float] = Query(default=None, ge=0, description="Maximum area in acres"),
    sort_by: Optional[str] = Query(
        default=None,
        description="Sort by: price_asc, price_desc, area_asc, area_desc, utility_desc, price_per_acre_asc",
    ),
) -> List[LandParcel]:
    """Return all parcels matching search and filter criteria."""
    if any([search, zone_type, min_price, max_price, min_area, max_area, sort_by]):
        return search_and_filter_parcels(
            search=search,
            zone_type=zone_type,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            sort_by=sort_by,
        )
    return get_all_parcels()


@router.get(
    "/provenance/audit",
    summary="Get platform-wide data provenance and verification audit",
    description="Returns formal data verification tiers, lineage sources, and methodological audit summary.",
)
async def get_provenance_audit() -> dict:
    """Return platform-wide data provenance and validation audit."""
    return get_provenance_audit_summary()


@router.get(
    "/budget/{budget_crore}",
    response_model=List[LandParcel],
    summary="Filter parcels by individual price cap",
    description=(
        "Returns parcels whose price does not exceed the given budget. "
        "This is a per-parcel filter, not a combinatorial budget constraint."
    ),
)
async def list_parcels_by_budget(
    budget_crore: float = Path(..., gt=0, description="Max price per parcel (₹ Cr)"),
) -> List[LandParcel]:
    """Return parcels within the per-parcel budget cap."""
    return get_parcels_within_budget(budget_crore)


@router.get(
    "/infrastructure",
    response_model=List[InfrastructureReport],
    summary="Infrastructure reports for all parcels",
    description="Generates IS-standard engineering reports for every parcel.",
)
async def list_infrastructure_reports() -> List[InfrastructureReport]:
    """Generate infrastructure reports for all parcels."""
    parcels = get_all_parcels()
    return [generate_infrastructure_report(p) for p in parcels]


@router.get(
    "/{parcel_id}",
    response_model=ParcelDetailedProfile,
    summary="Get complete detailed land intelligence profile",
    description="Returns cadastral, geographic, infrastructure proximity, feasibility, and quantum optimization details for a single parcel.",
)
async def get_parcel_profile(
    parcel_id: str = Path(..., description="Unique parcel identifier (e.g. 'PUNE-001')"),
) -> ParcelDetailedProfile:
    """Return full detailed profile for a selected parcel."""
    profile = get_parcel_detailed_profile(parcel_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Parcel with ID '{parcel_id}' not found.")
    return profile


@router.get(
    "/{parcel_id}/infrastructure",
    response_model=ParcelInfrastructureAnalysis,
    summary="Get multi-sector infrastructure proximity analysis",
    description="Calculates exact Haversine distances to highways, hospitals, universities, railway stations, airports, and commercial centers with configurable weights.",
)
async def get_parcel_infrastructure(
    parcel_id: str = Path(..., description="Unique parcel identifier (e.g. 'PUNE-001')"),
    weight_highway: Optional[float] = Query(default=None, ge=0),
    weight_hospital: Optional[float] = Query(default=None, ge=0),
    weight_commercial: Optional[float] = Query(default=None, ge=0),
    weight_railway: Optional[float] = Query(default=None, ge=0),
    weight_education: Optional[float] = Query(default=None, ge=0),
    weight_airport: Optional[float] = Query(default=None, ge=0),
) -> ParcelInfrastructureAnalysis:
    """Return infrastructure proximity and accessibility analysis."""
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ID '{parcel_id}' not found.")

    custom_weights = None
    if any(
        w is not None
        for w in [
            weight_highway,
            weight_hospital,
            weight_commercial,
            weight_railway,
            weight_education,
            weight_airport,
        ]
    ):
        custom_weights = {
            "highway": weight_highway if weight_highway is not None else 25.0,
            "hospital": weight_hospital if weight_hospital is not None else 20.0,
            "commercial": weight_commercial if weight_commercial is not None else 20.0,
            "railway": weight_railway if weight_railway is not None else 15.0,
            "education": weight_education if weight_education is not None else 10.0,
            "airport": weight_airport if weight_airport is not None else 10.0,
        }

    return analyze_parcel_infrastructure(parcel, custom_weights)


@router.get(
    "/{parcel_id}/overpass",
    summary="Query real-time OpenStreetMap amenities via Overpass API",
    description="Queries live OpenStreetMap POIs within a specified radius around the parcel centroid, with verified offline fallback.",
)
async def get_parcel_overpass_amenities(
    parcel_id: str = Path(..., description="Unique parcel identifier (e.g. 'PUNE-001')"),
    radius_meters: int = Query(default=5000, ge=500, le=25000, description="Search radius in meters"),
) -> dict:
    """Query live nearby infrastructure amenities from OpenStreetMap."""
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ID '{parcel_id}' not found.")

    elements, status_msg = query_overpass_amenities(
        parcel.location_lat, parcel.location_lng, radius_meters
    )
    return {
        "parcel_id": parcel.id,
        "parcel_name": parcel.name,
        "radius_meters": radius_meters,
        "query_status": status_msg,
        "elements_count": len(elements),
        "elements": elements,
        "attribution": "© OpenStreetMap contributors (ODbL 1.0 License)",
    }


@router.post(
    "/{parcel_id}/feasibility",
    response_model=FeasibilityScenarioResult,
    summary="Evaluate development feasibility scenario",
    description="Computes BUA, construction hard cost, statutory approvals, total project cost, GDV, and preliminary ROI under specified assumptions.",
)
async def calculate_parcel_feasibility(
    parcel_id: str = Path(..., description="Unique parcel identifier (e.g. 'PUNE-001')"),
    request: Optional[FeasibilityScenarioRequest] = None,
) -> FeasibilityScenarioResult:
    """Evaluate preliminary development feasibility for a parcel."""
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ID '{parcel_id}' not found.")
    return evaluate_feasibility(parcel, request)


@router.post(
    "/{parcel_id}/financial",
    response_model=FinancialAnalysisResponse,
    summary="Simulate financial scenarios and cash flow schedule",
    description="Simulates Conservative, Baseline, and Optimistic financial scenarios with 3-year phased cash flows and break-even analysis.",
)
async def calculate_parcel_financials(
    parcel_id: str = Path(..., description="Unique parcel identifier (e.g. 'PUNE-001')"),
    request: Optional[FeasibilityScenarioRequest] = None,
) -> FinancialAnalysisResponse:
    """Simulate financial scenarios and annual cash flows."""
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ID '{parcel_id}' not found.")
    return evaluate_financial_scenarios(parcel, request)
