#!/usr/bin/env python3
"""Read-only, standard-library capture of AI-seeded posthoc review workbooks.

This module does not call a receiver, write labels, or compute metrics. XLSX
files written by it are exact input-byte snapshots, never authored workbooks.
"""
import argparse
import collections
import copy
import datetime
import decimal
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
BINDING_SHA = "71579292c404c6ce63b5628a20632c3106138f8468bb41cef474b57111c65cea"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN}
DIMS = ("S", "E", "Ec", "I", "F")
DIM_TEXT = {"S": "S 安全性", "E": "E 有效性", "Ec": "Ec 经济性", "I": "I 创新性", "F": "F 公平性"}
FIELDS = {"A": "id", "B": "department", "C": "dimension_display", "D": "label", "E": "reason", "F": "original_text", "G": "judgment_version", "H": "context_pointer"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, obj):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def fingerprint(path, data):
    return {"path": str(path), "bytes": len(data), "sha256": sha(data)}


def decode_cell(cell, shared):
    kind = cell.get("t", "n")
    value = cell.find("m:v", NS)
    raw = "" if value is None or value.text is None else value.text
    if kind == "inlineStr":
        raw = "".join(x.text or "" for x in cell.findall("m:is//m:t", NS))
    elif kind == "s":
        try:
            index = int(raw)
            if index < 0:
                raise ValueError("Negative shared-string index")
            raw = shared[index]
        except (ValueError, IndexError) as exc:
            raise ValueError("Invalid shared-string index") from exc
    formula = cell.find("m:f", NS)
    return {"raw": raw, "type": kind, "formula": None if formula is None else (formula.text or "")}


EMPTY = {"raw": "", "type": "n", "formula": None}


def label_value(cell):
    """Missing, pending and invalid values remain distinct and never become 0."""
    raw = cell["raw"]
    text = raw.strip()
    if cell["formula"] is not None:
        return {"kind": "invalid", "value": None, "reason": "formula_not_literal_label"}
    if not text:
        return {"kind": "blank", "value": None, "reason": "empty_cell"}
    if cell["type"] in ("str", "s", "inlineStr"):
        if text == "待定":
            return {"kind": "pending", "value": None, "reason": "explicit_pending"}
        if text in ("0", "1"):
            return {"kind": "binary", "value": int(text), "reason": None}
        return {"kind": "invalid", "value": None, "reason": "string_not_0_1_or_待定"}
    if cell["type"] == "n":
        try:
            value = decimal.Decimal(text)
            if value.is_finite() and value in (0, 1):
                return {"kind": "binary", "value": int(value), "reason": None}
        except decimal.InvalidOperation:
            pass
        return {"kind": "invalid", "value": None, "reason": "numeric_not_0_or_1"}
    return {"kind": "invalid", "value": None, "reason": "unsupported_cell_type"}


def dim_value(cell):
    raw = cell["raw"].strip()
    if cell["formula"] is None:
        for dim in DIMS:
            if raw in (dim, DIM_TEXT[dim]):
                return dim
    return None


