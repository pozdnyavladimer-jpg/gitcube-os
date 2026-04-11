START HERE

This repo has two paths:

- Stable Runtime
- Experimental Runtime

---

1. Stable Runtime

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

2. Experimental Runtime

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

🧠 GitCube OS Runtime (Main System)

Run:

./run.sh

This activates:

- task graph (objects.json)
- agent routing (ARCHER / MAGE / TANK / HEALER)
- memory bias
- GitHub integration

---

🔁 Behavior Loop

analyze → generate tasks → route → execute → learn

---

👀 What to watch in logs

- SELECTED TASK
- PRIMARY_AGENT / SUPPORT_AGENT
- PAIR_REASON
- TANK_POLICY
- PUBLISH

---

🧭 Mental Model

Stable:

state → decision → update

Experimental:

state → field → class → decision → vitality → update

GitCube OS:

state → field → policy → routing → action → memory

---

⚠️ Important

Do not mix experimental into stable too early.

runtime/ = stable  
runtime_experimental/ = evolving  

---

🔑 Setup

Create ".env" file:

GITHUB_TOKEN=...
GITHUB_REPO=...

---

▶️ Run

./run.sh

---

🔄 Auto loop

./run_loop.sh

---

💡 One-line

GitCube OS executes adaptive state logic.

---

💡 One-line (Field)

GitCube OS turns code into a self-organizing system.
