"""Constructed module controls, not independent validation or source material."""
import json, sys, hashlib
from pathlib import Path
R = Path(__file__).resolve().parent
sys.path.insert(0, str(R/'runtime-v36.1'))
from rules_semantic_v36 import revise
from rule_support import rebuild

CASES = [
 ('project-function', '本试点工作旨在鼓励创新药向临床领域布局，聚焦并解决源头性创新罕见疾病药物研发中的科学问题。', {'I'}),
 ('project-function-not-outcome', '试点工作的核心目的在于鼓励创新药研发，关注并探讨解决源头性创新药物研发过程中的科学问题。', {'I'}),
 ('project-slogan', '本试点工作旨在鼓励创新药向临床领域布局。', set()),
 ('project-filing', '本试点工作旨在鼓励创新药研发，申请人应在五日内提交申请表。', set()),
 ('non-innovation-project', '本试点工作鼓励药物研发，帮助解决普通药物研发中的科学问题。', set()),
 ('technical-guidance', '专门起草了《创新药研发期间风险管理技术指导原则》，为临床试验各方将风险管理贯穿药物研发全过程提供指导。', {'I'}),
 ('technical-title-only', '现发布《创新药研发期间风险管理技术指导原则》。', set()),
 ('technical-filename', '文件名为“起草了《创新药风险管理技术指导原则》，为临床试验风险管理提供指导”。', set()),
 ('technical-filing-only', '制定《创新药研发技术指南》，为临床试验申请人填表上传报送提供指导。', set()),
 ('technical-generic-purpose', '起草了《创新药研发技术指南》，为提高工作质量提供指导。', set()),
 ('technical-non-innovation', '起草了《普通药品风险管理技术指导原则》，为临床试验风险管理提供指导。', set()),
 ('drug-benefit', '富集策略使患者最大可能地从试验药物中获益。', {'E'}),
 ('welfare-benefit', '患者从研究交通补助中获益。', set()),
 ('valid-data', '验证试验药物数据的有效性。', set()),
 ('effective-recipients', '确保药物上市后，目标患者接受合理有效的治疗。', {'E'}),
 ('surgical-recipients', '确保手术实施后，目标患者接受合理有效的治疗。', set()),
 ('comparator-choice', '关注阳性对照药是否代表患者的最佳治疗选择。', {'E'}),
 ('comparator-design', '选择阳性对照药并计算样本量。', set()),
 ('dose-modification', '在对给药频次进行改良时，应考虑患者用药习惯。', {'I'}),
 ('dose-record', '在记录给药频次时，应考虑患者用药习惯。', set()),
 ('dose-convenience', '选择便于记忆的给药频次。', set()),
 ('innovation-enumeration', '聚焦创新程度高、临床价值大，但暂时未获医保保障的药品。', {'I'}),
 ('innovation-name', '创新药目录内的药品按时提交材料。', set()),
 ('innovation-process', '创新程度高的生产方法生产的药品应提交材料。', set()),
 ('research-resources', '优化审评审批资源配置，推动提升创新药临床研发质效。', {'I'}),
 ('research-routine', '优化审批表单填写格式，推动提升创新药临床研发质效。', set()),
 ('research-title', '发布《关于优化创新药临床研发资源配置的公告》。', set()),
 ('research-team-inferred', '药审中心根据适应症和任务特点组建审评团队。', set()),
 ('shortage-drug', '对于明确为市场短缺且鼓励研发申报的儿童用药品实行优先审评。', {'F'}),
 ('shortage-staff', '优先解决药品审评人员的市场短缺问题。', set()),
 ('urgent-foreign', '对于临床急需境外已上市境内未上市的罕见病药品实行优先审评。', {'F'}),
 ('foreign-newness', '本品为境外已上市境内未上市的药品。', set()),
 ('urgent-disease', '创新药面向临床治疗需求迫切的疾病。', set()),
 ('no-standard', '选择安慰剂对照药时，应确定该适应症在临床中确无标准治疗。', {'F'}),
 ('ordinary-control', '选择安慰剂对照药时，应按标准治疗流程执行。', set()),
 ('drug-opportunity-loss', '患者无法耐受药物的不良反应，可能使患者失去治疗机会。', {'F'}),
 ('separate-surgery-loss', '研究药物设计。外科手术失败使患者失去治疗机会。', set()),
 ('commercial-success', '协商成功的药品纳入商保创新药目录，并签署协议。', {'F'}),
 ('commercial-application', '药品可以申报纳入商保创新药目录。', set()),
 ('commercial-scope-exclusion', '基本目录已有同类保障的品种，不会因为价格高而被纳入商保创新药目录。', {'F'}),
 ('renewal-condition', '谈判药品均须申报，不申报的药品无法续约。', {'F'}),
 ('renewal-opportunity', '谈判药品续约失败后，可以申请重新谈判。', set()),
 ('agreement-duration', '原则上谈判药品协议有效期为两年。', {'F'}),
 ('filing-deadline', '谈判药品协议签署申请应在两年内提交。', set()),
 ('payment-channel', '谈判药品通过两个渠道供应，并同步纳入医保支付的机制。', {'Ec'}),
 ('payment-settlement', '稳妥推进将谈判药品纳入异地就医直接结算范围。', {'Ec'}),
 ('payment-file', '上传文件名称为“谈判药品纳入异地就医直接结算范围”。', set()),
 ('no-drug-payment', '将交通服务纳入异地就医直接结算范围。', set()),
]

