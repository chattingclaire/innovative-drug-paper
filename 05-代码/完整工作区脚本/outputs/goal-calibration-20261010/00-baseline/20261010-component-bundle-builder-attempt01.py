"""Bind completed components prospectively without distributing packets or coding."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "05-validation/formal-component-freeze-v1-root"


def read(p):
    return json.loads(Path(p).read_text())


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def bind(p):
    p = Path(p).resolve()
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    if OUT.exists():
        raise RuntimeError("Component bundle already exists; do not overwrite a freeze")
    manual_dir = ROOT / "03-manual/common-manual-v1.3F-frozen"
    human = ROOT / "05-validation/formal-freeze-interface-v1-sol"
    native = ROOT / "06-coding/formal-frozen-native-interface-v1-sol"
    # Require actual sealed interfaces, not an anticipated deliverable.
    for p in [manual_dir / "seal.json", human / "seal.json", native / "seal.json"]:
        if not p.exists():
            raise RuntimeError(f"Actual seal missing: {p}")
    packet_dir = ROOT / "05-validation/full800-real-blindpack-sol"
    draw = read(packet_dir / "coordinator-private/draw-contract.json")
    pre = read(packet_dir / "pre-draw-freeze.json")
    assert draw["actual_drawn"] is True and draw["sample_n"] == 800
    assert len(draw["selected_strata"]) == 41
    frozen_manual = bind(manual_dir / "manual.txt")
    assert frozen_manual["sha256"] == "a0ef2967ef964c625f331fefa82f4020d384ecae579e2a0a7d178651e8beda70"
    OUT.mkdir()
    write(OUT / "identity-registry.pending.json", {
        "version": "actual-identity-pending-1", "actors": [],
        "status": "unassigned", "actual_human_independent_executions": 0,
        "AI_modified_labels": "Retain actual coding results; identify AI drafting/revision and any actual human review separately.",
        "primary_human_requirement_changed": False,
        "two_existing_user_clarifications": "pending; no repeated question or assumed answer",
    })
    sides = {}
    for side in ("A", "B"):
        dest = OUT / f"coder-{side}"
        dest.mkdir()
        (dest / "manual-v1.3F.txt").write_bytes((manual_dir / "manual.txt").read_bytes())
        old = packet_dir / f"coder-{side}"
        manifest = read(old / "packet-manifest.json")
        # Administrative overlay only: all packet/source/label values remain unchanged.
        manifest["manual"] = {**bind(dest / "manual-v1.3F.txt"), "declared_status": "normative component frozen; execution release pending"}
        manifest["status"] = "component_bound_unreleased_no_coding_authorized"
        write(dest / "packet-manifest.json", manifest)
        sub = read(old / "submission.blank.json")
        sub["manual_sha256"] = frozen_manual["sha256"]
        sub["sidecar_sha256"] = None
        write(dest / "submission.blank.json", sub)
        release = read(human / "human-release.template.json")
        release["side"] = side
        release["packet_manifest"] = bind(dest / "packet-manifest.json")
        release["packet_file"] = bind(old / "packet.jsonl")
        release["manual"] = bind(dest / "manual-v1.3F.txt")
        release["source_asset_index"] = bind(old / "source-assets-index.json")
        # Intentionally keep round, purpose, identity, and executor unset and status pending.
        write(dest / "release.pending.json", release)
        (dest / "操作说明.txt").write_text(
            "这是未分发的编码材料组件。实际身份、执行轮次与独立性登记完成后另行发布。\n"
            "现行共同手册为本目录 manual-v1.3F.txt。旧准备包中的 manual-v1.3.txt 保留为历史准备副本。\n"
            "packet-manifest.json 指向原样保存的本侧 packet、空白 labels 和公共来源附件；正文与空白标签未重写。\n"
            "实际执行只提供本侧材料、现行手册与公共附件；开发裁定、另一侧判断、机器答案及协调者私有文件不随包分发。\n"
            "先保存真实首判及理由，再另版复核或裁定。AI修改/初判及真人事后复核按实际身份登记。\n"
            "0需理由和依据；实际待定需具体补材请求。尚未填写的null不构成已完成判断。\n"
            "公共引文保持资源ID/SHA、原指针及连续原文；I3/F关系证据与实际来源读/用、图像查看记录另存sidecar。\n"
            "手册所引历史来源索引由协调者保存；不向编码者提供开发标签或案例裁定。\n"
        )
        sides[side] = {
            "manifest": bind(dest / "packet-manifest.json"),
            "pending_release": bind(dest / "release.pending.json"),
            "blank_submission": bind(dest / "submission.blank.json"),
            "original_blank_labels": manifest["blank_labels_file"],
            "packet_and_source_values_changed": False,
            "actual_released": False,
        }
    contract = {
        "version": "formal-component-freeze-v1-root",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "actual_author": "ROOT AI agent",
        "component_binding_builder": bind(Path(__file__)),
        "scope": "Completed normative manual, source/sample/statistical and executable interface components; administrative binding only",
        "component_freeze_complete": True,
        "joint_execution_release_complete": False,
        "new_coding_authorized": False,
        "actual_people_assigned": False,
        "actual_new_human_labels": 0, "actual_new_AI_labels": 0,
        "formal_metric_acceptance": False, "complete_paper_writing_started": False,
        "manual": frozen_manual,
        "component_seals": {"manual": bind(manual_dir / "seal.json"), "human_rule_interface": bind(human / "seal.json"), "native_interface": bind(native / "seal.json")},
        "source_and_sample": {
            "source_v14_seal": bind(ROOT / "01-review/context-projection-sol/source-interface-v14-textleaf/delivery-seal.json"),
            "actual_draw_contract": bind(packet_dir / "coordinator-private/draw-contract.json"),
            "actual_pre_draw_freeze": bind(packet_dir / "pre-draw-freeze.json"),
            "preparation_seal": bind(packet_dir / "seal.json"),
            "seed": draw["sampling_seed"], "population_N": pre["population_N"],
            "domain_population_N": pre["domain_population_N"], "sample_N": 800,
            "domain_sample_N": draw["domain_sample_n"], "department_sample_N": draw["department_n"],
            "strata_N": 41,
            "strata": [{k: v for k, v in h.items() if k != "selected_ids_sorted"} for h in draw["selected_strata"]],
            "sample_unchanged": True, "body_or_context_semantic_read_by_this_operation": False,
            "source_context_overlap": {"registered_remaining_same_primary_source_N": 43, "selected_remaining_source_context_overlap_N": 16, "actual_case_development_status": "unknown except recorded targets", "new_exclusion_or_redraw": False},
            "old_manual_binding_at_draw": pre["manual"],
            "administrative_manual_update": "v1.3F has six editorial/history edits; operative definitions and source/sample values unchanged; before any new first labels",
        },
        "statistics": {
            **pre["statistics"],
            "original_v2_proposal_status_kept": True,
            "current_sample_design": "Actual full800/41-stratum draw supersedes historical undecided 600-only planning flags for this sample",
            "analysis_domains": ["ALL", "remaining", "exposed", "NMPA", "NHSA", "NHC"],
            "single_joint_design_repeat_weights_for_all_domains": True,
            "human_primary_point_criterion": "Actual independent human A/B per-dimension Cohen kappa >= 0.80",
            "machine_primary_point_criteria": "Each of two machines versus credible adjudicated reference: per-dimension kappa/Precision/Recall/F1 >= 0.80",
            "diagnostics": ["original/design-weighted cells and denominators", "positive/negative class counts", "unknown/failed/unfilled counts", "Po/Pe/Ppos/Pneg", "Specificity/NPV where defined", "marginal 95% CI", "actual error types", "independent repeats and downstream attention robustness"],
            "no_added_CI_lower_bound_width_domain_census_or_zero_error_gate": True,
            "NA_never_one": True, "unknown_not_dropped_and_reweighted": True,
            "required_reference_and_first_judgments": "Actual identities, blinded independent firsts sealed before later adjudication; all sampled cases dual read and source-evidence review as preregistered",
        },
        "machine_execution": {
            "rule_algorithm": "v17 five exact modules retained; minimal driver interface only",
            "native_public_quote_schema": bind(ROOT / "06-coding/protocol-v15-common-public-quote-format-sol/output-item.schema.json"),
            "new_inference_runs": 0,
            "historical_native_attempts": "13 terminal contexts retained; interface version does not reset or reopen attempt limits",
            "rule_and_LLM_validation_or_full_recode": "Await actual credible reference and separately bound execution registration",
            "provider_telemetry_unknown": "null when unavailable, never inferred or a new gate",
        },
        "coder_sides": sides,
        "distribution": {"coordinator_private": ["mapping", "draw strata/development status", "history/source index/change logs", "reference or other actor outputs"], "actual_distribution_done": False},
        "full_eight_step_goal_unchanged": True,
    }
    write(OUT / "component-freeze.json", contract)
    (OUT / "README.md").write_text(
        "# 正式方法与材料组件冻结\n\n"
        "共同手册v1.3F、已抽取的800条材料与41层抽样/统计方案、规则/人工接收接口、LLM原生接口已绑定。\n\n"
        "本目录只新增管理文件与两份同字节正式手册。原盲包正文、空白标签、来源及历史封存均保留；未分发、未产生新判断或推断。\n\n"
        "人员及方法身份、实际独立首判和可信裁定参照仍待落实。真人逐维κ与两机器逐维κ/P/R/F1的0.80项目目标不变。正式验收后才开始完整正文修订。\n"
    )
    files = [bind(p) for p in sorted(OUT.rglob("*")) if p.is_file()]
    write(OUT / "seal.json", {"version": "component-freeze-seal-v1", "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "members": files, "component_only": True, "joint_release": False, "new_labels_or_inference": False})
    print(json.dumps({"component_bundle": str(OUT), "members": len(files), "seal": bind(OUT / "seal.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
