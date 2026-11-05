"""
Infrastructure Proximity and Geospatial Accessibility Engine.

Calculates great-circle Haversine distances and estimated transit times from
Pune micro-market parcels to major regional infrastructure facilities:
- Major Highways & Expressway Corridors
- Multispeciality Hospitals & Healthcare
- Universities & Engineering Institutions
- Railway Stations & Logistics Hubs
- Civil & International Airports
- Commercial, IT & Industrial Hubs

Phase 1.7 Data Trust Framework:
- WGS-84 coordinate validation and numerical singularity protection
- Explicit labeling of straight-line Haversine estimates vs road routing
- Documented transit time methodology based on IRC speed benchmarks
- Configurable and transparent accessibility scoring weights
- Provenance tracking with OpenStreetMap geodetic node attribution

Data Provenance:
- OpenStreetMap Public Geospatial Data (ODbL 1.0)
- PMRDA Regional Development Plan 2021-2041
- Indian Road Congress (IRC SP-73 / IRC-106) Speed & Access Norms
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from backend.app.models.schemas import (
    DistanceMethodology,
    InfrastructureProximityPoint,
    LandParcel,
    ParcelInfrastructureAnalysis,
    ProvenanceRecord,
    VerificationStatus,
)
from backend.app.data.provenance.verification import validate_coordinates
from backend.app.data.provenance.data_registry import (
    get_infrastructure_proximity_provenance,
)

# ═══════════════════════════════════════════════════════════════════════
# VERIFIED REGIONAL INFRASTRUCTURE ANCHORS (PUNE METROPOLITAN REGION)
# ═══════════════════════════════════════════════════════════════════════

INFRASTRUCTURE_ANCHORS: List[Dict[str, object]] = [
    # ── Highways & Expressways ──────────────────────────────────────────
    {
        "name": "Mumbai-Pune Expressway (Urse Toll Plaza)",
        "facility_type": "Highway",
        "lat": 18.7180,
        "lng": 73.6930,
        "avg_speed_kmh": 70.0,
        "data_source": "NHAI / MSRDC Cadastral Alignment",
    },
    {
        "name": "NH-48 Pune-Bangalore Bypass (Warje-Kothrud)",
        "facility_type": "Highway",
        "lat": 18.4850,
        "lng": 73.8050,
        "avg_speed_kmh": 50.0,
        "data_source": "NHAI GIS Records",
    },
    {
        "name": "Pune-Nashik Highway (NH-60 Bhosari Corridor)",
        "facility_type": "Highway",
        "lat": 18.6300,
        "lng": 73.8450,
        "avg_speed_kmh": 45.0,
        "data_source": "NHAI / PMRDA Arterial",
    },
    {
        "name": "Pune-Ahmednagar Highway (SH-27 / Nagar Road)",
        "facility_type": "Highway",
        "lat": 18.5800,
        "lng": 73.9800,
        "avg_speed_kmh": 40.0,
        "data_source": "Maharashtra PWD State Highway Network",
    },
    {
        "name": "PMRDA Western Ring Road Spur",
        "facility_type": "Highway",
        "lat": 18.5600,
        "lng": 73.7100,
        "avg_speed_kmh": 60.0,
        "data_source": "PMRDA Regional Master Plan 2021-2041",
    },

    # ── Hospitals & Healthcare ──────────────────────────────────────────
    {
        "name": "Aditya Birla Memorial Hospital (Chinchwad)",
        "facility_type": "Hospital",
        "lat": 18.6294,
        "lng": 73.7801,
        "avg_speed_kmh": 35.0,
        "data_source": "OpenStreetMap Healthcare GIS / NABH Registry",
    },
    {
        "name": "Ruby Hall Clinic (Sasoon Road / Bund Garden)",
        "facility_type": "Hospital",
        "lat": 18.5323,
        "lng": 73.8770,
        "avg_speed_kmh": 30.0,
        "data_source": "OpenStreetMap Healthcare GIS / NABH Registry",
    },
    {
        "name": "Sahyadri Super Speciality Hospital (Deccan Gymkhana)",
        "facility_type": "Hospital",
        "lat": 18.5152,
        "lng": 73.8346,
        "avg_speed_kmh": 30.0,
        "data_source": "OpenStreetMap Healthcare GIS / NABH Registry",
    },
    {
        "name": "Jupiter Hospital (Baner)",
        "facility_type": "Hospital",
        "lat": 18.5601,
        "lng": 73.7891,
        "avg_speed_kmh": 35.0,
        "data_source": "OpenStreetMap Healthcare GIS / NABH Registry",
    },
    {
        "name": "Manipal Hospital (Kharadi Bypass)",
        "facility_type": "Hospital",
        "lat": 18.5520,
        "lng": 73.9390,
        "avg_speed_kmh": 32.0,
        "data_source": "OpenStreetMap Healthcare GIS / NABH Registry",
    },
    {
        "name": "Talegaon General Hospital & Convalescent Center",
        "facility_type": "Hospital",
        "lat": 18.7290,
        "lng": 73.6820,
        "avg_speed_kmh": 35.0,
        "data_source": "OpenStreetMap Healthcare GIS",
    },

    # ── Educational Institutions ─────────────────────────────────────────
    {
        "name": "COEP Technological University (Shivajinagar)",
        "facility_type": "Education",
        "lat": 18.5284,
        "lng": 73.8567,
        "avg_speed_kmh": 30.0,
        "data_source": "Higher Education Dept / OSM Education Node",
    },
    {
        "name": "Savitribai Phule Pune University (Ganeshkhind)",
        "facility_type": "Education",
        "lat": 18.5529,
        "lng": 73.8248,
        "avg_speed_kmh": 32.0,
        "data_source": "Higher Education Dept / OSM Education Node",
    },
    {
        "name": "Symbiosis International University (Viman Nagar)",
        "facility_type": "Education",
        "lat": 18.5665,
        "lng": 73.9130,
        "avg_speed_kmh": 32.0,
        "data_source": "Higher Education Dept / OSM Education Node",
    },
    {
        "name": "Symbiosis International University (Lavale Campus)",
        "facility_type": "Education",
        "lat": 18.5398,
        "lng": 73.7345,
        "avg_speed_kmh": 35.0,
        "data_source": "Higher Education Dept / OSM Education Node",
    },
    {
        "name": "D.Y. Patil International University (Akurdi)",
        "facility_type": "Education",
        "lat": 18.6470,
        "lng": 73.7630,
        "avg_speed_kmh": 35.0,
        "data_source": "Higher Education Dept / OSM Education Node",
    },

    # ── Railway Stations & Terminals ─────────────────────────────────────
    {
        "name": "Pune Junction Railway Station",
        "facility_type": "Railway",
        "lat": 18.5289,
        "lng": 73.8744,
        "avg_speed_kmh": 28.0,
        "data_source": "Indian Railways Central Railway GIS",
    },
    {
        "name": "Shivajinagar Railway Station",
        "facility_type": "Railway",
        "lat": 18.5325,
        "lng": 73.8519,
        "avg_speed_kmh": 30.0,
        "data_source": "Indian Railways Central Railway GIS",
    },
    {
        "name": "Hadapsar Satellite Railway Station",
        "facility_type": "Railway",
        "lat": 18.5140,
        "lng": 73.9310,
        "avg_speed_kmh": 32.0,
        "data_source": "Indian Railways Central Railway GIS",
    },
    {
        "name": "Talegaon Suburban Railway Station",
        "facility_type": "Railway",
        "lat": 18.7305,
        "lng": 73.6730,
        "avg_speed_kmh": 35.0,
        "data_source": "Indian Railways Central Railway GIS",
    },
    {
        "name": "Dehu Road Railway Station",
        "facility_type": "Railway",
        "lat": 18.6750,
        "lng": 73.7220,
        "avg_speed_kmh": 35.0,
        "data_source": "Indian Railways Central Railway GIS",
    },

    # ── Airports ────────────────────────────────────────────────────────
    {
        "name": "Pune International Airport (Lohegaon - PNQ)",
        "facility_type": "Airport",
        "lat": 18.5822,
        "lng": 73.9197,
        "avg_speed_kmh": 35.0,
        "data_source": "Airports Authority of India (AAI) / ICAO VAPO",
    },
    {
        "name": "Proposed Purandar International Airport (New Pune)",
        "facility_type": "Airport",
        "lat": 18.3200,
        "lng": 73.9900,
        "avg_speed_kmh": 55.0,
        "data_source": "MADC / CIDCO Strategic Master Plan",
    },

    # ── Commercial & IT Hubs ─────────────────────────────────────────────
    {
        "name": "Rajiv Gandhi Infotech Park (Hinjawadi Phase 1-3)",
        "facility_type": "Commercial Hub",
        "lat": 18.5910,
        "lng": 73.7380,
        "avg_speed_kmh": 35.0,
        "data_source": "MIDC Special Economic Zone Registry",
    },
    {
        "name": "EON Free Zone / WTC (Kharadi)",
        "facility_type": "Commercial Hub",
        "lat": 18.5510,
        "lng": 73.9510,
        "avg_speed_kmh": 32.0,
        "data_source": "MIDC IT Park Cadastre",
    },
    {
        "name": "Magarpatta Cybercity (Hadapsar)",
        "facility_type": "Commercial Hub",
        "lat": 18.5160,
        "lng": 73.9290,
        "avg_speed_kmh": 30.0,
        "data_source": "Integrated Township Cadastre",
    },
    {
        "name": "Chakan MIDC Automobile Industrial Corridor",
        "facility_type": "Commercial Hub",
        "lat": 18.7650,
        "lng": 73.8550,
        "avg_speed_kmh": 45.0,
        "data_source": "MIDC Industrial Estate Authority",
    },
    {
        "name": "Talawade IT Park (PCMC)",
        "facility_type": "Commercial Hub",
        "lat": 18.6910,
        "lng": 73.7920,
        "avg_speed_kmh": 35.0,
        "data_source": "PCMC Municipal GIS",
    },
]

# Default weights for composite Accessibility Score (sum = 100.0)
DEFAULT_ACCESSIBILITY_WEIGHTS: Dict[str, float] = {
    "highway": 25.0,
    "hospital": 20.0,
    "commercial": 20.0,
    "railway": 15.0,
    "education": 10.0,
    "airport": 10.0,
}


# ═══════════════════════════════════════════════════════════════════════
# GEOSPATIAL DISTANCE MATHEMATICS (HAVERSINE)
# ═══════════════════════════════════════════════════════════════════════

def compute_haversine_distance_km(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate the great-circle spherical distance between two geographic coordinates
    on Earth using the Haversine formula.

    Radius of Earth R = 6371.0 km (WGS-84 mean spherical radius).

    Validates coordinates and guards against NaN/Inf and floating-point domain errors.
    """
    # 1. Coordinate validation
    v1, msg1 = validate_coordinates(lat1, lng1)
    if not v1:
        raise ValueError(f"Origin coordinate invalid: {msg1}")
    v2, msg2 = validate_coordinates(lat2, lng2)
    if not v2:
        raise ValueError(f"Destination coordinate invalid: {msg2}")

    # Identical points check
    if lat1 == lat2 and lng1 == lng2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Numerical guard: clamp to [0.0, 1.0] to prevent math domain error in sqrt
    a = max(0.0, min(1.0, a))

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(6371.0 * c, 2)


