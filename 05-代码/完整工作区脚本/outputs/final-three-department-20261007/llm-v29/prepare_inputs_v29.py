"""Build blind v29 LLM inputs from the frozen v28 context-repaired corpus.

This program copies source text and context only.  It never opens prediction,
reference-label, discrepancy, metric, or manuscript files.
"""
import hashlib
import json
from pathlib import Path
from functools import lru_cache

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "outputs/autocode-v28-review-20261004-111306/rule_inputs_v27.jsonl"
EXPECTED_SHA256 = "e8ec43faf7371f951101202a6fd291e8627d07940b9de15671b7778ba61585df"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=None)
def candidate_units(path_string):
    data = json.loads(Path(path_string).read_text())
    return data["unit_candidates"]


def main():
    assert sha256(SOURCE) == EXPECTED_SHA256, "frozen v28 input changed"
    source_rows = [json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
    assert len(source_rows) == 4924
    rows = []
    for wrapper in source_rows:
        record = wrapper["input"]
        contexts = {
            "paragraph_context": record.get("paragraph_context", []),
            "nearest_preceding_heading": record.get("nearest_preceding_heading"),
            "immediately_preceding_paragraph": record.get("immediately_preceding_paragraph"),
            "verified_parent_context": record.get("verified_parent_context", []),
            "verified_scope_qualifications_v28": record.get("verified_scope_qualifications_v28", []),
            "content_role": record.get("content_role"),
            "content_role_basis": record.get("content_role_basis"),
        }
        # Preserve every source-verified context certificate already present in
        # the frozen v28 input, regardless of the historical field name.
        contexts["verified_context_certificates"] = {
            key: value for key, value in record.items()
            if key.startswith("verified_") and value
        }
        # A colon-ended lead-in is structurally incomplete without its listed
        # children. Attach bounded, same-component following units as context;
        # this is a material-completeness repair and never assigns a label.
        contexts["structured_following_units"] = []
        if record["unit_text"].rstrip().endswith((":", "：")) and record.get("candidate_file"):
            units = candidate_units(record["candidate_file"])
            position = next(i for i, unit in enumerate(units) if unit["id"] == record["unit_id"])
            component = units[position].get("component")
            for unit in units[position + 1:position + 5]:
                if component is not None and unit.get("component") != component:
                    break
                contexts["structured_following_units"].append({
                    "unit_id": unit["id"], "text": unit["text"],
                    "pages": unit.get("pages", []), "paragraph_id": unit.get("paragraph_id")
                })
        rows.append({
            "id": wrapper["id"],
            "text": record["unit_text"],
            "source_title": record.get("original_file_stem"),
            "pages": record.get("pages", []),
            "contexts": contexts,
            "context_usage": "Only resolve object, reference, condition, comparison, abbreviation, or table relation; do not inherit labels from context.",
        })
    assert len({row["id"] for row in rows}) == 4924
    output = HERE / "frozen_blind_inputs_v29.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    manifest = {
        "status": "blind_input_prepared",
        "n": len(rows),
        "source": str(SOURCE),
        "source_sha256": EXPECTED_SHA256,
        "output": str(output),
        "output_sha256": sha256(output),
        "labels_or_predictions_read": False,
        "distinct_units_with_verified_parent_context": sum(bool(r["contexts"]["verified_parent_context"]) for r in rows),
        "distinct_units_with_scope_qualifications": sum(bool(r["contexts"]["verified_scope_qualifications_v28"]) for r in rows),
        "distinct_units_with_any_verified_certificate": sum(bool(r["contexts"]["verified_context_certificates"]) for r in rows),
        "distinct_units_with_structured_following_units": sum(bool(r["contexts"]["structured_following_units"]) for r in rows),
    }
    (HERE / "input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
