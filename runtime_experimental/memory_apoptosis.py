from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_BIAS_PATH = "memory/field_intent_priority_bias.json"
DEFAULT_MEMORY_PATH = "memory/field_intent_memory.jsonl"
DEFAULT_DECAYED_PATH = "memory/field_intent_priority_bias_decayed.json"
DEFAULT_REPORT_PATH = "reports/d65_apoptosis_decay_report.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, dict):
                out.append(item)
        except Exception:
            continue
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _priority_rank(priority: Any) -> int:
    p = str(priority or "").strip().lower()
    return {"critical": 4, "high": 3, "normal": 2, "medium": 2, "low": 1}.get(p, 2)


def _rank_priority(rank: int) -> str:
    if rank >= 4:
        return "critical"
    if rank == 3:
        return "high"
    if rank <= 1:
        return "low"
    return "normal"


def _norm_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(":", "")


def _extract_resonance_vector(item: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(item.get("resonance_vector"), dict):
        return item["resonance_vector"]
    payload = item.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("resonance_vector"), dict):
        return payload["resonance_vector"]
    raw = item.get("raw_payload")
    if isinstance(raw, dict) and isinstance(raw.get("resonance_vector"), dict):
        return raw["resonance_vector"]
    return {}


def _extract_memory_key(item: Dict[str, Any]) -> str:
    rv = _extract_resonance_vector(item)
    sources = [
        item,
        item.get("payload") if isinstance(item.get("payload"), dict) else {},
        item.get("raw_payload") if isinstance(item.get("raw_payload"), dict) else {},
        rv,
    ]
    for source in sources:
        if isinstance(source, dict):
            for key in ("bias_key", "memory_key", "meta_key", "key"):
                if source.get(key):
                    return str(source.get(key)).strip()
    return ""


def _extract_phase_error(item: Dict[str, Any]) -> float:
    rv = _extract_resonance_vector(item)
    return _safe_float(rv.get("phase_error", item.get("phase_error", 0.0)), 0.0)


def _extract_jitter(item: Dict[str, Any]) -> float:
    rv = _extract_resonance_vector(item)
    return _safe_float(rv.get("jitter", item.get("jitter", 0.0)), 0.0)


def _get_biases(store: Any) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], str]:
    if isinstance(store, dict) and isinstance(store.get("biases"), dict):
        biases: Dict[str, Dict[str, Any]] = {}
        for key, value in store["biases"].items():
            if isinstance(value, dict):
                item = deepcopy(value)
                item.setdefault("bias_key", str(key))
                biases[str(key)] = item
        return biases, deepcopy(store), "store"

    if isinstance(store, dict) and (
        "bias_key" in store
        or "memory_key" in store
        or "priority_boost_points" in store
        or "boost_points" in store
    ):
        key = str(store.get("bias_key") or store.get("memory_key") or store.get("key") or "default_bias")
        item = deepcopy(store)
        item.setdefault("bias_key", key)
        return {key: item}, {"state": "FIELD_INTENT_PRIORITY_BIAS_STORE", "biases": {key: item}}, "single"

    return {}, {"state": "FIELD_INTENT_PRIORITY_BIAS_STORE", "biases": {}}, "empty"


def _memory_key_matches_bias(memory_key: str, bias_key: str) -> bool:
    mk = _norm_key(memory_key)
    bk = _norm_key(bias_key)
    if not mk or not bk:
        return False
    return mk == bk or mk in bk or bk in mk


