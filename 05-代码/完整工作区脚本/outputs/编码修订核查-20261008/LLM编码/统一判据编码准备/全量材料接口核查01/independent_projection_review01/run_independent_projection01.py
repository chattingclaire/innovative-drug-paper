"""New invented interface structures only; never loads corpus/labels."""
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROJECTOR=BASE / "project_source_only_inputs.py"
VALIDATOR=BASE.parent / "runtime/validate_binary_output.py"
MANIFEST="9"*64

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
p=load("independent_source_projector",PROJECTOR)
v=load("independent_literal_validator",VALIDATOR)

def base(contexts=None,text="全新构造当前句。"):
    row={"id":"INVENTED-PROJECTION-ONLY","text":text,"pages":[4],"source_title":"DROP_FILENAME","contexts":contexts or {}}
    rule={"id":row["id"],"input":{"unit_text":text,"source":"invented-generic.txt","source_sha256":"1"*64,
                                    "unit_source":"invented-current.txt","unit_source_sha256":"2"*64,
                                    "source_image":"invented-image-A.bin","source_image_sha256":"3"*64}}
    return row,rule

def external_bind(row,rule):
    first=p.project_record(row,rule)
    registry={leaf["raw_pointer"]:{"text_sha256":leaf["text_sha256"],
             "source_sha256":leaf["source_binding"].get("table_source_structured_sha256") or leaf["source_binding"].get("source_sha256"),
             "manifest_sha256":MANIFEST,"proof_kind":"source_literal_span","locator":{"invented_occurrence":leaf["raw_pointer"]}}
              for leaf in first["provenance_sidecar"]["policy_leaves"]}
    return p.project_record(row,rule,literal_bindings=registry,manifest_sha256=MANIFEST)

def main():
    expected_projector="168617fe56eb050b4c5607f856715515a282e5c2a4643faf0ae7d5af26ab5e42"
    assert sha(PROJECTOR)==expected_projector
    results=[]
    row,rule=base({"verified_table_context_v4":[{"table_title":"构造原表名","column_names":["构造甲列","构造乙列"],"raw_row_cells":["重复构造格","重复构造格"],"row_index_zero_based":5,"labels":{"F":1},"verification":{"opinion":"DROP_OPINION"}}]})
    before=copy.deepcopy((row,rule));r=p.project_record(row,rule);visible=r["model_visible_candidate"]
    cells=[n for n in visible["contexts"] if n["kind"]=="table_row_cell"]
    payload=json.dumps(visible,ensure_ascii=False)
    passed=(visible["text"]==row["text"] and len(cells)==2 and len({c["context_id"] for c in cells})==2
            and [c["structure"]["column_index"] for c in cells]==[0,1] and "DROP_" not in payload
            and all(c["text"] in list(v.iter_context_text(visible["contexts"])) for c in cells)
            and (row,rule)==before and not r["provenance_sidecar"]["binding_complete_for_review"])
    results.append({"name":"exact_current_and_repeated_occurrences","passed":passed,"actual":r})

    row,rule=base({"paragraph_context":[{"paragraph_id":"invented-p","text":"全新构造来源乙段。","source_path":"invented-other.txt"}]})
    r=external_bind(row,rule);leaf=next(l for l in r["provenance_sidecar"]["policy_leaves"] if l["raw_pointer"]!="/text")
    passed=(not r["provenance_sidecar"]["binding_complete_for_review"] or leaf["source_binding"].get("source_path")=="invented-other.txt")
    results.append({"name":"partial_explicit_context_source_pair","passed":passed,"actual":r})

    row,rule=base({"paragraph_context":[{"paragraph_id":"invented-p","text":"全新构造图像相关段。","source_image":"invented-image-B.bin"}]})
    r=external_bind(row,rule);leaf=next(l for l in r["provenance_sidecar"]["policy_leaves"] if l["raw_pointer"]!="/text")
    mixed=(leaf["source_binding"].get("source_image")=="invented-image-B.bin" and leaf["source_binding"].get("source_image_sha256")=="3"*64)
    results.append({"name":"partial_source_image_pair","passed":not mixed,"actual":r})

    row,rule=base({"verified_table_context_v4":[{"table_title":"构造表名","column_names":["列"],"raw_row_cells":["格"],"row_index_zero_based":{"opinion":"DROP_ROW_INDEX_OPINION","labels":{"F":1}}}]})
    r=p.project_record(row,rule);payload=json.dumps(r["model_visible_candidate"],ensure_ascii=False)
    results.append({"name":"table_row_index_opinion_shape","passed":"DROP_ROW_INDEX_OPINION" not in payload,"actual":r})

    row,rule=base({"verified_scope_qualifications_v28":[{"paragraph_id":"invented-definition","definition":"本构造定义为需要保留的真实字段文本。"}]})
    r=external_bind(row,rule);texts=list(v.iter_context_text(r["model_visible_candidate"]["contexts"]))
    passed="本构造定义为需要保留的真实字段文本。" in texts or not r["provenance_sidecar"]["binding_complete_for_review"]
    results.append({"name":"known_definition_leaf","passed":passed,"actual":r})

    row,rule=base(text="");r=p.project_record(row,rule)
    results.append({"name":"empty_current_text","passed":not r["provenance_sidecar"]["binding_complete_for_review"],"actual":r})
    author_checks=p.self_test(VALIDATOR)
    assert sha(PROJECTOR)==expected_projector
    return {"at_utc":datetime.now(timezone.utc).isoformat(),"projector_sha256":sha(PROJECTOR),"validator_sha256":sha(VALIDATOR),
            "design_sha256":sha(HERE/"design_independent_projection01.json"),"executed_new_check_n":len(results),
            "passed_new_check_n":sum(r["passed"] for r in results),"results":results,"author13_reproduced":author_checks,
            "source_binding_test_note":"Matching external bindings are wholly invented registry fixtures, not actual source authentication. They expose readiness behavior only.",
            "real_corpus_read_or_exported":False,"protected_or_reference_material_read":False,"model_or_rule_called":False,"author_code_changed":False}

if __name__=="__main__":
    target=HERE/"actual_independent_projection01.json";assert not target.exists()
    result=main();target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"new_checks":result["executed_new_check_n"],"new_passed":result["passed_new_check_n"],
                      "failures":[r["name"] for r in result["results"] if not r["passed"]],
                      "author_checks_reproduced":result["author13_reproduced"]["check_n"],"output_sha256":sha(target)},ensure_ascii=False))
