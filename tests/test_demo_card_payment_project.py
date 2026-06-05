from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "demo_card_payment_project"
MEMORY = DEMO / "memory_atoms.jsonl"


def test_demo_card_payment_scanner_detects_false_green():
    old_memory = MEMORY.read_text(encoding="utf-8") if MEMORY.exists() else ""

    try:
        result = subprocess.run(
            [sys.executable, str(DEMO / "scan_demo.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        output = result.stdout

        assert "FLOWER COMPANY FIELD SCAN" in output
        assert "3V signal: PRESENT" in output
        assert "6V route: INCOMPLETE" in output
        assert "9V Gate: INCOMPLETE" in output
        assert "visible_color: GREEN" in output
        assert "suspected_true_state: YELLOW_BLUE_INCOMPLETE" in output
        assert "false_green_risk: True" in output
        assert "verdict: HOLD" in output

        color_verdict = (DEMO / "color_verdict.yaml").read_text(encoding="utf-8")
        scan_report = (DEMO / "scan_report.md").read_text(encoding="utf-8")

        assert "visible_color: GREEN" in color_verdict
        assert "suspected_true_state: YELLOW_BLUE_INCOMPLETE" in color_verdict
        assert "false_green_risk: true" in color_verdict
        assert "verdict: HOLD" in color_verdict

        assert "## Verdict" in scan_report
        assert "HOLD" in scan_report
        assert "No customer code from 3V alone." in scan_report

    finally:
        MEMORY.write_text(old_memory, encoding="utf-8")
