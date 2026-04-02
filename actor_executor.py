from v_bridge import VBridge

bridge = VBridge()

def act():
    signal = bridge.get_signal()

    if not signal:
        return

    if signal["action"] == "EXECUTE":
        print("ACTOR EXECUTING:", signal)

        # імітація дії
        bridge.update_flower({
            "structure": 0.9,
            "law": 0.8
        })

        bridge.set_signal("ACTOR", "CORE", "DONE", signal["bond"])

if __name__ == "__main__":
    act()
