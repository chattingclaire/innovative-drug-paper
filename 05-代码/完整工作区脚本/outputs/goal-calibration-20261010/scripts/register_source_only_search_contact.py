"""Disclose unintended source-only search hits without relabeling the frozen draw."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
HITS = {
    "718c657e19774070182809be23d1dcf5ad7482c1ab716022b207d698e01273a6": {"suffix": ".txt", "lines": [11]},
    "c2fc0fa7415194a5a98600b44e2c99a5055b5c67a92f062eb78239ee388b0b9d": {"suffix": ".json", "lines": [414]},
    "fe38c53150311f8eb8ba96f0b690cbcbc1e12a3a63e4ab12cbed407aa68bcc82": {"suffix": ".txt", "lines": [11, 16]},
    "0d4b904755a8425b910331d10acf508d33cc51338dd2cf20da2348ea28c725b5": {"suffix": ".txt", "lines": [87]},
    "dbddfca4cb82d3c76a92417efeffd3f102d735c5dc7e2871a8ff0e821e32c059": {"suffix": ".txt", "lines": [260, 314]},
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fingerprint(ids):
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def main():
    frame_path = ROOT / "01-review/context-projection-sol/source-interface-v14-textleaf/frame-bundle-bindings-v14.jsonl"
    mapping_path = ROOT / "05-validation/full800-real-blindpack-sol/coordinator-private/mapping.json"
    exposure_path = ROOT / "01-review/exposure-ids.json"
    prior_path = ROOT / "05-validation/full800-postdraw-development-read-exposure-check-sol/report.json"
    frame = [json.loads(line) for line in frame_path.open()]
    mapping = json.loads(mapping_path.read_text())["records"]
    exposure = json.loads(exposure_path.read_text())
    excluded = set(exposure["excluded_ids"])
    frame_ids = {r["id"] for r in frame}
    assert len(frame_ids) == len(frame) == 4481
    assert len(excluded) == 3037 and excluded <= frame_ids
    assert len(mapping) == 800
    remaining_ids = frame_ids - excluded
    sampled_remaining = {r["source_id"] for r in mapping if r["domain"] == "remaining"}
    sampled_exposed = {r["source_id"] for r in mapping if r["domain"] == "exposed"}
    prior_primary_sha = json.loads(prior_path.read_text())["primary_source_sha256"]
    old_contact = {r["id"] for r in frame if r["primary_source_sha256"] == prior_primary_sha}
    new_contact = {r["id"] for r in frame if r["primary_source_sha256"] in HITS}
    combined = old_contact | new_contact
    source_rows = []
    for source_sha, hit in HITS.items():
        source_path = ROOT / f"05-validation/full800-real-blindpack-sol/shared-source/source-files/{source_sha}{hit['suffix']}"
        assert sha(source_path) == source_sha
        members = {r["id"] for r in frame if r["primary_source_sha256"] == source_sha}
        source_rows.append({"source_path": str(source_path), "sha256": source_sha, "search_hit_lines_visible_in_tool_output": hit["lines"], "primary_source_member_N": len(members), "remaining_member_N": len(members & remaining_ids), "selected_remaining_member_N": len(members & sampled_remaining), "selected_exposed_member_N": len(members & sampled_exposed), "primary_membership_fingerprint": fingerprint(members), "zero_primary_membership_does_not_prove_zero_secondary_context_contact": True})
    output = {
        "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "scope": "source-only text-search excerpt contact; metadata-only intersection; no target-case coding, new gold or performance read",
        "trigger": "ROOT search for repetition/stability process records also descended into shared-source files; visible source hits are disclosed rather than described as untouched",
        "source_only_contact_not_full_document_read": True,
        "new_direct_case_development_exposure_proven_N": 0,
        "exclusion_definition_and_frozen_draw_unchanged": True,
        "claim_zero_source_context_contact_remaining600": False,
        "same_document_membership_is_conservative_source_contact_scope_not_actual_case_judgment": True,
        "source_rows": source_rows,
        "counts": {
            "new_search_source_primary_member_N": len(new_contact),
            "new_search_remaining_member_N": len(new_contact & remaining_ids),
            "new_search_selected_remaining_N": len(new_contact & sampled_remaining),
            "new_search_selected_exposed_N": len(new_contact & sampled_exposed),
            "known_prior_plus_new_primary_source_contact_member_N": len(combined),
            "known_prior_plus_new_selected_remaining_N": len(combined & sampled_remaining),
            "known_prior_plus_new_selected_exposed_N": len(combined & sampled_exposed),
        },
        "inputs": [{"path": str(p), "sha256": sha(p)} for p in [frame_path, mapping_path, exposure_path, prior_path]],
        "next_action": "preserve design and all first judgments; disclose source-context familiarity separately from direct case-development exposure; no semantic use of these search snippets to revise rules or manual",
        "actual_relabel_or_redraw": False,
        "formal_independent_human_coding_started": False,
    }
    target = ROOT / "logs/root-stability-search-source-contact-20261010.json"
    with target.open("x") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    p = ROOT / "progress.json"
    d = json.loads(p.read_text())
    d["source_only_stability_search_contact_actual"] = {"receipt": str(target.relative_to(ROOT)), "counts": output["counts"], "new_direct_case_development_proven_N": 0, "draw_unchanged": True, "no_zero_source_contact_claim": True}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"receipt": str(target), "counts": output["counts"], "draw_unchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
