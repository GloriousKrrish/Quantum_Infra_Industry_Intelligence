"""
encoding_metrics.py - Quantum Circuit Resource & Complexity Analyzer.

Inspects actual Qiskit QuantumCircuit instances to compute:
  - Qubit count
  - Circuit depth
  - Total gate count
  - Single-qubit gate count
  - Two-qubit gate count
  - Multi-qubit gate count
  - Parameter count
  - Statevector dimension (2^n)
  - Detailed gate breakdown dictionary
  - Transpiled basis metrics (depth, gate count, CX count)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from qiskit import QuantumCircuit, transpile


@dataclass
class EncodingResourceMetrics:
    num_qubits: int
    circuit_depth: int
    total_gates: int
    single_qubit_gates: int
    two_qubit_gates: int
    multi_qubit_gates: int
    num_parameters: int
    statevector_dimension: int
    gate_breakdown: Dict[str, int] = field(default_factory=dict)
    transpiled_depth: Optional[int] = None
    transpiled_gate_count: Optional[int] = None
    transpiled_cx_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_qubits": self.num_qubits,
            "circuit_depth": self.circuit_depth,
            "total_gates": self.total_gates,
            "single_qubit_gates": self.single_qubit_gates,
            "two_qubit_gates": self.two_qubit_gates,
            "multi_qubit_gates": self.multi_qubit_gates,
            "num_parameters": self.num_parameters,
            "statevector_dimension": self.statevector_dimension,
            "gate_breakdown": self.gate_breakdown,
            "transpiled_depth": self.transpiled_depth,
            "transpiled_gate_count": self.transpiled_gate_count,
            "transpiled_cx_count": self.transpiled_cx_count,
        }


def calculate_circuit_metrics(
    circuit: QuantumCircuit,
    transpile_to_basis: bool = False,
) -> EncodingResourceMetrics:
    """
    Forensically analyzes an actual QuantumCircuit by inspecting its instruction data.
    Does NOT use hardcoded estimates.
    """
    num_qubits = circuit.num_qubits
    depth = circuit.depth()
    total_gates = len(circuit.data)

    single_q = 0
    two_q = 0
    multi_q = 0
    breakdown: Dict[str, int] = {}

    for inst in circuit.data:
        op = inst.operation
        q_count = op.num_qubits
        if q_count == 1:
            single_q += 1
        elif q_count == 2:
            two_q += 1
        else:
            multi_q += 1

        op_name = op.name
        breakdown[op_name] = breakdown.get(op_name, 0) + 1

    transpiled_depth = None
    transpiled_gates = None
    transpiled_cx = None

    if transpile_to_basis and num_qubits > 0:
        try:
            t_qc = transpile(circuit, basis_gates=["u", "cx"], optimization_level=1)
            transpiled_depth = t_qc.depth()
            transpiled_gates = len(t_qc.data)
            transpiled_cx = sum(1 for inst in t_qc.data if inst.operation.name == "cx")
        except Exception:
            # Transpilation may fail on unparameterized/custom instructions
            pass

    return EncodingResourceMetrics(
        num_qubits=num_qubits,
        circuit_depth=depth,
        total_gates=total_gates,
        single_qubit_gates=single_q,
        two_qubit_gates=two_q,
        multi_qubit_gates=multi_q,
        num_parameters=circuit.num_parameters,
        statevector_dimension=2 ** num_qubits,
        gate_breakdown=breakdown,
        transpiled_depth=transpiled_depth,
        transpiled_gate_count=transpiled_gates,
        transpiled_cx_count=transpiled_cx,
    )

