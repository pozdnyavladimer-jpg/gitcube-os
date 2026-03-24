def evaluate_state(state: dict) -> dict:
    score = 0.0
    issues = []

    coherence = state.get("balance", 0)
    structure = state.get("structure", 0)
    law = state.get("law", 0)
    future = state.get("future", 0)

    # --- coherence ---
    if coherence < 0.3:
        issues.append("low_coherence")
    else:
        score += coherence

    # --- structure ---
    if structure < 0.3:
        issues.append("weak_structure")
    else:
        score += structure

    # --- law ---
    if law < 0.2:
        issues.append("no_constraints")
    else:
        score += law

    # --- exploration ---
    if future > 0.8:
        issues.append("too_chaotic")

    return {
        "score": round(score, 3),
        "issues": issues,
        "status": "stable" if score > 1.0 else "unstable"
    }


def suggest_fix(state: dict, issues: list) -> dict:
    new_state = dict(state)

    if "low_coherence" in issues:
        new_state["balance"] += 0.2

    if "weak_structure" in issues:
        new_state["structure"] += 0.2

    if "no_constraints" in issues:
        new_state["law"] += 0.2

    if "too_chaotic" in issues:
        new_state["future"] -= 0.2

    return new_state
