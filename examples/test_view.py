from app.state_engine import StateEngine
from app.view_model import build_view_model

engine = StateEngine()

print("\n=== VIEW MODEL TEST ===\n")

for _ in range(3):
    result = engine.step()
    view = build_view_model(result)

    print("current:", view["current"])
    print("decision:", view["decision"]["decision"])
    print("nodes:", len(view["nodes"]))
    print("edges:", len(view["edges"]))
    print("memory:", view["memory"])
    print()
