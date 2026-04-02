from v_bridge import VBridge
import time


def main():
    bridge = VBridge()

    state = bridge.read_state()
    signal = state.get("signal", {})

    action = signal.get("action", "WAIT")

    print("[ACTOR] action:", action)

    if action == "BUILD":
        print("[ACTOR] building...")
        bridge.update("flower", {"structure": 0.8})

    elif action == "STABILIZE":
        print("[ACTOR] stabilizing...")
        bridge.update("flower", {"balance": 0.8})

    # reset
    bridge.update("signal", {"action": "WAIT"})


if __name__ == "__main__":
    main()
