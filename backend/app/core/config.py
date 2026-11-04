"""
Core application configuration for Quantum Estate X.

Uses Pydantic BaseSettings for environment-driven configuration
with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Project Metadata ──────────────────────────────────────────────
    APP_NAME: str = "Quantum Estate X"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Quantum-optimized land portfolio selection for Pune real estate "
        "development using QAOA-based QUBO solvers with classical benchmarking."
    )
    DEBUG: bool = True

    # ── Server ────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # ── Quantum Defaults ──────────────────────────────────────────────
    QAOA_DEFAULT_P: int = 2
    QAOA_DEFAULT_SHOTS: int = 4096
    QAOA_MAX_QUBITS: int = 20

    # ── Budget Defaults (₹ Crore) ─────────────────────────────────────
    DEFAULT_BUDGET_CRORE: float = 40.0

    model_config = {
        "env_prefix": "QEX_",
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
