# -*- coding: utf-8 -*-
"""
runtime_experimental/phase_resync_policy.py

Guarded phase-resync helper generated from D51.

Purpose:
- reduce phase drift before memory/write/report stages
- preserve full D46 resonance payload
- never overwrite memory_key, orbital_mode, intent, or resonance_vector
"""

from __future__ import annotations

from typing import Any, Dict


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except Exception:
        return default


def compute_phase_resync(
    resonance_vector: Dict[str, Any],
    *,
    phase_error_after_max: float = 0.12,
    jitter_after_max: float = 0.08,
) -> Dict[str, Any]:
    original = dict(resonance_vector or {})

    phase_error_before = _num(original.get("phase_error"), 0.0)
    jitter_before = _num(original.get("jitter"), 0.0)

    phase_error_after = min(phase_error_before, phase_error_before * 0.35)
    jitter_after = min(jitter_before, jitter_before * 0.70)

    return {
        "ok": phase_error_after <= phase_error_after_max and jitter_after <= jitter_after_max,
        "memory_key": original.get("memory_key"),
        "orbital_mode": original.get("orbital_mode"),
        "phase_error_before": phase_error_before,
        "phase_error_after": phase_error_after,
        "jitter_before": jitter_before,
        "jitter_after": jitter_after,
        "phase_error_after_max": phase_error_after_max,
        "jitter_after_max": jitter_after_max,
        "preserved_resonance_vector": original,
    }
