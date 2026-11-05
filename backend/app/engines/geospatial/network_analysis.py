"""
Road and Transit Network Graph Analysis Engine.

Implements topological network routing, connectivity analysis, and transit time
estimation for the Pune Metropolitan Region using NetworkX:
- Road hierarchy representation (Expressway, National Highway, State Highway, Arterial, Metro)
- Dijkstra shortest-path calculations along network topology
- Clear scientific distinction between straight-line (Haversine) distance and network road distance
- Realistic transit time estimation incorporating IRC-106 guidelines and peak congestion multipliers
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from backend.app.engines.geospatial.coordinate_transform import (
    haversine_distance,
    wgs84_to_utm43n,
)

# Indian Road Congress (IRC) benchmark average operating speeds and congestion multipliers
ROAD_SPEED_PROFILES: Dict[str, Dict[str, float]] = {
    "expressway": {
        "free_flow_speed_kmh": 85.0,
        "peak_speed_kmh": 70.0,
        "congestion_factor": 1.21,
    },
    "national_highway": {
        "free_flow_speed_kmh": 60.0,
        "peak_speed_kmh": 45.0,
        "congestion_factor": 1.33,
    },
    "state_highway": {
        "free_flow_speed_kmh": 48.0,
        "peak_speed_kmh": 35.0,
        "congestion_factor": 1.37,
    },
    "arterial": {
        "free_flow_speed_kmh": 38.0,
        "peak_speed_kmh": 24.0,
        "congestion_factor": 1.58,
    },
    "metro": {
        "free_flow_speed_kmh": 33.0,
        "peak_speed_kmh": 33.0,
        "congestion_factor": 1.0,  # Grade-separated rail transit has zero road congestion
    },
    "local_connector": {
        "free_flow_speed_kmh": 28.0,
        "peak_speed_kmh": 18.0,
        "congestion_factor": 1.55,
    },
}

# ═══════════════════════════════════════════════════════════════════════
# PUNE METROPOLITAN REGION TOPOLOGICAL ROAD NETWORK GRAPH
# ═══════════════════════════════════════════════════════════════════════

NETWORK_NODES: Dict[str, Dict[str, Any]] = {
    # ── Expressways & Bypass Corridors ──────────────────────────────────
    "URSE_TOLL": {"name": "Urse Toll Plaza (Mumbai-Pune Expressway)", "lat": 18.7180, "lng": 73.6930, "type": "Toll"},
    "DEHU_ROAD": {"name": "Dehu Road Junction (NH-48 & Expressway)", "lat": 18.6750, "lng": 73.7220, "type": "Junction"},
    "MAMURDI_INTERCHANGE": {"name": "Mamurdi Expressway Interchange", "lat": 18.6571, "lng": 73.7489, "type": "Interchange"},
    "WAKAD_FLYOVER": {"name": "Wakad Flyover (NH-48 & Hinjawadi Rd)", "lat": 18.5980, "lng": 73.7630, "type": "Junction"},
    "CHANDANI_CHOWK": {"name": "Chandani Chowk Multimodal Flyover (NH-48)", "lat": 18.5080, "lng": 73.7920, "type": "Junction"},
    "WARJE_FLYOVER": {"name": "Warje Flyover (NH-48)", "lat": 18.4850, "lng": 73.8050, "type": "Junction"},
    "KATRAJ_CHOWK": {"name": "Katraj Chowk (NH-48 Southern Gate)", "lat": 18.4550, "lng": 73.8560, "type": "Junction"},

    # ── Hinjawadi IT Corridor ───────────────────────────────────────────
    "HINJAWADI_PH1": {"name": "Hinjawadi Phase 1 (Shivaji Chowk)", "lat": 18.5912, "lng": 73.7380, "type": "IT_Hub"},
    "HINJAWADI_PH2": {"name": "Hinjawadi Phase 2 (Wipro Circle)", "lat": 18.5860, "lng": 73.7120, "type": "IT_Hub"},
    "HINJAWADI_PH3": {"name": "Hinjawadi Phase 3 (Megapolis Circle)", "lat": 18.5790, "lng": 73.6890, "type": "IT_Hub"},

    # ── PCMC Industrial Corridor (NH-60) ────────────────────────────────
    "NIGDI_CHOWK": {"name": "Nigdi Pradhikaran Chowk", "lat": 18.6520, "lng": 73.7740, "type": "Junction"},
    "CHINCHWAD_STATION": {"name": "Chinchwad Station Chowk", "lat": 18.6280, "lng": 73.7840, "type": "Railway"},
    "PIMPRI_CHOWK": {"name": "Pimpri Chowk / PCMC HQ", "lat": 18.6240, "lng": 73.8010, "type": "Municipal_HQ"},
    "BHOSARI_MIDC": {"name": "Bhosari MIDC Industrial Gate (NH-60)", "lat": 18.6300, "lng": 73.8450, "type": "Industrial"},
    "MOSHI_TOLL": {"name": "Moshi Toll Plaza (NH-60)", "lat": 18.6810, "lng": 73.8510, "type": "Toll"},
    "CHAKAN_MIDC": {"name": "Chakan MIDC Industrial Corridor", "lat": 18.7609, "lng": 73.8639, "type": "Industrial"},
    "TALEGAON_DABHADE": {"name": "Talegaon Dabhade Industrial Hub", "lat": 18.7335, "lng": 73.6757, "type": "Industrial"},

    # ── Pune Core & Eastern Corridor (SH-27) ────────────────────────────
    "SHIVAJINAGAR": {"name": "Shivajinagar Multimodal Transit Hub", "lat": 18.5310, "lng": 73.8520, "type": "Transit_Hub"},
    "PUNE_STATION": {"name": "Pune Junction Railway Station", "lat": 18.5289, "lng": 73.8744, "type": "Railway"},
    "SWARGATE": {"name": "Swargate Multimodal Bus & Metro Hub", "lat": 18.5010, "lng": 73.8580, "type": "Transit_Hub"},
    "YERAWADA": {"name": "Yerawada Gunjan Chowk", "lat": 18.5520, "lng": 73.8830, "type": "Junction"},
    "KALYANI_NAGAR": {"name": "Kalyani Nagar / Ramwadi", "lat": 18.5510, "lng": 73.9050, "type": "Commercial"},
    "PUNE_AIRPORT": {"name": "Pune International Airport (PNQ Lohegaon)", "lat": 18.5822, "lng": 73.9197, "type": "Airport"},
    "KHARADI_EON": {"name": "Kharadi EON Free Zone / WTC", "lat": 18.5535, "lng": 73.9455, "type": "IT_Hub"},
    "HADAPSAR_MAGARPATTA": {"name": "Hadapsar / Magarpatta Cybercity", "lat": 18.5089, "lng": 73.9260, "type": "Commercial"},
    "WAGHOLI_BYPASS": {"name": "Wagholi Bypass (SH-27 Nagar Road)", "lat": 18.5788, "lng": 73.9787, "type": "Junction"},
    "PIRANGUT": {"name": "Pirangut Industrial Corridor", "lat": 18.5164, "lng": 73.6863, "type": "Industrial"},
}

# Network road segments with distance (km) and road hierarchy type
NETWORK_EDGES: List[Tuple[str, str, float, str]] = [
    # Expressway Corridor
    ("URSE_TOLL", "DEHU_ROAD", 8.2, "expressway"),
    ("DEHU_ROAD", "MAMURDI_INTERCHANGE", 4.1, "expressway"),
    ("MAMURDI_INTERCHANGE", "WAKAD_FLYOVER", 7.8, "national_highway"),
    ("WAKAD_FLYOVER", "CHANDANI_CHOWK", 10.4, "national_highway"),
    ("CHANDANI_CHOWK", "WARJE_FLYOVER", 4.5, "national_highway"),
    ("WARJE_FLYOVER", "KATRAJ_CHOWK", 8.6, "national_highway"),

    # Hinjawadi Links
    ("WAKAD_FLYOVER", "HINJAWADI_PH1", 3.8, "arterial"),
    ("HINJAWADI_PH1", "HINJAWADI_PH2", 3.2, "arterial"),
    ("HINJAWADI_PH2", "HINJAWADI_PH3", 3.9, "arterial"),
    ("HINJAWADI_PH3", "PIRANGUT", 9.4, "state_highway"),  # Hinjawadi-Pirangut Ghat link

    # PCMC Corridor
    ("DEHU_ROAD", "NIGDI_CHOWK", 6.2, "national_highway"),
    ("NIGDI_CHOWK", "CHINCHWAD_STATION", 3.9, "arterial"),
    ("CHINCHWAD_STATION", "PIMPRI_CHOWK", 2.8, "arterial"),
    ("PIMPRI_CHOWK", "BHOSARI_MIDC", 5.1, "arterial"),
    ("BHOSARI_MIDC", "MOSHI_TOLL", 6.3, "national_highway"),
    ("MOSHI_TOLL", "CHAKAN_MIDC", 11.2, "national_highway"),
    ("DEHU_ROAD", "TALEGAON_DABHADE", 7.5, "national_highway"),
    ("TALEGAON_DABHADE", "CHAKAN_MIDC", 18.5, "state_highway"),  # Talegaon-Chakan Industrial Belt

    # PCMC to Pune City
    ("PIMPRI_CHOWK", "SHIVAJINAGAR", 12.4, "arterial"),
    ("BHOSARI_MIDC", "YERAWADA", 10.2, "arterial"),

    # Pune City Core
    ("SHIVAJINAGAR", "PUNE_STATION", 2.6, "arterial"),
    ("SHIVAJINAGAR", "SWARGATE", 4.8, "arterial"),
    ("CHANDANI_CHOWK", "SHIVAJINAGAR", 7.9, "arterial"),
    ("SWARGATE", "KATRAJ_CHOWK", 5.2, "arterial"),
    ("SWARGATE", "HADAPSAR_MAGARPATTA", 7.1, "arterial"),

    # Eastern Nagar Road Corridor (SH-27)
    ("PUNE_STATION", "YERAWADA", 3.4, "arterial"),
    ("YERAWADA", "KALYANI_NAGAR", 3.1, "arterial"),
    ("YERAWADA", "PUNE_AIRPORT", 4.9, "arterial"),
    ("KALYANI_NAGAR", "KHARADI_EON", 4.8, "arterial"),
    ("KHARADI_EON", "WAGHOLI_BYPASS", 6.5, "state_highway"),
    ("KHARADI_EON", "HADAPSAR_MAGARPATTA", 5.9, "arterial"),

    # Pirangut to Chandani Chowk
    ("PIRANGUT", "CHANDANI_CHOWK", 11.8, "state_highway"),
]


class PuneRoadNetwork:
    """
    Graph-theoretical routing and accessibility engine for the Pune Metropolitan Region.
    """

    def __init__(self) -> None:
        self.graph = nx.Graph()
        self._build_network()

    def _build_network(self) -> None:
        for node_id, data in NETWORK_NODES.items():
            self.graph.add_node(
                node_id,
                name=data["name"],
                lat=data["lat"],
                lng=data["lng"],
                type=data["type"],
            )

        for u, v, dist_km, road_type in NETWORK_EDGES:
            profile = ROAD_SPEED_PROFILES.get(road_type, ROAD_SPEED_PROFILES["arterial"])
            free_speed = profile["free_flow_speed_kmh"]
            peak_speed = profile["peak_speed_kmh"]

            time_free_min = (dist_km / free_speed) * 60.0
            time_peak_min = (dist_km / peak_speed) * 60.0

            self.graph.add_edge(
                u,
                v,
                distance_km=dist_km,
                road_type=road_type,
                speed_free_kmh=free_speed,
                speed_peak_kmh=peak_speed,
                time_free_min=round(time_free_min, 1),
                time_peak_min=round(time_peak_min, 1),
            )

    def find_nearest_node(self, lat: float, lng: float) -> Tuple[str, float]:
        """
        Find closest road network graph vertex to a geographic coordinate.
        Returns: (node_id, distance_to_node_km)
        """
        best_node = ""
        min_dist = float("inf")

        for node_id, data in NETWORK_NODES.items():
            dist = haversine_distance(lat, lng, data["lat"], data["lng"])
            if dist < min_dist:
                min_dist = dist
                best_node = node_id

        return best_node, round(min_dist, 3)

    def calculate_road_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> Dict[str, Any]:
        """
        Calculate shortest network path and compare with straight-line distance.

        Returns comprehensive analysis with:
        - straight_line_distance_km
        - network_distance_km
        - circuity_factor (ratio of network to straight-line distance)
        - free_flow_time_minutes
        - peak_travel_time_minutes
        - route_nodes and step-by-step road segments
        """
        straight_dist_km = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)

        start_node, dist_to_start = self.find_nearest_node(origin_lat, origin_lng)
        end_node, dist_to_end = self.find_nearest_node(dest_lat, dest_lng)

        if start_node == end_node:
            # Same local cluster
            local_speed = 30.0
            time_min = (straight_dist_km / local_speed) * 60.0
            return {
                "origin": [origin_lat, origin_lng],
                "destination": [dest_lat, dest_lng],
                "straight_line_distance_km": round(straight_dist_km, 2),
                "network_distance_km": round(straight_dist_km * 1.25, 2),
                "circuity_factor": 1.25,
                "free_flow_time_minutes": round(time_min, 1),
                "peak_travel_time_minutes": round(time_min * 1.45, 1),
                "route_path": [start_node],
                "route_segments": [],
                "is_direct_local": True,
                "methodology": "Local cluster approximation: IRC urban access speed (30 km/h) with 1.25 circuity.",
            }

        try:
            path = nx.shortest_path(self.graph, start_node, end_node, weight="distance_km")
            net_dist_km = 0.0
            total_free_min = 0.0
            total_peak_min = 0.0
            segments: List[Dict[str, Any]] = []

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge_data = self.graph[u][v]
                seg_dist = edge_data["distance_km"]
                net_dist_km += seg_dist
                total_free_min += edge_data["time_free_min"]
                total_peak_min += edge_data["time_peak_min"]

                segments.append({
                    "from_node": u,
                    "to_node": v,
                    "road_name": f"{NETWORK_NODES[u]['name']} → {NETWORK_NODES[v]['name']}",
                    "road_type": edge_data["road_type"],
                    "distance_km": seg_dist,
                    "speed_kmh": edge_data["speed_free_kmh"],
                    "travel_time_min": edge_data["time_peak_min"],
                })

            # Add access legs from actual coordinates to entry/exit nodes
            access_km = dist_to_start + dist_to_end
            access_time_free = (access_km / 28.0) * 60.0
            access_time_peak = (access_km / 18.0) * 60.0

            total_network_km = net_dist_km + access_km
            circuity = round(total_network_km / max(straight_dist_km, 0.01), 2)

            return {
                "origin": [origin_lat, origin_lng],
                "destination": [dest_lat, dest_lng],
                "straight_line_distance_km": round(straight_dist_km, 2),
                "network_distance_km": round(total_network_km, 2),
                "circuity_factor": circuity,
                "free_flow_time_minutes": round(total_free_min + access_time_free, 1),
                "peak_travel_time_minutes": round(total_peak_min + access_time_peak, 1),
                "route_path": path,
                "route_segments": segments,
                "is_direct_local": False,
                "methodology": (
                    f"Topological Dijkstra route across {len(path)} network nodes. "
                    f"Circuity factor {circuity:.2f} reflects regional terrain and arterial layout. "
                    f"Speeds calibrated to IRC SP-73 / IRC-106 norms."
                ),
            }

        except nx.NetworkXNoPath:
            # Fallback if disconnected
            circuity = 1.35
            net_km = straight_dist_km * circuity
            time_min = (net_km / 40.0) * 60.0
            return {
                "origin": [origin_lat, origin_lng],
                "destination": [dest_lat, dest_lng],
                "straight_line_distance_km": round(straight_dist_km, 2),
                "network_distance_km": round(net_km, 2),
                "circuity_factor": circuity,
                "free_flow_time_minutes": round(time_min, 1),
                "peak_travel_time_minutes": round(time_min * 1.4, 1),
                "route_path": [],
                "route_segments": [],
                "is_direct_local": False,
                "methodology": "Empirical circuity estimate (1.35x Haversine).",
            }


# Singleton instance for platform-wide reuse
_ROAD_NETWORK: Optional[PuneRoadNetwork] = None


def get_road_network() -> PuneRoadNetwork:
    """Retrieve or initialize the singleton road network graph."""
    global _ROAD_NETWORK
    if _ROAD_NETWORK is None:
        _ROAD_NETWORK = PuneRoadNetwork()
    return _ROAD_NETWORK
