import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ============================================================
# CONFIG
# ============================================================

SEED = 42
random.seed(SEED)

DT = 0.06
DAMPING = 0.92
CENTER_PULL = 0.045
NEIGHBOR_PULL = 0.12
HEALER_GAIN = 0.18
CHAOS_GAIN = 0.08
TENSION_THRESHOLD = 0.09

RINGS = [
    (0.0, 1),   # bindu
    (0.9, 6),   # first flower ring
    (1.7, 12),  # second ring
    (2.5, 18),  # outer ring
]

WINDOW = 4.2


# ============================================================
# STATE
# ============================================================

@dataclass
class Node:
    id: int
    ring: int
    angle: float

    ideal_x: float
    ideal_y: float

    x: float
    y: float

    vx: float = 0.0
    vy: float = 0.0

    tension: float = 0.0
    is_anchor: bool = False
    neighbors: List[int] = field(default_factory=list)


# ============================================================
# BUILD FLOWER MESH
# ============================================================

def build_flower_mesh() -> List[Node]:
    nodes: List[Node] = []
    node_id = 0

    for ring_index, (radius, count) in enumerate(RINGS):
        if count == 1:
            nodes.append(
                Node(
                    id=node_id,
                    ring=ring_index,
                    angle=0.0,
                    ideal_x=0.0,
                    ideal_y=0.0,
                    x=0.0,
                    y=0.0,
                    is_anchor=True,
                )
            )
            node_id += 1
            continue

        for i in range(count):
            angle = (2 * math.pi * i) / count
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)

            nodes.append(
                Node(
                    id=node_id,
                    ring=ring_index,
                    angle=angle,
                    ideal_x=x,
                    ideal_y=y,
                    x=x,
                    y=y,
                )
            )
            node_id += 1

    connect_neighbors(nodes)
    return nodes


def connect_neighbors(nodes: List[Node]) -> None:
    by_ring: dict[int, List[Node]] = {}
    for n in nodes:
        by_ring.setdefault(n.ring, []).append(n)

    ring_ids = sorted(by_ring.keys())

    for ring in ring_ids:
        ring_nodes = by_ring[ring]
        if len(ring_nodes) > 1:
            count = len(ring_nodes)
            for i, node in enumerate(ring_nodes):
                left = ring_nodes[(i - 1) % count].id
                right = ring_nodes[(i + 1) % count].id
                node.neighbors.extend([left, right])

        if ring > 0:
            inner = by_ring[ring - 1]
            for node in ring_nodes:
                nearest_inner = min(
                    inner,
                    key=lambda m: (node.ideal_x - m.ideal_x) ** 2 + (node.ideal_y - m.ideal_y) ** 2,
                )
                node.neighbors.append(nearest_inner.id)
                nearest_inner.neighbors.append(node.id)

    for node in nodes:
        node.neighbors = sorted(set(node.neighbors))


# ============================================================
# CHAOS / FRACTAL INPUT
# ============================================================

def inject_fractal_chaos(nodes: List[Node], frame: int) -> None:
    t = frame * DT

    for node in nodes:
        if node.is_anchor:
            continue

        radius = math.hypot(node.ideal_x, node.ideal_y)
        angle = node.angle

        # radial wave
        radial = math.sin(2.7 * t + 3.0 * angle + 0.9 * radius)

        # ring wave
        ring = math.cos(1.8 * t - 2.0 * angle + 1.2 * radius)

        # local asymmetry: one sector gets more stress
        sector_bias = 0.0
        if -0.6 < angle < 0.4 and node.ring >= 2:
            sector_bias = 1.0

        fx = CHAOS_GAIN * (
            0.6 * radial * math.cos(angle)
            + 0.35 * ring * math.sin(2 * angle)
            + 0.7 * sector_bias
        )
        fy = CHAOS_GAIN * (
            0.6 * radial * math.sin(angle)
            + 0.35 * ring * math.cos(3 * angle)
            + 0.25 * sector_bias
        )

        node.vx += fx
        node.vy += fy


# ============================================================
# TENSION + HEALER
# ============================================================

