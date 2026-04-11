from runtime_experimental.object_store import add_object

def seed_mage_task():
    task = {
        "type": "task",
        "title": "MAGE: Structural expansion seed",
        "origin": "manual_seed",
        "status": "open",
        "kind": "task",
        "intensity": 0.85,
        "novelty": 0.9,
        "payload": {
            "problem": "missing_init_group",
            "paths": ["runtime_experimental", "apps", "core"],
            "priority": "high",
            "executor_hint": "MAGE"
        },
        "resonance_vector": {
            "pressure": 0.7,
            "flow": 0.3,
            "structure": 0.2,
            "balance": 0.3,
            "law": 0.25,
            "future": 0.9
        },
        "meta_key": "manual_mage_seed"
    }

    add_object(task)
    print("MAGE SEED CREATED")

if __name__ == "__main__":
    seed_mage_task()
