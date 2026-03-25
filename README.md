# GitCube OS

GitCube OS is not a model.

It is an operating system for pattern evolution:
a framework for evaluating, compressing, and promoting adaptive structures under pressure.

---

## Core Idea

The system does not optimize for maximum safety or maximum novelty.

It optimizes for sustainable adaptability.

---

## Repository Map

- docs/ → laws and architecture
- core/ → kernel logic
- runtime/ → execution loop
- examples/ → runnable entry points
- tests/ → stability checks

---

## Related Repositories

- geometric-state-navigator → state engine
- gitcube-lab → experimental sandbox
- gitcube-os → execution layer (this repo)

---

## Quick Start

1. Read START_HERE.md  
2. Run:

    python examples/simple_loop.py

3. Then explore:

- examples/loop_run.py
- runtime/agent_loop.py
- runtime/adaptive_bindu.py
- runtime/memory_control.py
- runtime/agent_learning.py

---

## Current System Capabilities

The OS layer currently includes:

- adaptive bindu thresholds
- memory-driven decision control
- topological filtering
- agent selection and biasing
- neuro state modulation
- rerouting logic

---

## Execution Flow (Detailed)

At runtime, the system follows this sequence:

1. agent selection  
2. metric evaluation  
3. topological filtering  
4. memory-derived control  
5. adaptive bindu decision  
6. state update or rejection  
7. memory write  
8. neuro modulation update  

This loop forms a closed adaptive cycle.

---

## Adaptive Behavior

The system evolves during execution through:

- dynamic threshold adjustment (bindu)
- memory feedback loops
- agent performance biasing
- topological validation constraints

This allows the OS to shift from static execution to adaptive regulation.

---

## Visual Projection

The OS can optionally project internal state into visual form:

- mood
- palette
- composition
- texture
- intensity
- prompt

Handled via:

- core/projector.py
- runtime/render_adapter.py

---

## Notes

- deterministic structure, adaptive thresholds  
- memory is session-based unless persisted  
- topological filter validates structure  

---

## Philosophy

GitCube OS is not trying to generate answers.

It decides:

- which structures are valid  
- which transitions are allowed  
- which trajectories survive  

---

## System Architecture

GitCube OS is part of a 3-layer system:

- GitCube Lab → experiments  
- Geometry Navigator → meaning  
- GitCube OS → execution  

Flow:

Lab → Navigator → OS

---

## One-line Summary

GitCube OS decides what patterns deserve to survive.

---

## One-line (Strict)

GitCube OS enforces survival through adaptive structural validation.

---

## 🔬 Experimental Layer (Current Implementation)

The current implementation introduces a discrete binary state space:

Each state:
(0,0,0) → (1,1,1)

Transitions are constrained:
only local moves are allowed.

---

## 🧊 Binary State Cube

The system operates inside a 3D binary cube.

- nodes → states
- edges → valid transitions
- invalid jumps are blocked

---

## 🤖 Agent Modes

We tested multiple behavioral modes:

- balanced
- planner-biased
- explorer-biased
- stabilizer-biased

---

## 📊 Results

Experiment (60 steps):

- stabilizer-biased → max stability (but stagnation)
- planner-biased → best balance
- explorer-biased → high exploration, low stability
- balanced → neutral baseline

Conclusion:

Planner-biased mode provides the most устойчивий adaptive behavior.

---

## 🔁 Additional Mechanics

New system features:

- anti-stuck penalty
- curiosity bonus
- adaptive temperature (reject-driven)
- transition memory feedback

---

## 🧪 Run Experiment

PYTHONPATH=. python examples/compare_modes.py

---

## 🧠 Interpretation

The system confirms:

- pure stability leads to collapse (no movement)
- pure exploration leads to chaos
- structured bias leads to устойчивість

---

## 🔭 Next Direction

Planned extensions:

- image-space navigation
- latent geometry mapping
- adaptive visual projection
---
