from app.live_agent import LiveAgent

MODES = [
    "balanced",
    "planner-biased",
    "explorer-biased",
    "stabilizer-biased",
]

STEPS = 60


def run_mode(mode: str, steps: int = STEPS):
    agent = LiveAgent(mode=mode)
    packet = None

    for _ in range(steps):
        packet = agent.step()

    result = packet["result"]
    visit_counts = packet["visit_counts"]

    top_states = sorted(
        visit_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        "mode": mode,
        "steps": steps,
        "summary": result["summary"],
        "temperature": result.get("temperature"),
        "reject_streak": result.get("reject_streak"),
        "top_states": top_states,
        "last_agent": result["agent"],
        "last_decision": result["decision"]["decision"],
    }


def main():
    print("\n=== GITCUBE OS MODE COMPARISON ===\n")

    all_results = []

    for mode in MODES:
        report = run_mode(mode)
        all_results.append(report)

        print(f"--- mode: {mode} ---")
        print("steps:", report["steps"])
        print("summary:", report["summary"])
        print("temperature:", report["temperature"])
        print("reject_streak:", report["reject_streak"])
        print("last_agent:", report["last_agent"])
        print("last_decision:", report["last_decision"])
        print("top_states:", report["top_states"])
        print()

    print("=== FINAL RANKING (by stability_score) ===")
    ranked = sorted(
        all_results,
        key=lambda x: x["summary"]["stability_score"],
        reverse=True
    )
    for item in ranked:
        print(
            item["mode"],
            "-> stability:",
            item["summary"]["stability_score"],
            "| blocked:",
            item["summary"]["blocked_moves"],
            "| reject_streak:",
            item["reject_streak"],
        )


if __name__ == "__main__":
    main()
