from runtime_experimental.object_store import add_object

task = {
    "type": "task",
    "title": "MAGE: Repair package structure (forced)",
    "origin": "manual_inject",
    "status": "open",
    "kind": "task",
    "intensity": 0.9,
    "novelty": 0.8,
    "meta_key": "force_structural_task",
    "payload": {
        "problem": "missing_init_group",
        "paths": ["runtime_experimental", "core"],
        "priority": "high",
        "executor_hint": "MAGE"
    },
    "resonance_vector": {
        "pressure": 0.7,
        "flow": 0.2,
        "structure": 0.1,
        "balance": 0.3,
        "law": 0.2,
        "future": 0.8
    }
}

add_object(task)
print("TASK_INJECTED")
