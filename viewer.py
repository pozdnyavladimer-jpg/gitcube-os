import json
import math
import os
import textwrap
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

OBJECTS_PATH = "objects.json"
CLOCK_STATE_PATH = "v_clock_state.json"
BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")


def load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_objects() -> List[Dict[str, Any]]:
    data = load_json(OBJECTS_PATH, [])
    return data if isinstance(data, list) else []


def load_clock_state() -> Dict[str, Dict[str, Any]]:
    data = load_json(CLOCK_STATE_PATH, {})
    return data if isinstance(data, dict) else {}


def load_bus() -> Dict[str, Any]:
    data = load_json(BUS_PATH, {})
    return data if isinstance(data, dict) else {}


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def get_open_tasks() -> List[Dict[str, Any]]:
    out = []
    for obj in load_objects():
        if str(obj.get("type", "")).strip().lower() != "task":
            continue
        if str(obj.get("status", "")).strip().lower() != "open":
            continue
        out.append(obj)
    return out


def task_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return str(payload.get("problem", "")).strip().lower()


def short_title(text: str, width: int = 28) -> str:
    s = str(text or "").strip()
    if len(s) <= width:
        return s
    return s[: width - 1] + "…"


def category_index(problem: str) -> int:
    structural = {
        "missing_init",
        "missing_init_group",
        "python_without_docs",
        "package_structure",
        "missing_root_readme",
        "missing_start_here",
    }
    macro = {
        "routing_failure",
        "no_target_path",
        "global_block",
    }
    hygiene = {
        "debug_prints_group",
        "todo_group",
        "pass_blocks_group",
        "bare_except_group",
        "large_files_group",
        "empty_directories_group",
    }

    if problem in structural:
        return 0
    if problem in hygiene:
        return 1
    if problem in macro:
        return 2
    return 3


def status_color(task_id: str, active_ids: set, suppressed_ids: set, promoted_ids: set, state_row: Dict[str, Any]) -> str:
    deferred = float(state_row.get("deferred_energy", 0.0) or 0.0)

    if task_id in promoted_ids:
        return "#ff5a36"  # red/orange
    if task_id in active_ids:
        return "#36d66b"  # green
    if deferred >= 1.0:
        return "#ffd84d"  # yellow
    if task_id in suppressed_ids:
        return "#7f8c8d"  # gray
    return "#5dade2"      # blue fallback


