from app.state_engine import StateEngine
from app.view_model import build_view_model

engine = StateEngine()


for _ in range(3):
    result = engine.step()
    view = build_view_model(result)

