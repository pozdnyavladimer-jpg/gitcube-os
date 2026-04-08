from app.state_engine import StateEngine

engine = StateEngine(mode="balanced")


for _ in range(5):
    result = engine.step()
