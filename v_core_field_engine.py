# v_core_field_engine.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================
# STATE
# ============================================

@dataclass
class FieldVector:
    pressure: float = 0.0
    flow: float = 0.0
    structure: float = 0.0
    balance: float = 0.0
    law: float = 0.0
    future: float = 0.0


@dataclass
class FractalVision:
    radial_score: float = 0.0      # MAGE
    ring_score: float = 0.0        # TANK
    strike_score: float = 0.0      # ARCHER
    tension_score: float = 0.0     # HEALER
    symmetry_score: float = 0.0    # FLOWER / FIELD


@dataclass
class FieldState:
    task: Dict[str, Any]
    mode: str = "UNKNOWN"
    bindu_locked: bool = False

    field_vector: FieldVector = field(default_factory=FieldVector)
    vision: FractalVision = field(default_factory=FractalVision)

    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    target_paths: List[str] = field(default_factory=list)
    candidate_paths: List[str] = field(default_factory=list)

    issues: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    action_plan: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    history: List[str] = field(default_factory=list)


# ============================================
# BINDU
# ============================================

def bindu_lock(state: FieldState) -> FieldState:
    state.bindu_locked = True
    state.history.append("BINDU_LOCK")
    return state


# ============================================
# MODE DETECTOR
# ============================================

def detect_task_mode(state: FieldState) -> FieldState:
    problem = str(state.task.get("problem", "")).strip().lower()

    if problem in {"missing_init_group", "package_structure"}:
        state.mode = "STRUCTURAL_REPAIR"
    elif problem in {"broken_import_group", "structural_orphans_group", "missing_bridge_group"}:
        state.mode = "TOPOLOGY_REPAIR"
    elif problem in {"debug_prints_group", "todo_group", "pass_blocks_group"}:
        state.mode = "SURFACE_HYGIENE"
    else:
        state.mode = "GENERAL_REPAIR"

    state.history.append(f"MODE:{state.mode}")
    return state


# ============================================
# FLOWER FIELD CONSTRAINT
# ============================================

def flower_field_constraint(state: FieldState) -> FieldState:
    payload = state.task

    state.allowed_actions = list(payload.get("allowed_actions", []))
    state.forbidden_actions = list(payload.get("forbidden_actions", []))
    state.candidate_paths = list(payload.get("paths", []))

    # базовий коефіцієнт симетрії поля
    if state.mode == "STRUCTURAL_REPAIR":
        state.vision.symmetry_score = 0.92
    elif state.mode == "TOPOLOGY_REPAIR":
        state.vision.symmetry_score = 0.86
    else:
        state.vision.symmetry_score = 0.70

    state.history.append("FLOWER_FIELD_ACTIVE")
    return state


# ============================================
# MAGE: RADIAL SCAN
# бачить можливі координати
# ============================================

def mage_scan(state: FieldState) -> FieldState:
    paths = state.candidate_paths
    problem = str(state.task.get("problem", "")).strip().lower()

    radial_score = 0.0
    targets: List[str] = []

    for p in paths:
        p = str(p).strip().rstrip("/")
        if not p:
            continue

        if problem == "missing_init_group":
            if p.endswith(".py"):
                parent = p.rsplit("/", 1)[0] if "/" in p else "."
                targets.append(f"{parent}/__init__.py" if parent != "." else "__init__.py")
            else:
                targets.append(f"{p}/__init__.py")
            radial_score += 1.0

        elif problem == "package_structure":
            if not p.endswith(".py"):
                targets.append(f"{p}/__init__.py")
                radial_score += 0.8

        elif problem in {"broken_import_group", "structural_orphans_group", "missing_bridge_group"}:
            targets.append(p)
            radial_score += 0.6

        else:
            targets.append(p)
            radial_score += 0.3

    # unique
    seen = set()
    uniq_targets = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            uniq_targets.append(t)

    state.target_paths = uniq_targets
    state.vision.radial_score = round(radial_score, 3)
    state.history.append(f"MAGE_SCAN:{len(uniq_targets)}")
    return state


# ============================================
# TANK: RING FILTER
# стискає поле, залишає безпечні дії
# ============================================

def tank_filter(state: FieldState) -> FieldState:
    filtered: List[str] = []

    for path in state.target_paths:
        if "delete" in state.forbidden_actions:
            pass

        # захист від виходу за межі репо
        if path.startswith("/") or ".." in path:
            state.issues.append(f"UNSAFE_PATH:{path}")
            continue

        # для structural repair дозволяємо тільки __init__.py
        if state.mode == "STRUCTURAL_REPAIR":
            if not path.endswith("__init__.py"):
                state.issues.append(f"REJECT_NON_INIT:{path}")
                continue

        filtered.append(path)

    state.target_paths = filtered
    state.vision.ring_score = round(len(filtered) / max(1, len(state.candidate_paths)), 3)
    state.history.append(f"TANK_FILTER:{len(filtered)}")

    if not filtered:
        state.issues.append("NO_SAFE_TARGETS")

    return state


