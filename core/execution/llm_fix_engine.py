from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from core.memory.evolution_memory import recall_import_fix, record_import_fix
from core.memory.graph_weight_engine import reinforce_edge, get_heaviest_neighbors
from core.utils.repo_similarity_bridge import blended_similarity


REPO_ROOT = Path(".")


FORBIDDEN_MODULES = {
    "os",
    "sys",
    "re",
    "difflib",
    "json",
    "math",
    "typing",
    "pathlib",
    "subprocess",
    "datetime",
    "collections",
    "shutil",
    "asyncio",
    "functools",
    "itertools",
    "traceback",
    "tokenize",
    "linecache",
    "urllib",
    "argparse",
}


def is_forbidden_module(module: str) -> bool:
    module = str(module or "").strip()
    if not module:
        return True
    if module in FORBIDDEN_MODULES:
        return True
    return any(module.startswith(name + ".") for name in FORBIDDEN_MODULES)


def is_alias_import(line: str) -> bool:
    return " as " in str(line or "")


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def similarity(a: str, b: str) -> float:
    return blended_similarity(normalize_token(a), normalize_token(b))


def module_to_py_path(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")).with_suffix(".py")


def module_to_package_init(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")) / "__init__.py"


def module_exists(module: str) -> bool:
    if is_forbidden_module(module):
        return False
    return module_to_py_path(module).exists() or module_to_package_init(module).exists()


def path_to_module(path: Path) -> str:
    if path.name == "__init__.py":
        rel = path.parent.relative_to(REPO_ROOT)
    else:
        rel = path.relative_to(REPO_ROOT).with_suffix("")
    return ".".join(rel.parts)


def file_path_to_module(path: str) -> str:
    p = Path(path)
    if p.suffix == ".py":
        return ".".join(p.with_suffix("").parts)
    return ".".join(p.parts)


def list_repo_modules() -> List[str]:
    modules: List[str] = []
    for path in REPO_ROOT.rglob("*.py"):
        if ".git" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            mod = path_to_module(path)
            if not is_forbidden_module(mod):
                modules.append(mod)
        except Exception:
            continue
    return sorted(set(modules))


def extract_neighbor_modules(file_content: str) -> List[str]:
    found: List[str] = []

    for raw in str(file_content or "").splitlines():
        line = raw.strip()

        if line.startswith("from ") and " import " in line:
            parts = line.split()
            if len(parts) >= 4:
                mod = parts[1].strip()
                if mod and not mod.startswith(".") and not is_forbidden_module(mod):
                    found.append(mod)

        elif line.startswith("import "):
            payload = line.replace("import ", "", 1).strip()
            if payload and "," not in payload and not payload.startswith(".") and not is_forbidden_module(payload):
                found.append(payload)

    return list(dict.fromkeys(found))


def get_file_namespace(path: str) -> List[str]:
    p = Path(path)
    parent = p.parent
    parts = [x for x in parent.parts if x not in {".", ""}]
    out: List[str] = []

    if parts:
        for i in range(len(parts), 0, -1):
            out.append(".".join(parts[:i]))

    return out


def find_memory_fix(module: str, symbol: str, current_file_path: str = "") -> Optional[Dict[str, Any]]:
    module = str(module or "").strip().strip(".")
    symbol = str(symbol or "").strip()

    if not module or is_forbidden_module(module):
        return None

    remembered = recall_import_fix(
        problem_type="broken_import_group",
        source_module=module,
        file_path=current_file_path,
    )

    if not remembered and module.startswith("core."):
        remembered = recall_import_fix(
            problem_type="broken_import_group",
            source_module=module.split("core.", 1)[-1],
            file_path="",
        )

    if not remembered:
        return None

    resolved = str(remembered.get("resolved_module", "")).strip()
    remembered_symbol = str(remembered.get("symbol", "")).strip()
    remembered_source = str(remembered.get("source_module", "")).strip().strip(".")

    if not resolved or is_forbidden_module(resolved):
        return None

    module_ok = (
        module == remembered_source
        or module.endswith(remembered_source)
        or remembered_source.endswith(module)
    )
    if not module_ok:
        return None

    if symbol and remembered_symbol and symbol != remembered_symbol:
        return None

    if module_exists(resolved):
        return remembered

    return None


def exact_or_package_match(module: str) -> Optional[str]:
    module = str(module or "").strip()
    if not module or is_forbidden_module(module):
        return None
    if module_exists(module):
        return module
    return None


def orbit_candidates(module: str, file_path: str, neighbor_modules: List[str]) -> List[str]:
    if is_forbidden_module(module):
        return []

    tail = module.split(".")[-1]
    candidates: List[str] = []

    for ns in get_file_namespace(file_path):
        candidates.append(f"{ns}.{module}")
        candidates.append(f"{ns}.{tail}")

    for neighbor in neighbor_modules:
        base = neighbor.rsplit(".", 1)[0] if "." in neighbor else neighbor
        candidates.append(f"{base}.{tail}")
        if "." in module:
            candidates.append(f"{base}.{module}")

    common_roots = [
        "core",
        "core.execution",
        "core.analysis",
        "core.validation",
        "core.memory",
        "core.policy",
        "core.field",
        "app",
        "app.orchestration",
        "runtime_experimental",
        "bridges",
    ]

    for root in common_roots:
        candidates.append(f"{root}.{tail}")
        candidates.append(f"{root}.{module}")

    out: List[str] = []
    seen = set()

    for item in candidates:
        item = item.strip(".")
        if not item or item in seen or is_forbidden_module(item):
            continue
        seen.add(item)
        out.append(item)

    return out


def fuzzy_find_module(
    module: str,
    repo_modules: List[str],
    file_path: str,
    neighbor_modules: List[str],
) -> Optional[str]:
    if is_forbidden_module(module):
        return None

    tail = module.split(".")[-1]
    exact_tail_matches = [m for m in repo_modules if m.split(".")[-1] == tail]
    if len(exact_tail_matches) == 1:
        return exact_tail_matches[0]

    preferred_prefixes = get_file_namespace(file_path)
    neighbor_prefixes: List[str] = []

    for nm in neighbor_modules:
        if "." in nm:
            neighbor_prefixes.append(nm.rsplit(".", 1)[0])

    weighted: List[Tuple[float, str]] = []

    for candidate in repo_modules:
        score = similarity(module, candidate)

        if candidate.split(".")[-1] == tail:
            score += 0.20

        for pref in preferred_prefixes:
            if candidate.startswith(pref + "."):
                score += 0.10
                break

        for pref in neighbor_prefixes:
            if candidate.startswith(pref + "."):
                score += 0.07
                break

        if candidate.startswith(("core.", "app.", "runtime_experimental.", "bridges.")):
            score += 0.03

        weighted.append((score, candidate))

    weighted.sort(reverse=True, key=lambda x: x[0])

    if not weighted:
        return None

    best_score, best = weighted[0]
    if best_score >= 0.72:
        return best

    return None


def find_repo_module(module: str, current_file_path: str = "", file_content: str = "") -> Optional[str]:
    module = str(module).strip()
    if not module or is_forbidden_module(module):
        return None

    exact = exact_or_package_match(module)
    if exact:
        return exact

    remembered = recall_import_fix(
        problem_type="broken_import_group",
        source_module=module,
        file_path=current_file_path,
    )
    if remembered:
        resolved = str(remembered.get("resolved_module", "")).strip()
        if resolved and not is_forbidden_module(resolved) and module_exists(resolved):
            return resolved

    current_module = file_path_to_module(current_file_path) if current_file_path else ""
    if current_module:
        heavy_neighbors = get_heaviest_neighbors(current_module, limit=5)
        tail = module.split(".")[-1]

        for heavy in heavy_neighbors:
            if is_forbidden_module(heavy):
                continue
            if heavy == module and module_exists(heavy):
                return heavy
            if heavy.split(".")[-1] == tail and module_exists(heavy):
                return heavy

    neighbor_modules = extract_neighbor_modules(file_content) if file_content else []

    for candidate in orbit_candidates(module, current_file_path, neighbor_modules):
        if module_exists(candidate):
            return candidate

    repo_modules = list_repo_modules()
    return fuzzy_find_module(module, repo_modules, current_file_path, neighbor_modules)


def try_fix_from_import(
    line: str,
    current_file_path: str,
    file_content: str,
) -> Tuple[str, Optional[Tuple[str, str, str, str]]]:
    stripped = line.strip()

    if is_alias_import(line):
        return line, None

    if not (stripped.startswith("from ") and " import " in stripped):
        return line, None

    parts = stripped.split()
    if len(parts) < 4:
        return line, None

    module = parts[1]
    imported_name = parts[3].strip()
    if imported_name == "*":
        imported_name = ""

    if module.startswith(".") or is_forbidden_module(module):
        return line, None

    if module_exists(module):
        return line, None

    memory_fix = find_memory_fix(module, imported_name, current_file_path=current_file_path)
    if memory_fix:
        resolved_module = str(memory_fix.get("resolved_module", "")).strip()
        if resolved_module and not is_forbidden_module(resolved_module):
            return (
                line.replace(f"from {module} import", f"from {resolved_module} import", 1),
                (module, resolved_module, imported_name, "memory_fast_path"),
            )

    repaired = find_repo_module(module, current_file_path=current_file_path, file_content=file_content)
    if repaired and repaired != module:
        return (
            line.replace(f"from {module} import", f"from {repaired} import", 1),
            (module, repaired, imported_name, "fuzzy_or_graph_fix"),
        )

    return line, None


def try_fix_plain_import(
    line: str,
    current_file_path: str,
    file_content: str,
) -> Tuple[str, Optional[Tuple[str, str, str, str]]]:
    stripped = line.strip()

    if is_alias_import(line):
        return line, None

    if not stripped.startswith("import "):
        return line, None

    if "," in stripped:
        return line, None

    module = stripped.replace("import ", "", 1).strip()

    if not module or module.startswith(".") or is_forbidden_module(module):
        return line, None

    if module_exists(module):
        return line, None

    repaired = find_repo_module(module, current_file_path=current_file_path, file_content=file_content)
    if repaired and repaired != module:
        return (
            line.replace(f"import {module}", f"import {repaired}", 1),
            (module, repaired, "", "fuzzy_or_graph_fix"),
        )

    return line, None

def build_prompt(task: Dict[str, Any], original_content: str, path: str) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip()
    return f"""Task type: {problem}
Target file: {path}

Allowed actions:
- fix obviously broken imports
- preserve unrelated code
- prefer valid in-repo module paths
- keep relative imports intact

Forbidden actions:
- create stdlib shadow files
- delete unrelated logic
- rename public APIs
- rewrite the whole file without need

Return only corrected file content.
"""


def request_fix(
    prompt: str,
    original_content: str,
    current_file_path: str,
) -> Tuple[str, List[Tuple[str, str, str, str]]]:
    lines = original_content.splitlines()
    fixed: List[str] = []
    learned_pairs: List[Tuple[str, str, str, str]] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("from ") and " import " in stripped:
            new_line, pair = try_fix_from_import(line, current_file_path, original_content)
            fixed.append(new_line)
            if pair:
                learned_pairs.append(pair)
            continue

        if stripped.startswith("import "):
            new_line, pair = try_fix_plain_import(line, current_file_path, original_content)
            fixed.append(new_line)
            if pair:
                learned_pairs.append(pair)
            continue

        fixed.append(line)

    result = "\n".join(fixed)
    if original_content.endswith("\n"):
        result += "\n"

    return result, learned_pairs


def make_backup(path: str) -> str:
    backup_path = f"{path}.bak"
    shutil.copy2(path, backup_path)
    return backup_path


def restore_backup(path: str, backup_path: str) -> bool:
    try:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, path)
            return True
        return False
    except Exception:
        return False


def cleanup_backup(backup_path: str) -> None:
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
    except Exception:
        pass


def apply_llm_fix(task: Dict[str, Any], path: str) -> Dict[str, Any]:
    path = str(path).strip()
    if not path or not os.path.exists(path):
        return {
            "ok": False,
            "reason": "target_file_missing",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    try:
        original = Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return {
            "ok": False,
            "reason": f"read_failed:{e}",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    prompt = build_prompt(task, original, path)
    fixed, learned_pairs = request_fix(prompt, original, path)

    if not isinstance(fixed, str) or not fixed.strip():
        return {
            "ok": False,
            "reason": "empty_result",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    if fixed == original:
        return {
            "ok": True,
            "reason": "no_change",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    try:
        backup_path = make_backup(path)
        Path(path).write_text(fixed, encoding="utf-8")
    except Exception as e:
        return {
            "ok": False,
            "reason": f"write_failed:{e}",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    recorded = []
    current_module = file_path_to_module(path)

    for source_module, resolved_module, symbol, kind in learned_pairs:
        info = record_import_fix(
            problem_type="broken_import_group",
            source_module=source_module,
            resolved_module=resolved_module,
            file_path=path,
            symbol=symbol,
            kind=kind,
            success=True,
        )
        recorded.append(info)

        if resolved_module and not is_forbidden_module(resolved_module):
            reinforce_edge(current_module, resolved_module, weight_delta=1)

    return {
        "ok": True,
        "reason": "llm_fix_applied",
        "changed_files": [path],
        "backup_files": [backup_path],
        "learned_rules": recorded,
    }


def apply_llm_fix_multi(task: Dict[str, Any], paths: List[str]) -> Dict[str, Any]:
    unique_paths: List[str] = []
    seen = set()

    for p in paths:
        sp = str(p).strip()
        if not sp or sp in seen:
            continue
        seen.add(sp)
        unique_paths.append(sp)

    if not unique_paths:
        return {
            "ok": False,
            "reason": "no_targets",
            "changed_files": [],
            "backup_files": [],
            "results": [],
        }

    changed_files: List[str] = []
    backup_files: List[str] = []
    results: List[Dict[str, Any]] = []
    any_ok = False

    for path in unique_paths[:3]:
        result = apply_llm_fix(task, path)
        results.append({"path": path, **result})

        if result.get("ok"):
            any_ok = True

        for changed in result.get("changed_files", []):
            if changed not in changed_files:
                changed_files.append(changed)

        for backup in result.get("backup_files", []):
            if backup not in backup_files:
                backup_files.append(backup)

    return {
        "ok": any_ok,
        "reason": "llm_multi_fix_applied" if any_ok else "llm_multi_fix_failed",
        "changed_files": changed_files,
        "backup_files": backup_files,
        "results": results,
    }


def rollback_changed_files(changed_files: List[str]) -> Dict[str, Any]:
    restored: List[str] = []
    missing_backups: List[str] = []
    failed: List[Dict[str, str]] = []

    for path in changed_files:
        backup = f"{path}.bak"
        if not os.path.exists(backup):
            missing_backups.append(path)
            continue

        try:
            shutil.copy2(backup, path)
            restored.append(path)
        except Exception as e:
            failed.append({"path": path, "reason": str(e)})

    return {
        "ok": len(failed) == 0,
        "restored": restored,
        "missing_backups": missing_backups,
        "failed": failed,
    }


def finalize_backups(changed_files: List[str]) -> Dict[str, Any]:
    removed: List[str] = []
    failed: List[Dict[str, str]] = []

    for path in changed_files:
        backup = f"{path}.bak"
        if not os.path.exists(backup):
            continue

        try:
            os.remove(backup)
            removed.append(backup)
        except Exception as e:
            failed.append({"path": backup, "reason": str(e)})

    return {
        "ok": len(failed) == 0,
        "removed": removed,
        "failed": failed,
    }


if __name__ == "__main__":
    demo_task = {
        "priority": "high",
        "payload": {
            "problem": "broken_import_group",
            "paths": ["core/execution/llm_fix_engine.py"],
            "has_shadow_backup": True,
        },
    }
    print(apply_llm_fix_multi(demo_task, ["core/execution/llm_fix_engine.py"]))

# live_tick_event
