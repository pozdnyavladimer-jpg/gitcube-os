from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

D80_BOUNDARY="reports/d80_ai_provider_boundary.json"
D80_PROPOSAL="reports/d80_ai_provider_mock_proposal.json"
OUT="reports/d81_ai_proposal_intake.json"
CONTRACT_OUT="reports/d81_ai_proposal_intake_contract.json"

FORBIDDEN_KEYS={
 "raw_shell_command","shell_command","command","exec","subprocess","auto_apply","apply_now",
 "direct_core_edit","protected_core_mutation","api_secret","api_key","token",
 "canonical_memory_overwrite","overwrite_canonical_memory","git_commit","git_push",
}
REQUIRED_FIELDS=["proposal_id","proposal_type","target_scope","candidate_files","guardrails","validation_plan"]

def now(): return datetime.now(timezone.utc).isoformat()
def readj(p, default=None):
    p=Path(p)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default
def writej(p,d):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def shaj(d): return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def scan_forbidden_keys(obj, path="$"):
    hits=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            kn=str(k).strip().lower()
            if kn!="forbidden_fields" and kn in FORBIDDEN_KEYS:
                hits.append(f"{path}.{k}")
            hits += scan_forbidden_keys(v, f"{path}.{k}")
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            hits += scan_forbidden_keys(v, f"{path}[{i}]")
    return hits

def validate_boundary(rep, errors):
    if not rep:
        errors.append("D80 boundary report missing or unreadable"); return {}
    if rep.get("ok") is not True: errors.append("D80 ok flag is not true")
    if rep.get("decision")!="AI_PROVIDER_BOUNDARY_READY": errors.append("D80 decision is not AI_PROVIDER_BOUNDARY_READY")
    b=rep.get("boundary") if isinstance(rep.get("boundary"),dict) else {}
    if not b:
        errors.append("D80 boundary object missing"); return {}
    if b.get("mode")!="PROPOSE_ONLY": errors.append("D80 mode is not PROPOSE_ONLY")
    if b.get("provider")!="mock_local": errors.append("D80 provider is not mock_local")
    for key in ("external_ai_call_allowed","network_access_allowed","actual_apply_allowed","route_insert_allowed","raw_code_execution_allowed","shell_command_generation_allowed","git_commit_allowed"):
        if b.get(key) is not False: errors.append(f"D80 boundary {key} is not false")
    g=rep.get("guardrails") if isinstance(rep.get("guardrails"),dict) else {}
    for key in ("external_ai_called","network_accessed","runtime_code_mutated","protected_core_mutated","canonical_memory_mutated","actual_apply_executed","route_inserted"):
        if g.get(key) is not False: errors.append(f"D80 guardrail {key} is not false")
    if g.get("proposal_only") is not True: errors.append("D80 proposal_only is not true")
    return b

def validate_proposal(rep, errors, warnings):
    if not rep:
        errors.append("D80 mock proposal missing or unreadable"); return {}
    if rep.get("ok") is not True: errors.append("D80 mock proposal ok is not true")
    if rep.get("mode")!="PROPOSE_ONLY": errors.append("D80 mock proposal mode is not PROPOSE_ONLY")
    if rep.get("provider")!="mock_local": errors.append("D80 mock proposal provider is not mock_local")
    hits=scan_forbidden_keys(rep)
    if hits: errors.append("forbidden executable/control keys found: "+", ".join(hits))
    prop=rep.get("proposal") if isinstance(rep.get("proposal"),dict) else {}
    if not prop:
        errors.append("proposal body missing"); return {}
    if prop.get("type")!="NEXT_MODULE_PROPOSAL": warnings.append("proposal type is not NEXT_MODULE_PROPOSAL")
    contract=prop.get("allowed_output_contract") if isinstance(prop.get("allowed_output_contract"),dict) else {}
    if not contract:
        errors.append("allowed_output_contract missing")
    else:
        if contract.get("format")!="json": errors.append("allowed_output_contract format is not json")
        req=contract.get("required_fields")
        if not isinstance(req,list): errors.append("required_fields is not a list")
        else:
            for f in REQUIRED_FIELDS:
                if f not in req: errors.append(f"missing required field declaration: {f}")
        forb=contract.get("forbidden_fields")
        if not isinstance(forb,list): errors.append("forbidden_fields is not a list")
        else:
            for f in ("raw_shell_command","auto_apply","direct_core_edit","api_secret"):
                if f not in forb: errors.append(f"missing forbidden field declaration: {f}")
    g=rep.get("guardrails") if isinstance(rep.get("guardrails"),dict) else {}
    for key in ("external_ai_called","runtime_code_mutated","protected_core_mutated","canonical_memory_mutated","actual_apply_executed","route_inserted"):
        if g.get(key) is not False: errors.append(f"D80 proposal guardrail {key} is not false")
    if g.get("proposal_only") is not True: errors.append("D80 proposal_only is not true")
    if g.get("mock_provider_only") is not True: errors.append("D80 mock_provider_only is not true")
    return prop

