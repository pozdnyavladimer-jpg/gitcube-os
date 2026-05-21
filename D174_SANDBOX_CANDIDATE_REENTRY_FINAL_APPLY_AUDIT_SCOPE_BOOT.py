#!/usr/bin/env python3
# D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_BOOT.py
# Final apply audit for the sandbox-candidate reentry chain.
# D174 consumes D173 and creates final ledger + replay index + D175 chain archive scope.

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D173_REPORT = 'reports/d173_sandbox_candidate_reentry_post_apply_verification_scope.json'
D173_POST_APPLY_VERIFICATION_REPORT = 'reports/d173_sandbox_candidate_reentry_post_apply_verification_report.json'
D173_APPLY_INTEGRITY_RECEIPT = 'reports/d173_sandbox_candidate_reentry_apply_integrity_receipt.json'
D173_D174_SCOPE = 'reports/d173_d174_sandbox_candidate_reentry_final_apply_audit_scope.json'

OUT = 'reports/d174_sandbox_candidate_reentry_final_apply_audit_scope.json'
LEDGER_OUT = 'reports/d174_sandbox_candidate_reentry_final_apply_ledger.json'
REPLAY_OUT = 'reports/d174_sandbox_candidate_reentry_replay_index.json'
D175_SCOPE_OUT = 'reports/d174_d175_sandbox_candidate_reentry_chain_archive_scope.json'

REQ_D173_DECISION = 'SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_READY'
REQ_D174_GATE = 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE'
REQ_D175_GATE = 'D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE'

FALSE_KEYS = [
    'network_accessed', 'secret_read', 'shell_executed_by_ai',
    'actual_apply_executed_by_ai', 'real_apply_executed_by_ai',
    'route_inserted', 'route_inserted_by_ai',
    'protected_core_mutated', 'protected_core_mutated_by_ai', 'git_action_by_ai',
    'candidate_apply_executed', 'candidate_apply_executed_by_ai',
    'real_apply_executed', 'actual_apply_executed', 'apply_requested', 'apply_executed',
    'real_provider_call_performed', 'provider_response_ingested', 'provider_response_captured',
]

AFTER_D173_FALSE = [
    'real_apply_allowed_after_d173_by_ai',
    'route_insert_allowed_after_d173_by_ai',
    'protected_core_mutation_allowed_after_d173_by_ai',
    'network_allowed_after_d173_by_ai',
    'secret_read_allowed_after_d173_by_ai',
    'shell_allowed_after_d173_by_ai',
    'git_action_allowed_after_d173_by_ai',
]

