"""
Development Feasibility and Land Suitability Engine.

Computes preliminary development scenarios for:
- Residential Development
- Commercial / IT Park Development
- Industrial & Logistics Development
- Mixed-Use Integrated Development

Phase 1.7 Validation & Safeguards:
- Strict mathematical boundary guards (non-positive area, negative costs, division-by-zero protection)
- Transparent distinction between statutory FSI approvals and preliminary model estimates
- Direct lineage tracking via ProvenanceRecord

Assumptions & Standards:
- National Building Code (NBC 2016)
- Unified Development Control and Promotion Regulations (UDCPR 2020 Maharashtra)
- Typical PMRDA Micro-Market Benchmarks
"""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.models.schemas import (
    FeasibilityScenarioRequest,
    FeasibilityScenarioResult,
    LandParcel,
)
from backend.app.data.provenance.data_registry import get_feasibility_model_provenance

SQFT_PER_ACRE: float = 43560.0

# ═══════════════════════════════════════════════════════════════════════
# TYPOLOGY BENCHMARK DEFAULTS (PMRDA REGION)
# ═══════════════════════════════════════════════════════════════════════

TYPOLOGY_BENCHMARKS: Dict[str, Dict[str, object]] = {
    "residential": {
        "fsi": 1.75,
        "construction_cost_sqft": 2600.0,
        "selling_price_sqft": 6500.0,
        "duration_months": 28,
        "infra_pct": 0.08,
        "approvals_pct": 0.06,
        "contingency_pct": 0.05,
        "infra_requirements": [
            "Dedicated Sewage Treatment Plant (STP) per MPCB norms",
            "Hydro-pneumatic domestic water distribution network",
            "MSEDCL 11kV transformer yard with dual DG back-up",
            "12-meter wide internal circulation asphalt roads",
            "Stormwater drainage retention tank with rainwater harvesting",
        ],
        "constraints": [
            "Mandatory 10% ground-level Recreational Open Space (RG)",
            "Maximum permissible building height subject to PMRDA road width",
            "State Environment Impact Assessment Authority (SEIAA) clearance if BUA > 20,000 sq.m",
        ],
    },
    "commercial": {
        "fsi": 2.25,
        "construction_cost_sqft": 3800.0,
        "selling_price_sqft": 9200.0,
        "duration_months": 36,
        "infra_pct": 0.10,
        "approvals_pct": 0.07,
        "contingency_pct": 0.05,
        "infra_requirements": [
            "Central chilled water HVAC plant and high-performance double-glazed facade",
            "Dual-source 22kV express electrical power feed",
            "High-density subterranean fiber optical entry routes",
            "Multi-level basement parking with automated ventilation (NBC Part 4)",
            "Comprehensive NFPA/NBC compliant sprinkler and hydrants network",
        ],
        "constraints": [
            "Traffic Impact Assessment (TIA) study required for PMRDA approval",
            "Aviation height NOC required if within civil airport funnel zone",
            "Peak power demand sanction required from MSEDCL prior to plinth",
        ],
    },
    "industrial": {
        "fsi": 1.0,
        "construction_cost_sqft": 2100.0,
        "selling_price_sqft": 4500.0,
        "duration_months": 18,
        "infra_pct": 0.12,
        "approvals_pct": 0.05,
        "contingency_pct": 0.05,
        "infra_requirements": [
            "Heavy-duty industrial flooring (50 kN/m2 floor load capacity)",
            "Heavy commercial vehicle turning radiuses conforming to IRC WB-20",
            "Effluent Treatment Plant (ETP) with zero-liquid discharge (ZLD) readiness",
            "Express HT industrial power feeder line",
            "Dedicated hazardous materials containment and spill isolation sump",
        ],
        "constraints": [
            "Maharashtra Pollution Control Board (MPCB) Consent to Establish (CTE)",
            "15-meter peripheral green buffer mandatory along boundary",
            "Restricted to authorized industrial / warehousing zoning corridors",
        ],
    },
    "mixed": {
        "fsi": 2.0,
        "construction_cost_sqft": 3200.0,
        "selling_price_sqft": 7800.0,
        "duration_months": 32,
        "infra_pct": 0.09,
        "approvals_pct": 0.06,
        "contingency_pct": 0.05,
        "infra_requirements": [
            "Segregated residential and commercial vehicular entrances and exits",
            "Independent utility metering and multi-stage STP distribution",
            "Retail frontage pedestrian plaza with high-durability paver blocks",
            "Dual-circuit electrical distribution substation",
        ],
        "constraints": [
            "Mixed-use zoning compliance under PMRDA Unified DCPR",
            "Separate commercial and residential parking ratio compliance",
            "Fire segregation barriers between commercial podium and residential towers",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def evaluate_feasibility(
    parcel: LandParcel,
    req: Optional[FeasibilityScenarioRequest] = None,
) -> FeasibilityScenarioResult:
    """
    Calculate development feasibility for a parcel under specified or default typology assumptions.

    Includes mathematical boundary validations and explicit regulatory labeling.
    """
    if parcel.area_acres <= 0:
        raise ValueError(f"Parcel area must be positive, got {parcel.area_acres} acres.")

    if parcel.price_crore < 0:
        raise ValueError(f"Parcel price cannot be negative, got {parcel.price_crore} crore.")

    typology = (req.development_type if req and req.development_type else parcel.zone_type).lower()
    if typology not in TYPOLOGY_BENCHMARKS:
        typology = "mixed"

    bench = TYPOLOGY_BENCHMARKS[typology]

    # Resolve configurable parameters with boundary guards
    raw_fsi = req.custom_target_fsi if req and req.custom_target_fsi else bench["fsi"]
    fsi = max(float(raw_fsi), 0.1)

    raw_cost = (
        req.custom_construction_cost_sqft
        if req and req.custom_construction_cost_sqft
        else bench["construction_cost_sqft"]
    )
    cost_per_sqft = max(float(raw_cost), 100.0)

    raw_sell = (
        req.projected_selling_price_sqft
        if req and req.projected_selling_price_sqft
        else bench["selling_price_sqft"]
    )
    sell_price_sqft = max(float(raw_sell), 100.0)

    # 1. Area conversions
    land_area_sqft = round(parcel.area_acres * SQFT_PER_ACRE, 2)
    bua_sqft = round(land_area_sqft * fsi, 2)

    # 2. Hard construction cost (₹ Crore)
    # 1 Crore = 10,000,000
    construction_cost_crore = round((bua_sqft * cost_per_sqft) / 10000000.0, 2)

    # 3. Soft costs & infrastructure
    infra_pct = float(bench["infra_pct"])
    approvals_pct = float(bench["approvals_pct"])
    contingency_pct = float(bench["contingency_pct"])

    infra_and_approvals_crore = round(
        construction_cost_crore * (infra_pct + approvals_pct), 2
    )
    contingency_crore = round(
        construction_cost_crore * contingency_pct, 2
    )

    # 4. Total project cost
    land_cost_crore = parcel.price_crore
    total_cost_crore = round(
        land_cost_crore
        + construction_cost_crore
        + infra_and_approvals_crore
        + contingency_crore,
        2,
    )

    # 5. Projected Gross Development Value (GDV)
    projected_gdv_crore = round((bua_sqft * sell_price_sqft) / 10000000.0, 2)

    # 6. Returns & margins (with non-zero denominator guard)
    margin_crore = round(projected_gdv_crore - total_cost_crore, 2)
    roi_pct = round((margin_crore / max(total_cost_crore, 0.01)) * 100.0, 2)

    duration = int(bench["duration_months"])
    infra_reqs = list(bench["infra_requirements"])
    constraints = list(bench["constraints"])

    provenance = get_feasibility_model_provenance(typology)

    return FeasibilityScenarioResult(
        development_type=typology,
        permissible_fsi=fsi,
        land_area_sqft=land_area_sqft,
        built_up_area_sqft=bua_sqft,
        construction_cost_per_sqft=cost_per_sqft,
        land_acquisition_cost_crore=land_cost_crore,
        construction_cost_crore=construction_cost_crore,
        infra_and_approvals_cost_crore=infra_and_approvals_crore,
        contingency_cost_crore=contingency_crore,
        total_project_cost_crore=total_cost_crore,
        projected_selling_price_sqft=sell_price_sqft,
        projected_gdv_crore=projected_gdv_crore,
        estimated_margin_crore=margin_crore,
        roi_pct=roi_pct,
        estimated_duration_months=duration,
        infrastructure_requirements=infra_reqs,
        development_constraints=constraints,
        disclaimer=(
            "Preliminary engineering & financial feasibility model. Does not constitute formal "
            "architectural sanction, sanctioned FSI certificate, or statutory clearance under Maharashtra UDCPR."
        ),
        regulatory_applicability_note=(
            "Permissible FSI and built-up allowances depend on road width, plot depth, and TDR eligibility "
            "under Maharashtra Unified DCPR 2020. Parameters are configurable estimates, not statutory sanctions."
        ),
        provenance=provenance,
    )
