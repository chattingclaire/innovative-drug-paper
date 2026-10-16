#!/usr/bin/env python3
"""Expand explicitly selected judgments/reason phrases; no classification logic."""
import json, sys
from pathlib import Path

DIMS=["S","E","Ec","I","F"]
R={
 "S0":"未涉及药物或用药损害、安全证据或药品质量安全。",
 "E0":"未涉及药物治疗效果、临床获益或效果证据要求。",
 "C0":"未涉及药品价格、药费、治疗成本、支付或基金影响。",
 "I0":"未涉及药物创新属性、创新资格或创新研发支持。",
 "F0":"未涉及药品保障获取、患者可负担或特定药品临床管理难度。",
 "S1":"明确讨论药物或用药风险、安全性或相应证据要求。",
 "SQ":"明确讨论药品质量安全或质量风险。",
 "E1":"明确讨论药物疗效、临床获益或相应证据要求。",
 "C1":"明确讨论药品价格、费用、支付标准、预算或基金影响。",
 "IA":"明确讨论或要求提供药物创新属性信息。",
 "IR":"明确规定或讨论针对药物创新研发的支持措施。",
 "IQ":"明确以临床比较优势识别已登记的创新或改良资格。",
 "FA":"明确讨论药品配备、供应、目录保障或治疗获取。",
 "FP":"明确讨论患者支付能力或药费负担。",
 "FM":"明确讨论特定药品使用的管理复杂性、障碍或监测负担。",
 "FI":"明确要求提供公平性维度信息但未细分具体内容。"
}
here=Path(__file__).resolve().parent
b=sys.argv[1]
ip=here/f"input-{b}.json"; jp=here/f"judgments-{b}.json"; op=here/f"output-{b}.json"
if op.exists(): raise SystemExit(f"refusing to overwrite {op.name}")
inputs=json.loads(ip.read_text())["rows"]; js=json.loads(jp.read_text())
if list(js)!=[x["id"] for x in inputs]: raise SystemExit("ID/order mismatch")
rows=[]
for x in inputs:
 j=js[x["id"]]
 if set(j)!={"l","r","e","f","i","q","m"}: raise SystemExit(x["id"]+": explicit fields missing")
 if len(j["l"])!=5 or len(j["r"])!=5: raise SystemExit(x["id"]+": five judgments required")
 vals=[{"0":0,"1":1,"?":"待定"}[v] for v in j["l"]]
 reasons=[R.get(v,v) for v in j["r"]]
 if any(not v for v in reasons): raise SystemExit(x["id"]+": blank reason")
 rows.append({"id":x["id"],"labels":dict(zip(DIMS,vals)),"dimension_reasons":dict(zip(DIMS,reasons)),
  "evidence":[dict(zip(("dimension","source","quote"),e)) for e in j["e"]],"material_issue":j["m"],
  "fairness_subtypes":j["f"],"innovation_subtypes":j["i"],"safety_quality_basis":j["q"]})
op.write_text(json.dumps({"protocol_version":"CAL-5D-20260926-v1.3","rows":rows},ensure_ascii=False,indent=2)+"\n")
print(op)
