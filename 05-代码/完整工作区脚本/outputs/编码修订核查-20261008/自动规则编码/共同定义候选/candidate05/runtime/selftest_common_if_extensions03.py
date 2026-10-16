"""Eight groups of wholly invented source-bound fixtures; no real units.

The source authenticators are exercised against temporary TXT/JSON/byte fixtures,
not mocked as `verified=True`.  Table visual provenance flags are fixture data,
not a claim of visual review of real policies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Existing frozen source authentication modules are read-only dependencies.
sys.path.insert(0, str(HERE.parents[1] / "runtime"))
sys.path.insert(0, str(HERE))
from common_if_extensions03 import inspect_extensions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def prose(folder, current, prefix="改良型新药的研发应关注产品设计。", suffix=""):
    folder.mkdir()
    source, candidate = folder / "source.txt", folder / "candidate.json"
    paragraph = prefix + current + suffix
    source.write_text(paragraph, encoding="utf-8")
    para = {"id": "fixture-paragraph", "text": paragraph, "pages": [1], "line_ids": ["fixture:1"]}
    write_json(candidate, {"unit_candidates": [{"id": "fixture-unit", "text": current,
        "paragraph_id": para["id"]}], "paragraphs": [para]})
    context = {"paragraph_id": para["id"], "text": paragraph, "pages": [1]}
    return {"unit_id": "fixture-unit", "unit_text": current,
            "source": str(source), "unit_source": str(source),
            "source_sha256": sha(source), "unit_source_sha256": sha(source),
            "candidate_file": str(candidate), "candidate_sha256": sha(candidate),
            "paragraph_context": [context],
            "llm_v29_shared_context": {"paragraph_context": [copy.deepcopy(context)]}}


def table(folder, *, title="治疗用生物制品注册分类示例表", description="改良型生物制品"):
    folder.mkdir()
    source, candidate, image = folder / "source.json", folder / "candidate.json", folder / "fixture-image.bin"
    image.write_bytes(b"invented-source-image-fixture-not-a-real-policy")
    columns = ["分类", "内容", "数据保护期", "备注"]
    cells = ["2类", description, "9年", "本行为自拟构造，不描述实际制度。"]
    current = " | ".join(cells)
    grid = {"title": title, "source_image": str(image), "source_sha256": sha(image),
            "source_url": "https://fixture.invalid/table", "visually_checked": True,
            "columns": columns, "rows": [cells]}
    write_json(source, {"source_url": "https://fixture.invalid/document", "tables": [grid]})
    para = {"id": "fixture-paragraph", "text": current, "cells": cells,
            "columns": columns, "table_title": title, "source_image": str(image),
            "line_ids": ["tables:1:row:1"]}
    unit = {"id": "fixture-unit", "type": "normative_table_row", "text": current,
            "paragraph_id": para["id"], "table_title": title, "columns": columns, "cells": cells}
    write_json(candidate, {"source": str(source), "source_sha256": sha(source),
        "unit_candidates": [unit], "paragraphs": [para], "structured_tables": [grid]})
    cert = {"kind": "verified_table_title_columns_v4", "table_title": title,
            "column_names": columns, "raw_row_cells": cells,
            "text": title + "；列名：" + " | ".join(columns),
            "source_structured_sha256": sha(source), "source_image": str(image),
            "source_image_sha256": sha(image), "source_url": grid["source_url"],
            "source_document_url": "https://fixture.invalid/document", "row_index_zero_based": 0}
    return {"unit_id": "fixture-unit", "unit_type": "normative_table_row", "unit_text": current,
            "source": str(source), "unit_source": str(source),
            "source_sha256": sha(source), "unit_source_sha256": sha(source),
            "candidate_file": str(candidate), "candidate_sha256": sha(candidate),
            "verified_table_context_v4": [cert],
            "llm_v29_shared_context": {"verified_table_context_v4": [copy.deepcopy(cert)]}}


def check(record, expected):
    before = copy.deepcopy(record)
    result = {"labels": {"I": 0}, "evidence": []}
    old = copy.deepcopy(result)
    evidence = inspect_extensions(record, result)
    assert bool(evidence) is expected, evidence
    assert record == before and result == old
    assert evidence == inspect_extensions(record, {"labels": {"I": 1}, "evidence": []})
    for e in evidence:
        assert e["dimension"] == "I" and e["subtype"] == "attribute"
        assert record["unit_text"][e["start"]:e["end"]] == e["text"]
        assert e["common_basis"] and e["context_dependency"]
    return evidence


def expect_binding_error(record):
    try:
        inspect_extensions(record, {})
    except ValueError:
        return
    raise AssertionError("altered supplied binding was silently accepted")


def main():
    with tempfile.TemporaryDirectory(prefix="common-if03-invented-") as tmp:
        root = Path(tmp)
        # 1: explicit improvement versus ordinary adjustment in identical scope.
        check(prose(root / "g1p", "对释放特征作改良时，应记录设计依据。"), True)
        check(prose(root / "g1n", "对释放特征作调整时，应记录设计依据。"), False)
        print("PASS group1 explicit_improvement_not_ordinary_change")
        # 2: self-contained substantive drug improvement; plain improvement insufficient.
        check({"unit_text": "对本药给药方式进行实质性改进。"}, True)
        check({"unit_text": "对本药给药方式进行改进。"}, False)
        print("PASS group2 self_contained_substantive_relation")
        # 3: genuine same-paragraph R&D object versus a title mention only.
        check(prose(root / "g3p", "对给药频率进行改良时，应说明研究方案。"), True)
        check(prose(root / "g3n", "对给药频率进行改良时，应说明研究方案。",
                    prefix="请阅读《改良型新药研发手册》。"), False)
        print("PASS group3_authenticated_object_not_title")
        # 4: exact paragraph membership cannot be forged by altering input text.
        real = prose(root / "g4", "对剂型进行改良时，应说明设计目的。")
        check(real, True)
        forged = copy.deepcopy(real)
        forged["paragraph_context"][0]["text"] = "伪造的改良型新药研发。" + real["unit_text"]
        forged["llm_v29_shared_context"]["paragraph_context"] = copy.deepcopy(forged["paragraph_context"])
        expect_binding_error(forged)
        print("PASS group4_paragraph_source_binding")
        # 5: an actual registration row requires its authenticated table context.
        registered = table(root / "g5")
        ev = check(registered, True)
        assert ev[0]["text"] == "2类 | 改良型生物制品" and "9年" not in ev[0]["text"]
        absent = copy.deepcopy(registered)
        absent.pop("verified_table_context_v4")
        absent["llm_v29_shared_context"] = {}
        check(absent, False)
        print("PASS group5_actual_classification_not_protection_term")
        # 6: category names in a non-registration table are ordinary objects.
        check(table(root / "g6p"), True)
        check(table(root / "g6n", title="治疗用生物制品库存统计表"), False)
        print("PASS group6_registration_header_required")
        # 7: a descriptive object/usage phrase is not an actual category cell.
        check(table(root / "g7p", description="创新型生物制品"), True)
        check(table(root / "g7n", description="改良型药品使用登记"), False)
        print("PASS group7_actual_category_not_object_name")
        # 8: stale row context fails certification; undetermined input is untouched.
        valid = table(root / "g8")
        check(valid, True)
        stale = copy.deepcopy(valid)
        stale["unit_text"] = stale["unit_text"].replace("2类", "3类", 1)
        expect_binding_error(stale)
        assert inspect_extensions(valid, {"judgement_status": "undetermined"}) == []
        print("PASS group8_current_row_binding_and_undetermined")
    print("8 invented positive/negative groups passed; actual fixture authentication, exact offsets and non-mutation checked")


if __name__ == "__main__":
    main()
