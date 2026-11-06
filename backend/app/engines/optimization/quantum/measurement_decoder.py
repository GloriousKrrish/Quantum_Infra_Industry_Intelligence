"""
measurement_decoder.py - Measurement Distribution Decoder for QAOA.

Analyzes raw measurement counts from Qiskit Aer quantum simulation,
evaluating exact QUBO energies, probability distributions, expectation values,
and ground-state overlap.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..qubo.qubo_model import QUBOModel


@dataclass
class BitstringMeasurement:
    bitstring: str
    counts: int
    probability: float
    energy: float
    is_ground_state: bool = False


@dataclass
class QAOADecodedResult:
    most_probable_bitstring: str
    most_probable_probability: float
    best_energy_bitstring: str
    best_energy: float
    expected_energy: float
    ground_state_probability: float
    total_shots: int
    top_measurements: List[BitstringMeasurement]
    all_measurements: Dict[str, int]


class MeasurementDecoder:
    """
    Decodes measurement bitstrings and evaluates energy distribution against QUBO.
    """

    def __init__(self, qubo: QUBOModel):
        self.qubo = qubo

    def decode_counts(
        self,
        counts: Dict[str, int],
        ground_state_energy: Optional[float] = None,
        top_k: int = 15
    ) -> QAOADecodedResult:
        total_shots = sum(counts.values())
        if total_shots == 0:
            raise ValueError("Measurement counts dictionary is empty.")

        measurements: List[BitstringMeasurement] = []
        best_bitstring = ""
        best_energy = float("inf")
        sum_energy = 0.0
        ground_state_counts = 0

        # Sort bitstrings by frequency
        sorted_counts = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        most_probable_bitstring = sorted_counts[0][0].replace(" ", "")[::-1]
        most_probable_probability = sorted_counts[0][1] / total_shots

        for bstr, cnt in sorted_counts:
            # Qiskit counts use little-endian bitstrings (qubit 0 is rightmost).
            # We reverse so index i corresponds to variable x_i.
            clean_bstr = bstr.replace(" ", "")[::-1]
            energy = self.qubo.evaluate_energy(clean_bstr)
            prob = cnt / total_shots
            sum_energy += prob * energy

            is_gs = False
            if ground_state_energy is not None:
                is_gs = abs(energy - ground_state_energy) < 1e-6
                if is_gs:
                    ground_state_counts += cnt

            if energy < best_energy:
                best_energy = energy
                best_bitstring = clean_bstr

            measurements.append(
                BitstringMeasurement(
                    bitstring=clean_bstr,
                    counts=cnt,
                    probability=prob,
                    energy=round(energy, 6),
                    is_ground_state=is_gs,
                )
            )

        ground_state_prob = (
            ground_state_counts / total_shots if ground_state_energy is not None else 0.0
        )

        return QAOADecodedResult(
            most_probable_bitstring=most_probable_bitstring,
            most_probable_probability=most_probable_probability,
            best_energy_bitstring=best_bitstring,
            best_energy=round(best_energy, 6),
            expected_energy=round(sum_energy, 6),
            ground_state_probability=round(ground_state_prob, 6),
            total_shots=total_shots,
            top_measurements=measurements[:top_k],
            all_measurements=counts,
        )
