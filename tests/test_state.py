from core.state import normalize_state


def test_normalize_state_sums_to_one():
    v = normalize_state(
        {
            "pressure": 1,
            "flow": 1,
            "structure": 1,
            "balance": 1,
            "law": 1,
            "future": 1,
        }
    )
    total = sum(v.values())
    assert abs(total - 1.0) < 1e-9
