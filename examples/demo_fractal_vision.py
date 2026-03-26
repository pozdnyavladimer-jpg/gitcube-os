from runtime.fractal_vision import FractalVision

history = [
    (1, 1, 1),
    (1, 0, 1),
    (1, 0, 0),
    (1, 0, 1),
]

metrics = {
    "shadow": 0.12,
    "coherence": 0.91,
    "target_fit": 0.53,
    "vitality": 0.44,
}

vision = FractalVision(blink_period=4)

for step in range(1, 9):
    current = history[-1]
    frame = vision.observe(
        step=step,
        current=current,
        metrics=metrics,
        history=history[:-1],
    )

    print(f"\n--- step {step} ---")
    print("current:", frame.current)
    print("coarse:", frame.coarse)
    print("mid:", frame.mid)
    print("fine:", frame.fine)
    print("blink_gate:", frame.blink_gate)
    print("phase:", frame.vibration_phase)
    print("anomaly:", frame.anomaly)

    # невелика симуляція руху
    if step % 2 == 0:
        history.append((1, 1, 1))
    else:
        history.append((1, 0, 1))
