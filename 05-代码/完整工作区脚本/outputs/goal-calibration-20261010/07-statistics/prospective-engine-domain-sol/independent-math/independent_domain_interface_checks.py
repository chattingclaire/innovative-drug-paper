#!/usr/bin/env python3
"""Synthetic-only interface checks against old/new source files.

Imports the two engines solely for small artificial payloads; never reads any
project labels, predictions, corpus, assigned IDs, or analysis result files.
Mathematical expected values come from this directory's independent helpers.
"""
import copy
import hashlib
import importlib.util
from itertools import product
from collections import Counter
import json
import math
from pathlib import Path
import numpy as np

import independent_domain_mask_checks as independent

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT.parent / "prospective-engine-sol/metrics_engine.py"
NEW = ROOT / "metrics_engine.py"
OUTDIR = ROOT / "independent-math"
DIMS = ("S", "E", "Ec", "I", "F")
METHODS = ("A", "B", "reference", "rule", "LLM")
CHECKS = []


def check(name, passed, detail=None):
    CHECKS.append({"name": name, "passed": bool(passed), "detail": detail})
    if not passed:
        raise AssertionError(name)


def load_engine(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def toy_strata():
    return {
        "R_A": {"domain": "remaining", "department": "A", "N": 4, "n": 2, "categories": [0, 1, 2, 3]},
        "R_B": {"domain": "remaining", "department": "B", "N": 3, "n": 2, "categories": [0, 3, 3]},
        "E_A": {"domain": "exposed", "department": "A", "N": 3, "n": 3, "categories": [0, 0, 3]},
        "E_B": {"domain": "exposed", "department": "B", "N": 4, "n": 2, "categories": [0, 1, 3, 3]},
        "E_C": {"domain": "exposed", "department": "C", "N": 1, "n": 1, "categories": [3]},
    }


def payload(strata=None, named=True):
    strata = toy_strata() if strata is None else strata
    declarations, records = [], []
    for hid, h in strata.items():
        declarations.append({"id": hid, **{k: v for k, v in h.items() if k in ("N", "n", "department", "domain") and (named or k != "domain")}})
        for i in range(h["n"]):
            category = h["categories"][i]
            pred, ref = int(category in (0, 1)), int(category in (0, 2))
            labels = {}
            for method in METHODS:
                labels[method] = {}
                for j, dim in enumerate(DIMS):
                    p = pred if dim == "S" else int((i + len(hid) + j) % 3 < 2)
                    r = ref if dim == "S" else int((2 * i + len(hid) + j) % 4 < 2)
                    labels[method][dim] = r if method in ("A", "B", "reference") else p if method == "rule" else p if dim != "E" else 1 - p
            records.append({"unit_id": f"ARTIFICIAL_{hid}_{i}", "stratum_id": hid, "department": h["department"],
                            "outputs": {m: {"status": "completed", "labels": values} for m, values in labels.items()}})
    design = {"kind": "stratified_srswor", "sampling_unit": "source_unit", "strata": declarations}
    if named:
        design["domain_partition"] = "remaining_exposed"
        design["domain_population_N"] = {d: sum(h["N"] for h in strata.values() if h["domain"] == d) for d in ("remaining", "exposed")}
    return {"data_role": "synthetic", "metadata": {"analysis_stage": "combined", "design": design,
            "scope": {"kind": "ARTIFICIAL_TOY_ONLY", "population_N": sum(h["N"] for h in strata.values())}}, "records": records}


def enumerated_W(strata):
    choices = []
    for h in strata.values():
        N, n = h["N"], h["n"]
        if N == n:
            choices.append([(1.0,) * n])
        else:
            rows = []
            for draws in product(range(n), repeat=n - 1):
                count = Counter(draws)
                rows.append(tuple(1 + math.sqrt(1 - n / N) * (n * count[i] / (n - 1) - 1) for i in range(n)))
            choices.append(rows)
    return np.asarray([[h["N"] / h["n"] * factor[i] for h, factor in zip(strata.values(), joint) for i in range(h["n"])]
                       for joint in product(*choices)])


def invoke_common_W(engine, toy, W, guard_mode="none"):
    original = engine.rao_wu_weights
    calls = []
    def supplied(prepared, replicates=5000, seed=20261010):
        calls.append((replicates, seed, len(prepared["records"])))
        assert W.shape == (replicates, len(prepared["records"]))
        return W.copy()
    engine.rao_wu_weights = supplied
    try:
        result = engine.analyze(toy, replicates=len(W), seed=20261010, guard_mode=guard_mode)
    finally:
        engine.rao_wu_weights = original
    return result, calls


def rejects(engine, label, bad):
    try:
        engine.prepare(bad)
    except engine.DataError:
        check(label, True)
    else:
        check(label, False)


def main():
    old, new = load_engine("old_synthetic_interface", OLD), load_engine("new_synthetic_domain_interface", NEW)
    declarations = toy_strata()
    toy = payload()
    prep = new.prepare(toy)
    scopes = new.analysis_scopes(prep)
    W = enumerated_W(declarations)
    result, calls = invoke_common_W(new, toy, W)
    expected_keys = {"ALL", "domain:remaining", "domain:exposed", "department:A", "department:B", "department:C",
                     "domain:remaining|department:A", "domain:remaining|department:B",
                     "domain:exposed|department:A", "domain:exposed|department:B", "domain:exposed|department:C"}
    check("all 11 present views; empty domain-department view excluded", set(scopes) == expected_keys == set(result["analysis_scopes"]))
    check("one complete source-unit W requested exactly once", calls == [(8, 20261010, 10)] and result["design"]["replicate_weight_generation_count"] == 1)
    digest = hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest()
    check("all views explicitly share the one W SHA", result["design"]["shared_replicate_weights_sha256"] == digest and all(v["shared_replicate_weights_sha256"] == digest for v in result["analysis_scopes"].values()))
    check("scope masks all keep full source n=10", all(v["mask"].shape == (10,) and v["mask"].dtype == bool for v in scopes.values()))
    expected_flags = {"ALL": False, "domain:remaining": False, "domain:exposed": False, "department:A": False, "department:B": False,
                      "department:C": True, "domain:remaining|department:A": False, "domain:remaining|department:B": False,
                      "domain:exposed|department:A": True, "domain:exposed|department:B": False, "domain:exposed|department:C": True}
    check("all fixed-layer view census flags correct", all(v["full_census"] is expected_flags[k] and new.domain_is_census(prep, k) is expected_flags[k] for k, v in scopes.items()))
    for key, view in scopes.items():
        mask = view["mask"]
        expected_N = sum(declarations[hid]["N"] for hid in view["stratum_ids"])
        info = result["analysis_scopes"][key]
        check(key + ": weight and replicate totals equal frozen view N",
              info["population_N"] == expected_N and info["population_membership_frozen"] is True
              and math.isclose(info["weighted_assigned_total"], expected_N)
              and np.allclose(W @ mask.astype(float), expected_N, atol=1e-12, rtol=1e-12)
              and np.allclose(info["replicate_assigned_total_range"], [expected_N, expected_N]))
        for dim in DIMS:
            j = DIMS.index(dim)
            pair = prep["states"]["rule"][:, j] * 4 + prep["states"]["reference"][:, j]
            X = [[independent.F(int(pair[i] == cat and mask[i])) for cat in (5, 4, 1, 0)] for i in range(10)]
            sample_vectors = {hid: [X[i] for i, h in enumerate(prep["stratum_ids"]) if h == hid] for hid in declarations}
            expected_V = independent.masked_covariance(declarations, sample_vectors, sampled=True)
            actual_V = new.analytic_covariance(prep, X)
            check(key + " " + dim + ": source-design covariance keeps masked zero rows",
                  np.allclose(actual_V, np.asarray(expected_V, dtype=float), atol=1e-12, rtol=1e-12))
    masks = {k: v["mask"].astype(float) for k, v in scopes.items()}
    check("full mask/domain partition exact", np.array_equal(masks["ALL"], masks["domain:remaining"] + masks["domain:exposed"]))
    Vpart = new.analytic_covariance(prep, np.stack([masks["domain:remaining"], masks["domain:exposed"]], axis=1))
    check("fixed population counts for domains have covariance zero", np.array_equal(Vpart, np.zeros((2, 2))))
    comp = result["comparisons"]["rule_vs_reference"]["domains"]
    for dim in DIMS:
        cells = {k: [independent.F(x) for x in comp[k][dim]["weighted_four_exact_fractions"]] for k in ("ALL", "domain:remaining", "domain:exposed")}
        check(dim + ": ALL weighted cells exactly add domain cells", cells["ALL"] == [cells["domain:remaining"][i] + cells["domain:exposed"][i] for i in range(4)])
    census_kappa = result["comparisons"]["A_vs_B"]["domains"]["domain:exposed|department:A"]["S"]["intervals"]["kappa"]
    check("census cross-view defined kappa has [1,1] interval", census_kappa["CI95"] == [1.0, 1.0])
    undefined_census = result["comparisons"]["A_vs_B"]["domains"]["department:C"]["S"]
    check("singleton census does not create an undefined kappa",
          undefined_census["design_weighted_metrics"]["kappa"] is None
          and undefined_census["intervals"]["kappa"]["CI95"] is None
          and undefined_census["intervals"]["kappa"]["status"] == "undefined_point_denominator")
    noncensus_kappa = result["comparisons"]["A_vs_B"]["domains"]["domain:remaining|department:A"]["S"]["intervals"]["kappa"]
    check("noncensus identical sample kappa does not claim [1,1] adequate CI", noncensus_kappa["CI95"] is None and "degenerate_non_census" in noncensus_kappa["status"])
    check("synthetic per-scope numerical flags do not assert formal acceptance", result["project_review"]["formal_acceptance"] is False and all(v["formal_acceptance"] is False for v in result["numeric_targets_by_analysis_scope"].values()))
    guarded, guard_calls = invoke_common_W(new, toy, W, guard_mode="joint_table")
    check("view guards do not regenerate or subset bootstrap W", guard_calls == calls and guarded["design"]["shared_replicate_weights_sha256"] == digest)
    for key, view in scopes.items():
        guard = guarded["comparisons"]["rule_vs_reference"]["domains"][key]["S"]["finite_guard"]
        check(key + ": guard uses only that frozen full-layer count universe",
              {r["stratum"] for r in guard["strata"]} == set(view["stratum_ids"])
              and sum(r["N"] for r in guard["strata"]) == view["population_N"]
              and math.isclose(guard["alpha_per_count"], .05 / (len(view["stratum_ids"]) * 16))
              and guard["metric_projection_implemented"] is False)
    unknown = copy.deepcopy(toy)
    unknown["records"][0]["outputs"]["reference"]["labels"]["E"] = None
    unknown["records"][8]["outputs"]["LLM"] = {"status": "execution_failure", "labels": {}}
    unknown["records"][1]["outputs"]["A"]["labels"]["I"] = None
    unknown["records"][1]["outputs"]["A"]["dimension_status"] = {"I": "execution_failure"}
    del unknown["records"][9]["outputs"]["rule"]
    unknown_prep = new.prepare(unknown)
    unknown_result, unknown_calls = invoke_common_W(new, unknown, W)
    check("unknown/failure ledger still uses identical complete-unit W", unknown_calls == calls and unknown_result["design"]["shared_replicate_weights_sha256"] == digest)
    for key, view in scopes.items():
        mask = view["mask"]
        den = float(unknown_prep["weights"][mask].sum())
        for method in METHODS:
            att = unknown_result["attention"][method][key]
            expected = {}
            for j, dim in enumerate(DIMS):
                states = unknown_prep["states"][method][:, j]
                expected[dim] = tuple(float(unknown_prep["weights"] @ ((states == code) & mask)) for code in (1, 2, 3))
            check(key + " " + method + ": unknown/failure totals retain assigned weight denominator",
                  all(math.isclose(att[d]["design_weighted"]["assigned_weight_total"], den)
                      and math.isclose(att[d]["design_weighted"]["known_positive"], expected[d][0])
                      and math.isclose(att[d]["design_weighted"]["semantic_null"], expected[d][1])
                      and math.isclose(att[d]["design_weighted"]["execution_failure"], expected[d][2])
                      and math.isclose(att[d]["design_weighted"]["unresolved_total"], expected[d][1] + expected[d][2]) for d in DIMS))
        check(key + ": full16-state weighted tables retain all assigned mass",
              all(math.isclose(sum(sum(row) for row in unknown_result["comparisons"][comparison]["domains"][key][dim]["design_weighted"]["full4x4_including_failure"]), den)
                  for comparison in new.COMPARISONS for dim in DIMS))
    legacy = payload(named=False)
    old_prep, new_prep = old.prepare(legacy), new.prepare(legacy)
    check("legacy no-domain prepared weights exactly unchanged", np.array_equal(old_prep["weights"], new_prep["weights"]) and new_prep["named_domains"] is False)
    old_result, old_calls = invoke_common_W(old, legacy, W, "single_category")
    legacy_result, legacy_calls = invoke_common_W(new, legacy, W, "single_category")
    check("legacy views remain only ALL and departments", set(legacy_result["analysis_scopes"]) == {"ALL", "department:A", "department:B", "department:C"})
    check("legacy same whole-ledger resampling contract", old_calls == legacy_calls == calls)
    equal = True
    for comparison, obj in old_result["comparisons"].items():
        for scope, dimensions in obj["domains"].items():
            for dim, item in dimensions.items():
                new_item = legacy_result["comparisons"][comparison]["domains"][scope][dim]
                equal &= all(new_item[k] == v for k, v in item.items())
    check("legacy existing comparison outputs unchanged; additions only", equal)
    check("legacy attention/contrast/numeric/project outputs unchanged",
          all(old_result[k] == legacy_result[k] for k in ("attention", "department_attention_difference_bounds", "numeric_targets", "project_review")))
    mixed = {"mixed": {"N": 4, "n": 2, "department": "A", "categories": [0, 3, 0, 3]}}
    mixed_payload = payload(mixed, named=False)
    del mixed_payload["metadata"]["design"]["strata"][0]["department"]
    mixed_payload["records"][1]["department"] = "B"
    mixed_prep = new.prepare(mixed_payload)
    mixed_scopes = new.analysis_scopes(mixed_prep)
    mixed_X = np.stack([mixed_scopes["department:A"]["mask"], mixed_scopes["department:B"]["mask"]], axis=1).astype(float)
    mixed_V = new.analytic_covariance(mixed_prep, mixed_X)
    check("legacy mixed-stratum departments retain nonzero cross covariance", np.allclose(mixed_V, [[2, -2], [-2, 2]]) and all(mixed_scopes[k]["stratum_ids"] is None and mixed_scopes[k]["population_N"] is None and mixed_scopes[k]["full_census"] is False for k in ("department:A", "department:B")))
    check("legacy ALL variance includes cross terms, not department variance sum", np.allclose(new.analytic_covariance(mixed_prep, np.ones(2)), [[0]]) and mixed_V[0, 0] + mixed_V[1, 1] + 2 * mixed_V[0, 1] == 0)
    global_census = toy_strata()
    for h in global_census.values():
        h["n"] = h["N"]
    census_payload = payload(global_census, named=False)
    for h in census_payload["metadata"]["design"]["strata"]:
        del h["department"]
    census_prep = new.prepare(census_payload)
    census_scopes = new.analysis_scopes(census_prep)
    check("global census preserves legacy observed-department census exception", all(v["full_census"] for v in census_scopes.values()) and all(v["population_N"] == int(v["mask"].sum()) for k, v in census_scopes.items() if k != "ALL"))
    nonprob = copy.deepcopy(toy)
    nonprob["metadata"]["design"]["kind"] = "nonprobability"
    nonprob_result = new.analyze(nonprob, replicates=8, guard_mode="none")
    check("nonprobability named views gain no population CIs/census/W", nonprob_result["design"]["replicate_weight_generation_count"] == 0 and nonprob_result["design"]["shared_replicate_weights_sha256"] is None and all(v["full_census_no_sampling_error"] is False and v["replicate_assigned_total_range"] is None for v in nonprob_result["analysis_scopes"].values()))
    for label, change in (
        ("partial frozen domain declarations rejected", lambda p: p["metadata"]["design"]["strata"][0].pop("domain")),
        ("named domain missing frozen department rejected", lambda p: p["metadata"]["design"]["strata"][0].pop("department")),
        ("wrong frozen domain total rejected", lambda p: p["metadata"]["design"]["domain_population_N"].update(remaining=8)),
        ("domain-specific label bindings rejected", lambda p: p["metadata"].update(domain_input_seals={})),
        ("root-level domain-specific label bindings rejected", lambda p: p.update(domain_input_seals={})),
        ("named rows require explicit department even if legacy default would match", lambda p: (
            p["records"][0].pop("department"),
            p["metadata"]["design"]["strata"][0].update(department="UNSPECIFIED"),
            p["records"][1].update(department="UNSPECIFIED"))),
        ("per-record domain overrides rejected", lambda p: p["records"][0].update(domain="exposed")),
        ("department mismatch with frozen stratum rejected", lambda p: p["records"][0].update(department="B")),
        ("noncensus singleton source stratum rejected", lambda p: p["metadata"]["design"]["strata"][0].update(n=1)),
    ):
        bad = copy.deepcopy(toy)
        change(bad)
        rejects(new, label, bad)
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (OLD, NEW, Path(__file__), Path(independent.__file__))}
    output = {"status": "PASS_SYNTHETIC_DOMAIN_INTERFACE_REVIEW", "date": "2026-10-10",
              "project_labels_predictions_body_IDs_or_results_read": False, "only_artificial_engine_execution": True,
              "legacy_core_behavior_unchanged": True, "input_bindings_sha256": bindings,
              "toy_population_N": 15, "toy_assigned_n": 10, "exhaustive_conditional_W_rows": 8,
              "all_view_count": len(scopes), "mixed_stratum_covariance": mixed_V.tolist(),
              "check_count": len(CHECKS), "all_passed": all(c["passed"] for c in CHECKS), "checks": CHECKS}
    target = OUTDIR / "independent_domain_interface_results.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "checks": len(CHECKS), "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
