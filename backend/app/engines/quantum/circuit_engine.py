"""
Quantum Circuit Engine for Quantum Estate X.

Translates high-level circuit specifications into Qiskit QuantumCircuit instances,
validates quantum operations, and extracts structural metrics (depth, gate counts).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from qiskit import QuantumCircuit
from qiskit.circuit.exceptions import CircuitError


class CircuitValidationError(ValueError):
    """Raised when circuit specification violates quantum physical or sizing constraints."""
    pass


def validate_qubit_bounds(num_qubits: int, max_qubits: int = 8) -> None:
    """Ensure qubit count is within reasonable simulation bounds (1-8 qubits)."""
    if not isinstance(num_qubits, int):
        raise CircuitValidationError(f"num_qubits must be an integer, got {type(num_qubits)}")
    if num_qubits < 1 or num_qubits > max_qubits:
        raise CircuitValidationError(
            f"Supported qubit range is 1 to {max_qubits} qubits; requested {num_qubits}."
        )


def build_qiskit_circuit(
    num_qubits: int,
    operations: List[Dict[str, Any]],
    with_measurements: bool = False,
) -> QuantumCircuit:
    """
    Construct a validated Qiskit QuantumCircuit from structured operations.

    Operation schema:
    {
        "gate": str,          # "H", "X", "CX", "RX", etc.
        "targets": List[int], # Target qubit indices
        "controls": List[int],# Control qubit indices (for CX, CZ, CCX)
        "params": Dict[str, float] | List[float] | float | None  # Parameter value(s)
    }
    """
    validate_qubit_bounds(num_qubits)

    # Initialize circuit with classical register if measurements requested
    qc = QuantumCircuit(num_qubits, num_qubits if with_measurements else 0)

    for step_idx, op in enumerate(operations):
        gate_name = op.get("gate", "").upper()
        targets = op.get("targets", [])
        controls = op.get("controls", [])
        raw_params = op.get("params")

        # Basic index validation
        all_qubits = list(targets) + list(controls)
        for q in all_qubits:
            if not isinstance(q, int) or q < 0 or q >= num_qubits:
                raise CircuitValidationError(
                    f"Operation #{step_idx} ({gate_name}): Qubit index {q} is out of bounds for {num_qubits}-qubit circuit."
                )

        if len(set(all_qubits)) != len(all_qubits):
            raise CircuitValidationError(
                f"Operation #{step_idx} ({gate_name}): Control and target qubits must be disjoint; received targets={targets}, controls={controls}."
            )

        # Gate-specific dispatch
        if gate_name == "I":
            if len(targets) != 1:
                raise CircuitValidationError(f"I gate requires exactly 1 target; got {targets}")
            qc.id(targets[0])

        elif gate_name == "X":
            if len(targets) != 1:
                raise CircuitValidationError(f"X gate requires exactly 1 target; got {targets}")
            qc.x(targets[0])

        elif gate_name == "Y":
            if len(targets) != 1:
                raise CircuitValidationError(f"Y gate requires exactly 1 target; got {targets}")
            qc.y(targets[0])

        elif gate_name == "Z":
            if len(targets) != 1:
                raise CircuitValidationError(f"Z gate requires exactly 1 target; got {targets}")
            qc.z(targets[0])

        elif gate_name == "H":
            if len(targets) != 1:
                raise CircuitValidationError(f"H gate requires exactly 1 target; got {targets}")
            qc.h(targets[0])

        elif gate_name == "S":
            if len(targets) != 1:
                raise CircuitValidationError(f"S gate requires exactly 1 target; got {targets}")
            qc.s(targets[0])

        elif gate_name in ("SDG", "S_DAG"):
            if len(targets) != 1:
                raise CircuitValidationError(f"Sdg gate requires exactly 1 target; got {targets}")
            qc.sdg(targets[0])

        elif gate_name == "T":
            if len(targets) != 1:
                raise CircuitValidationError(f"T gate requires exactly 1 target; got {targets}")
            qc.t(targets[0])

        elif gate_name in ("TDG", "T_DAG"):
            if len(targets) != 1:
                raise CircuitValidationError(f"Tdg gate requires exactly 1 target; got {targets}")
            qc.tdg(targets[0])

        elif gate_name == "RX":
            if len(targets) != 1:
                raise CircuitValidationError(f"RX gate requires exactly 1 target; got {targets}")
            theta = _extract_param(raw_params, default=math.pi / 2.0)
            qc.rx(theta, targets[0])

        elif gate_name == "RY":
            if len(targets) != 1:
                raise CircuitValidationError(f"RY gate requires exactly 1 target; got {targets}")
            theta = _extract_param(raw_params, default=math.pi / 2.0)
            qc.ry(theta, targets[0])

        elif gate_name == "RZ":
            if len(targets) != 1:
                raise CircuitValidationError(f"RZ gate requires exactly 1 target; got {targets}")
            phi = _extract_param(raw_params, default=math.pi / 2.0)
            qc.rz(phi, targets[0])

        elif gate_name in ("CX", "CNOT"):
            ctrl = controls[0] if controls else (targets[0] if len(targets) == 2 else None)
            tgt = targets[0] if controls else (targets[1] if len(targets) == 2 else None)
            if ctrl is None or tgt is None:
                raise CircuitValidationError(
                    f"CX/CNOT gate requires 1 control and 1 target qubit; received controls={controls}, targets={targets}."
                )
            qc.cx(ctrl, tgt)

        elif gate_name == "CZ":
            ctrl = controls[0] if controls else (targets[0] if len(targets) == 2 else None)
            tgt = targets[0] if controls else (targets[1] if len(targets) == 2 else None)
            if ctrl is None or tgt is None:
                raise CircuitValidationError(
                    f"CZ gate requires 1 control and 1 target qubit; received controls={controls}, targets={targets}."
                )
            qc.cz(ctrl, tgt)

        elif gate_name == "SWAP":
            if len(targets) != 2:
                raise CircuitValidationError(f"SWAP gate requires 2 target qubits; got {targets}")
            qc.swap(targets[0], targets[1])

        elif gate_name in ("CCX", "TOFFOLI"):
            if len(controls) == 2 and len(targets) == 1:
                qc.ccx(controls[0], controls[1], targets[0])
            elif len(targets) == 3:
                qc.ccx(targets[0], targets[1], targets[2])
            else:
                raise CircuitValidationError(
                    f"CCX/Toffoli requires 2 controls and 1 target; received controls={controls}, targets={targets}."
                )

        elif gate_name == "MEASURE":
            if not with_measurements:
                # Measurement will be applied automatically if requested
                pass
            else:
                for q in targets:
                    qc.measure(q, q)

        else:
            raise CircuitValidationError(f"Unsupported quantum gate '{gate_name}' at step {step_idx}.")

    if with_measurements and not any(op.get("gate", "").upper() == "MEASURE" for op in operations):
        qc.measure_all()

    return qc


def _extract_param(params: Any, default: float = 0.0) -> float:
    """Extract floating-point angle parameter from scalar, dict, or list."""
    if params is None:
        return float(default)
    if isinstance(params, (int, float)):
        return float(params)
    if isinstance(params, dict):
        for key in ("theta", "phi", "lambda", "angle", "val", "value"):
            if key in params:
                return float(params[key])
        if params:
            return float(next(iter(params.values())))
    if isinstance(params, (list, tuple)) and len(params) > 0:
        return float(params[0])
    return float(default)


def get_circuit_metrics(qc: QuantumCircuit) -> Dict[str, Any]:
    """Calculate depth, operation counts, and gate summary for a QuantumCircuit."""
    ops_dict = dict(qc.count_ops())
    return {
        "num_qubits": qc.num_qubits,
        "num_clbits": qc.num_clbits,
        "circuit_depth": qc.depth(),
        "total_gate_count": len(qc.data),
        "ops_breakdown": ops_dict,
        "is_entangled": "cx" in ops_dict or "cz" in ops_dict or "swap" in ops_dict or "ccx" in ops_dict,
    }

