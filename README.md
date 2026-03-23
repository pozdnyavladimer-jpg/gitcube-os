# GitCube OS

GitCube OS is not a model.

It is an operating system for pattern evolution:
a framework for evaluating, compressing, and promoting adaptive structures under pressure.

## Core Idea

The system does not optimize for maximum safety or maximum novelty.

It optimizes for sustainable adaptability.

## Repository Map

- `docs/` → laws and architecture
- `core/` → kernel logic
- `runtime/` → execution loop
- `examples/` → minimal runnable entry points
- `tests/` → stability checks

## Related Repositories

- `geometric-state-navigator` → state engine (GSL)
- `gitcube-lab` → experimental sandbox
- `gitcube-os` → stabilized operating layer

## Quick Start

1. Read `START_HERE.md`
2. Run:

```bash
python examples/simple_loop.py
```
One-line Summary
GitCube OS decides what patterns deserve to survive.
---

# 3. Встав `START_HERE.md`

```md
# START HERE
```

This repository is the OS layer of the GitCube system.

## What to do first

1. Read:
   - `docs/ARCHITECTURE.md`

2. Run:
   - `python examples/simple_loop.py`

3. Explore:
   - `core/state.py`
   - `core/evaluation.py`
   - `runtime/agent_loop.py`

## Mental Model

Lab explores.  
OS stabilizes.  
Memory preserves.

## What this repo does

This repo takes pattern logic out of experimental notebooks and moves it into a stable executable layer.

It is designed to answer:

- what state is the system in
- whether that state is healthy
- what transition is allowed next
- what should be retained
# GitCube OS

GitCube OS is the runtime execution layer of the GitCube system.

It does not define meaning.

It enforces it.

---

## 🔧 What OS does

- executes agent loops  
- applies bindu decisions  
- controls memory  
- performs rerouting  
- applies environment pressure  

---

## 🧿 Bindu

Bindu is implemented in runtime:

- COMMIT → update state + memory  
- SOFT_COMMIT → conditional update  
- REJECT → reroute  
- REROUTE → alternative agent  

---

## 🔁 Execution Loop

1. select agent  
2. compute metrics  
3. apply bindu  
4. update or reject  
5. reroute if needed  
6. write memory  

---

## 🧠 Memory

OS enforces:

- only stable states persist  
- rejected states are discarded  

---

## 🌍 Environment

Environment modifies:

- metric weighting  
- selection pressure  

But does NOT redefine meaning.

---

## 🔗 System Architecture

GitCube OS is part of a 3-layer system:

- GitCube Lab → experiments  
- Geometry Navigator → meaning  
- GitCube OS → execution (this repo)  

Flow:

Lab → Navigator → OS  

---

## ⚡ One-line

OS executes decisions defined by Navigator and validated through runtime survival.
