# AUTO-GENERATED BRIDGE

"""
Bridge: core → app
"""

try:
    import app
except Exception:
    app = None

def connect():
    return {
        "bridge": "core_to_app",
        "source": "core",
        "target": "app",
        "target_available": app is not None,
    }
