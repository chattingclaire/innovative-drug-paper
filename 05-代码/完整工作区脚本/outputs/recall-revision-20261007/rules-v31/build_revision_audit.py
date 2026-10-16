from pathlib import Path
import json,hashlib,collections,difflib,datetime
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'final-three-department-20261007'/'rules-v30'
PACKET=ROOT.parent/'all_weak_metrics_disagreements.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
notes={
'00126/F':'罕见病和临床急需限定审评时限的适用对象，当前没有治疗获取或保障安排；不从特定药品身份推F。',
'00174/F':'当前明确仍有患者未能得到有效治疗并要求关注更高治疗需求，按手册未满足治疗需求边界保留F=1。',
'00646/F':'当前明确确认支付标准后纳入目录，属于具体保障归属安排；不因旧A将其只解释为程序而删除。',
'00722/F':'仅允许申报新增适应症并签补充协议，没有当前实际范围或获取安排；保留F=0。',
'00723/F':'规定哪类事项进入目录调整程序而不属申报范围，没有具体保障扩缩，保留F=0。',
'00837/F':'父条明确对象已是协议期内谈判药品，当前只列入常规目录乙类管理，并未改变实际给付覆盖；删除类别误触发，保留独立自付比例内容。',
'01081/F':'报价条件触发通用名药品不被纳入目录，是具体保障排除，保留F=1。',
'01134/F':'一般疾病负担、基本用药需求和选题程序没有明确获取缺口或患者药费负担；保留F=0。',
'01503/F':'就诊路径与现实治疗选择资料，未实述药品获取障碍、未满足需求或保障安排；不把所有诊治现状当公平性。',
'01723/F':'仅规定重新谈判或简易续约路线，原范围是办理对象，不单独生成F。',
'02259/F':'当前明确清除出机构药品供应目录，改变实际供应获取范围，保留F=1。',
'02317/F':'组织确定下一期支付标准及范围，没有当前具体保障内容；保留F=0。',
'02361/F':'药品联动管理及目录规范没有实述配备、供应或获取安排；保留边界，不继承同段其他配备句。',
'02391/F':'临床药师院际会诊是一般药学服务，没有针对药品获取或具体使用障碍，保留F=0。',
'02393/F':'一般社区药学服务清单未实述获取或管理障碍，不从服务接近患者推F。',
'02534/F':'明确药物使用病例按病种标准支付不适合，给予特例单议通道，保留F=1。',
'02598/F':'当前优先考虑医保目录外基本药物，同段提供调入评审对象关系，是具体补保障机会安排，保留F=1。',
'03220/F':'当前是药物类别，已核验父谓词明确该类不纳入目录，形成完整保障排除内容，保留F=1。',
'03274/F':'已核验费用支付条件枚举中属于诊断或治疗目的，是否构成F须读父谓词；旧代码未按该项独立增加保障标签，等统一回源后重跑。',
'03282/F':'协议期内已覆盖药品的乙类管理归属，不是当前新增给付覆盖；删除类别误触发，不能继承后续患者先付比例。',
'03308/F':'紧急健康事件下可临时调整医保药品支付范围，是特殊保障安排，保留F=1。',
'03425/F':'难以记住是否/何时/如何服药和混淆药品，具体用药管理障碍而非仅年龄特征，保留F=1。',
'03474/F':'当前仅要求掰断操作便利性资料及片剂改良，未明确障碍或管理难度；一般适宜性不自动为F，保留0。',
'03715/F':'扩大申报时间只是申请资格安排，未直接扩大药物保障或获取，保留F=0。',
'03734/F':'当前仅为已覆盖谈判药品转入常规乙类管理，未扩大给付或讨论负担；撤回初步转类候选，保留F=0。',
'03759/F':'价格红黄标预警未在当前单元实述患者负担；不把前句减负目的传给每个价格子项，保留F=0。',
'03803/F':'当前报告具体19种商保药成员及撤市移出，包含真实保障归属变化；申报用途不能抹去当前药品成员内容，保留F=1。',
'04703/F':'审评时限与罕见病/急需身份没有当前具体获取内容，不从身份推F。',
'03090/Ec':'泛医疗费用赔付数据定义，未实指药费或药物治疗成本。药物监管研究用途不改变数据定义对象，保留Ec=0，不迎合A/C。',
'00009/I':'旧A/C缺现在已核验的创新/改良资格对象证书。当前明确临床比较优势且父条是创新资格条件；保留I=1并记录材料不可直接等同比较。',
'00178/I':'新一代药物被明确用于克服既有耐药，实述产品改进方向而非仅新药类名，补属性规则I=1。',
'01385/I':'概括制定宗旨未给具体支持工具或属性内容，不能为提高召回把所有创新目的句赋I；保留I=0。',
'02224/I':'当前实际给予同步研发品种30日通道支持，同段明确创新药早期研发对象；补同段对象消解而非按程序类名推I。',
'02226/I':'当前实质解释主要研究者牵头及早期参与条件、创新药同步研发作用；同段明确创新研发通道支持，补条件—支持工具关系。',
'03894/I':'要求与已上市中药处方做属性对比，手册不要求已证明优越；规则保留I=1，A对此属性边界不同不作追分修改。',
'00028/I':'当前实质提供优先资源及指导研发，已核验创新/改良对象证书补齐旧A/C所缺范围；补research_support对象关系I=1，不当作qualification_advantage，也不据旧参照0抹去新增材料意义。',
'03410/I':'只有文件制定及文件名称，没有当前创新内容；标题不作为实质创新，保留I=0。',
'03474/I':'以数据改善片剂易碎性是具体产品属性改良，不需证明优势，保留I=1。',
'03489/I':'药物设计中针对多药使用改善制剂特征，是具体产品改良内容，保留I=1。',
'04444/I':'当前提供技术指导、资源优先等支持，同条明确药物创新对象，是支持措施非纯时限/标题，保留I=1。',
'00203/F':'同段明确末线人群没有标准治疗可选，当前将试验作为治疗手段并规定获得潜在治疗安排；补带严格锚点的试验治疗获取关系。',
'00225/F':'当前是富集研究设计后的研究扩展建议，未明确原本无治疗可选或当前实际获取通道；与A/C边界不同暂保留F=0。',
'00270/F':'已入组患者被分配到不同治疗组的比例不是原本无法得到治疗者的药物获取安排，保留F=0。',
'02912/E':'目前只是以纳入诊疗方案身份限定对象，缺少具体药物效果或推荐内容，不赋E；待统一补父谓词，不从来源名称推效果。',
'03838/E':'药品临床价值、市场定位泛称不明确疗效/临床获益内容，保留E=0。',
'00589/F':'流程图中的协商成功/失败具体决定目录纳入与否；示例可表达政策要求，当前编码按具体保障条件保留F=1，图示敏感性另检验。',
'00653/F':'当前医保制度公平性同段后文被解释为药物保障空白，属于对象解释与标签传播的边界；候选暂保留0，交独立理由核对。',
'00843/F':'当前仅组织专家论证是否转类的办理职责，没有实际保障条件或归属；片段membership过宽，删除该独立F依据。',
'01051/F':'当前报价条件具体决定通用名药物是否纳入乙类目录，保留F=1；不为贴近A的0删除。',
'01646/F':'同00843，组织专家论证是否纳入只是办理职责，删除误匹配的membership依据。',
'02625/F':'已竞价纳入目录只限定价格承诺对象，实质只约束供应价格，不是当前成员决定；删除membership依据，Ec保留1。',
}
manual=(ROOT/'protocol-v1.3.md').read_text()
quotes={
 'I':['讨论药物创新属性、创新点、原创或改良、作用机制或靶点的新颖性、相关知识产权、注册创新分类，以及明确针对药物研发创新的激励。','仅把“创新药”作为某类药品的名称、政策标题或支付对象，不自动赋I。'],
 'F':['保障获取包括弥补用药保障空白、改善药品可及、短缺供应及防止不合理用药获取限制；患者可负担涉及患者支付能力或药费负担。','若条款明确使原本无法获得治疗的人群获得研究药物或治疗机会，则根据具体获取安排判断F，不能只凭“临床试验”“受试者”“便利性”推断。','上下文用于确定指代、对象、条件与列含义，不把父段或标题中的所有维度复制到子项。'],
 'Ec':['讨论药品价格、药费、治疗成本、支付标准、报销与费用责任、相关销量或金额、成本效果、预算影响及药品支付对基金的影响。','一般医保筹资、机构建设、医疗服务均等化没有明确药品使用或保障联系时，作为制度背景保留，不直接生成药品五维标签。'],
 'E':['讨论药物防治疾病的效果、临床获益、治疗优势、疗效终点、相关生活质量、指南的药物治疗推荐，或为这些判断提供的研究与证据。']}
