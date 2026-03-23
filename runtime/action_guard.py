from typing import Dict, List


def guard_action(
    repo_type: str,
    idea_status: str,
    requested_action: str,
    cube_validation: Dict[str, object],
    allowed_actions: List[str],
) -> Dict[str, object]:
    """
    Decide whether an action is allowed in current repo/lifecycle/cube state.
    """

    if requested_action not in allowed_actions:
        return {
            "allow": False,
            "reason": "action_not_allowed_in_repo",
            "final_action": "hold",
        }

    is_stable = cube_validation.get("is_stable", False)
    is_crystal = cube_validation.get("is_crystal", False)
    shadow_pressure = cube_validation.get("shadow_pressure", 1.0)

    # OS is the strictest layer
    if repo_type == "os":
        if requested_action == "execute" and not is_stable:
            return {
                "allow": False,
                "reason": "unstable_cube_for_execution",
                "final_action": "reroute",
            }

        if requested_action == "write_memory" and not is_stable:
            return {
                "allow": False,
                "reason": "unstable_cube_for_memory",
                "final_action": "hold",
            }

    # Navigator should not execute runtime actions
    if repo_type == "navigator":
        if requested_action in ["execute", "write_memory", "reroute"]:
            return {
                "allow": False,
                "reason": "navigator_cannot_execute_runtime",
                "final_action": "approve_for_runtime",
            }

    # Lab should not bypass canonical phase
    if repo_type == "lab":
        if requested_action in ["execute", "write_memory", "approve_for_runtime"]:
            return {
                "allow": False,
                "reason": "lab_cannot_jump_to_runtime",
                "final_action": "propose_candidate",
            }

    # Additional shadow-pressure safety
    if shadow_pressure > 0.4:
        return {
            "allow": False,
            "reason": "shadow_pressure_too_high",
            "final_action": "reroute",
        }

    # Strong signal: crystal is safe
    if is_crystal:
        return {
            "allow": True,
            "reason": "crystal_state",
            "final_action": requested_action,
        }

    return {
        "allow": True,
        "reason": "allowed",
        "final_action": requested_action,
    }
