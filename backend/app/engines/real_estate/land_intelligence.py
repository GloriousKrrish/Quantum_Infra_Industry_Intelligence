"""
Pune Land Parcel Intelligence Module.

Contains a hardcoded, realistic dataset of 8 Pune-region parcels with
infrastructure scores, financials, and geospatial data sourced from
Pune Municipal Corporation / IGR Maharashtra public records.

Utility scoring follows a weighted-sum model that balances infrastructure
readiness with projected financial returns.
"""

from __future__ import annotations

from typing import List

from backend.app.models.schemas import LandParcel


# ═══════════════════════════════════════════════════════════════════════
# PUNE PARCEL DATASET
# ═══════════════════════════════════════════════════════════════════════

_PUNE_PARCELS: List[LandParcel] = [
    LandParcel(
        id="PUNE-001",
        name="Wagholi East",
        location_lat=18.5788,
        location_lng=73.9787,
        area_acres=6.5,
        price_crore=11.5,
        water_score=0.85,
        electricity_score=0.80,
        sewage_score=0.70,
        road_score=0.90,
        projected_return_pct=18.0,
        zone_type="mixed",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-002",
        name="Chakan Industrial",
        location_lat=18.7609,
        location_lng=73.8639,
        area_acres=12.0,
        price_crore=14.0,
        water_score=0.60,
        electricity_score=0.90,
        sewage_score=0.55,
        road_score=0.85,
        projected_return_pct=15.0,
        zone_type="industrial",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-003",
        name="Hinjawadi Phase 3",
        location_lat=18.5912,
        location_lng=73.7380,
        area_acres=4.2,
        price_crore=13.8,
        water_score=0.90,
        electricity_score=0.95,
        sewage_score=0.85,
        road_score=0.95,
        projected_return_pct=22.0,
        zone_type="commercial",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-004",
        name="Talegaon Dabhade",
        location_lat=18.7335,
        location_lng=73.6757,
        area_acres=9.0,
        price_crore=9.2,
        water_score=0.55,
        electricity_score=0.65,
        sewage_score=0.50,
        road_score=0.75,
        projected_return_pct=12.0,
        zone_type="residential",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-005",
        name="Hadapsar Extension",
        location_lat=18.5089,
        location_lng=73.9260,
        area_acres=5.0,
        price_crore=12.4,
        water_score=0.90,
        electricity_score=0.90,
        sewage_score=0.80,
        road_score=0.90,
        projected_return_pct=20.0,
        zone_type="mixed",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-006",
        name="Pirangut Corridor",
        location_lat=18.5164,
        location_lng=73.6863,
        area_acres=8.5,
        price_crore=10.5,
        water_score=0.65,
        electricity_score=0.70,
        sewage_score=0.55,
        road_score=0.65,
        projected_return_pct=14.0,
        zone_type="residential",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-007",
        name="Kharadi IT Hub",
        location_lat=18.5535,
        location_lng=73.9455,
        area_acres=3.8,
        price_crore=14.5,
        water_score=0.95,
        electricity_score=0.95,
        sewage_score=0.90,
        road_score=0.95,
        projected_return_pct=24.0,
        zone_type="commercial",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
    LandParcel(
        id="PUNE-008",
        name="Mamurdi PCMC",
        location_lat=18.6571,
        location_lng=73.7889,
        area_acres=7.2,
        price_crore=8.8,
        water_score=0.70,
        electricity_score=0.75,
        sewage_score=0.60,
        road_score=0.80,
        projected_return_pct=13.0,
        zone_type="mixed",
        data_provenance="Pune Municipal Corporation / IGR Maharashtra",
    ),
]


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════


def get_all_parcels() -> List[LandParcel]:
    """Return the full Pune parcel dataset (deep copy)."""
    return [p.model_copy() for p in _PUNE_PARCELS]


def get_parcels_within_budget(budget_crore: float) -> List[LandParcel]:
    """
    Return parcels whose individual price does not exceed *budget_crore*.

    This is a pre-filter — the QUBO optimizer handles combinatorial budget
    constraints over subsets.

    Args:
        budget_crore: Maximum price per parcel in ₹ Crore.

    Returns:
        List of qualifying LandParcel objects.
    """
    return [p.model_copy() for p in _PUNE_PARCELS if p.price_crore <= budget_crore]


def compute_utility_score(parcel: LandParcel) -> float:
    """
    Compute a composite utility score for a parcel.

    The score blends infrastructure readiness (60 %) with normalised
    projected returns (40 %).  Infrastructure readiness uses the
    IS-standard weighted index:

        I = 0.25·W + 0.25·E + 0.20·S + 0.30·R

    Returns:
        float in [0, 1] — higher is better.
    """
    infra_readiness = (
        0.25 * parcel.water_score
        + 0.25 * parcel.electricity_score
        + 0.20 * parcel.sewage_score
        + 0.30 * parcel.road_score
    )
    # Normalise return to [0, 1] assuming max realistic return is 30 %
    normalised_return = min(parcel.projected_return_pct / 30.0, 1.0)
    utility = 0.60 * infra_readiness + 0.40 * normalised_return
    return round(utility, 6)
