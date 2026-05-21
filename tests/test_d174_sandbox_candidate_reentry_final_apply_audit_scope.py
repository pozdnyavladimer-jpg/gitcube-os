
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_candidate_reentry_final_apply_audit_scope import create_sandbox_candidate_reentry_final_apply_audit_scope


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding='utf-8')


def no_ai_flags():
    return {
        'network_accessed': False,
        'secret_read': False,
        'shell_executed_by_ai': False,
        'actual_apply_executed_by_ai': False,
        'real_apply_executed_by_ai': False,
        'route_inserted': False,
        'route_inserted_by_ai': False,
        'protected_core_mutated': False,
        'protected_core_mutated_by_ai': False,
        'git_action_by_ai': False,
        'candidate_apply_executed': False,
        'candidate_apply_executed_by_ai': False,
        'real_apply_executed': False,
        'actual_apply_executed': False,
        'apply_requested': False,
        'apply_executed': False,
        'real_provider_call_performed': False,
        'provider_response_ingested': False,
        'provider_response_captured': False,
    }


class TestD174SandboxCandidateReentryFinalApplyAuditScope(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / 'reports').mkdir(parents=True, exist_ok=True)

        ids = {
            'post_apply_verification_id': 'd173-test',
            'guarded_apply_id': 'd172-test',
            'apply_intent_id': 'd171-test',
            'apply_preflight_id': 'd170-test',
            'verification_id': 'd169-test',
            'run_id': 'd168-test',
            'intent_id': 'd167-test',
            'preflight_id': 'd166-test',
            'validation_id': 'd165-test',
            'candidate_id': 'd164-test',
            'response_id': 'd163-test',
            'runner_id': 'd162-test',
            'plan_id': 'd161-test',
            'review_id': 'd160-test',
            'scope_id': 'd159-test',
            'intake_id': 'd158-test',
            'reentry_id': 'd157-test',
            'next_cycle_id': 'd156-test',
            'cycle_closure_id': 'd155-test',
            'previous_candidate_id': 'd126-test',
            'proposal_id': 'd107-valid-test',
        }

        d173 = {
            'ok': True,
            'decision': 'SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_READY',
            **ids,
            'guardrails': {
                **no_ai_flags(),
                'sandbox_candidate_reentry_post_apply_verification_scope_only': True,
                'sandbox_candidate_reentry_post_apply_verification_report_only': True,
                'sandbox_candidate_reentry_apply_integrity_receipt_only': True,
                'canonical_guard_schema_applied': True,
                'fresh_intent_required': True,
                'human_review_required': True,
                'guarded_apply_recorded': True,
                'candidate_apply_recorded': True,
                'post_apply_verified': True,
                'apply_integrity_verified': True,
                'approval_for_d174_sandbox_candidate_reentry_final_apply_audit_scope_only': True,
                'real_apply_allowed_after_d173_by_ai': False,
                'route_insert_allowed_after_d173_by_ai': False,
                'protected_core_mutation_allowed_after_d173_by_ai': False,
                'network_allowed_after_d173_by_ai': False,
                'secret_read_allowed_after_d173_by_ai': False,
                'shell_allowed_after_d173_by_ai': False,
                'git_action_allowed_after_d173_by_ai': False,
            },
            'summary': {
                'canonical_schema_status': 'CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D173_PLUS',
                'post_apply_verification_status': 'GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY',
                'apply_integrity_receipt_status': 'POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY',
                'candidate_status': 'SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFIED_READY_FOR_FINAL_APPLY_AUDIT',
                'real_provider_status': 'NOT_CALLED',
                'provider_response_status': 'NOT_INGESTED_DRY_PLACEHOLDER_USED',
                'network_status': 'NOT_ACCESSED',
                'secret_status': 'NOT_READ',
                'shell_status': 'NOT_EXECUTED',
                'candidate_execution_status': 'EXECUTED_IN_SANDBOX_NO_OP_ONLY',
                'real_apply_by_ai_status': 'BLOCKED',
                'route_insert_status': 'BLOCKED',
                'protected_core_status': 'UNTOUCHED_BY_AI',
                'approval_scope': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_ONLY',
                'next_step': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE',
            },
        }

        post_report = {
            **no_ai_flags(),
            'ok': True,
            'post_apply_verification_status': 'GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY',
            'guarded_apply_recorded': True,
            'candidate_apply_recorded': True,
            'no_real_apply': True,
            'no_network': True,
            'no_secret_read': True,
            'no_shell': True,
            'no_route_insert': True,
            'no_core_mutation_by_ai': True,
            'no_git_action_by_ai': True,
        }
        receipt = dict(post_report)
        receipt['apply_integrity_receipt_status'] = 'POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY'
        receipt.pop('post_apply_verification_status')

        d174_scope = {
            'ok': True,
            'allowed_next_gate': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE',
            'sandbox_candidate_reentry_final_apply_audit_scope_only': True,
            'post_apply_verified': True,
            'apply_integrity_verified': True,
            'guarded_apply_recorded': True,
            'candidate_apply_recorded': True,
            'candidate_apply_executed': False,
            'candidate_apply_executed_by_ai': False,
            'fresh_intent_required': True,
            'human_review_required': True,
            'canonical_guard_schema_required': True,
            'real_apply_allowed_after_d173_by_ai': False,
            'route_insert_allowed_after_d173_by_ai': False,
            'protected_core_mutation_allowed_after_d173_by_ai': False,
            'network_allowed_after_d173_by_ai': False,
            'secret_read_allowed_after_d173_by_ai': False,
            'shell_allowed_after_d173_by_ai': False,
            'git_action_allowed_after_d173_by_ai': False,
        }

        write(root / 'reports/d173_sandbox_candidate_reentry_post_apply_verification_scope.json', d173)
        write(root / 'reports/d173_sandbox_candidate_reentry_post_apply_verification_report.json', post_report)
        write(root / 'reports/d173_sandbox_candidate_reentry_apply_integrity_receipt.json', receipt)
        write(root / 'reports/d173_d174_sandbox_candidate_reentry_final_apply_audit_scope.json', d174_scope)
        return td, root

    def test_creates_final_apply_audit_outputs(self):
        td, root = self.root()
        try:
            r = create_sandbox_candidate_reentry_final_apply_audit_scope(root)
            self.assertTrue(r['ok'])
            self.assertEqual(r['decision'], 'SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_READY')
            self.assertEqual(r['summary']['approval_scope'], 'D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_ONLY')
            self.assertEqual(r['d175_scope']['allowed_next_gate'], 'D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE')
            self.assertTrue(r['guardrails']['final_apply_audit_complete'])
            self.assertFalse(r['guardrails']['real_apply_executed'])
            self.assertTrue((root / 'reports/d174_sandbox_candidate_reentry_final_apply_audit_scope.json').exists())
            self.assertTrue((root / 'reports/d174_sandbox_candidate_reentry_final_apply_ledger.json').exists())
            self.assertTrue((root / 'reports/d174_sandbox_candidate_reentry_replay_index.json').exists())
            self.assertTrue((root / 'reports/d174_d175_sandbox_candidate_reentry_chain_archive_scope.json').exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d173(self):
        td, root = self.root()
        try:
            (root / 'reports/d173_sandbox_candidate_reentry_post_apply_verification_scope.json').unlink()
            r = create_sandbox_candidate_reentry_final_apply_audit_scope(root)
            self.assertFalse(r['ok'])
        finally:
            td.cleanup()

    def test_blocks_if_post_report_executed_by_ai(self):
        td, root = self.root()
        try:
            p = root / 'reports/d173_sandbox_candidate_reentry_post_apply_verification_report.json'
            data = json.loads(p.read_text())
            data['candidate_apply_executed_by_ai'] = True
            p.write_text(json.dumps(data), encoding='utf-8')
            r = create_sandbox_candidate_reentry_final_apply_audit_scope(root)
            self.assertFalse(r['ok'])
        finally:
            td.cleanup()

    def test_blocks_if_receipt_real_apply_executed(self):
        td, root = self.root()
        try:
            p = root / 'reports/d173_sandbox_candidate_reentry_apply_integrity_receipt.json'
            data = json.loads(p.read_text())
            data['real_apply_executed'] = True
            p.write_text(json.dumps(data), encoding='utf-8')
            r = create_sandbox_candidate_reentry_final_apply_audit_scope(root)
            self.assertFalse(r['ok'])
        finally:
            td.cleanup()

    def test_blocks_if_d174_scope_allows_shell(self):
        td, root = self.root()
        try:
            p = root / 'reports/d173_d174_sandbox_candidate_reentry_final_apply_audit_scope.json'
            data = json.loads(p.read_text())
            data['shell_allowed_after_d173_by_ai'] = True
            p.write_text(json.dumps(data), encoding='utf-8')
            r = create_sandbox_candidate_reentry_final_apply_audit_scope(root)
            self.assertFalse(r['ok'])
        finally:
            td.cleanup()


if __name__ == '__main__':
    unittest.main()
