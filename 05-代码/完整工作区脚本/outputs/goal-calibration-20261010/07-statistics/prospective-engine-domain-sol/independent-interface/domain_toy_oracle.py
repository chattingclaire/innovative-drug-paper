#!/usr/bin/env python3
"""Independent domain-interface contract toy; never imports the main engine.

All IDs/states are synthetic. Reads only the adjacent fixed fixture and writes
only its adjacent results. No population IDs, prediction files or source bodies.
"""
import copy
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

ALLOWED = {"remaining", "exposed"}
STATES = ("0", "1", "null", "execution_failure")


class InterfaceError(ValueError):
    pass


def prepare_contract(payload):
    design, records = payload["design"], payload["records"]
    strata = design.get("strata")
    if not isinstance(strata, list) or not strata or not records:
        raise InterfaceError("Nonempty design and assigned records required")
    has_tags = any("domain" in h for h in strata)
    if not has_tags and "domain_N" in design:
        raise InterfaceError("domain_N cannot bind strata with absent domain tags")
    index = {}
    for h in strata:
        hid = h.get("id")
        if not isinstance(hid, str) or not hid or hid in index:
            raise InterfaceError("Unique nonempty stratum id required")
        N, n = h.get("N"), h.get("n")
        if type(N) is not int or type(n) is not int or not 1 <= n <= N:
            raise InterfaceError("Positive fixed stratum capacity/sample required")
        if n == 1 and N > 1:
            raise InterfaceError("Noncensus singleton unsupported")
        if has_tags:
            if h.get("domain") not in ALLOWED:
                raise InterfaceError("Partial/null/illegal frozen design domain")
            if not isinstance(h.get("department"), str) or not h["department"]:
                raise InterfaceError("Explicit domain intersections require frozen department")
        index[hid] = h
    computed = Counter()
    if has_tags:
        for h in strata:
            computed[h["domain"]] += h["N"]
        if "domain_N" in design:
            supplied = design["domain_N"]
            if not isinstance(supplied, dict) or set(supplied) != set(computed):
                raise InterfaceError("Declared domain_N keys mismatch")
            if any(type(v) is not int or v <= 0 for v in supplied.values()):
                raise InterfaceError("domain_N requires positive strict integers")
            if supplied != dict(computed):
                raise InterfaceError("Declared domain_N totals mismatch")
    seen, observed, weights = set(), Counter(), []
    for row in records:
        rid, hid = row.get("id"), row.get("stratum_id")
        if not isinstance(rid, str) or not rid or rid in seen or hid not in index:
            raise InterfaceError("Invalid/duplicate assigned ID or stratum")
        seen.add(rid)
        observed[hid] += 1
        h = index[hid]
        department = row.get("department", "UNSPECIFIED")
        if not isinstance(department, str) or not department:
            raise InterfaceError("Invalid department")
        if has_tags and "department" not in row:
            raise InterfaceError("Explicit-domain row department absent")
        if h.get("department") is not None and h["department"] != department:
            raise InterfaceError("Row and frozen stratum department mismatch")
        if row["left"] not in STATES or row["right"] not in STATES:
            raise InterfaceError("Invalid synthetic state")
        weights.append(Fraction(h["N"], h["n"]))
    if any(observed[hid] != h["n"] for hid, h in index.items()):
        raise InterfaceError("All assigned rows, including failure, must remain")
    return {"explicit": has_tags, "index": index, "records": records, "weights": weights,
            "domain_N": dict(computed), "population_N": sum(h["N"] for h in strata)}


def point_metrics(cells):
    a, b, c, d = cells
    n = a + b + c + d
    div = lambda x, y: x / y if y else None
    po = div(a + d, n)
    pe = div((a + b) * (a + c) + (c + d) * (b + d), n * n)
    return {"kappa": None if pe is None else div(po - pe, 1 - pe),
            "Precision": div(a, a + b), "Recall": div(a, a + c),
            "F1": div(2 * a, 2 * a + b + c)}


def summaries(prepared):
    rows, index, weights = prepared["records"], prepared["index"], prepared["weights"]
    masks = {"ALL": [True] * len(rows)}
    departments = sorted({row.get("department", "UNSPECIFIED") for row in rows})
    for dep in departments:
        masks["department:" + dep] = [row.get("department", "UNSPECIFIED") == dep for row in rows]
    if prepared["explicit"]:
        for dom in sorted(prepared["domain_N"]):
            mask = [index[row["stratum_id"]]["domain"] == dom for row in rows]
            masks["domain:" + dom] = mask
            for dep in departments:
                intersection = [m and row["department"] == dep for m, row in zip(mask, rows)]
                if any(intersection):
                    masks["domain:" + dom + "|department:" + dep] = intersection
    output = {}
    categories = (("1", "1"), ("1", "0"), ("0", "1"), ("0", "0"))
    for label, mask in masks.items():
        members = {row["stratum_id"] for row, member in zip(rows, mask) if member}
        cells = [sum((w for row, w, member in zip(rows, weights, mask) if member and (row["left"], row["right"]) == cat), Fraction(0)) for cat in categories]
        comparable = [member and row["left"] in ("0", "1") and row["right"] in ("0", "1") for row, member in zip(rows, mask)]
        output[label] = {
            "assigned_n": sum(mask), "assigned_weight": sum((w for w, m in zip(weights, mask) if m), Fraction(0)),
            "pair_n": sum(comparable), "pair_weight": sum(cells, Fraction(0)),
            "weighted_four": cells, **point_metrics(cells),
            "census": bool(members) and all(index[h]["N"] == index[h]["n"] for h in members),
            "semantic_null_pair_units": sum(member and "null" in (row["left"], row["right"]) and "execution_failure" not in (row["left"], row["right"]) for row, member in zip(rows, mask)),
            "any_failure_pair_units": sum(member and "execution_failure" in (row["left"], row["right"]) for row, member in zip(rows, mask)),
        }
    if prepared["explicit"]:
        assert output["ALL"]["assigned_weight"] == sum(prepared["domain_N"].values())
        assert sum(output["domain:" + d]["assigned_weight"] for d in prepared["domain_N"]) == output["ALL"]["assigned_weight"]
        for c in range(4):
            assert sum(output["domain:" + d]["weighted_four"][c] for d in prepared["domain_N"]) == output["ALL"]["weighted_four"][c]
    return output


