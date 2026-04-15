from __future__ import annotations

from typing import Dict, Any
import os


def build_prompt(task: Dict[str, Any], file_content: str, path: str) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return f"""Task type: broken_import_group
Target file: {path}

Allowed actions:
- fix clearly broken local imports
- replace unresolved local package imports with safe relative/local equivalents when obvious
- add missing package marker import-safe structure only if strictly needed

Forbidden actions:
- delete unrelated code
- rename public APIs
- rewrite the whole file unnecessarily
- invent external dependencies

Goal:
Reduce architectural tension while preserving behavior.

Current payload:
{payload}

Current file content:
{file_content}

Return only corrected file content.
"""


def request_fix(prompt: str, original_content: str) -> str:
    lines = original_content.splitlines()
    fixed = []

    for line in lines:
        stripped = line.strip()

        # Лишаємо пусті рядки як є
        if not stripped:
            fixed.append(line)
            continue

        # Простий кейс: голий import без package path поки не чіпаємо
        if stripped.startswith("import ") and "." not in stripped:
            fixed.append(line)
            continue

        # from x import y
        if stripped.startswith("from ") and " import " in stripped:
            parts = stripped.split()
            if len(parts) >= 4:
                module = parts[1]

                # дозволяємо локальні простори
                if module.startswith("app.") or module.startswith("core.") or module.startswith("runtime_experimental."):
                    fixed.append(line)
                    continue

                # явний підозрілий import — коментуємо
                fixed.append(f"# FIXME broken import: {line}")
                continue

        fixed.append(line)

    return "\n".join(fixed) + ("\n" if original_content.endswith("\n") else "")


def apply_llm_fix(task: Dict[str, Any], path: str) -> Dict[str, Any]:
    path = str(path).strip()
    if not path or not os.path.exists(path):
        return {
            "ok": False,
            "reason": "target_file_missing",
            "changed_files": [],
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
    except Exception as e:
        return {
            "ok": False,
            "reason": f"read_failed:{e}",
            "changed_files": [],
        }

    prompt = build_prompt(task, original, path)
    fixed = request_fix(prompt, original)

    if not isinstance(fixed, str) or not fixed.strip():
        return {
            "ok": False,
            "reason": "llm_empty_result",
            "changed_files": [],
        }

    if fixed == original:
        return {
            "ok": True,
            "reason": "llm_no_change",
            "changed_files": [],
        }

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(fixed)
    except Exception as e:
        return {
            "ok": False,
            "reason": f"write_failed:{e}",
            "changed_files": [],
        }

    return {
        "ok": True,
        "reason": "llm_fix_applied",
        "changed_files": [path],
    }
