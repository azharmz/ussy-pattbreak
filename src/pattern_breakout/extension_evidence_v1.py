"""Extension evidence envelope for Pattern Breakout.

This contract deliberately does not implement Weinstein or Minervini/VCP
methodology.  It defines how independently source-locked extension engines may
attach point-in-time evidence to a frozen O'Neil structural observation without
changing Core v1 eligibility or lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Mapping, Optional

EXTENSION_CONTRACT_VERSION = "pattern-breakout-extension-evidence-v1"


class ExtensionType(str, Enum):
    WEINSTEIN_V1 = "WEINSTEIN_V1"
    MINERVINI_VCP_V1 = "MINERVINI_VCP_V1"


class EvidenceState(str, Enum):
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    NOT_DETECTED = "NOT_DETECTED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass(frozen=True)
class CoreOpportunityIdentity:
    """Frozen structural identity plus the exact observation being enriched."""

    security_id: str
    assessment_id: str
    base_id: str
    lineage_id: str
    as_of_date: date
    pattern_type: str
    pivot_level: float

    def validate(self) -> None:
        for name in ("security_id", "assessment_id", "base_id", "lineage_id", "pattern_type"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if self.pivot_level <= 0:
            raise ValueError("pivot_level must be positive")


@dataclass(frozen=True)
class ExtensionEvidence:
    opportunity: CoreOpportunityIdentity
    extension_type: ExtensionType
    extension_version: str
    evidence_state: EvidenceState
    payload: Mapping[str, Any]
    source_hash: str
    methodology_lock: str
    contract_version: str = EXTENSION_CONTRACT_VERSION

    def validate(self) -> None:
        self.opportunity.validate()
        if not self.extension_version:
            raise ValueError("extension_version is required")
        if not self.methodology_lock:
            raise ValueError("methodology_lock is required")
        if not self.source_hash.startswith("sha256:") or len(self.source_hash) != 71:
            raise ValueError("source_hash must be canonical sha256:<64 hex>")
        try:
            int(self.source_hash[7:], 16)
        except ValueError as exc:
            raise ValueError("source_hash must contain hexadecimal SHA-256") from exc


def attach_extension_evidence(
    *,
    opportunity: CoreOpportunityIdentity,
    extension_type: ExtensionType,
    extension_version: str,
    evidence_state: EvidenceState,
    payload: Optional[Mapping[str, Any]],
    source_hash: str,
    methodology_lock: str,
) -> ExtensionEvidence:
    """Create validated evidence without changing any Core v1 state."""
    evidence = ExtensionEvidence(
        opportunity=opportunity,
        extension_type=extension_type,
        extension_version=extension_version,
        evidence_state=evidence_state,
        payload=dict(payload or {}),
        source_hash=source_hash,
        methodology_lock=methodology_lock,
    )
    evidence.validate()
    return evidence
