from app.orchestration.execution_loop import run_loop

if __name__ == "__main__":
    print(run_loop(max_cycles=5, refresh_first=True, cooldown_seconds=900))
