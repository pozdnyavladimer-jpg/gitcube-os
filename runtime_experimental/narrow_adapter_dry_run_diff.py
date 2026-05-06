from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Dict,List

D77="reports/d77_narrow_adapter_contract.json"
OUT="reports/d78_narrow_adapter_dry_run_diff.json"
DIFF="reports/d78_narrow_adapter_dry_run.diff"

def now(): return datetime.now(timezone.utc).isoformat()
def readj(p,default=None):
    p=Path(p)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default
def writej(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def writet(p,t):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t,encoding="utf-8")
def safe(s):
    s=str(s or "").strip().replace("\\","/").lstrip("/")
    return "/".join(x for x in s.split("/") if x and x not in (".",".."))
def sym(s):
    s=safe(s).replace("/","_").replace(".","_").replace("-","_")
    out="".join(c.lower() if c.isalnum() or c=="_" else "_" for c in s)
    while "__" in out: out=out.replace("__","_")
    return out.strip("_") or "adapter"
def sha(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def shaj(d): return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def build_diff(src, child, adapter, cid):
    imp=child[:-3].replace("/",".") if child.endswith(".py") else child.replace("/",".")
    h=sym(adapter).upper()
    return f"""diff --git a/{src} b/{src}
--- a/{src}
+++ b/{src}
@@ DRY-RUN ONLY: narrow adapter route proposal, not applied @@
+# D78 DRY-RUN ONLY — DO NOT APPLY AUTOMATICALLY
+# contract_id: {cid}
+# adapter_name: {adapter}
+# child_module: {child}
+#
+# Proposed guarded import:
+#     from {imp} import run_sandbox_probe as {h}_SANDBOX_PROBE
+#
+# Proposed guarded route shape:
+#     if event.get("route") == "{adapter}":
+#         return {h}_SANDBOX_PROBE(event)
+#
+# Required before any real route insertion:
+#     - D66_RECHECK
+#     - D73_PACKAGE_READY
+#     - D76_CHILD_PROBE_PASSED
+#     - UNIT_TESTS
+#     - REGRESSION_TESTS
+#     - ROLLBACK_MANIFEST
+#     - HUMAN_OR_HIGHER_POLICY_APPROVAL
"""

def build_narrow_adapter_dry_run_diff(root=".", d77_contract_path=D77, output_path=OUT, diff_output_path=DIFF):
    root=Path(root).resolve()
    d77=readj(root/d77_contract_path,{}) or {}
    errors=[]; warnings=[]
    if not d77:
        errors.append("D77 narrow adapter contract report missing or unreadable")
        contract={}
    else:
        if d77.get("ok") is not True: errors.append("D77 ok flag is not true")
        if d77.get("decision")!="NARROW_ADAPTER_CONTRACT_READY": errors.append("D77 decision is not ready")
        g=d77.get("guardrails") if isinstance(d77.get("guardrails"),dict) else {}
        if g.get("actual_apply_executed") is not False: errors.append("D77 actual_apply_executed is not false")
        if g.get("contract_only") is not True: errors.append("D77 contract_only is not true")
        contract=d77.get("narrow_adapter_contract") if isinstance(d77.get("narrow_adapter_contract"),dict) else {}
        if not contract: errors.append("D77 narrow_adapter_contract missing")

    rp=contract.get("route_policy") if isinstance(contract.get("route_policy"),dict) else {}
    if rp.get("route_insert_allowed_now") is not False: errors.append("D77 route_insert_allowed_now is not false")
    if rp.get("contract_only") is not True: errors.append("D77 route_policy contract_only is not true")
    for gate in ("D66_RECHECK","D76_CHILD_PROBE_PASSED","ROLLBACK_MANIFEST"):
        if gate not in (contract.get("required_before_integration") or []): errors.append(f"D77 missing required gate: {gate}")
    for act in ("direct_core_edit","protected_core_mutation","auto_apply_runtime_mutation"):
        if act not in (contract.get("forbidden_actions") or []): errors.append(f"D77 missing forbidden action: {act}")

    src=safe(contract.get("source_node",""))
    child=safe(contract.get("child_module_path",""))
    adapter=str(contract.get("adapter_name",""))
    cid=str(contract.get("contract_id") or d77.get("contract_id") or "")
    if not src: errors.append("D77 source_node missing")
    if not child: errors.append("D77 child_module_path missing")
    elif not child.startswith("runtime_experimental/differentiated_modules/"): errors.append("child module outside sandbox")
    if child and not (root/child).exists(): errors.append(f"child module does not exist on disk: {child}")
    if not adapter: errors.append("D77 adapter_name missing")
    if not cid: errors.append("D77 contract_id missing")
    if src and not (root/src).exists(): warnings.append(f"source_node not on disk; diff remains conceptual: {src}")

    diff=""
    if not errors:
        diff=build_diff(src,child,adapter,cid)
        writet(root/diff_output_path,diff)
    dh=sha(diff) if diff else ""
    pid="d78-"+shaj({"src":src,"child":child,"adapter":adapter,"cid":cid,"dh":dh})[:16]
    ok=not errors
    decision="NARROW_ADAPTER_DRY_RUN_DIFF_READY" if ok else "NARROW_ADAPTER_DRY_RUN_DIFF_BLOCKED"
    result="D78_NARROW_ADAPTER_DRY_RUN_DIFF_CREATED" if ok else "D78_NARROW_ADAPTER_DRY_RUN_DIFF_BLOCKED"
    report={
      "state":"D78_NARROW_ADAPTER_DRY_RUN_DIFF","result":result,"route":"FIELD_INTENT_NARROW_ADAPTER_DRY_RUN_DIFF",
      "ok":ok,"decision":decision,"created_at":now(),"package_id":pid,
      "dry_run_diff_package":{
        "package_id":pid,"mode":"DRY_RUN_DIFF_ONLY_NO_ROUTE_INSERT","source_node":src,"child_module_path":child,
        "adapter_name":adapter,"contract_id":cid,"diff_output_path":str(root/diff_output_path),"diff_sha256":dh,
        "would_touch_files":[src] if src else [],"would_touch_protected_core":bool(src),"actual_files_touched":[],
        "route_insert_allowed_now":False,"apply_allowed_now":False,
        "required_before_apply":["D66_RECHECK","D73_PACKAGE_READY","D76_CHILD_PROBE_PASSED","D77_CONTRACT_READY","UNIT_TESTS","REGRESSION_TESTS","ROLLBACK_MANIFEST","HUMAN_OR_HIGHER_POLICY_APPROVAL"],
        "forbidden_actions":["direct_core_edit","protected_core_mutation","overwrite_canonical_memory","external_ai_call","auto_apply_runtime_mutation"],
        "diff_preview":diff},
      "input_reports":{"d77_contract_path":str(root/d77_contract_path)},
      "guardrails":{"runtime_code_mutated":False,"protected_core_mutated":False,"canonical_memory_mutated":False,"external_ai_called":False,"actual_apply_executed":False,"route_inserted":False,"dry_run_only":True},
      "validation":{"ok":ok,"errors":errors,"warnings":warnings},
      "summary":{"decision":decision,"package_id":pid,"source_node":src,"child_module_path":child,"adapter_name":adapter,"diff_sha256":dh,"errors_count":len(errors),"warnings_count":len(warnings)},
      "success_condition":{"dry_run_diff_created":ok,"actual_apply_executed":False,"route_inserted":False,"protected_core_untouched":True,"next_step":"D79 can verify the dry-run diff against D66/D64 policies before guarded route insertion."}}
    writej(root/output_path,report)
    return report

if __name__=="__main__":
    print(json.dumps(build_narrow_adapter_dry_run_diff(),ensure_ascii=False,indent=2))
