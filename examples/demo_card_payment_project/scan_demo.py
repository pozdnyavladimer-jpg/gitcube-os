from pathlib import Path
from datetime import datetime, timezone
import json


ROOT = Path(__file__).parent


def clean(value: str) -> str:
    return value.strip().strip('"').strip("'")


def read_file(name: str) -> str:
    path = ROOT / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_edges(text: str):
    edges = []
    current = None

    for raw in text.splitlines():
        s = raw.strip()

        if s.startswith("- id:"):
            if current:
                edges.append(current)
            current = {"id": clean(s.split(":", 1)[1])}

        elif current and ":" in s:
            key, value = s.split(":", 1)
            current[clean(key)] = clean(value)

    if current:
        edges.append(current)

    return edges


def parse_gates(text: str):
    gates = {}
    current = None
    in_gates = False

    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()

        if s == "gates:":
            in_gates = True
            continue

        if not in_gates:
            continue

        if line.startswith("  ") and not line.startswith("    ") and s.endswith(":"):
            current = s[:-1]
            gates[current] = {}

        elif current and line.startswith("    ") and ":" in s:
            key, value = s.split(":", 1)
            gates[current][clean(key)] = clean(value)

    return gates


def discover_operators():
    operators_root = ROOT / "operators"
    operators = []

    if not operators_root.exists():
        return operators

    for state_file in operators_root.glob("*/OPERATOR_STATE.yaml"):
        text = state_file.read_text(encoding="utf-8")
        operator = {
            "folder": state_file.parent.name,
            "path": str(state_file.relative_to(ROOT)),
        }

        for raw in text.splitlines():
            s = raw.strip()
            if ":" not in s:
                continue

            key, value = s.split(":", 1)
            key = clean(key)
            value = clean(value)

            if key in {
                "operator_id",
                "role",
                "current_color",
                "current_octave",
                "verdict",
            }:
                operator[key] = value

        operators.append(operator)

    return operators


def yaml_list(items, indent=4):
    space = " " * indent
    if not items:
        return f"{space}[]"
    return "\n".join(f"{space}- {item}" for item in items)


