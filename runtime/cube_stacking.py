from dataclasses import asdict
from typing import Dict

from core.cube_validator import CubeState


def compare_faces(a: float, b: float) -> float:
    """
    Face similarity in [0..1]
    1.0 = identical, 0.0 = maximally mismatched
    """
    diff = abs(a - b)
    return max(0.0, 1.0 - diff)


def stack_cubes(cube_a: CubeState, cube_b: CubeState) -> Dict[str, object]:
    """
    Evaluate whether two cubes can be stably stacked.
    """

    face_scores = {
        "pressure": compare_faces(cube_a.pressure, cube_b.pressure),
        "flow": compare_faces(cube_a.flow, cube_b.flow),
        "structure": compare_faces(cube_a.structure, cube_b.structure),
        "balance": compare_faces(cube_a.balance, cube_b.balance),
        "law": compare_faces(cube_a.law, cube_b.law),
        "future": compare_faces(cube_a.future, cube_b.future),
    }

    compatibility_score = sum(face_scores.values()) / len(face_scores)

    shadow_pressure = (
        (1.0 - face_scores["pressure"]) * 0.25 +
        (1.0 - face_scores["structure"]) * 0.25 +
        (1.0 - face_scores["balance"]) * 0.25 +
        (1.0 - face_scores["law"]) * 0.25
    )

    is_stackable = (
        compatibility_score >= 0.72 and
        shadow_pressure <= 0.25 and
        face_scores["law"] >= 0.75 and
        face_scores["structure"] >= 0.70
    )

    is_crystal_stack = (
        compatibility_score >= 0.86 and
        shadow_pressure <= 0.12 and
        min(face_scores.values()) >= 0.75
    )

    return {
        "cube_a": asdict(cube_a),
        "cube_b": asdict(cube_b),
        "face_scores": face_scores,
        "compatibility_score": round(compatibility_score, 3),
        "shadow_pressure": round(shadow_pressure, 3),
        "is_stackable": is_stackable,
        "is_crystal_stack": is_crystal_stack,
    }