def mutated(base, mutation):
    value = copy.deepcopy(base)
    design, rows = value["design"], value["records"]
    h = design["strata"]
    if mutation == "none": pass
    elif mutation == "omit_domain_N": design.pop("domain_N")
    elif mutation in ("only_remaining", "extra_empty_domain"):
        design["strata"] = h[:2]
        value["records"] = rows[:4]
        design["domain_N"] = {"remaining": 6}
        if mutation == "extra_empty_domain": design["domain_N"]["exposed"] = 0
    elif mutation in ("legacy", "domain_N_without_tags"):
        for item in h: item.pop("domain")
        if mutation == "legacy": design.pop("domain_N")
    elif mutation == "omit_one_domain": h[1].pop("domain")
    elif mutation == "all_null_domain":
        for item in h: item["domain"] = None
    elif mutation == "empty_domain": h[0]["domain"] = ""
    elif mutation == "illegal_domain": h[0]["domain"] = "developed"
    elif mutation == "wrong_domain_N": design["domain_N"]["exposed"] = 7
    elif mutation == "float_domain_N": design["domain_N"]["remaining"] = 6.0
    elif mutation == "bool_domain_N": design["domain_N"]["remaining"] = True
    elif mutation == "omit_stratum_department": h[0].pop("department")
    elif mutation == "list_department": h[0]["department"] = ["Alpha", "Beta"]
    elif mutation == "wrong_row_department": rows[0]["department"] = "Beta"
    elif mutation == "omit_row_department": rows[0].pop("department")
    elif mutation == "empty_strata": design["strata"] = []
    elif mutation == "zero_n": h[0]["n"] = 0
    elif mutation == "omit_failure_row": value["records"] = rows[:-1]
    elif mutation == "duplicate_id": rows[1]["id"] = rows[0]["id"]
    else: raise AssertionError("Unrecognized fixture mutation")
    return value


def simple(value):
    if isinstance(value, Fraction): return str(value)
    if isinstance(value, dict): return {k: simple(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [simple(v) for v in value]
    return value


def run(fixture):
    checks = []
    for case in fixture["validation_cases"]:
        try:
            prepared = prepare_contract(mutated(fixture["base"], case["mutation"]))
            accepted, error = True, None
        except InterfaceError as e:
            accepted, error = False, str(e)
        assert accepted == case["accepted"], (case["id"], accepted)
        if accepted:
            summary = summaries(prepared)
            if case["mutation"] == "legacy": assert all(not k.startswith("domain:") for k in summary)
            if case["mutation"] == "only_remaining": assert "domain:exposed" not in summary
        checks.append({"id": case["id"], "accepted": accepted, "expected": case["accepted"], "error": error, "pass": True})
    actual = summaries(prepare_contract(fixture["base"]))
    for label, expected in fixture["expected_base"].items():
        for key, value in expected.items():
            assert simple(actual[label][key]) == value, (label, key, simple(actual[label][key]), value)
    assert actual["ALL"]["pair_weight"] == 11 < actual["ALL"]["assigned_weight"] == 14
    assert actual["ALL"]["semantic_null_pair_units"] == 1 and actual["ALL"]["any_failure_pair_units"] == 2
    avg_kappa = (actual["domain:remaining"]["kappa"] + actual["domain:exposed"]["kappa"]) / 2
    assert avg_kappa != actual["ALL"]["kappa"]
    numeric_case = fixture["independent_numeric_flag_case"]
    left = [Fraction(v) for v in numeric_case["remaining_four"]]
    right = [Fraction(v) for v in numeric_case["exposed_four"]]
    total = [x + y for x, y in zip(left, right)]
    assert total == numeric_case["expected_full_four"]
    def passing(cells):
        return all(value is not None and value >= Fraction(4, 5) for value in point_metrics(cells).values())
    flags = {"full_point_targets_met": passing(total), "remaining_point_targets_met": passing(left),
             "exposed_point_targets_met": passing(right), "formal_acceptance": False}
    assert flags == numeric_case["expected"]
    return {"status": "passed_independent_synthetic_interface_contract_checks",
            "metadata_validation_cases": checks, "weighted_mask_summaries": actual,
            "nonaverage_numeric_flag_case": {"flags": flags, "full_metrics": point_metrics(total),
                "remaining_metrics": point_metrics(left), "exposed_metrics": point_metrics(right)},
            "real_ID_draws": 0, "real_predictions_read": 0, "source_bodies_read": 0,
            "main_engine_executed": False, "formal_acceptance": False}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "domain-toy-cases.json").read_text())
    results = run(fixture)
    path = root / "domain-toy-results.json"
    path.write_text(json.dumps(simple(results), ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": results["status"], "metadata_validation_cases": len(results["metadata_validation_cases"]), "nonempty_mask_count": len(results["weighted_mask_summaries"]), "output": str(path)}, ensure_ascii=False))
