import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

from app.live_agent import LiveAgent


def heat_color(count, max_count):
    if max_count <= 0:
        return "lightgray"
    ratio = count / max_count
    if ratio >= 0.85:
        return "red"
    if ratio >= 0.6:
        return "orange"
    if ratio >= 0.3:
        return "deepskyblue"
    if ratio > 0:
        return "lightgreen"
    return "lightgray"


def draw_cube(view, history, allowed_history, blocked_history, visit_counts):
    G = nx.Graph()
    current = tuple(view["current"])

    for node in view["nodes"]:
        G.add_node(tuple(node["id"]))

    nodes = list(G.nodes)
    for a in nodes:
        for b in nodes:
            if a != b and sum(x != y for x, y in zip(a, b)) == 1:
                G.add_edge(a, b)

    pos = {
        (0, 0, 0): (-1.0, -1.0),
        (0, 0, 1): (-1.0,  0.2),
        (0, 1, 0): ( 0.2, -1.0),
        (0, 1, 1): ( 0.2,  0.2),
        (1, 0, 0): (-0.2, -0.2),
        (1, 0, 1): (-0.2,  1.0),
        (1, 1, 0): ( 1.0, -0.2),
        (1, 1, 1): ( 1.0,  1.0),
    }

    max_count = max(visit_counts.values()) if visit_counts else 0

    node_colors = []
    node_sizes = []
    for n in G.nodes:
        if n == current:
            node_colors.append("gold")
            node_sizes.append(1500)
        else:
            count = visit_counts.get(n, 0)
            node_colors.append(heat_color(count, max_count))
            node_sizes.append(800 + count * 12)

    edge_colors = []
    edge_widths = []
    for a, b in G.edges:
        if a == current or b == current:
            edge_colors.append("limegreen")
            edge_widths.append(2.5)
        else:
            edge_colors.append("gray")
            edge_widths.append(1.5)

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=edge_widths, alpha=0.85)
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,
        edgecolors="white", linewidths=1.2
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white", font_size=10)

    for a, b in allowed_history:
        ax.plot(
            [pos[a][0], pos[b][0]],
            [pos[a][1], pos[b][1]],
            color="cyan",
            linewidth=2.2,
            alpha=0.9,
            linestyle="--",
        )

    for a, b in blocked_history:
        ax.plot(
            [pos[a][0], pos[b][0]],
            [pos[a][1], pos[b][1]],
            color="red",
            linewidth=2.6,
            alpha=0.95,
            linestyle="--",
        )

    ax.set_title("Binary State Cube", color="white", fontsize=14)
    ax.set_axis_off()
    plt.tight_layout()
    return fig


if "agent" not in st.session_state:
    st.session_state.agent = LiveAgent(mode="balanced")

if "packet" not in st.session_state:
    st.session_state.packet = None

if "auto_run" not in st.session_state:
    st.session_state.auto_run = False

if "mode" not in st.session_state:
    st.session_state.mode = "balanced"

agent = st.session_state.agent

st.set_page_config(layout="wide")
st.title("🧠 GitCube OS — Unified Navigator")

top1, top2, top3, top4 = st.columns([1, 1, 1, 2])

with top1:
    if st.button("▶ STEP"):
        st.session_state.packet = agent.step()

with top2:
    if st.button("⏩ RUN x10"):
        st.session_state.packet = agent.run(steps=10)

with top3:
    if st.button("🔄 RESET"):
        st.session_state.agent = LiveAgent(mode=st.session_state.mode)
        st.session_state.packet = None
        st.session_state.auto_run = False

with top4:
    speed_ms = st.slider("Auto speed (ms)", 300, 2000, 1000, 100)

mode = st.selectbox(
    "Agent mode",
    ["balanced", "planner-biased", "explorer-biased", "stabilizer-biased"],
    index=["balanced", "planner-biased", "explorer-biased", "stabilizer-biased"].index(st.session_state.mode),
)

if mode != st.session_state.mode:
    st.session_state.mode = mode
    st.session_state.agent.set_mode(mode)

auto_col1, auto_col2 = st.columns(2)
with auto_col1:
    if st.button("🟢 START AUTO"):
        st.session_state.auto_run = True
with auto_col2:
    if st.button("⛔ STOP AUTO"):
        st.session_state.auto_run = False

agent = st.session_state.agent

if st.session_state.auto_run:
    st_autorefresh(interval=speed_ms, key="gitcube_auto_refresh")
    st.session_state.packet = agent.step()

if st.session_state.packet:
    packet = st.session_state.packet
    result = packet["result"]
    view = packet["view"]
    history = packet["history"]
    allowed_history = packet["allowed_history"]
    blocked_history = packet["blocked_history"]
    visit_counts = packet["visit_counts"]

    left, center, right = st.columns([1, 2, 1])

    with left:
        st.subheader("📊 Metrics")
        for k, v in view["metrics"].items():
            try:
                st.write(f"{k}: {round(v, 3)}")
            except TypeError:
                st.write(f"{k}: {v}")

        st.subheader("🧠 Memory")
        st.json(view["memory"])

        st.subheader("🤖 Auto")
        st.write("Running:", st.session_state.auto_run)
        st.write("Speed ms:", speed_ms)
        st.write("Mode:", st.session_state.mode)
        st.write("Temperature:", result.get("temperature", 1.0))
        st.write("Reject streak:", result.get("reject_streak", 0))

        if "vision" in result:
            st.subheader("👁️ Vision")
            st.write("Anomaly:", result["vision"]["anomaly"])
            st.write("Blink:", result["vision"]["blink_gate"])
            st.write("Phase:", result["vision"]["vibration_phase"])

            st.markdown("**Coarse**")
            st.json(result["vision"]["coarse"])

            st.markdown("**Mid**")
            st.json(result["vision"]["mid"])

            st.markdown("**Fine**")
            st.json(result["vision"]["fine"])

    with center:
        st.subheader("🧊 State Space")
        st.write("Current:", view["current"])

        fig = draw_cube(view, history, allowed_history, blocked_history, visit_counts)
        st.pyplot(fig)

        st.subheader("Trajectory")
        st.write(" → ".join(str(tuple(h['current'])) for h in history[-20:]))

        st.subheader("Legend")
        st.write("🟡 Current state")
        st.write("🟩 Rarely visited")
        st.write("🔵 Medium visited")
        st.write("🟧 Highly visited")
        st.write("🟥 Dominant state")
        st.write("➖ Cyan dashed = allowed path")
        st.write("➖ Red dashed = blocked jump")

    with right:
        st.subheader("⚡ Decision")
        decision = view["decision"]

        st.write("Type:", decision["decision"])
        st.write("Reason:", decision["reason"])

        if "thresholds" in decision:
            st.subheader("Thresholds")
            st.json(decision["thresholds"])

        st.subheader("📈 Summary")
        st.json(view["summary"])

        st.subheader("🔥 Visit Heat")
        for node, count in sorted(visit_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"{node}: {count}")

        st.subheader("🏁 Agent Scores")
        if "agent_scores" in result:
            st.json(result["agent_scores"])

        st.subheader("🤖 Agent History")
        for item in reversed(history[-12:]):
            line = (
                f"step {item['step']} | "
                f"{item['agent']} | "
                f"{item['mode']} | "
                f"{item['decision']} | "
                f"{item['current']} | "
                f"allowed={item['allowed']}"
            )
            st.write(line)
else:
    st.info("Press STEP, RUN x10, or START AUTO.")
