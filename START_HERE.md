# START HERE

This repository is the OS layer of the GitCube system.

---

## What to do first

1. Read:
   docs/ARCHITECTURE.md

2. Run:

    python examples/simple_loop.py

3. Then explore:

- examples/loop_run.py
- runtime/agent_loop.py
- runtime/adaptive_bindu.py
- runtime/memory_control.py
- runtime/agent_learning.py

---

## Minimal Mental Model

Think of the system as:

state → agents → metrics → filters → decision → memory → adaptation

Each step modifies what is possible next.

---

## Key Files

Core logic:

- core/state.py
- core/topological_filter.py

Runtime:

- runtime/agent_loop.py
- runtime/adaptive_bindu.py
- runtime/memory_control.py
- runtime/agent_learning.py

Integration:

- examples/loop_run.py

---

## What To Look For During Execution

Run:

    python examples/loop_run.py

Watch for:

- selected_agent
- agent_bias
- memory_control
- bindu decision
- threshold changes

These logs show how the system adapts.

---

## Interpreting Output

- many SOFT_COMMIT → system is uncertain  
- many REJECT → thresholds are tightening  
- COMMIT appears → stable trajectory  

---

## Important

Do not treat this as a standard ML system.

There is:

- no loss function  
- no gradient descent  
- no probability sampling  

Instead:

- structure replaces probability  
- filtering replaces scoring  
- survival replaces optimization  

---

## Execution Logic (Simple)

1. select agent  
2. compute metrics  
3. apply topological filter  
4. apply bindu decision  
5. update or reject state  
6. write memory  
7. adapt thresholds  

---

## What this repo does

This repo takes pattern logic out of experimental notebooks
and moves it into a stable executable layer.

It answers:

- what state the system is in  
- whether that state is valid  
- what transition is allowed next  
- what should be retained  

---

## Next Step

Once comfortable:

- modify adaptive_bindu.py
- modify memory_control.py
- observe agent_learning.py

Run again and compare behavior.

---

## One-line

This system learns by restricting what is allowed to happen next.

---


## Experimental Features

Recent updates introduce:

- class-based agents
- survival economy (vitality)
- ecology penalties
- class interaction effects

These are currently tested separately and may not be fully active in all execution paths.