ROWS=[]
def run(name, text, expected, extra=None, seed=None):
    rec={'unit_text':text, **(extra or {})}
    evidence=[]
    for dim, rule, quote in seed or []:
        a=text.index(quote)
        evidence.append({'dimension':dim,'rule':rule,'start':a,'end':a+len(quote),
                         'text':quote,'matching_text':quote,'subtype':'access' if dim=='F' else None})
    out=rebuild(revise(rec,{'evidence':evidence,'suppressions':[],'judgement_status':'determined'}))
    got={d for d,x in out['labels'].items() if x}
    assert got==expected,(name,got,expected,out)
    for e in out['evidence']+out['suppressions']:
        if 'start' in e:assert text[e['start']:e['end']]==e['text']
    ROWS.append({'name':name,'constructed_text':text,'expected':sorted(expected),
                 'actual':sorted(got),'pass':True,'context_fixture':extra,'seed_evidence':seed})

for args in CASES:run(*args)
run('drop-urgency-only','药品用于治疗需求迫切的疾病。',set(),seed=[('F','V27_F_unmet_treatment','治疗需求迫切')])
run('retain-independent-gap','药品用于治疗需求迫切且无药可治的患者。',{'F'},seed=[('F','V27_F_unmet_treatment','治疗需求迫切'),('F','V27_F_unmet_treatment','无药可治')])
run('disease-counterfactual','严重影响生存质量是指如果得不到有效治疗将导致残疾。',set(),seed=[('E','E06','有效治疗')])
run('independent-efficacy','严重影响生存质量是指如果得不到有效治疗将导致残疾；该药改善患者疗效。',{'E'},seed=[('E','E06','有效治疗'),('E','E01','疗效')])
run('rights-categories','药品的数据保护范围包括用于证明安全性、有效性的全部试验数据。',set(),seed=[('S','S01','安全性'),('E','E01','有效性')])
run('independent-content-demand','药品的数据保护范围包括用于证明安全性的全部试验数据；另须提交药物有效性资料。',{'E'},seed=[('S','S01','安全性'),('E','E01','有效性')])
run('pricing-premise','新纳入《药品目录》的药品同步确定支付标准。',{'Ec'},seed=[('F','V27_F_quoted_directory_decision','纳入《药品目录》'),('Ec','V27_Ec_payment_standard','支付标准')])
run('admission-decision','确定支付标准后，将该药品纳入《药品目录》。',{'F','Ec'},seed=[('F','V27_F_quoted_directory_decision','纳入《药品目录》'),('Ec','V27_Ec_payment_standard','支付标准')])
run('filing-premise','谈判药品无论是否申请调整支付标准和支付范围，均須申报。',set(),seed=[('Ec','V27_Ec_payment_standard','支付标准')])
run('independent-payment','谈判药品无论是否申请调整支付标准和支付范围，均須申报；应下调支付标准。',{'Ec'},seed=[('Ec','V27_Ec_payment_standard','支付标准'),('Ec','V27_Ec_payment_standard','下调支付标准')])

exit_parent={'paragraph_id':'constructed_parent','text':'《药品目录》内的药品，有下列情况之一的，经评审后，直接调出《药品目录》：','pages':[]}
run('exit-child','（三）风险大于收益的药品；',{'F'},{'verified_parent_context':[exit_parent]})
run('application-child','（三）风险大于收益的药品；',set(),{'verified_parent_context':[{'paragraph_id':'constructed_parent','text':'以下药品可以提出目录调整申请：','pages':[]}]})
run('unmet-information','• 未满足的临床需求。',{'F'},{'verified_parent_context':[{'text':'一、目标适应症诊疗情况','paragraph_id':'scope','pages':[]},{'text':'本节请简要总结以下内容：','paragraph_id':'request','pages':[]}]})
run('unbound-information','• 未满足的临床需求。',set())
level='要根据基金承受能力，确定适宜的保障水平。'
run('bound-guarantee-level',level,{'F'},{'paragraph_context':[{'paragraph_id':'same','text':'对谈判药品可探索建立单独的药品保障机制。'+level,'pages':[]}]})
run('unrelated-guarantee-level',level,set(),{'paragraph_context':[{'paragraph_id':'same','text':'对谈判药品建立保障机制。另设员工住房福利。'+level,'pages':[]}]})
endpoint='该研究的主要终点通过病历审查进行验证。'
run('effect-endpoint',endpoint,{'E'},{'paragraph_context':[{'paragraph_id':'same','text':'某药上市后研究评价其减少骨折的有效性和安全性。该研究遵循良好实践，研究方案已公开。'+endpoint,'pages':[]}]})
run('generic-study-endpoint',endpoint,set(),{'paragraph_context':[{'paragraph_id':'same','text':'某药上市后开展研究。'+endpoint,'pages':[]}]})
run('intervening-study-endpoint',endpoint,set(),{'paragraph_context':[{'paragraph_id':'same','text':'某药研究评价其临床获益。另一项研究评估机构服务。'+endpoint,'pages':[]}]})

out={'all_checks_pass':True,'n':len(ROWS),'scope':'constructed module controls; source validation is separately exercised by full production run','not_independent_validation':True,'rows':ROWS,'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(R/'constructed_semantic_controls_v36.1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(len(ROWS),'constructed semantic controls passed')
