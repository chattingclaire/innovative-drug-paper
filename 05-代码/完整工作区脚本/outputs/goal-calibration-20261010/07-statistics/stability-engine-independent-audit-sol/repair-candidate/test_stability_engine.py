#!/usr/bin/env python3
"""Finite meaningful controls: independent hand arithmetic plus contract counterexamples."""
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from constructed_controls import make_fixture, json_bytes
from stability_engine import (analyze_registry, save_analysis, ContractError, digest, object_sha,
                              table_metrics, request_bytes, DIMS)


class StabilityControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".control-test-", dir=Path(__file__).resolve().parent)
        self.base = Path(self.temp.name)
        self.registry, self.ledger = make_fixture(self.base / "input")

    def tearDown(self):
        self.temp.cleanup()

    def report(self):
        return analyze_registry(self.registry, self.ledger)[0]

    def change(self, registry=None, ledger=None):
        reg = json.loads(self.registry.read_text())
        led = json.loads(self.ledger.read_text())
        if registry:
            registry(reg)
            reg.pop("registry_content_sha256")
            reg["registry_content_sha256"] = object_sha(reg)
            data = json_bytes(reg)
            self.registry.write_bytes(data)
            led["registry_file_sha256"] = digest(data)
        if ledger:
            ledger(led)
        self.ledger.write_bytes(json_bytes(led))

    def rejected(self, substring):
        with self.assertRaisesRegex(ContractError, substring):
            analyze_registry(self.registry, self.ledger)

    def test_hand_pair_cells_margins_po_pe_kappa(self):
        # S: n00=3,n01=0,n10=1,n11=2; N=6, Po=5/6,Pe=1/2,k=2/3.
        s = self.report()["paired_comparisons"]["R1/R2"]["dimensions"]["S"]
        self.assertEqual(s["raw"]["cells"], {"n00": 3, "n01": 0, "n10": 1, "n11": 2})
        self.assertEqual(s["raw"]["marginals"], {"first_0": 3, "first_1": 3, "second_0": 4, "second_1": 2})
        self.assertAlmostEqual(s["raw"]["Po"], 5/6)
        self.assertEqual(s["raw"]["Pe"], 1/2)
        self.assertAlmostEqual(s["raw"]["kappa"], 2/3)
        self.assertEqual(s["raw"]["positive_counts"]["change_second_minus_first"], -1)
        self.assertEqual(s["label_changes"][0]["assignedID"], "TOY-004")
        # Fixed weights 1,2,3,4,5,8: weighted cells 12,0,4,7; N=23;
        # Pe=269/529, Po=19/23 and kappa=168/260=42/65.
        self.assertEqual(s["weighted"]["cells"], {"n00": 12, "n01": 0, "n10": 4, "n11": 7})
        self.assertEqual(s["weighted"]["denominator"], 23)
        self.assertAlmostEqual(s["weighted"]["Pe"], 269/529)
        self.assertAlmostEqual(s["weighted"]["kappa"], 42/65)
        self.assertEqual(s["weighted"]["positive_counts"]["change_second_minus_first"], -4)
        # I: n00=3,n01=1,n10=0,n11=1; Po=4/5,Pe=14/25,k=6/11.
        i = self.report()["paired_comparisons"]["R1/R2"]["dimensions"]["I"]["raw"]
        self.assertEqual(i["cells"], {"n00": 3, "n01": 1, "n10": 0, "n11": 1})
        self.assertAlmostEqual(i["kappa"], 6/11)

    def test_all_zero_and_no_joint_observation_kappa_are_na(self):
        reg, led = make_fixture(self.base / "zero", "all_zero")
        report = analyze_registry(reg, led)[0]
        raw = report["paired_comparisons"]["R1/R2"]["dimensions"]["S"]["raw"]
        self.assertEqual(raw["Po"], 1)
        self.assertEqual(raw["Pe"], 1)
        self.assertIsNone(raw["kappa"])
        self.assertEqual(raw["kappa_na_reason"], "Pe_equals_one_degenerate_marginals")
        empty = table_metrics({"n00": 0, "n01": 0, "n10": 0, "n11": 0})
        self.assertIsNone(empty["Po"])
        self.assertIsNone(empty["kappa"])
        self.assertEqual(empty["kappa_na_reason"], "no_joint_binary_records")
        q = report["three_main_runs"]["q"]
        self.assertEqual(q["by_run"]["R1"]["unweighted_sum5T"], 0)
        self.assertIsNone(q["q_ranges"]["unweighted_q"]["S"]["min"])

    def test_rare_agreement_and_one_positive_change_counterexample(self):
        reg, led = make_fixture(self.base / "rare", "rare")
        f = analyze_registry(reg, led)[0]["paired_comparisons"]["R1/R2"]["dimensions"]["F"]["raw"]
        self.assertEqual(f["cells"], {"n00": 7, "n01": 0, "n10": 0, "n11": 1})
        self.assertEqual(f["Pe"], 25/32)
        self.assertEqual(f["kappa"], 1)
        # One marginal is all zero: Po=7/8, Pe=7/8, kappa=0, never 1.
        changed = table_metrics({"n00": 7, "n01": 1, "n10": 0, "n11": 0})
        self.assertEqual(changed["Po"], 7/8)
        self.assertEqual(changed["kappa"], 0)

    def test_null_failure_not_called_and_overlap_are_distinct(self):
        report = self.report()
        r1 = report["run_summaries"]["R1"]
        self.assertEqual(r1["record_states"], {"valid_binary": 5, "valid_semantic_null": 1, "technical_failure": 1, "not_called": 1})
        domain = report["paired_comparisons"]["R1/R2"]["dimensions"]["I"]["domain"]
        self.assertEqual(domain["excluded_assignedIDs"], ["TOY-005", "TOY-006", "TOY-007"])
        states = [p["states_in_run_order"] for p in domain["exclusion_overlap_patterns"]]
        self.assertIn({"R1": "semantic_null", "R2": "binary_0"}, states)
        self.assertIn({"R1": "technical_failure", "R2": "binary_0"}, states)
        self.assertIn({"R1": "not_called", "R2": "not_called"}, states)
        self.assertEqual(domain["material_pending_n"], 1)
        nulls = report["three_main_runs"]["semantic_null_patterns"]
        self.assertFalse(nulls["is_binary_stability"])
        self.assertEqual(nulls["at_least_one_semantic_null_n"], 2)

    def test_three_run_vector_denominator_hand_count(self):
        triple = self.report()["three_main_runs"]
        v = triple["five_dimension_vector"]
        self.assertEqual(v["domain"]["joint_comparable_assignedIDs"], ["TOY-001", "TOY-002", "TOY-003", "TOY-004"])
        self.assertEqual(v["agreement_assignedIDs"], ["TOY-001"])
        self.assertEqual(v["complete_agreement_rate"], 1/4)
        self.assertEqual(v["weighted_complete_agreement_rate"], 1/10)
        self.assertEqual(triple["by_dimension"]["S"]["complete_agreement_rate"], 5/6)
        self.assertEqual(triple["by_dimension"]["I"]["complete_agreement_rate"], 3/5)

    def test_q_shared_five_binary_subset_unequal_weights_own_denominators(self):
        q = self.report()["three_main_runs"]["q"]
        self.assertEqual(q["domain"]["excluded_assignedIDs"], ["TOY-005", "TOY-006", "TOY-007", "TOY-008"])
        expected = {"R1": ({"S": 2, "E": 2, "Ec": 1, "I": 1, "F": 1}, 7, {"S": 6, "E": 7, "Ec": 4, "I": 4, "F": 4}, 25),
                    "R2": ({"S": 1, "E": 2, "Ec": 1, "I": 2, "F": 1}, 7, {"S": 2, "E": 7, "Ec": 4, "I": 7, "F": 4}, 24),
                    "R3": ({"S": 2, "E": 2, "Ec": 1, "I": 2, "F": 1}, 8, {"S": 6, "E": 7, "Ec": 4, "I": 6, "F": 4}, 27)}
        for run, (t, den, wt, wden) in expected.items():
            value = q["by_run"][run]
            self.assertEqual(value["unweighted_T"], t)
            self.assertEqual(value["unweighted_sum5T"], den)
            self.assertEqual(value["weighted_T"], wt)
            self.assertEqual(value["weighted_sum5T"], wden)
            self.assertAlmostEqual(sum(value["weighted_q"].values()), 1)
        self.assertAlmostEqual(q["by_run"]["R1"]["weighted_q"]["S"], 6/25)
        self.assertAlmostEqual(q["by_run"]["R2"]["weighted_q"]["S"], 1/12)
        self.assertAlmostEqual(q["q_ranges"]["weighted_q"]["S"]["range"], 6/25-1/12)
        self.assertFalse(self.report()["limits"]["population_claim_made"])

    def test_fixed_variant_baseline_despite_better_other_main_match(self):
        report = self.report()
        self.assertEqual(list(report["paired_comparisons"]), ["R1/R2", "R1/R3", "R2/R3", "W/R1", "H/R1"])
        for variant in ("W/R1", "H/R1"):
            i = report["paired_comparisons"][variant]["dimensions"]["I"]
            self.assertEqual(i["label_changes"][0]["assignedID"], "TOY-003")
            # W/H = R2 at this record; tool still compares R1 and records disagreement.
            self.assertEqual(i["label_changes"][0]["first_label"], 1)
            self.assertEqual(i["label_changes"][0]["second_label"], 0)

    def test_first_production_raw_binding_and_no_fill_from_diagnostics(self):
        report, firsts, audit, _ = analyze_registry(self.registry, self.ledger)
        self.assertEqual(firsts["runs"]["P"]["TOY-001"]["attempt_number"], 2)
        self.assertIsNone(firsts["runs"]["P"]["TOY-003"])
        self.assertIsNotNone(firsts["runs"]["R1"]["TOY-003"])
        self.assertIsNone(report["production_firsts"]["TOY-002"]["labels"]["I"])
        self.assertEqual(report["production_firsts"]["TOY-004"]["labels"], dict.fromkeys(DIMS, 0))
        self.assertEqual(audit["runs"]["P"][2]["actual_attempt_count"], 3)
        self.assertEqual(audit["runs"]["P"][6]["actual_attempt_count"], 0)

    def test_configuration_version_and_batch_drift_rejected(self):
        self.change(registry=lambda r: r["conditions"]["R2"].update(common_configuration_sha256="0"*64))
        self.rejected("configuration drift")
        self.registry, self.ledger = make_fixture(self.base / "version")
        self.change(registry=lambda r: r["common_artifacts"]["manual"].update(version="changed-v2"))
        self.rejected("version/manual/prompt drift")
        self.registry, self.ledger = make_fixture(self.base / "batch")
        self.change(ledger=lambda l: l["runs"]["R2"]["records"][0].update(batch_id="B2"))
        self.rejected("order or batch drift")

    def test_retry_exact_request_drift_rejected(self):
        self.change(ledger=lambda l: l["runs"]["P"]["records"][0]["attempts"][1]["request_binding"]["exact_request"].update(sha256="0"*64))
        self.rejected("retry exact request/material drift")

    def test_configuration_json_types_are_exact_not_python_equal(self):
        self.change(registry=lambda r: r["common_configuration"]["request_settings"].update(toy_controllable_parameter=1))
        self.rejected("configuration drift")
        self.registry, self.ledger = make_fixture(self.base / "json-types")
        self.change(ledger=lambda l: l["runs"]["R1"]["records"][0]["attempts"][0]["executed_configuration"]["request_settings"].update(toy_numeric_parameter=True))
        self.rejected("model/settings drift")

    def test_incomplete_failed_snapshot_does_not_claim_retry_exhaustion(self):
        self.change(ledger=lambda l: l["runs"]["R1"]["records"][5]["attempts"].__delitem__(slice(1, None)))
        report = self.report()
        row = report["per_record_diagnostic_states"]["TOY-006"]["R1"]
        self.assertEqual(row["state"], "technical_failure")
        self.assertFalse(row["failure_exhausted_three_attempts"])
        self.assertEqual(row["remaining_retry_slots_if_unresolved"], 2)
        self.assertFalse(report["limits"]["all_registered_records_have_technical_firsts"])

    def test_stability_threshold_and_ci_gate_cannot_be_added(self):
        self.change(registry=lambda r: r.update(stability_pass_threshold=0.80))
        self.rejected("no stability pass threshold or CI gate")

    def test_semantic_null_is_first_valid_and_cannot_trigger_retry(self):
        def add_retry(led):
            row = led["runs"]["P"]["records"][1]
            a = copy.deepcopy(row["attempts"][0])
            a["attempt_number"] = 2
            a["started_at"], a["ended_at"] = "2026-10-09T01:00:04+00:00", "2026-10-09T01:00:05+00:00"
            row["attempts"].append(a)
        self.change(ledger=add_retry)
        self.rejected("semantic null cannot trigger retry")

    def test_diagnostic_cannot_replace_production_first(self):
        self.change(ledger=lambda l: l["runs"]["P"]["records"][2].update(first=copy.deepcopy(l["runs"]["R1"]["records"][2]["first"])))
        self.rejected("no diagnostic substitution")

    def test_missing_rows_and_unregistered_repeats_rejected(self):
        self.change(ledger=lambda l: l["runs"]["R2"]["records"].pop())
        self.rejected("complete ordered record ledger")
        self.registry, self.ledger = make_fixture(self.base / "new-repeat")
        self.change(registry=lambda r: r["conditions"].update(R4=copy.deepcopy(r["conditions"]["R3"])))
        self.rejected("conditions must be registered once")

    def test_model_receipt_drift_rejected_and_hash_never_proves_model(self):
        def mutate(led):
            for run, returned in [("R1", "actual-v1"), ("R2", "actual-v2")]:
                a = led["runs"][run]["records"][0]["attempts"][0]
                a["provider_receipt"] = {"status": "observed_unverified", "request_id": f"toy-{run}", "returned_model": returned, "configuration_evidence": None}
        self.change(ledger=mutate)
        self.rejected("provider-returned model identity drift")

    def test_batch_context_reports_protocol_difference_and_unverified_independence(self):
        reg, led = make_fixture(self.base / "batch-context", context_unit="batch")
        report = analyze_registry(reg, led)[0]
        identity = report["identity_and_independence"]
        self.assertEqual(identity["context_unit"], "batch")
        self.assertFalse(identity["per_record_context_protocol_shape"])
        self.assertFalse(identity["independent_contexts_verified"])
        self.assertFalse(identity["actual_model_identity_proven"])
        self.assertIn("differs", identity["batch_context_warning"])
        self.assertFalse(report["limits"]["binary_input_complete_for_all_registered_runs"])

    def test_context_unit_required_and_no_native77_default(self):
        self.change(registry=lambda r: r.pop("context_unit"))
        self.rejected("registry top-level fields must be exactly")

    def test_whitespace_preserves_source_string_and_heading_not_stacked(self):
        reg = json.loads(self.registry.read_text())
        first = "TOY-001"
        requests = {}
        for run in ("R1", "W", "H"):
            ref = reg["conditions"][run]["requests"][first]["exact_request"]
            requests[run] = json.loads((self.registry.parent / ref["path"]).read_text())
        wuser = requests["W"]["messages"][1]["content"]
        self.assertTrue(wuser.startswith("判读要求\n{\n  "))
        self.assertIn("a  b\\n", wuser)
        huser = requests["H"]["messages"][1]["content"]
        self.assertTrue(huser.startswith("判读说明\n{"))
        # Replace the W bytes with H; reseal its registration and ledger to expose semantic gate.
        wref = reg["conditions"]["W"]["requests"][first]["exact_request"]
        href = reg["conditions"]["H"]["requests"][first]["exact_request"]
        (self.registry.parent / wref["path"]).write_bytes((self.registry.parent / href["path"]).read_bytes())
        self.change(registry=lambda r: r["conditions"]["W"]["requests"][first]["exact_request"].update(sha256=href["sha256"]))
        self.rejected("permitted assembly")

    def test_probability_metadata_remains_scope_declaration_not_population_claim(self):
        reg, led = make_fixture(self.base / "probability", probability=True)
        report = analyze_registry(reg, led)[0]
        self.assertEqual(report["sampling"]["selection_mode"], "probability")
        self.assertFalse(report["limits"]["population_claim_made"])
        self.assertFalse(report["limits"]["confidence_intervals_computed"])

    def test_reproducible_outputs_and_nonoverwrite_guard(self):
        s1 = save_analysis(self.registry, self.ledger, self.base / "output-1")
        s2 = save_analysis(self.registry, self.ledger, self.base / "output-2")
        self.assertEqual(s1["outputs"], s2["outputs"])
        with self.assertRaisesRegex(ContractError, "will not be overwritten"):
            save_analysis(self.registry, self.ledger, self.base / "output-1")
        for output in s1["outputs"]:
            self.assertEqual(digest((self.base / "output-1" / output["path"]).read_bytes()), output["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
