"""Save read-only static findings and seal this independent audit once."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / "06-coding/rule-v20-SEEconomic-repair-sol"
BASELINE = ROOT / "06-coding/full4481-rule-production-adapter-sol"
MANUAL = ROOT / "03-manual/full4481-common-release-20261010-root/manual.txt"


def binding(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write_new(name, obj):
    with (HERE / name).open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def location(filename, token, *, last=False):
    text = (CANDIDATE / filename).read_text()
    at = text.rindex(token) if last else text.index(token)
    return {"path": str(CANDIDATE / filename), "line": text[:at].count("\n") + 1,
            "literal": token}


def manual_location(quote):
    text = MANUAL.read_text()
    at = text.index(quote)
    return {"path": str(MANUAL), "line": text[:at].count("\n") + 1,
            "quote": quote, "start": at, "end": at + len(quote), "exact_match": True}


def definitions(path):
    tree = ast.parse(path.read_text())
    out = {}
    def walk(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + node.name
                out[name] = {"line": node.lineno, "end_line": node.end_lineno,
                             "ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()}
            elif isinstance(node, ast.ClassDef):
                walk(node.body, prefix + node.name + ".")
    walk(tree.body)
    return out


def main():
    result = json.loads((HERE / "execution-results.json").read_text())
    cases = {c["name"]: c for c in result["cases"]}
    manual_quotes = [
        "递交安全文件的纯操作不能从文件名继承S；当前实质要求提供、核验或补充药物风险证据则可纳入。",
        "明确效果不足、尚不确定，或不存在达到防治效果要求的药物选项，仍是E内容。",
        "纳入：** 疗效、疾病控制、生存、健康相关生命质量、治疗优势、对应的药效研究/效果比较及证据要求；与药物效果判断有关的指南或诊疗推荐。",
        "当前实际设置或适用药品价格磋商、价格测算、评估价或协商价的形成/核验，属于价格内容，可按Ec纳入；不要求已有具体金额或协商成功。",
        "排除：** 一般行政收费、科研项目经费、设备采购等未与药品治疗/支付资源相连的费用；仅谈判阶段、协商成败、目录结果、普通申报资格或经济栏目名称。",
        "仅处方与诊断匹配、一般符合用药规范、适宜性安排",
        "药代动力学或作用机制的术语提及不自动构成E；当前明确要求考虑、评价或比较人群对药物作用反应的变化时，可按药效证据内容判断，不要求已证明临床获益。",
    ]
    manual_text = MANUAL.read_text()
    # Keep the actual complete original manual lines for every matched rule.
    quotes = [manual_location(q) for q in manual_quotes]
    for line in manual_text.splitlines():
        if ("宗旨" in line or "完整" in line or "兄弟" in line) and ("当前" in line or "原文" in line or "成员" in line):
            quotes.append(manual_location(line))
    write_new("manual-basis-quotes.json", {
        "manual_binding": binding(MANUAL), "exact_quote_match_N": len(quotes), "quotes": quotes,
        "semantic_sections_read": ["一、共同阈值及完整命题", "二、同版有限关系和完整成员", "三、安全性", "四、有效性", "五、经济性"],
        "human_reference": False})

    executed = [
        ("OBS-01", "over_inclusion", ["safety_filename_format", "ADR_report_archive_upload"],
         "纯文件命名/压缩包上传被赋S=1",
         "两个当前命题只规定文件名、命名格式、上传压缩包和包名。候选把安全性信息/不良反应名称与整个命题中的确认、应等动作共同匹配，未核定动作实际针对风险证据内容。",
         [location("dimensions.py", "def _se_form_or_status"), location("dimensions.py", "substance = bool(re.search(SE_ACTION")]),
        ("OBS-02", "over_inclusion", ["publication_purpose"],
         "纯印发宗旨被赋E=1",
         "当前只说明保证安全有效、改善健康的印发宗旨，无独立效果要求。原有印发边界未覆盖‘现将本工作流程予以印发’句式，新增qualified分支可单凭药物安全有效表达纳入。",
         [location("dimensions.py", "def _publication_content_spans"), location("dimensions.py", "qualified = re.search(r\"(?:安全")]),
        ("OBS-03", "omission", ["negative_benefit_risk"],
         "否定证据充分性的获益超过风险句漏S/E",
         "否定的是支持获益超过风险的证据，药物获益及风险评价仍在当前条件。匹配串获益比较未覆盖‘获益超过风险’，实际输出两个0；不能把证据尚不足处理成议题不存在。",
         [location("dimensions.py", "SE_BENEFIT_RISK =")]),
        ("OBS-04", "omission", ["PKPD_toxicity_only"],
         "明确肝损伤/副作用风险的PK/PD用途漏S",
         "当前PK/PD资料直接用于解释药物肝损伤信号并评估副作用风险，E=0合理；S=0不符合已表达的药物损害关系。新风险串未覆盖该损害表达，术语控制不能把实际风险内容清空。",
         [location("dimensions.py", "SE_RISK ="), location("dimensions.py", "def _safety_effect(acc, unit, obj):", last=True)]),
        ("OBS-05", "omission", ["expert_price_responsibility"],
         "明确药品价格/治疗费用协商职责漏Ec",
         "当前安排专家与企业协商本药价格及治疗费用，未要求本次成功。候选价格分支偏重‘价格协商’或确定/测算等词序，没有覆盖‘协商本药的价格及治疗费用’内容关系。",
         [location("dimensions.py", "price_action = re.search(r\"(?:现场价格协商")]),
        ("OBS-06", "omission", ["complete_explicit_article_three_dimensions"],
         "完整明确引用中疾病控制效果证据漏E",
         "确指的四段条文已完整进入SE_explicit_provided_article_condition，S/Ec得到引用正判。‘应提供患者疾病控制效果证据’是E实质内容，但新SE_EFFECT未覆盖疾病控制效果表达，E仍0；不是引用加载失败。",
         [location("dimensions.py", "SE_EFFECT ="), location("relations.py", "relation_subtype='SE_explicit_provided_article_condition'")]),
    ]
    observed_findings = []
    for fid, kind, names, title, reason, code_locations in executed:
        observed_findings.append({"finding_id": fid, "evidence_level": "executed_presealed_synthetic_control",
                                  "kind": kind, "title": title, "reason": reason,
                                  "synthetic_case_names": names, "code_locations": code_locations,
                                  "observed": [{"name": n, "expected": cases[n]["expected"],
                                                "observed": cases[n]["observed"], "mismatches": cases[n]["mismatches"]}
                                               for n in names],
                                  "real_record_labels_examined": False, "candidate_edit_requested_here": False})
    static_findings = [
        {"finding_id": "STATIC-01", "evidence_level": "read_only_code_inference_not_additional_execution",
         "kind": "scope_widening_risk", "title": "明确款次被丢弃后整条消费",
         "reason": "ARTICLE_REFERENCE捕获条号与款号，但新增循环只把条号存入requested，随后引用同条全部cited_article成员。该新路径没有按当前明确款次选择有限成员，因此兄弟款独立风险/效果/费用有被吸入的风险；旧_operative_references的款次选择不能证明新路径同样有界。",
         "code_locations": [location("relations.py", "for number, clause in refs:"),
                            location("relations.py", "value = ordinal_number(number)"),
                            location("relations.py", "completeness_scope='all original delivered cited_article members; no additional file reading'")],
         "additional_control_executed": False},
        {"finding_id": "STATIC-02", "evidence_level": "read_only_code_inference_not_additional_execution",
         "kind": "incomplete_scope_acceptance_risk", "title": "连续已供编号与末句句号不足以证明全文闭合",
         "reason": "新article路径按已供unique长度检查1..n编号，末项以句号结尾即可声明full_scope。没有核见原件末边界或全成员库存，也不验证SHA绑定全文里还存在未供最后成员。本次缺末项对照因剩余最后一项是分号而正确停为null；若各成员均为独立句号，该通过结果不能证明一般缺末项均停。不能把该风险说成本次已经发生的正式误判。",
         "code_locations": [location("relations.py", "list(range(1,len(unique)))"),
                            location("relations.py", "not norm(unique[-1]['text']).endswith('。')"),
                            location("relations.py", "completeness_scope='all original delivered cited_article members; no additional file reading'")],
         "relevant_executed_case": "missing_final_article_member", "additional_control_executed": False},
        {"finding_id": "STATIC-03", "evidence_level": "read_only_code_inference_not_additional_execution",
         "kind": "scope_widening_risk", "title": "同段共现替代精确指代目标",
         "reason": "新增_bounded_content以当前触发串和整个paragraph中的另一串共现建立关系，shared_predicate为整段；S/E/Ec消费者又将整个继承段与当前合并匹配。虽然比全文或任意preceding_paragraph有限，部分触发串没有核定当前指代与该风险/效果/费用是同一对象，混合段内无关兄弟义务仍可能被继承。本次两个preceding_paragraph反例没有激活该同段路径，不能证明所有同段兄弟反例已受控。",
         "code_locations": [location("relations.py", "def _se_bounded_content(self):"),
                            location("relations.py", "shared_predicate=raw, member_text=self.text, not_whole_source_inheritance=True"),
                            location("dimensions.py", "scope = text + (\"。\" + unit.inherited if direct_parent else \"\")")],
         "additional_control_executed": False},
        {"finding_id": "STATIC-04", "evidence_level": "read_only_code_inference_not_additional_execution",
         "kind": "source_scope_validation_risk", "title": "章节容器边界只检查存在",
         "reason": "新section路径要求child_groups含structure_boundary，但没有从边界组解析有序ID并核实实际文本、来源SHA、component与明确地址对应。full_scope和finite_reference_depth=2是结果说明字段，不能补足尚未核定的边界关系。此路径未在20对照中构造/执行，因此仅列静态风险。",
         "code_locations": [location("relations.py", "boundary = [g for g in groups if g.get('position') == 'structure_boundary']"),
                            location("relations.py", "reference_address=container['structure'].get('reference_address')"),
                            location("relations.py", "full_scope=True, finite_reference_depth=2")],
         "additional_control_executed": False},
    ]
    guards = [
        "新增关系代码没有文件读取、语料扫描、记录ID或答案表输入；仅消费已供语境。",
        "SE新增parent_predicate/cited_standard声明affected_dimensions限S/E/Ec；judge对I/F消费加过滤。",
        "_generic关闭S/E/Ec旧通用入围，_se_allowed排除named_mechanism/policy_explanation及任意price_arrangement，保留已绑定同版价格节点旧路径。",
        "两个无关preceding_paragraph兄弟风险/费用控制均输出全0；未以相邻背景直接纳入。",
        "无标准治疗身份、孤立PK/PD档案目录、行政受理/场租费及支付字段仅格式控制均符合固定0。",
        "风险条件/例外、安全性不确定性、药物作用反应人群比较、疾病控制要求未满足、否定生存改善和治疗预算影响控制符合预期。",
    ]
    findings = {"status": "independent_candidate_review_completed_with_semantic_failures_and_scope_risks",
                "candidate_seal_sha256": result["summary"]["inputs"]["candidate_seal"]["sha256"],
                "manual_sha256": binding(MANUAL)["sha256"], "executed_control_summary": result["summary"],
                "executed_findings": observed_findings, "static_scope_findings": static_findings,
                "observed_guards": guards,
                "conclusion": "现封存候选在有限对照中仍有语义过纳入、遗漏及引用范围静态风险，不能以已有自测或800回放替代该独立语义审查。该报告支持另存通用修复候选及未来独立复审，不修改或重判既有冻结输入/结果。",
                "is_formal_accuracy_result": False, "is_human_reference": False,
                "additional_execution_beyond_fixed_20": False, "acceptance_threshold_added": False}
    write_new("findings.json", findings)

    diffs = []
    for name in ("dimensions.py", "relations.py"):
        old, new = definitions(BASELINE / name), definitions(CANDIDATE / name)
        changed = []
        for symbol in sorted(set(old) | set(new)):
            if old.get(symbol, {}).get("ast_sha256") != new.get(symbol, {}).get("ast_sha256"):
                changed.append({"symbol": symbol, "baseline": old.get(symbol), "candidate": new.get(symbol)})
        diffs.append({"filename": name, "baseline_binding": binding(BASELINE / name),
                      "candidate_binding": binding(CANDIDATE / name), "changed_or_added_functions": changed})
    write_new("read-only-function-diff.json", {"comparison": diffs, "baseline_executed": False,
                                               "claim_of_every_baseline_behavior_unchanged": False})
    extra_inputs = ["candidate-seal.json", "manual-binding.json", "frozen-origin-bindings.json",
                    "semantic_selfcheck.py", "se_predicates.inc", "se_relations.inc",
                    "dimensions.py.patch", "relations.py.patch"]
    inputs = result["summary"]["inputs"]["sealed_manual_and_code"]
    inputs.extend(binding(CANDIDATE / n) for n in extra_inputs)
    inputs.extend(binding(BASELINE / n) for n in ("dimensions.py", "relations.py"))
    paths = {x["path"]: x for x in inputs}
    write_new("audited-input-bindings.json", {"inputs": list(paths.values()),
                                              "verification": "actual_SHA256_and_bytes_read; candidate_seal_members_verified_before_execution",
                                              "semantic_selfcheck_source_read": True,
                                              "owner_selfcheck_result_files_read": False,
                                              "owner_800_or_77_labels_read": False})
    final_binding = []
    seal = json.loads((CANDIDATE / "candidate-seal.json").read_text())
    for expected in [seal["manual"], *seal["code"]]:
        actual = binding(Path(expected["path"]))
        if actual["sha256"] != expected["sha256"] or actual["bytes"] != expected["bytes"]:
            raise ValueError("candidate or manual changed during audit: " + expected["path"])
        final_binding.append(actual)
    write_new("readback-scope.json", {
        "candidate_unchanged_after_audit": True, "final_bound_members": final_binding,
        "actual_reading": {"new_SE_predicate_and_relation_functions": "complete new function bodies, patch files and call/filter integration read",
                           "baseline": "read-only AST comparison of full baseline files; selected finite source/reference/object and evidence validators read",
                           "manual": "current complete S/E/Ec sections and relevant common/finite relation boundaries read",
                           "synthetic_controls": "20 complete current propositions plus all supplied contexts constructed and read before execution",
                           "real_materials": "none used in this SE/Ec control execution"},
        "execution": {"synthetic_case_N": 20, "execution_attempt_N": 1,
                      "current_text_and_all_decisions_saved": True, "relation_and_source_requests_saved": True,
                      "semantic_mismatches_saved": 8, "technical_exception_N": 0,
                      "evidence_validator_passed_N": 20, "owner_selfcheck_or_replay_called": False,
                      "formal_rule_or_LLM_runner_called": False, "new_Codex_CLI_started": False},
        "not_claimed": ["20 controls are exhaustive", "formal human reference or accuracy", "800 independent validation complete",
                        "all source files semantically read", "all article/section completeness or sibling references are safe"],
        "preserved": ["candidate v1 modules and seals", "manual and releases", "all raw and prior predictions", "earlier statistics and audits"]})
    readme = """# S/E/Ec 候选独立审查