def apply_field_forces(nodes: List[Node]) -> None:
    id_to_node = {n.id: n for n in nodes}

    for node in nodes:
        if node.is_anchor:
            node.x = 0.0
            node.y = 0.0
            node.vx = 0.0
            node.vy = 0.0
            node.tension = 0.0
            continue

        # error from ideal flower position
        ex = node.ideal_x - node.x
        ey = node.ideal_y - node.y

        # bindu pull
        node.vx += CENTER_PULL * ex
        node.vy += CENTER_PULL * ey

        # neighbor pull (mesh integrity)
        for nid in node.neighbors:
            other = id_to_node[nid]
            desired_dx = other.ideal_x - node.ideal_x
            desired_dy = other.ideal_y - node.ideal_y

            actual_dx = other.x - node.x
            actual_dy = other.y - node.y

            node.vx += NEIGHBOR_PULL * (actual_dx - desired_dx) * 0.06
            node.vy += NEIGHBOR_PULL * (actual_dy - desired_dy) * 0.06

        # compute local tension
        node.tension = math.hypot(ex, ey)

        # healer only appears when tension is large enough
        if node.tension > TENSION_THRESHOLD:
            node.vx += HEALER_GAIN * ex
            node.vy += HEALER_GAIN * ey

        # damping
        node.vx *= DAMPING
        node.vy *= DAMPING


def integrate(nodes: List[Node]) -> None:
    for node in nodes:
        if node.is_anchor:
            continue

        node.x += node.vx * DT
        node.y += node.vy * DT


# ============================================================
# VIEW
# ============================================================

def plot_edges(ax, nodes: List[Node]) -> None:
    id_to_node = {n.id: n for n in nodes}
    drawn = set()

    for node in nodes:
        for nid in node.neighbors:
            key = tuple(sorted((node.id, nid)))
            if key in drawn:
                continue
            drawn.add(key)

            other = id_to_node[nid]
            ax.plot(
                [node.x, other.x],
                [node.y, other.y],
                linewidth=0.7,
                alpha=0.22,
            )


def plot_flower_guides(ax, nodes: List[Node]) -> None:
    by_ring: dict[int, List[Node]] = {}
    for n in nodes:
        by_ring.setdefault(n.ring, []).append(n)

    for ring, ring_nodes in by_ring.items():
        if ring == 0 or len(ring_nodes) < 3:
            continue

        xs = [n.ideal_x for n in ring_nodes] + [ring_nodes[0].ideal_x]
        ys = [n.ideal_y for n in ring_nodes] + [ring_nodes[0].ideal_y]
        ax.plot(xs, ys, linestyle="--", linewidth=0.5, alpha=0.15)


def render(ax, nodes: List[Node], frame: int) -> None:
    ax.clear()
    ax.set_xlim(-WINDOW, WINDOW)
    ax.set_ylim(-WINDOW, WINDOW)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("black")

    plot_flower_guides(ax, nodes)
    plot_edges(ax, nodes)

    # split nodes by state
    stable_x, stable_y = [], []
    tension_x, tension_y = [], []
    anchor_x, anchor_y = [], []

    for n in nodes:
        if n.is_anchor:
            anchor_x.append(n.x)
            anchor_y.append(n.y)
        elif n.tension > TENSION_THRESHOLD:
            tension_x.append(n.x)
            tension_y.append(n.y)
        else:
            stable_x.append(n.x)
            stable_y.append(n.y)

    # stable mesh
    if stable_x:
        ax.scatter(stable_x, stable_y, s=18, alpha=0.75)

    # tension points
    if tension_x:
        ax.scatter(tension_x, tension_y, s=28, marker="x")

    # bindu
    ax.scatter(anchor_x, anchor_y, s=90)

    # soft flower shell
    shell_x = [n.x for n in nodes if n.ring == len(RINGS) - 1]
    shell_y = [n.y for n in nodes if n.ring == len(RINGS) - 1]
    if shell_x:
        shell_x += [shell_x[0]]
        shell_y += [shell_y[0]]
        ax.plot(shell_x, shell_y, linewidth=1.2, alpha=0.35)

    avg_tension = sum(n.tension for n in nodes if not n.is_anchor) / max(1, len(nodes) - 1)
    ax.set_title(f"V-CORE Self-Stabilizing Mesh | frame={frame} | avg_tension={avg_tension:.3f}")


# ============================================================
# MAIN LOOP
# ============================================================

def step(nodes: List[Node], frame: int) -> None:
    inject_fractal_chaos(nodes, frame)
    apply_field_forces(nodes)
    integrate(nodes)


def main() -> None:
    nodes = build_flower_mesh()

    fig, ax = plt.subplots(figsize=(8, 8))

    def update(frame: int):
        step(nodes, frame)
        render(ax, nodes, frame)
        return []

    FuncAnimation(fig, update, frames=400, interval=40, blit=False, repeat=True)
    plt.show()


if __name__ == "__main__":
    main()