# ============================================
# ARCHER: STRIKE PLAN
# матеріалізація дії
# ============================================

def archer_plan(state: FieldState) -> FieldState:
    problem = str(state.task.get("problem", "")).strip().lower()

    if state.issues:
        state.history.append("ARCHER_SKIP_DUE_TO_ISSUES")
        return state

    if problem in {"missing_init_group", "package_structure"}:
        state.action_plan = {
            "action": "create_package_markers",
            "targets": state.target_paths,
            "content": '"""Auto-created package marker."""\n',
        }
        state.vision.strike_score = 0.95

    elif problem == "missing_bridge_group":
        state.action_plan = {
            "action": "create_bridge_placeholders",
            "targets": state.target_paths,
        }
        state.vision.strike_score = 0.75

    else:
        state.action_plan = {
            "action": "inspect_only",
            "targets": state.target_paths,
        }
        state.vision.strike_score = 0.40

    state.history.append(f"ARCHER_PLAN:{state.action_plan['action']}")
    return state


# ============================================
# BUILDER EXECUTION
# ============================================

def _safe_write(path: str, content: str) -> bool:
    try:
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        if parent:
            import os
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def archer_strike(state: FieldState) -> FieldState:
    plan = state.action_plan
    if not plan:
        state.issues.append("NO_ACTION_PLAN")
        state.history.append("ARCHER_NO_PLAN")
        return state

    action = plan.get("action")
    targets = list(plan.get("targets", []))

    if action == "create_package_markers":
        content = str(plan.get("content", '"""Auto-created package marker."""\n'))
        for target in targets:
            import os
            if not os.path.exists(target):
                ok = _safe_write(target, content)
                if ok:
                    state.changed_files.append(target)
                else:
                    state.issues.append(f"WRITE_FAIL:{target}")

    elif action == "inspect_only":
        pass

    else:
        state.issues.append(f"UNKNOWN_ACTION:{action}")

    state.history.append(f"ARCHER_STRIKE:{len(state.changed_files)}")
    return state


# ============================================
# HEALER: TENSION CHECK
# ============================================

def healer_check(state: FieldState) -> FieldState:
    import py_compile

    for path in state.changed_files:
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            state.validation_errors.append(f"{path}: {e}")

    state.vision.tension_score = round(len(state.validation_errors) / max(1, len(state.changed_files)), 3)

    if state.validation_errors:
        state.issues.append("VALIDATION_FAILED")
        state.history.append("HEALER_FAIL")
    else:
        state.history.append("HEALER_OK")

    return state


# ============================================
# HEALER: REROUTE
# ============================================

def healer_reroute(state: FieldState) -> FieldState:
    if not state.validation_errors:
        state.history.append("REROUTE_NOT_NEEDED")
        return state

    # поки що м'який reroute: просто фіксуємо збій
    state.result = {
        "ok": False,
        "reason": "validation_failed",
        "changed_files": state.changed_files,
        "validation_errors": state.validation_errors,
    }
    state.history.append("REROUTE_FAIL_LOCK")
    return state


# ============================================
# FINALIZE
# ============================================

def finalize(state: FieldState) -> FieldState:
    if state.result is None:
        if state.issues and "VALIDATION_FAILED" not in state.issues:
            state.result = {
                "ok": False,
                "reason": "field_blocked",
                "issues": state.issues,
                "changed_files": state.changed_files,
            }
        else:
            state.result = {
                "ok": True,
                "reason": "field_cycle_complete",
                "changed_files": state.changed_files,
                "issues": state.issues,
            }

    state.history.append("FINALIZE")
    return state


# ============================================
# MAIN PIPELINE
# ============================================

def run_field_cycle(task: Dict[str, Any]) -> FieldState:
    state = FieldState(task=task)

    state = bindu_lock(state)
    state = detect_task_mode(state)
    state = flower_field_constraint(state)

    state = mage_scan(state)
    state = tank_filter(state)

    state = archer_plan(state)
    state = archer_strike(state)

    state = healer_check(state)
    state = healer_reroute(state)

    state = finalize(state)
    return state


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    demo_task = {
        "problem": "missing_init_group",
        "paths": ["core", "tests", "runtime_experimental"],
        "allowed_actions": ["create_init_files"],
        "forbidden_actions": ["delete", "rewrite_unrelated_modules"],
    }

    s = run_field_cycle(demo_task)
    print("MODE:", s.mode)
    print("TARGETS:", s.target_paths)
    print("CHANGED:", s.changed_files)
    print("ISSUES:", s.issues)
    print("RESULT:", s.result)
    print("HISTORY:", s.history)
