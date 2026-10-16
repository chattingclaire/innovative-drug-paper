"""Minimal structural and literal-evidence validator for CAL-5D binary output.

This program does not assign labels and does not inspect keywords to infer a
dimension.  It can verify JSON shape, input ID order, binary label types,
required evidence presence, literal quotation, subtype consistency, and the
safety-quality flag contract.

It cannot prove that an LLM read the full sentence or contexts; that a label is
semantically correct; that a reason is specific rather than templated; that an
excerpt is the best or shortest evidence; that background was not propagated;
or that the supplied input is materially complete.  Those remain review and
provenance questions.
"""

import json
import sys
from pathlib import Path


DIMS = ["S", "E", "Ec", "I", "F"]
F_SUBTYPES = {"access", "affordability", "clinical_management", "dimension_information"}
I_SUBTYPES = {"attribute", "research_support", "qualification_advantage"}
S_BASES = {"quality_only", "quality_and_other", "no_quality_basis"}
ISSUE_STATUSES = {"resolved_text_issue", "resolved_context_issue", "boundary_note"}


def iter_context_text(value):
    """Yield only human-readable context fields; metadata hashes are excluded."""
    if isinstance(value, list):
        for item in value:
            yield from iter_context_text(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in {"text", "headers", "row_cells", "caption", "definition", "title", "note"}:
                if isinstance(item, str):
                    yield item
                else:
                    yield from iter_context_text(item)
            elif isinstance(item, (dict, list)):
                yield from iter_context_text(item)


def exact_keys(value, expected, location, errors):
    if not isinstance(value, dict):
        errors.append(f"{location}:not_object")
        return False
    if set(value) != set(expected):
        errors.append(f"{location}:fields")
        return False
    return True


def validate(packet, output):
    errors = []
    inputs = packet.get("rows")
    if not isinstance(inputs, list):
        return ["input:rows_not_array"]

    top = ["protocol_version", "execution_version", "release_stage", "rows", "issue_records"]
    if not exact_keys(output, top, "root", errors):
        return errors
    if output["protocol_version"] != "CAL-5D-20260926-v1.3":
        errors.append("root:protocol_version")
    if output["execution_version"] != "LLM-binary-v30":
        errors.append("root:execution_version")
    if output["release_stage"] != "final_binary_labels":
        errors.append("root:release_stage")

    rows = output["rows"]
    if not isinstance(rows, list):
        return errors + ["root.rows:not_array"]
    input_ids = [row.get("id") if isinstance(row, dict) else None for row in inputs]
    output_ids = [row.get("id") if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(value, str) or not value for value in input_ids):
        errors.append("input.rows:id_not_nonempty_string")
    if any(not isinstance(value, str) or not value for value in output_ids):
        errors.append("root.rows:id_not_nonempty_string")
    if all(isinstance(value, str) for value in input_ids) and len(input_ids) != len(set(input_ids)):
        errors.append("input.rows:duplicate_id")
    if all(isinstance(value, str) for value in output_ids) and len(output_ids) != len(set(output_ids)):
        errors.append("root.rows:duplicate_id")
    if output_ids != input_ids:
        errors.append("root.rows:id_count_order_or_duplicate")

    expected_row = [
        "id", "labels", "dimension_reasons", "evidence", "fairness_subtypes",
        "innovation_subtypes", "safety_quality_basis"
    ]
    for index, (inp, row) in enumerate(zip(inputs, rows)):
        loc = f"rows[{index}]"
        if not exact_keys(row, expected_row, loc, errors):
            continue
        rid = row["id"]
        labels = row["labels"]
        reasons = row["dimension_reasons"]
        if exact_keys(labels, DIMS, f"{loc}.labels", errors):
            for dim in DIMS:
                value = labels[dim]
                if type(value) is not int or value not in (0, 1):
                    errors.append(f"{rid}:{dim}:not_binary_integer")
        else:
            continue
        if exact_keys(reasons, DIMS, f"{loc}.dimension_reasons", errors):
            for dim in DIMS:
                if not isinstance(reasons[dim], str) or not reasons[dim].strip():
                    errors.append(f"{rid}:{dim}:empty_reason")

        evidence = row["evidence"]
        if not isinstance(evidence, list):
            errors.append(f"{rid}:evidence_not_array")
            evidence = []
        valid_evidence = []
        for eidx, item in enumerate(evidence):
            eloc = f"{loc}.evidence[{eidx}]"
            if not exact_keys(item, ["dimension", "source", "quote"], eloc, errors):
                continue
            dim, source, quote = item["dimension"], item["source"], item["quote"]
            if dim not in DIMS:
                errors.append(f"{rid}:evidence:{eidx}:dimension")
                continue
            if source not in {"unit", "context"}:
                errors.append(f"{rid}:{dim}:evidence:{eidx}:source")
                continue
            if not isinstance(quote, str) or not quote:
                errors.append(f"{rid}:{dim}:evidence:{eidx}:empty_quote")
                continue
            haystacks = [inp.get("text", "")] if source == "unit" else list(iter_context_text(inp.get("contexts", {})))
            if not any(quote in text for text in haystacks if isinstance(text, str)):
                errors.append(f"{rid}:{dim}:evidence:{eidx}:nonliteral_quote")
                continue
            valid_evidence.append(item)

        for dim in DIMS:
            if labels[dim] == 1 and not any(e["dimension"] == dim and e["source"] == "unit" for e in valid_evidence):
                errors.append(f"{rid}:{dim}:missing_literal_unit_evidence")
            if labels[dim] == 0 and any(e["dimension"] == dim for e in valid_evidence):
                errors.append(f"{rid}:{dim}:evidence_for_zero_label")

        fsub = row["fairness_subtypes"]
        isub = row["innovation_subtypes"]
        if not isinstance(fsub, list):
            errors.append(f"{rid}:fairness_subtypes")
        elif any(not isinstance(value, str) or value not in F_SUBTYPES for value in fsub):
            errors.append(f"{rid}:fairness_subtypes")
        else:
            if len(fsub) != len(set(fsub)):
                errors.append(f"{rid}:fairness_subtypes_duplicate")
            if bool(fsub) != (labels["F"] == 1):
                errors.append(f"{rid}:fairness_subtypes_label_conflict")
        if not isinstance(isub, list):
            errors.append(f"{rid}:innovation_subtypes")
        elif any(not isinstance(value, str) or value not in I_SUBTYPES for value in isub):
            errors.append(f"{rid}:innovation_subtypes")
        else:
            if len(isub) != len(set(isub)):
                errors.append(f"{rid}:innovation_subtypes_duplicate")
            if bool(isub) != (labels["I"] == 1):
                errors.append(f"{rid}:innovation_subtypes_label_conflict")

        sbasis = row["safety_quality_basis"]
        if sbasis not in S_BASES:
            errors.append(f"{rid}:safety_quality_basis")
        elif labels["S"] == 0 and sbasis != "no_quality_basis":
            errors.append(f"{rid}:S_zero_basis_conflict")

    issues = output["issue_records"]
    if not isinstance(issues, list):
        errors.append("root.issue_records:not_array")
    else:
        seen = set()
        valid_ids = {value for value in input_ids if isinstance(value, str)}
        for index, issue in enumerate(issues):
            loc = f"issue_records[{index}]"
            if not exact_keys(issue, ["id", "status", "description"], loc, errors):
                continue
            iid = issue["id"]
            if not isinstance(iid, str) or not iid:
                errors.append(f"{loc}:id_not_nonempty_string")
                continue
            if iid not in valid_ids:
                errors.append(f"{loc}:unknown_id")
            if iid in seen:
                errors.append(f"{loc}:duplicate_id")
            seen.add(iid)
            if issue["status"] not in ISSUE_STATUSES:
                errors.append(f"{loc}:status")
            if not isinstance(issue["description"], str) or not issue["description"].strip():
                errors.append(f"{loc}:empty_description")

    return errors


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: validate_binary_output.py INPUT.json OUTPUT.json")
    packet_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    output = json.loads(output_path.read_text(encoding="utf-8"))
    errors = validate(packet, output)
    print(json.dumps({"n": len(packet.get("rows", [])), "errors": errors, "valid": not errors}, ensure_ascii=False))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
