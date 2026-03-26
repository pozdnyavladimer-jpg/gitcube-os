from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


StateTuple = Tuple[int, int, int]


@dataclass
class VisionFrame:
    current: StateTuple
    coarse: Dict[str, float]
    mid: Dict[str, float]
    fine: Dict[str, float]
    vibration_phase: float
    blink_gate: bool
    anomaly: float


class FractalVision:
    """
    FractalVision:
    - zoom_levels: бачить стан на 3 рівнях
    - vibrate: мікросканування, щоб не залипати
    - blink: періодичне очищення кадру
    - anomaly_score: оцінка порушення симетрії / шуму
    """

    def __init__(self, blink_period: int = 7, vibration_step: float = 0.35):
        self.blink_period = blink_period
        self.vibration_step = vibration_step
        self.phase = 0.0

    def state_energy(self, state: StateTuple) -> int:
        return sum(state)

    def state_symmetry(self, state: StateTuple) -> float:
        """
        Груба симетрія:
        - всі 3 однакові -> 1.0
        - 2 однакові -> 0.66
        - все різне тут неможливо для бінарного 3D стану
        """
        ones = sum(state)
        if ones in (0, 3):
            return 1.0
        return 2.0 / 3.0

    def zoom_levels(
        self,
        current: StateTuple,
        history: List[StateTuple],
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        """
        coarse  -> загальна форма потоку
        mid     -> локальна поведінка
        fine    -> поточний вузол
        """
        recent = history[-5:] if history else [current]
        energies = [self.state_energy(s) for s in recent]
        symmetries = [self.state_symmetry(s) for s in recent]

        coarse = {
            "avg_energy": round(sum(energies) / len(energies), 3),
            "avg_symmetry": round(sum(symmetries) / len(symmetries), 3),
            "history_span": float(len(recent)),
        }

        if len(recent) >= 2:
            transitions = []
            for i in range(1, len(recent)):
                dist = sum(a != b for a, b in zip(recent[i - 1], recent[i]))
                transitions.append(dist)
            avg_jump = sum(transitions) / len(transitions)
        else:
            avg_jump = 0.0

        mid = {
            "local_jump_avg": round(avg_jump, 3),
            "local_energy": float(self.state_energy(current)),
            "local_symmetry": round(self.state_symmetry(current), 3),
        }

        fine = {
            "bit_x": float(current[0]),
            "bit_y": float(current[1]),
            "bit_z": float(current[2]),
        }

        return coarse, mid, fine

    def vibrate(self, value: float) -> float:
        """
        Невелике мікросканування, щоб уникати 'мертвого' сприйняття.
        """
        self.phase += self.vibration_step
        return value + 0.05 * math.sin(self.phase)

    def blink(self, step: int, metrics: Dict[str, float]) -> Tuple[bool, Dict[str, float]]:
        """
        Blink:
        - раз на blink_period кроків робимо легке очищення шуму
        - зменшуємо shadow / дрібний noise
        """
        gate = (step % self.blink_period == 0)

        cleaned = dict(metrics)
        if gate:
            shadow = cleaned.get("shadow", 0.0)
            coherence = cleaned.get("coherence", 0.0)

            cleaned["shadow"] = max(0.0, round(shadow * 0.85, 6))
            cleaned["coherence"] = min(1.0, round(coherence * 1.01, 6))

        return gate, cleaned

    def anomaly_score(
        self,
        current: StateTuple,
        metrics: Dict[str, float],
        history: List[StateTuple],
    ) -> float:
        """
        Аномалія росте, якщо:
        - низька симетрія
        - великий shadow
        - різкі стрибки в недавній історії
        """
        symmetry_penalty = 1.0 - self.state_symmetry(current)
        shadow_penalty = metrics.get("shadow", 0.0)

        jump_penalty = 0.0
        if history:
            prev = history[-1]
            jump_penalty = sum(a != b for a, b in zip(prev, current)) / 3.0

        anomaly = (
            0.4 * symmetry_penalty
            + 0.4 * shadow_penalty
            + 0.2 * jump_penalty
        )
        return round(anomaly, 6)

    def observe(
        self,
        step: int,
        current: StateTuple,
        metrics: Dict[str, float],
        history: List[StateTuple],
    ) -> VisionFrame:
        """
        Повний кадр сприйняття.
        """
        blink_gate, cleaned_metrics = self.blink(step, metrics)
        coarse, mid, fine = self.zoom_levels(current, history)

        coarse["avg_energy"] = round(self.vibrate(coarse["avg_energy"]), 6)
        mid["local_jump_avg"] = round(self.vibrate(mid["local_jump_avg"]), 6)

        anomaly = self.anomaly_score(current, cleaned_metrics, history)

        return VisionFrame(
            current=current,
            coarse=coarse,
            mid=mid,
            fine=fine,
            vibration_phase=round(self.phase, 6),
            blink_gate=blink_gate,
            anomaly=anomaly,
        )