def make_contract(boundary_id, proposal_id, enabled):
    return {
      "state":"D81_AI_PROPOSAL_INTAKE_CONTRACT","enabled":enabled,"mode":"JSON_CONTRACT_ONLY",
      "source_boundary_id":boundary_id,"source_proposal_id":proposal_id,
      "accepted_input":{"format":"json","required_fields":REQUIRED_FIELDS,
        "candidate_files_prefixes_allowed":["runtime_experimental/","reports/","tests/"],
        "candidate_files_prefixes_blocked":["app/orchestration/","core/","runtime/","bridges/","memory/"]},
      "required_guardrails":{"external_ai_called":False,"network_accessed":False,"runtime_code_mutated":False,"protected_core_mutated":False,"canonical_memory_mutated":False,"actual_apply_executed":False,"route_inserted":False,"proposal_only":True,"json_only":True},
      "forbidden_fields":sorted(FORBIDDEN_KEYS),
      "forbidden_actions":["execute_shell_command","write_raw_code_to_protected_core","auto_apply_patch","git_commit_or_push","request_or_store_api_secret","overwrite_canonical_memory","route_insert_without_D66_D79_D80_D81_D82"],
      "next_gate":"D82_HUMAN_APPROVAL_SIGNED_INTENT"}

def create_ai_proposal_intake(root=".", d80_boundary_path=D80_BOUNDARY, d80_proposal_path=D80_PROPOSAL, output_path=OUT, contract_output_path=CONTRACT_OUT):
    root=Path(root).resolve()
    brep=readj(root/d80_boundary_path,{}) or {}
    prep=readj(root/d80_proposal_path,{}) or {}
    errors=[]; warnings=[]
    boundary=validate_boundary(brep,errors)
    proposal=validate_proposal(prep,errors,warnings)
    boundary_id=str(brep.get("boundary_id") or boundary.get("boundary_id") or "")
    proposal_id=str(prep.get("proposal_id") or "")
    if not boundary_id: errors.append("D80 boundary_id missing")
    if not proposal_id: errors.append("D80 proposal_id missing")
    intake_id="d81-"+shaj({"boundary_id":boundary_id,"proposal_id":proposal_id,"proposal_type":proposal.get("type") if proposal else ""})[:16]
    ok=not errors
    decision="AI_PROPOSAL_INTAKE_READY" if ok else "AI_PROPOSAL_INTAKE_BLOCKED"
    result="D81_AI_PROPOSAL_INTAKE_CREATED" if ok else "D81_AI_PROPOSAL_INTAKE_BLOCKED"
    contract=make_contract(boundary_id,proposal_id,ok)
    if ok: writej(root/contract_output_path,contract)
    declared_req=((proposal.get("allowed_output_contract") or {}).get("required_fields") or []) if proposal else []
    declared_forb=((proposal.get("allowed_output_contract") or {}).get("forbidden_fields") or []) if proposal else []
    report={"state":"D81_AI_PROPOSAL_INTAKE","result":result,"route":"FIELD_INTENT_AI_PROPOSAL_INTAKE","ok":ok,"decision":decision,"created_at":now(),"intake_id":intake_id,
      "intake_contract_path":str(root/contract_output_path) if ok else "","intake_contract":contract,
      "input_reports":{"d80_boundary_path":str(root/d80_boundary_path),"d80_proposal_path":str(root/d80_proposal_path)},
      "evidence":{"boundary_id":boundary_id,"proposal_id":proposal_id,"provider":prep.get("provider"),"mode":prep.get("mode"),"recommended_next_module":proposal.get("recommended_next_module") if proposal else None,"proposal_action":proposal.get("action") if proposal else None},
      "policy_checks":{"json_contract_only":ok,"boundary_propose_only":boundary.get("mode")=="PROPOSE_ONLY" if boundary else False,"proposal_propose_only":prep.get("mode")=="PROPOSE_ONLY","no_forbidden_keys":not scan_forbidden_keys(prep),"required_fields_declared":all(f in declared_req for f in REQUIRED_FIELDS),"forbidden_fields_declared":all(f in declared_forb for f in ("raw_shell_command","auto_apply","direct_core_edit","api_secret"))},
      "guardrails":{"external_ai_called":False,"network_accessed":False,"runtime_code_mutated":False,"protected_core_mutated":False,"canonical_memory_mutated":False,"actual_apply_executed":False,"route_inserted":False,"proposal_intake_only":True,"json_only":True},
      "validation":{"ok":ok,"errors":errors,"warnings":warnings},
      "summary":{"decision":decision,"intake_id":intake_id,"boundary_id":boundary_id,"proposal_id":proposal_id,"errors_count":len(errors),"warnings_count":len(warnings)},
      "success_condition":{"proposal_intake_created":ok,"actual_apply_executed":False,"route_inserted":False,"protected_core_untouched":True,"next_step":"D82 should create human/signed approval intent before any sandbox writer receives AI proposals."}}
    writej(root/output_path,report)
    return report
if __name__=="__main__":
    print(json.dumps(create_ai_proposal_intake(),ensure_ascii=False,indent=2))
