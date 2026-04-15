from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MeshResult:
    ok: bool = True
    avg_tension: float = 0.0
    stabilization_score: float = 1.0
    hotspots: List[Dict[str, Any]] = field(default_factory=list)
    recommended_targets: List[str] = field(default_factory=list)


@dataclass
class FieldState:
    task: Dict[str, Any]
    mode: str = "UNKNOWN"
    bindu_locked: bool = False

    candidate_paths: List[str] = field(default_factory=list)
    target_paths: List[str] = field(default_factory=list)

    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)

    issues: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    mesh: Optional[MeshResult] = None
    action_plan: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    history: List[str] = field(default_factory=list)
