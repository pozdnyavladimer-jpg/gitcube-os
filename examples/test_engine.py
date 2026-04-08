from app.state_engine import StateEngine

engine = StateEngine()


for _ in range(5):
    result = engine.step()

