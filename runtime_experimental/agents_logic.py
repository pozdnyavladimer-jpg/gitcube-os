from typing import Dict, Any, List, Optional


def tank_guard(state: Dict[str, float], action_history: List[str]) -> Optional[Dict[str, Any]]:
    structure = float(state.get("structure", 0.0))
    balance = float(state.get("balance", 0.0))

    recent = [str(x) for x in action_history[-5:]]
    tank_count = recent.count("EMERGENCY_STABILIZE")

    if structure < 0.20 and tank_count < 3:
        return {
            "role": "TANK",
            "action": "EMERGENCY_STABILIZE",
            "new_mode": "stability_boost",
            "reason": "structure_too_low",
            "priority": 100,
        }

    if balance < 0.15 and tank_count < 3:
        return {
            "role": "TANK",
            "action": "REBALANCE",
            "new_mode": "stability_boost",
            "reason": "balance_too_low",
            "priority": 90,
        }

    return None


def mage_anti_stall(action_history: List[str]) -> Optional[Dict[str, Any]]:
    if len(action_history) < 3:
        return None

    last_actions = [str(x) for x in action_history[-3:]]

    if len(set(last_actions)) == 1:
        return {
            "role": "MAGE",
            "action": "FORCE_MODE_SHIFT",
            "new_mode": "law_boost",
            "reason": f"loop_detected:{last_actions[0]}",
            "priority": 80,
            "repair_state": True,
        }

    return None


def archer_boost(state: Dict[str, float]) -> Optional[Dict[str, Any]]:
    flow = float(state.get("flow", 0.0))
    pressure = float(state.get("pressure", 0.0))

    if flow < 0.25 and pressure < 0.60:
        return {
            "role": "ARCHER",
            "action": "INCREASE_FLOW",
            "new_mode": "flow_boost",
            "reason": "low_flow",
            "priority": 60,
        }

    return None


def explorer_novelty(vitality_history: List[float]) -> Optional[Dict[str, Any]]:
    if len(vitality_history) < 4:
        return None

    recent = [float(x) for x in vitality_history[-4:]]
    span = max(recent) - min(recent)

    if span < 0.02:
        return {
            "role": "EXPLORER",
            "action": "EXPLORE_NEW_ROUTE",
            "new_mode": "discovery",
            "reason": "vitality_plateau",
            "priority": 40,
        }

    return None


def choose_coordination_effect(
    *,
    state: Dict[str, float],
    action_history: List[str],
    vitality_history: List[float],
) -> Dict[str, Any]:
    effects = []

    tank = tank_guard(state, action_history)
    if tank:
        effects.append(tank)

    mage = mage_anti_stall(action_history)
    if mage:
        effects.append(mage)

    archer = archer_boost(state)
    if archer:
        effects.append(archer)

    explorer = explorer_novelty(vitality_history)
    if explorer:
        effects.append(explorer)

    if not effects:
        return {
            "role": "NONE",
            "action": "STABLE",
            "new_mode": None,
            "reason": "no_override",
            "priority": 0,
        }

    effects.sort(key=lambda x: int(x.get("priority", 0)), reverse=True)
    return effects[0]
