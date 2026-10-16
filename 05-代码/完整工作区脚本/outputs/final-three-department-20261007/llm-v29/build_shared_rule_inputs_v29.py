"""Add the v29 LLM context packet to frozen v28 rule inputs, without labels."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "outputs/autocode-v28-review-20261004-111306/rule_inputs_v27.jsonl"
BLIND = HERE / "frozen_blind_inputs_v29.jsonl"
OUTPUT = HERE / "rule_inputs_v29_shared.jsonl"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    contexts = {row["id"]: row["contexts"] for row in map(json.loads, BLIND.read_text().splitlines())}
    supplement_path = HERE / "supplement_RECODE25-02158.json"
    supplement = json.loads(supplement_path.read_text())
    source_path = Path(supplement["source_path"])
    supplement["source_sha256"] = sha(source_path)
    override_ids=['RECODE25-00932','RECODE25-01008','RECODE25-01241','RECODE25-01959','RECODE25-02158','RECODE25-02287','RECODE25-02914','RECODE25-04282']
    for rid in override_ids:
        payload=json.loads(json.dumps(supplement,ensure_ascii=False));payload['id']=rid
        contexts[rid]["resolved_material_supplement"] = payload
    output = []
    for row in map(json.loads, SOURCE.read_text().splitlines()):
        copied = json.loads(json.dumps(row, ensure_ascii=False))
        copied["input"]["llm_v29_shared_context"] = contexts[copied["id"]]
        output.append(copied)
    assert len(output) == len(contexts) == 4924
    assert [row["id"] for row in output] == list(contexts)
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output))
    manifest = {
        "n": 4924, "source_sha256": sha(SOURCE), "blind_input_sha256": sha(BLIND),
        "output_sha256": sha(OUTPUT), "labels_or_predictions_read": False,
        "supplement_template_sha256": hashlib.sha256(json.dumps(supplement, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "override_ids": override_ids,
        "change": "Original rule input preserved; effective llm_v29_shared_context appended per ID, including eight uniformly completed Articles 9/10 cross-references."
    }
    (HERE / "rule_inputs_v29_shared_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
