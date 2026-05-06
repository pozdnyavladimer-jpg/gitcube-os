import json,tempfile,unittest
from pathlib import Path
from runtime_experimental.ai_proposal_intake import create_ai_proposal_intake

class TestD81AIProposalIntake(unittest.TestCase):
    def make_root(self):
        td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/"reports").mkdir(parents=True)
        bid="d80-test-boundary"; pid="d80-proposal-test"
        (root/"reports/d80_ai_provider_boundary.json").write_text(json.dumps({"ok":True,"decision":"AI_PROVIDER_BOUNDARY_READY","boundary_id":bid,"boundary":{"boundary_id":bid,"provider":"mock_local","mode":"PROPOSE_ONLY","network_access_allowed":False,"external_ai_call_allowed":False,"raw_code_execution_allowed":False,"shell_command_generation_allowed":False,"git_commit_allowed":False,"actual_apply_allowed":False,"route_insert_allowed":False},"guardrails":{"external_ai_called":False,"network_accessed":False,"runtime_code_mutated":False,"protected_core_mutated":False,"canonical_memory_mutated":False,"actual_apply_executed":False,"route_inserted":False,"proposal_only":True}}),encoding="utf-8")
        (root/"reports/d80_ai_provider_mock_proposal.json").write_text(json.dumps({"state":"D80_AI_PROVIDER_MOCK_PROPOSAL","ok":True,"proposal_id":pid,"provider":"mock_local","mode":"PROPOSE_ONLY","proposal":{"type":"NEXT_MODULE_PROPOSAL","recommended_next_module":"D81_AI_PROPOSAL_INTAKE","action":"CREATE_JSON_INTAKE_GATE_FOR_AI_PROPOSALS","allowed_output_contract":{"format":"json","required_fields":["proposal_id","proposal_type","target_scope","candidate_files","guardrails","validation_plan"],"forbidden_fields":["raw_shell_command","auto_apply","direct_core_edit","api_secret"]}},"guardrails":{"external_ai_called":False,"runtime_code_mutated":False,"protected_core_mutated":False,"canonical_memory_mutated":False,"actual_apply_executed":False,"route_inserted":False,"proposal_only":True,"mock_provider_only":True}}),encoding="utf-8")
        return td,root
    def test_creates_json_only_intake(self):
        td,root=self.make_root()
        try:
            r=create_ai_proposal_intake(root=root)
            self.assertTrue(r["ok"]); self.assertEqual(r["decision"],"AI_PROPOSAL_INTAKE_READY")
            self.assertEqual(r["intake_contract"]["mode"],"JSON_CONTRACT_ONLY")
            self.assertFalse(r["guardrails"]["actual_apply_executed"]); self.assertTrue(r["guardrails"]["json_only"])
            self.assertTrue((root/"reports/d81_ai_proposal_intake.json").exists())
            self.assertTrue((root/"reports/d81_ai_proposal_intake_contract.json").exists())
        finally: td.cleanup()
    def test_blocks_missing_boundary(self):
        td,root=self.make_root()
        try:
            (root/"reports/d80_ai_provider_boundary.json").unlink()
            r=create_ai_proposal_intake(root=root)
            self.assertFalse(r["ok"]); self.assertEqual(r["decision"],"AI_PROPOSAL_INTAKE_BLOCKED")
        finally: td.cleanup()
    def test_blocks_forbidden_shell_key(self):
        td,root=self.make_root()
        try:
            p=root/"reports/d80_ai_provider_mock_proposal.json"; d=json.loads(p.read_text()); d["proposal"]["raw_shell_command"]="rm -rf ."; p.write_text(json.dumps(d))
            r=create_ai_proposal_intake(root=root)
            self.assertFalse(r["ok"]); self.assertEqual(r["decision"],"AI_PROPOSAL_INTAKE_BLOCKED")
        finally: td.cleanup()
if __name__=="__main__": unittest.main()
