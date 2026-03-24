from typing import List, Dict


class TopologicalFilter:
    """
    Discrete lattice-based consistency filter.

    - Validates sequences through phase transitions
    - Applies friction (shadow) constraint
    - Uses modular resonance as checksum
    """

    def __init__(self):
        # 7 octaves × 6 phases
        self.lattice = [[0.0 for _ in range(6)] for _ in range(7)]

    def compute_coherence(self, data: str) -> float:
        """
        Basic symbolic coherence metric (pluggable).
        """
        if not data:
            return 0.0

        vowels = set("AEIOUYАЕЄИІЇОУЮЯ")
        clean = "".join(filter(str.isalpha, data.upper()))

        if not clean:
            return 0.0

        ratio = sum(1 for c in clean if c in vowels) / len(clean)

        # ideal region ~0.4
        dist = abs(ratio - 0.4)
        return max(0.0, 1.0 - dist * 2.5)

    def apply_transition(self, octave: int, weight: float) -> bool:
        """
        Attempt phase shift in lattice.
        Returns False if blocked (high shadow / low friction).
        """
        friction = 1.0 - weight

        if friction < 0.3:
            return False

        row = octave - 1

        # manual roll right by 1
        old_row = self.lattice[row]
        new_row = [old_row[-1]] + old_row[:-1]
        new_row[0] = weight
        self.lattice[row] = new_row

        return True

    def resonance_check(self) -> Dict[str, object]:
        """
        Modular checksum (3-6-9 class).
        """
        total = 0.0
        for row in self.lattice:
            total += sum(row)

        mod = total % 9

        return {
            "total_mass": round(total, 3),
            "mod9": round(mod, 3),
            "resonant": round(mod, 3) in [0, 3, 6],
        }

    def process(self, sequence: List[str]) -> Dict[str, object]:
        """
        Run sequence through filter.
        """
        steps = []
        success = True

        for item in sequence:
            coherence = self.compute_coherence(item)
            octave = (len(item) % 7) + 1

            ok = self.apply_transition(octave, coherence)

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
            "status": (
                "valid" if success and resonance["resonant"]
                else "unstable"
            )
        }
