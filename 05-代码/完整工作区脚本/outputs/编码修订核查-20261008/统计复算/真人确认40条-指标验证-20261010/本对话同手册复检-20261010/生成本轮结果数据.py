from pathlib import Path
import json, hashlib, argparse
from 核查与复算 import metric

ROOT = Path(__file__).resolve().parent
DIMS = {"S":"安全性","E":"有效性","Ec":"经济性","I":"创新性","F":"公平性"}

def read(p):
    return json.loads(p.read_text())

def lines(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+"\n")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--llm-directory",type=Path,required=True)
    parser.add_argument("--output-directory",type=Path,required=True)
    a=parser.parse_args()
    out=a.output_directory.resolve()
    out.mkdir(exist_ok=True)
    qa=read(a.llm_directory/"LLM来源与引文核查.json")
    assert qa["coded_N"]==40 and not qa["pending_files"] and not qa["material_issues"]
    assert qa["exact_quote_and_schema_checks"]=="passed_for_received_rows"
    used_files=[Path(b["path"]) for b in qa["bindings"]]
    assert all(sha(p)==qa["bindings"][i]["sha256"] for i,p in enumerate(used_files))
    before={r["material_id"]:r for r in lines(ROOT/"当前真人参照40条.jsonl")}
    refs={r["material_id"]:r for r in lines(ROOT/"校准17裁定后参照40条.jsonl")}
    units={}
    for i in range(1,5):
        units.update({u["material_id"]:u for u in read(ROOT/f"无答案输入/批次{i:02d}.json")["units"]})
    rule_path=ROOT/"规则修正/40条规则实际输出-dc26-relation-candidate-04.jsonl"
    rules={r["material_id"]:r["prediction"] for r in lines(rule_path)}
    llms={}
    for p in used_files:
        llms.update({r["material_id"]:r for r in read(p)["rows"]})
    assert len(refs)==len(rules)==len(llms)==40
    assert set(before)==set(refs)==set(units)==set(rules)==set(llms)
    assert all(llms[k]["material_status"]=="coded" for k in llms)
    changes=[(k,d,before[k]["labels"][d],refs[k]["labels"][d]) for k in refs for d in DIMS if before[k]["labels"][d]!=refs[k]["labels"][d]]
    assert changes==[("校准17","F",0,1)], changes
    rule_quote_checks=0
    for k,p in rules.items():
        u=units[k]
        assert p["manual_sha256"]==refs[k]["manual_sha256"]
        assert p["unit_text_sha256"]==hashlib.sha256(u["current_text"].encode()).hexdigest()
        assert p["context_sha256"]==[hashlib.sha256(c.encode()).hexdigest() for c in u["contexts"]]
        for e in p["evidence"]:
            assert e["current_statement"]["text"]==u["current_text"]
            for anchor in e["current_relation_anchors"]:
                assert u["current_text"][anchor["start"]:anchor["end"]]==anchor["text"]
                rule_quote_checks+=1
            for anchor in e["consumed_context_anchors"]:
                c=u["contexts"][anchor["context_index"]]
                assert c[anchor["start"]:anchor["end"]]==anchor["text"]
                rule_quote_checks+=1
        assert all(not p["labels"][d] or any(e["dimension"]==d for e in p["evidence"]) for d in DIMS)
    metrics=[]
    for dep in ["总体","药监","医保","卫健"]:
        keys=[k for k in refs if dep=="总体" or refs[k]["department"]==dep]
        for d,name in DIMS.items():
            for method,pred in [("自动规则编码",rules),("LLM编码",llms)]:
                m=metric([(pred[k]["labels"][d],refs[k]["labels"][d]) for k in keys])
                m.update(method=method,dimension=d,dimension_name=name,department=dep)
                m["project_target_status"]=("不可估计" if any(m[x] is None for x in ["kappa","precision","recall","F1"]) else "达到0.80" if all(m[x]>=.8 for x in ["kappa","precision","recall","F1"]) else "未达到0.80")
                metrics.append(m)
    diagnostic=[]
    for d,name in DIMS.items():
        row={"dimension":d,"dimension_name":name}
        for method,pred in [("规则",rules),("LLM",llms)]:
            # 两份原A/B复核标签相同；不得将17裁定写成两位编码员新的提交。
            row[method+"—原A"]=metric([(pred[k]["labels"][d],before[k]["labels"][d]) for k in refs])["kappa"]
            row[method+"—原B"]=row[method+"—原A"]
        row["原A—原B"]=metric([(before[k]["labels"][d],before[k]["labels"][d]) for k in refs])["kappa"]
        row["规则—LLM"]=metric([(rules[k]["labels"][d],llms[k]["labels"][d]) for k in refs])["kappa"]
        diagnostic.append(row)
    raw=[]; disagreements=[]
    for k,r in refs.items():
        u=units[k]
        for d,name in DIMS.items():
            rp=rules[k]
            lr=llms[k]
            adjud=r.get("adjudication") if d=="F" and k=="校准17" else None
            rule_reason="\n".join(e.get("reason","") for e in rp["evidence"] if e["dimension"]==d) or "未命中本维显式关系规则；不从对象身份或一般背景继承。"
            row={
                "material_id":k,"global_id":r["global_id"],"department":r["department"],"dimension":d,"dimension_name":name,
                "original_A":before[k]["labels"][d],"original_B":before[k]["labels"][d],"reference":r["labels"][d],
                "rule":rp["labels"][d],"LLM":lr["labels"][d],"current_text":u["current_text"],
                "contexts":"\n\n".join(f"[{i}] {c}" for i,c in enumerate(u["contexts"],1)),
                "A_review_reason":r["actual_review_notes"]["A"][d],"B_review_reason":r["actual_review_notes"]["B"][d],
                "adjudication_note":("用户核对完整同段语境后确认1；原A/B的0保留。不是新的独立A/B提交。" if adjud else ""),
                "rule_reason":rule_reason,"LLM_reason":lr["dimension_reasons"][d],
                "rule_same_reference":int(rp["labels"][d]==r["labels"][d]),"LLM_same_reference":int(lr["labels"][d]==r["labels"][d])
            }
            raw.append(row)
            if not row["rule_same_reference"] or not row["LLM_same_reference"]:
                disagreements.append(row)
    bindings=[]
    for p in [ROOT/"无答案输入/共用编码手册.md",ROOT/"当前真人参照40条.jsonl",ROOT/"校准17裁定后参照40条.jsonl",rule_path,a.llm_directory/"执行契约.json",a.llm_directory/"固定执行提示.txt",a.llm_directory/"引文序号修正记录.json"]+used_files+[a.llm_directory/f"原始输出/批次{i:02d}-首次输出.json" for i in range(1,5)]+[ROOT/f"规则修正/relation_coder_v{i:02d}.py" for i in [2,3,4]]:
        bindings.append({"path":str(p.resolve()),"sha256":sha(p)})
    data={"scope":"40条同手册开发核查","department_n":{"医保":19,"药监":18,"卫健":3},"reference_note":"真人接续复核加校准17用户裁定；不属于独立盲评初判","target":.8,"model":"gpt-5.6-sol",
          "metrics":metrics,"original_review_diagnostic_kappa":diagnostic,"raw":raw,"disagreements":disagreements,
          "reference_change":changes,"rule_exact_anchor_checks":rule_quote_checks,"bindings":bindings,
          "independent_population_validation":False,"other_chat77_used":False}
    save(out/"结果数据.json",data)
    save(out/"逐项分歧.json",disagreements)
    print(json.dumps({"overall":[m for m in metrics if m["department"]=="总体"],"disagreement_n":len(disagreements),"rule_exact_anchor_checks":rule_quote_checks},ensure_ascii=False))
if __name__=="__main__":
    main()
