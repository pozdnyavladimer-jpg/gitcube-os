from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory
from runtime.bindu import bindu_decision
from runtime.reroute import choose_next_agent
from runtime.compression import compress_memory
from runtime.environment_score import apply_environment_to_score
from runtime.env_select import get_environment


def run_episode(steps=5, environment_name="balanced"):
    state = default_state()
    memory = EpisodeMemory()
    env = get_environment(environment_name)

    print("=== START EPISODE ===")
    print(f"environment: {env.name}")

    for step in range(steps):
        print(f"\n--- step {step} ---")

        _, results = choose_best_agent(state)

        ranked = []
        for name, data in results.items():
            env_score = apply_environment_to_score(data["metrics"], env)
            ranked.append((name, env_score, data))

        ranked.sort(key=lambda x: x[1], reverse=True)

        best = ranked[0][0]
        best_data = ranked[0][2]
        metrics = best_data["metrics"]

        bindu = bindu_decision(metrics)

        print(f"selected: {best}")
        print(f"env_score: {ranked[0][1]}")
        print(f"metrics: {metrics}")
        print(f"bindu: {bindu}")

        if bindu["decision"] == "COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="accepted",
            )
            state = best_data["state"]
            continue

        if bindu["decision"] == "SOFT_COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="soft",
            )
            state = best_data["state"]
            continue

        print("REJECTED -> trying reroute")

        reroute_name, reroute_data = choose_next_agent(results, best, env=env)
        reroute_metrics = reroute_data["metrics"]
        reroute_bind = bindu_decision(reroute_metrics)
        reroute_env_score = apply_environment_to_score(reroute_metrics, env)

        print(f"reroute_selected: {reroute_name}")
        print(f"reroute_env_score: {reroute_env_score}")
        print(f"reroute_metrics: {reroute_metrics}")
        print(f"reroute_bind: {reroute_bind}")

        if reroute_bind["decision"] == "COMMIT":
            memory.add(
                step=step,
                agent=reroute_name,
                metrics=reroute_metrics,
                state=reroute_data["state"].to_dict(),
                status="accepted",
            )
            state = reroute_data["state"]
        elif reroute_bind["decision"] == "SOFT_COMMIT":
            memory.add(
                step=step,
                agent=reroute_name,
                metrics=reroute_metrics,
                state=reroute_data["state"].to_dict(),
                status="soft",
            )
            state = reroute_data["state"]
        else:
            print("REROUTE REJECTED -> state not updated")

    print("\n=== FINAL STATE ===")
    print(state.to_dict())

    print("\n=== MEMORY SUMMARY ===")
    print(memory.summary())

    print("\n=== COMPRESSED MEMORY ===")
    print(compress_memory(memory))


if __name__ == "__main__":
    run_episode(steps=5, environment_name="balanced")
