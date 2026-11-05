"""
Synthetic and Demonstration Data Management.

Explicitly isolates and documents simulated parameters used for algorithmic
testing and visual demonstration, preventing synthetic records from being
misconstrued as surveyed or commercial reality.
"""

from __future__ import annotations

from typing import Any, Dict
from backend.app.models.schemas import ProvenanceRecord, VerificationStatus

SYNTHETIC_CATALOG: Dict[str, Dict[str, Any]] = {
    "DEMO_PARCEL_PRICES": {
        "field": "price_crore",
        "description": "Demonstration land asking price calibrated to approximate micro-market averages (₹8.8 - ₹14.5 Cr).",
        "purpose": "Provides bounded numeric cost coefficients for QAOA combinatorial budget constraint simulation.",
        "status": VerificationStatus.SYNTHETIC,
        "disclaimer": "Not an actual commercial listing or transaction price. Sourced from empirical ready reckoner estimates.",
    },
    "DEMO_PARCEL_AREAS": {
        "field": "area_acres",
        "description": "Demonstration parcel plot sizes (3.8 - 12.0 acres).",
        "purpose": "Simulates institutional development parcels for civil infrastructure demand calculations.",
        "status": VerificationStatus.SYNTHETIC,
        "disclaimer": "Approximated plot footprint for demonstration. Actual boundary polygons require title survey.",
    },
    "ILLUSTRATIVE_3D_MESHES": {
        "field": "CityTwin3D.tsx massing geometry",
        "description": "Procedural extruded bounding boxes and ribbons representing buildings and pipes.",
        "purpose": "Spatial volumetric visual intuition in Three.js viewport.",
        "status": VerificationStatus.SYNTHETIC,
        "disclaimer": "Illustrative spatial envelopes. Does not represent surveyed CAD/BIM architecture or cadastral bounds.",
    },
    "QAOA_HAMILTONIAN_WEIGHTS": {
        "field": "lambda_budget, lambda_risk",
        "description": "Penalty multipliers in QUBO formulation.",
        "purpose": "Penalty tuning for statevector ground-state convergence.",
        "status": VerificationStatus.ESTIMATED,
        "disclaimer": "Mathematical simulation parameters. Eligibility does not imply statutory land clearance.",
    },
}


def get_synthetic_provenance(key: str) -> ProvenanceRecord:
    """Return a typed ProvenanceRecord documenting synthetic demonstration origin."""
    entry = SYNTHETIC_CATALOG.get(key, SYNTHETIC_CATALOG["DEMO_PARCEL_PRICES"])
    return ProvenanceRecord(
        source_name="Quantum Estate X Synthetic Benchmark Engine",
        source_url=None,
        source_type="Synthetic Simulation",
        verification_status=entry["status"],
        last_verified="2026-11-05",
        confidence_level=None,  # Do not assign confidence scores to synthetic data
        methodology_notes=f"{entry['description']} Purpose: {entry['purpose']}. Disclaimer: {entry['disclaimer']}",
    )