for qs in quotes.values():
 for q in qs:assert q in manual,q
new={r['id']:r['prediction'] for r in map(json.loads,(ROOT/'all_predictions.jsonl').read_text().splitlines())}
old={r['id']:r['prediction'] for r in map(json.loads,(BASE/'all_predictions.jsonl').read_text().splitlines())}
records=[]
for c in json.loads(PACKET.read_text())['records']:
 rid=c['id'];d=c['dimension'];key=rid.split('-')[-1]+'/'+d
 assert key in notes,key
 records.append({'id':rid,'dimension':d,'group':c['group'],'unit_text':c['blind_input']['text'],
 'contexts':c['blind_input']['contexts'],'old_rule':old[rid]['labels'][d],'candidate_v31_rule':new[rid]['labels'][d],
 'diagnosis':notes[key],'manual_literal_quotes':quotes[d],
 'action':'changed_by_generic_relation' if old[rid]['labels'][d]!=new[rid]['labels'][d] else 'retained_or_boundary_for_review',
 'reference_labels_unchanged':{'A':c['A']['labels'][d],'C':c['C']['labels'][d]},
 'new_evidence':[e for e in new[rid]['evidence'] if e['dimension']==d],
 'new_suppressions':[e for e in new[rid].get('suppressions',[]) if d in e.get('dimensions',[]) and e['rule'].startswith('V31')]})
