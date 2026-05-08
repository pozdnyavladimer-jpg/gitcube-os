#!/usr/bin/env python3
# D105_GUARDED_AUTONOMY_CHAIN_DOC_BOOT.py
#
# Creates a separate documentation file for the sealed D90-D104 guarded autonomy chain:
#
#   docs/GUARDED_AUTONOMY_CHAIN.md
#   reports/d105_guarded_autonomy_chain_doc.json
#
# This script is documentation-only.
# It does NOT mutate runtime, protected core, canonical memory, routes, or execution gates.
# It does NOT call external AI/network.
# It does NOT run apply/rollback/restore.
# It does NOT modify the main README.md.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DOC_PATH = Path("docs/GUARDED_AUTONOMY_CHAIN.md")
REPORT_PATH = Path("reports/d105_guarded_autonomy_chain_doc.json")

DOC = """# Guarded Autonomy Chain

## Status

**CHAIN:** D90 → D104  
**TAG:** `guarded-autonomy-d90-d104-sealed`  
**STATE:** `GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED`  
**AI MODE:** `PROPOSE_ONLY`  
**REAL APPLY:** `BLOCKED`  
**ROUTE INSERT:** `BLOCKED`  
**PROTECTED CORE MUTATION:** `BLOCKED`

---

## Purpose

This document explains the guarded autonomy layer added to GitCube OS.

The goal of this chain is not to let AI execute code directly.

The goal is to create a controlled boundary where AI may propose, generate evidence, prepare dry-run artifacts, and build audit reports — while real execution remains blocked until explicit human-controlled gates are satisfied.

---

## Core Rule

```text
AI proposes.
System verifies.
Human approves.
Execution remains gated.
```

No AI module may:

- run real apply
- insert routes
- mutate protected core
- overwrite canonical memory
- call external AI/network execution
- commit or push by itself
- execute rollback by itself
- delete runtime candidates

---

## Chain Overview

| Gate | Purpose | Real execution |
|---|---|---|
| D90 | Controlled apply plan | blocked |
| D91 | Explicit apply scope approval | blocked |
| D92 | Guarded apply dry-run package | blocked |
| D93 | Dry-run recheck gate | blocked |
| D94 | Final execution approval request | blocked |
| D95 | Human signed execution intent | blocked |
| D96 | Final local full regression | blocked |
| D97 | Protected-core no-touch reconfirmation | blocked |
| D98 | Rollback restore command pack | blocked |
| D99 | Final guarded execution capsule | blocked |
| D100 | Controlled human execution decision | blocked |
| D101 | One-shot manual execution capsule | blocked |
| D102 | Post-execution verifier | blocked |
| D103 | Rollback evidence builder | blocked |
| D104 | Final audit ledger | blocked |

---

## Final Sealed State

D104 seals the pre-execution guarded chain.

The system has enough structure to explain, audit, replay, and verify the path toward controlled execution, but it still does not grant autonomous apply.

```text
TERMINAL_STATUS: PRE_EXECUTION_GUARDED_CHAIN_SEALED
REAL_APPLY: BLOCKED
AI_AUTONOMOUS_EXECUTION: BLOCKED
HUMAN_REVIEW_REQUIRED: TRUE
```

---

## Important Reports

```text
reports/d104_final_audit_ledger.json
reports/d104_replay_log_index.json
reports/d104_guarded_autonomy_chain_summary.json
reports/d104_terminal_safety_state.json
```

---

## Git Tag

The sealed checkpoint is stored as:

```text
guarded-autonomy-d90-d104-sealed
```

Verify:

```bash
git tag | grep guarded-autonomy
git show --stat guarded-autonomy-d90-d104-sealed
```

---

## Interpretation

This layer turns GitCube OS autonomy into controlled autonomy.

It does not remove autonomy.

It gives autonomy a membrane:

- proposal without uncontrolled mutation
- dry-run without real apply
- rollback evidence without rollback execution
- audit ledger without execution permission
- human confirmation before any irreversible step

---

## Why This Is Separate From The Main README

The main README describes the product: GitCube OS, its agent model, memory, routing, cooldown, GitHub integration, and runtime safety.

This file describes the safety protocol around controlled autonomy.

Keeping it separate makes the repository easier to read:

- `README.md` explains what GitCube OS is.
- `docs/GUARDED_AUTONOMY_CHAIN.md` explains how the D90-D104 safety chain is sealed.

---

## Optional README Link

Add this small section to the main `README.md` only if you want a visible entry point:

```md
## Guarded Autonomy Chain

The D90-D104 controlled autonomy safety chain is documented here:

[Guarded Autonomy Chain](docs/GUARDED_AUTONOMY_CHAIN.md)
```

---

## Final Principle

```text
Autonomy is allowed to think.
Autonomy is allowed to propose.
Autonomy is allowed to verify.

Autonomy is not allowed to silently execute.
```
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(cmd: list[str]) -> dict:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
        return {
            "cmd": cmd,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-2000:],
            "stderr_tail": p.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "cmd": cmd,
            "returncode": -1,
            "stdout_tail": "",
            "stderr_tail": repr(exc),
        }


def main() -> int:
    root = repo_root()
    os.chdir(root)

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    previous = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
    DOC_PATH.write_text(DOC, encoding="utf-8")

    checks = {
        "doc_exists": DOC_PATH.exists(),
        "main_readme_untouched_by_script": True,
        "contains_chain": "D90 → D104" in DOC,
        "contains_tag": "guarded-autonomy-d90-d104-sealed" in DOC,
        "contains_propose_only": "PROPOSE_ONLY" in DOC,
        "contains_real_apply_blocked": "REAL APPLY:** `BLOCKED`" in DOC,
        "contains_d104_terminal_state": "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED" in DOC,
        "contains_optional_readme_link": "Optional README Link" in DOC,
    }

    ok = all(checks.values())

    report = {
        "state": "D105_GUARDED_AUTONOMY_CHAIN_DOC",
        "ok": ok,
        "decision": "GUARDED_AUTONOMY_CHAIN_DOC_READY" if ok else "GUARDED_AUTONOMY_CHAIN_DOC_INCOMPLETE",
        "created_at": now(),
        "doc_path": str(DOC_PATH),
        "report_path": str(REPORT_PATH),
        "doc_sha256": sha256_text(DOC),
        "previous_doc_sha256": sha256_text(previous) if previous else "",
        "main_readme_modified": False,
        "writes": [
            str(DOC_PATH),
            str(REPORT_PATH),
        ],
        "does_not_execute": [
            "real_apply",
            "route_insert",
            "protected_core_mutation",
            "canonical_memory_overwrite",
            "external_ai_or_network_call",
            "rollback",
            "restore",
            "git_commit_by_ai",
        ],
        "checks": checks,
        "summary": {
            "purpose": "Create a separate Markdown explanation for the sealed D90-D104 guarded autonomy chain.",
            "recommended_main_readme_action": "Optionally add a short link to docs/GUARDED_AUTONOMY_CHAIN.md.",
            "safe_to_commit": ok,
        },
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\nVerification commands:")
    print("cat docs/GUARDED_AUTONOMY_CHAIN.md")
    print("cat reports/d105_guarded_autonomy_chain_doc.json")
    print("git status --short")

    print("\nSave commands:")
    print("git add -f D105_GUARDED_AUTONOMY_CHAIN_DOC_BOOT.py")
    print("git add -f docs/GUARDED_AUTONOMY_CHAIN.md")
    print("git add -f reports/d105_guarded_autonomy_chain_doc.json")
    print('git commit -m "docs: add guarded autonomy chain readme"')
    print("git push origin HEAD")
    print("git status --short")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
