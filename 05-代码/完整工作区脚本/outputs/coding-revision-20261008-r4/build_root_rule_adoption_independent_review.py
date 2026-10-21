from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, unicodedata
from pypdf import PdfReader

ROOT=Path('/PROJECT_ROOT')
OUT=ROOT/'outputs/coding-revision-20261008-r4'
SHADOW=OUT/'rules-v37.2-shadow-full-v14'
TARGETS={'RECODE25-'+n for n in ['00035','00741','01378','01388','03574','01353']}
MANUAL=ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'
OPS=ROOT/'outputs/coding-revision-20261007-r3/future-human-validation-v5/手册/共用操作说明-v1.4.md'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def norm(t):return re.sub(r'\W+','',unicodedata.normalize('NFKC',t))
def strings(x):
    if isinstance(x,str):yield x
    elif isinstance(x,list):
        for v in x:yield from strings(v)
    elif isinstance(x,dict):
        for v in x.values():yield from strings(v)
def targeted(p,key):
    out={}
    for ln in Path(p).read_text().splitlines():
        r=json.loads(ln)
        if r.get('id') in TARGETS:out[r['id']]=r[key]
    assert set(out)==TARGETS
    return out
OLD=ROOT/'outputs/coding-revision-20261007-r3/rules-v36.2-development/all_predictions_material_v14.jsonl'
NEW=SHADOW/'all_predictions_material_v14_shadow.jsonl'
INPUT=ROOT/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
inputs=targeted(INPUT,'input');old=targeted(OLD,'prediction');new=targeted(NEW,'prediction')
prior=load(SHADOW/'exhaustive_nonreserved_change_review.json')
projection=load(SHADOW/'nonreserved_changes_manual_review_projection.json')
freeze_path=OUT/'rules-v37.2-development/candidate_freeze.json';freeze=load(freeze_path)
exclude_path=OUT/'validation-state-audit/future_human_v5_development_exclusion_metadata.json';reserved=set(load(exclude_path)['all_registered_members_of_reserved_families_unit_ids'])
assert TARGETS & reserved=={'RECODE25-01353'}
assert sha(OLD)==prior['baseline_predictions_sha256'] and sha(NEW)==prior['shadow_predictions_sha256'] and sha(freeze_path)==prior['candidate_freeze_sha256']
code_checks=[{'path':p,'expected_sha256':h,'actual_sha256':sha(p),'matches':sha(p)==h} for p,h in freeze['production_code_sha256'].items()]
assert all(r['matches'] for r in code_checks)

