"""
datasets.py - Dataset Generator, Preprocessing & Domain Problem Library for QML.

Provides:
  1. Synthetic 2D Datasets (Linearly Separable, Moons, Circles)
  2. Standard ML Datasets (Iris Binary)
  3. Domain Real Estate Datasets (Pune Land Suitability, Infrastructure Risk)
  4. Leakage-free Preprocessing Pipeline (StandardScaler + Optional PCA dimension reduction)
"""

from typing import Dict, Tuple, Optional, Any, List
import numpy as np
from sklearn.datasets import make_moons, make_circles, make_classification, load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA


class DatasetPreprocessor:
    """
    Leakage-free preprocessing pipeline that fits transformations strictly on X_train.
    """

    def __init__(
        self,
        scaler_type: str = "minmax",  # 'minmax' [0, pi] or 'standard'
        target_dimensions: Optional[int] = None,
        scale_to_pi: bool = True,
    ):
        self.scaler_type = scaler_type.lower()
        self.target_dimensions = target_dimensions
        self.scale_to_pi = scale_to_pi

        if self.scaler_type == "standard":
            self.scaler = StandardScaler()
        else:
            feature_range = (0.0, np.pi) if scale_to_pi else (0.0, 1.0)
            self.scaler = MinMaxScaler(feature_range=feature_range)

        self.pca: Optional[PCA] = None

    def fit_transform(
        self,
        X_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Fits scalers and optional PCA on X_train only, then transforms both splits.
        Guarantees zero data leakage.
        """
        X_tr = np.asarray(X_train, dtype=float)
        d_orig = X_tr.shape[1]

        # 1. Fit & Transform Scaler on X_train
        X_tr_scaled = self.scaler.fit_transform(X_tr)

        # 2. Fit & Transform PCA if dimension reduction requested
        if self.target_dimensions is not None and self.target_dimensions < d_orig:
            self.pca = PCA(n_components=self.target_dimensions, random_state=42)
            X_tr_final = self.pca.fit_transform(X_tr_scaled)
            # Re-scale PCA outputs to [0, pi] if minmax requested
            if self.scaler_type == "minmax":
                X_tr_final = MinMaxScaler(feature_range=(0.0, np.pi)).fit_transform(X_tr_final)
        else:
            X_tr_final = X_tr_scaled

        if X_test is None:
            return X_tr_final, None

        # 3. Transform X_test using fitted parameters
        X_te = np.asarray(X_test, dtype=float)
        X_te_scaled = self.scaler.transform(X_te)
        if self.pca is not None:
            X_te_final = self.pca.transform(X_te_scaled)
            if self.scaler_type == "minmax":
                X_te_final = np.clip(X_te_final, 0.0, np.pi)
        else:
            X_te_final = X_te_scaled

        return X_tr_final, X_te_final


class VQCDatasetLibrary:
    """
    Catalog of synthetic, benchmark, and domain real-estate datasets.
    """

    @staticmethod
    def get_linearly_separable(
        n_samples: int = 100,
        noise: float = 0.1,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Generates 2D linearly separable binary dataset."""
        X, y = make_classification(
            n_samples=n_samples,
            n_features=2,
            n_informative=2,
            n_redundant=0,
            n_clusters_per_class=1,
            flip_y=0.0,
            class_sep=1.5,
            random_state=seed,
        )
        metadata = {
            "dataset_name": "Linearly Separable",
            "n_samples": n_samples,
            "n_features": 2,
            "classes": [0, 1],
            "provenance_tier": "SYNTHETIC_BENCHMARK",
            "description": "2D linearly separable clusters for sanity and convergence checking",
        }
        return X, y, metadata

    @staticmethod
    def get_moons(
        n_samples: int = 100,
        noise: float = 0.15,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Generates 2D interlocking half-moons non-linear dataset."""
        X, y = make_moons(n_samples=n_samples, noise=noise, random_state=seed)
        metadata = {
            "dataset_name": "Two Moons",
            "n_samples": n_samples,
            "n_features": 2,
            "classes": [0, 1],
            "provenance_tier": "SYNTHETIC_BENCHMARK",
            "description": "Non-linearly separable interlocking half-moons challenge",
        }
        return X, y, metadata

    @staticmethod
    def get_circles(
        n_samples: int = 100,
        noise: float = 0.1,
        factor: float = 0.5,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Generates concentric circles non-linear dataset."""
        X, y = make_circles(n_samples=n_samples, noise=noise, factor=factor, random_state=seed)
        metadata = {
            "dataset_name": "Concentric Circles",
            "n_samples": n_samples,
            "n_features": 2,
            "classes": [0, 1],
            "provenance_tier": "SYNTHETIC_BENCHMARK",
            "description": "Radial non-linear classification boundary",
        }
        return X, y, metadata

    @staticmethod
    def get_iris_binary(
        class_pair: Tuple[int, int] = (0, 1),
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Loads canonical Iris dataset filtered to 2 classes (Setosa vs Versicolor)."""
        data = load_iris()
        mask = np.isin(data.target, class_pair)
        X = data.data[mask]
        y = data.target[mask]
        y = (y == class_pair[1]).astype(int)  # Map to 0 and 1

        metadata = {
            "dataset_name": "Iris Binary (Setosa vs Versicolor)",
            "n_samples": len(X),
            "n_features": 4,
            "feature_names": list(data.feature_names),
            "classes": [0, 1],
            "provenance_tier": "BENCHMARK_CANONICAL",
            "description": "Fisher 1936 classic botanical benchmark filtered to 2 classes",
        }
        return X, y, metadata

    @staticmethod
    def get_land_suitability(
        n_samples: int = 120,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Domain Dataset: Real Estate Land Development Suitability.
        Features:
          1. Road distance (km)
          2. Transit/Metro distance (km)
          3. Floodline hazard exposure (0.0 to 1.0)
          4. Topographic slope degree (0 to 30 deg)
        Label:
          1 = High Suitability for Development
          0 = Constrained / Unsuitable
        """
        rng = np.random.default_rng(seed)

        road_dist = rng.uniform(0.1, 4.0, size=n_samples)
        transit_dist = rng.uniform(0.2, 8.0, size=n_samples)
        flood_hazard = rng.uniform(0.0, 1.0, size=n_samples)
        slope_deg = rng.uniform(0.0, 25.0, size=n_samples)

        # Suitability score calculation based on Indian planning norms:
        # Favorable: low road distance, low transit distance, low flood, low slope
        score = (
            2.5 * (4.0 - road_dist) / 4.0
            + 2.0 * (8.0 - transit_dist) / 8.0
            - 4.0 * flood_hazard
            - 2.0 * (slope_deg / 25.0)
            + rng.normal(0.0, 0.35, size=n_samples)
        )
        y = (score > np.median(score)).astype(int)

        X = np.column_stack([road_dist, transit_dist, flood_hazard, slope_deg])
        metadata = {
            "dataset_name": "Pune Land Development Suitability",
            "n_samples": n_samples,
            "n_features": 4,
            "feature_names": [
                "Road Distance (km)",
                "Transit/Metro Distance (km)",
                "Floodline Hazard (0-1)",
                "Slope Angle (deg)",
            ],
            "classes": [0, 1],
            "class_labels": ["Unsuitable / Constrained", "High Development Suitability"],
            "provenance_tier": "SYNTHETIC_BENCHMARK",
            "data_provenance": "SYNTHETIC_BENCHMARK (Simulated indicative parameters based on Pune UDCPR development rules; not transactional registry records)",
        }
        return X, y, metadata

    @staticmethod
    def get_infrastructure_risk(
        n_samples: int = 120,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Domain Dataset: Regional Infrastructure Investment Risk.
        Features:
          1. Transport Circuity Factor (1.1 to 2.2)
          2. Substation Electrical Headroom Load % (40% to 95%)
          3. Drainage Stormwater Deficit Index (0.0 to 1.0)
          4. Environmental Proximity Buffer (0.0 to 1.0)
        Label:
          1 = High Infrastructure Investment Risk
          0 = Low/Manageable Infrastructure Risk
        """
        rng = np.random.default_rng(seed)

        circuity = rng.uniform(1.15, 2.10, size=n_samples)
        substation_load = rng.uniform(0.40, 0.95, size=n_samples)
        drainage_deficit = rng.uniform(0.05, 0.95, size=n_samples)
        env_buffer = rng.uniform(0.10, 0.90, size=n_samples)

        risk_score = (
            1.8 * (circuity - 1.15)
            + 2.5 * (substation_load - 0.40)
            + 2.2 * drainage_deficit
            - 1.5 * env_buffer
            + rng.normal(0.0, 0.25, size=n_samples)
        )
        y = (risk_score > np.median(risk_score)).astype(int)

        X = np.column_stack([circuity, substation_load, drainage_deficit, env_buffer])
        metadata = {
            "dataset_name": "Regional Infrastructure Risk",
            "n_samples": n_samples,
            "n_features": 4,
            "feature_names": [
                "Road Circuity Factor",
                "Substation Grid Load (%)",
                "Drainage Deficit Index",
                "Environmental Buffer Score",
            ],
            "classes": [0, 1],
            "class_labels": ["Low / Manageable Risk", "High Infrastructure Risk"],
            "provenance_tier": "SYNTHETIC_BENCHMARK",
            "data_provenance": "SYNTHETIC_BENCHMARK (Simulated engineering parameters for hybrid QML benchmarking)",
        }
        return X, y, metadata

    @classmethod
    def load_dataset(
        cls,
        dataset_name: str,
        n_samples: int = 100,
        test_size: float = 0.25,
        scale_to_pi: bool = True,
        target_dimensions: Optional[int] = None,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Loads dataset by name, performs stratified train/test split, and applies leakage-free preprocessing.
        """
        key = dataset_name.lower().replace("-", "_").replace(" ", "_")
        if key in ("linearly_separable", "linear"):
            X, y, meta = cls.get_linearly_separable(n_samples=n_samples, seed=seed)
        elif key in ("moons", "two_moons"):
            X, y, meta = cls.get_moons(n_samples=n_samples, seed=seed)
        elif key in ("circles", "concentric_circles"):
            X, y, meta = cls.get_circles(n_samples=n_samples, seed=seed)
        elif key in ("iris", "iris_binary"):
            X, y, meta = cls.get_iris_binary(seed=seed)
        elif key in ("land_suitability", "pune_land_suitability"):
            X, y, meta = cls.get_land_suitability(n_samples=n_samples, seed=seed)
        elif key in ("infrastructure_risk", "infra_risk"):
            X, y, meta = cls.get_infrastructure_risk(n_samples=n_samples, seed=seed)
        else:
            X, y, meta = cls.get_moons(n_samples=n_samples, seed=seed)

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=seed, stratify=y
        )

        # Leakage-free preprocessing
        preprocessor = DatasetPreprocessor(
            scaler_type="minmax",
            scale_to_pi=scale_to_pi,
            target_dimensions=target_dimensions,
        )
        X_tr_proc, X_te_proc = preprocessor.fit_transform(X_train, X_test)

        return {
            "metadata": meta,
            "X_train_raw": X_train,
            "X_test_raw": X_test,
            "X_train": X_tr_proc,
            "X_test": X_te_proc,
            "y_train": y_train,
            "y_test": y_test,
            "num_features": X_tr_proc.shape[1],
            "train_samples": len(y_train),
            "test_samples": len(y_test),
        }
