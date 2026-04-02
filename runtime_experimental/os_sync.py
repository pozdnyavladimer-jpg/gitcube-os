from v_bridge import VBridge
import random


def main():
    bridge = VBridge()

    state = bridge.read_state()
    flower = state.get("flower", {})
    meta = state.get("meta", {})

    step = meta.get("step", 0)
    vitality = meta.get("vitality", 0.42)

    # simple logic
    pressure = random.uniform(0.3, 0.9)
    flow = 1.0 - pressure

    decision = "REJECT"
    action = "WAIT"

    if flow > 0.7:
        decision = "COMMIT"
        action = "BUILD"
    elif flow > 0.5:
        decision = "SOFT_COMMIT"
        action = "STABILIZE"

    # update flower
    bridge.update("flower", {
        "pressure": round(pressure, 3),
        "flow": round(flow, 3)
    })

    # update meta
    bridge.update("meta", {
        "step": step + 1,
        "vitality": round(vitality + (flow - pressure) * 0.1, 3)
    })

    # update signal
    bridge.update("signal", {
        "action": action,
        "decision": decision
    })

    print("CORE STEP:", step, "| decision:", decision, "| action:", action)


if __name__ == "__main__":
    main()
