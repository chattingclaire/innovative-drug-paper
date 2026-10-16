"""Author reproduction + predeclared deep synthetic boundary checks only."""
import argparse
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PREVIOUS_RUNNER = BASE / "全量材料接口核查03/independent_review03/run_independent03.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    code = HERE / "project_source_only_inputs.py"
    before = sha(code)
    reports = []
    for filename in ("design_previous28_regression.json", "design_deep_boundary16.json"):
        design_path = HERE / filename
        original_design = json.loads(design_path.read_text())
        design = copy.deepcopy(original_design)
        design["code_sha256"] = before  # Target identity only; fixtures/expected contracts unchanged.
        spec = importlib.util.spec_from_file_location("boundary04_author_constructed", PREVIOUS_RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory(prefix="author-boundary04-check-driver-") as tmp:
            runner.HERE = Path(tmp)
            runner.BASE = BASE
            (runner.HERE / "design_independent03.json").write_text(json.dumps(design, ensure_ascii=False))
            preserved = json.loads((HERE / "preservation_before04.json").read_text())
            (runner.HERE / "preservation_before.json").write_text(json.dumps(preserved, ensure_ascii=False))
            report = runner.run()
        report["reviewer"] = "/root/independent06_static author checks; not independent04 review"
        report["origin"] = original_design["origin"]
        report["static_design_sha256"] = sha(design_path)
        report["target_identity_adaptation_only"] = design["cases"] == original_design["cases"]
        for case, result in zip(design["cases"], report["results"]):
            if case["structural_check"] != "deep_supported_duplicates":
                continue
            nodes = result["actual"]["model_visible_candidate"]["contexts"]
            by_id = {n["context_id"]: n for n in nodes}
            parent = next(n for n in nodes if n["structure"].get("paragraph_id") == "deep-parent")
            group = next(g for g in parent["structure"]["child_groups"] if g["position"] == "contexts")
            ordered = group["ordered_context_ids"]
            result["assertions"]["deep_distinct_ordered_occurrences"] = len(ordered) == len(set(ordered)) == 2
            result["assertions"]["deep_member_position_order"] = [by_id[c]["structure"].get("paragraph_id") for c in ordered] == ["deep-g5", "deep-g6"]
            result["assertions"]["deep_member_parent_links"] = all(by_id[c]["structure"].get("parent_context_id") == parent["context_id"] for c in ordered)
            result["passed"] = all(result["assertions"].values())
        report["passed_n"] = sum(r["passed"] for r in report["results"])
        report["fail_n"] = sum(not r["passed"] for r in report["results"])
        reports.append(report)
    preserved = json.loads((HERE / "preservation_before04.json").read_text())
    preservation = [{"path": path, "before": old, "after": sha(path), "unchanged": sha(path) == old} for path, old in preserved.items()]
    assert sha(code) == before
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": before,
            "wrapper_sha256": sha(__file__), "reused_constructed_runner_sha256": sha(PREVIOUS_RUNNER),
            "check_n": sum(r["case_n"] for r in reports), "passed_n": sum(r["passed_n"] for r in reports),
            "fail_n": sum(r["fail_n"] for r in reports), "groups": reports,
            "preservation": preservation, "all_previous_files_unchanged": all(x["unchanged"] for x in preservation),
            "scope": "Author checks only; original28 expectations unchanged + 16 predeclared deep controls. No real text, gold labels, corpus export, model or rule run."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    args = parser.parse_args()
    path = HERE / f"boundary04_{args.phase}.json"
    if path.exists():
        raise SystemExit("Existing first phase result retained; do not overwrite.")
    result = run()
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("check_n", "passed_n", "fail_n", "all_previous_files_unchanged")}))
