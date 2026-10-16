"""Assemble explicitly authored, row-by-row semantic decisions; performs no classification."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ["S", "E", "Ec", "I", "F"]
NEG = {
    "S": "未讨论药物或用药损害、安全风险及其评价控制。",
    "E": "未讨论药物治疗效果、临床获益或相关证据。",
    "Ec": "未讨论药品价格、治疗费用、支付标准或基金影响。",
    "I": "未讨论药物创新属性、创新资格或研发创新支持。",
    "F": "未讨论药品保障获取、患者可负担性或具体临床管理难度。",
}

def build(packet_no: int):
    inp_path = HERE / f"input-{packet_no:03d}.json"
    spec_path = HERE / f"decisions-{packet_no:03d}.json"
    out_path = HERE / f"output-{packet_no:03d}.json"
    if out_path.exists():
        raise SystemExit(f"refusing to overwrite {out_path.name}")
    inputs = json.loads(inp_path.read_text())["rows"]
    specs = json.loads(spec_path.read_text())["rows"]
    if [x["id"] for x in inputs] != [x["id"] for x in specs]:
        raise SystemExit("decision/input ID mismatch")
    rows = []
    for inp, spec in zip(inputs, specs):
        positives = spec["positive_dimensions"]
        pending = spec.get("pending", False)
        if pending:
            labels = {d: "待定" for d in DIMS}
            reasons = {d: spec["pending_reason"] for d in DIMS}
            evidence = []
            safety_basis = "undetermined"
        else:
            labels = {d: int(d in positives) for d in DIMS}
            reasons = {}
            for d in DIMS:
                if d in positives:
                    reasons[d] = spec["positive_reasons"][d]
                else:
                    reasons[d] = f"该条仅涉及{spec['topic']}；{NEG[d]}"
            evidence = []
            for d in positives:
                evidence.append({"dimension": d, "source": "unit", "quote": inp["text"]})
            for extra in spec.get("context_evidence", []):
                evidence.append(extra)
            safety_basis = spec.get("safety_quality_basis", "no_quality_basis")
        row = {
            "id": inp["id"],
            "labels": labels,
            "dimension_reasons": reasons,
            "evidence": evidence,
            "material_issue": spec.get("material_issue", ""),
            "fairness_subtypes": spec.get("fairness_subtypes", []),
            "innovation_subtypes": spec.get("innovation_subtypes", []),
            "safety_quality_basis": safety_basis,
        }
        rows.append(row)
    out_path.write_text(json.dumps({"protocol_version": "CAL-5D-20260926-v1.3", "rows": rows}, ensure_ascii=False, indent=2) + "\n")
    print(out_path.name, hashlib.sha256(out_path.read_bytes()).hexdigest())

if __name__ == "__main__":
    build(int(sys.argv[1]))
