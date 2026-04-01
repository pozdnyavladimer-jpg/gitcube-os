# GitCube OS

GitCube OS is the execution layer of the GitCube system.

It is not the experimental lab.
It is not the canonical meaning layer.

It is the place where adaptive logic becomes executable behavior.

---

## System Position

GitCube OS is part of a 3-layer architecture:

- GitCube Lab → exploration and mutation
- Geometry Navigator → canonical meaning and interpretation
- GitCube OS → runtime execution

Flow:

Lab → Navigator → OS

Meaning:

- Lab invents
- Navigator explains
- OS executes

---

## Core Idea

GitCube OS executes an adaptive control loop that decides:

- what state is valid
- what transition is allowed
- what should persist
- when the system should reroute

---

## Repository Map

- app/
- core/
- runtime/
- runtime_experimental/
- examples/
- docs/
- tests/

---

## ▶️ Quick Start

### Stable runtime

Run:

PYTHONPATH=. python examples/simple_loop.py

Explore:

- examples/loop_run.py
- app/state_engine.py
- runtime/agent_loop.py
- runtime/adaptive_bindu.py
- runtime/transition_memory.py

---

### Experimental runtime

Run:

PYTHONPATH=. python examples/experimental_loop.py

This activates:

- field (environment)
- roles (classes)
- vitality economy
- adaptive selection

Main files:

- runtime_experimental/field_engine.py
- runtime_experimental/agent_loop.py
- runtime_experimental/role_transaction.py
- runtime_experimental/vitality_engine.py
- runtime_experimental/lab_bridge.py

---

## Stable Runtime Flow

state  
→ agent  
→ metrics  
→ bindu  
→ decision  
→ update  
→ memory  

---

## Experimental Runtime Flow

state  
→ field  
→ class candidates  
→ role logic  
→ decision  
→ vitality update  
→ state update  

---

## State Language

State vector:

- pressure
- flow
- structure
- balance
- law
- future

Metrics:

- shadow
- coherence
- target_fit
- vitality

---

## Classes (Experimental)

- TANK → stability
- ARCHER → direction
- MAGE → transformation
- HEALER → recovery
- ASSASSIN → anti-stagnation

---

## Why runtime_experimental exists

To allow evolution of the system without breaking stable runtime.

It is:

- adaptive
- experimental
- environment-driven

---

## Philosophy

This system does not optimize probability.

It selects survivable state transitions.

---

## One-line

GitCube OS turns structural meaning into runtime behavior.

---

## One-line (Experimental)

runtime_experimental is a living field engine with roles, phases, and vitality.
