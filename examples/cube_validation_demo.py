from core.cube_validator import evaluate_state, suggest_fix


def demo():
    state = {
        "pressure": 0.3,
        "flow": 0.4,
        "structure": 0.2,
        "balance": 0.2,
        "law": 0.1,
        "future": 0.9,
    }


    result = evaluate_state(state)

    fixed = suggest_fix(state, result["issues"])


if __name__ == "__main__":
    demo()