def read_workbook(data):
    """Read values and formulas only; no external relationships or code execute."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member names")
        shared = []
        if "xl/sharedStrings.xml" in names:
            tree = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//m:t", NS)) for si in tree.findall("m:si", NS)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relation = {}
        for rel in rels:
            if rel.get("Id") in relation:
                raise ValueError("Duplicate workbook relationship ID")
            relation[rel.get("Id")] = rel.attrib
        result = {"sheet_order": [], "sheets": {}}
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            name = sheet.get("name")
            if name in result["sheets"]:
                raise ValueError("Duplicate worksheet name")
            ref = relation[sheet.get("{" + REL + "}id")]
            if ref.get("TargetMode") == "External":
                raise ValueError("External worksheet relationship")
            target = ref["Target"]
            member = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("xl") / target)
            if ".." in PurePosixPath(member).parts:
                raise ValueError("Parent-path worksheet relationship")
            tree = ET.fromstring(archive.read(member))
            rows = {}
            cells = {}
            for row in tree.findall("m:sheetData/m:row", NS):
                if not re.fullmatch(r"[1-9][0-9]*", row.get("r", "")):
                    raise ValueError("Invalid worksheet row number")
                number = int(row.get("r"))
                if number < 1 or number in rows:
                    raise ValueError("Invalid or duplicate worksheet row")
                rows[number] = {}
                for cell in row.findall("m:c", NS):
                    coordinate = cell.get("r", "")
                    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", coordinate)
                    if not match or int(match[2]) != number or coordinate in cells:
                        raise ValueError("Invalid or duplicate cell coordinate")
                    value = decode_cell(cell, shared)
                    rows[number][match[1]] = value
                    cells[coordinate] = value
            result["sheet_order"].append(name)
            result["sheets"][name] = {"rows": rows, "cells": cells}
        return result


def coding_rows(book):
    sheet = book["sheets"]["编码表"]
    result = []
    for number, cells in sorted(sheet["rows"].items()):
        if number < 7 or not any(v["raw"].strip() or v["formula"] is not None for v in cells.values()):
            continue
        values = {field: cells.get(col, EMPTY) for col, field in FIELDS.items()}
        result.append({"row": number, "id": values["id"]["raw"].strip(), "dimension": dim_value(values["dimension_display"]), "cells": values, "label": label_value(values["label"])})
    return result


def key(row):
    return (row["id"], row["dimension"])


def validate(rows, expected):
    errors = []
    counts = collections.Counter(key(row) for row in rows)
    duplicates = [{"id": k[0], "dimension": k[1], "count": n, "rows": [r["row"] for r in rows if key(r) == k]} for k, n in counts.items() if n > 1]
    if len(rows) != 385:
        errors.append({"kind": "row_count", "expected": 385, "actual": len(rows)})
    if len({r["id"] for r in rows}) != 77:
        errors.append({"kind": "id_count", "expected": 77, "actual": len({r["id"] for r in rows})})
    if duplicates:
        errors.append({"kind": "duplicate_id_dimension", "details": duplicates})
    invalid_identifiers = [{"row": r["row"], "raw": r["cells"]["id"]} for r in rows if not re.fullmatch(r"RECODE25-[0-9]{5}", r["id"]) or r["cells"]["id"]["formula"] is not None]
    if invalid_identifiers:
        errors.append({"kind": "invalid_identifier", "details": invalid_identifiers})
    invalid_dimensions = [{"row": r["row"], "raw": r["cells"]["dimension_display"]} for r in rows if r["dimension"] is None]
    if invalid_dimensions:
        errors.append({"kind": "invalid_dimension", "details": invalid_dimensions})
    missing = sorted(expected - set(counts))
    extra = sorted(set(counts) - expected, key=lambda x: (x[0], str(x[1])))
    if missing or extra:
        errors.append({"kind": "baseline_key_set_changed", "missing": missing, "extra": extra})
    dim_errors = [{"id": identifier, "dimension_counts": dict(collections.Counter(r["dimension"] for r in rows if r["id"] == identifier))} for identifier in sorted({r["id"] for r in rows}) if collections.Counter(r["dimension"] for r in rows if r["id"] == identifier) != collections.Counter(DIMS)]
    if dim_errors:
        errors.append({"kind": "id_must_have_exactly_five_dimensions", "details": dim_errors})
    kinds = collections.Counter(r["label"]["kind"] for r in rows)
    issues = {kind: [{"row": r["row"], "id": r["id"], "dimension": r["dimension"], "cell": "D" + str(r["row"]), "raw_cell": r["cells"]["label"], **r["label"]} for r in rows if r["label"]["kind"] == kind] for kind in ("blank", "pending", "invalid")}
    return {"structural_ok": not errors, "row_count": len(rows), "unique_id_dimension_count": len(counts), "id_count": len({r["id"] for r in rows}), "structural_errors": errors, "label_kind_counts": {kind: kinds[kind] for kind in ("binary", "pending", "blank", "invalid")}, "binary_class_counts": {str(value): sum(r["label"]["kind"] == "binary" and r["label"]["value"] == value for r in rows) for value in (0, 1)}, "label_issues": issues, "blank_reason_rows": [r["row"] for r in rows if not r["cells"]["reason"]["raw"].strip()], "pending_without_reason_rows": [r["row"] for r in rows if r["label"]["kind"] == "pending" and not r["cells"]["reason"]["raw"].strip()]}


def meaningful_cells(sheet):
    return {c: v for c, v in sheet["cells"].items() if v["raw"] != "" or v["formula"] is not None}


def diff_cells(left, right):
    result = []
    for coordinate in sorted(set(left) | set(right), key=lambda c: (int(re.search(r"[0-9]+", c)[0]), re.match(r"[A-Z]+", c)[0])):
        old, new = left.get(coordinate, EMPTY), right.get(coordinate, EMPTY)
        if old != new:
            result.append({"cell": coordinate, "baseline": old, "captured": new})
    return result


def compare_book(baseline, current, base_rows, rows):
    # Ambiguous duplicate keys do not silently select the last row.
    base_map = {key(r): r for r in base_rows}
    counts = collections.Counter(key(r) for r in rows)
    current_map = {key(r): r for r in rows if counts[key(r)] == 1}
    field_changes = {field: [] for field in FIELDS.values()}
    row_moves = []
    for k in sorted(set(base_map) & set(current_map)):
        old, new = base_map[k], current_map[k]
        if old["row"] != new["row"]:
            row_moves.append({"id": k[0], "dimension": k[1], "baseline_row": old["row"], "captured_row": new["row"]})
        for field in FIELDS.values():
            if old["cells"][field] != new["cells"][field]:
                item = {"id": k[0], "dimension": k[1], "baseline_row": old["row"], "captured_row": new["row"], "baseline": old["cells"][field], "captured": new["cells"][field]}
                if field == "label":
                    item["baseline_parsed"] = old["label"]
                    item["captured_parsed"] = new["label"]
                field_changes[field].append(item)
    position_changes = []
    a, b = {r["row"]: r for r in base_rows}, {r["row"]: r for r in rows}
    for row in sorted(set(a) | set(b)):
        old, new = a.get(row), b.get(row)
        if (None if old is None else key(old)) != (None if new is None else key(new)):
            position_changes.append({"row": row, "baseline_id_dimension": None if old is None else key(old), "captured_id_dimension": None if new is None else key(new), "baseline_identifier_cell": None if old is None else old["cells"]["id"], "captured_identifier_cell": None if new is None else new["cells"]["id"], "baseline_dimension_cell": None if old is None else old["cells"]["dimension_display"], "captured_dimension_cell": None if new is None else new["cells"]["dimension_display"]})
    headers = diff_cells({c: v for c, v in meaningful_cells(baseline["sheets"]["编码表"]).items() if int(re.search(r"[0-9]+", c)[0]) < 7}, {c: v for c, v in meaningful_cells(current["sheets"]["编码表"]).items() if int(re.search(r"[0-9]+", c)[0]) < 7})
    context = diff_cells(meaningful_cells(baseline["sheets"]["原文语境"]), meaningful_cells(current["sheets"]["原文语境"]))
    return {"field_changes_by_id_dimension": field_changes, "row_moves": row_moves, "identifier_dimension_position_changes": position_changes, "coding_header_changes": headers, "original_context_cell_changes": context, "sheet_order_changed": baseline["sheet_order"] != current["sheet_order"], "baseline_sheet_order": baseline["sheet_order"], "captured_sheet_order": current["sheet_order"], "representation_changes_are_reported_even_if_parsed_label_is_equal": True}


def load_baseline():
    path = HERE / "baseline-binding.json"
    raw = path.read_bytes()
    if sha(raw) != BINDING_SHA:
        raise ValueError("Frozen baseline-binding SHA mismatch")
    binding = json.loads(raw)
    books = {}
    for record in [binding["root_receipt"], binding["root_human_report_reception"], *binding["workbooks"].values()]:
        snapshot = (HERE / record["snapshot_relative_path"]).resolve()
        if not snapshot.is_relative_to(HERE / "baseline"):
            raise ValueError("Baseline snapshot escapes component")
        data = snapshot.read_bytes()
        if len(data) != record["bytes"] or sha(data) != record["sha256"]:
            raise ValueError("Frozen baseline snapshot bytes/SHA mismatch")
    receipt = json.loads((HERE / binding["root_receipt"]["snapshot_relative_path"]).read_bytes())
    report = json.loads((HERE / binding["root_human_report_reception"]["snapshot_relative_path"]).read_bytes())
    if report["human_posthoc_review_report_received"] is not True:
        raise ValueError("Bound human posthoc report reception missing")
    for role, record in binding["workbooks"].items():
        expected_receipt = [r for r in receipt["output_files"] if r["filename"] == Path(record["path"]).name]
        if len(expected_receipt) != 1 or expected_receipt[0]["sha256"] != record["sha256"]:
            raise ValueError("Baseline workbook not bound to ROOT delivery receipt")
        book = read_workbook((HERE / record["snapshot_relative_path"]).read_bytes())
        rows = coding_rows(book)
        status = validate(rows, set(key(r) for r in rows))
        if not status["structural_ok"] or status["label_kind_counts"] != {"binary": 385, "pending": 0, "blank": 0, "invalid": 0}:
            raise ValueError("Frozen baseline shape/labels mismatch")
        books[role] = (book, rows)
    if set(key(r) for r in books["A"][1]) != set(key(r) for r in books["B"][1]):
        raise ValueError("A/B frozen baseline key sets differ")
    return binding, books


def finite_controls(base_rows):
    expected = set(key(r) for r in base_rows)
    tests = []
    for name, raw, kind, expected_kind, value in [("numeric_zero", "0", "n", "binary", 0), ("numeric_one", "1.0", "n", "binary", 1), ("string_zero", "0", "str", "binary", 0), ("string_one", "1", "inlineStr", "binary", 1), ("blank", "", "n", "blank", None), ("pending", "待定", "str", "pending", None), ("illegal", "2", "n", "invalid", None)]:
        rows = copy.deepcopy(base_rows)
        rows[0]["cells"]["label"] = {"raw": raw, "type": kind, "formula": None}
        rows[0]["label"] = label_value(rows[0]["cells"]["label"])
        outcome = validate(rows, expected)
        passed = outcome["structural_ok"] and rows[0]["label"]["kind"] == expected_kind and rows[0]["label"]["value"] == value
        tests.append({"name": name, "pass": passed, "label_result": rows[0]["label"], "no_xlsx_written": True})
    rows = copy.deepcopy(base_rows)
    rows[5]["id"] = rows[0]["id"]
    rows[5]["cells"]["id"] = copy.deepcopy(rows[0]["cells"]["id"])
    outcome = validate(rows, expected)
    tests.append({"name": "duplicate_id_dimension", "pass": not outcome["structural_ok"] and any(x["kind"] == "duplicate_id_dimension" for x in outcome["structural_errors"]), "structural_errors": outcome["structural_errors"], "no_xlsx_written": True})
    if not all(x["pass"] for x in tests):
        raise AssertionError("Finite control failed")
    return {"mode": "standard_library_in_memory_rows_only", "passed": len(tests), "total": len(tests), "tests": tests}


def capture(a_path, b_path, out):
    binding, baseline = load_baseline()
    out = out.resolve()
    delivery = Path(binding["root"]) / "09-delivery"
    if out.is_relative_to(delivery) or out.is_relative_to(HERE / "baseline"):
        raise ValueError("Output cannot be inside delivery or frozen baseline")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Capture output must be a new empty directory; no overwrite")
    paths = {"A": a_path.resolve(), "B": b_path.resolve()}
    if paths["A"] == paths["B"]:
        raise ValueError("A and B must be distinct input files")
    data = {role: path.read_bytes() for role, path in paths.items()}
    if any(path.is_relative_to(out) for path in paths.values()):
        raise ValueError("Input cannot be inside new capture output")
    out.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": "review77-xlsx-intake-capture-1", "captured_at_utc": utc(), "capture_role": "read_only_file_structure_and_actual_differences", "coder_role": "AI_seeded_posthoc_review", "human_posthoc_review_report_received": True, "human_report_evidence_role": binding["human_report_evidence_role"], "original_workbooks_modified_by_reviewers": False, "original_workbooks_modified_by_reviewers_scope": "ROOT reception states this for the already-submitted review round; this file reader does not infer editor identity", "independent_human_first_coding": False, "full77_human_gold_certified": False, "all385_individual_human_checks_inferred": False, "do_not_request_same_whole_table_review_again": True, "workbook_saved_values_received": True, "user_report_unresolved": binding["user_report_unresolved"], "root_additional_source_disagreements": binding["root_additional_source_disagreements"], "baseline_binding": fingerprint(HERE / "baseline-binding.json", (HERE / "baseline-binding.json").read_bytes()), "original_manual_binding": binding["original_manual_binding"], "root_original_review_rows_binding": binding["root_original_review_rows_binding"], "root_delivery_receipt_binding": binding["root_receipt"], "root_human_report_reception_binding": binding["root_human_report_reception"], "workbooks": {}}
    for role in ("A", "B"):
        snapshot = out / (role + "-input-byte-snapshot.xlsx")
        with snapshot.open("xb") as stream:
            stream.write(data[role])
        info = {"input": fingerprint(paths[role], data[role]), "input_snapshot": fingerprint(snapshot, data[role]), "snapshot_role": "exact_bytes_copy_not_authored_xlsx", "matches_delivered_baseline_bytes": sha(data[role]) == binding["workbooks"][role]["sha256"]}
        try:
            current = read_workbook(data[role])
            rows = coding_rows(current)
            base_book, base_rows = baseline[role]
            info["structure"] = validate(rows, set(key(r) for r in base_rows))
            info["differences"] = compare_book(base_book, current, base_rows, rows)
            differences = info["differences"]
            info["content_outside_label_reason_changed"] = any(differences["field_changes_by_id_dimension"][f] for f in FIELDS.values() if f not in ("label", "reason")) or bool(differences["identifier_dimension_position_changes"] or differences["coding_header_changes"] or differences["original_context_cell_changes"] or differences["sheet_order_changed"])
            if not info["structure"]["structural_ok"]:
                info["status"] = "captured_structural_issues"
            elif info["content_outside_label_reason_changed"]:
                info["status"] = "captured_nonlabel_content_changes"
            elif any(info["structure"]["label_kind_counts"][k] for k in ("blank", "invalid", "pending")) or info["structure"]["blank_reason_rows"]:
                info["status"] = "captured_label_or_reason_issues"
            else:
                info["status"] = "captured_structure_compatible"
            info["context_sheet_nonempty_rows"] = sum(any(v["raw"] or v["formula"] is not None for v in cells.values()) for cells in current["sheets"]["原文语境"]["rows"].values())
        except (ValueError, KeyError, zipfile.BadZipFile, ET.ParseError, OSError) as exc:
            info["status"] = "captured_workbook_read_failed"
            info["read_error"] = {"type": type(exc).__name__, "message": str(exc)}
        try:
            info["source_bytes_unchanged_at_capture_end"] = sha(paths[role].read_bytes()) == sha(data[role])
        except OSError:
            info["source_bytes_unchanged_at_capture_end"] = None
        result["workbooks"][role] = info
    result["finite_controls"] = finite_controls(baseline["A"][1])
    result["labels_or_metrics_written"] = False
    result["formal_receiver_called"] = False
    write_json(out / "capture-proof.json", result)
    proof = (out / "capture-proof.json").read_bytes()
    write_json(out / "seal.json", {"schema_version": "byte-sha-seal-1", "created_at_utc": utc(), "scope": "read-only capture; no human gold certification", "files": [fingerprint(p, p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()]})
    return {"capture_proof": str(out / "capture-proof.json"), "capture_proof_sha256": sha(proof), "human_posthoc_review_report_received": True, "workbook_statuses": {r: x["status"] for r, x in result["workbooks"].items()}, "finite_controls_passed": result["finite_controls"]["passed"], "independent_human_first_coding": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, help="Saved A XLSX; read only")
    parser.add_argument("--b", type=Path, help="Saved B XLSX; read only")
    parser.add_argument("--out", type=Path, help="New empty capture directory; no overwrite")
    parser.add_argument("--self-test", action="store_true", help="Only run the eight in-memory finite controls; write nothing")
    args = parser.parse_args()
    try:
        if args.self_test:
            _, baseline = load_baseline()
            result = finite_controls(baseline["A"][1])
        else:
            if not all((args.a, args.b, args.out)):
                parser.error("--a, --b and --out are required")
            result = capture(args.a, args.b, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, ET.ParseError, AssertionError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
