"""Expand manually recorded row-by-row judgments into the frozen output schema."""
import json
import sys
from pathlib import Path

DIMS = ["S", "E", "Ec", "I", "F"]

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text())
    rows = []
    for item in data:
        assert list(item["labels"].keys()) == DIMS
        assert list(item["reasons"].keys()) == DIMS
        rows.append({
            "id": item["id"],
            "labels": item["labels"],
            "dimension_reasons": item["reasons"],
            "evidence": item["evidence"],
            "material_issue": item.get("material_issue", ""),
            "fairness_subtypes": item.get("fairness_subtypes", []),
            "innovation_subtypes": item.get("innovation_subtypes", []),
            "safety_quality_basis": item["safety_quality_basis"],
        })
    dst.write_text(json.dumps({"protocol_version":"CAL-5D-20260926-v1.3","rows":rows}, ensure_ascii=False, indent=2)+"\n")

if __name__ == "__main__":
    main()