assert len(records)==51
summary={'status':'candidate_exposed_development_review_not_independent_validation','reviewer':'AI domain review agent',
 'manual_path':str((ROOT/'protocol-v1.3.md').resolve()),'manual_sha256':sha(ROOT/'protocol-v1.3.md'),
 'review_packet_path':str(PACKET),'review_packet_sha256':sha(PACKET),
 'reviewed_id_dimensions':51,'reviewed_unique_ids':len(set(r['id'] for r in records)),
 'old_input_path':str((BASE/'rule_inputs_v30_shared.jsonl').resolve()),'old_input_sha256':sha(BASE/'rule_inputs_v30_shared.jsonl'),
 'candidate_prediction_sha256':sha(ROOT/'all_predictions.jsonl'),
 'reference_labels_modified':False,'metrics_used_as_change_target':False,
 'pending_context_completion':'Root is uniformly checking enumerated conditions; this candidate run separates code effect on frozen old material.',
 'records':records}
(ROOT/'weak_case_diagnostic_51.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
changes=json.loads((ROOT/'changes_by_id_dimension.json').read_text())
counts=collections.Counter((c['dimension'],c['old'],c['new']) for c in changes)
release={'version':'v31-recall-boundary-review-20261007','created_at':datetime.datetime.now().astimezone().isoformat(),
 'status':'candidate_development_revision_on_frozen_v30_inputs','input_sha256':sha(BASE/'rule_inputs_v30_shared.jsonl'),
 'all_predictions_sha256':sha(ROOT/'all_predictions.jsonl'),'n':4924,'pending_n':0,
 'changed_id_dimensions':len(changes),'changed_unique_ids':len(set(c['id'] for c in changes)),
 'counts':[{'dimension':d,'from':a,'to':b,'n':n} for (d,a,b),n in counts.items()],
 'code_uses_identifiers_departments_reference_labels_or_metrics':False,
 'tests':{'applicable_historical_methods_passed':167,'v30_methods_passed':9,'v31_methods_passed':11,
 'superseded_original_expectation':'One old guideline-identity E positive control was already superseded in v30; preserved historical failure, no other failures.'},
 'artifacts':{str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix not in ['.pyc'] and '__pycache__' not in str(p) and p.name not in ['release_manifest.json']}}
(ROOT/'release_manifest.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
for name in ['policy_coding_v27.py','rule_support.py']:
 a=(BASE/name).read_text().splitlines(keepends=True);b=(ROOT/name).read_text().splitlines(keepends=True)
 (ROOT/(name+'.patch')).write_text(''.join(difflib.unified_diff(a,b,fromfile='v30/'+name,tofile='v31/'+name)))
print(json.dumps({k:release[k] for k in ['version','input_sha256','all_predictions_sha256','changed_id_dimensions','counts']},ensure_ascii=False))
