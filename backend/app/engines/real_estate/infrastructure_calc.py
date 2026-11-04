"""
Infrastructure Engineering Calculator.

Deterministic engineering formulas based on Indian Standards (IS) codes
for computing water demand, sewage output, electricity load, and a
composite Infrastructure Readiness Index.

References:
    - IS 1172:1993  — Water supply for buildings
    - CPHEEO Manual — Sewage & sewerage (80 % return factor)
    - NBC 2016      — Electrical load norms
"""

from __future__ import annotations

from backend.app.models.schemas import InfrastructureReport, LandParcel


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

# IS 1172 domestic water supply standard: 135 litres per capita per day
WATER_LPCD: float = 135.0

# CPHEEO sewage-to-water return ratio
SEWAGE_RETURN_RATIO: float = 0.80

# Population density assumptions (persons per acre)
DENSITY_MAP: dict[str, float] = {
    "residential": 120.0,
    "commercial": 60.0,
    "industrial": 30.0,
    "mixed": 90.0,
}

# Per-unit electrical load (kW)
ELECTRICAL_LOAD_KW: dict[str, float] = {
    "residential": 2.0,    # per dwelling unit
    "commercial": 5.0,     # per commercial unit
    "industrial": 10.0,    # per industrial bay
    "mixed": 3.0,          # weighted average
}

# Dwelling/unit density (units per acre)
UNIT_DENSITY: dict[str, float] = {
    "residential": 30.0,
    "commercial": 15.0,
    "industrial": 5.0,
    "mixed": 20.0,
}

# Power factor for kW → kVA conversion
POWER_FACTOR: float = 0.85


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════


def compute_water_demand(parcel: LandParcel) -> float:
    """
    Compute daily water demand in litres per day (LPD).

    Formula:  demand = area_acres × pop_density × 135 lpcd
    """
    density = DENSITY_MAP.get(parcel.zone_type, DENSITY_MAP["mixed"])
    population = parcel.area_acres * density
    return round(population * WATER_LPCD, 2)


def compute_sewage_output(water_demand_lpd: float) -> float:
    """
    Compute daily sewage output as 80 % of water demand (CPHEEO).

    Args:
        water_demand_lpd: Water demand in litres per day.

    Returns:
        Sewage output in litres per day.
    """
    return round(water_demand_lpd * SEWAGE_RETURN_RATIO, 2)


def compute_electricity_kva(parcel: LandParcel) -> float:
    """
    Compute total electrical demand in kVA.

    Formula:  kVA = (units × load_kw) / power_factor
    """
    zone = parcel.zone_type if parcel.zone_type in UNIT_DENSITY else "mixed"
    units = parcel.area_acres * UNIT_DENSITY[zone]
    load_kw = units * ELECTRICAL_LOAD_KW[zone]
    return round(load_kw / POWER_FACTOR, 2)


def compute_infra_readiness_index(parcel: LandParcel) -> float:
    """
    Composite Infrastructure Readiness Index (IRI).

    I = 0.25·W + 0.25·E + 0.20·S + 0.30·R

    Weights reflect road connectivity's outsized impact on development
    feasibility (NBC 2016 guidance).

    Returns:
        float in [0, 1].
    """
    return round(
        0.25 * parcel.water_score
        + 0.25 * parcel.electricity_score
        + 0.20 * parcel.sewage_score
        + 0.30 * parcel.road_score,
        6,
    )


def generate_infrastructure_report(parcel: LandParcel) -> InfrastructureReport:
    """
    Generate a full infrastructure report for a single parcel.

    Combines water demand, sewage output, electricity load, and
    the composite readiness index into one report object.
    """
    water = compute_water_demand(parcel)
    sewage = compute_sewage_output(water)
    electricity = compute_electricity_kva(parcel)
    iri = compute_infra_readiness_index(parcel)

    return InfrastructureReport(
        parcel_id=parcel.id,
        parcel_name=parcel.name,
        water_demand_lpd=water,
        sewage_output_lpd=sewage,
        electricity_kva=electricity,
        infra_readiness_index=iri,
    )
