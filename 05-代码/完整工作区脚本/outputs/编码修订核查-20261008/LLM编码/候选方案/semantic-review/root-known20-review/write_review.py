"""Record root's actual source-based review; never modify model/reference labels."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE.parents[3]
SOURCE = BASE / 'semantic-review/interim_candidate07_mandatory30_REDACTED_PRIVATE.json'
OUT = Path(__file__).resolve().parent / 'root_20_unit_full_dimension_review.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not OUT.exists()
    assert sha(SOURCE) == '98164ef939b2f2834b3c5559534eb97a73e232e10b0ad5ef7e38bf024da34f1d'
    rows = {r['id']: r for r in json.loads(SOURCE.read_text())['rows']}
    gates_path = BASE / 'predeclared_acceptance_PROPOSED.json'
    gates = json.loads(gates_path.read_text())
    # Every note below was determined by reading the full current unit, all
    # unique given context texts, and the actual five-dimensional output.
    notes = {
        '00663': '临床获益、创新程度及基本目录暂时排除分别有E/I/F依据；目录定位本身不补费用责任Ec。',
        '00964': '当前仅组织现场价格协商，未提出价格取值/调整、经济评价或费用责任；Ec理由正是谈判程序，违反手册37行的排除边界。不能由上一段费用测算补入。',
        '01264': '确定限定支付范围支持F/access；参照药身份不自动E，支付范围本身不自动Ec。',
        '01432': '第七条第一款实际要求安全性/有效性全部试验数据，支持S/E；改良分类及专有数据期限支持I。质量可控性提及不另外自动变成质量安全依据。',
        '01562': '核验父句明确全部条件决定简易续约两年；预算条件支持Ec并参与保障延续F，不是孤立办理资格。',
        '01616': '诊疗方案是降价例外对象的既有身份，不是当前治疗推荐E；基金预算与不降价支持Ec，当前续约安排可按保障连续解释F。',
        '01765': '安全评价重点与治疗获益分别支持S/E；一般指导宗旨未规定实体创新支持，I0成立。F理由额外写尚待满足，现句仅迫切需求与尽早上市，是否已明确实际治疗缺口需与一般疾病需求区分，不强行归为已证实获取。',
        '01768': '语境消解个性化问题来自安全资料准备，但当前仅规定沟通形式与未来指南维护，没有安全评价/安全证据要求。S1仍是主题传播；boundary_note不能撤销预声明错误检查。',
        '01955': '适应症或功能主治发生重大变化是当前明确的相对既有产品属性改变；与申请动作并列，不能全部降为程序身份。I0违反共用说明14行，不要求出现创新字样或已证明优效。',
        '02086': '明确以下条件及已给定完整列表，基金支出、预算和价格条件支持Ec；续约两年支持F。未要求删Ec，避免重现旧审查误判。',
        '02220': 'CDE专门提供创新药研发全过程风险管理技术指导，当前支持内容和创新研发对象明确，S及I/research_support成立，不能把全部指南形式排除。',
        '02364': '机构采购、检查和验收分工未表达质量安全评价、实际取药渠道、患者费用或创新内容，全0具有依据。',
        '02830': '药物警戒和风险最小化直接支持S；申请人义务不是I，试验可靠性不是E，受试者一般权益不是本研究F。',
        '02845': '药物警戒识别管理风险支持S；一般试验安全义务不自动I/F，其他维度无当前依据。',
        '03261': '当前医保谈判药品协议两年有效期支持保障连续F；同段未来价格调整没有被当前期限句引用，不自动Ec。',
        '03471': '一般减量/调量未说明管理障碍、监测负担、药物损害或创新改变，全0成立。',
        '03704': '药品目录选择直接受医保基金约束，Ec1成立而基金安全不属于S；雪中送炭的抽象保障含义保留解释边界，不借此伪造具体药品覆盖。',
        '03712': '当前给予1类新药谈判机会，但给定材料未说明1类注册类别的实际创新含义；一般创新支持背景不能替代具体对象的创新依据。I/research_support1不满足预声明保留I0检查。Ec降幅条件成立，申请重新谈判不自动F。',
        '03866': '当前仅要求未载明规格提交书面申请，未决定纳入；下一句支付标准不能复制到当前申请动作，全0成立。',
        '04894': '医疗机构与药店之间实际电子处方流转渠道支持F/access；信息平台形式不消除取药关系，不从后句基金监管复制Ec/S。',
    }
    unsupported = {'00964': ['Ec'], '01768': ['S'], '01955': ['I'], '03712': ['I']}
    boundary = {'01765': ['F'], '03704': ['F']}
    records = []
    for suffix, note in notes.items():
        rid = 'RECODE25-' + suffix
        row = rows[rid]
        records.append({'id': rid, 'current_unit_and_all_unique_masked_context_texts_actually_read': True,
                        'complete_actual_five_dimension_row_reasons_evidence_subtypes_quality_and_issues_read': True,
                        'actual_labels_UNCHANGED': row['candidate07_intact_actual_row']['labels'],
                        'per_dimension_review': {d: 'UNSUPPORTED_UNDER_FIXED_MANUAL' if d in unsupported.get(suffix, [])
                                                 else 'BOUNDARY_OR_ADDITIONAL_SUPPORT_CHECK' if d in boundary.get(suffix, [])
                                                 else 'SUPPORTED_ON_AVAILABLE_MASKED_MATERIAL'
                                                 for d in ('S', 'E', 'Ec', 'I', 'F')},
                        'source_based_review_note': note,
                        'metadata_review': 'F/I subtypes and S quality were actually reviewed with their source, not inferred merely from agreement.'})
    checks = []
    for group, field in [('eight_clear06_error_cells_WORKING_NOT_GOLD', 'reviewer_manual_judgment_not_gold'),
                         ('nine_fixed06_working_cells_to_preserve', 'reviewer_manual_judgment_not_gold'),
                         ('additional_independently_identified_known_items_NOT_GOLD', 'working_judgment_not_gold')]:
        for item in gates[group]:
            dim = item.get('dimension', item.get('target_dimension'))
            actual = rows[item['id']]['candidate07_intact_actual_row']['labels'][dim]
            checks.append({'group': group, 'id': item['id'], 'dimension': dim,
                           'predeclared_working_judgment_not_gold': item[field], 'actual07': actual,
                           'passes_fixed_cell_check': actual == item[field]})
    assert len(records) == 20 and len(checks) == 19
    assert {r['id'] + ':' + r['dimension'] for r in checks if not r['passes_fixed_cell_check']} == {
        'RECODE25-00964:Ec', 'RECODE25-01768:S', 'RECODE25-01955:I', 'RECODE25-03712:I'}
    paths = [SOURCE, gates_path, BASE / 'semantic-review/interim_mandatory30_projection_metadata.json',
             BASE / 'design_freeze.json', Path(__file__),
             ROOT / 'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
             ROOT / 'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md']
    result = {'status': 'ROOT_COMPLETE20_SEMANTIC_REVIEW_FOUR_REQUIRED_CHECKS_FAIL_NOT_ADOPTION',
              'created_at_UTC': datetime.now(timezone.utc).isoformat(),
              'review_identity': 'Root AI review of existing development material; not a new blind human validation.',
              'n_units': 20, 'n_dimensions_actually_reviewed': 100,
              'original_AB_T_labels_or_scores_read_for_this_review': False,
              'new_reference_or_machine_label_written': False,
              'formal15_audit_and_formal30_exact_match_still_required': True,
              'predeclared_required_cells': checks, 'required_cell_pass_n': 15, 'required_cell_fail_n': 4,
              'confirmed_nonadoption_blockers': ['00964 Ec regression', '01768 S persistent error',
                                               '01955 I additional required check not resolved', '03712 I regression'],
              'complete240_or106_semantic_review_claimed': False,
              'protected_context_limit': 'Only author-provided mechanically redacted projection read. Full-normalized matching is not proof against all partial/paraphrased exposure. No missing masked content was reconstructed.',
              'source_bindings': [{'path': str(p.resolve()), 'sha256': sha(p)} for p in paths],
              'records': records}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(OUT), 'sha256': sha(OUT), 'units': 20, 'required_cells_pass': 15, 'required_cells_fail': 4}, ensure_ascii=False))


if __name__ == '__main__':
    main()
