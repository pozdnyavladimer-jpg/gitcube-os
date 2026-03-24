from typing import List, Dict


class TopologicalFilter:
    """
    Adaptive lattice-based consistency filter.

    - Does NOT hard-block everything
    - Works as soft gate (membrane, not wall)
    - Allows learning loop to continue
    """

    def __init__(self):
        # 7 octaves × 6 phases
        self.lattice = [[0.0 for _ in range(6)] for _ in range(7)]

    # -----------------------------
    # COHERENCE
    # -----------------------------
    def compute_coherence(self, data: str) -> float:
        if not data:
            return 0.0

        vowels = set("AEIOUYАЕЄИІЇОУЮЯ")
        clean = "".join(filter(str.isalpha, data.upper()))

        if not clean:
            return 0.0

        ratio = sum(1 for c in clean if c in vowels) / len(clean)
        dist = abs(ratio - 0.4)

        return max(0.0, 1.0 - dist * 2.5)

    # -----------------------------
    # TRANSITION (SOFT GATE)
    # -----------------------------
    def apply_transition(self, octave: int, weight: float) -> bool:
        """
        Soft gate:
        - almost always allows transition
        - blocks only extreme instability
        """
        row = octave - 1

        # --- VERY STRICT BLOCK ONLY ---
        if weight > 0.95:
            return False

        # --- NORMAL FLOW ---
        old_row = self.lattice[row]
        new_row = [old_row[-1]] + old_row[:-1]
        new_row[0] = weight
        self.lattice[row] = new_row

        return True

    # -----------------------------
    # RESONANCE
    # -----------------------------
    def resonance_check(self) -> Dict[str, object]:
        total = 0.0
        for row in self.lattice:
            total += sum(row)

        mod = total % 9

        return {
            "total_mass": round(total, 3),
            "mod9": round(mod, 3),
            "resonant": round(mod, 3) in [0, 3, 6],
        }

    # -----------------------------
    # MAIN PIPELINE
    # -----------------------------
    def process(self, sequence: List[str]) -> Dict[str, object]:
        steps = []
        success = True
        soft_flags = []

        for item in sequence:
            coherence = self.compute_coherence(item)
            octave = (len(item) % 7) + 1

            ok = self.apply_transition(octave, coherence)

            if coherence < 0.25:
                soft_flags.append("low_coherence")

            if coherence > 0.9:
                soft_flags.append("overfit")

            steps.append({
                "item": item,
                "coherence": round(coherence, 3),
                "octave": octave,
                "accepted": ok
            })

            if not ok:
                success = False
                break

        resonance = self.resonance_check()

        return {
            "success": success,
            "steps": steps,
            "resonance": resonance,
            "flags": soft_flags,
            "status": (
                "valid" if success else "blocked"
            )
        }
