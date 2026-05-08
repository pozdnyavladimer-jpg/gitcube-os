#!/usr/bin/env python3
# CONTROLLED_AUTONOMY_CHAIN_DOC_BOOT.py
#
# Creates docs/CONTROLLED_AUTONOMY_CHAIN.md
#
# Purpose:
# - Explain the D90-D99 guarded autonomy chain.
# - Make clear that AI is propose-only and real apply remains blocked.
# - Create a readable architecture legend for humans and future agents.
#
# This script does NOT mutate runtime code, protected core, routes, or memory.
# It only writes a documentation file and optionally commits it.

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DOC = r"""# GitCube OS — Controlled Autonomy Chain

## Purpose

This repository implements a guarded autonomy chain for AI-assisted code evolution.

The system is designed to allow AI to propose, simulate, package, review, and prepare changes — without granting direct execution authority.

Core principle:

```text
AI proposes.
System verifies.
Human approves.
Execution remains gated.
Rollback evidence is prepared before any real apply.
```

## Current Chain

```text
D90  Controlled Apply Plan
D91  Explicit Apply Scope Approval
D92  Guarded Apply Dry-Run Package
D93  Dry-Run Recheck Gate
D94  Final Execution Approval Request
D95  Human Signed Execution Intent
D96  Final Local Full Regression
D97  Protected Core No-Touch Reconfirmation
D98  Rollback Restore Command Pack
D99  Final Guarded Execution Capsule
```

## What the Chain Already Does

The current system can:

```text
- create guarded plans
- generate dry-run packages
- block real apply
- require human intent
- run local regression checks
- snapshot protected-core files
- confirm route insertion did not happen
- prepare rollback/restore documentation
- create a final guarded capsule before execution
```

## What the Chain Does NOT Do

The system does not currently allow:

```text
- automatic apply
- route insertion
- protected-core mutation
- canonical memory overwrite
- external AI/network execution
- AI git commit or push
- rollback execution
- destructive restore commands
```

These actions remain blocked until a later explicit human decision gate.

## Safety Model

Every module must preserve these flags unless a later explicit human execution gate changes the state:

```text
actual_apply_executed: false
route_inserted: false
protected_core_mutated: false
canonical_memory_mutated: false
runtime_code_mutated: false
external_ai_called: false
network_accessed: false
git_commit_by_ai: false
```

## AI Boundary

AI is allowed only in propose/review/planning mode.

Allowed:

```text
PROPOSE_ONLY
JSON_ONLY
DRY_RUN_ONLY
DOCUMENTATION_ONLY
REGRESSION_ONLY
```

Forbidden:

```text
SHELL_EXECUTION
GIT_COMMIT_BY_AI
GIT_PUSH_BY_AI
PROTECTED_CORE_EDIT
ROUTE_INSERT
REAL_APPLY
NETWORK_MUTATION
SECRET_ACCESS
```

## Current Status

As of D99, the system has reached the final guarded capsule stage.

This means the architecture has a complete pre-execution safety chain, but real execution is still intentionally blocked.

D99 prepares the system for a future controlled human decision gate.

## Next Gates

Recommended next modules:

```text
D100 Controlled Human Execution Decision
D101 One-Shot Manual Execution Capsule
D102 Post-Execution Verifier
D103 Rollback Evidence Builder
D104 Final Audit Ledger / Replay Log
```

## Interpretation

This project treats code change as a controlled biological/evolutionary process:

```text
pressure -> proposal -> simulation -> review -> regression -> no-touch proof -> rollback plan -> capsule -> human decision
```

The goal is not to let AI mutate the system freely.

The goal is to build an operating system where AI-generated change can be safely proposed, tested, rejected, audited, or eventually applied under strict human-controlled gates.

## Practical Rule for Future Agents

A future AI agent may produce candidate JSON, candidate diffs, review packets, reports, and documentation.

A future AI agent must not:

```text
- run destructive commands
- commit by itself
- push by itself
- insert routes
- touch protected core
- overwrite canonical memory
- call external AI/network services for execution
- mark real apply as approved
```

The chain should remain safe by default.

Real execution requires a separate, explicit, human-controlled gate.
"""


def repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


def run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def main() -> int:
    root = repo_root()
    print("CONTROLLED AUTONOMY CHAIN DOC BOOT: repo =", root)

    doc_path = root / "docs" / "CONTROLLED_AUTONOMY_CHAIN.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(DOC, encoding="utf-8")

    text = doc_path.read_text(encoding="utf-8")
    required = [
        "GitCube OS — Controlled Autonomy Chain",
        "D90  Controlled Apply Plan",
        "D99  Final Guarded Execution Capsule",
        "D100 Controlled Human Execution Decision",
        "AI proposes.",
        "System verifies.",
        "Human approves.",
        "Execution remains gated.",
        "actual_apply_executed: false",
        "route_inserted: false",
        "protected_core_mutated: false",
        "Real execution requires a separate, explicit, human-controlled gate.",
    ]

    missing = [item for item in required if item not in text]
    if missing:
        print("DOC VALIDATION FAILED")
        for item in missing:
            print("missing:", item)
        return 1

    print("DOC CREATED:", doc_path)
    print("DOC VALIDATION: OK")
    print("DOC SIZE:", doc_path.stat().st_size, "bytes")

    # Save in git if this is a repository.
    if (root / ".git").exists():
        add = run(["git", "add", "-f", "docs/CONTROLLED_AUTONOMY_CHAIN.md"], check=False)
        if add.stdout:
            print(add.stdout)
        if add.stderr:
            print(add.stderr)

        status = run(["git", "status", "--porcelain", "docs/CONTROLLED_AUTONOMY_CHAIN.md"], check=False)
        if status.stdout.strip():
            commit = run(["git", "commit", "-m", "docs: add controlled autonomy chain explainer"], check=False)
            if commit.stdout:
                print(commit.stdout)
            if commit.stderr:
                print(commit.stderr)
        else:
            print("No documentation changes to commit.")

        print("FINAL STATUS:")
        final = run(["git", "status", "--short"], check=False)
        if final.stdout:
            print(final.stdout)
        if final.stderr:
            print(final.stderr)

    print("CONTROLLED AUTONOMY CHAIN DOC BOOT DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
