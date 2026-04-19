from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Tuple

from core.memory.evolution_memory import recall_import_fix, record_import_fix
from core.memory.graph_weight_engine import reinforce_edge, get_heaviest_neighbors
import difflib


REPO_ROOT = Path(".")


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
- comment import only if no valid repo replacement exists

Forbidden actions:
- delete unrelated logic
- rename public APIs
- rewrite the whole file without need

Return only corrected file content.
"""


def module_to_py_path(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")).with_suffix(".py")


def module_to_package_init(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")) / "__init__.py"


def module_exists(module: str) -> bool:
    return module_to_py_path(module).exists() or module_to_package_init(module).exists()


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def similarity(a: str, b: str) -> float:
    return difflib.difflib.SequenceMatcher(None, normalize_token(a), normalize_token(b)).ratio()


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
        if ".venv" in path.parts or "__pycache__" in path.parts or ".git" in path.parts:
            continue
        try:
            modules.append(path_to_module(path))
        except Exception:
            continue
    return sorted(set(modules))


def get_file_namespace(path: str) -> List[str]:
    p = Path(path)
    parent = p.parent
    parts = [x for x in parent.parts if x not in {".", ""}]
    namespaces: List[str] = []

    if parts:
        for i in range(len(parts), 0, -1):
            namespaces.append(".".join(parts[:i]))

    return namespaces


def extract_neighbor_modules(file_content: str) -> List[str]:
    found: List[str] = []

    for raw in file_content.splitlines():
        line = raw.strip()
        if line.startswith("from ") and " import " in line:
            parts = line.split()
            if len(parts) >= 4:
                mod = parts[1].strip()
                if mod and not mod.startswith("."):
                    found.append(mod)
        elif line.startswith("import "):
            payload = line.replace("import ", "", 1).strip()
            if payload and "," not in payload and not payload.startswith("."):
                found.append(payload)

    return list(dict.fromkeys(found))


def exact_or_package_match(module: str) -> Optional[str]:
    module = str(module).strip()
    if not module:
        return None
    if module_exists(module):
        return module
    return None


def orbit_candidates(module: str, file_path: str, neighbor_modules: List[str]) -> List[str]:
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

    unique: List[str] = []
    seen = set()
    for c in candidates:
        c = c.strip(".")
        if not c or c in seen:
            continue
        seen.add(c)
        unique.append(c)

    return unique


def fuzzy_find_module(module: str, repo_modules: List[str], file_path: str, neighbor_modules: List[str]) -> Optional[str]:
    tail = module.split(".")[-1]
    exact_tail_matches = [m for m in repo_modules if m.split(".")[-1] == tail]
    if len(exact_tail_matches) == 1:
        return exact_tail_matches[0]

    weighted: List[Tuple[float, str]] = []

    preferred_prefixes = get_file_namespace(file_path)
    neighbor_prefixes = []
    for nm in neighbor_modules:
        if "." in nm:
            neighbor_prefixes.append(nm.rsplit(".", 1)[0])

    for candidate in repo_modules:
        score = similarity(module, candidate)

        cand_tail = candidate.split(".")[-1]
        if cand_tail == tail:
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




def find_memory_fix(module: str, symbol: str, current_file_path: str = "") -> Optional[Dict[str, Any]]:
    module = str(module or "").strip().strip(".")
    symbol = str(symbol or "").strip()

    if not module:
        return None

    remembered = recall_import_fix(
        problem_type="broken_import_group",
        source_module=module,
        file_path=current_file_path,
    )

    if not remembered:
        remembered = recall_import_fix(
            problem_type="broken_import_group",
            source_module=module.split("core.")[-1],
            file_path="",
        )

    if not remembered:
        return None

    resolved = str(remembered.get("resolved_module", "")).strip()
    remembered_symbol = str(remembered.get("symbol", "")).strip()
    remembered_source = str(remembered.get("source_module", "")).strip().strip(".")

    if not resolved:
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

    return remembered

def find_repo_module(module: str, current_file_path: str = "", file_content: str = "") -> Optional[str]:
    module = str(module).strip()
    if not module:
        return None

    exact = exact_or_package_match(module)
    if exact:
        return exact

    # 1. memory reflex
    remembered = recall_import_fix(
        problem_type="broken_import_group",
        source_module=module,
        file_path=current_file_path,
    )
    if remembered:
        resolved = remembered.get("resolved_module")
        if resolved and module_exists(resolved):
            return resolved

    # 2. graph weights
    current_module = file_path_to_module(current_file_path) if current_file_path else ""
    if current_module:
        heavy_neighbors = get_heaviest_neighbors(current_module, limit=5)
        tail = module.split(".")[-1]

        for heavy in heavy_neighbors:
            if heavy == module and module_exists(heavy):
                return heavy
            if heavy.split(".")[-1] == tail and module_exists(heavy):
                return heavy

    # 3. orbit search
    neighbor_modules = extract_neighbor_modules(file_content) if file_content else []

    for candidate in orbit_candidates(module, current_file_path, neighbor_modules):
        if module_exists(candidate):
            return candidate

    # 4. fuzzy
    repo_modules = list_repo_modules()
    return fuzzy_find_module(module, repo_modules, current_file_path, neighbor_modules)




def create_stub_module(module: str, class_name: str | None = None) -> str | None:
    try:
        path = module_to_py_path(module)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                if class_name:
                    f.write(f"class {class_name}:\n    pass\n")
                else:
                    f.write("# auto-generated stub\n")

        # ensure __init__.py
        init_path = path.parent / "__init__.py"
        if not init_path.exists():
            init_path.write_text("", encoding="utf-8")

        return module
    except Exception:
        return None




# === FORCE_STUB_TRIGGER ===
def force_stub_from_imports(file_content: str):
    lines = file_content.splitlines()
    new_lines = []
    changes = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from ") and " import " in stripped:
            parts = stripped.split()
            if len(parts) >= 4:
                module = parts[1]
                name = parts[3]

                created = create_stub_module(module, class_name=name)
                if created:
                    changes.append(module)

        new_lines.append(line)

    return "\n".join(new_lines), changes


def try_fix_from_import(line: str, current_file_path: str, file_content: str) -> Tuple[str, Optional[Tuple[str, str]]]:
    stripped = line.strip()

    if not (stripped.startswith("from ") and " import " in stripped):
        return line, None

    parts = stripped.split()
    if len(parts) < 4:
        return line, None

    module = parts[1]
    imported_name = parts[3].strip()
    if imported_name == "*":
        imported_name = ""

    if module.startswith("."):
        return line, None

    if module in {"os", "sys", "json", "math", "typing", "pathlib", "subprocess", "datetime", "collections"}:
        return line, None

    if module_exists(module):
        return line, None

    memory_fix = find_memory_fix(module, imported_name, current_file_path=current_file_path)
    if memory_fix:
        resolved_module = str(memory_fix.get("resolved_module", "")).strip()
        remembered_symbol = str(memory_fix.get("symbol", "")).strip()

        class_name = imported_name or remembered_symbol or None

        if resolved_module:
            created = create_stub_module(resolved_module, class_name=class_name)
            if created:
                return line, (module, resolved_module, class_name, "memory_fast_path")

    repaired = find_repo_module(module, current_file_path=current_file_path, file_content=file_content)
    if repaired and repaired != module:
        return line.replace(f"from {module} import", f"from {repaired} import", 1), (module, repaired)

    if repaired == module:
        return line, None

    # 👉 STUB fallback
    tail = module.split(".")[-1]
    imported_name = parts[3].strip()
    if imported_name == "*":
        imported_name = None
    created = create_stub_module(module, class_name=imported_name)

    if created:
        record_import_fix(
            problem_type="broken_import_group",
            source_module=module,
            resolved_module=module,
            file_path=current_file_path,
            symbol=imported_name,
            kind="stub_fallback",
            success=True,
        )
        return line, (module, module, imported_name, "stub_fallback")

    return f"# FIXME broken import: {line}", None


def try_fix_plain_import(line: str, current_file_path: str, file_content: str) -> Tuple[str, Optional[Tuple[str, str]]]:
    stripped = line.strip()

    if not stripped.startswith("import "):
        return line, None

    if "," in stripped:
        return line, None

    module = stripped.replace("import ", "", 1).strip()

    if not module or module.startswith("."):
        return line, None

    if module in {"os", "sys", "json", "math", "typing", "pathlib", "subprocess", "datetime", "collections"}:
        return line, None

    if module_exists(module):
        return line, None

    repaired = find_repo_module(module, current_file_path=current_file_path, file_content=file_content)
    if repaired and repaired != module:
        return line.replace(f"import {module}", f"import {repaired}", 1), (module, repaired)

    if repaired == module:
        return line, None

    # 👉 STUB fallback
    tail = module.split(".")[-1]
    imported_name = parts[3].strip()
    if imported_name == "*":
        imported_name = None
    created = create_stub_module(module, class_name=imported_name)

    if created:
        record_import_fix(
            problem_type="broken_import_group",
            source_module=module,
            resolved_module=module,
            file_path=current_file_path,
            symbol=imported_name,
            kind="stub_fallback",
            success=True,
        )
        return line, (module, module, imported_name, "stub_fallback")

    return f"# FIXME broken import: {line}", None


def request_fix(prompt: str, original_content: str, current_file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
    lines = original_content.splitlines()
    fixed = []
    learned_pairs: List[Tuple[str, str]] = []

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

    # === FAST PATH: import fix BEFORE LLM ===
    try:
        from pathlib import Path as _Path

        content = _Path(path).read_text(encoding="utf-8")

        new_lines = []
        changed = False

        for line in content.splitlines():
            if line.strip().startswith("from ") and " import " in line:
                fixed_line, info = try_fix_from_import(
                    line,
                    current_file_path=path,
                    file_content=content,
                )
                if info:
                    changed = True
                    new_lines.append(fixed_line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if changed:
            new_content = "\n".join(new_lines)
            _Path(path).write_text(new_content, encoding="utf-8")

            return {
                "ok": True,
                "reason": "memory_or_simple_fix_applied",
                "changed_files": [path],
            }

    except Exception as e:
        print("force_try_fix_error:", e)

    # === END FAST PATH ===

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
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
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
            "reason": "llm_empty_result",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    if fixed == original:
        return {
            "ok": True,
            "reason": "llm_no_change",
            "changed_files": [],
            "backup_files": [],
            "learned_rules": [],
        }

    try:
        backup_path = make_backup(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fixed)
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

    for pair in learned_pairs:
        symbol = ""
        kind = "unknown"

        if len(pair) >= 4:
            source_module, resolved_module, symbol, kind = pair[0], pair[1], pair[2], pair[3]
        else:
            source_module, resolved_module = pair[0], pair[1]

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
    restored = []
    failed = []

    for path in changed_files:
        backup_path = f"{path}.bak"
        ok = restore_backup(path, backup_path)
        if ok:
            restored.append(path)
        else:
            failed.append(path)

    return {
        "ok": len(failed) == 0,
        "restored": restored,
        "failed": failed,
    }


def finalize_backups(changed_files: List[str]) -> None:
    for path in changed_files:
        cleanup_backup(f"{path}.bak")
