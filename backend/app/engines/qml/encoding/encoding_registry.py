"""
encoding_registry.py - Quantum Data Encoding Registry & Comparative Factory.

Provides a decoupled factory interface for instantiating and comparing
quantum data encoders across Basis, Amplitude, Angle, and IQP Feature Maps.
"""

from typing import Dict, List, Optional, Any, Type, Callable
import time
import numpy as np

from .base_encoder import BaseQuantumEncoder, EncodingResult
from .basis_encoding import BasisEncoder
from .amplitude_encoding import AmplitudeEncoder
from .angle_encoding import AngleEncoder
from .feature_maps import IQPFeatureMap


class EncodingRegistry:
    """
    Central factory and comparative benchmark registry for all quantum encoders.
    """

    _REGISTRY: Dict[str, Callable[..., BaseQuantumEncoder]] = {
        "basis": lambda **kw: BasisEncoder(**kw),
        "amplitude": lambda **kw: AmplitudeEncoder(**kw),
        "angle": lambda **kw: AngleEncoder(**kw),
        "angle_rx": lambda **kw: AngleEncoder(rotation="rx", **kw),
        "angle_ry": lambda **kw: AngleEncoder(rotation="ry", **kw),
        "angle_rz": lambda **kw: AngleEncoder(rotation="rz", **kw),
        "angle_combined": lambda **kw: AngleEncoder(rotation="combined", **kw),
        "iqp": lambda **kw: IQPFeatureMap(**kw),
    }

    @classmethod
    def register(cls, name: str, factory: Callable[..., BaseQuantumEncoder]) -> None:
        """Registers a new custom quantum encoder."""
        cls._REGISTRY[name.lower()] = factory

    @classmethod
    def get_encoder(cls, name: str, **kwargs) -> BaseQuantumEncoder:
        """
        Factory method to instantiate an encoder by name.
        """
        key = name.lower()
        if key not in cls._REGISTRY:
            raise KeyError(
                f"Unknown quantum encoder '{name}'. Available encoders: {list(cls._REGISTRY.keys())}"
            )
        return cls._REGISTRY[key](**kwargs)

    @classmethod
    def list_encoders(cls) -> List[Dict[str, Any]]:
        """
        Returns catalog of available encoders with their descriptions and scaling laws.
        """
        catalog = []
        for name in cls._REGISTRY.keys():
            try:
                # Instantiate with default parameters for introspection
                encoder = cls.get_encoder(name)
                meta = encoder.get_metadata()
                meta["identifier"] = name
                catalog.append(meta)
            except Exception as e:
                catalog.append({"identifier": name, "error": str(e)})
        return catalog

    @classmethod
    def compare_encodings(
        cls,
        data: Any,
        encoder_names: Optional[List[str]] = None,
        transpile_metrics: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Executes and benchmarks multiple encoders on the same dataset sample.
        Returns actual empirical resource comparisons (no hardcoding).
        """
        if encoder_names is None:
            # Default set of continuous-compatible encoders
            encoder_names = ["amplitude", "angle_ry", "angle_rx", "angle_rz", "iqp"]

        results = []
        arr = np.asarray(data)

        for enc_name in encoder_names:
            try:
                # Special handling: if basis encoder requested, ensure input is binary
                if enc_name == "basis":
                    # Convert to binary threshold
                    binary_data = (arr > np.median(arr)).astype(int)
                    encoder = cls.get_encoder(enc_name)
                    t0 = time.perf_counter()
                    res = encoder.encode(binary_data, transpile_metrics=transpile_metrics)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                else:
                    encoder = cls.get_encoder(enc_name)
                    t0 = time.perf_counter()
                    res = encoder.encode(arr, transpile_metrics=transpile_metrics)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0

                dom = res.get_dominant_state()
                results.append({
                    "encoder_name": enc_name,
                    "status": "SUCCESS",
                    "num_qubits": res.circuit.num_qubits,
                    "circuit_depth": res.metrics.circuit_depth,
                    "total_gates": res.metrics.total_gates,
                    "single_qubit_gates": res.metrics.single_qubit_gates,
                    "two_qubit_gates": res.metrics.two_qubit_gates,
                    "multi_qubit_gates": res.metrics.multi_qubit_gates,
                    "num_parameters": res.metrics.num_parameters,
                    "statevector_dimension": res.metrics.statevector_dimension,
                    "gate_breakdown": res.metrics.gate_breakdown,
                    "transpiled_depth": res.metrics.transpiled_depth,
                    "transpiled_cx_count": res.metrics.transpiled_cx_count,
                    "dominant_basis_state": dom["bitstring"],
                    "dominant_probability": dom["probability"],
                    "encoding_time_ms": round(elapsed_ms, 3),
                })
            except Exception as e:
                results.append({
                    "encoder_name": enc_name,
                    "status": "ERROR",
                    "error_message": str(e),
                })

        return results

