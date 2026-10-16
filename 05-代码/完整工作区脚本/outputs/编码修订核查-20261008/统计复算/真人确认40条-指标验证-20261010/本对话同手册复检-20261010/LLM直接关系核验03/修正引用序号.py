from pathlib import Path
import json,hashlib,copy
ROOT=Path(__file__).resolve().parent.parent
stage=ROOT/"LLM直接关系核验03"
output=stage/"使用输出"
output.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
units={u["material_id"]:u for i in range(1,5) for u in json.loads((ROOT/f"无答案输入/批次{i:02d}.json").read_text())["units"]}
changes=[];bindings=[]
for i in range(1,5):
    src=stage/f"原始输出/批次{i:02d}-首次输出.json"
    dest=output/src.name
    assert not dest.exists(),str(dest)
    original=json.loads(src.read_text())
    obj=copy.deepcopy(original)
    for row in obj["rows"]:
        u=units[row["material_id"]]
        for e in row["evidence"]:
            if e["source"]!="context":continue
            provided=u["contexts"][e["context_index"]-1]
            if e["quote"] not in provided:
                matches=[k+1 for k,c in enumerate(u["contexts"]) if e["quote"] in c]
                assert len(matches)==1,(row["material_id"],matches)
                changes.append({"material_id":row["material_id"],"dimension":e["dimension"],"old_context_index":e["context_index"],"new_context_index":matches[0],"quote_unchanged":e["quote"],"labels_changed":False,"reason":"同一给定材料中的逐字引文唯一定位；只修正引用序号"})
                e["context_index"]=matches[0]
    assert [r["labels"] for r in original["rows"]]==[r["labels"] for r in obj["rows"]]
    assert [r["dimension_reasons"] for r in original["rows"]]==[r["dimension_reasons"] for r in obj["rows"]]
    if obj==original:dest.write_bytes(src.read_bytes())
    else:dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    bindings.append({"source":str(src),"source_sha256":sha(src),"used":str(dest),"used_sha256":sha(dest)})
report={"operation":"逐字引文位置核查后序号修正","new_model_execution":False,"labels_or_reasons_changed":False,"changes":changes,"bindings":bindings,"originals_preserved":True}
(stage/"引文序号修正记录.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"n":len(changes),"changes":changes},ensure_ascii=False))
