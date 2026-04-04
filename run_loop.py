import os
import time

STEPS = 5

for i in range(STEPS):
    print(f"\n=== LOOP {i+1}/{STEPS} START ===")
    os.system("PYTHONPATH=. python runtime_experimental/os_sync.py")
    os.system("python actor_executor.py")
    print(f"=== LOOP {i+1}/{STEPS} END ===\n")
    time.sleep(2)

print("DONE")
