"""Six small mechanism guards only; no real data or coder labels."""
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("finite_binder04_guards", HERE / "literal_source_binder.py")
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    checks = [
        ("real_word_change", ".txt", "药物，安全。", "药物,有效。", {}, "source_literal_absent"),
        ("ASCII_word_separator_loss", ".txt", "new drug", "newdrug", {}, "source_literal_absent"),
        ("native_child_p_join_in_cell", ".html", "<table><tr><td><p>药物，</p><p>安全。</p></td></tr></table>", "药物,安全。", {}, "source_literal_absent"),
        ("normalized_duplicate_cannot_pick_index", ".txt", "药物，安全。药物,安全。", "药物,安全。", {"occurrence_index": 0}, "source_literal_ambiguous"),
        ("Roman_drug_name_outside_guard", ".txt", "药品Ⅰ具有活性。", "药品I具有活性。", {}, "source_literal_absent"),
        ("Roman_value_cannot_select_partial_expansion", ".txt", "Ⅲ期临床试验。", "I期临床试验。", {}, "source_literal_absent"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="finite-layout-guards04-") as temp:
        root = Path(temp)
        for name, suffix, original, leaf, locator, expected in checks:
            source, candidate = root / (name + suffix), root / (name + ".json")
            source.write_text(original, encoding="utf-8")
            candidate.write_text(json.dumps({"source": str(source), "source_sha256": sha(source),
                "paragraphs": [{"id": "p", "text": leaf}], "unit_candidates": [{"id": "u", "paragraph_id": "p", "text": leaf}]}))
            actual = binder.bind_leaf(leaf, record_id=name, raw_pointer="/text",
                source_identity={"source_path": str(source), "source_sha256": sha(source)},
                candidate_identity={"candidate_path": str(candidate), "candidate_sha256": sha(candidate)},
                candidate_locator={"leaf_scope": "unit", "unit_id": "u", "paragraph_id": "p"},
                source_locator=locator, allow_finite_layout_mapping=True)
            passed = actual["status"] == binder.UNBOUND and expected in actual["reasons"]
            results.append({"name": name, "expected": expected, "passed": passed, "actual": actual})
    report = {"at_utc": datetime.now(timezone.utc).isoformat(), "code_sha256": sha(HERE / "literal_source_binder.py"),
        "test_sha256": sha(__file__), "n": len(results), "passed_n": sum(x["passed"] for x in results), "results": results,
        "scope": "Six fresh-file mechanism guards; no corpus/model/rule/labels; not independent validation."}
    out = HERE / "mechanism_execution04.json"
    with out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write("\n")
    print(json.dumps({"n": report["n"], "passed_n": report["passed_n"], "results": [{"name": x["name"], "passed": x["passed"], "reasons": x["actual"]["reasons"]} for x in results]}))


if __name__ == "__main__":
    run()