def _recurrence_for_bias(bias_key: str, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = 0
    phase_error_max = 0.0
    jitter_max = 0.0
    for atom in atoms:
        mk = _extract_memory_key(atom)
        if _memory_key_matches_bias(mk, bias_key):
            count += 1
            phase_error_max = max(phase_error_max, _extract_phase_error(atom))
            jitter_max = max(jitter_max, _extract_jitter(atom))
    return {"count": count, "phase_error_max": round(phase_error_max, 4), "jitter_max": round(jitter_max, 4)}


def _decay_bias_item(
    key: str,
    item: Dict[str, Any],
    recurrence: Dict[str, Any],
    decay_points: int,
    reinforce_points: int,
    min_boost: int,
    max_boost: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    old = deepcopy(item)
    old_boost = _safe_int(old.get("priority_boost_points", old.get("boost_points", old.get("boost", 0))), 0)
    old_priority = str(old.get("recommended_priority") or old.get("priority") or "normal")
    old_rank = _priority_rank(old_priority)

    recurrence_count = _safe_int(recurrence.get("count"), 0)
    phase_error_max = _safe_float(recurrence.get("phase_error_max"), 0.0)

    still_active = recurrence_count > 0 and phase_error_max >= 0.12
    repeated = recurrence_count > 1

    if still_active:
        new_boost = min(max_boost, old_boost + (reinforce_points if repeated else 0))
        new_rank = min(4, old_rank + (1 if repeated and old_rank < 4 else 0))
        action = "preserve_or_reinforce"
        reason = "bias still matches active memory recurrence"
    else:
        new_boost = max(min_boost, old_boost - decay_points)
        new_rank = max(1, old_rank - (1 if old_boost <= decay_points else 0))
        action = "decay"
        reason = "bias did not match active recurring memory"

    new_item = deepcopy(old)
    new_item["bias_key"] = key
    new_item["priority_boost_points_before"] = old_boost
    new_item["priority_boost_points"] = new_boost
    new_item["recommended_priority_before_decay"] = old_priority
    new_item["recommended_priority"] = _rank_priority(new_rank)
    new_item["apoptosis"] = {
        "action": action,
        "reason": reason,
        "recurrence_count": recurrence_count,
        "phase_error_max": phase_error_max,
        "jitter_max": _safe_float(recurrence.get("jitter_max"), 0.0),
        "decay_points": decay_points,
        "reinforce_points": reinforce_points,
        "old_boost": old_boost,
        "new_boost": new_boost,
        "old_priority": old_priority,
        "new_priority": new_item["recommended_priority"],
        "updated_at": _now(),
    }

    delta = {
        "bias_key": key,
        "action": action,
        "reason": reason,
        "old_boost": old_boost,
        "new_boost": new_boost,
        "old_priority": old_priority,
        "new_priority": new_item["recommended_priority"],
        "recurrence_count": recurrence_count,
        "phase_error_max": phase_error_max,
    }
    return new_item, delta


def run_memory_apoptosis(
    bias_path: str = DEFAULT_BIAS_PATH,
    memory_path: str = DEFAULT_MEMORY_PATH,
    output_path: str = DEFAULT_DECAYED_PATH,
    report_path: str = DEFAULT_REPORT_PATH,
    decay_points: int = 10,
    reinforce_points: int = 5,
    min_boost: int = 0,
    max_boost: int = 50,
) -> Dict[str, Any]:
    raw_store = _read_json(bias_path, default={})
    atoms = _read_jsonl(memory_path)
    biases, outer_store, shape = _get_biases(raw_store)

    errors: List[str] = []
    warnings: List[str] = []
    if not Path(bias_path).exists():
        warnings.append(f"bias_path missing: {bias_path}")
    if not Path(memory_path).exists():
        warnings.append(f"memory_path missing: {memory_path}")
    if not biases:
        warnings.append("no usable bias entries found")

    new_biases: Dict[str, Dict[str, Any]] = {}
    deltas: List[Dict[str, Any]] = []

    for key, item in biases.items():
        recurrence = _recurrence_for_bias(key, atoms)
        new_item, delta = _decay_bias_item(
            key=key,
            item=item,
            recurrence=recurrence,
            decay_points=decay_points,
            reinforce_points=reinforce_points,
            min_boost=min_boost,
            max_boost=max_boost,
        )
        new_biases[key] = new_item
        deltas.append(delta)

    decayed_store = deepcopy(outer_store)
    decayed_store["state"] = "FIELD_INTENT_PRIORITY_BIAS_DECAYED_STORE"
    decayed_store["result"] = "APOPTOSIS_DECAY_CANDIDATE_CREATED"
    decayed_store["created_at"] = _now()
    decayed_store["source_bias_path"] = str(bias_path)
    decayed_store["source_memory_path"] = str(memory_path)
    decayed_store["canonical_overwritten"] = False
    decayed_store["biases"] = new_biases
    decayed_store["apoptosis_summary"] = {
        "bias_entries_seen": len(biases),
        "memory_atoms_seen": len(atoms),
        "decayed_count": len([d for d in deltas if d["action"] == "decay"]),
        "preserved_or_reinforced_count": len([d for d in deltas if d["action"] == "preserve_or_reinforce"]),
        "decay_points": decay_points,
        "reinforce_points": reinforce_points,
        "min_boost": min_boost,
        "max_boost": max_boost,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(decayed_store, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "state": "D65_MEMORY_APOPTOSIS_DECAY",
        "result": "APOPTOSIS_DECAY_REPORT_CREATED",
        "route": "FIELD_INTENT_MEMORY_APOPTOSIS",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "bias_path": str(bias_path),
        "memory_path": str(memory_path),
        "output_path": str(output_path),
        "report_path": str(report_path),
        "canonical_overwritten": False,
        "store_shape": shape,
        "deltas": deltas,
        "summary": decayed_store["apoptosis_summary"],
        "validation": {"ok": len(errors) == 0, "errors": errors, "warnings": warnings},
        "success_condition": {
            "decayed_candidate_created": True,
            "canonical_memory_preserved": True,
            "invalid_memory_does_not_crash": True,
            "next_step": "D66 may review this candidate before D64 guarded apply to canonical memory.",
        },
    }

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run_memory_apoptosis(), ensure_ascii=False, indent=2))
