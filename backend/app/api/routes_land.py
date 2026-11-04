"""
API routes for land parcel data access.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Path, Query

from backend.app.models.schemas import InfrastructureReport, LandParcel
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    get_parcels_within_budget,
)
from backend.app.engines.real_estate.infrastructure_calc import (
    generate_infrastructure_report,
)

router = APIRouter(prefix="/api/parcels", tags=["Land Parcels"])


@router.get(
    "",
    response_model=List[LandParcel],
    summary="List all Pune parcels",
    description="Returns the full dataset of 8 Pune-region land parcels.",
)
async def list_parcels() -> List[LandParcel]:
    """Return all available parcels."""
    return get_all_parcels()


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
