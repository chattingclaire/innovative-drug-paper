"""Independent readonly frozen130 metadata / seven selected-packet audit.

No classification calls, external source assets, reference workbooks or unselected
packet bodies. Design is reviewed as a proposal, never certified as a candidate.
"""
import json
import hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

G=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
B=G/'08-audits/current-machine-rare-disagreement-semantic-20261011-sol'
D=G/'08-audits/v9-generic-relationship-repair-design-sol'
O=G/'08-audits/v9-repair-adoption-independent-20261012-sol/semantic-and-design-phase01'
IDS=['RECODE25-'+x for x in ['01391','01430','01435','01436','02235','02229','01482']]

def bind(p):
    p=Path(p);r=p.read_bytes()
    return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}

opened={}
def read(p):
    p=Path(p);opened[str(p)]=bind(p)
    return json.loads(p.read_text())

def ptr(x,p):
    for k in p.strip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~')
        x=x[int(k)] if isinstance(x,list) else x[k]
    return x

def save(n,x):
    (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

a=read(B/'final130/semantic-reviews130.json')
s=read(B/'final130/summary130.json')
addendum=read(B/'final130/audit-analysis-addendum-02209.json')
freeze=read(B/'readable-disagreement-selection-freeze.json')
membership=read(B/'population-membership-metadata.json')
seal=read(B/'final130/seal.json')
read(B/'final130/outputs-hashes.json')
eligible={(x['id'],x['dimension']):x for x in freeze['eligible_all_records']}
actual={(x['id'],x['dimension']):x for x in a}
assert len(a)==len(eligible)==len(actual)==130 and set(actual)==set(eligible)
assert len({x['id'] for x in a})==98
assert {x['id'] for x in a} <= set(membership['exposed_ids_in_frame_order'])
assert not ({x['id'] for x in a} & set(membership['remaining_ids_in_frame_order']))
assert not ({x['id'] for x in a} & set(membership['human200_source_ids_excluded']))
for k,x in actual.items():
    e=eligible[k]
    assert x['machine_values']=={'rules_v7':e['rule'],'native_original_whole_batch':e['native']}
    assert x['current_direct_material']['packet']==e['packet']
    assert x['machine_labels_modified'] is False
counts=dict(Counter(x['review_class'] for x in a));dims=dict(Counter(x['dimension'] for x in a))
assert counts==s['review_classes'] and dims==s['dimensions']
assert actual[('RECODE25-02209','I')]==addendum['integrated_review']
assert addendum['old_phase02_review']['review_class']=='边界待定'
assert addendum['integrated_review']['review_class']=='更支持LLM'
final_seal_checks=[]
for q in seal['outputs']:
    assert Path(q['path']).parent==B/'final130'
    z=bind(q['path']);assert z==q
    opened[z['path']]=z;final_seal_checks.append(z)

design_seal=read(D/'output-seal.json')
design_input=read(D/'input-seal.json')
design_contract=read(D/'selector-contract-template.json')
controls=read(D/'synthetic-controls-fixed-before-code.json')
read(D/'controls-draft.json')
read(D/'selector-static-selfchecks.json')
for f in ['report.md','select_static_impact.py']:
    opened[str(D/f)]=bind(D/f)
# Already inspected these exact code bodies statically; no classifier import/run.
old_dim=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/dimensions.py'
opened[str(old_dim)]=bind(old_dim)
assert design_contract['manual_static_audit']['approved'] is False
assert controls['not_executed'] is True

packet_checks=[];quote_checks=[];finite_text_resources=[];unsupported_external=[];packets={}
for sid in IDS:
    x=next(x for x in a if x['id']==sid)
    spec=x['current_direct_material']['packet'];p=Path(spec['path'])
    assert p.parent==G/'06-coding/full4481-common-v15-production-preparation-sol/packets'
    assert p.name==sid+'.json'
    z=bind(p);assert z==spec
    d=read(p);packets[sid]=d
    assert d['source_id']==sid and d['output_id']=='B-'+sid.split('-')[-1]
    packet_checks.append({'review_id':sid,'original_packet_output_id':d['output_id'],'binding':z,'source_ref':d['source_bundle']['source_record']['source_ref']})
    for i,e in enumerate([x['current_direct_material']]+x['native_material_evidence']):
        if e.get('pointer'):
            t=ptr(d,e['pointer']);q=e['quote'];j=t.find(q)
            assert j>=0
            quote_checks.append({'id':sid,'evidence_index':i,'pointer':e['pointer'],'quote':q,'unicode_interval_half_open':[j,j+len(q)],'exact':True})
        else:
            unsupported_external.append({'id':sid,'asset_path':e['asset_path'],'quoted_locator':e.get('page'),'not_opened':True,'reason':'current packet text sufficient for this focused diagnosis; no independent external visual/literal asset certification'})
    for i,c in enumerate(d['source_bundle']['source_record'].get('contexts',[])):
        if c.get('text'):
            finite_text_resources.append({'id':sid,'pointer':f'/source_bundle/source_record/contexts/{i}/text','kind':c.get('kind'),'semantic_use':'direct current paragraph, finite local context or table identity; no standalone sibling packet'})

care=packets['RECODE25-01482']['source_bundle']['source_full_text_resources'][0]
care_pointers=[]
for i in [6,19,20,21,22,23,24,25,26,27,28,29,40,43,110,111]:
    p=care['paragraphs'][i];raw=p['text'].encode();assert hashlib.sha256(raw).hexdigest()==p['text_sha256']
    rec={'id':'RECODE25-01482','pointer':f'/source_bundle/source_full_text_resources/0/paragraphs/{i}/text','source_paragraph_id':p['source_paragraph_id'],'physical_pages':p['physical_pages'],'text':p['text'],'text_sha256':p['text_sha256']}
    care_pointers.append(rec);finite_text_resources.append({k:v for k,v in rec.items() if k!='text'})
assert '②在境内尚无药物获批拟开发的罕见疾病适应症' in care['paragraphs'][24]['text']
assert '1.1 申请资格' in care['paragraphs'][29]['text']
assert '跟踪随访' in care['paragraphs'][43]['text']
assert '当品种被纳入试点项目后' in care['paragraphs'][110]['text']
save('read-inventory-and-bindings.json',{'opened_file_bindings':list(opened.values()),'focused_packet_checks':packet_checks,'actual_new_task_packet_reads_N':7,'packet_permission_basis':'IDs strictly inside frozen130, exposed and disjoint from human200/remaining','finite_packet_text_resource_pointers_used':finite_text_resources,'unopened_external_asset_citations':unsupported_external,'external_manual_not_opened':'Use only already provided frozen-manual excerpts; no new direct manual-file certification.','current_body_outside_frozen130_read':False,'classification_runs':0})
save('quote-and-care-chain-checks.json',{'exact_pointer_checks':quote_checks,'care_chain_nodes':care_pointers,'external_assets_verified':False,'care_chain':'CARE-P025② gap branch AND complete1.1 qualification → CARE-P030 admission → current CARE-P044 development service → CARE-P007 / CARE-P111 / CARE-P112 concrete same-stage framework and milestone feedback'})

positions=[
 {'ids':['01391/I'],'finding':'supports_object_mismatch_correction','reason':'当前第三方自行取得数据有注册批准、不给数据保护期且后续不得依赖的独立待遇；创新持有人数据不是同一数据对象。旧I4引用第五条创新药保护及其他创新适应症定义，不能证明该自行取数申请人有创新/改良资格。','constraints':['按当前数据对象及角色闭合，不按“其他申请人”一词否决。','依赖创新持有人受保护数据的第三方限制仍可能直接作用于原创新权利；不得连带撤掉。']},
 {'ids':['01430/I','01435/I','01436/I'],'finding':'supports_table_member_scope_correction','reason':'当前实质表行分别为境内已上市疫苗、生物类似药、其他生物制品，不给数据保护；原行没有创新/改良条件。表头明确分类/内容/数据保护期/备注，当前3类成员不能从1/2类兄弟行及制度总定义反向继承创新关系。','constraints':['按实际行、表头、合并分类格及内容对象匹配，不硬编码ID或3.3数值。','“不给予”本身不是排除词；创新/改良合格对象的真实限制或撤回仍保留。','本次核包内真实表行与结构，未新开外部表图，故不宣称再做图像复核。']},
 {'ids':['02235/I'],'finding':'supports_selfcontained_support_correction','reason':'当前原句同时写创新药研发/临床申请对象与受理后30工作日完成审评审批，对象—实际办理便利自足。不能因创新词与支持目的在前半句就把后半句实质安排全部当口号。','constraints':['不从任何30日数字孤立推导创新或更快。','需保存对象、实际安排和直接连接；不要求已兑现。']},
 {'ids':['02229/I'],'finding':'supports_selfcontained_resource_correction','reason':'当前原句明确审评审批资源向符合条件的创新药临床申请倾斜，30日通道为具名具体机制，三项关系自足。包内source_documents候选抽取第7条也有额外资源文字，但外部doc未重开，其字面/图页不纳入主要证明。','constraints':['不用政策解读标题把一般承诺/12周数字创新化。','不要求外部额外doc引文成立才能识别当前自足资源关系。']},
 {'ids':['01482/F'],'finding':'supports_existing_branch_safe_need_service_chain','reason':'原包同版CARE-P025②明示目标适应症无境内获批药物，P030按完整1.1资格决定拟纳入，当前P044对已纳入品种实施研发随访/密切沟通，P007/P111/P112核明框架、关键节点计划及研发共识反馈。缺口是实际资格分支，同一研发阶段具体支持链闭合；可支持原规则关系，无需字面“优先”。','constraints':['OR分支逐支：FIC/比较优势分支不随之获得缺口含义。','本链是特殊资格→具体研发资源，不把一般罕见病身份、仅研发需要、常规随访/报告/通知默认F。','这是独立代理的条件语义诊断，不是新human判断，也不声称项目已兑现反馈。']}
]
save('focused-semantic-positions.json',positions)
design_findings=[
 {'issue':'original append-only route cannot remove old false positives','evidence':'Actual v8 Accumulator.finish takes any positive before boundary/material/zero; original design preserves full old run then only appends new IF evidence.','requirement':'Need guarded per-candidate keep/drop/unresolved filtering, independently audit every removed positive and preserve any other valid candidate. Revision02 response is a proposal until actual sealed code exists.'},
 {'issue':'limited-object concurrent application / preapplication service','evidence':'Prior sealed secondcheck00068/I and00071/I,F not automatically established; actual preapplication mechanism proven but conditioned-approval cohort intersection with innovation/need branch not proven.','requirement':'Do not hard-code positive expected or use whole-program object union without current mother-object proof; preserve boundaries.'},
 {'issue':'gate isolation alone is not full effect proof','evidence':'Template accepts newly named functions then requires manual_static_audit flags. AST stripping verifies old code equivalence, not semantic soundness or all mutable side effects.','requirement':'Inspect actual new bodies, defaults/annotations/import-time evaluation, shared mutable state, aliases, old units consumption, every decision and material/source request mutation. Restrict to I/F and record-local; S/E/Ec complete decisions must stay identical.'},
 {'issue':'positive, negative, null and evidence-only changes all affected','evidence':'Append/filter can alter current already-positive evidence as well as values.','requirement':'Full current gate closure plus input/baseline uncertainty; no selection by old0/1/null, ID, human77, disagreement, department or semantics judgment. Prove inherited mixed4474v7+7v8 baseline compatible with exact frozenv8 semantics or fallback.'},
 {'issue':'body access limit for independent closure review','evidence':'This phase opened only7 frozen130 packet bodies.','requirement':'Subsequent audit uses actual sealed candidate/selector/full manifest and lineage metadata first. Do not turn closure audit into semantic reading of unselected200/remaining bodies or independently run a classifier.'}
]
save('design-review-obligations.json',design_findings)
report={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'semantic_and_design_phase01_complete_candidate_adoption_not_yet_reviewed','frozen130_metadata':{'items':130,'unique_ids':98,'dimensions':dims,'review_classes_as_AI_diagnostic_not_gold':counts,'all130_match_frozen_selection_and_machine_values':True,'all98_exposed_and_disjoint_human200_remaining':True,'final_seal_outputs_verified':len(final_seal_checks),'02209_integrated_temporal_addendum_matches_and_old_phase_preserved':True},'focused_original_packet_reads':7,'focused_semantic_positions':positions,'exact_quote_pointer_checks':len(quote_checks),'care_selected_paragraph_text_hash_checks':len(care_pointers),'design_review_obligations':design_findings,'pending':['Actual revision02 design/control seal','C actual sealed candidate implementation','AST isolation, complete impact closure and mixedv7/v8 equivalence adoption audit'],'classification_runs':0,'labels_or_manual_or_production_modified':False,'new_human_judgment':False,'formal_validation':False,'all130_semantics_independently_adjudicated':False}
save('report.json',report)
lines=['# v9采用独立审计：语义与设计阶段','', '冻结130项元数据与原冻结集合逐项一致，98个ID均在exposed且排除human200/remaining；最终B报告为119更支持LLM、1更支持规则、10边界（仅代理诊断数量）。02209时态补充与保留旧阶段一致。仅新开7个指定原包，不把B的130项当金标准或全部重新审定。','', '## 重点原文结论','']
for p in positions:
    lines += ['- **'+','.join(p['ids'])+'**：'+p['reason']+' 约束：'+'；'.join(p['constraints'])]
lines+=['','## 采用前必须证明','']
for f in design_findings:lines+=['- **'+f['issue']+'**：'+f['requirement']]
lines+=['','当前阶段不采用v9：实际候选尚未到位，代码隔离、闭包及混合来源承接仍待审核。未分类重跑、改原封印或改标签。所用手册内容仅沿用B及前次复核提供的冻结引文，不声称再次核其外部全文。','']
(O/'report.md').write_text('\n'.join(lines))
for q in opened.values():assert bind(q['path'])==q
members=[bind(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='output-seal.json']
save('output-seal.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'members':members,'member_count':len(members),'inputs_unchanged':True,'candidate_adoption_approved':False})
print(json.dumps({'report':bind(O/'report.json'),'seal':bind(O/'output-seal.json'),'opened_packets':7,'quote_checks':len(quote_checks),'status':report['status']},ensure_ascii=False,indent=2))
