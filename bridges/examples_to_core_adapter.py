# AUTO-GENERATED BRIDGE

"""
Bridge: examples → core
"""

try:
    import core
except Exception:
    core = None

def connect():
    return {
        "bridge": "examples_to_core",
        "source": "examples",
        "target": "core",
        "target_available": core is not None,
    }
