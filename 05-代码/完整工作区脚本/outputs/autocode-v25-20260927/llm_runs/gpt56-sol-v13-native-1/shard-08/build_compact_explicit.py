"""Expand explicit compact judgments; this performs no text classification."""
import json, sys
from pathlib import Path
DIMS=["S","E","Ec","I","F"]
NEG={"S":"本单元未实质涉及药物或用药安全。","E":"本单元未实质涉及药物治疗效果或临床获益。","Ec":"本单元未实质涉及药品价格、治疗费用或支付资源。","I":"本单元未实质涉及药物创新属性或创新研发支持。","F":"本单元未实质涉及药品保障获取、患者可负担或临床管理难度。"}
def main():
 d=json.loads(Path(sys.argv[1]).read_text()); out=[]
 for x in d:
  assert len(x["l"])==5 and all(v in "01?" for v in x["l"])
  labels={k:("待定" if v=="?" else int(v)) for k,v in zip(DIMS,x["l"])}
  reasons={}; ev=[]
  for k in DIMS:
   if labels[k]==0: reasons[k]=x.get("zero",{}).get(k,NEG[k])
   elif labels[k]==1:
    p=x["pos"][k]; reasons[k]=p["r"]
    for q in p["q"]:
     if isinstance(q,str): ev.append({"dimension":k,"source":"unit","quote":q})
     else: ev.append({"dimension":k,"source":q[0],"quote":q[1]})
   else: reasons[k]=x["pending_reason"]
  out.append({"id":x["id"],"labels":labels,"dimension_reasons":reasons,"evidence":ev,
   "material_issue":x.get("material_issue",""),"fairness_subtypes":x.get("f",[]),
   "innovation_subtypes":x.get("i",[]),"safety_quality_basis":x.get("sq","undetermined" if labels["S"]=="待定" else "no_quality_basis")})
 Path(sys.argv[2]).write_text(json.dumps({"protocol_version":"CAL-5D-20260926-v1.3","rows":out},ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__": main()
