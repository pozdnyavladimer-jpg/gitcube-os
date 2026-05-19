
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_static_validation_scope import create_sandbox_candidate_reentry_static_validation_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD165SandboxCandidateReentryStaticValidationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        candidate_id = "d164-test"
        response_id = "d163-test"
        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"
        work_dir = Path("runtime_experimental/ai_sandbox_work") / candidate_id
        abs_work = root / work_dir
        abs_work.mkdir(parents=True, exist_ok=True)

        no_ai = {
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "git_action_by_ai": False,
        }

        candidate_payload = {
            "ok": True,
            "candidate_id": candidate_id,
            "payload_kind": "NO_OP_REENTRY_PLACEHOLDER_FOR_STATIC_VALIDATION",
            "payload_status": "MATERIALIZED_IN_SANDBOX_ONLY_NO_EXECUTION",
            "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }
        candidate_manifest = {
            "ok": True,
            "candidate_id": candidate_id,
            "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }
        write(abs_work / "candidate_payload.json", candidate_payload)
        write(abs_work / "candidate_manifest.json", candidate_manifest)
        (abs_work / "candidate_summary.md").write_text("D164 placeholder", encoding="utf-8")

        d164 = {
            "ok": True,
            "decision": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY",
            "candidate_id": candidate_id,
            "response_id": response_id,
            "runner_id": runner_id,
            "plan_id": plan_id,
            "review_id": review_id,
            "scope_id": scope_id,
            "intake_id": intake_id,
            "reentry_id": reentry_id,
            "next_cycle_id": next_cycle_id,
            "cycle_closure_id": "d155-test",
            "previous_candidate_id": "d126-test",
            "proposal_id": proposal_id,
            "candidate_work_dir": str(work_dir),
            "guardrails": {
                "sandbox_candidate_reentry_materialization_scope_only": True,
                "sandbox_candidate_reentry_materialization_manifest_only": True,
                "sandbox_candidate_reentry_materialization_preflight_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "candidate_files_created": True,
                "candidate_payload_written": True,
                "candidate_manifest_written": True,
                "candidate_summary_written": True,
                "candidate_ready_for_static_validation": True,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d165_sandbox_candidate_reentry_static_validation_scope_only": True,
                "real_apply_allowed_after_d164_by_ai": False,
                "route_insert_allowed_after_d164_by_ai": False,
                "protected_core_mutation_allowed_after_d164_by_ai": False,
                "network_allowed_after_d164_by_ai": False,
                "secret_read_allowed_after_d164_by_ai": False,
                "shell_allowed_after_d164_by_ai": False,
                "git_action_allowed_after_d164_by_ai": False,
                **no_ai,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D164_PLUS",
                "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_READY_FOR_STATIC_VALIDATION",
                "source_response_mode": "DRY_CAPTURE_PLACEHOLDER_ONLY",
                "real_provider_status": "NOT_CALLED",
                "provider_response_status": "NOT_INGESTED_DRY_PLACEHOLDER_USED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_ONLY",
                "next_step": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
            },
        }

        mat_manifest = {
            "ok": True,
            "materialization_status": "SANDBOX_CANDIDATE_REENTRY_MATERIALIZED_DRY_PLACEHOLDER_NO_EXECUTION",
            "canonical_guard_schema_applied": True,
            "sandbox_candidate_reentry_materialization_scope_only": True,
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_ready_for_static_validation": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "provider_response_captured": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "candidate_work_dir": str(work_dir),
            **no_ai,
        }

        preflight = {
            "ok": True,
            "preflight_status": "MATERIALIZATION_PREFLIGHT_READY_FOR_STATIC_VALIDATION_NO_EXECUTION",
            "candidate_work_dir": str(work_dir),
            "candidate_manifest_exists": True,
            "candidate_payload_exists": True,
            "candidate_summary_exists": True,
            "candidate_files_created": True,
            "candidate_payload_written": True,
            "candidate_manifest_written": True,
            "candidate_summary_written": True,
            "candidate_ready_for_static_validation": True,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            **no_ai,
        }

        d165_scope = {
            "ok": True,
            "allowed_next_gate": "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE",
            "sandbox_candidate_reentry_static_validation_scope_only": True,
            "candidate_files_required": True,
            "candidate_work_dir": str(work_dir),
            "candidate_payload_path": str(work_dir / "candidate_payload.json"),
            "candidate_manifest_path": str(work_dir / "candidate_manifest.json"),
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "candidate_execution_allowed": False,
            "real_apply_allowed_after_d164_by_ai": False,
            "route_insert_allowed_after_d164_by_ai": False,
            "protected_core_mutation_allowed_after_d164_by_ai": False,
            "network_allowed_after_d164_by_ai": False,
            "secret_read_allowed_after_d164_by_ai": False,
            "shell_allowed_after_d164_by_ai": False,
            "git_action_allowed_after_d164_by_ai": False,
        }

        write(root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json", d164)
        write(root / "reports/d164_sandbox_candidate_reentry_materialization_manifest.json", mat_manifest)
        write(root / "reports/d164_sandbox_candidate_reentry_materialization_preflight.json", preflight)
        write(root / "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json", d165_scope)
        return td, root

    def test_creates_static_validation_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE_ONLY")
            self.assertEqual(r["d166_scope"]["allowed_next_gate"], "D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE")
            self.assertTrue(r["guardrails"]["candidate_static_validation_passed"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_scope.json").exists())
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_report.json").exists())
            self.assertTrue((root / "reports/d165_sandbox_candidate_reentry_static_validation_receipt.json").exists())
            self.assertTrue((root / "reports/d165_d166_sandbox_candidate_reentry_controlled_execution_preflight_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d164(self):
        td, root = self.root()
        try:
            (root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").unlink()
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_missing_candidate_payload(self):
        td, root = self.root()
        try:
            d164 = json.loads((root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").read_text())
            (root / d164["candidate_work_dir"] / "candidate_payload.json").unlink()
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_payload_requests_execution(self):
        td, root = self.root()
        try:
            d164 = json.loads((root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").read_text())
            p = root / d164["candidate_work_dir"] / "candidate_payload.json"
            data = json.loads(p.read_text())
            data["candidate_execution_requested"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d165_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d164_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_static_validation_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
