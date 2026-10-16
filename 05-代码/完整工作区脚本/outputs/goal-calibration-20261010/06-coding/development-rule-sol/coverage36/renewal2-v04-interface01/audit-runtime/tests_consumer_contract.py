"""Synthetic relation contract checks only; never import dimensions or judge."""
from pathlib import Path
import copy
import datetime
import hashlib
import io
import json
import sys
import unittest

AUDIT = Path(__file__).resolve().parent
BASE = AUDIT.parent
sys.path.insert(0, str(BASE))
import relations

NEWPAR = "same_snapshot_referenced_source_paragraph"
NEWGEO = "same_snapshot_source_numbered_group_geometry"
SHA = "a" * 64
OUTPUTS = []

def context(cid, kind, text="", structure=None):
    return {"context_id": cid, "kind": kind, "text": text,
            "structure": structure or {}, "source_ref": {"sha256": SHA}}

def standard(par_kind="source_paragraph", graph_kind="structural_relation", top=False):
    text = "符合上述条件的药品可以申请研发审评试点。"
    contexts = [context("CTX-current", "paragraph", text),
                context("CTX-rule", par_kind, "研发审评试点适用条件：申请人应符合既有条件。")]
    if not top:
        contexts.append(context("CTX-graph", graph_kind, structure={"related_context_ids": ["CTX-rule"]}))
    unit = {"text": text, "contexts": contexts}
    if top:
        unit["source_references"] = [{"context_id": "CTX-rule", "literal_reference": "研发审评试点", "literal_relation_type": "same_source_original_reference"}]
    return unit

def numbered(new_graph=False, new_member=False):
    text = "符合以下条件的药品可以申请。"
    current = context("CTX-current", "paragraph", text)
    member = context("CTX-member", NEWPAR if new_member else "ordered_members", "所提交内容应满足原始条件乙。")
    if new_graph:
        graph = context("CTX-graph", NEWGEO, structure={"rule1_condition_group": {"parent_resource_id": "CTX-current", "numbered_members": ["CTX-member"], "operator": "all"}})
    else:
        graph = context("CTX-graph", "ordered_list", structure={"child_groups": [{"position": "contexts", "ordered_context_ids": ["CTX-current", "CTX-member"]}]})
    return {"text": text, "contexts": [current, member, graph]}

def inspect(name, unit):
    before = copy.deepcopy(unit)
    view = relations.RelationView(unit)
    assert unit == before, "RelationView changed the original synthetic source"
    OUTPUTS.append({"name": name, "input": before, "relations": view.traces(), "material_requests": view.material_requests, "input_unchanged": unit == before})
    return view

class ConsumerContract(unittest.TestCase):
    def test_old_standard_with_structural_edge(self):
        self.assertTrue(inspect("old_standard_with_structural_edge", standard()).linked("cited_standard"))

    def test_new_paragraph_with_old_edge(self):
        view = inspect("new_paragraph_with_old_edge", standard(par_kind=NEWPAR))
        self.assertFalse(view.linked("cited_standard"))
        self.assertTrue(any(x["path"] == "cited_standard" for x in view.material_requests))

    def test_old_paragraph_with_new_geometry_edge(self):
        view = inspect("old_paragraph_with_new_geometry_edge", standard(graph_kind=NEWGEO))
        self.assertFalse(view.linked("cited_standard"))
        self.assertTrue(any(x["path"] == "cited_standard" for x in view.material_requests))

    def test_source_references_alone(self):
        view = inspect("source_references_alone", standard(top=True))
        self.assertFalse(view.linked("cited_standard"))
        self.assertTrue(any(x["path"] == "cited_standard" for x in view.material_requests))

    def test_old_numbered_graph(self):
        self.assertTrue(inspect("old_numbered_graph", numbered()).linked("substantive_list"))

    def test_new_geometry_numbered_graph(self):
        view = inspect("new_geometry_numbered_graph", numbered(new_graph=True, new_member=True))
        self.assertFalse(view.linked("substantive_list"))
        self.assertTrue(any(x["path"] == "substantive_list" for x in view.material_requests))

    def test_new_raw_kind_through_old_numbered_graph(self):
        view = inspect("new_raw_kind_through_old_numbered_graph", numbered(new_member=True))
        self.assertTrue(view.linked("substantive_list"))
        self.assertEqual(view.by_id["CTX-member"]["kind"], NEWPAR)

    def test_arbitrary_extra_raw_metadata_preserved(self):
        unit = standard(par_kind=NEWPAR, graph_kind=NEWGEO)
        unit["source_ref"] = {"sha256": SHA, "source_resource_id": "RAWRESOURCE", "locator": {"physical_pages": [2, 3]}}
        unit["source_references"] = [{"context_id": None, "source_field": "source_context", "literal_reference": "原始参考字串"}]
        unit["contexts"][-1]["structure"]["original_geometry"] = {"operator_printed": "之一", "operator": "any", "nested": [[1.25, 2.5], [3, 4]], "raw_null": None}
        inspect("arbitrary_extra_raw_metadata_preserved", unit)

def main():
    paths = [AUDIT / "consumer-contract-tests-run01.json", AUDIT / "consumer-contract-tests-run01.txt"]
    if any(p.exists() for p in paths):
        raise ValueError("Refuse to overwrite any contract attempt")
    declaration = AUDIT / "consumer-contract-contrasts-before-execution.json"
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    code = {name: sha(BASE / name) for name in ("evidence.py", "relations.py")}
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContract))
    report = {"role": "synthetic_RelationView_contract_execution_only", "started_at_utc": start,
              "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "declaration_sha256": sha(declaration), "code_sha256": code,
              "code_unchanged_during_execution": all(sha(BASE / name) == digest for name, digest in code.items()),
              "test_n": result.testsRun, "failure_n": len(result.failures), "error_n": len(result.errors),
              "passed": result.wasSuccessful(), "all_outputs": OUTPUTS,
              "failures": [{"test": str(t), "trace": s} for t, s in result.failures],
              "errors": [{"test": str(t), "trace": s} for t, s in result.errors],
              "actual_new2_source_used_in_tests": False, "dimensions_imported_or_judge_called": False,
              "raw_reference_A_B_native_read": False, "new2_expected_labels_assigned": False}
    with paths[0].open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False); f.write("\n")
    with paths[1].open("x") as f:
        f.write(stream.getvalue())
    print(json.dumps({k: report[k] for k in ("test_n", "failure_n", "error_n", "passed", "code_unchanged_during_execution")}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
