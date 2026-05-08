# Guarded Autonomy Chain

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
