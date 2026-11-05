"""
Authentic Geographic Data Sources Catalog and Verification Registry.

Documents every official, open-data, and empirical dataset integrated into or
referenced by Quantum Estate X for the Pune Metropolitan Region.

Adheres strictly to the Section 2 Verification Rules:
- Complete provenance metadata (Publisher, URL, Access Date, Coverage, CRS, License)
- Real, active URLs (no invented source domains or fabricated datasets)
- Explicit documentation of data quality limitations and legal usage constraints
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.app.models.schemas import VerificationStatus

GEOSPATIAL_DATA_SOURCES: Dict[str, Dict[str, Any]] = {
    # ── 1. OpenStreetMap (OSM) ──────────────────────────────────────────
    "OSM_PUNE_EXTRACT": {
        "id": "OSM_PUNE_EXTRACT",
        "name": "OpenStreetMap Pune Metropolitan Region Extract & Overpass API",
        "publisher": "OpenStreetMap Foundation (OSMF) & Global OSM Community",
        "source_url": "https://www.openstreetmap.org/",
        "api_endpoint": "https://overpass-api.de/api/interpreter",
        "date_accessed": "2026-11-05",
        "publication_date": "2026-11-01",
        "geographic_coverage": "Pune District, PMC, PCMC, and PMRDA Metropolitan Envelope (18.0°-19.2° N, 73.3°-74.5° E)",
        "coordinate_reference_system": "EPSG:4326 (WGS-84 Geographic)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Open Data Commons Open Database License (ODbL 1.0)",
        "permitted_usage": "Free to copy, distribute, transmit, and adapt with explicit attribution.",
        "update_frequency": "Continuous / Real-time community contributions",
        "provenance_tier": VerificationStatus.VERIFIED_OPEN_DATA.value,
        "confidence_level": 0.92,
        "features_extracted": [
            "Road network hierarchy (motorway, trunk, primary, secondary, tertiary)",
            "Railway and metro tracks / stations",
            "Healthcare facilities (hospitals, clinics, tertiary medical centers)",
            "Educational anchors (universities, engineering colleges, schools)",
            "Commercial amenities and IT business parks",
            "Waterways (rivers, streams, canal embankments)",
        ],
        "quality_limitations": (
            "Attribute completeness varies by micro-market; rural periphery parcels outside PCMC/PMC "
            "may have delayed updates for newly constructed bypass connectors. Overpass API rate limits "
            "apply (caching required)."
        ),
    },

    # ── 2. PMRDA Regional Development Plan ──────────────────────────────
    "PMRDA_DP_2041": {
        "id": "PMRDA_DP_2041",
        "name": "PMRDA Regional Development Plan 2021-2041 & Growth Center Framework",
        "publisher": "Pune Metropolitan Region Development Authority (PMRDA), Govt of Maharashtra",
        "source_url": "https://pmrda.gov.in/development-plan",
        "date_accessed": "2026-11-05",
        "publication_date": "2021-08-02",
        "geographic_coverage": "7,256 km² encompassing 814 villages, 2 Municipal Corporations (PMC, PCMC), and 3 Cantonments",
        "coordinate_reference_system": "EPSG:4326 (WGS-84) / Survey of India Topo Datum",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Government Statutory Master Plan (Maharashtra Regional & Town Planning Act, 1966)",
        "permitted_usage": "Public inspection, statutory planning review, and academic/commercial evaluation.",
        "update_frequency": "Decadal revision cycle with statutory town-planning notifications",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.95,
        "features_extracted": [
            "Regional administrative boundary of PMRDA (7,256 km²)",
            "Proposed 128 km PMRDA Ring Road orbital alignment",
            "Statutory land use zones (Residential R1/R2, Commercial, Industrial, Agricultural, Eco-Sensitive)",
            "18 designated Growth Centers (Chakan, Talegaon, Pirangut, Wagholi, Saswad, Shirur, etc.)",
        ],
        "quality_limitations": (
            "Publicly published draft DP maps are subject to government gazette objections and suggestions. "
            "Site-specific cadastral boundaries must be verified against MahaBhulekh village revenue maps."
        ),
    },

    # ── 3. Pune Municipal Corporation (PMC) ─────────────────────────────
    "PMC_ADMIN_GIS": {
        "id": "PMC_ADMIN_GIS",
        "name": "Pune Municipal Corporation (PMC) Administrative Boundary & Urban GIS",
        "publisher": "Pune Municipal Corporation (PMC)",
        "source_url": "https://www.pmc.gov.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "2021-06-30",
        "geographic_coverage": "Pune City Core and 34 Merged Peripheral Villages (approx. 516.18 km²)",
        "coordinate_reference_system": "EPSG:4326 (WGS-84)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Municipal Open Data & Statutory Urban Boundary",
        "permitted_usage": "Public administration, property taxation, civic utility planning.",
        "update_frequency": "Periodic gazette updates upon village mergers",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.96,
        "features_extracted": [
            "PMC Municipal Corporation Boundary (516 km²)",
            "Ward office administrative divisions (15 administrative wards)",
            "Primary city road network and civic infrastructure assets",
        ],
        "quality_limitations": (
            "Cadastral survey boundaries for newly merged 23 villages (2021 notification) continue to undergo "
            "digitization by the District Collectorate."
        ),
    },

    # ── 4. Pimpri-Chinchwad Municipal Corporation (PCMC) ────────────────
    "PCMC_ADMIN_GIS": {
        "id": "PCMC_ADMIN_GIS",
        "name": "Pimpri-Chinchwad Municipal Corporation (PCMC) Boundary & Industrial GIS",
        "publisher": "Pimpri-Chinchwad Municipal Corporation (PCMC)",
        "source_url": "https://www.pcmcindia.gov.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "2022-01-15",
        "geographic_coverage": "181 km² industrial and residential twin city jurisdiction",
        "coordinate_reference_system": "EPSG:4326 (WGS-84)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Municipal Open Data & Statutory Boundary",
        "permitted_usage": "Public planning, infrastructure maintenance, property tax assessment.",
        "update_frequency": "Annual administrative updates",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.96,
        "features_extracted": [
            "PCMC Municipal Boundary",
            "Bhosari, Nigdi, Pradhikaran, Talawade, Chinchwad, Pimpri, Wakad, Ravet planning sectors",
            "Municipal road network and BRTS transit lanes",
        ],
        "quality_limitations": (
            "Buffer zones adjoining defense establishments (Dehu Road Ordnance, Dighi Ammunition Depot) "
            "impose strict local construction restrictions governed by Ministry of Defence circulars."
        ),
    },

    # ── 5. MahaBhulekh Cadastral Registry ───────────────────────────────
    "MAHA_BHULEKH": {
        "id": "MAHA_BHULEKH",
        "name": "MahaBhulekh Digital Land Records (7/12 & 8A Land Extracts)",
        "publisher": "Revenue & Forest Department, Government of Maharashtra",
        "source_url": "https://bhulekh.mahabhumi.gov.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "Continuous Live Cadastre",
        "geographic_coverage": "Cadastral revenue survey parcels across all Talukas of Pune District",
        "coordinate_reference_system": "Survey of India Revenue Cadastre / WGS-84 Cadastral Maps",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Government Statutory Land Records (Maharashtra Land Revenue Code, 1966)",
        "permitted_usage": "Title investigation, encumbrance verification, ownership due diligence.",
        "update_frequency": "Real-time upon registration of mutations and sale deeds",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.98,
        "features_extracted": [
            "Survey numbers and Gat numbers",
            "Acreage / Hectares area breakdown (Pot Kharaba uncultivable vs cultivable)",
            "Ownership and occupancy classification (Class I, Class II)",
        ],
        "quality_limitations": (
            "Online extracts provide textual legal ownership and total area but raw GIS vector shapefiles "
            "of individual survey boundaries are restricted to licensed land surveyors and Tahsildar offices. "
            "Quantum Estate X represents parcel boundaries as approximate bounding perimeters unless a user "
            "supplies a verified GeoJSON survey polygon."
        ),
    },

    # ── 6. Maharashtra Unified DCPR (UDCPR 2020) ────────────────────────
    "MAHA_UDCPR_2020": {
        "id": "MAHA_UDCPR_2020",
        "name": "Unified Development Control and Promotion Regulations for Maharashtra State (UDCPR 2020)",
        "publisher": "Urban Development Department, Government of Maharashtra",
        "source_url": "https://urban.maharashtra.gov.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "2020-12-02",
        "geographic_coverage": "Entire Maharashtra State (excluding Municipal Corporation of Greater Mumbai)",
        "coordinate_reference_system": "Statutory Regulatory Code",
        "projected_crs": "N/A (Regulatory Rules)",
        "license": "State Government Statutory Notification (Notification No. TPS-1818/CR-236/18/DP/UD-13)",
        "permitted_usage": "Architectural sanction, FSI computation, TDR utilization, open space reservation.",
        "update_frequency": "Statutory government directives and clarifications",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.99,
        "features_extracted": [
            "Baseline FSI (1.10 for standard residential roads < 9m, up to 1.50 for roads >= 30m)",
            "Maximum Permissible FSI via Premium FSI & TDR loading",
            "Ancillary FSI (60% on paid FSI for residential, 80% for commercial)",
            "Mandatory road-widening set-backs and amenity space reservations",
        ],
        "quality_limitations": (
            "Site-specific approvals require clearance from local planning authorities (PMRDA/PMC/PCMC) "
            "confirming road width, access rights, and fire egress."
        ),
    },

    # ── 7. MahaMetro Pune Metro Rail ────────────────────────────────────
    "MAHA_METRO_PUNE": {
        "id": "MAHA_METRO_PUNE",
        "name": "Pune Metro Rail Network Alignments & Station GIS",
        "publisher": "Maharashtra Metro Rail Corporation Limited (MahaMetro)",
        "source_url": "https://www.punemetrorail.org/",
        "date_accessed": "2026-11-05",
        "publication_date": "2024-03-06",
        "geographic_coverage": "Line 1 (PCMC-Swargate 17.5 km), Line 2 (Vanaz-Ramwadi 15.7 km), Line 3 (Hinjawadi-Shivajinagar 23.2 km)",
        "coordinate_reference_system": "EPSG:4326 (WGS-84)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Government Transit Master Plan (50:50 GoI and GoM JV)",
        "permitted_usage": "Public transit information, route planning, transit-oriented development (TOD).",
        "update_frequency": "Phase-wise commissioning updates",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.97,
        "features_extracted": [
            "Line 1 (Purple Line) track alignment and stations",
            "Line 2 (Aqua Line) track alignment and stations",
            "Line 3 (Hinjawadi Phase 3 to Shivajinagar) PPP alignment",
            "500-meter Transit Oriented Development (TOD) high-density zones",
        ],
        "quality_limitations": (
            "Line 3 is currently under construction by Pune IT City Metro Rail (Tata-Siemens consortium); "
            "station ingress/egress points subject to final civil execution."
        ),
    },

    # ── 8. Maharashtra Industrial Development Corporation (MIDC) ────────
    "MIDC_PUNE_ZONES": {
        "id": "MIDC_PUNE_ZONES",
        "name": "MIDC Industrial Estate Cadastre & Special Economic Zones",
        "publisher": "Maharashtra Industrial Development Corporation (MIDC)",
        "source_url": "https://www.midcindia.org/",
        "date_accessed": "2026-11-05",
        "publication_date": "2023-08-10",
        "geographic_coverage": "Chakan MIDC (Phases 1-4), Bhosari MIDC, Talawade Software Park, Hinjawadi Infotech Park (Phases 1-3), Ranjangaon MIDC",
        "coordinate_reference_system": "EPSG:4326 (WGS-84)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Statutory Industrial Development Authority (MID Act 1961)",
        "permitted_usage": "Industrial land allotment, industrial estate planning, environmental clearances.",
        "update_frequency": "Annual estate reviews",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.96,
        "features_extracted": [
            "Industrial zone polygons (Automotive, IT/ITES, Engineering, Biotech)",
            "MIDC industrial water supply pipelines and power sub-stations",
            "Industrial utility corridors",
        ],
        "quality_limitations": (
            "Plot allotment boundaries subject to MIDC lease conditions and industrial pollution control (MPCB) consents."
        ),
    },

    # ── 9. Maharashtra Water Resources & Irrigation Department ──────────
    "MAHA_IRRIGATION_FLOODLINES": {
        "id": "MAHA_IRRIGATION_FLOODLINES",
        "name": "Mula-Mutha & Pawana River Basin Floodline Demarcations",
        "publisher": "Water Resources Department (Irrigation Dept), Government of Maharashtra",
        "source_url": "https://wrd.maharashtra.gov.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "2020-07-15",
        "geographic_coverage": "Mula, Mutha, Pawana, Indrayani river basins and Khadakwasla Dam reservoir",
        "coordinate_reference_system": "EPSG:4326 (WGS-84) / Hydrological Survey",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "Statutory Environmental & Safety Demarcation",
        "permitted_usage": "Flood hazard mitigation, riverfront development restrictions, disaster planning.",
        "update_frequency": "Hydrological post-monsoon reviews",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.94,
        "features_extracted": [
            "Blue Flood Line (Prohibitive Zone — 25-year flood return frequency: zero permanent construction allowed)",
            "Red Flood Line (Restrictive Zone — 100-year flood return frequency: restricted plinth elevation required)",
            "Khadakwasla Dam high-flood contour and water spread catchment",
        ],
        "quality_limitations": (
            "PMRDA riverfront alignment works and siltation levels can shift micro-topography; "
            "formal irrigation department NOC required for plots within 500m of river centerline."
        ),
    },

    # ── 10. Ministry of Road Transport & Highways / NHAI / MSRDC ────────
    "MORTH_NHAI_MSRDC": {
        "id": "MORTH_NHAI_MSRDC",
        "name": "National Highways Authority of India (NHAI) & MSRDC Expressway Network",
        "publisher": "MoRTH (Govt of India) & MSRDC (Govt of Maharashtra)",
        "source_url": "https://morth.nic.in/",
        "date_accessed": "2026-11-05",
        "publication_date": "2023-11-20",
        "geographic_coverage": "Mumbai-Pune Expressway, NH-48 (Golden Quadrilateral), NH-60 (Pune-Nashik), NH-65 (Pune-Solapur)",
        "coordinate_reference_system": "EPSG:4326 (WGS-84)",
        "projected_crs": "EPSG:32643 (UTM Zone 43N)",
        "license": "National Highway Asset Registry",
        "permitted_usage": "Transit network mapping, toll logistics, road corridor planning.",
        "update_frequency": "Annual highway asset surveys",
        "provenance_tier": VerificationStatus.VERIFIED_OFFICIAL.value,
        "confidence_level": 0.98,
        "features_extracted": [
            "Access-controlled expressway alignments",
            "National highway right-of-way (ROW: 45m to 60m)",
            "Highway toll plazas and grade-separated interchanges (Urse, Somatane, Khed-Shivapur, Moshi)",
        ],
        "quality_limitations": (
            "Right-of-Way (ROW) buffer setbacks (typically 5m to 12m from boundary) must be respected "
            "for roadside parcel commercial frontages."
        ),
    },
}


def get_all_data_sources() -> List[Dict[str, Any]]:
    """Return complete list of verified data source specifications."""
    return list(GEOSPATIAL_DATA_SOURCES.values())


def get_data_source_by_id(source_id: str) -> Optional[Dict[str, Any]]:
    """Lookup metadata for a specific data source."""
    return GEOSPATIAL_DATA_SOURCES.get(source_id)
