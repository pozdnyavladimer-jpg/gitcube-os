# AUTO-GENERATED BRIDGE REGISTRY

from pathlib import Path
import importlib

def load_bridges():
    bridges = []

    base = Path(__file__).parent

    for f in base.glob("*_adapter.py"):
        name = f.stem
        module_name = f"bridges.{name}"

        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, "connect"):
                bridges.append(mod.connect())
        except Exception as e:
            bridges.append({
                "bridge": name,
                "error": str(e)
            })

    return bridges
