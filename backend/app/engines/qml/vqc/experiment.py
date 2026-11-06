"""
experiment.py - Experiment Tracking & Registry for VQC Runs.

Persists completed training sessions and comparative benchmarks with timestamps,
hyperparameters, evaluation metrics, and convergence histories.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid
from datetime import datetime, timezone


@dataclass
class VQCExperimentRecord:
    experiment_id: str
    created_at: str
    dataset_name: str
    provenance_tier: str
    model_config: Dict[str, Any]
    training_metrics: Dict[str, Any]
    evaluation_metrics: Dict[str, Any]
    history: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "created_at": self.created_at,
            "dataset_name": self.dataset_name,
            "provenance_tier": self.provenance_tier,
            "model_config": self.model_config,
            "training_metrics": self.training_metrics,
            "evaluation_metrics": self.evaluation_metrics,
            "history": self.history,
            "tags": self.tags,
        }


class VQCExperimentRegistry:
    """Thread-safe in-memory experiment history store."""

    _STORE: Dict[str, VQCExperimentRecord] = {}

    @classmethod
    def save(
        cls,
        dataset_name: str,
        provenance_tier: str,
        model_config: Dict[str, Any],
        training_metrics: Dict[str, Any],
        evaluation_metrics: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        exp_id = f"vqc_exp_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        record = VQCExperimentRecord(
            experiment_id=exp_id,
            created_at=now,
            dataset_name=dataset_name,
            provenance_tier=provenance_tier,
            model_config=model_config,
            training_metrics=training_metrics,
            evaluation_metrics=evaluation_metrics,
            history=history or [],
            tags=tags or ["vqc", "phase_05_2"],
        )
        cls._STORE[exp_id] = record
        return exp_id

    @classmethod
    def get(cls, experiment_id: str) -> Optional[Dict[str, Any]]:
        record = cls._STORE.get(experiment_id)
        return record.to_dict() if record else None

    @classmethod
    def list_all(cls, limit: int = 25) -> List[Dict[str, Any]]:
        records = sorted(
            cls._STORE.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return [r.to_dict() for r in records[:limit]]

    @classmethod
    def clear(cls) -> None:
        cls._STORE.clear()
