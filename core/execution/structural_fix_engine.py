from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List


REPO_ROOT = Path(".")


def _safe_write(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def _ensure_init_chain(directory: Path) -> List[str]:
    changed: List[str] = []

    current = directory
    while True:
        init_path = current / "__init__.py"
        if not init_path.exists():
            ok = _safe_write(
                init_path,
                '"""Auto-created package marker by GitCube structural repair."""\n',
            )
            if ok:
                changed.append(str(init_path))

        if current == REPO_ROOT or current.parent == current:
            break

        try:
            current = current.parent
            if str(current) in {".", ""}:
                break
        except Exception:
            break

    return list(reversed(changed))


def _module_to_file(module_name: str) -> Path:
    return REPO_ROOT / Path(module_name.replace(".", "/")).with_suffix(".py")


def create_missing_module(module_name: str) -> Dict[str, Any]:
    module_name = str(module_name).strip().strip(".")
    if not module_name:
        return {
            "ok": False,
            "reason": "empty_module_name",
            "changed_files": [],
        }

    target_file = _module_to_file(module_name)
    target_dir = target_file.parent
    changed_files: List[str] = []

    changed_files.extend(_ensure_init_chain(target_dir))

    if target_file.exists():
        return {
            "ok": True,
            "reason": "module_already_exists",
            "changed_files": changed_files,
            "target_file": str(target_file),
        }

    stub = (
        '"""Auto-generated structural stub by GitCube.\n\n'
        f"Module: {module_name}\n"
        'Status: placeholder_for_future_logic\n'
        '"""\n\n'
        "__all__ = []\n\n"
        "# TODO: replace stub with real implementation.\n"
    )

    ok = _safe_write(target_file, stub)
    if not ok:
        return {
            "ok": False,
            "reason": "write_failed",
            "changed_files": changed_files,
            "target_file": str(target_file),
        }

    changed_files.append(str(target_file))

    return {
        "ok": True,
        "reason": "module_stub_created",
        "changed_files": changed_files,
        "target_file": str(target_file),
    }


def execute_structural_fix(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    changed_files: List[str] = []

    if problem in {"missing_init_group", "missing_init", "package_structure"}:
        paths = payload.get("paths", task.get("paths", []))
        if not isinstance(paths, list):
            paths = []

        for raw in paths:
            p = Path(str(raw).strip())
            if not str(p):
                continue

            target_dir = p.parent if p.suffix == ".py" else p
            changed_files.extend(_ensure_init_chain(target_dir))

        return {
            "ok": True,
            "reason": "package_markers_created_or_already_present",
            "changed_files": sorted(set(changed_files)),
        }

    if problem in {"structural_orphans_group", "missing_module_group", "broken_module_group"}:
        recommended = mesh_result.get("recommended_targets", [])
        targets: List[str] = []

        if isinstance(recommended, list):
            targets.extend(str(x).strip() for x in recommended if str(x).strip())

        if not targets:
            payload_paths = payload.get("paths", task.get("paths", []))
            if isinstance(payload_paths, list):
                targets.extend(str(x).strip() for x in payload_paths if str(x).strip())

        created = []
        for module_name in targets[:3]:
            # якщо передали .py шлях, перетворюємо на module name
            if module_name.endswith(".py"):
                module_name = module_name[:-3].replace("/", ".").replace("\\", ".")
            result = create_missing_module(module_name)
            if result.get("ok"):
                created.extend(result.get("changed_files", []))

        return {
            "ok": True,
            "reason": "structural_genesis_applied" if created else "no_structural_targets",
            "changed_files": sorted(set(created)),
        }

    return {
        "ok": False,
        "reason": "unsupported_structural_problem",
        "changed_files": [],
    }


if __name__ == "__main__":
    demo_task = {
        "problem": "structural_orphans_group",
        "payload": {
            "problem": "structural_orphans_group",
            "paths": ["core.policy.safety_policy"],
        },
    }
    demo_mesh = {"recommended_targets": ["core.policy.safety_policy"]}
    print(execute_structural_fix(demo_task, demo_mesh))
