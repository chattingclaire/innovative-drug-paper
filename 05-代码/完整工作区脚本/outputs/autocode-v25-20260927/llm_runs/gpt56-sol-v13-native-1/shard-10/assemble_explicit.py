#!/usr/bin/env python3
"""Assemble already-made row judgments; performs no classification."""
import json, sys
from pathlib import Path

DIMS = ["S", "E", "Ec", "I", "F"]
here = Path(__file__).resolve().parent
batch = sys.argv[1]
inp_path = here / f"input-{batch}.json"
jud_path = here / f"judgments-{batch}.json"
out_path = here / f"output-{batch}.json"
if out_path.exists():
    raise SystemExit(f"refusing to overwrite {out_path.name}")
inputs = json.loads(inp_path.read_text())["rows"]
judgments = json.loads(jud_path.read_text())
if list(judgments) != [r["id"] for r in inputs]:
    raise SystemExit("judgment IDs/order do not match input")
rows = []
for inp in inputs:
    bid = inp["id"]
    j = judgments[bid]
    if set(j) != {"labels", "reasons", "evidence", "material_issue", "fairness_subtypes", "innovation_subtypes", "safety_quality_basis"}:
        raise SystemExit(f"{bid}: incomplete explicit judgment fields")
    if len(j["labels"]) != 5 or len(j["reasons"]) != 5:
        raise SystemExit(f"{bid}: five labels/reasons required")
    rows.append({
        "id": bid,
        "labels": dict(zip(DIMS, j["labels"])),
        "dimension_reasons": dict(zip(DIMS, j["reasons"])),
        "evidence": [dict(zip(("dimension", "source", "quote"), e)) for e in j["evidence"]],
        "material_issue": j["material_issue"],
        "fairness_subtypes": j["fairness_subtypes"],
        "innovation_subtypes": j["innovation_subtypes"],
        "safety_quality_basis": j["safety_quality_basis"],
    })
out_path.write_text(json.dumps({"protocol_version": "CAL-5D-20260926-v1.3", "rows": rows}, ensure_ascii=False, indent=2) + "\n")
print(out_path)
