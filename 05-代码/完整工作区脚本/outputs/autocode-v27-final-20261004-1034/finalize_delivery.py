"""Write a concise explanation tied to the final saved numerical results."""
import json
from pathlib import Path
from datetime import datetime,timezone
import hashlib

ROOT=Path(__file__).resolve().parent
metrics=json.loads((ROOT/'metrics.json').read_text())
release=json.loads((ROOT/'release_manifest.json').read_text())
context=json.loads((ROOT/'context_repair_audit.json').read_text())
names={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}

text=[
    '自动规则五维修订说明',
    f"版本：{release['version']}；实际全量执行结束时间：{release['completed_at']}",
    '',
    f"已按 CAL-5D v1.3 固定定义逐项审查五个维度，完成全量 {metrics['n']} 条重跑。自动规则待定 {metrics['pending_n']} 条，较 v26.2 有 {metrics['changed_units']} 条至少一个维度变化。",
    f"通过 {release['semantic_regression_tests_passed']} 项回归测试；验证 {release['evidence_checks']['literal_evidence_spans']} 个原文证据位置与 {release['evidence_checks']['literal_suppression_spans']} 个排除证据位置。",
    '',
    '本轮修订内容',
    '安全性和有效性：明确药物对象、药物风险/临床效果及同段缩写依赖；排除培训、软件、手术、纯档案操作等不同对象；保留否定结果和实质资料要求。',
    '经济性：按价格、治疗成本、支付标准、报销与费用责任、销售量额、经济评价及预算/基金影响逐组处理；纠正枚举、修饰语、费用指代和程序性提及边界。',
    '创新性：区分药物属性、注册创新分类、具体改良、研发支持、专利/数据保护与创新资格；资格判定同时保留当前内容和已核验适用范围。',
    '公平性：区分药物获取/保障、患者负担、具体用药管理难度与公平性资料要求；避免把人群名、目录身份或“双通道”名称自动变为公平性。',
    '',
    '上下文修复',
    f"补齐 {context['repaired_count']} 条必需条件列表，并对同一来源中 {context['innovation_scope_component_count']} 条突破性治疗分支补入已核验创新/改良适用范围。单元原文和编号均未改动。",
    f"本轮分别运行原输入与补全输入；上下文补全单独改变 {len(release['context_only_label_changes'])} 条标签状态/标签。逐条记录见 release_manifest.json。条件列表仅用于确认理解完整，不整段复制维度。",
    '',
    '指标如何计算',
    'A/C 为按人工编码标准执行的 AI 编码员首次结果，不是真人金标准。本轮未修改参照标签，未重跑或修改 LLM。',
    '每个样本组、维度、参照下，旧自动规则、新自动规则和原 LLM 使用同一共同可判子集；历史待定不填0。H427 与 current1268 分开报告，不把全量4924当作有A/C比较的样本量。',
    'Cohen κ=(观察一致率−偶然一致率)/(1−偶然一致率)。精确率=TP/(TP+FP)，召回率=TP/(TP+FN)，F1=2TP/(2TP+FP+FN)。这些指标相对于所列A/C参照。',
    'κ 已用独立整数分数计算核对；Excel 中再依据混淆计数计算，并与 Python 结果逐项核对。',
    '',
]
for scope in ('H427','current1268'):
    text.append(scope+'：未加权的共同可判比较')
    for d,name in names.items():
        pieces=[]
        for ref in ('A','C'):
            row=metrics['comparisons'][scope]['references'][ref][d]
            old=row['methods']['rules_v26_2']['common_unweighted']
            new=row['methods']['rules_v27']['common_unweighted']
            score=new['conditional_scores']
            pieces.append(f"{ref}: n={row['common_n']}, κ {old['binary_agreement']['kappa']:.3f}→{new['binary_agreement']['kappa']:.3f}, 精确率 {score['precision']:.1%}, 召回率 {score['recall']:.1%}, F1 {score['f1']:.1%}")
        text.append(name+'；'+'；'.join(pieces))
    text.append('')
text += [
    '结果的使用范围',
    '本轮代码修订和全量执行已完成。语义组检查与回归测试通过不等于识别完美，也不自动证明测量效度。',
    'H427 和 current1268 已暴露为开发材料，这些数值只能用于描述修订后与原参照的一致性，不能写为新的独立验证通过。规则版本中的任何升降均如实保留。',
    '规则匹配仍可能遗漏未覆盖的改写、隐含指代、复杂并列和长距离对象关系。各模块 coverage 文件列明限制。',
    '修订过程中对独立发现的语义缺陷做了纠正；首次全量结果与对应代码已保存在 iterations/before_final_semantic_audit，不删除中间版本。',
    '',
    '交付与复现',
    '自动规则五维修订结果-v27.xlsx：总览、公式计算及4924条原文/新旧标签/A/C标签/证据。',
    'policy_coding_v27.py：总入口；rules_se.py、rules_ec.py、rules_if.py：五维判定模块。',
    'release_manifest.json：代码、输入、输出指纹与执行记录；metrics.json：完整计数、覆盖率、未加权及历史权重描述结果。',
    'comparison_masks.json：每个表格实际使用的条目；label_changes.json：旧规则与最终规则的逐条变更。',
    '现有工作区复现：先运行全部 test*.py，再运行 run_release.py --predict，最后运行 run_release.py --compare。源数据和历史参照保持在相邻版本目录。',
]
(ROOT/'自动规则修订说明.txt').write_text('\n'.join(text)+'\n')
outputs=['自动规则五维修订结果-v27.xlsx','自动规则修订说明.txt','all_predictions.jsonl','metrics.json','release_manifest.json','analysis_binding.json']
binding={'finalized_at':datetime.now(timezone.utc).isoformat(),'version':release['version'],
         'files':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in outputs}}
(ROOT/'delivery_binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')
print('Final delivery explanation and checksums written.')