def compute_positions(tasks: List[Dict[str, Any]], clock_state: Dict[str, Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
    # four sectors / rings
    sectors = {
        0: math.radians(45),   # structural
        1: math.radians(135),  # hygiene
        2: math.radians(225),  # macro
        3: math.radians(315),  # misc
    }

    grouped: Dict[int, List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {0: [], 1: [], 2: [], 3: []}

    for task in tasks:
        tid = str(task.get("id"))
        row = clock_state.get(tid, {}) if isinstance(clock_state.get(tid), dict) else {}
        grouped[category_index(task_problem(task))].append((task, row))

    positions: Dict[str, Tuple[float, float]] = {}

    for cat, items in grouped.items():
        if not items:
            continue

        # strongest closer to center
        items.sort(
            key=lambda x: (
                float(x[1].get("admission_score", 0.0) or 0.0),
                float(x[1].get("alignment", 0.0) or 0.0),
                float(x[1].get("deferred_energy", 0.0) or 0.0),
            ),
            reverse=True,
        )

        base_angle = sectors[cat]
        spread = math.radians(60)

        n = len(items)
        for i, (task, row) in enumerate(items):
            tid = str(task.get("id"))
            rank = i + 1

            angle = base_angle
            if n > 1:
                angle = base_angle - spread / 2 + spread * (i / (n - 1))

            align = float(row.get("alignment", 0.0) or 0.0)
            deferred = float(row.get("deferred_energy", 0.0) or 0.0)

            # better aligned closer to center, more deferred slightly farther
            radius = 2.0 + (rank * 0.45) + (1.0 - align) * 1.5 + min(1.5, deferred * 0.25)

            x = radius * math.cos(angle)
            y = radius * math.sin(angle)

            positions[tid] = (x, y)

    return positions


def draw_panel(ax, bus: Dict[str, Any], tasks: List[Dict[str, Any]], active_ids: set, suppressed_ids: set, promoted_ids: set):
    ax.set_axis_off()

    meta = bus.get("meta", {}) if isinstance(bus.get("meta"), dict) else {}
    vclock = meta.get("v_clock", {}) if isinstance(meta.get("v_clock"), dict) else {}
    directive = vclock.get("prime_directive", {}) if isinstance(vclock.get("prime_directive"), dict) else {}

    lines = []
    lines.append("GITCUBE FIELD VIEWER")
    lines.append("")
    lines.append(f"Open tasks: {len(tasks)}")
    lines.append(f"Active: {len(active_ids)}")
    lines.append(f"Suppressed: {len(suppressed_ids)}")
    lines.append(f"Triggered: {len(promoted_ids)}")
    lines.append(f"Focus limit: {vclock.get('focus_limit', '-')}")
    lines.append("")

    lines.append("PRIME_DIRECTIVE")
    for k in ("pressure", "flow", "structure", "balance", "law", "future"):
        val = directive.get(k, "-")
        lines.append(f"  {k:<10} {val}")
    lines.append("")

    lines.append("LEGEND")
    lines.append("  green   = active")
    lines.append("  gray    = suppressed")
    lines.append("  yellow  = charging")
    lines.append("  red     = triggered")
    lines.append("")
    lines.append("SIZE = intensity")
    lines.append("ALPHA = alignment")
    lines.append("RING = deferred energy")

    txt = "\n".join(lines)
    ax.text(
        0.02, 0.98, txt,
        va="top", ha="left",
        fontsize=10,
        family="monospace",
        color="white",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#111827", edgecolor="#334155")
    )


def main():
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.6, 1.4])
    ax = fig.add_subplot(gs[0, 0])
    panel = fig.add_subplot(gs[0, 1])

    fig.patch.set_facecolor("#050816")

    def update(_frame):
        ax.clear()
        panel.clear()

        ax.set_facecolor("#07111f")
        panel.set_facecolor("#050816")

        tasks = get_open_tasks()
        clock_state = load_clock_state()
        bus = load_bus()

        meta = bus.get("meta", {}) if isinstance(bus.get("meta"), dict) else {}
        vclock = meta.get("v_clock", {}) if isinstance(meta.get("v_clock"), dict) else {}

        active_ids = set(str(x) for x in vclock.get("active_task_ids", []) if x is not None)
        suppressed_ids = set(str(x) for x in vclock.get("suppressed_task_ids", []) if x is not None)
        promoted_ids = set(str(x) for x in vclock.get("promoted_task_ids", []) if x is not None)

        positions = compute_positions(tasks, clock_state)

        # base canvas
        ax.set_title("GitCube OS — State Field", fontsize=18, color="white", pad=16)
        ax.set_xlim(-8.5, 8.5)
        ax.set_ylim(-8.0, 8.0)
        ax.set_aspect("equal")
        ax.axis("off")

        # rings
        for r, alpha in [(2.0, 0.15), (3.5, 0.12), (5.0, 0.10), (6.5, 0.08)]:
            ax.add_patch(Circle((0, 0), r, fill=False, lw=1.0, ec="#60a5fa", alpha=alpha))

        # axes
        ax.plot([-8, 8], [0, 0], color="#1e293b", lw=1, alpha=0.5)
        ax.plot([0, 0], [-8, 8], color="#1e293b", lw=1, alpha=0.5)

        # center
        ax.scatter([0], [0], s=900, c="#38bdf8", alpha=0.95, edgecolors="white", linewidths=1.5, zorder=5)
        ax.text(
            0, 0,
            "PRIME\nDIRECTIVE",
            ha="center", va="center",
            color="white", fontsize=11, weight="bold", zorder=6
        )

        # labels for sectors
        ax.text(4.9, 4.9, "STRUCTURE", color="#93c5fd", fontsize=11, alpha=0.8)
        ax.text(-6.4, 4.9, "HYGIENE", color="#93c5fd", fontsize=11, alpha=0.8)
        ax.text(-6.0, -5.6, "MACRO", color="#93c5fd", fontsize=11, alpha=0.8)
        ax.text(5.4, -5.6, "MISC", color="#93c5fd", fontsize=11, alpha=0.8)

        for task in tasks:
            tid = str(task.get("id"))
            x, y = positions.get(tid, (0, 0))

            row = clock_state.get(tid, {}) if isinstance(clock_state.get(tid), dict) else {}
            alignment = clamp01(row.get("alignment", 0.0))
            deferred = float(row.get("deferred_energy", 0.0) or 0.0)
            intensity = clamp01(task.get("intensity", 0.4))

            color = status_color(tid, active_ids, suppressed_ids, promoted_ids, row)
            size = 180 + 900 * intensity
            alpha = 0.35 + 0.65 * alignment

            # link to center
            ax.plot([0, x], [0, y], color=color, lw=1.0, alpha=0.15 + 0.20 * alignment, zorder=1)

            # deferred ring
            if deferred > 0:
                ring_r = 0.28 + min(0.65, deferred * 0.08)
                ax.add_patch(Circle((x, y), ring_r, fill=False, lw=1.6, ec=color, alpha=0.55, zorder=2))

            # node
            ax.scatter([x], [y], s=size, c=color, alpha=alpha, edgecolors="white", linewidths=1.0, zorder=3)

            label = f"{tid}\n{short_title(task.get('title', ''))}"
            ax.text(
                x, y - 0.55,
                label,
                ha="center", va="top",
                fontsize=8.5,
                color="white",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#0f172a", edgecolor="#1f2937", alpha=0.85),
                zorder=4
            )

            mini = f"a={alignment:.2f} d={deferred:.2f}"
            ax.text(x, y + 0.46, mini, ha="center", va="bottom", fontsize=7.5, color="#cbd5e1", zorder=4)

        draw_panel(panel, bus, tasks, active_ids, suppressed_ids, promoted_ids)

    ani = FuncAnimation(fig, update, interval=2000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
