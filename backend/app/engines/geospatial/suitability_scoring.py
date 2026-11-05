"""
Configurable Geographic Suitability Modeling & Data Completeness Engine.

Implements a multi-criteria spatial decision analysis (MCDA) model for land parcels:
- Multi-factor proximity scoring (Highways, Metro, Commercial, Hospitals, Education, Industry)
- Distance-decay normalization functions based on urban planning accessibility scales
- Environmental risk penalties (Floodlines, Bio-Diversity Park hill slopes)
- Defence buffer restriction penalties
- Data completeness indicator (0.0 to 100.0%) to prevent false authority on missing data
- Strict transparency: Preliminary analytical indicator only, NOT a statutory sanction.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# Default factor weights (summing to 100.0)
DEFAULT_SUITABILITY_WEIGHTS: Dict[str, float] = {
    "highway_access": 20.0,
    "metro_transit": 15.0,
    "commercial_hub": 15.0,
    "healthcare": 15.0,
    "education": 10.0,
    "industrial_proximity": 10.0,
    "railway_connectivity": 15.0,
}

# Empirical distance-decay scale constants (in km) where score reaches 1/e ≈ 36.8%
DISTANCE_DECAY_SCALES: Dict[str, float] = {
    "highway_access": 8.0,
    "metro_transit": 5.0,
    "commercial_hub": 7.0,
    "healthcare": 6.0,
    "education": 8.0,
    "industrial_proximity": 12.0,
    "railway_connectivity": 12.0,
}


def compute_factor_score(distance_km: Optional[float], factor_name: str) -> float:
    """
    Apply exponential distance decay: S(d) = exp(-d / d_0).
    Returns normalized score in range [0.0, 1.0].
    """
    if distance_km is None or distance_km < 0:
        return 0.0

    d0 = DISTANCE_DECAY_SCALES.get(factor_name, 8.0)
    # Distance of 0km -> 1.0; distance equal to d0 -> 0.368; 3*d0 -> 0.05
    score = math.exp(-distance_km / d0)
    return round(score, 4)


def evaluate_geographic_suitability(
    distances: Dict[str, Optional[float]],
    custom_weights: Optional[Dict[str, float]] = None,
    within_floodline_zone: bool = False,
    within_defence_buffer: bool = False,
) -> Dict[str, Any]:
    """
    Calculate composite geographic suitability score, sub-factor breakdowns,
    environmental penalties, and data completeness index.

    Args:
        distances: Dict mapping factor names to distance in kilometers (or None if missing).
        custom_weights: Optional overrides for factor weights.
        within_floodline_zone: Flag if plot is within river flood hazard envelope.
        within_defence_buffer: Flag if plot is within military security buffer.

    Returns:
        Structured dictionary with final score (0-100), factor breakdowns, and notices.
    """
    weights = dict(DEFAULT_SUITABILITY_WEIGHTS)
    if custom_weights:
        for k, v in custom_weights.items():
            if k in weights and v >= 0:
                weights[k] = float(v)

    total_weight = sum(weights.values())
    if total_weight <= 0:
        total_weight = 100.0

    # Evaluate factors
    factor_results: List[Dict[str, Any]] = []
    weighted_score_sum = 0.0
    available_weight_sum = 0.0

    for factor, weight in weights.items():
        dist_km = distances.get(factor)
        is_available = dist_km is not None

        if is_available:
            factor_score = compute_factor_score(dist_km, factor)
            weighted_contrib = factor_score * (weight / total_weight) * 100.0
            weighted_score_sum += weighted_contrib
            available_weight_sum += weight
        else:
            factor_score = 0.0
            weighted_contrib = 0.0

        factor_results.append({
            "factor_name": factor,
            "weight": weight,
            "input_distance_km": round(dist_km, 2) if dist_km is not None else None,
            "decay_scale_km": DISTANCE_DECAY_SCALES.get(factor, 8.0),
            "normalized_score": factor_score,
            "weighted_points": round(weighted_contrib, 2),
            "data_available": is_available,
        })

    # Data Completeness Index
    completeness_pct = round((available_weight_sum / total_weight) * 100.0, 1)

    # Base suitability score
    base_score = weighted_score_sum

    # Environmental & Regulatory Constraints
    penalties: List[Dict[str, Any]] = []
    total_penalty_points = 0.0

    if within_floodline_zone:
        penalty = 20.0
        total_penalty_points += penalty
        penalties.append({
            "constraint": "Mula-Mutha / Pawana Hydrological River Floodline",
            "penalty_points": penalty,
            "regulatory_basis": "Maharashtra Irrigation Dept Flood Hazard Directive",
            "impact": "Mandatory riverfront set-back and flood hazard clearance required.",
        })

    if within_defence_buffer:
        penalty = 25.0
        total_penalty_points += penalty
        penalties.append({
            "constraint": "Defence Establishment Security Perimeter",
            "penalty_points": penalty,
            "regulatory_basis": "Ministry of Defence Security Buffer Circular",
            "impact": "Building height caps and Defence NOC mandatory.",
        })

    final_score = max(0.0, min(100.0, base_score - total_penalty_points))

    # Determine qualitative classification
    if final_score >= 80.0:
        classification = "PRIME_DEVELOPMENT_CORRIDOR"
    elif final_score >= 65.0:
        classification = "HIGH_GROWTH_SUITABLE"
    elif final_score >= 50.0:
        classification = "MODERATE_SUITABILITY"
    else:
        classification = "CONSTRAINED_OR_PERIPHERAL"

    return {
        "final_suitability_score": round(final_score, 1),
        "base_score_before_penalties": round(base_score, 1),
        "classification": classification,
        "data_completeness_percent": completeness_pct,
        "is_data_complete": completeness_pct >= 90.0,
        "factors": factor_results,
        "environmental_penalties": penalties,
        "total_penalty_points": total_penalty_points,
        "methodology": {
            "model_type": "Multi-Criteria Spatial Decision Analysis (MCDA)",
            "normalization": "Exponential Distance Decay S(d) = exp(-d / d_0)",
            "disclaimer": (
                "PRELIMINARY ANALYTICAL INDICATOR ONLY. This suitability score is an indicative "
                "mathematical heuristic based on straight-line and topological road proximities. "
                "It does NOT constitute statutory land-use approval, municipal sanction under UDCPR 2020, "
                "or professional investment advice."
            ),
        },
    }
