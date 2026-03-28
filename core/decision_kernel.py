from core.agent_roles import (
    score_planner,
    score_critic,
    score_explorer,
    score_stabilizer,
)
from core.topology import get_neighbors, is_local_transition


class DecisionKernel:
    def __init__(self):
        self.memory = {
            "total_steps": 0,
            "blocked_steps": 0,
            "blocked_ratio": 0.0,
            "caution_bias": 0.0,
            "coherence_penalty": 0.0,
        }
        self.visit_heat = {}
        self.reject_streak = 0
        self.temperature = 1.0

    def update_visit(self, state):
        self.visit_heat[state] = self.visit_heat.get(state, 0) + 1

    def adaptive_temperature(self):
        # якщо система stuck, трохи піднімаємо температуру
        self.temperature = min(3.0, 1.0 + 0.05 * self.reject_streak)

    def choose(self, current_state, metrics_fn):
        candidates = get_neighbors(current_state)

        scored = []
        for cand in candidates:
            if not is_local_transition(current_state, cand):
                continue

            metrics = metrics_fn(cand)

            planner = score_planner(metrics, self.memory, cand, self.visit_heat)
            critic = score_critic(metrics, self.memory, cand, self.visit_heat)
            explorer = score_explorer(metrics, self.memory, cand, self.visit_heat)
            stabilizer = score_stabilizer(metrics, self.memory, cand, self.visit_heat)

            total = (
                0.35 * planner.adjusted_score
                + 0.20 * critic.adjusted_score
                + 0.25 * explorer.adjusted_score
                + 0.20 * stabilizer.adjusted_score
            )

            scored.append({
                "candidate": cand,
                "metrics": metrics,
                "agent_scores": {
                    "planner": planner.__dict__,
                    "critic": critic.__dict__,
                    "explorer": explorer.__dict__,
                    "stabilizer": stabilizer.__dict__,
                },
                "total_score": total,
            })

        scored.sort(key=lambda x: x["total_score"], reverse=True)
        return scored

    def decide(self, current_state, metrics_fn, thresholds):
        self.adaptive_temperature()
        ranked = self.choose(current_state, metrics_fn)

        if not ranked:
            self.reject_streak += 1
            return {
                "type": "REJECT",
                "reason": "no_local_candidates",
                "next_state": current_state,
                "ranked": [],
            }

        best = ranked[0]
        m = best["metrics"]

        commit_ok = (
            m["shadow"] <= thresholds["commit_shadow_max"]
            and m["coherence"] >= thresholds["commit_coherence_min"]
        )

        soft_ok = (
            m["shadow"] <= thresholds["soft_shadow_max"]
            and m["coherence"] >= thresholds["soft_coherence_min"]
        )

        # anti-stuck escape
        if self.reject_streak >= 10 and soft_ok:
            decision = "SOFT_COMMIT"
            reason = "adaptive_escape"
            self.reject_streak = 0
            self.update_visit(best["candidate"])
            return {
                "type": decision,
                "reason": reason,
                "next_state": best["candidate"],
                "ranked": ranked,
                "best": best,
            }

        if commit_ok:
            decision = "COMMIT"
            reason = "threshold_commit"
            self.reject_streak = 0
            self.update_visit(best["candidate"])
            return {
                "type": decision,
                "reason": reason,
                "next_state": best["candidate"],
                "ranked": ranked,
                "best": best,
            }

        if soft_ok:
            decision = "SOFT_COMMIT"
            reason = "threshold_soft_commit"
            self.reject_streak = 0
            self.update_visit(best["candidate"])
            return {
                "type": decision,
                "reason": reason,
                "next_state": best["candidate"],
                "ranked": ranked,
                "best": best,
            }

        self.reject_streak += 1
        return {
            "type": "REJECT",
            "reason": "adaptive_reject",
            "next_state": current_state,
            "ranked": ranked,
            "best": best,
          }