assessments={
'RECODE25-00035':{'dimension':'I','old':0,'new':1,'category':'真实实现修复：漏判实质创新研发指导','verdict':'支持采纳','manual_locators':[{'path':str(OPS),'line':13},{'path':str(OPS),'line':7}],'reason':'当前单元不仅允许申请会议或提交材料，还规定药审中心安排相关审评人员，基于已有研究资料对下一步研究方案提出意见或建议。实际科学指导及人员资源在当前单元内成立；已认证突破性治疗创新药/改良型新药范围只消解其对象，不负责替当前单元制造支持内容。','evidence_summary':'安排相关审评人员；基于研究资料对下一步研究方案提出意见或建议','subtype_review':'research_support成立，依据为实际指导资源及方案支持；不把申请渠道或会议形式本身编码为I。','limits':'不是所有II类会议、普通研究咨询或突破性程序事务均为I；也不从上位资格向该单元复制E/S。'},
'RECODE25-00741':{'dimension':'Ec','old':0,'new':1,'category':'真实实现修复：漏判具体药品价格取值','verdict':'支持采纳','manual_locators':[{'path':str(MANUAL),'line':33}],'reason':'当前单元的取值对象是药品集采中选最高价，条件是参照药已纳入集采；这是药品价格基准的实质选择，非仅列谈判/采购程序名或幻灯片文件名。','evidence_summary':'取药品集采中选最高价','subtype_review':'Ec无独立来源子类型要求；当前价格依据充分，不从同段其他未满足需求或创新分级内容增加F/I。','limits':'该规定不表示真实成交价、医保基金支出或患者实际负担，也不能把最高价改述为最低价。'},
'RECODE25-01378':{'dimension':'I','old':1,'new':0,'category':'真实实现修复：删除一般制定宗旨误报','verdict':'支持采纳','manual_locators':[{'path':str(OPS),'line':17},{'path':str(OPS),'line':15}],'reason':'当前单元只表达促进药品创新、完善制度的制定宗旨，以及制定/发布/施行实施办法。未在该单元陈述权利对象、保护期限、实质适用条件或具体研发支持资源。v1.4第5项明确排除此类宗旨/印发命题；不能因为同文件后文存在实际权利条款而反向继承到公告宗旨。','evidence_summary':'促进药品创新发展、完善制度、制定实施办法、现予发布及施行','subtype_review':'I=0时不留research_support；旧证据只截取一般宗旨不足以支撑该子类型。','limits':'不能把本次I=0推广成所有数据保护条款为0；含实体权利命题的其他单元仍须判断。'},
'RECODE25-01388':{'dimension':'I','old':0,'new':1,'category':'真实实现修复：漏判专有试验数据保护实体权利','verdict':'支持采纳','manual_locators':[{'path':str(OPS),'line':15},{'path':str(MANUAL),'line':41},{'path':str(MANUAL),'line':166}],'reason':'当前单元规定符合条件的化学药品和生物制品获批上市时，保护申请人自行取得且未披露的试验及其他数据，并给予最长不超过6年保护期。权利对象、实质条件、保护行为与期限均在当前单元中，是v1.4第3项明确纳入的相关知识产权内容，不是泛称保密或资料递交。','evidence_summary':'自行取得且未披露的试验数据和其他数据实施保护；最长不超过6年的数据保护期','subtype_review':'research_support作为实际授予研发数据保护权利的制度支持可以成立；不得解释为该药原创、临床改良已获认定，不额外补attribute或qualification_advantage。','limits':'这是冻结操作化纳入相关知识产权的结果，不证明权利属于专利，不证明支持已经产生创新效果，也不意味着一切数据安全/商业秘密都算I。'},
'RECODE25-03574':{'dimension':'I','old':0,'new':1,'category':'合理操作边界：具体产品改变的限制性讨论','verdict':'支持采纳，须保留操作化边界','manual_locators':[{'path':str(OPS),'line':14},{'path':str(OPS),'line':7},{'path':str(MANUAL),'line':142}],'reason':'口服制剂改注射制剂明确给出改变前后两种不同制剂及改变关系，超出只列剂型名称或普通规格。限制改制与在口服可满足临床需求时不批准上市，是针对该具体产品改变的否定/条件性规定；现手册不要求创新标签必须正面或已证明优效。','evidence_summary':'口服制剂改注射制剂；口服制剂能够满足临床需求时不批准注射制剂上市','subtype_review':'attribute成立，依据为明确产品属性改变；不能从邻段罕见病研发支持或章节标题复制research_support。','limits':'不能写成该改变必然创新、必然改良、已带来优势或值得鼓励；本审计只支持现冻结定义下I=1。没有直接的药物损害依据时不凭注射二字追加S。'},
'RECODE25-01353':{'dimension':'S','old':0,'new':1,'category':'真实实现修复：已暴露开发案例的用药错误预防漏判','verdict':'支持采纳，保留开发暴露标记','manual_locators':[{'path':str(MANUAL),'line':19}],'reason':'当前单元在药品调配、交接、发放和使用场景中，要求医务人员互相提醒、开展患者用药教育并防范误选误用，直接讨论用药错误预防。患者损害预防关系在当前单元自足，无需从文件标题推定。','evidence_summary':'药品调配交接以及发放使用；防范误选误用','subtype_review':'S依据为用药错误预防，属于other_safety；不是仅药品质量安全，也不据一般用药教育附加F。','limits':'该单位至少在此前十例差异审计及写稿中已暴露；本次为root明确授权复核，不是新独立验证，不删除v5行、不清除暴露flag。','exposure_flag':'previously_exposed_in_10_case_development_audit_not_independent_validation'}
}

