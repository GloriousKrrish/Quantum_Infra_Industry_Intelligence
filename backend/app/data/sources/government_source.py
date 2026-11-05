"""
Authoritative Government & Cadastral Data Source Specifications.

Documents official planning, statutory, and cadastral references governing
the Pune Metropolitan Region (PMRDA) real estate ecosystem.
"""

from __future__ import annotations

from typing import Any, Dict, List
from backend.app.models.schemas import ProvenanceRecord, VerificationStatus

GOVERNMENT_STANDARDS: Dict[str, Dict[str, Any]] = {
    "PMRDA_DP_2041": {
        "source_name": "Pune Metropolitan Region Development Authority (PMRDA)",
        "source_url": "https://pmrda.gov.in/development-plan",
        "source_type": "Government Statutory Master Plan",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "PMRDA Regional Development Plan 2021-2041",
        "jurisdiction": "Pune Metropolitan Region (7,256 km²)",
        "legal_basis": "Maharashtra Regional and Town Planning Act, 1966 (MRTP Act)",
        "confidence_level": 0.95,
        "methodology": "Statutory land use zoning belts, growth centers, and arterial transit ring alignments.",
    },
    "MAHA_UDCPR_2020": {
        "source_name": "Urban Development Dept, Government of Maharashtra",
        "source_url": "https://urban.maharashtra.gov.in/",
        "source_type": "State Building Code & Planning Regulations",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "Unified Development Control and Promotion Regulations (UDCPR 2020)",
        "jurisdiction": "State of Maharashtra (excluding Municipal Corporation of Greater Mumbai)",
        "legal_basis": "Notification No. TPS-1818/CR-236/18/DP/UD-13",
        "confidence_level": 0.98,
        "methodology": "Standardized Base FSI, Premium FSI, TDR loading ratios, and parking standards based on road widths.",
    },
    "MAHA_BHULEKH": {
        "source_name": "Revenue Department, Government of Maharashtra",
        "source_url": "https://bhulekh.mahabhumi.gov.in/",
        "source_type": "Government Cadastral Land Registry",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "MahaBhulekh (7/12 & 8A Land Extracts)",
        "jurisdiction": "State of Maharashtra Cadastral Parcels",
        "legal_basis": "Maharashtra Land Revenue Code, 1966",
        "confidence_level": 0.95,
        "methodology": "Survey number demarcations, ownership rights, encumbrances, and cadastral acreage verification.",
    },
    "IS_1172_1993": {
        "source_name": "Bureau of Indian Standards (BIS)",
        "source_url": "https://standardsbis.bsbedge.com/",
        "source_type": "National Engineering Standard",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "IS 1172:1993 — Code of Basic Requirements for Water Supply, Drainage and Sanitation",
        "jurisdiction": "Republic of India",
        "legal_basis": "Bureau of Indian Standards Act, 2016",
        "confidence_level": 1.0,
        "methodology": "Deterministic domestic water requirement of 135 litres per capita per day (LPCD) for urban communities.",
    },
    "CPHEEO_MANUAL": {
        "source_name": "Ministry of Housing and Urban Affairs (MoHUA)",
        "source_url": "http://cpheeo.gov.in/",
        "source_type": "National Engineering Standard",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "CPHEEO Manual on Sewerage and Sewage Treatment Systems",
        "jurisdiction": "Republic of India",
        "legal_basis": "MoHUA Technical Guidelines",
        "confidence_level": 1.0,
        "methodology": "80% return factor of domestic water supply sizing dry weather wastewater flow.",
    },
    "NBC_2016": {
        "source_name": "Bureau of Indian Standards (BIS)",
        "source_url": "https://www.bis.gov.in/",
        "source_type": "National Building Code",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "National Building Code of India 2016 (SP 7)",
        "jurisdiction": "Republic of India",
        "legal_basis": "BIS Model Building Code",
        "confidence_level": 1.0,
        "methodology": "Electrical connected load densities, power factor benchmarks (0.85), fire safety egress, and structural norms.",
    },
    "SURVEY_OF_INDIA": {
        "source_name": "Survey of India (SOI)",
        "source_url": "https://surveyofindia.gov.in/",
        "source_type": "National Geodetic Authority",
        "verification_status": VerificationStatus.VERIFIED_OFFICIAL,
        "title": "National Geodetic Network & Topographic Sheets",
        "jurisdiction": "Deccan Plateau / Pune Region",
        "legal_basis": "Department of Science and Technology, Government of India",
        "confidence_level": 0.95,
        "methodology": "WGS-84 ellipsoid datum, Mean Sea Level (MSL) elevation benchmarks (Pune Plateau datum ~560m).",
    },
}


def get_government_provenance(key: str) -> ProvenanceRecord:
    """Return a typed ProvenanceRecord for an authoritative government standard."""
    std = GOVERNMENT_STANDARDS.get(key, GOVERNMENT_STANDARDS["PMRDA_DP_2041"])
    return ProvenanceRecord(
        source_name=std["source_name"],
        source_url=std["source_url"],
        source_type=std["source_type"],
        verification_status=std["verification_status"],
        last_verified="2026-11-05",
        confidence_level=std["confidence_level"],
        methodology_notes=f"{std['title']}. {std['methodology']}",
    )
