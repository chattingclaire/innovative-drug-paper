"""Predeclared fresh real-file adapter constructs, not corpus validation."""
import copy
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from source_locator_adapter01 import Adapter, PROJECTOR, Unsupported, sha

HERE = Path(__file__).resolve().parent


def run():
    design = json.loads((HERE / "constructed_design01.json").read_text())
    results = []
    with tempfile.TemporaryDirectory(prefix="locator-adapter01-constructs-") as tmp:
        for case in design["checks"]:
            name = case["name"]
            folder = Path(tmp) / name; folder.mkdir()
            leaf = "独立构造的定位句。"
            source = folder / ("source.pdf" if name.startswith(("PDF_", "explicit_single_")) else "source.txt")
            source.write_text(leaf, encoding="utf-8")
            para = {"id": "p1", "text": leaf, "pages": [1]}
            unit = {"id": "u1", "text": leaf, "paragraph_id": "p1", "pages": [1]}
            candidate = {"source": str(source), "source_sha256": sha(source), "unit_candidates": [unit], "paragraphs": [para]}
            row = {"id": "CONSTRUCT-" + name, "text": leaf, "pages": [1], "contexts": {}}
            pointer = "/text"
            if name == "current_multi_paragraph_relation_rejected":
                del unit["paragraph_id"]; unit["paragraph_ids"] = ["p1", "p2"]
            elif name == "current_duplicate_unit_id_rejected":
                candidate["unit_candidates"].append(copy.deepcopy(unit))
            elif name.startswith("context_") and name != "candidate_relation_mismatch_binder_rejected":
                row["contexts"]["paragraph_context"] = [{"paragraph_id": "p1" if name == "context_exact_paragraph_id_unique" else "not-real", "text": leaf, "pages": [1]}]
                pointer = "/contexts/paragraph_context/0/text"
            elif name.startswith("heading_") or name.startswith("preceding_"):
                key = "nearest_preceding_heading" if name.startswith("heading_") else "immediately_preceding_paragraph"
                row["contexts"][key] = {"text": leaf, "pages": [1]}; pointer = "/contexts/" + key + "/text"
                if "repeated" in name:
                    candidate["paragraphs"].append({"id": "p2", "text": leaf, "pages": [1]})
            elif name == "candidate_relation_mismatch_binder_rejected":
                other = folder / "other.txt"; other.write_text("另一来源", encoding="utf-8")
                candidate.update(source=str(other), source_sha256=sha(other))
            elif name == "PDF_multpage_not_guessed":
                unit["pages"] = para["pages"] = row["pages"] = [1, 2]
            elif name.startswith("native_grid_") or name == "non_native_table_array_rejected":
                cells, columns, title = ["格甲", "格乙"], ["列甲", "列乙"], "构造原生表题"
                grid = {"title": title, "columns": columns, "rows": [cells]}
                if name == "native_grid_duplicate_row_without_index_rejected":
                    grid["rows"].append(copy.deepcopy(cells))
                if name != "non_native_table_array_rejected":
                    source = folder / "source.json"; source.write_text(json.dumps({"tables": [grid]}, ensure_ascii=False), encoding="utf-8")
                candidate.update(source=str(source), source_sha256=sha(source), structured_tables=[copy.deepcopy(grid)])
                unit.update(text=" | ".join(cells), cells=cells, columns=columns, table_title=title)
                para.update(text=unit["text"], cells=cells, columns=columns, table_title=title)
                row["text"] = unit["text"]; leaf = row["text"]
                if name in {"native_grid_cell_column_position", "non_native_table_array_rejected"}:
                    row["contexts"]["verified_table_context_v4"] = [{"table_title": title, "column_names": columns, "raw_row_cells": cells, "row_index_zero_based": 0}]
                    pointer = "/contexts/verified_table_context_v4/0/raw_row_cells/1"; leaf = cells[1]
            elif name.startswith("boundary_"):
                row["contexts"]["verified_parent_list_v8"] = {"boundary": leaf}
                pointer = "/contexts/verified_parent_list_v8/boundary"
                if name == "boundary_absent_from_candidate_rejected":
                    leaf = "候选从未出现的边界。"; row["contexts"]["verified_parent_list_v8"]["boundary"] = leaf
            candidate_path = folder / "candidate.json"; candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            rule = {"id": row["id"], "input": {"unit_id": "u1", "source": str(source), "source_sha256": sha(source), "candidate_file": str(candidate_path), "candidate_sha256": sha(candidate_path)}}
            origin = PROJECTOR.source_pair(rule["input"], pointer="/rule/input")
            if name == "source_partial_layer_rejected":
                origin = PROJECTOR.source_pair({"source_path": str(source)}, origin, "/contexts/partial")
            occurrence = {"raw_pointer": pointer, "text_sha256": hashlib.sha256(leaf.encode()).hexdigest(), "character_n": len(leaf)}
            if not name.startswith("boundary_"):
                occurrence["source_binding"] = origin
            sidecar = {"current_source_priority": origin}
            original = copy.deepcopy((row, rule, occurrence, sidecar))
            adapter = Adapter()
            if name == "explicit_single_page_metadata_preserved":
                _, plan = adapter.plan(row, rule, occurrence, sidecar)
                actual_ok = plan["source_locator"] == {"page_one_based": 1}
                actual = {"check_kind": "locator_plan_only_not_PDF_authentication", "plan": plan}
            else:
                actual = adapter.bind(row, rule, occurrence, sidecar)
                actual_ok = actual["status"] in {"bound_literal", "bound_native_grid_image_bytes_only"}
            checks = {"predeclared_expected_matches": actual_ok is case["expected_bound"], "inputs_unchanged": (row, rule, occurrence, sidecar) == original}
            if name == "native_grid_cell_column_position" and actual_ok:
                pos = actual["binding"]["source_position"]["native_grid_position"]
                checks["actual_cell_position_preserved"] = pos["row_index"] == 0 and pos["column_index"] == 1
            if name == "PDF_multpage_not_guessed":
                checks["binder_not_called_for_multi_page"] = actual["binder_called"] is False
            results.append({"name": name, "passed": all(checks.values()), "checks": checks, "actual": actual})
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "adapter_sha256": sha(HERE / "source_locator_adapter01.py"),
            "test_runner_sha256": sha(__file__), "design_sha256": sha(HERE / "constructed_design01.json"),
            "n": len(results), "passed_n": sum(x["passed"] for x in results), "results": results,
            "scope": "Fresh real-file constructs only; one PDF case is plan-only, no invented PDF authentication; no actual corpus/model/rule/gold."}


if __name__ == "__main__":
    target = HERE / "constructed_execution01.json"
    if target.exists():
        raise SystemExit("Retain first execution; do not overwrite.")
    report = run(); target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"n": report["n"], "passed_n": report["passed_n"], "failures": [r["name"] for r in report["results"] if not r["passed"]]}, ensure_ascii=False))