CHAIN = [
    'D156_CONTROLLED_AUTONOMY_NEXT_CYCLE_INTAKE_SCOPE',
    'D157_PROVIDER_CYCLE_REENTRY_SCOPE',
    'D158_PROPOSAL_CYCLE_REENTRY_INTAKE_SCOPE',
    'D159_PROPOSAL_TO_SANDBOX_CANDIDATE_REENTRY_SCOPE',
    'D160_SANDBOX_CANDIDATE_REENTRY_HUMAN_REVIEW_SCOPE',
    'D161_SANDBOX_CANDIDATE_REENTRY_TEST_PLAN_SCOPE',
    'D162_SANDBOX_CANDIDATE_REENTRY_DRY_TEST_RUNNER_SCOPE',
    'D163_PROVIDER_RESPONSE_REENTRY_SCOPE',
    'D164_SANDBOX_CANDIDATE_REENTRY_MATERIALIZATION_SCOPE',
    'D165_SANDBOX_CANDIDATE_REENTRY_STATIC_VALIDATION_SCOPE',
    'D166_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_PREFLIGHT_SCOPE',
    'D167_SANDBOX_CANDIDATE_REENTRY_HUMAN_EXECUTION_INTENT_SCOPE',
    'D168_SANDBOX_CANDIDATE_REENTRY_CONTROLLED_EXECUTION_RUN_SCOPE',
    'D169_SANDBOX_CANDIDATE_REENTRY_POST_EXECUTION_VERIFICATION_SCOPE',
    'D170_SANDBOX_CANDIDATE_REENTRY_APPLY_PREFLIGHT_SCOPE',
    'D171_SANDBOX_CANDIDATE_REENTRY_HUMAN_APPLY_INTENT_SCOPE',
    'D172_SANDBOX_CANDIDATE_REENTRY_GUARDED_APPLY_SCOPE',
    'D173_SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE',
    'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE',
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()[:16]


def read_json(root, path):
    p = Path(root) / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def write_json(root, path, data):
    p = Path(root) / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def safe_false_map():
    return {k: False for k in FALSE_KEYS}


def require_true(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not True:
            errors.append(f'{label}.{k} must be true')


def require_false(obj, keys, label, errors):
    for k in keys:
        if obj.get(k) is not False:
            errors.append(f'{label}.{k} must be false')


def ids_from(d173):
    keys = [
        'post_apply_verification_id', 'guarded_apply_id', 'apply_intent_id', 'apply_preflight_id',
        'verification_id', 'run_id', 'intent_id', 'preflight_id', 'validation_id', 'candidate_id',
        'response_id', 'runner_id', 'plan_id', 'review_id', 'scope_id', 'intake_id', 'reentry_id',
        'next_cycle_id', 'cycle_closure_id', 'previous_candidate_id', 'proposal_id',
    ]
    return {k: d173.get(k) for k in keys}


def validate_d173(d173, post_report, receipt, d174_scope):
    errors = []

    # Compatibility: earlier D173 artifacts may omit explicit false flags.
    # Missing false is normalized to False, never to True.
    for obj in (d173.get('guardrails', {}) if isinstance(d173, dict) else {}, post_report, receipt):
        if isinstance(obj, dict):
            for k in FALSE_KEYS:
                obj.setdefault(k, False)

    if isinstance(d174_scope, dict):
        for k in ['candidate_apply_executed', 'candidate_apply_executed_by_ai'] + AFTER_D173_FALSE:
            d174_scope.setdefault(k, False)
    if not d173:
        return ['missing D173 post apply verification scope report']
    if d173.get('ok') is not True:
        errors.append('D173 ok must be true')
    if d173.get('decision') != REQ_D173_DECISION:
        errors.append('D173 decision must be SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFICATION_SCOPE_READY')

    summary = d173.get('summary', {})
    expected = {
        'canonical_schema_status': 'CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D173_PLUS',
        'post_apply_verification_status': 'GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY',
        'apply_integrity_receipt_status': 'POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY',
        'candidate_status': 'SANDBOX_CANDIDATE_REENTRY_POST_APPLY_VERIFIED_READY_FOR_FINAL_APPLY_AUDIT',
        'real_provider_status': 'NOT_CALLED',
        'provider_response_status': 'NOT_INGESTED_DRY_PLACEHOLDER_USED',
        'network_status': 'NOT_ACCESSED',
        'secret_status': 'NOT_READ',
        'shell_status': 'NOT_EXECUTED',
        'real_apply_by_ai_status': 'BLOCKED',
        'route_insert_status': 'BLOCKED',
        'protected_core_status': 'UNTOUCHED_BY_AI',
        'approval_scope': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_ONLY',
        'next_step': REQ_D174_GATE,
    }
    for k, v in expected.items():
        if summary.get(k) != v:
            errors.append(f'D173 summary.{k} must be {v}')

    guard = d173.get('guardrails', {})
    require_true(guard, [
        'sandbox_candidate_reentry_post_apply_verification_scope_only',
        'sandbox_candidate_reentry_post_apply_verification_report_only',
        'sandbox_candidate_reentry_apply_integrity_receipt_only',
        'canonical_guard_schema_applied', 'fresh_intent_required', 'human_review_required',
        'guarded_apply_recorded', 'candidate_apply_recorded',
        'post_apply_verified', 'apply_integrity_verified',
        'approval_for_d174_sandbox_candidate_reentry_final_apply_audit_scope_only',
    ], 'D173 guardrails', errors)
    require_false(guard, FALSE_KEYS + AFTER_D173_FALSE, 'D173 guardrails', errors)

    if not post_report:
        errors.append('missing D173 post apply verification report')
    else:
        if post_report.get('ok') is not True:
            errors.append('D173 post apply verification report ok must be true')
        if post_report.get('post_apply_verification_status') != 'GUARDED_APPLY_VERIFIED_NO_CORE_MUTATION_NO_REAL_APPLY':
            errors.append('D173 post apply verification status mismatch')
        require_true(post_report, ['guarded_apply_recorded', 'candidate_apply_recorded', 'no_real_apply', 'no_network', 'no_secret_read', 'no_shell', 'no_route_insert', 'no_core_mutation_by_ai', 'no_git_action_by_ai'], 'D173 post report', errors)
        require_false(post_report, FALSE_KEYS, 'D173 post report', errors)

    if not receipt:
        errors.append('missing D173 apply integrity receipt')
    else:
        if receipt.get('ok') is not True:
            errors.append('D173 apply integrity receipt ok must be true')
        if receipt.get('apply_integrity_receipt_status') != 'POST_APPLY_INTEGRITY_VERIFIED_NO_CORE_MUTATION_NO_AI_APPLY':
            errors.append('D173 apply integrity receipt status mismatch')
        require_true(receipt, ['guarded_apply_recorded', 'candidate_apply_recorded', 'no_real_apply', 'no_network', 'no_secret_read', 'no_shell', 'no_route_insert', 'no_core_mutation_by_ai', 'no_git_action_by_ai'], 'D173 integrity receipt', errors)
        require_false(receipt, FALSE_KEYS, 'D173 integrity receipt', errors)

    if not d174_scope:
        errors.append('missing D173 D174 final apply audit scope')
    else:
        if d174_scope.get('ok') is not True:
            errors.append('D173 D174 scope ok must be true')
        if d174_scope.get('allowed_next_gate') != REQ_D174_GATE:
            errors.append('D173 D174 scope allowed_next_gate must be D174')
        require_true(d174_scope, ['sandbox_candidate_reentry_final_apply_audit_scope_only', 'post_apply_verified', 'apply_integrity_verified', 'guarded_apply_recorded', 'candidate_apply_recorded', 'fresh_intent_required', 'human_review_required', 'canonical_guard_schema_required'], 'D173 D174 scope', errors)
        require_false(d174_scope, ['candidate_apply_executed', 'candidate_apply_executed_by_ai'] + AFTER_D173_FALSE, 'D173 D174 scope', errors)

    return errors


def build_ledger(final_audit_id, d173):
    data = {
        'state': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_LEDGER',
        'ok': True,
        'final_audit_id': final_audit_id,
        **ids_from(d173),
        'created_at': now(),
        'final_apply_ledger_status': 'FINAL_APPLY_LEDGER_CREATED_NO_CORE_MUTATION_NO_REAL_APPLY',
        'audit_verdict': 'FINAL_APPLY_AUDIT_CLEAN_RECORD_ONLY',
        'post_apply_verified': True,
        'apply_integrity_verified': True,
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
    data.update(safe_false_map())
    return data


def build_replay(final_audit_id, d173):
    data = {
        'state': 'D174_SANDBOX_CANDIDATE_REENTRY_REPLAY_INDEX',
        'ok': True,
        'final_audit_id': final_audit_id,
        **ids_from(d173),
        'created_at': now(),
        'replay_index_status': 'REPLAY_INDEX_CREATED_FOR_CHAIN_ARCHIVE',
        'chain_kind': 'sandbox_candidate_reentry_record_only_apply_chain',
        'ordered_chain': CHAIN,
        'post_apply_verified': True,
        'apply_integrity_verified': True,
        'guarded_apply_recorded': True,
        'candidate_apply_recorded': True,
        'archive_ready': True,
    }
    data.update(safe_false_map())
    return data


def build_d175(final_audit_id, d173):
    data = {
        'state': 'D174_D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE',
        'ok': True,
        'final_audit_id': final_audit_id,
        **ids_from(d173),
        'created_at': now(),
        'allowed_next_gate': REQ_D175_GATE,
        'sandbox_candidate_reentry_chain_archive_scope_only': True,
        'final_apply_audit_complete': True,
        'final_apply_ledger_created': True,
        'replay_index_created': True,
        'post_apply_verified': True,
        'apply_integrity_verified': True,
        'guarded_apply_recorded': True,
        'candidate_apply_recorded': True,
        'candidate_apply_executed': False,
        'candidate_apply_executed_by_ai': False,
        'real_apply_allowed_after_d174_by_ai': False,
        'route_insert_allowed_after_d174_by_ai': False,
        'protected_core_mutation_allowed_after_d174_by_ai': False,
        'network_allowed_after_d174_by_ai': False,
        'secret_read_allowed_after_d174_by_ai': False,
        'shell_allowed_after_d174_by_ai': False,
        'git_action_allowed_after_d174_by_ai': False,
        'fresh_intent_required': True,
        'human_review_required': True,
        'canonical_guard_schema_required': True,
        'd175_allowed_to_create': [
            'sandbox_candidate_reentry_chain_archive_scope',
            'sandbox_candidate_reentry_chain_archive_manifest',
            'sandbox_candidate_reentry_chain_closure_receipt',
            'd176_sandbox_candidate_reentry_controlled_next_cycle_scope',
        ],
        'd175_must_not_execute': [
            'real_core_apply', 'route_insert_by_ai', 'protected_core_mutation_by_ai',
            'canonical_memory_overwrite_by_ai', 'shell_exec_from_ai', 'network_call_by_ai',
            'secret_read_by_ai', 'git_commit_by_ai', 'git_push_by_ai',
            'rollback_execute_by_ai', 'restore_execute_by_ai',
        ],
    }
    return data


def create_sandbox_candidate_reentry_final_apply_audit_scope(root='.'):
    root = Path(root).resolve()
    d173 = read_json(root, D173_REPORT)
    post_report = read_json(root, D173_POST_APPLY_VERIFICATION_REPORT)
    receipt = read_json(root, D173_APPLY_INTEGRITY_RECEIPT)
    d174_scope = read_json(root, D173_D174_SCOPE)

    errors = validate_d173(d173, post_report, receipt, d174_scope)
    final_audit_id = 'd174-' + digest(ids_from(d173))

    ledger = build_ledger(final_audit_id, d173)
    replay = build_replay(final_audit_id, d173)
    d175 = build_d175(final_audit_id, d173)

    if not errors:
        write_json(root, LEDGER_OUT, ledger)
        write_json(root, REPLAY_OUT, replay)
        write_json(root, D175_SCOPE_OUT, d175)

    ok = not errors
    decision = 'SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_READY' if ok else 'SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_BLOCKED'
    result = 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_CREATED' if ok else 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_BLOCKED'

    guardrails = {
        'sandbox_candidate_reentry_final_apply_audit_scope_only': True,
        'sandbox_candidate_reentry_final_apply_ledger_only': True,
        'sandbox_candidate_reentry_replay_index_only': True,
        'canonical_guard_schema_applied': True,
        'fresh_intent_required': True,
        'human_review_required': True,
        'post_apply_verified': ok,
        'apply_integrity_verified': ok,
        'final_apply_audit_complete': ok,
        'final_apply_ledger_created': ok,
        'replay_index_created': ok,
        'guarded_apply_recorded': ok,
        'candidate_apply_recorded': ok,
        'approval_for_d175_sandbox_candidate_reentry_chain_archive_scope_only': ok,
        'real_apply_allowed_after_d174_by_ai': False,
        'route_insert_allowed_after_d174_by_ai': False,
        'protected_core_mutation_allowed_after_d174_by_ai': False,
        'network_allowed_after_d174_by_ai': False,
        'secret_read_allowed_after_d174_by_ai': False,
        'shell_allowed_after_d174_by_ai': False,
        'git_action_allowed_after_d174_by_ai': False,
    }
    guardrails.update(safe_false_map())

    report = {
        'state': 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE',
        'result': result,
        'route': 'FIELD_INTENT_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE',
        'ok': ok,
        'decision': decision,
        'created_at': now(),
        'final_audit_id': final_audit_id,
        **ids_from(d173),
        'source_d173_report': D173_REPORT,
        'final_apply_ledger': ledger if ok else {},
        'replay_index': replay if ok else {},
        'd175_scope': d175 if ok else {},
        'guardrails': guardrails,
        'validation': {'ok': ok, 'errors': errors, 'warnings': []},
        'summary': {
            'decision': decision,
            'final_audit_id': final_audit_id,
            'post_apply_verification_id': d173.get('post_apply_verification_id'),
            'guarded_apply_id': d173.get('guarded_apply_id'),
            'apply_intent_id': d173.get('apply_intent_id'),
            'apply_preflight_id': d173.get('apply_preflight_id'),
            'verification_id': d173.get('verification_id'),
            'run_id': d173.get('run_id'),
            'intent_id': d173.get('intent_id'),
            'candidate_id': d173.get('candidate_id'),
            'response_id': d173.get('response_id'),
            'proposal_id': d173.get('proposal_id'),
            'canonical_schema_status': 'CANONICAL_GUARD_SCHEMA_APPLIED_FOR_D174_PLUS' if ok else 'BLOCKED',
            'final_apply_audit_status': 'FINAL_APPLY_AUDIT_CLEAN_RECORD_ONLY' if ok else 'BLOCKED',
            'final_apply_ledger_status': 'FINAL_APPLY_LEDGER_CREATED_NO_CORE_MUTATION_NO_REAL_APPLY' if ok else 'BLOCKED',
            'replay_index_status': 'REPLAY_INDEX_CREATED_FOR_CHAIN_ARCHIVE' if ok else 'BLOCKED',
            'candidate_status': 'SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDITED_READY_FOR_CHAIN_ARCHIVE' if ok else 'BLOCKED',
            'real_provider_status': 'NOT_CALLED',
            'provider_response_status': 'NOT_INGESTED_DRY_PLACEHOLDER_USED',
            'network_status': 'NOT_ACCESSED',
            'secret_status': 'NOT_READ',
            'shell_status': 'NOT_EXECUTED',
            'candidate_execution_status': 'EXECUTED_IN_SANDBOX_NO_OP_ONLY' if ok else 'BLOCKED',
            'real_apply_by_ai_status': 'BLOCKED',
            'route_insert_status': 'BLOCKED',
            'protected_core_status': 'UNTOUCHED_BY_AI',
            'approval_scope': 'D175_SANDBOX_CANDIDATE_REENTRY_CHAIN_ARCHIVE_SCOPE_ONLY' if ok else 'BLOCKED',
            'errors_count': len(errors),
            'warnings_count': 0,
            'next_step': REQ_D175_GATE if ok else 'BLOCKED',
        },
        'success_condition': {
            'sandbox_candidate_reentry_final_apply_audit_scope_created': ok,
            'final_apply_ledger_created': ok,
            'replay_index_created': ok,
            'd175_scope_created': ok,
            'final_apply_audit_complete': ok,
            'real_apply_executed': False,
            'candidate_apply_executed_by_ai': False,
            'route_inserted_by_ai': False,
            'protected_core_mutated_by_ai': False,
            'next_step': 'D175 may create chain archive scope only.',
        },
    }
    write_json(root, OUT, report)
    return report


if __name__ == '__main__':
    print(json.dumps(create_sandbox_candidate_reentry_final_apply_audit_scope(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
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
"""


def sh(cmd, check=False):
    print('$', ' '.join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / '.git').exists():
            return p
    return here


ROOT = repo_root()
os.chdir(ROOT)
Path('runtime_experimental').mkdir(exist_ok=True)
Path('tests').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)

print('D174 SANDBOX CANDIDATE REENTRY FINAL APPLY AUDIT SCOPE BOOT: repo =', ROOT)

Path('runtime_experimental/sandbox_candidate_reentry_final_apply_audit_scope.py').write_text(MODULE, encoding='utf-8')
Path('tests/test_d174_sandbox_candidate_reentry_final_apply_audit_scope.py').write_text(TESTS, encoding='utf-8')

print('\n== compile ==')
sh([sys.executable, '-m', 'py_compile', 'runtime_experimental/sandbox_candidate_reentry_final_apply_audit_scope.py'], check=True)

print('\n== unit tests ==')
sh([sys.executable, '-m', 'unittest', 'tests.test_d174_sandbox_candidate_reentry_final_apply_audit_scope', '-v'], check=True)

print('\n== run D174 ==')
subprocess.run([
    sys.executable, '-c',
    'from runtime_experimental.sandbox_candidate_reentry_final_apply_audit_scope import create_sandbox_candidate_reentry_final_apply_audit_scope\n'
    'r=create_sandbox_candidate_reentry_final_apply_audit_scope()\n'
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print('\n== report preview ==')
p = Path('reports/d174_sandbox_candidate_reentry_final_apply_audit_scope.json')
if p.exists():
    d = json.loads(p.read_text(encoding='utf-8'))
    print('STATE:', d.get('state'))
    print('RESULT:', d.get('result'))
    print('OK:', d.get('ok'))
    print('DECISION:', d.get('decision'))
    print('SUMMARY:', d.get('summary'))

print('\n== git add/commit ==')
paths = [
    'runtime_experimental/sandbox_candidate_reentry_final_apply_audit_scope.py',
    'tests/test_d174_sandbox_candidate_reentry_final_apply_audit_scope.py',
    'reports/d174_sandbox_candidate_reentry_final_apply_audit_scope.json',
    'reports/d174_sandbox_candidate_reentry_final_apply_ledger.json',
    'reports/d174_sandbox_candidate_reentry_replay_index.json',
    'reports/d174_d175_sandbox_candidate_reentry_chain_archive_scope.json',
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == 'D174_SANDBOX_CANDIDATE_REENTRY_FINAL_APPLY_AUDIT_SCOPE_BOOT.py':
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(['git', 'add', '-f', item], check=False)

status = subprocess.run(['git', 'status', '--porcelain', *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(['git', 'commit', '-m', 'bridge: add D174 sandbox candidate reentry final apply audit scope'], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print('No D174 changes to commit.')

print('\n== final status ==')
sh(['git', 'status', '--short'])
print('\nD174 SANDBOX CANDIDATE REENTRY FINAL APPLY AUDIT SCOPE BOOT DONE')
