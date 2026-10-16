"""Independent constructed checks; never opens corpus input or label files."""
import copy
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE / "runtime"))
import policy_coding_v27 as coder
from selftest_common_if_extensions03 import prose

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    design = HERE / "design_independent06.json"
    cases = json.loads(design.read_text())["cases"]
    files = sorted((BASE / "runtime").glob("*.py")) + [BASE / "run_bounded_common_candidate.py", BASE / "run_frozen_common_full.py"]
    hashes_before = {str(p): sha(p) for p in files}
    delivery = json.loads((BASE / "implementation_delivery06.json").read_text())
    expected_hashes = {str(BASE / "runtime" / k): v for k, v in delivery["runtime_sha256"].items()}
    expected_hashes.update({str(BASE / k): v for k,v in delivery["runner_sha256"].items()})
    assert hashes_before == expected_hashes
    old = json.loads((BASE / "candidate05_preserved_base06.json").read_text())
    old_unchanged = {p: sha(p) == h for p,h in old.items()}
    assert all(old_unchanged.values())
    outputs=[]
    with tempfile.TemporaryDirectory(prefix="independent06-invented-") as td:
        for case in cases:
            record=prose(Path(td) / case["name"], case["text"], prefix=case["prefix"])
            if case.get("mutation") == "source_without_prefix_rebound_sha":
                source=Path(record["source"])
                source.write_text(case["text"]+"此临时来源并没有给定前句。", encoding="utf-8")
                record["source_sha256"]=record["unit_source_sha256"]=sha(source)
            before=copy.deepcopy(record)
            prediction,error=None,None
            try:
                prediction=coder.code_unit(record)
            except Exception as exc:
                error={"type":type(exc).__name__,"message":str(exc)}
            passed=bool(error and error["type"]=="ValueError") if case.get("expected_error") else error is None and prediction["labels"][case["dimension"]]==case["expected"]
            offset_n=anchor_n=context_n=0
            if prediction is not None:
                assert prediction["common_rules_sha256"] == delivery["manual"]["sha256"]
                for e in prediction["evidence"]:
                    assert case["text"][e["start"]:e["end"]] == e["text"]
                    offset_n+=1
                    for a in e.get("current_relation_anchors",[]):
                        assert case["text"][a["start"]:a["end"]] == a["text"]
                        anchor_n+=1
                    dep=e.get("context_dependency") or {}
                    if dep.get("kind") == "COMMON06_authenticated_current_relation_scope":
                        para=next(p for p in record["paragraph_context"] if p["paragraph_id"]==dep["paragraph_id"])
                        assert para["text"][dep["antecedent_start_in_paragraph"]:dep["antecedent_end_in_paragraph"]] == dep["antecedent_text"]
                        assert dep["source_sha256"] == sha(record["source"])
                        assert dep["candidate_sha256"] == sha(record["candidate_file"])
                        assert dep["source_authentication"].get("literal_reproduced_in_current_runtime") is True
                        context_n+=1
            assert record==before
            outputs.append({"case":case,"passed":passed,"labels":prediction["labels"] if prediction else None,
                            "error":error,"evidence":prediction["evidence"] if prediction else None,
                            "evidence_offset_n":offset_n,"relation_anchor_n":anchor_n,"context_binding_n":context_n,"input_unchanged":True})
    assert hashes_before == {str(p):sha(p) for p in files}
    return {"at_utc":datetime.now(timezone.utc).isoformat(),"design_sha256":sha(design),"code_matches_delivery":True,
            "code_unchanged_during_check":True,"candidate05_files_hash_checked_n":len(old_unchanged),"candidate05_unchanged":True,
            "executed_n":len(outputs),"pass_n":sum(o["passed"] for o in outputs),"outputs":outputs,
            "no_real_or_protected_material_read":True,"no_reference_labels_read":True,"no_llm_calls":True}

if __name__=="__main__":
    target=HERE / "actual_independent06.json"
    assert not target.exists()
    result=main()
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"executed_n":result["executed_n"],"pass_n":result["pass_n"],
                      "failures":[{"name":o["case"]["name"],"expected":o["case"].get("expected"),"actual":o["labels"][o["case"]["dimension"]] if o["labels"] else None,"error":o["error"]} for o in result["outputs"] if not o["passed"]],
                      "output":str(target),"sha256":sha(target)},ensure_ascii=False))
