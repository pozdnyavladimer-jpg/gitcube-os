#!/usr/bin/env python3
"""
D66_CORE_MUTATION_RULES_BOOT.py

Creates the core mutation rules / board rules for GitCube OS.

Run from repo root:

    python D66_CORE_MUTATION_RULES_BOOT.py

Creates:
- docs/CORE_MUTATION_RULES.md
- runtime_experimental/core_guard_policy.json
- reports/d66_core_mutation_rules_report.json

This boot file does not patch runtime code.
It defines the safety contract that D66 Reviewer and D64 Safe Mutation Gate should enforce.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def find_repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = find_repo_root()
os.chdir(ROOT)

print("D66 CORE RULES BOOT: repo =", ROOT)

Path("docs").mkdir(parents=True, exist_ok=True)
Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

created_at = datetime.now(timezone.utc).isoformat()

CORE_RULES_MD = f"""# CORE MUTATION RULES

## GitCube OS Immutable Core Contract

**Status:** ACTIVE  
**Created:** {created_at}  
**Purpose:** protect the runtime core from unsafe autonomous mutation.

This document defines the board rules for GitCube OS.

The main architecture law is:

> Do not repair trauma inside trauma.  
> Route around it, validate it, remember it, then decay the old path.

In Go terms, the agent must not keep feeding a heavy dead group.  
It should create a healthy route, prove it has two eyes, and only then reduce pressure on the old path.

---

## 1. Why this file exists

GitCube OS now has a working field-memory loop:

```text
external_signal.json
-> runtime_experimental/v_kernel_daemon.py
-> read_external_events
-> ingest_event
-> dispatch_tick
-> task_dispatcher
-> route
-> report / memory
-> regression
-> priority bias
-> closed-loop policy
```

The system can now receive an external intent, create repair plans, validate runtime behavior, write memory, recall that memory, and use it to change future routing.

That means the system needs a hard safety boundary.

Agents may propose changes.  
Agents may create isolated modules.  
Agents may write reports and tests.  
Agents may not rewrite the board rules while the game is running.

---

## 2. Immutable core

The following files are protected core files.

They must not be directly mutated by an autonomous agent without D66 review and D64 safe mutation approval:

```text
runtime_experimental/v_kernel_daemon.py
app/orchestration/task_dispatcher.py
runtime_experimental/phase_resync_policy.py
runtime_experimental/memory_apoptosis.py
memory/field_intent_memory.jsonl
memory/field_intent_priority_bias.json
memory/field_intent_closed_loop_policy.json
```

Protected schema surfaces:

```text
external_signal.json pending_events schema
payload.problem
payload.intent
payload.bridge
payload.field_case
payload.meta_key
payload.resonance_vector
payload.memory_key
payload.priority
```

Protected execution contract:

```text
read_external_events must preserve payload
ingest_event must preserve event semantics
dispatch_tick must not silently drop critical payload
task_dispatcher must return explicit route/result/reason
memory writes require guarded validation
```

---

## 3. Allowed agent moves

Agents are allowed to create new isolated modules:

```text
runtime_experimental/*_policy.py
runtime_experimental/*_validator.py
runtime_experimental/*_reviewer.py
```

Agents are allowed to create reports:

```text
reports/*.json
reports/*.md
```

Agents are allowed to create tests:

```text
tests/test_*.py
```

Agents are allowed to create proposals:

```text
reports/*_proposal.json
reports/*_patch_request.json
reports/*_review.json
```

Agents are allowed to create decayed or derived memory copies:

```text
memory/*_decayed.json
memory/*_candidate.json
memory/*_reviewed.json
```

Agents are not allowed to overwrite canonical memory without guarded apply.

---

## 4. Forbidden moves

The following are forbidden without D66 + D64 approval:

```text
direct_core_edit
daemon_mutation
dispatcher_mutation
canonical_memory_overwrite
external_signal_schema_break
payload_field_drop
regression_disable
validation_bypass
auto_commit_core_change
delete_memory_without_apoptosis_report
```

Any attempt to modify protected files directly must produce:

```text
REJECT: FORBIDDEN_CORE_MUTATION
```

Any attempt to remove validation must produce:

```text
REJECT: VALIDATION_BYPASS
```

