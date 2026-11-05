"""
High-Performance Metric Spatial Indexing Engine.

Uses scipy.spatial.KDTree over projected UTM Zone 43N coordinates to achieve
sub-millisecond spatial search operations:
- K-Nearest Neighbor (k-NN) queries in O(log N)
- Metric radius searches (e.g., all amenities within 3,000 meters)
- Category-filtered spatial queries
- Axis-aligned bounding box containment
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial import KDTree

from backend.app.engines.geospatial.coordinate_transform import (
    haversine_distance,
    projected_euclidean_distance,
    wgs84_to_utm43n,
)


class SpatialFeatureIndex:
    """
    Projected 2D metric spatial index storing geographic features in UTM Zone 43N.
    """

    def __init__(self, features: Optional[List[Dict[str, Any]]] = None) -> None:
        self.features: List[Dict[str, Any]] = []
        self.coords_utm: np.ndarray = np.empty((0, 2), dtype=np.float64)
        self.tree: Optional[KDTree] = None
        if features:
            self.build(features)

    def build(self, features: List[Dict[str, Any]]) -> None:
        """
        Build or rebuild the KDTree index from a list of feature dictionaries.
        Each feature must have 'lat' and 'lng' attributes or a GeoJSON centroid.
        """
        self.features = list(features)
        coords_list: List[Tuple[float, float]] = []

        for feat in self.features:
            lat = feat.get("lat")
            lng = feat.get("lng")
            if lat is None or lng is None:
                # Try GeoJSON properties
                geom = feat.get("geometry", {})
                if geom.get("type") == "Point":
                    lng, lat = geom.get("coordinates", [0.0, 0.0])
                else:
                    centroid = feat.get("properties", {}).get("centroid", [0.0, 0.0])
                    lng, lat = centroid[0], centroid[1]

            e, n = wgs84_to_utm43n(float(lat), float(lng))
            coords_list.append((e, n))

        if coords_list:
            self.coords_utm = np.array(coords_list, dtype=np.float64)
            self.tree = KDTree(self.coords_utm)
        else:
            self.coords_utm = np.empty((0, 2), dtype=np.float64)
            self.tree = None

    def query_nearest(
        self,
        lat: float,
        lng: float,
        k: int = 1,
        category: Optional[str] = None,
        max_distance_meters: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find k nearest features to (lat, lng).

        Returns:
            List of dictionaries with feature data, 'distance_meters', and 'distance_km'.
        """
        if self.tree is None or len(self.features) == 0:
            return []

        target_e, target_n = wgs84_to_utm43n(lat, lng)

        # If category filter requested, query more points to ensure adequate category matches
        query_k = min(len(self.features), k * 5 if category else k)
        distances, indices = self.tree.query([target_e, target_n], k=query_k)

        if query_k == 1:
            distances = [distances]
            indices = [indices]

        results: List[Dict[str, Any]] = []
        for dist_m, idx in zip(distances, indices):
            if idx >= len(self.features) or math.isinf(dist_m):
                continue

            feat = self.features[idx]
            if category:
                feat_cat = feat.get("category") or feat.get("facility_type") or feat.get("type")
                if str(feat_cat).lower() != category.lower():
                    continue

            if max_distance_meters is not None and dist_m > max_distance_meters:
                continue

            res_item = dict(feat)
            res_item["distance_meters"] = round(float(dist_m), 1)
            res_item["distance_km"] = round(float(dist_m) / 1000.0, 3)
            # Also calculate great-circle Haversine for scientific comparison
            feat_lat = feat.get("lat", lat)
            feat_lng = feat.get("lng", lng)
            res_item["haversine_distance_km"] = round(
                haversine_distance(lat, lng, feat_lat, feat_lng), 3
            )
            results.append(res_item)

            if len(results) >= k:
                break

        return results

    def query_radius(
        self,
        lat: float,
        lng: float,
        radius_meters: float,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find all features located within radius_meters of (lat, lng).
        """
        if self.tree is None or len(self.features) == 0:
            return []

        target_e, target_n = wgs84_to_utm43n(lat, lng)
        indices = self.tree.query_ball_point([target_e, target_n], r=radius_meters)

        results: List[Dict[str, Any]] = []
        for idx in indices:
            feat = self.features[idx]
            if category:
                feat_cat = feat.get("category") or feat.get("facility_type") or feat.get("type")
                if str(feat_cat).lower() != category.lower():
                    continue

            feat_e, feat_n = self.coords_utm[idx]
            dist_m = math.hypot(feat_e - target_e, feat_n - target_n)

            res_item = dict(feat)
            res_item["distance_meters"] = round(float(dist_m), 1)
            res_item["distance_km"] = round(float(dist_m) / 1000.0, 3)
            results.append(res_item)

        # Sort by distance
        results.sort(key=lambda x: x["distance_meters"])
        return results

    def query_bbox(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
    ) -> List[Dict[str, Any]]:
        """Find all features whose point coordinates fall within the bounding box."""
        results: List[Dict[str, Any]] = []
        for feat in self.features:
            f_lat = feat.get("lat")
            f_lng = feat.get("lng")
            if f_lat is not None and f_lng is not None:
                if min_lat <= f_lat <= max_lat and min_lng <= f_lng <= max_lng:
                    results.append(dict(feat))
        return results
