# GitCube OS — Architecture

GitCube OS is a layered execution system.

It transforms abstract structure into runtime behavior.

---

## 1. Global Structure

The system is divided into 3 layers:

1. Lab Layer  
2. Navigator Layer  
3. OS Layer  

Flow:

Lab → Navigator → OS

---

## 2. OS Layer (This Repo)

GitCube OS is responsible for:

- execution
- validation
- decision making
- adaptive control

It answers:

- what state is valid
- what transition is allowed
- what survives

---

## 3. Internal Layers

Inside GitCube OS:

### core/

Pure logic:

- state definition
- normalization
- metrics

Files:

- state.py
- evaluation.py

---

### runtime/

Stable execution engine:

- agent loop
- bindu logic
- transition control
- memory

This layer is deterministic and safe.

---

### runtime_experimental/

Adaptive field layer:

- environment (field)
- class dynamics
- vitality system
- role transactions

This layer introduces:

- non-linear behavior
- adaptive priorities
- ecological dynamics

---

### app/

High-level orchestration:

- state engine
- system coordination

---

### examples/

Entry points:

- simple_loop.py → stable
- experimental_loop.py → adaptive

---

## 4. Execution Models

### Stable Model

state  
→ metrics  
→ decision  
→ update  
→ memory  

This is a closed deterministic loop.

---

### Experimental Model

state  
→ field  
→ class selection  
→ role interaction  
→ decision  
→ vitality update  
→ state update  

This is a dynamic adaptive loop.

---

## 5. Core Concepts

### State

6-dimensional vector:

- pressure
- flow
- structure
- balance
- law
- future

---

### Metrics

Derived values:

- shadow → instability / pressure
- coherence → alignment
- target_fit → goal alignment
- vitality → energy / survival

---

### Bindu

Decision threshold:

- determines commit vs reject
- adapts over time

---

### Field (Experimental)

Environment that modifies behavior.

Examples:

- CRISIS
- FLOW
- STAGNATION
- REFRACTORY

---

### Classes (Experimental)

Behavior roles:

- TANK → stabilize
- ARCHER → act
- MAGE → transform
- HEALER → restore
- ASSASSIN → disrupt

---

## 6. System Evolution

The system evolves in layers:

1. static validation
2. adaptive thresholds
3. environment influence
4. role-based behavior
5. full ecosystem

---

## 7. Design Principle

The system is not probabilistic.

It is:

- constraint-driven
- state-based
- survival-oriented

---

## 8. Future Direction

Planned:

- memory-aware field
- graph-based field input
- attractor dynamics
- long-term vitality control
- navigator integration

---

## 9. Summary

GitCube OS is an execution engine.

It converts structure into behavior.

---

## One-line

Architecture = structure → decision → survival