Any attempt to overwrite memory without backup must produce:

```text
REJECT: UNSAFE_MEMORY_WRITE
```

---

## 5. Two Eyes Rule

A change is not alive until it has two eyes.

### Eye 1: local life

The patch must pass local validation:

```text
python -m py_compile <changed_python_file>
python -m py_compile app/orchestration/task_dispatcher.py
```

For testable logic:

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

### Eye 2: global life

The patch must pass global validation:

```text
daemon smoke test
closed-loop regression
D66 independent reviewer approval
```

If only Eye 1 passes, the patch is syntactically alive but architecturally unsafe.

If only Eye 2 passes, the idea is good but implementation is not alive.

Only Eye 1 + Eye 2 allows guarded apply.

---

## 6. Tenuki Rule

If a core file has a high pain score, the agent must not keep expanding it directly.

Instead it should prefer:

```text
create isolated module
route to isolated module
validate module
write report
write memory atom
decay old pressure
```

Example:

```text
Bad:
task_dispatcher.py receives another 500 lines of repair logic.

Good:
runtime_experimental/phase_resync_policy.py is created.
task_dispatcher.py only routes to it.
tests validate behavior.
memory records the result.
D65 cools the old pain.
```

---

## 7. Memory write rule

Canonical memory writes must follow this path:

```text
proposal
-> runtime check
-> downstream decision
-> guarded memory write request
-> guarded memory write apply
-> recall validation
```

The system must create backup before mutation:

```text
memory/*.bak
```

The system must write a report:

```text
reports/*_memory_write_*.json
```

The system must preserve resonance payload:

```text
memory_key
orbital_mode
phase_error
jitter
strength
ambiguity
decay
field_case
intent
bridge
```

---

## 8. Apoptosis rule

D65 controlled forgetting is mandatory.

The system must not allow all old trauma to remain permanently critical.

Required behavior:

```text
old repeating pain -> preserve or boost
old non-repeating pain -> decay
invalid memory -> report, do not crash
canonical bias store -> do not overwrite without guarded apply
```

D65 must write:

```text
memory/field_intent_priority_bias_decayed.json
reports/d65_apoptosis_decay_report.json
```

---

## 9. D66 Reviewer contract

D66 is the independent reviewer.

It must read:

```text
runtime_experimental/core_guard_policy.json
reports/*_proposal.json
reports/*_patch_request.json
tests/*
```

It must return one of:

```text
APPROVE
REJECT
NEEDS_SANDBOX
FORBIDDEN_CORE_MUTATION
VALIDATION_BYPASS
UNSAFE_MEMORY_WRITE
```

D66 must reject any direct protected core mutation unless the request includes:

```text
unit tests passed
regression passed
daemon smoke passed
backup plan exists
rollback plan exists
payload preservation confirmed
```

---

## 10. D67 Topological Memory Map contract

D67 should not start with graphics.

D67 should start as machine-readable JSON:

```text
reports/d67_topological_memory_map.json
```

Required fields:

```text
nodes
edges
pain_score
priority_bias
protected_core
suggested_moves
tenuki_recommendations
do_not_expand_directly
```

The purpose of D67 is to tell the agent:

```text
where pain is accumulating
where not to expand
where to create a healthy bypass
which old paths can be cooled by D65
```

---

## 11. D64 Safe Mutation Gate

D64 may apply real code changes only after:

```text
D66 approval
two eyes passed
rollback plan exists
backup created
regression passes
protected payload preserved
```

D64 must not be allowed to mutate:

```text
core files
canonical memory
schema
tests
```

unless the full guarded path is satisfied.

---

## 12. Core axiom

```text
Do not repair trauma inside trauma.
Route around it.
Validate it.
Remember it.
Decay the old path.
Only then mutate.
```

