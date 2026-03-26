from app.state_engine import StateEngine

engine = StateEngine(mode="balanced")

print("\n=== GUARD TEST ===\n")

for _ in range(30):
    result = engine.step()
    print(
        "step:", result["step"],
        "| agent:", result["agent"],
        "| decision:", result["decision"]["decision"],
        "| state:", result["cube_position"],
        "| reason:", result["decision"].get("reason", "-"),
    )
