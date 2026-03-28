import json
import time
from typing import Any, Dict, List

import streamlit as st

from app.state_engine import StateEngine


st.set_page_config(page_title="GitCube OS", layout="wide")


def init_session():
    if "engine" not in st.session_state:
        st.session_state.engine = StateEngine(mode="balanced")

    if "history" not in st.session_state:
        st.session_state.history = []

    if "auto_running" not in st.session_state:
        st.session_state.auto_running = False

    if "speed_ms" not in st.session_state:
        st.session_state.speed_ms = 1000


def reset_engine(mode: str):
    st.session_state.engine = StateEngine(mode=mode)
    st.session_state.history = []
    st.session_state.auto_running = False


def run_one_step():
    result = st.session_state.engine.step()
    st.session_state.history.append(result)
    return result


def get_last_result() -> Dict[str, Any] | None:
    if st.session_state.history:
        return st.session_state.history[-1]
    return None


def pretty_json(data: Any):
    st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")


def render_header():
    st.title("GitCube OS")
    st.caption("Adaptive decision-making in a constrained binary state space.")


def render_controls():
    st.subheader("Controls")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mode = st.selectbox(
            "Mode",
            options=["balanced", "planner", "critic", "explorer", "stabilizer"],
            index=["balanced", "planner", "critic", "explorer", "stabilizer"].index(
                st.session_state.engine.mode
            )
            if st.session_state.engine.mode in ["balanced", "planner", "critic", "explorer", "stabilizer"]
            else 0,
        )

    with col2:
        speed_ms = st.number_input(
            "Auto speed (ms)",
            min_value=100,
            max_value=5000,
            value=st.session_state.speed_ms,
            step=100,
        )
        st.session_state.speed_ms = int(speed_ms)

    with col3:
        if st.button("STEP", use_container_width=True):
            st.session_state.engine.set_mode(mode)
            run_one_step()

    with col4:
        if st.button("RESET", use_container_width=True):
            reset_engine(mode)

    col5, col6, col7 = st.columns(3)

    with col5:
        if st.button("RUN x10", use_container_width=True):
            st.session_state.engine.set_mode(mode)
            for _ in range(10):
                run_one_step()

    with col6:
        if st.button("START AUTO", use_container_width=True):
            st.session_state.engine.set_mode(mode)
            st.session_state.auto_running = True

    with col7:
        if st.button("STOP AUTO", use_container_width=True):
            st.session_state.auto_running = False


def render_state_block(last: Dict[str, Any] | None):
    st.subheader("State")

    if not last:
        st.info("Press STEP, RUN x10, or START AUTO.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Current")
        st.write(f"Step: **{last['step']}**")
        st.write(f"Agent: **{last['agent']}**")
        st.write(f"Mode: **{last['mode']}**")

    with col2:
        st.markdown("### Runtime")
        st.write(f"Temperature: **{last['temperature']}**")
        st.write(f"Reject streak: **{last['reject_streak']}**")
        st.write(f"Applied: **{last['applied']}**")

    with col3:
        st.markdown("### Cube")
        st.write(f"Binary state: **{tuple(last['binary_state'])}**")
        st.write(f"Cube position: **{last['cube_position']}**")
        st.write(f"Transition allowed: **{last['transition_allowed']}**")


def render_kernel_block(last: Dict[str, Any] | None):
    st.subheader("Kernel")

    if not last or "kernel" not in last:
        st.info("Kernel data will appear after first step.")
        return

    kernel = last["kernel"]
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Winner", kernel.get("winner", "-"))

    with col2:
        st.metric("Score", kernel.get("score", "-"))


def render_decision_block(last: Dict[str, Any] | None):
    st.subheader("Decision")

    if not last:
        return

    decision = last["decision"]
    metrics = last["metrics"]
    summary = last["summary"]
    transition_memory = last.get("transition_memory", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Decision Output")
        pretty_json(decision)

        st.markdown("### Summary")
        pretty_json(summary)

    with col2:
        st.markdown("### Metrics")
        pretty_json(metrics)

        st.markdown("### Transition Memory")
        pretty_json(transition_memory)


def render_vision_block(last: Dict[str, Any] | None):
    st.subheader("Vision")

    if not last:
        return

    pretty_json(last["vision"])


def render_state_values(last: Dict[str, Any] | None):
    st.subheader("State Values")

    if not last:
        return

    pretty_json(last["state"])


def render_agent_scores(last: Dict[str, Any] | None):
    st.subheader("Agent Scores")

    if not last:
        return

    scores = last["agent_scores"]
    pretty_json(scores)


def render_history():
    st.subheader("Agent History")

    history: List[Dict[str, Any]] = st.session_state.history
    if not history:
        st.info("No history yet.")
        return

    lines = []
    for item in reversed(history[-20:]):
        decision_name = item["decision"]["decision"] if isinstance(item["decision"], dict) else str(item["decision"])
        cube_pos = item.get("cube_position")
        allowed = item.get("transition_allowed")
        lines.append(
            f"step {item['step']} | {item['agent']} | mode={item['mode']} | "
            f"{decision_name} | {cube_pos} | allowed={allowed}"
        )

    st.code("\n".join(lines), language="text")


def render_trajectory():
    st.subheader("Trajectory")

    history: List[Dict[str, Any]] = st.session_state.history
    if not history:
        st.info("No trajectory yet.")
        return

    points = [str(item.get("cube_position")) for item in history[-30:]]
    st.write(" → ".join(points))


def render_visit_heat():
    st.subheader("Visit Heat")

    history: List[Dict[str, Any]] = st.session_state.history
    if not history:
        st.info("No visits yet.")
        return

    counts: Dict[str, int] = {}
    for item in history:
        key = str(item.get("cube_position"))
        counts[key] = counts.get(key, 0) + 1

    pretty_json(counts)


def render_auto_status():
    st.subheader("Auto")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Running: **{st.session_state.auto_running}**")
    with col2:
        st.write(f"Speed ms: **{st.session_state.speed_ms}**")
    with col3:
        st.write(f"History size: **{len(st.session_state.history)}**")


def auto_run_if_needed():
    if st.session_state.auto_running:
        run_one_step()
        time.sleep(st.session_state.speed_ms / 1000.0)
        st.rerun()


def main():
    init_session()
    render_header()
    render_controls()

    last = get_last_result()

    left, right = st.columns([1.2, 1])

    with left:
        render_state_block(last)
        render_kernel_block(last)
        render_decision_block(last)
        render_trajectory()
        render_visit_heat()

    with right:
        render_auto_status()
        render_vision_block(last)
        render_state_values(last)
        render_agent_scores(last)
        render_history()

    auto_run_if_needed()


if __name__ == "__main__":
    main()
