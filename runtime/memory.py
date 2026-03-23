from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MemoryEntry:
    step: int
    agent: str
    metrics: Dict[str, float]
    state: Dict[str, float]


@dataclass
class EpisodeMemory:
    entries: List[MemoryEntry] = field(default_factory=list)

    def add(self, step: int, agent: str, metrics: Dict[str, float], state: Dict[str, float]) -> None:
        self.entries.append(
            MemoryEntry(
                step=step,
                agent=agent,
                metrics=dict(metrics),
                state=dict(state),
            )
        )

    def last(self) -> Optional[MemoryEntry]:
        if not self.entries:
            return None
        return self.entries[-1]

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def summary(self) -> Dict[str, object]:
        if not self.entries:
            return {
                "steps": 0,
                "agents_used": [],
                "final_metrics": None,
                "final_state": None,
            }

        agents_used = []
        seen = set()
        for entry in self.entries:
            if entry.agent not in seen:
                seen.add(entry.agent)
                agents_used.append(entry.agent)

        last = self.entries[-1]

        return {
            "steps": len(self.entries),
            "agents_used": agents_used,
            "final_metrics": last.metrics,
            "final_state": last.state,
        }
