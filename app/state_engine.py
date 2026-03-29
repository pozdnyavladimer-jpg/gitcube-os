from typing import Dict, Any
from collections import Counter

from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.adaptive_bindu import adaptive_bindu
from runtime.binary_cube import (
    to_binary_state,
    state_to_tuple,
    transition_allowed,
)
from runtime.transition_memory import derive_transition_memory
from runtime.agent_modes import get_mode_bias
from runtime.fractal_vision import FractalVision
from runtime.perelman_guard import PerelmanGuard
from runtime.school_layer import (
    class_fatigue_penalty,
    build_school_profile,
)


class StateEngine:
    def __init__(self, mode: str = "balanced"):
        self.state = default_state()
        self.prev_tuple = None

        self.allowed_moves = 0
        self.blocked_moves = 0
        self.step_count = 0

        self.mode = mode
        self.state_visits = Counter()

        self.temperature = 1.0
        self.reject_streak = 0

        self.vision = FractalVision(blink_period=7, vibration_step=0.35)
        self.vision_history = []

        self.guard = PerelmanGuard(loop_threshold=12)

        # school / party dynamics
        self.class_history = []

    def reset(self):
        mode = self.mode
        self.__init__(mode=mode)

    def set_mode(self, mode: str):
        self.mode = mode

    def _apply_mode_bias(self, results: Dict[str, Any]) -> Dict[str, Any]:
        biases = get_mode_bias(self.mode)
        adjusted = {}

        total_visits = sum(self.state_visits.values()) + 1

        for agent_name, agent_data in results.items():
            metrics = dict(agent_data["metrics"])
            candidate_binary = to_binary_state(metrics)
            candidate_tuple = state_to_tuple(candidate_binary)

            frame = self.vision.observe(
                step=self.step_count,
                current=candidate_tuple,
                metrics=metrics,
                history=self.vision_history,
            )

            metrics["shadow"] = round(
                min(1.0, metrics.get("shadow", 0.0) + frame.anomaly * 0.25),
                6,
            )

            if frame.blink_gate:
                metrics["coherence"] = round(
                    min(1.0, metrics.get("coherence", 0.0) + 0.01),
                    6,
                )

            base_score = (
                metrics.get("coherence", 0.0)
                - metrics.get("shadow", 0.0)
                + metrics.get("target_fit", 0.0)
                + metrics.get("vitality", 0.0)
            )

            mode_bias = biases.get(agent_name, 0.0)

            repeat_count = self.state_visits.get(candidate_tuple, 0)
            repeat_penalty = round(repeat_count * 0.03, 3)

            rarity = 1.0 - (repeat_count / total_visits)
            curiosity_bonus = round(rarity * 0.15 * self.temperature, 3)

            dominant_class = agent_data.get("dominant_class", "UNKNOWN")
            fatigue_penalty = class_fatigue_penalty(dominant_class, self.class_history)

            adjusted_score = (
                base_score
                + mode_bias
                - repeat_penalty
                + curiosity_bonus
                - fatigue_penalty
            )

            adjusted[agent_name] = {
                **agent_data,
                "metrics": metrics,
                "candidate_tuple": candidate_tuple,
                "vision_frame": frame,
                "base_score": base_score,
                "mode_bias": mode_bias,
                "repeat_penalty": repeat_penalty,
                "curiosity_bonus": curiosity_bonus,
                "fatigue_penalty": fatigue_penalty,
                "adjusted_score": adjusted_score,
            }

        return adjusted

    def _update_temperature(self, decision_name: str):
        if decision_name == "REJECT":
            self.reject_streak += 1
            self.temperature = min(2.5, round(self.temperature + 0.08, 3))
        else:
            self.reject_streak = 0
            self.temperature = max(0.7, round(self.temperature - 0.03, 3))

    def _build_party_summary(self, results: Dict[str, Any], stability_score: float) -> Dict[str, Any]:
        class_votes = {
            "TANK": 0,
            "ARCHER": 0,
            "MAGE": 0,
            "HEALER": 0,
            "ASSASSIN": 0,
        }
        class_score_sum = {
            "TANK": 0.0,
            "ARCHER": 0.0,
            "MAGE": 0.0,
            "HEALER": 0.0,
            "ASSASSIN": 0.0,
        }

        for _, data in results.items():
            cls = data.get("dominant_class", None)
            if cls in class_votes:
                class_votes[cls] += 1
                class_score_sum[cls] += data.get("adjusted_score", 0.0)

        return build_school_profile(
            class_votes=class_votes,
            class_score_sum=class_score_sum,
            class_history=self.class_history,
            allowed_moves=self.allowed_moves,
            blocked_moves=self.blocked_moves,
            stability_score=stability_score,
            reject_streak=self.reject_streak,
        )

    def step(self) -> Dict[str, Any]:
        self.step_count += 1

        _, raw_results = choose_best_agent(self.state)
        results = self._apply_mode_bias(raw_results)

        best_agent = max(results, key=lambda k: results[k]["adjusted_score"])
        best_data = results[best_agent]

        metrics = best_data["metrics"]
        next_state = best_data["state"]
        current_tuple = best_data["candidate_tuple"]
        binary = to_binary_state(metrics)
        frame = best_data["vision_frame"]
        dominant_class = best_data.get("dominant_class", "UNKNOWN")

        allowed = True
        if self.prev_tuple is not None:
            allowed = transition_allowed(self.prev_tuple, current_tuple)

            if allowed:
                self.allowed_moves += 1
            else:
                self.blocked_moves += 1

        transition_memory = derive_transition_memory(
            blocked_moves=self.blocked_moves,
            allowed_moves=self.allowed_moves,
        )

        # ---- PERELMAN GUARD ----
        loop_detected, loop_state, loop_count = self.guard.detect_loop(self.vision_history)

        total = self.allowed_moves + self.blocked_moves
        stability_score = round(self.allowed_moves / total, 3) if total else 1.0
        party_summary = self._build_party_summary(results, stability_score)

        if loop_detected:
            candidates = []
            for _, data in results.items():
                candidates.append({
                    "state": data["candidate_tuple"],
                    "visits": self.state_visits.get(data["candidate_tuple"], 0),
                })

            escape_state = self.guard.force_escape(current_tuple, candidates)

            if escape_state != current_tuple:
                self.state_visits[escape_state] += 1
                self.vision_history.append(escape_state)
                self.prev_tuple = escape_state
                self.class_history.append("ASSASSIN")
                self.class_history = self.class_history[-50:]

                total = self.allowed_moves + self.blocked_moves
                stability_score = round(self.allowed_moves / total, 3) if total else 1.0
                party_summary = self._build_party_summary(results, stability_score)

                return {
                    "step": self.step_count,
                    "agent": "GUARD",
                    "mode": self.mode,
                    "temperature": self.temperature,
                    "reject_streak": self.reject_streak,
                    "vision": {
                        "current": escape_state,
                        "coarse": frame.coarse,
                        "mid": frame.mid,
                        "fine": frame.fine,
                        "vibration_phase": frame.vibration_phase,
                        "blink_gate": frame.blink_gate,
                        "anomaly": frame.anomaly,
                    },
                    "agent_scores": {
                        k: {
                            "base_score": round(v["base_score"], 3),
                            "mode_bias": round(v["mode_bias"], 3),
                            "repeat_penalty": round(v["repeat_penalty"], 3),
                            "curiosity_bonus": round(v["curiosity_bonus"], 3),
                            "fatigue_penalty": round(v["fatigue_penalty"], 3),
                            "adjusted_score": round(v["adjusted_score"], 3),
                            "dominant_class": v.get("dominant_class", "UNKNOWN"),
                        }
                        for k, v in results.items()
                    },
                    "metrics": metrics,
                    "binary_state": binary,
                    "cube_position": escape_state,
                    "transition_allowed": True,
                    "transition_memory": transition_memory,
                    "decision": {
                        "decision": "FORCE_ESCAPE",
                        "reason": f"loop_detected_{loop_state}_{loop_count}",
                    },
                    "kernel": {
                        "winner": best_agent,
                        "score": round(best_data["adjusted_score"], 6),
                        "dominant_class": dominant_class,
                    },
                    "party": party_summary,
                    "applied": True,
                    "state": self.state.to_dict(),
                    "summary": {
                        "allowed_moves": self.allowed_moves,
                        "blocked_moves": self.blocked_moves,
                        "stability_score": stability_score,
                    },
                }

        decision = adaptive_bindu(
            metrics,
            force_reject=not allowed,
            transition_memory=transition_memory,
        )

        applied = False
        if decision["decision"] in ("COMMIT", "SOFT_COMMIT"):
            self.state = next_state
            self.state_visits[current_tuple] += 1
            self.vision_history.append(current_tuple)
            applied = True

        self._update_temperature(decision["decision"])
        self.prev_tuple = current_tuple

        # store class history after decision
        self.class_history.append(dominant_class)
        self.class_history = self.class_history[-50:]

        total = self.allowed_moves + self.blocked_moves
        stability_score = round(self.allowed_moves / total, 3) if total else 1.0
        party_summary = self._build_party_summary(results, stability_score)

        return {
            "step": self.step_count,
            "agent": best_agent,
            "mode": self.mode,
            "temperature": self.temperature,
            "reject_streak": self.reject_streak,
            "vision": {
                "current": frame.current,
                "coarse": frame.coarse,
                "mid": frame.mid,
                "fine": frame.fine,
                "vibration_phase": frame.vibration_phase,
                "blink_gate": frame.blink_gate,
                "anomaly": frame.anomaly,
            },
            "agent_scores": {
                k: {
                    "base_score": round(v["base_score"], 3),
                    "mode_bias": round(v["mode_bias"], 3),
                    "repeat_penalty": round(v["repeat_penalty"], 3),
                    "curiosity_bonus": round(v["curiosity_bonus"], 3),
                    "fatigue_penalty": round(v["fatigue_penalty"], 3),
                    "adjusted_score": round(v["adjusted_score"], 3),
                    "dominant_class": v.get("dominant_class", "UNKNOWN"),
                }
                for k, v in results.items()
            },
            "metrics": metrics,
            "binary_state": binary,
            "cube_position": current_tuple,
            "transition_allowed": allowed,
            "transition_memory": transition_memory,
            "decision": decision,
            "kernel": {
                "winner": best_agent,
                "score": round(best_data["adjusted_score"], 6),
                "dominant_class": dominant_class,
            },
            "party": party_summary,
            "applied": applied,
            "state": self.state.to_dict(),
            "summary": {
                "allowed_moves": self.allowed_moves,
                "blocked_moves": self.blocked_moves,
                "stability_score": stability_score,
            },
        }
