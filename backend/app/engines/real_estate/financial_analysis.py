"""
Financial Scenario Modeling and Multi-Year Cash Flow Projection Engine.

Simulates three investment scenarios:
- Conservative (Lower realization, escalated construction budget)
- Baseline (PMRDA micro-market empirical averages)
- Optimistic (Premium absorption rate, value-engineered construction)

Phase 1.7 Data Trust Framework:
- Division-by-zero safeguards on margin and break-even calculations
- Documented cash flow distribution phasing
- Full data lineage and methodological provenance tracking
"""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.engines.real_estate.development_feasibility import evaluate_feasibility
from backend.app.models.schemas import (
    CashFlowYear,
    FeasibilityScenarioRequest,
    FeasibilityScenarioResult,
    FinancialAnalysisResponse,
    FinancialScenarioItem,
    LandParcel,
    ProvenanceRecord,
    VerificationStatus,
)
from backend.app.data.provenance.data_registry import get_financial_model_provenance


def evaluate_financial_scenarios(
    parcel: LandParcel,
    req: Optional[FeasibilityScenarioRequest] = None,
) -> FinancialAnalysisResponse:
    """
    Generate complete 3-tier financial scenarios and a 3-year cash flow model for a parcel.
    """
    baseline_result = evaluate_feasibility(parcel, req)
    financial_prov = get_financial_model_provenance()

    # ── 1. Conservative Scenario (-10% sales price, +10% construction cost) ─
    cons_req = FeasibilityScenarioRequest(
        development_type=baseline_result.development_type,
        custom_target_fsi=baseline_result.permissible_fsi,
        custom_construction_cost_sqft=round(baseline_result.construction_cost_per_sqft * 1.10, 2),
        projected_selling_price_sqft=round(baseline_result.projected_selling_price_sqft * 0.90, 2),
    )
    cons_result = evaluate_feasibility(parcel, cons_req)
    cons_margin_pct = round(
        (cons_result.estimated_margin_crore / max(cons_result.projected_gdv_crore, 0.01)) * 100.0, 1
    )

    conservative_item = FinancialScenarioItem(
        scenario_name="Conservative",
        projected_gdv_crore=cons_result.projected_gdv_crore,
        total_project_cost_crore=cons_result.total_project_cost_crore,
        net_profit_crore=cons_result.estimated_margin_crore,
        margin_pct=cons_margin_pct,
        roi_pct=cons_result.roi_pct,
        assumptions_summary="-10% Selling Realization, +10% Construction Cost Escalation",
        provenance=financial_prov,
    )

    # ── 2. Baseline Scenario ─────────────────────────────────────────────
    base_margin_pct = round(
        (baseline_result.estimated_margin_crore / max(baseline_result.projected_gdv_crore, 0.01)) * 100.0, 1
    )
    baseline_item = FinancialScenarioItem(
        scenario_name="Baseline",
        projected_gdv_crore=baseline_result.projected_gdv_crore,
        total_project_cost_crore=baseline_result.total_project_cost_crore,
        net_profit_crore=baseline_result.estimated_margin_crore,
        margin_pct=base_margin_pct,
        roi_pct=baseline_result.roi_pct,
        assumptions_summary="Standard PMRDA Micro-Market Engineering & Price Baseline",
        provenance=financial_prov,
    )

    # ── 3. Optimistic Scenario (+15% sales price, -5% construction cost) ──
    opt_req = FeasibilityScenarioRequest(
        development_type=baseline_result.development_type,
        custom_target_fsi=baseline_result.permissible_fsi,
        custom_construction_cost_sqft=round(baseline_result.construction_cost_per_sqft * 0.95, 2),
        projected_selling_price_sqft=round(baseline_result.projected_selling_price_sqft * 1.15, 2),
    )
    opt_result = evaluate_feasibility(parcel, opt_req)
    opt_margin_pct = round(
        (opt_result.estimated_margin_crore / max(opt_result.projected_gdv_crore, 0.01)) * 100.0, 1
    )

    optimistic_item = FinancialScenarioItem(
        scenario_name="Optimistic",
        projected_gdv_crore=opt_result.projected_gdv_crore,
        total_project_cost_crore=opt_result.total_project_cost_crore,
        net_profit_crore=opt_result.estimated_margin_crore,
        margin_pct=opt_margin_pct,
        roi_pct=opt_result.roi_pct,
        assumptions_summary="+15% Premium Realization, -5% EPC Value Engineering",
        provenance=financial_prov,
    )

    scenarios = {
        "conservative": conservative_item,
        "baseline": baseline_item,
        "optimistic": optimistic_item,
    }

    # ── 4. Three-Year Cash Flow Projection (Baseline) ────────────────────
    land_cost = baseline_result.land_acquisition_cost_crore
    dev_cost = baseline_result.total_project_cost_crore - land_cost
    gdv = baseline_result.projected_gdv_crore

    # Year 1: Land Acquisition (100%), Site Prep & Approvals (25% of dev)
    outflow_y1 = round(land_cost + (dev_cost * 0.25), 2)
    inflow_y1 = round(gdv * 0.15, 2)  # Pre-launch token bookings

    # Year 2: Superstructure & Core Civil Works (50% of dev)
    outflow_y2 = round(dev_cost * 0.50, 2)
    inflow_y2 = round(gdv * 0.45, 2)  # Construction-linked milestone payments

    # Year 3: MEP Finishes, Handover & Landscaping (25% of dev)
    outflow_y3 = round(dev_cost * 0.25, 2)
    inflow_y3 = round(gdv * 0.40, 2)  # Possession & registry balance collections

    cashflow_timeline = [
        CashFlowYear(
            year=1,
            milestone="Land Acquisition, Master Approvals & Substructure",
            outflow_crore=outflow_y1,
            inflow_crore=inflow_y1,
            net_cashflow_crore=round(inflow_y1 - outflow_y1, 2),
        ),
        CashFlowYear(
            year=2,
            milestone="Superstructure & MEP Milestone Progression",
            outflow_crore=outflow_y2,
            inflow_crore=inflow_y2,
            net_cashflow_crore=round(inflow_y2 - outflow_y2, 2),
        ),
        CashFlowYear(
            year=3,
            milestone="Façade, Interior Fit-Out & Possession Handover",
            outflow_crore=outflow_y3,
            inflow_crore=inflow_y3,
            net_cashflow_crore=round(inflow_y3 - outflow_y3, 2),
        ),
    ]

    break_even_pct = round(
        (baseline_result.total_project_cost_crore / max(baseline_result.projected_gdv_crore, 0.01)) * 100.0,
        1,
    )

    assumptions = {
        "fsi": baseline_result.permissible_fsi,
        "built_up_area_sqft": baseline_result.built_up_area_sqft,
        "construction_cost_per_sqft": baseline_result.construction_cost_per_sqft,
        "projected_selling_price_sqft": baseline_result.projected_selling_price_sqft,
        "holding_period_months": baseline_result.estimated_duration_months,
        "inflation_reserve_pct": 5.0,
    }

    return FinancialAnalysisResponse(
        parcel_id=parcel.id,
        parcel_name=parcel.name,
        land_cost_crore=land_cost,
        baseline_scenario=baseline_result,
        scenarios=scenarios,
        cashflow_timeline=cashflow_timeline,
        break_even_sales_pct=break_even_pct,
        assumptions=assumptions,
        provenance=financial_prov,
    )
