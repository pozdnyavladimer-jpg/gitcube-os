
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_materialization_scope import create_sandbox_candidate_reentry_materialization_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD164SandboxCandidateReentryMaterializationScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir(parents=True, exist_ok=True)

        response_id = "d163-test"
        runner_id = "d162-test"
        plan_id = "d161-test"
        review_id = "d160-test"
        scope_id = "d159-test"
        intake_id = "d158-test"
        reentry_id = "d157-test"
        next_cycle_id = "d156-test"
        proposal_id = "d107-valid-test"

        d163 = {
            "ok": True,
            "decision": "PROVIDER_RESPONSE_REENTRY_SCOPE_READY",
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
            "guardrails": {
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
                "provider_response_reentry_scope_only": True,
                "provider_response_reentry_manifest_only": True,
                "provider_response_reentry_dry_capture_receipt_only": True,
                "canonical_guard_schema_applied": True,
                "fresh_intent_required": True,
                "human_review_required": True,
                "real_provider_call_performed": False,
                "provider_response_ingested": False,
                "provider_response_captured": False,
                "dry_capture_only": True,
                "candidate_materialization_allowed_next": True,
                "candidate_payload_written": False,
                "candidate_files_created": False,
                "candidate_execution_requested": False,
                "candidate_executed": False,
                "apply_requested": False,
                "apply_executed": False,
                "approval_for_d164_sandbox_candidate_reentry_materialization_scope_only": True,
                "real_apply_allowed_after_d163_by_ai": False,
                "route_insert_allowed_after_d163_by_ai": False,
                "protected_core_mutation_allowed_after_d163_by_ai": False,
                "network_allowed_after_d163_by_ai": False,
                "secret_read_allowed_after_d163_by_ai": False,
                "shell_allowed_after_d163_by_ai": False,
                "git_action_allowed_after_d163_by_ai": False,
            },
            "summary": {
                "canonical_schema_status": "CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D163_PLUS",
                "provider_response_status": "DRY_CAPTURE_DECLARED_NO_PROVIDER_CALL_NO_NETWORK",
                "candidate_status": "SANDBOX_CANDIDATE_REENTRY_READY_FOR_MATERIALIZATION_SCOPE_NOT_WRITTEN",
                "real_provider_status": "NOT_CALLED",
                "network_status": "NOT_ACCESSED",
                "secret_status": "NOT_READ",
                "shell_status": "NOT_EXECUTED",
                "candidate_execution_status": "NOT_EXECUTED",
                "real_apply_by_ai_status": "BLOCKED",
                "route_insert_status": "BLOCKED",
                "protected_core_status": "UNTOUCHED_BY_AI",
                "approval_scope": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_ONLY",
                "next_step": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE",
            },
        }

        manifest = {
            "ok": True,
            "manifest_status": "PROVIDER_RESPONSE_REENTRY_DECLARED_DRY_CAPTURE_ONLY_NO_PROVIDER_CALL",
            "canonical_guard_schema_applied": True,
            "provider_response_reentry_scope_only": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "provider_response_captured": False,
            "provider_response_required_before_candidate": True,
            "candidate_materialization_allowed_next": True,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
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

        receipt = {
            "ok": True,
            "receipt_status": "DRY_PROVIDER_RESPONSE_CAPTURE_RECORDED_NO_NETWORK_NO_SECRET_NO_PROVIDER_CALL",
            "canonical_guard_schema_applied": True,
            "dry_capture_only": True,
            "real_provider_call_performed": False,
            "provider_response_ingested": False,
            "provider_response_captured": False,
            "network_accessed": False,
            "secret_read": False,
            "shell_executed_by_ai": False,
            "candidate_payload_written": False,
            "candidate_files_created": False,
            "candidate_execution_requested": False,
            "candidate_executed": False,
            "apply_requested": False,
            "apply_executed": False,
            "no_provider_call": True,
            "no_network": True,
            "no_secret_read": True,
            "no_shell": True,
            "no_candidate_payload_write": True,
            "no_candidate_execution": True,
            "no_apply": True,
            "no_route_insert": True,
            "no_core_mutation_by_ai": True,
            "no_git_action_by_ai": True,
            "human_review_required": True,
            "actual_apply_executed_by_ai": False,
            "real_apply_executed_by_ai": False,
            "route_inserted": False,
            "route_inserted_by_ai": False,
            "protected_core_mutated": False,
            "protected_core_mutated_by_ai": False,
            "git_action_by_ai": False,
        }

        d164_scope = {
            "ok": True,
            "allowed_next_gate": "D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE",
            "sandbox_candidate_reentry_materialization_scope_only": True,
            "fresh_intent_required": True,
            "human_review_required": True,
            "canonical_guard_schema_required": True,
            "provider_response_required_before_candidate": True,
            "provider_response_capture_required_or_dry_placeholder_allowed": True,
            "real_apply_allowed_after_d163_by_ai": False,
            "route_insert_allowed_after_d163_by_ai": False,
            "protected_core_mutation_allowed_after_d163_by_ai": False,
            "network_allowed_after_d163_by_ai": False,
            "secret_read_allowed_after_d163_by_ai": False,
            "shell_allowed_after_d163_by_ai": False,
            "git_action_allowed_after_d163_by_ai": False,
        }

        write(root / "reports/d163_provider_response_reentry_scope.json", d163)
        write(root / "reports/d163_provider_response_reentry_manifest.json", manifest)
        write(root / "reports/d163_provider_response_reentry_dry_capture_receipt.json", receipt)
        write(root / "reports/d163_d164_sandbox_candidate_reentry_materialization_scope.json", d164_scope)
        return td, root

    def test_creates_sandbox_candidate_reentry_materialization_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_materialization_scope(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE_READY")
            self.assertEqual(r["summary"]["approval_scope"], "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE_ONLY")
            self.assertEqual(r["d165_scope"]["allowed_next_gate"], "D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE")
            self.assertTrue(r["guardrails"]["candidate_payload_written"])
            self.assertTrue(r["guardrails"]["candidate_files_created"])
            self.assertFalse(r["guardrails"]["candidate_executed"])
            self.assertFalse(r["guardrails"]["apply_executed"])
            work = root / r["candidate_work_dir"]
            self.assertTrue((work / "candidate_payload.json").exists())
            self.assertTrue((work / "candidate_manifest.json").exists())
            self.assertTrue((work / "candidate_summary.md").exists())
            self.assertTrue((root / "reports/d164_sandbox_candidate_reentry_materialization_scope.json").exists())
            self.assertTrue((root / "reports/d164_sandbox_candidate_reentry_materialization_manifest.json").exists())
            self.assertTrue((root / "reports/d164_sandbox_candidate_reentry_materialization_preflight.json").exists())
            self.assertTrue((root / "reports/d164_d165_sandbox_candidate_reentry_static_validation_scope.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d163(self):
        td, root = self.root()
        try:
            (root / "reports/d163_provider_response_reentry_scope.json").unlink()
            r = create_sandbox_candidate_reentry_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_dry_capture_receipt_provider_called(self):
        td, root = self.root()
        try:
            p = root / "reports/d163_provider_response_reentry_dry_capture_receipt.json"
            data = json.loads(p.read_text())
            data["real_provider_call_performed"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_manifest_candidate_already_written(self):
        td, root = self.root()
        try:
            p = root / "reports/d163_provider_response_reentry_manifest.json"
            data = json.loads(p.read_text())
            data["candidate_payload_written"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()

    def test_blocks_if_d164_scope_allows_network(self):
        td, root = self.root()
        try:
            p = root / "reports/d163_d164_sandbox_candidate_reentry_materialization_scope.json"
            data = json.loads(p.read_text())
            data["network_allowed_after_d163_by_ai"] = True
            p.write_text(json.dumps(data), encoding="utf-8")
            r = create_sandbox_candidate_reentry_materialization_scope(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
