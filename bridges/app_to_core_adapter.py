# AUTO-GENERATED BRIDGE

"""
Bridge: app → core
"""

try:
    import core
except Exception:
    core = None

def connect():
    return {
        "bridge": "app_to_core",
        "source": "app",
        "target": "core",
        "target_available": core is not None,
    }
