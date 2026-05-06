import json,tempfile,unittest
from pathlib import Path
from runtime_experimental.narrow_adapter_dry_run_diff import build_narrow_adapter_dry_run_diff

class TestD78NarrowAdapterDryRunDiff(unittest.TestCase):
    def make_root(self):
        td=tempfile.TemporaryDirectory(); root=Path(td.name)
        (root/"reports").mkdir(); (root/"runtime_experimental/differentiated_modules").mkdir(parents=True); (root/"app/orchestration").mkdir(parents=True)
        src="app/orchestration/task_dispatcher.py"; child="runtime_experimental/differentiated_modules/01_route_policy_child.py"; adapter="D77_NARROW_ADAPTER_ROUTE_POLICY_CHILD"
        (root/src).write_text("# source\n",encoding="utf-8")
        (root/child).write_text("def run_sandbox_probe(event=None): return {'ok': True}\n",encoding="utf-8")
        (root/"reports/d77_narrow_adapter_contract.json").write_text(json.dumps({"ok":True,"decision":"NARROW_ADAPTER_CONTRACT_READY","contract_id":"d77-test","guardrails":{"actual_apply_executed":False,"contract_only":True},"narrow_adapter_contract":{"contract_id":"d77-test","source_node":src,"child_module_path":child,"adapter_name":adapter,"route_policy":{"route_insert_allowed_now":False,"contract_only":True},"required_before_integration":["D66_RECHECK","D76_CHILD_PROBE_PASSED","ROLLBACK_MANIFEST"],"forbidden_actions":["direct_core_edit","protected_core_mutation","auto_apply_runtime_mutation"]}}),encoding="utf-8")
        return td,root,src,child
    def test_creates_diff_without_mutation(self):
        td,root,src,child=self.make_root()
        try:
            before=(root/src).read_text()
            r=build_narrow_adapter_dry_run_diff(root=root)
            self.assertTrue(r["ok"]); self.assertEqual(r["decision"],"NARROW_ADAPTER_DRY_RUN_DIFF_READY")
            self.assertEqual((root/src).read_text(),before)
            self.assertFalse(r["guardrails"]["route_inserted"]); self.assertFalse(r["guardrails"]["actual_apply_executed"])
            self.assertTrue((root/"reports/d78_narrow_adapter_dry_run.diff").exists())
        finally: td.cleanup()
    def test_blocks_missing_d77(self):
        td,root,_,_=self.make_root()
        try:
            (root/"reports/d77_narrow_adapter_contract.json").unlink()
            r=build_narrow_adapter_dry_run_diff(root=root)
            self.assertFalse(r["ok"]); self.assertEqual(r["decision"],"NARROW_ADAPTER_DRY_RUN_DIFF_BLOCKED")
        finally: td.cleanup()
    def test_blocks_route_insert_allowed(self):
        td,root,_,_=self.make_root()
        try:
            p=root/"reports/d77_narrow_adapter_contract.json"; d=json.loads(p.read_text()); d["narrow_adapter_contract"]["route_policy"]["route_insert_allowed_now"]=True; p.write_text(json.dumps(d))
            r=build_narrow_adapter_dry_run_diff(root=root)
            self.assertFalse(r["ok"])
        finally: td.cleanup()
if __name__=="__main__": unittest.main()
