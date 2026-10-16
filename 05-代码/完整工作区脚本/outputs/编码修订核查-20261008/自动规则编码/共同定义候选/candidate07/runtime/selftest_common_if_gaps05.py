"""Six invented component checks; no real inputs or reference labels.

Source-dependent cases use temporary literal sources and the real authenticators.
The table PNG is an actually rendered, visually inspected invented fixture.
No fake authentication dictionaries or mocked authenticators are used.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from common_if_relations import inspect_innovation, inspect_fairness
from common_if_extensions03 import inspect_extensions
from common_definition_stage import _context_evidence
from source_context_adapter_v34 import authenticate_target, following_list
from context_validation import payload_digest

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def registration_table(folder):
    folder.mkdir()
    source, candidate = folder / "source.json", folder / "candidate.json"
    image = HERE.parent / "fixtures" / "registration_table_fixture.png"
    title = "自拟夹具：治疗用生物制品注册分类示例表"
    columns = ["分类", "内容", "数据保护期", "备注"]
    cells = ["2类", "改良型生物制品", "9年", "仅为构造示例，不描述实际制度"]
    current = " | ".join(cells)
    grid = {"title": title, "source_image": str(image), "source_sha256": sha(image),
            "source_url": "https://fixture.invalid/table", "visually_checked": True,
            "columns": columns, "rows": [cells]}
    write_json(source, {"source_url": "https://fixture.invalid/document", "tables": [grid]})
    para = {"id": "p0", "text": current, "cells": cells, "columns": columns,
            "table_title": title, "source_image": str(image), "line_ids": ["tables:1:row:1"]}
    unit = {"id": "u0", "type": "normative_table_row", "text": current,
            "paragraph_id": "p0", "table_title": title, "columns": columns, "cells": cells}
    write_json(candidate, {"source": str(source), "source_sha256": sha(source),
                           "unit_candidates": [unit], "paragraphs": [para], "structured_tables": [grid]})
    cert = {"kind": "verified_table_title_columns_v4", "table_title": title,
            "column_names": columns, "raw_row_cells": cells,
            "text": title + "；列名：" + " | ".join(columns),
            "source_structured_sha256": sha(source), "source_image": str(image),
            "source_image_sha256": sha(image), "source_url": grid["source_url"],
            "source_document_url": "https://fixture.invalid/document", "row_index_zero_based": 0}
    return {"unit_id": "u0", "unit_type": "normative_table_row", "unit_text": current,
            "source": str(source), "unit_source": str(source),
            "source_sha256": sha(source), "unit_source_sha256": sha(source),
            "candidate_file": str(candidate), "candidate_sha256": sha(candidate),
            "verified_table_context_v4": [cert],
            "llm_v29_shared_context": {"verified_table_context_v4": [copy.deepcopy(cert)]}}


def required_list(folder, current):
    folder.mkdir()
    source, candidate = folder / "source.txt", folder / "candidate.json"
    texts = [current, "药物原创性。", "患者可负担性。", "下一节行政事项。"]
    source.write_text("\n".join(texts), encoding="utf-8")
    paragraphs = [{"id": "p" + str(i), "text": text, "line_ids": ["fixture:" + str(i + 1)]}
                  for i, text in enumerate(texts)]
    write_json(candidate, {"paragraphs": paragraphs,
                           "unit_candidates": [{"id": "u0", "text": current, "paragraph_id": "p0"}]})
    contexts = [{"text": x["text"], "paragraph_id": x["id"], "source_path": str(source),
                 "source_sha256": sha(source), "candidate_path": str(candidate),
                 "candidate_sha256": sha(candidate), "source_lines": x["line_ids"]}
                for x in paragraphs[:3]]
    cert = {"original_unit_sha256": digest(current), "source_sha256": sha(source),
            "contexts": contexts, "contexts_sha256": payload_digest(contexts),
            "repair_status": "supplemented", "unresolved_material_gaps": [],
            "structure_boundary": {"all_paragraphs_in_interval_included": True,
                "first_paragraph": "p0", "last_paragraph": "p2",
                "next_paragraph_id": "p3", "next_paragraph_text": texts[3]}}
    record = {"unit_id": "u0", "unit_text": current, "source": str(source),
              "unit_source": str(source), "source_sha256": sha(source),
              "unit_source_sha256": sha(source), "candidate_file": str(candidate),
              "candidate_sha256": sha(candidate), "complete_following_list_v11": cert,
              "llm_v29_shared_context": {"complete_following_list_v11": copy.deepcopy(cert)}}
    authenticate_target(record)
    typed = []
    assert following_list(record, record["llm_v29_shared_context"], typed, [])
    assert all(c["authentication_v34"]["literal_reproduced_in_current_runtime"]
               for g in typed for c in g["contexts"])
    record["typed_contexts_v34"] = typed
    return record


def main():
    checks = []

    def inspect(group, name, text, dimension, expected, *, drug_scope=False):
        detector = inspect_innovation if dimension == "I" else inspect_fairness
        evidence = detector(text, drug_scope=drug_scope)
        assert bool(evidence) is expected, (name, evidence)
        assert all(text[e["start"]:e["end"]] == e["quote"] for e in evidence)
        checks.append({"group": group, "name": name, "constructed_text": text,
                       "dimension": dimension, "expected_attention": expected,
                       "actual_relation_present": bool(evidence), "source_offsets_valid": True,
                       "kind": "pure_relation_component", "drug_scope_argument": drug_scope})

    inspect(1, "needs_base", "按临床用药需求配备药品。", "F", True)
    inspect(1, "needs_comma", "按临床用药需求，配备药品。", "F", True)
    inspect(1, "needs_ascii_comma", "按临床用药需求,配备药品。", "F", True)
    inspect(1, "unrelated_subject_after_comma", "按临床用药需求，运输部门登记药品。", "F", False)
    inspect(1, "hard_sentence_boundary", "按临床用药需求。另行配备药品。", "F", False)
    inspect(1, "ordinary_supply", "配备药品。", "F", False)

    inspect(2, "affordability_base", "需要评估该药的患者可负担性。", "F", True)
    inspect(2, "affordability_subject_first", "该药的患者可负担性需要评估。", "F", True)
    inspect(2, "affordability_uncertain", "该药的患者可负担性尚不明确。", "F", True)
    inspect(2, "affordability_column", "该药的患者可负担性栏目需要评估。", "F", False)
    inspect(2, "fund_not_patient_affordability", "该药的基金可负担性需要评估。", "F", False)
    inspect(2, "other_cost_despite_drug_scope", "患者交通费可负担性需要评估。", "F", False, drug_scope=True)

    inspect(3, "drug_cost_base", "降低低收入患者的药品费用。", "F", True)
    inspect(3, "parallel_other_cost", "降低低收入患者的交通费及药品费用。", "F", True)
    inspect(3, "parallel_three_costs", "降低低收入患者的交通费、检查费及药品费用。", "F", True)
    inspect(3, "only_non_drug_costs", "降低低收入患者的交通费及设备费。", "F", False, drug_scope=True)
    inspect(3, "ordinary_cost_no_fairness", "降低患者的交通费及药品费用。", "F", False)
    inspect(3, "separate_cost_predicates", "降低低收入患者的交通费，另行登记药品费用。", "F", False)

    inspect(4, "support_base", "为创新药研发提供专项资金。", "I", True)
    inspect(4, "support_resource_first", "专项资金由政策部门提供给创新药研发项目。", "I", True)
    inspect(4, "generic_rd_not_innovation", "专项资金由政策部门提供给药品研发项目。", "I", False)
    inspect(4, "innovative_object_only", "创新药研发项目应报送财务材料。", "I", False)
    inspect(4, "non_drug_innovation", "专项资金由政策部门提供给设备研发项目。", "I", False)

    with tempfile.TemporaryDirectory(prefix="common-if05-invented-") as tmp:
        root = Path(tmp)
        registered = registration_table(root / "registration")
        before = copy.deepcopy(registered)
        ev = inspect_extensions(registered, {})
        assert ev and registered == before
        assert all(registered["unit_text"][e["start"]:e["end"]] == e["text"] for e in ev)
        checks.append({"group": 5, "name": "registration_bound_table", "expected_attention": True,
                       "actual_relation_present": bool(ev), "source_offsets_valid": True,
                       "kind": "actual_temporary_source_candidate_image_binding",
                       "invented_image_sha256": sha(HERE.parent / "fixtures" / "registration_table_fixture.png")})
        inspect(5, "registration_prose_same_category", "该药注册分类为改良型生物制品。", "I", True)
        inspect(5, "registration_existing_category", "该药注册分类为改良型新药。", "I", True)
        inspect(5, "category_object_only", "改良型生物制品应按时提交资料。", "I", False)
        inspect(5, "class_number_only", "该药属于2类。", "I", False)
        unbound = copy.deepcopy(registered)
        unbound.pop("verified_table_context_v4")
        unbound["llm_v29_shared_context"] = {}
        assert inspect_extensions(unbound, {}) == []
        checks.append({"group": 5, "name": "table_without_certificate", "rejected": True})
        stale = copy.deepcopy(registered)
        stale["unit_text"] = stale["unit_text"].replace("2类", "3类", 1)
        try:
            inspect_extensions(stale, {})
        except ValueError:
            checks.append({"group": 5, "name": "stale_table_target", "authentication_error": True})
        else:
            raise AssertionError("stale table target accepted")

        for i, (name, text, expected) in enumerate([
            ("requirement_base", "药品评价应包括以下内容：", {"I", "F"}),
            ("independent_navigation", "药品评价应包括以下内容，附件格式详见工作方案：", {"I", "F"}),
            ("navigation_before_requirement", "附件格式详见工作方案。药品评价应包括以下内容：", {"I", "F"}),
            ("navigation_only", "药品评价内容详见工作方案。", set()),
            ("requirement_inside_navigation", "药品评价详见应包括以下内容的工作方案。", set()),
        ]):
            record = required_list(root / ("list" + str(i)), text)
            before = copy.deepcopy(record)
            evidence = _context_evidence(record, text, True)
            assert {e["dimension"] for e in evidence} == expected, (name, evidence)
            assert record == before
            for e in evidence:
                assert text[e["start"]:e["end"]] == e["text"]
                for a in e["cited_substantive_anchors"]:
                    assert a["source_authentication"]["literal_reproduced_in_current_runtime"]
                    context = next(c for g in record["typed_contexts_v34"] for c in g["contexts"]
                                   if c["paragraph_id"] == a["paragraph_id"])
                    assert context["text"][a["start"]:a["end"]] == a["text"]
            checks.append({"group": 6, "name": name, "constructed_text": text,
                           "expected_dimensions": sorted(expected),
                           "actual_dimensions": sorted({e["dimension"] for e in evidence}),
                           "source_offsets_valid": True, "kind": "actual_literal_complete_list_authentication"})
        assert _context_evidence({"unit_text": "药品评价应包括以下内容："}, "药品评价应包括以下内容：", True) == []
        checks.append({"group": 6, "name": "requirement_without_authenticated_context", "rejected": True})
        forged = required_list(root / "list-forged", "药品评价应包括以下内容：")
        forged["complete_following_list_v11"]["contexts"][1]["text"] = "来源中不存在的内容。"
        forged["complete_following_list_v11"]["contexts_sha256"] = payload_digest(forged["complete_following_list_v11"]["contexts"])
        forged["llm_v29_shared_context"]["complete_following_list_v11"] = copy.deepcopy(forged["complete_following_list_v11"])
        try:
            following_list(forged, forged["llm_v29_shared_context"], [], [])
        except ValueError:
            checks.append({"group": 6, "name": "forged_context_text", "authentication_error": True})
        else:
            raise AssertionError("invented unbound content accepted")

    print(json.dumps({"passed": True, "group_n": 6, "check_n": len(checks), "checks": checks,
                      "real_policy_units_read": 0, "reference_labels_loaded": False,
                      "authenticators_mocked": False, "full_pipeline_executed": False,
                      "interpretation": "Constructed component behavior only; no empirical validity or real error-rate claim."}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