对已封存 v1 候选先固定 20 个合成对照，再执行一次：13 项符合预期，7 项不符合（8 个维度差异），无技术异常。20 项原文/引文结构校验通过。全部固定预期、当前全文、五维决策、关系和材料请求均保存；没有调整期望、修候选或再跑真实800/77。

实际发现安全性信息表纯文件命名、ADR报告纯上传和印发宗旨的过度纳入；获益超过风险的否定证据句、PK/PD明确毒性用途、药价费用协商职责及确指完整条文中的疾病控制效果证据存在遗漏。见 `findings.json` 的执行证据，原始结果在 `execution-results.json` / `.jsonl`。

另列静态引用范围风险：新增引用路径丢弃明确款次后按整条消费；连续已供编号和末句句号不等于核见原件完整末边界；同段共现与整段继承可能吸入无关兄弟谓词；章节容器只检查边界组存在。这些未追加执行例，不冒称已发生的正式误判。两项无关相邻语境反例和一个以分号暴露缺末项的null对照通过，只支持这些有限构造。

`controls-fixed-before-execution.json` 与 `pre-execution-seal.json` 为运行前固定输入，前者SHA为 de9674155d9cb449009ad8021adc9e40bfb0d31f6af7e18886acc2598d9066b4。`audited-input-bindings.json` 绑定实际代码与手册，`manual-basis-quotes.json` 保存连续原句和位置，`readback-scope.json` 明确读取/执行范围。封存 v1 代码和共同手册运行前后SHA均一致。

本目录是独立开发语义审查；合成预期不是真人参照，13/20不是正式准确率。不读取主全量部分标签，不启动新Codex CLI，不修改旧材料/手册/预测。新增检查可支持另存通用修复候选及未来独立复审，不为任何指标过线改变判断。
"""
    with (HERE / "README.md").open("x", encoding="utf-8") as f:
        f.write(readme)
    members = [binding(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "output-seal.json"]
    write_new("output-seal.json", {"status": "sealed_independent_read_only_semantic_candidate_audit",
                                  "output_members": members, "self_excluded": True,
                                  "candidate_seal_sha256": result["summary"]["inputs"]["candidate_seal"]["sha256"],
                                  "manual_sha256": binding(MANUAL)["sha256"],
                                  "synthetic_case_N": 20, "pass_N": 13, "fail_N": 7,
                                  "formal_results_created": False, "human_results_created": False})
    print(json.dumps({"output_root": str(HERE), "output_member_N": len(members),
                      "seal": binding(HERE / "output-seal.json"),
                      "manual_quote_match_N": len(quotes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