def main():
    edges_text = read_file("edges.yaml")
    gates_text = read_file("gates.yaml")

    edges = parse_edges(edges_text)
    gates = parse_gates(gates_text)
    operators = discover_operators()

    missing_edges = [
        e for e in edges
        if e.get("status", "").upper() == "MISSING"
    ]

    confirmed_edges = [
        e for e in edges
        if e.get("status", "").upper() == "CONFIRMED"
    ]

    open_gates = [
        name for name, data in gates.items()
        if data.get("status", "").upper() == "OPEN"
    ]

    closed_gates = [
        name for name, data in gates.items()
        if data.get("status", "").upper() == "CLOSED"
    ]

    missing_edge_ids = [e.get("id", "unknown_edge") for e in missing_edges]
    open_gate_ids = open_gates

    required_operators = sorted(set(
        [e.get("to_operator") for e in missing_edges if e.get("to_operator")]
        + [gates[g].get("owner") for g in open_gates if gates[g].get("owner")]
    ))

    three_v_status = "PRESENT"
    six_v_status = "INCOMPLETE" if missing_edges else "COMPLETE"
    nine_v_status = "INCOMPLETE" if open_gates else "COMPLETE"

    false_green_risk = bool(missing_edges or open_gates)

    visible_color = "GREEN"
    suspected_true_state = (
        "YELLOW_BLUE_INCOMPLETE"
        if false_green_risk
        else "TRUE_GREEN"
    )

    verdict = "HOLD" if false_green_risk else "COMMIT_ALLOWED"

    reason = (
        "Visible payment flow can be drafted, but required business document edges or Gates are incomplete."
        if false_green_risk
        else "All required edges and Gates are complete."
    )

    required_action = []
    if missing_edges:
        required_action.append("create_missing_document_edges")
    if open_gates:
        required_action.append("request_operator_gates")
    if false_green_risk:
        required_action.extend([
            "define_refund_rollback",
            "add_contact_coverage_test",
            "record_memory_atom",
        ])

    timestamp = datetime.now(timezone.utc).isoformat()

    color_verdict = f"""project_id: card_payment_feature
customer_request: "Add card payment to the website."

visible_color: {visible_color}
suspected_true_state: {suspected_true_state}
false_green_risk: {str(false_green_risk).lower()}

checked_layers:
  three_v_signal:
    status: {three_v_status}
    evidence:
      - customer_request
      - ui_payment_task
      - payment_button_possible

  six_v_route:
    status: {six_v_status}
    missing_edges:
{yaml_list(missing_edge_ids, indent=6)}

  nine_v_gate:
    status: {nine_v_status}
    missing_gates:
{yaml_list(open_gate_ids, indent=6)}

required_operators:
{yaml_list(required_operators, indent=2)}

verdict: {verdict}

required_action:
{yaml_list(required_action, indent=2)}
"""

    (ROOT / "color_verdict.yaml").write_text(color_verdict, encoding="utf-8")

    memory_atom = {
        "memory_atom_id": f"mem_card_payment_scan_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "project_id": "card_payment_feature",
        "customer_request": "Add card payment to the website.",
        "visible_color": visible_color,
        "suspected_true_state": suspected_true_state,
        "false_green_risk": false_green_risk,
        "verdict": verdict,
        "reason": reason,
        "missing_edges": missing_edge_ids,
        "open_gates": open_gate_ids,
        "required_operators": required_operators,
        "timestamp": timestamp,
    }

    with (ROOT / "memory_atoms.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(memory_atom, ensure_ascii=False) + "\n")

    report = f"""# GitCube OS Flower Company Field Scan

## Project

card_payment_feature

## Customer Request

Add card payment to the website.

## Operator Repos Detected

{len(operators)}

{chr(10).join(f"- {op.get('operator_id', op['folder'])}: color={op.get('current_color', 'UNKNOWN')}, verdict={op.get('verdict', 'UNKNOWN')}" for op in operators)}

## Result

3V signal: {three_v_status}  
6V route: {six_v_status}  
9V Gate: {nine_v_status}  

Visible color: {visible_color}  
Suspected true state: {suspected_true_state}  
False-green risk: {str(false_green_risk).lower()}  

## Confirmed Edges

{chr(10).join(f"- {e.get('id')}" for e in confirmed_edges) if confirmed_edges else "- none"}

## Missing Edges

{chr(10).join(f"- {edge}" for edge in missing_edge_ids) if missing_edge_ids else "- none"}

## Closed Gates

{chr(10).join(f"- {gate}" for gate in closed_gates) if closed_gates else "- none"}

## Open Gates

{chr(10).join(f"- {gate}" for gate in open_gate_ids) if open_gate_ids else "- none"}

## Required Operators

{chr(10).join(f"- {operator}" for operator in required_operators) if required_operators else "- none"}

## Verdict

{verdict}

## Meaning

{reason}

## Required Action

{chr(10).join(f"- {action}" for action in required_action) if required_action else "- none"}

## Final Rule

No customer code from 3V alone.  
No true-green without 6V route.  
No commit without 9V Gate.  
No AI-owned approval.
"""

    (ROOT / "scan_report.md").write_text(report, encoding="utf-8")

    print("FLOWER COMPANY FIELD SCAN")
    print()
    print("Project: card_payment_feature")
    print(f"3V signal: {three_v_status}")
    print(f"6V route: {six_v_status}")
    print(f"9V Gate: {nine_v_status}")
    print(f"visible_color: {visible_color}")
    print(f"suspected_true_state: {suspected_true_state}")
    print(f"false_green_risk: {false_green_risk}")
    print(f"verdict: {verdict}")
    print()
    print("Missing edges:")
    for edge in missing_edge_ids:
        print(f"- {edge}")
    print()
    print("Open gates:")
    for gate in open_gate_ids:
        print(f"- {gate}")
    print()
    print("Generated:")
    print("- color_verdict.yaml")
    print("- scan_report.md")
    print("- memory_atoms.jsonl")


if __name__ == "__main__":
    main()
