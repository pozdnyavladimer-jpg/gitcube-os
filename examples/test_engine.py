from app.state_engine import StateEngine

engine = StateEngine()

print("\n=== STATE ENGINE TEST ===\n")

for _ in range(5):
    result = engine.step()

    print("step:", result["step"])
    print("agent:", result["agent"])
    print("decision:", result["decision"]["decision"])
    print("allowed:", result["transition_allowed"])
    print("memory:", result["transition_memory"])
    print("summary:", result["summary"])
    print()