records=[]
for i in sorted(TARGETS):
    r=assessments[i];inp=inputs[i];actual={d:{'old':old[i]['labels'][d],'new':new[i]['labels'][d]} for d in ['S','E','Ec','I','F'] if old[i]['labels'][d]!=new[i]['labels'][d]}
    assert actual=={r['dimension']:{'old':r['old'],'new':r['new']}}
    source=Path(inp.get('unit_source') or inp['source']);raw=source.read_bytes()
    if source.suffix=='.pdf':doc=PdfReader(source);pages=[p.extract_text() or '' for p in doc.pages];source_text='\n'.join(pages)
    elif source.suffix=='.json':source_text='\n'.join(strings(json.loads(raw)));pages=[]
    else:source_text=raw.decode();pages=[]
    match=norm(inp['unit_text']) in norm(source_text)
    check={'actual_unit_source':str(source),'actual_unit_source_sha256':sha(source),'expected_unit_source_sha256':inp.get('unit_source_sha256') or inp.get('source_sha256'),'expected_hash_matches':sha(source)==(inp.get('unit_source_sha256') or inp.get('source_sha256')),'NFKC_punctuation_whitespace_normalized_unit_literal_present':match,'source_pages_with_full_unit':[j+1 for j,t in enumerate(pages) if norm(inp['unit_text']) in norm(t)]}
    assert check['expected_hash_matches'] and match
    o={'id':i,'reserved_member':i in reserved,'unit_text_sha256':hashlib.sha256(inp['unit_text'].encode()).hexdigest(),'actual_machine_change':actual,**r,'source_check':check}
    if i!='RECODE25-01353':o['reviewed_current_unit_text']=inp['unit_text']
    if i=='RECODE25-00035':
        pr=next(p for p in projection if p['id']==i);scope=pr['new_changed_dimension_evidence'][0]['context_dependency']['innovation_object_scope'];o['scope_literal_check']={'source_hash_matches':scope['source_sha256']==sha(source),'scope_quote_hash_matches':hashlib.sha256(scope['text'].encode()).hexdigest()==scope['text_sha256'],'NFKC_scope_literal_in_original_source':norm(scope['text']) in norm(source_text)}
        assert all(o['scope_literal_check'].values())
    records.append(o)

