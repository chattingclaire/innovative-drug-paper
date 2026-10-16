"""Constructed semantic controls; no research row IDs or reference input."""
import hashlib
import json
from pathlib import Path

from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

CASES = [
    ("general-design-goal", "本指南指导药物使用设计考虑，回应老年患者需求，以减少用药差错，提升老年患者的整体健康水平。", {"S": 1, "E": 0}),
    ("unmarked-general-goal", "药物研发考虑患者体验和偏好，以提升整体健康水平。", {"E": 0}),
    ("direct-drug-benefit", "该药可改善老年患者的整体健康水平。", {"E": 1}),
    ("uncertain-drug-benefit", "该药能否提高老年患者整体健康水平尚需验证。", {"E": 1}),
    ("negative-drug-benefit", "研究尚不能证明该药提高老年患者的整体健康水平。", {"E": 1}),
    ("effect-evaluation", "应评估该药对老年患者整体健康水平的影响。", {"E": 1}),
    ("baseline-only", "药物临床试验入组前，应评估患者基线整体健康水平。", {"E": 0}),
    ("before-after-effect", "应比较该药治疗前后老年患者整体健康水平的变化。", {"E": 1}),
    ("safety-only", "药师应核对用药禁忌，预防用药差错。", {"S": 1, "E": 0}),
    ("enactment-purpose-only", "为促进合理用药、保障患者用药安全，制定本规范。", {"S": 0, "E": 0}),
    ("purpose-with-effect-content", "本研究旨在比较该药与现有疗法的治疗效果。", {"E": 1}),
    ("explicit-health-benefit", "应提供该药治疗产生的健康获益证据。", {"E": 1}),
]


def run_case(name, current, expected):
    sha = hashlib.sha256(current.encode()).hexdigest()
    ref = {"sha256": sha, "source_resource_id": "CONSTRUCTED-" + sha, "locator": {}}
    bundle = {
        "common_source_bundle_version": "constructed-control-not-study",
        "source_record": {"id": "CONSTRUCTED-" + name, "text": current, "source_ref": ref, "contexts": []},
        "source_documents": [], "explicit_or_primary_source_resources": [],
        "preserved_historical_neutral_source_supplements": [], "source_full_text_resources": [],
        "source_asset_locations": [], "source_locator_bases": {}, "source_reference_index": [],
        "source_provenance_addenda": [],
    }
    view = RelationView(semantic_unit(bundle))
    decisions = judge(view)
    validate_decisions(view.unit, decisions)
    actual = {dim: decisions[dim]["value"] for dim in expected}
    return {
        "name": name, "current": current, "expected_by_frozen_manual": expected,
        "actual": actual, "passed": actual == expected,
        "reasons": {dim: decisions[dim]["reason"] for dim in expected},
        "constructed_only": True, "cohort_inference": False,
    }


results = [run_case(*case) for case in CASES]
output = {"cases": results, "case_N": len(results), "passed": all(case["passed"] for case in results),
          "research_reference_read": False, "actual_cohort_runs": 0, "LLM_calls": 0}
with (Path(__file__).parent / "health-boundary-control-results-attempt01.json").open("x") as stream:
    stream.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"case_N": len(results), "passed": output["passed"],
                  "failed": [case for case in results if not case["passed"]]}, ensure_ascii=False))
raise SystemExit(0 if output["passed"] else 2)