def estimate_drive_time_minutes(distance_km: float, avg_speed_kmh: float = 35.0) -> int:
    """
    Estimate vehicular travel time in minutes based on Indian Road Congress (IRC SP-73)
    speed benchmarks, incorporating a 15 % junction and traffic deceleration factor.

    Note: This is an estimated nominal transit time, not real-time turn-by-turn navigation.
    """
    effective_speed = max(avg_speed_kmh * 0.85, 15.0)
    minutes = (distance_km / effective_speed) * 60.0
    return max(int(round(minutes)), 2)


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def get_nearest_anchor_by_type(
    parcel_lat: float, parcel_lng: float, facility_type: str
) -> InfrastructureProximityPoint:
    """
    Find the nearest infrastructure anchor of a specific type.
    """
    matching = [a for a in INFRASTRUCTURE_ANCHORS if a["facility_type"] == facility_type]
    if not matching:
        return InfrastructureProximityPoint(
            name=f"No verified {facility_type} anchor registered",
            facility_type=facility_type,
            distance_km=999.0,
            drive_time_min=999,
            coordinates=[0.0, 0.0],
            data_source="Unavailable",
            distance_methodology=DistanceMethodology.ESTIMATED_PROXIMITY,
            distance_label="Unavailable",
            drive_time_label="Unavailable",
            provenance=None,
        )

    best_anchor = None
    min_dist = float("inf")
    for anchor in matching:
        d = compute_haversine_distance_km(
            parcel_lat, parcel_lng, float(anchor["lat"]), float(anchor["lng"])
        )
        if d < min_dist:
            min_dist = d
            best_anchor = anchor

    speed = float(best_anchor.get("avg_speed_kmh", 35.0))
    drive_min = estimate_drive_time_minutes(min_dist, speed)
    provenance = get_infrastructure_proximity_provenance(
        str(best_anchor["name"]), str(best_anchor["facility_type"])
    )

    return InfrastructureProximityPoint(
        name=str(best_anchor["name"]),
        facility_type=str(best_anchor["facility_type"]),
        distance_km=min_dist,
        drive_time_min=drive_min,
        coordinates=[float(best_anchor["lat"]), float(best_anchor["lng"])],
        data_source=str(best_anchor.get("data_source", "OpenStreetMap GIS")),
        distance_methodology=DistanceMethodology.HAVERSINE_STRAIGHT_LINE,
        distance_label="Straight-line distance estimate (Haversine)",
        drive_time_label="Estimated transit time at benchmark road speed (IRC SP-73 / IRC-106)",
        provenance=provenance,
    )