scope_text=[norm(s) for s in strings(projection)];unexpected_reserved=[]
for ln in (ROOT/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl').read_text().splitlines():
    x=json.loads(ln)
    if x['id'] in reserved:
        t=norm(x['text'])
        if len(t)>=20 and any(t in s for s in scope_text):unexpected_reserved.append(x['id'])
assert not unexpected_reserved
bindings=[{'path':str(p),'sha256':sha(p)} for p in [SHADOW/'exhaustive_nonreserved_change_review.json',SHADOW/'nonreserved_changes_manual_review_projection.json',SHADOW/'previously_exposed_01353_flagged_check.json',freeze_path,OLD,NEW,INPUT,MANUAL,OPS,exclude_path]]
result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'reviewer':'validation_state_oct8 independent semantic audit','scope':'Only six root-authorized cases and necessary current/authenticated context; assess changed dimensions under frozen v1.3/v1.4, not A/C labels or kappa/performance.','overall':'SUPPORT_ADOPTION_OF_ALL_SIX_CURRENT_CHANGES_WITH_OPERATIONAL_BOUNDARIES_AND_EXPOSURE_FLAG','reviewed_cases_n':6,'real_implementation_repairs_n':5,'reasonable_operational_boundary_cases_n':1,'required_semantic_repairs_identified_n':0,'records':records,'binding_checks':{'old_new_prediction_hashes_match_author_seal':True,'candidate_freeze_hash_matches':True,'production_code_hash_checks':code_checks,'both_manual_copies_identical':sha(MANUAL)==sha(ROOT/'outputs/coding-revision-20261007-r3/future-human-validation-v5/手册/完整五维手册-v1.3.md'),'actual_six_changed_dimensions_match_projection':True,'reserved_target_intersection':['RECODE25-01353'],'other_reserved_full_current_unit_text_in_nonreserved_review_projection':unexpected_reserved},'artifact_provenance_note':{'id':'RECODE25-00741','note':'Projection的source保留旧归档工作方案PDF指针（9页），不能用其pages19–20定位该原句。实际冻结rule_inputs的unit_source已明确为医保2025公告附件/5.pdf，SHA7f5b1829…，全文在物理第20页；实际全量执行run绑定该附件SHA。语义与实际运行来源可核，当前不构成代码/预测阻断。后续展示应同时列actual unit_source，不能将旧source字段冒称FAQ原件。'},'read_and_write_discipline':{'A_C_labels_loaded':False,'human_labels_or_scores_loaded':False,'kappa_or_performance_used_for_judgement':False,'new_model_calls':0,'tests_or_reruns_started':False,'code_predictions_main_text_modified':False,'original_freeze_and_review_files_modified':False,'source_originals_read_by_model_beyond_authorized_six_and_needed_context':False},'scope_limits':['Exhaustive review of these six observed changes, not full-corpus semantic gold audit. No conclusion about unchanged-unit correctness, generalization, sensitivity/specificity or independent validity.','03574 positiveI means attention to explicit product change under the frozen operational definition, not proven innovation or therapeutic superiority.','01388 positiveI means substantive proprietary research-data rights, not mere word数据/保护 and not general confidentiality.','01353 remains exposed development material; neither this review nor same-batch recalculation repairs independence.'],'evidence_bindings':bindings}
(OUT/'root-rule-adoption-independent-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
lines=['# 自动规则37.2六处变化独立内容审核','', '结论：支持采纳这6处当前标签变化；5处为现冻结规范下的实现修复，03574属于有明确文本依据的操作边界。未发现这6处还需修复的语义阻断。判断只依据当前原文、必要语境和v1.3/v1.4，未读取A/C或人工标签，未看κ/性能。','', '|ID|实际变化|分类|独立结论及依据|','|---|---|---|---|']
for r in records:lines.append(f"|{r['id']}|{r['dimension']} {r['old']}→{r['new']}|{r['category']}|{r['reason']}|")
lines += ['', '01378和01388必须区分：前者是宗旨及发布，按v1.4第5项为I=0；后者明确专有试验数据的保护条件、对象和最长6年期限，按第3项为I=1。无需靠文件题名推断，也不能把整个数据保护文件一律计I或一律排除。','', '03574的“口服制剂改注射制剂”明确产品改变，限制或不批准同样是讨论该改变；按v1.3新品种/剂型边界与v1.4第2项可赋I=1。但不能写成该改制已实现创新、临床优势或改善效果。','', '01353已在此前十例差异审计及写稿中暴露。当前S=1依据是药品使用中的误选误用预防；本次复核仍属开发信息，保留原暴露flag，不算独立验证。','', '核对实际旧/新预测，两文件SHA与原审读封存一致；冻结24个生产代码文件当前SHA均匹配。6条当前原句与实际unit_source经NFKC、标点和空白正规化机械匹配均通过。00035创新对象范围原件、引文SHA及当前源SHA匹配。五条非保留投影未包含其他保留单元的完整原句。','', '来源展示注意：00741投影source仍指向旧9页工作方案PDF；实际冻结输入unit_source为2025公告附件5，原句在其物理第20页，实际执行已绑定正确附件SHA。不能把旧source字段与19–20页组合冒称实际原件。本报告不改冻结材料。','', '这些结论不等于规则全量准确、未变化记录正确或独立机器效度通过。完整原句、每条手册定位、来源SHA、实际变化及核查边界见同名JSON。']
(OUT/'root-rule-adoption-independent-review.md').write_text('\n'.join(lines))
print(json.dumps({'verdict':result['overall'],'reviewed':6,'required_repairs':0,'json_sha256':sha(OUT/'root-rule-adoption-independent-review.json'),'md_sha256':sha(OUT/'root-rule-adoption-independent-review.md')},ensure_ascii=False))
