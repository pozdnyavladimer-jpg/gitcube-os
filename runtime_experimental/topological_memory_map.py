from __future__ import annotations

import ast
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _json(path: str, default: Any) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _jsonl(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            pass
    return out


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _i(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return default


def _priority_weight(priority: Any) -> float:
    return {
        "critical": 1.0,
        "high": 0.75,
        "normal": 0.45,
        "medium": 0.45,
        "low": 0.2,
    }.get(str(priority or "").lower(), 0.25)


def _rv(obj: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(obj.get("resonance_vector"), dict):
        return obj["resonance_vector"]
    payload = obj.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("resonance_vector"), dict):
        return payload["resonance_vector"]
    raw = obj.get("raw_payload")
    if isinstance(raw, dict) and isinstance(raw.get("resonance_vector"), dict):
        return raw["resonance_vector"]
    return {}


def _memory_key(obj: Dict[str, Any]) -> str:
    rv = _rv(obj)
    sources = [obj, rv]
    if isinstance(obj.get("payload"), dict):
        sources.append(obj["payload"])
    for src in sources:
        for key in ("memory_key", "bias_key", "meta_key", "key"):
            if src.get(key):
                return str(src.get(key))
    return ""


def _targets(obj: Dict[str, Any]) -> List[str]:
    out: List[str] = []

    def add(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            p = _norm(value)
            if p:
                out.append(p)
        elif isinstance(value, list):
            for v in value:
                add(v)
        elif isinstance(value, dict):
            for k in ("path", "file", "target", "target_file", "target_path"):
                add(value.get(k))

    for k in ("target_files", "changed_files", "paths", "files", "candidate_target_files"):
        add(obj.get(k))
    if isinstance(obj.get("payload"), dict):
        for k in ("target_files", "changed_files", "paths", "files", "candidate_target_files"):
            add(obj["payload"].get(k))
    if isinstance(obj.get("execution"), dict):
        add(obj["execution"].get("changed_files"))

    seen: Set[str] = set()
    uniq: List[str] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _default_targets(memory_key: str) -> List[str]:
    key = str(memory_key or "").lower()
    if "d3_o6" in key or "phase_drift" in key or "phase" in key:
        return [
            "runtime_experimental/phase_resync_policy.py",
            "app/orchestration/task_dispatcher.py",
            "runtime_experimental/v_kernel_daemon.py",
        ]
    return []


def _bias_entries(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        biases = data.get("biases")
        if isinstance(biases, dict):
            out = []
            for key, value in biases.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("bias_key", key)
                    out.append(item)
            return out
        if "bias_key" in data or "priority_boost_points" in data or "boost_points" in data:
            return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _py_files(root: Path) -> List[Path]:
    skip = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
    files = []
    for p in root.rglob("*.py"):
        parts = set(p.relative_to(root).parts)
        if parts.intersection(skip):
            continue
        files.append(p)
    return sorted(files)


def _module_name(path: Path, root: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def _import_edges(root: Path) -> List[Dict[str, Any]]:
    py = _py_files(root)
    index = {_module_name(p, root): p.relative_to(root).as_posix() for p in py}
    edges = []
    for p in py:
        source = p.relative_to(root).as_posix()
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                target = ""
                while parts:
                    mod = ".".join(parts)
                    if mod in index:
                        target = index[mod]
                        break
                    parts.pop()
                if target:
                    edges.append({"from": source, "to": target, "type": "import", "weight": 1.0, "stress": 0.0})
    seen = set()
    uniq = []
    for e in edges:
        key = (e["from"], e["to"], e["type"])
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    return uniq


def _heat(score: float) -> str:
    if score >= 0.75:
        return "red"
    if score >= 0.45:
        return "amber"
    if score >= 0.2:
        return "blue"
    return "white"


def _move(path: str, score: float, protected: bool, boost: int, repeat: int) -> Dict[str, Any]:
    if protected and score >= 0.45:
        return {
            "recommendation": "do_not_expand_directly",
            "move_type": "TENUKI",
            "action": "create isolated policy/reviewer module and route through a narrow interface",
            "reason": "protected core has stress; direct expansion risks core mutation",
        }
    if score >= 0.75:
        return {
            "recommendation": "isolate_and_bypass",
            "move_type": "SABAKI",
            "action": "extract pressure into a new module, add tests, then decay old pressure",
            "reason": "high pain score indicates trauma accumulation",
        }
    if boost > 0 or repeat > 0:
        return {
            "recommendation": "monitor_and_decay",
            "move_type": "APOPTOSIS_WATCH",
            "action": "keep memory and run D65 decay if no recurrence",
            "reason": "memory exists but node is not overloaded",
        }
    return {
        "recommendation": "stable",
        "move_type": "HOLD_SHAPE",
        "action": "no direct action",
        "reason": "no significant pain signal",
    }


def build_topological_memory_map(
    root: str = ".",
    policy_path: str = "runtime_experimental/core_guard_policy.json",
    memory_path: str = "memory/field_intent_memory.jsonl",
    bias_path: str = "memory/field_intent_priority_bias.json",
    map_path: str = "reports/d67_topological_memory_map.json",
    report_path: str = "reports/d67_topological_memory_map_report.json",
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    policy = _json(policy_path, {})
    protected = {_norm(p) for p in policy.get("protected_files", []) if _norm(p)}
    atoms = _jsonl(memory_path)
    biases = _bias_entries(_json(bias_path, {}))

    node_paths: Set[str] = set(p.relative_to(root_path).as_posix() for p in _py_files(root_path))
    node_paths.update(protected)

    repeat = defaultdict(int)
    phase = defaultdict(float)
    prio = defaultdict(float)
    boost = defaultdict(int)
    memory_keys = defaultdict(set)
    bias_keys = defaultdict(set)

    for atom in atoms:
        key = _memory_key(atom)
        rv = _rv(atom)
        targets = _targets(atom) or _default_targets(key)
        for t in targets:
            node_paths.add(t)
            repeat[t] += 1
            phase[t] = max(phase[t], _f(rv.get("phase_error")))
            prio[t] = max(prio[t], _priority_weight(atom.get("priority")))
            if key:
                memory_keys[t].add(key)

    for b in biases:
        key = str(b.get("bias_key") or b.get("memory_key") or b.get("key") or "")
        targets = _targets(b) or _default_targets(key)
        points = _i(b.get("priority_boost_points", b.get("boost_points", b.get("boost", 0))))
        for t in targets:
            node_paths.add(t)
            boost[t] = max(boost[t], points)
            if key:
                bias_keys[t].add(key)

    edges = _import_edges(root_path)
    nodes = []
    moves = []

    for path in sorted(node_paths):
        is_core = path in protected
        phase_component = min(1.0, phase[path] / 0.40)
        bias_component = min(1.0, max(0, boost[path]) / 30.0)
        repeat_component = min(1.0, repeat[path] / 5.0)
        core_component = 0.15 if is_core and (phase_component or bias_component or repeat_component) else 0.0
        pain_score = round(min(1.0, 0.35 * phase_component + 0.30 * bias_component + 0.20 * repeat_component + 0.10 * prio[path] + core_component), 4)

        role = "core" if is_core else "module"
        if "dispatcher" in path:
            role = "router"
        elif "daemon" in path:
            role = "daemon"
        elif "policy" in path:
            role = "policy"
        elif "reviewer" in path or "guard" in path:
            role = "reviewer"
        elif path.startswith("tests/"):
            role = "test"
        elif path.startswith("memory/"):
            role = "memory"
        elif path.startswith("reports/"):
            role = "report"

        suggestion = _move(path, pain_score, is_core, boost[path], repeat[path])

        node = {
            "id": path,
            "type": "file",
            "role": role,
            "protected_core": is_core,
            "pain_score": pain_score,
            "heat": _heat(pain_score),
            "priority_bias": boost[path],
            "repeat_count": repeat[path],
            "phase_error": round(phase[path], 4),
            "memory_keys": sorted(memory_keys[path]),
            "bias_keys": sorted(bias_keys[path]),
            "recommendation": suggestion["recommendation"],
            "suggested_move": suggestion,
        }
        nodes.append(node)
        if suggestion["recommendation"] != "stable":
            moves.append({"target": path, "pain_score": pain_score, "protected_core": is_core, **suggestion})

    score_by_node = {n["id"]: n["pain_score"] for n in nodes}
    for edge in edges:
        stress = max(score_by_node.get(edge["from"], 0.0), score_by_node.get(edge["to"], 0.0))
        edge["stress"] = round(stress, 4)
        edge["weight"] = round(1.0 + stress, 4)

    moves.sort(key=lambda x: float(x["pain_score"]), reverse=True)
    tenuki = [m for m in moves if m["move_type"] == "TENUKI"]

    result = {
        "state": "D67_TOPOLOGICAL_MEMORY_MAP",
        "result": "TOPOLOGICAL_MEMORY_MAP_CREATED",
        "route": "FIELD_INTENT_TOPOLOGICAL_MEMORY_MAP",
        "ok": True,
        "created_at": _now(),
        "map_path": map_path,
        "summary": {
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "protected_core_count": len([n for n in nodes if n["protected_core"]]),
            "hot_nodes_count": len([n for n in nodes if n["pain_score"] >= 0.75]),
            "tenuki_count": len(tenuki),
            "suggested_moves_count": len(moves),
        },
        "legend": {
            "red": "high pain / trauma attractor",
            "amber": "medium stress / watch",
            "blue": "low stress / memory present",
            "white": "stable or no known pain",
            "TENUKI": "do not expand directly; create a healthy bypass",
            "SABAKI": "stabilize pressure through flexible shape",
            "APOPTOSIS_WATCH": "monitor and decay if no recurrence",
        },
        "core_axiom": "Do not repair trauma inside trauma. Route around it, validate it, remember it, then decay the old path.",
        "nodes": nodes,
        "edges": edges,
        "suggested_moves": moves,
        "tenuki_recommendations": tenuki,
        "raw_inputs": {
            "memory_atoms_seen": len(atoms),
            "bias_entries_seen": len(biases),
            "protected_files": sorted(protected),
        },
        "validation": {"ok": True, "errors": []},
        "success_condition": {
            "map_created": True,
            "machine_readable": True,
            "runtime_code_mutated": False,
            "next_step": "D68 may visualize this JSON or D64 may use it for safe mutation planning.",
        },
    }

    Path(map_path).parent.mkdir(parents=True, exist_ok=True)
    Path(map_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "state": "D67_TOPOLOGICAL_MEMORY_MAP_REPORT",
        "result": "D67_MAP_BUILD_COMPLETED",
        "route": "FIELD_INTENT_TOPOLOGICAL_MEMORY_MAP",
        "ok": True,
        "created_at": result["created_at"],
        "map_path": map_path,
        "report_path": report_path,
        "summary": result["summary"],
        "top_suggested_moves": moves[:5],
        "validation": {"ok": True, "errors": []},
        "success_condition": {
            "d67_map_created": True,
            "topology_extracted": True,
            "pain_scores_computed": True,
            "tenuki_recommendations_created": True,
            "runtime_code_mutated": False,
        },
    }

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    m = build_topological_memory_map()
    print(json.dumps(m["summary"], ensure_ascii=False, indent=2))
