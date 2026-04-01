# START HERE

This repo has two paths:

- Stable Runtime
- Experimental Runtime

---

## 1. Stable Runtime

Run:

PYTHONPATH=. python examples/simple_loop.py

Use this if you want:

- canonical behavior
- bindu logic
- transition memory

Key files:

- app/state_engine.py
- core/state.py
- core/evaluation.py
- runtime/agent_loop.py

---

## 2. Experimental Runtime

Run:

PYTHONPATH=. python examples/experimental_loop.py

This gives:

- field (environment)
- class dynamics
- vitality economy
- adaptive behavior

Key files:

- runtime_experimental/field_engine.py
- runtime_experimental/agent_loop.py
- runtime_experimental/role_transaction.py
- runtime_experimental/vitality_engine.py

---

## Mental Model

Stable:

state → decision → update

Experimental:

state → field → class → decision → vitality → update

---

## Repo Structure

app/
core/
runtime/
runtime_experimental/
examples/
docs/

---

## Which to use

Stable → control, debugging  
Experimental → behavior, evolution  

---

## What to watch

Stable:

- decision
- bindu
- state change

Experimental:

- class
- vitality
- field mode
- decisions

---

## Important

Do not mix experimental into stable too early.

runtime/ = stable  
runtime_experimental/ = evolving  

---

## Entry Point

Best start:

PYTHONPATH=. python examples/experimental_loop.py

---

## One-line

GitCube OS executes adaptive state logic.

---

## One-line (Experimental)

Experimental runtime turns the system into a living adaptive field.