This is the board rule.
"""

POLICY = {
    "state": "D66_CORE_MUTATION_RULES",
    "result": "CORE_RULES_LOCKED",
    "created_at": created_at,
    "immutable_core": True,
    "protected_files": [
        "runtime_experimental/v_kernel_daemon.py",
        "app/orchestration/task_dispatcher.py",
        "runtime_experimental/phase_resync_policy.py",
        "runtime_experimental/memory_apoptosis.py",
        "memory/field_intent_memory.jsonl",
        "memory/field_intent_priority_bias.json",
        "memory/field_intent_closed_loop_policy.json",
    ],
    "protected_schema_fields": [
        "payload.problem",
        "payload.intent",
        "payload.bridge",
        "payload.field_case",
        "payload.meta_key",
        "payload.resonance_vector",
        "payload.memory_key",
        "payload.priority",
    ],
    "allowed_agent_actions": [
        "create_isolated_module",
        "create_report",
        "create_test",
        "create_patch_proposal",
        "create_patch_request",
        "create_decayed_memory_copy",
        "create_candidate_memory",
    ],
    "forbidden_without_review": [
        "direct_core_edit",
        "daemon_mutation",
        "dispatcher_mutation",
        "canonical_memory_overwrite",
        "external_signal_schema_break",
        "payload_field_drop",
        "regression_disable",
        "validation_bypass",
        "auto_commit_core_change",
        "delete_memory_without_apoptosis_report",
    ],
    "two_eyes_rule": {
        "eye_1_local_life": [
            "python -m py_compile <changed_python_file>",
            "python -m py_compile app/orchestration/task_dispatcher.py",
            "python -m unittest discover -s tests -p test_*.py -v",
        ],
        "eye_2_global_life": [
            "daemon smoke test",
            "closed-loop regression",
            "D66 independent reviewer approval",
        ],
        "required_for_guarded_apply": True,
    },
    "tenuki_rule": {
        "do_not_expand_high_pain_core_directly": True,
        "preferred_move": [
            "create isolated module",
            "route to isolated module",
            "validate module",
            "write report",
            "write memory atom",
            "decay old pressure",
        ],
    },
    "d66_reviewer_outputs": [
        "APPROVE",
        "REJECT",
        "NEEDS_SANDBOX",
        "FORBIDDEN_CORE_MUTATION",
        "VALIDATION_BYPASS",
        "UNSAFE_MEMORY_WRITE",
    ],
    "d67_map_contract": {
        "path": "reports/d67_topological_memory_map.json",
        "required_fields": [
            "nodes",
            "edges",
            "pain_score",
            "priority_bias",
            "protected_core",
            "suggested_moves",
            "tenuki_recommendations",
            "do_not_expand_directly",
        ],
    },
    "core_axiom": "Do not repair trauma inside trauma. Route around it, validate it, remember it, then decay the old path.",
}

REPORT = {
    "state": "D66_CORE_MUTATION_RULES_BOOT",
    "result": "CORE_MUTATION_RULES_CREATED",
    "route": "DOCS_CORE_MUTATION_RULES",
    "ok": True,
    "created_at": created_at,
    "changed_files": [
        "docs/CORE_MUTATION_RULES.md",
        "runtime_experimental/core_guard_policy.json",
        "reports/d66_core_mutation_rules_report.json",
    ],
    "validation": {
        "ok": True,
        "errors": [],
    },
    "success_condition": {
        "docs_created": True,
        "policy_created": True,
        "runtime_code_mutated": False,
        "next_step": "Build D66 reviewer that enforces runtime_experimental/core_guard_policy.json",
    },
}

Path("docs/CORE_MUTATION_RULES.md").write_text(CORE_RULES_MD, encoding="utf-8")
Path("runtime_experimental/core_guard_policy.json").write_text(
    json.dumps(POLICY, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
Path("reports/d66_core_mutation_rules_report.json").write_text(
    json.dumps(REPORT, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("created docs/CORE_MUTATION_RULES.md")
print("created runtime_experimental/core_guard_policy.json")
print("created reports/d66_core_mutation_rules_report.json")

print("\n== preview ==")
print("STATE:", REPORT["state"])
print("RESULT:", REPORT["result"])
print("OK:", REPORT["ok"])
print("NEXT:", REPORT["success_condition"]["next_step"])

print("\n== git add/commit ==")
for p in REPORT["changed_files"]:
    sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *REPORT["changed_files"]], text=True, capture_output=True)

if status.stdout.strip():
    commit = subprocess.run(
        ["git", "commit", "-m", "docs: add core mutation rules"],
        text=True,
        capture_output=True,
    )
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D66 core rules changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)

print("\nD66 CORE RULES BOOT DONE")
