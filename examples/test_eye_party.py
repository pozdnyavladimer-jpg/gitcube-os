from runtime.v_eye_profile import evaluate_party

SCENARIOS = [
    {
        "name": "clean_signal",
        "content": "clean",
        "shadow": 0.1,
        "coherence": 0.92,
        "anomaly": 0.08,
        "trajectory": 0.2,
    },
    {
        "name": "chaos_load",
        "content": "chaos",
        "shadow": 0.82,
        "coherence": 0.48,
        "anomaly": 0.35,
        "trajectory": 0.4,
    },
    {
        "name": "prediction",
        "content": "moving",
        "shadow": 0.28,
        "coherence": 0.74,
        "anomaly": 0.14,
        "trajectory": 0.95,
    },
]


for s in SCENARIOS:

    results = evaluate_party(
        s["content"],
        s["shadow"],
        s["coherence"],
        s["anomaly"],
        s["trajectory"],
    )

    for r in results:

