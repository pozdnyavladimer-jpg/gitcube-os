from runtime.v_pair_fusion import evaluate_all_pairs

SCENARIOS = [
    {
        "name": "clean",
        "shadow": 0.1,
        "coherence": 0.9,
        "anomaly": 0.1,
        "trajectory": 0.2,
    },
    {
        "name": "chaos",
        "shadow": 0.8,
        "coherence": 0.4,
        "anomaly": 0.3,
        "trajectory": 0.4,
    },
    {
        "name": "prediction",
        "shadow": 0.3,
        "coherence": 0.7,
        "anomaly": 0.1,
        "trajectory": 0.95,
    },
]


for s in SCENARIOS:

    results = evaluate_all_pairs(
        "test",
        s["shadow"],
        s["coherence"],
        s["anomaly"],
        s["trajectory"],
    )

    for r in results[:5]:

