from app.state_engine import StateEngine

engine = StateEngine(mode="balanced")

print("\n=== STATE ENGINE + FRACTAL VISION TEST ===\n")

for _ in range(5):
    result = engine.step()
    print("step:", result["step"])
    print("agent:", result["agent"])
    print("decision:", result["decision"]["decision"])
    print("current:", result["cube_position"])
    print("anomaly:", result["vision"]["anomaly"])
    print("blink:", result["vision"]["blink_gate"])
    print("phase:", result["vision"]["vibration_phase"])
    print("summary:", result["summary"])
    print()
