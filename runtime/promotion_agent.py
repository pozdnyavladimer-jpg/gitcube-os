from typing import Dict


def evaluate_promotion(
    repo_type: str,
    idea_status: str,
    cube_validation: Dict[str, object],
) -> Dict[str, object]:
    """
    Decide whether an idea should stay, promote, execute, or reject.
    """

    is_stable = cube_validation.get("is_stable", False)
    is_crystal = cube_validation.get("is_crystal", False)
    fit_score = cube_validation.get("fit_score", 0.0)
    shadow_pressure = cube_validation.get("shadow_pressure", 1.0)

    # Hard reject
    if shadow_pressure > 0.45:
        return {
            "decision": "reject",
            "reason": "shadow_too_high",
            "next_stage": "lab",
        }

    # Lab -> Navigator
    if repo_type == "lab":
        if fit_score >= 0.60:
            return {
                "decision": "promote",
                "reason": "candidate_has_signal",
                "next_stage": "navigator",
            }
        return {
            "decision": "stay",
            "reason": "needs_more_experiment",
            "next_stage": "lab",
        }

    # Navigator -> OS
    if repo_type == "navigator":
        if idea_status == "canonical" and is_stable:
            return {
                "decision": "promote",
                "reason": "canonical_and_stable",
                "next_stage": "os",
            }
        if is_stable:
            return {
                "decision": "refine",
                "reason": "stable_but_not_canonical",
                "next_stage": "navigator",
            }
        return {
            "decision": "hold",
            "reason": "not_ready_for_runtime",
            "next_stage": "navigator",
        }

    # OS execution state
    if repo_type == "os":
        if is_crystal:
            return {
                "decision": "stabilize",
                "reason": "crystal_state",
                "next_stage": "memory",
            }
        if is_stable:
            return {
                "decision": "execute",
                "reason": "runtime_stable",
                "next_stage": "os",
            }
        return {
            "decision": "reroute",
            "reason": "runtime_unstable",
            "next_stage": "feedback",
        }

    return {
        "decision": "unknown",
        "reason": "unknown_context",
        "next_stage": "unknown",
    }
