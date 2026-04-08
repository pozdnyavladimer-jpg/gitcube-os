import os
import time

STEPS = 5

for i in range(STEPS):
    os.system("PYTHONPATH=. python runtime_experimental/os_sync.py")
    os.system("python actor_executor.py")
    time.sleep(2)

