"""Freeze a department-balanced random sample without consulting labels."""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / "frozen_blind_inputs_v29.jsonl").read_text().splitlines()]
groups = {"NMPA": [], "CDE": [], "NHSA": []}
for row in rows:
    title = row.get("source_title") or ""
    for department in groups:
        if title.startswith(department + "-"):
            groups[department].append(row)
            break
rng = random.Random(20261007)
selected = []
selection = {}
for department, candidates in groups.items():
    picks = rng.sample(candidates, 12)
    selected.extend(picks)
    selection[department] = [row["id"] for row in picks]
# Freeze one deterministic order, stratified blocks; no label information read.
packet = {"rows": selected}
(HERE / "stability_sample_36.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
(HERE / "stability_sample_manifest.json").write_text(json.dumps({
    "seed": 20261007, "n_per_department": 12, "n": 36,
    "selection_basis": "source_title prefix only; no labels, predictions, or metrics read",
    "ids": selection
}, ensure_ascii=False, indent=2) + "\n")