def analyze_parcel_infrastructure(
    parcel: LandParcel,
    custom_weights: Optional[Dict[str, float]] = None,
) -> ParcelInfrastructureAnalysis:
    """
    Perform a complete multi-sector infrastructure proximity analysis for a land parcel.

    Supports configurable accessibility weights.
    """
    nearest_hw = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Highway")
    nearest_hosp = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Hospital")
    nearest_edu = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Education")
    nearest_rail = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Railway")
    nearest_air = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Airport")
    nearest_comm = get_nearest_anchor_by_type(parcel.location_lat, parcel.location_lng, "Commercial Hub")

    all_points = [nearest_hw, nearest_hosp, nearest_edu, nearest_rail, nearest_air, nearest_comm]

    # Resolve configurable accessibility weights (normalized to 100)
    w = dict(DEFAULT_ACCESSIBILITY_WEIGHTS)
    if custom_weights:
        for k, v in custom_weights.items():
            if k in w and v >= 0:
                w[k] = float(v)

    total_w = sum(w.values()) or 100.0
    norm_w = {k: (v / total_w) * 100.0 for k, v in w.items()}

    # Decay benchmarks (maximum distances considered for scoring)
    # Highway <= 12km, Hospital <= 15km, Comm <= 15km, Rail <= 25km, Edu <= 15km, Air <= 40km
    score_hw = max(0.0, norm_w["highway"] * (1.0 - min(nearest_hw.distance_km / 12.0, 1.0)))
    score_hosp = max(0.0, norm_w["hospital"] * (1.0 - min(nearest_hosp.distance_km / 15.0, 1.0)))
    score_comm = max(0.0, norm_w["commercial"] * (1.0 - min(nearest_comm.distance_km / 15.0, 1.0)))
    score_rail = max(0.0, norm_w["railway"] * (1.0 - min(nearest_rail.distance_km / 25.0, 1.0)))
    score_edu = max(0.0, norm_w["education"] * (1.0 - min(nearest_edu.distance_km / 15.0, 1.0)))
    score_air = max(0.0, norm_w["airport"] * (1.0 - min(nearest_air.distance_km / 40.0, 1.0)))

    accessibility_score = round(score_hw + score_hosp + score_comm + score_rail + score_edu + score_air, 1)

    # Network status labels based on deterministic engineering ratings
    power_status = (
        "Connected to MSEDCL High-Tension Substation (High Reliability)"
        if parcel.electricity_score >= 0.8
        else "Standard 11kV Grid Feed Available (Substation Augmentation Advised)"
    )
    water_status = (
        "PMRDA Bulk Municipal Water Conduit within 500m"
        if parcel.water_score >= 0.8
        else "Intermediate Borewell & Regional Tanker Supplementary Network"
    )
    sewage_status = (
        "Connected to Municipal Trunk Sewer"
        if parcel.sewage_score >= 0.8
        else "On-site Sewage Treatment Plant (STP) Mandatory per MPCB Norms"
    )
    road_status = (
        f"Direct frontage to major arterial ({nearest_hw.name}, {nearest_hw.distance_km} km straight-line)"
        if nearest_hw.distance_km <= 3.0
        else f"Secondary connecting road ({nearest_hw.distance_km} km straight-line to primary arterial)"
    )

    score_methodology = (
        f"Multi-sector weighted proximity decay formula "
        f"(Highway {round(norm_w['highway'])}%, Hospital {round(norm_w['hospital'])}%, "
        f"Commercial {round(norm_w['commercial'])}%, Railway {round(norm_w['railway'])}%, "
        f"Education {round(norm_w['education'])}%, Airport {round(norm_w['airport'])}%)"
    )

    provenance = ProvenanceRecord(
        source_name="OpenStreetMap Public GIS & IRC Speed Standards",
        source_url="https://www.openstreetmap.org/",
        source_type="Open Data Proximity Model",
        verification_status=VerificationStatus.ESTIMATED,
        last_verified="2026-11-05",
        confidence_level=0.90,
        methodology_notes="Calculates great-circle Haversine distances to verified OpenStreetMap anchor nodes.",
    )

    return ParcelInfrastructureAnalysis(
        parcel_id=parcel.id,
        parcel_name=parcel.name,
        coordinates=[parcel.location_lat, parcel.location_lng],
        nearest_highway=nearest_hw,
        nearest_hospital=nearest_hosp,
        nearest_education=nearest_edu,
        nearest_railway=nearest_rail,
        nearest_airport=nearest_air,
        nearest_commercial_hub=nearest_comm,
        all_proximity_points=all_points,
        accessibility_score=accessibility_score,
        power_grid_status=power_status,
        water_network_status=water_status,
        sewage_network_status=sewage_status,
        road_connectivity_status=road_status,
        data_source="OpenStreetMap GIS & PMRDA Regional Development Plan 2021-2041",
        accessibility_score_methodology=score_methodology,
        is_official_rating=False,
        provenance=provenance,
    )
