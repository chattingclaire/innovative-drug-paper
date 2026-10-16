"""Read-only independent checks of already executed synthetic controls, no rule/model call."""
from pathlib import Path
import json,hashlib,datetime,importlib.util
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/编码修订核查-20261008/自动规则编码/候选方案/rules39-five-relations-candidate01'
OUT=BASE/'independent-actual32-review'
ACTUAL=BASE/'audit-run04/controls_results_PRIVATE.json'
DESIGN=BASE/'design-v3/controls_FULL5_FROZEN.json'
MANIFEST=BASE/'design-v3/freeze_manifest.json'
DIMS=['S','E','Ec','I','F']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def textsha(t):return hashlib.sha256(t.encode()).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
bindings={}
def read(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
assert sha(ACTUAL)=='45aedb124cd69678b12b7b6fe8424199f5a0208a57b957c9e6b35781a7fc8262'
assert sha(DESIGN)=='b39327e4af68075d0679a95e415cf99c17f031a8d0c1cd777ae59c20b83a8422'
assert sha(MANIFEST)=='72f7de5c0d7361d282b17be7695078acc71c5d8d746d521d75c467acd622ab9c'
a=read(ACTUAL);d=read(DESIGN)['controls'];m=read(MANIFEST)
assert len(a)==len(d)==32
for rel,h in m['files'].items():
    p=BASE/rel;assert sha(p)==h;bindings[str(p)]=h
manual_bits=['11100','10000','01100','00000','00000','00000','00000','01000','01000','00000','00000','00000','10000','10000','00000','00000','00000','00010','00010','00000','00000','00000','00001','00001','00000','00000','00000',None,'00000','00000','10000','00001']
notes=[
'当前明确符合第七条，实际第七条为安全有效价格合理；只S/E/Ec，不借未援引条款，不把临床必需变F。',
'当前必须满足第八条，实际第八条为不良反应，S及other_safety。',
'当前明确援引第九、十条，疗效和经济性分别来自实际各条，E/Ec；未借第七、八条安全。',
'申请表填写导航参见第七条，当前非实质条件，不借S/E/Ec。',
'当前援引实际第十一条仅申请人名称联系信息，其他备给条款不传播。',
'归档标注条号是事务，Ec格式排除span逐字、无实质经济命题。',
'实际第十二条已提供且只是编号顺序，完整0；与缺料技术项区分。',
'当前未观测协变量影响治疗选择概率，同段同协变量敏感性分析明确用于疗效估计偏倚，E，不将治疗概率自动F。',
'当前敏感性分析检验假设，后句同一分析明确确定药物疗效估计上下限，E。',
'同分析仅计算稳定性，无疗效用途，不给E。',
'另一独立研究疗效不传播当前模型假设句。',
'当前统一数据归档，不从后句疗效分析传播E；格式排除span逐字。',
'处方审核实际要求患者过敏史，具体用药风险S；信息系统不是自动S或F。',
'处方审核收集药物过敏史，明确用药风险S。',
'一般处方信息化没有具体风险，不自动S/F。',
'就诊编号及挂号记录非风险信息，不从处方审核身份推S。',
'申请人联系方式是申报行政信息，全0。',
'药监批准且适应症重大变化为实际相对产品属性变化，attribute；批准非另设创新必需门槛。',
'药监批准且功能主治重大改变为实际属性变化，attribute；未推优效E或保障F。',
'首次目录申报不是产品创新或实际覆盖。',
'申请调整支付范围仅申请事项，未实际覆盖或独立费用责任。',
'补交注册材料事务，不推I。',
'医疗机构与定点药店连通并保证电子处方流转为常规药物获取渠道，access；未推负担或经济。',
'实际电子处方流转供患者凭处方取药，access。',
'一般信息平台数据归档不是患者取药渠道。',
'医疗机构药店之间仅档案数据流转，不是实际处方取药渠道。',
'电子处方记录归档不等于流转给患者取药。',
'缺当前实质援引第十二条；实际五维null、context_insufficient/undetermined，missing_current_cited_articles含第十二条且publishable=false。不得记已判全0。',
'“符合第七条”只在书名内，当前文件名格式事务，输出全0及无援引证据；仅证明该控制边界，不证明任意标题解析完整。',
'明确第七条第二款仅编号，不借第一款S/E/Ec，当前全0成立；不据此声称已支持所有细款阳性解析。',
'实际第十三条仅药品质量安全资料，S来源quality_safety且quality_only，无other_safety。',
'新增顺利流转句医疗机构—定点零售药店连通且电子处方流转，access；平台或医保身份不另推I/Ec。']
assert len(notes)==len(manual_bits)==32
reviews=[];ev_n=sup_n=cited_n=stat_n=0
for ordinal,(actual,control,bits,note) in enumerate(zip(a,d,manual_bits,notes),1):
    ident=control['id'];p=actual['prediction'];inp=control['input'];unit=control['input_text']
    assert actual['id']==ident and p['unit_text_sha256']==textsha(unit)
    assert inp['unit_text']==unit and inp['unit_id']==ident
    # Always prefer the unit-specific source over any inherited source field.
    source=Path(inp.get('unit_source') or inp['source'])
    candidate=Path(inp['candidate_file'])
    assert source.is_relative_to(BASE/'design-v3/synthetic_source_fixtures')
    assert candidate.is_relative_to(BASE/'design-v3/synthetic_source_fixtures')
    source_sha=sha(source);candidate_sha=sha(candidate)
    assert source_sha==inp['unit_source_sha256']==inp['source_sha256']
    assert candidate_sha==inp['candidate_sha256']
    source_text=source.read_text();cand=read(candidate)
    assert unit in source_text and control['paragraph'] in source_text
    cu=[u for u in cand['unit_candidates'] if u['id']==ident]
    assert len(cu)==1 and cu[0]['text']==unit
    paras={q['id']:q['text'] for q in cand['paragraphs']}
    assert paras[cu[0]['paragraph_id']]==control['paragraph']
    for q in cand['paragraphs']:
        assert all(source_text.splitlines()[line-1]==q['text'] for line in q['source_lines'])
    refs=inp.get('explicitly_cited_articles_v10',[])
    assert refs==inp.get('llm_v29_shared_context',{}).get('explicitly_cited_articles_v10',[])
    refmap={q['article']:q for q in refs}
    for q in refs:
        assert q['source_path']==str(source) and q['source_sha256']==source_sha
        assert q['candidate_sha256']==candidate_sha and q['text']==paras[q['paragraph_id']]
        assert q['text'] in source_text
    preferred=dict.fromkeys(DIMS,None) if bits is None else dict(zip(DIMS,map(int,bits)))
    assert p['labels']==preferred
    if bits is None:
        assert actual['expected_labels'] is None and control['expected_labels'] is None
    else:
        assert preferred==actual['expected_labels']==control['expected_labels']
    assert p['status']=='development_revision_not_independently_validated'
    if bits is None:
        assert p['judgement_status']=='undetermined' and p['input_assessment_status']=='context_insufficient'
        assert p['issue_reason']=='current_substantive_cited_article_content_missing'
        assert p['current_reference_gate_v39']['missing_current_cited_articles']==['第十二条']
        assert p['current_reference_gate_v39']['publishable'] is False
        assert not p['evidence'] and not p['suppressions']
        assert p['innovation_subtype_status']=='undetermined'
    else:
        assert p['judgement_status']=='rule_prediction'
        assert p['input_assessment_status']=='not_assessed'
        assert all(type(p['labels'][dim]) is int for dim in DIMS)
        assert p['safety_quality_basis']==('quality_only' if ident=='REF-P04-QUALITY' else 'no_quality_basis')
        expected_f=['access'] if p['labels']['F'] else []
        expected_i=['attribute'] if p['labels']['I'] else []
        assert p['fairness_subtypes']==expected_f and p['innovation_subtypes']==expected_i
        expected_s=['quality_safety'] if ident=='REF-P04-QUALITY' else ['other_safety'] if p['labels']['S'] else []
        assert p['safety_subtypes']==expected_s
        assert p['innovation_unclassified_evidence']==[]
        for dim in DIMS:
            assert not p['labels'][dim] or any(e['dimension']==dim for e in p['evidence'])
    for e in p['evidence']:
        ev_n+=1;assert p['labels'][e['dimension']]==1
        assert type(e['start']) is int and type(e['end']) is int
        assert 0<=e['start']<e['end']<=len(unit)
        assert unit[e['start']:e['end']]==e['text']
        assert e['protocol_basis'] and e['rule'] and e['rule_release']==p['version']
        if 'current_relation_anchor' in e:
            k=e['current_relation_anchor'];assert unit[k['start']:k['end']]==k['text']
        dep=e.get('context_dependency',{})
        if 'cited_article' in dep:
            cited_n+=1;q=refmap[dep['cited_article']]
            assert dep['cited_source_path']==str(source)
            assert dep['cited_source_sha256']==source_sha and dep['cited_candidate_sha256']==candidate_sha
            assert q['text'][dep['cited_start']:dep['cited_end']]==dep['cited_text']
            assert dep['cited_text'] in source_text
            assert dep['cited_article'] in dep['current_cited_articles']
            assert dep['source_authentication']['literal_reproduced_in_current_runtime'] is True
            for k in e['cited_substantive_anchors']:
                assert k['source_path']==str(source) and k['source_sha256']==source_sha and k['candidate_sha256']==candidate_sha
                assert k['paragraph_sha256']==textsha(q['text'])
                assert q['text'][k['start']:k['end']]==k['text']
        if 'context_start' in dep:
            stat_n+=1;paragraph=control['paragraph']
            assert paragraph[dep['context_start']:dep['context_end']]==dep['context_text']
            assert dep['source_sha256']==source_sha
            assert dep['source_authentication']['literal_reproduced_in_current_runtime'] is True
            assert dep['context_text'] in source_text
        if e['dimension']=='S':
            assert e['safety_basis']==('quality_safety' if ident=='REF-P04-QUALITY' else 'other_safety')
    for s in p['suppressions']:
        sup_n+=1;assert unit[s['start']:s['end']]==s['text']
    # Verify duplicated typed reference metadata rather than relying on authentication flags alone.
    for typed in p.get('typed_contexts_v34',[]):
        for q in typed.get('contexts',[]):
            if 'source_path' in q:
                assert q['source_path']==str(source) and q['source_sha256']==source_sha
                assert q['candidate_sha256']==candidate_sha and q['text'] in source_text
    reviews.append({'ordinal':ordinal,'id':ident,'kind':'missing_material_technical' if bits is None else 'semantic',
      'input_and_given_paragraph_articles_read':True,'all_five_dimensions_read':True,
      'independent_preferred_labels':preferred,'actual_labels':p['labels'],'semantic_status':'supported',
      'note':note,'actual_evidence_rule_basis_relations_suppressions_and_subtypes_read':True,
      'dimension_reasons_field':'not supplied by this rule output; independent five-dimensional judgement above, not fabricated model reasons',
      'offset_and_reference_source_checks':'PASS','unit_source_preferred':str(source),'unit_source_sha256':source_sha,
      'actual_prediction_canonical_sha256':textsha(canon(p)),
      'status_precision':'rule_prediction is compatible runtime enum; not_assessed is not proof of material sufficiency' if bits else 'undetermined/nonpublishable, not a zero label'})

redactorpath=ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
bindings[str(redactorpath)]=sha(redactorpath)
spec=importlib.util.spec_from_file_location('redactor_rule32',redactorpath);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
r=mod.ReservedContextRedactor();scan=r.audit_object_no_full_match({'design':d,'actual':a})
assert scan['no_remaining_full_normalized_reserved_unit_match']
for name in ['完整五维手册-v1.3.md','共用操作说明-v1.4.md']:
    p=ROOT/'outputs/coding-revision-20261007-r3/protocol'/name;bindings[str(p)]=sha(p)
assert all(sha(Path(p))==h for p,h in bindings.items())
report={'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PASS_FOR_THESE_ACTUAL_SYNTHETIC_CONTROLS_ONLY','blocking_findings':[],
 'review_type':'independent_agent_actual_full_field_control_review_without_author_audit_import',
 'source_files_modified':False,'reviewer_model_calls':0,'reviewer_rule_classifier_calls':0,
 'scope':{'actual_controls_read':32,'semantic_controls':31,'semantic_dimensions':155,'missing_material_technical':1,
  'real180_read':False,'protected_originals_manually_read':False,'whole_corpus_execution':False},
 'checks':{'actual_sha256':sha(ACTUAL),'design_v3_sha256':sha(DESIGN),'manifest_files_checked':len(m['files']),
  'all_manual_independent_labels_match_actual':True,'all_actual_evidence_offsets_literal':True,'evidence_n':ev_n,
  'all_suppression_offsets_literal':True,'suppression_n':sup_n,'cited_evidence_dependency_n':cited_n,
  'same_paragraph_statistical_dependency_n':stat_n,'all_fixture_texts_and_candidate_lines_source_authenticated':True,
  'unit_source_display_priority_checked':True,'quality_only_and_source_subtype_checked':True,
  'missing_material_not_published_as_zero':True,'protected_full_match_scan':scan},
 'metadata_precision_notes':[
  '普通输出没有dimension_reasons五维理由字段，实际保存规则名、protocol_basis、关系与证据；本次全部阅读，并对五维另给独立语义意见，不虚称已有五维模型理由。',
  '完整语义项实际judgement_status=rule_prediction，与先前设计报告determined语义描述兼容；not_assessed不构成充分性认证。',
  'RISK-P01的既存Ec排除标签non_drug_research_institution_or_asset_resource较宽泛；当前句确无实质药品费用，未造成控制误判，不据该元数据类别推论一般信息系统句都应排除。',
  '部分drug_object_in_unit=false未识别“该药”；当前具体关系仍有原句和同段证据。该词表标记不是否定药物对象的人工结论。'],
 'reviewer_check_repair_history':{'preserved_failed_check':str(OUT/'attempt01_failure_PRESERVED.json'),
  'correction':'缺料控制expected_labels容器为null，实际labels为五维各null；改为分别显式核两种表示，并保留undetermined及nonpublishable门禁，不改源文件或候选结果。'},
 'limitations':[
  '只支持这31语义构造例和1缺料技术例；不能由32/32推广全量召回、任意细款解析或全部标题覆盖。',
  '未读真实180、A/C、κ或保留267原文来决定标签；不运行规则、模型或全量入口，不改任何冻结文件。',
  '开发材料复审不是新独立真人验证，不能保证录用或新的独立效度。'],
 'manual_basis':['v1.3:11/17/21/29/31/35/43/53/65/95/142/152/156','v1.4:7/9/14/17/21/24/30'],
 'reviews':reviews,'source_bindings':bindings}
OUT.mkdir(parents=True,exist_ok=True)
p=OUT/'rules39_actual32_independent_review.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md='''# 规则39实际32控制独立复审

本次范围通过：实际逐条读完31条语义控制的155维及1条缺料技术控制，核输入、全部段落/条款、实际规则依据、证据、抑制项、F/I来源和S质量标记。没有新增实质阻断。

实质援引只使用当前对应条文；同一统计对象明确服务疗效估计时才计E；过敏史提供具体用药风险；明确产品属性变化计I；机构—药店电子处方流转计F access。标题内条号、未援引其他条款及具体第二款不借第一款的负例均未传播。

质量安全专例实际为quality_safety及quality_only。缺第十二条的技术例五维null、context_insufficient/undetermined，publishable=false，未误记全0。普通rule_prediction是实际枚举，not_assessed并非材料充分性认证。

机械独立复核：冻结清单66文件哈希、unit_source优先、当前证据和抑制项offset、实际援引条文offset及源SHA、同段统计承接offset均通过；没有导入作者审计函数，也没有重新调用分类器或模型。原文件未改。

规则输出没有dimension_reasons五维模型理由字段；本报告阅读实际规则依据，并另给五维独立判断。既有元数据中RISK-P01的Ec排除类名偏宽，部分“该药”对象词表标记为false；这些未造成当前控制标签错误，报告留精度说明。

仅限这些开发构造例通过，不能证明全量语义效度、任意细款阳性解析、全部标题覆盖或论文录用。不读真实180或267保留正文，不改A/C、手册或正文。
'''
(OUT/'rules39_actual32_independent_review.md').write_text(md)
seal={'finished_utc':report['finished_utc'],'files':{str(f):sha(f) for f in [p,OUT/'rules39_actual32_independent_review.md',Path(__file__)]}}
(OUT/'actual32_review_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'status':report['status'],'cases':32,'semantic_dimensions':155,'source_files_modified':False},ensure_ascii=False))
