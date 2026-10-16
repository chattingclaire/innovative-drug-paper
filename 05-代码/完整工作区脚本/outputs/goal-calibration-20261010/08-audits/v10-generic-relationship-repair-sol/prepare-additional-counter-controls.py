from pathlib import Path
import json,copy,hashlib,datetime
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol';D=R/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation'
# These fresh fictional cases use previously exposed literal branch material;
# all fictional locations are explicit. No original packet or control changes.
sha='c'*64
def context(cid,kind,t,**loc):return {'context_id':cid,'kind':kind,'text':t,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':loc},'structure':loc.copy()}
cur='关于表征工具的选择或是否接受自行开发的评估工具，建议与药监机构进行沟通。'
contexts=[context('cur','paragraph',cur,paragraph_id='p0060',pages=[20])]
roles=[('published_title_and_notice','已发布《创新药临床试验工具指导原则》（见附件）。',[1],'p0'),('same_title_attachment_link','附件：创新药临床试验工具指导原则',[1],'p0'),('self_declared_scope','本指导原则涉及创新药临床试验的设计。',[4],'p0005'),('body_opening','一、概述',[4],'p0001'),('body_last_paragraph','正文最后一段。',[16,17],'p0057'),('actual_reference_component_boundary','参考文献',[18],'p0058')]
for seq,(role,t,pages,pid) in enumerate(roles):contexts.append(context('r'+str(seq),'source_fragment',t,source_role=role,component_id='fiction-component',physical_pages=pages,candidate_paragraph_id=pid,sequence_index=seq))
tools={'text':cur,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_ids':['p0060'],'physical_pages':[20]}},'contexts':contexts}
# Current recipient is explicitly independent-data other applicants; qualified
# original holders in the same supplied arrangement cannot donate that right.
cur='经审核符合药品试验数据保护条件的药品，按照《实施办法》有关规定执行。'
paragraph='其他申请人提交自行取得并未依赖他人受保护数据的申请。符合《实施办法》中给予药品试验数据保护条件的，' +cur
rights={'text':cur,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_ids':['p0002']}},'contexts':[context('cur','paragraph',paragraph,paragraph_id='p0002')],'source_bundle':{'explicit_or_primary_source_resources':[]},'derived_context_origins':{}}
source=json.loads((R/'06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-01382.json').read_bytes())['source_bundle']['explicit_or_primary_source_resources'][0]
doc={'source_resource_id':'fiction-articles','source_sha256':sha,'ordered_article_groups':[],'source_texts':[]}
for g in source['ordered_article_groups']:
 ids=[]
 for j,rid in enumerate(g['ordered_source_resource_ids'],1):
  x=next(x for x in source['source_texts'] if x['source_resource_id']==rid);newrid='fiction-'+str(len(doc['source_texts']));ti=len(doc['source_texts']);cid='clause-'+str(ti);ids.append(newrid)
  doc['source_texts'].append({'source_resource_id':newrid,'source_sha256':sha,'article':g['article'],'clause_index_one_based':j,'text':x['text']})
  rights['contexts'].append(context(cid,'source_resource_text',x['text']))
  rights['derived_context_origins'][cid]={'source_bundle_pointer':f'/explicit_or_primary_source_resources/0/source_texts/{ti}','source_resource_id':newrid,'origin_inventory_resource_id':newrid,'origin_inventory_view':'text','origin_inventory_view_sha256':hashlib.sha256(x['text'].encode()).hexdigest()}
 doc['ordered_article_groups'].append({'article':g['article'],'ordered_source_resource_ids':ids})
rights['source_bundle']['explicit_or_primary_source_resources'].append(doc)
cs=[]
for name,u,why in [('v10_tool_outside_attachment_body',tools,'同源附件明确创新范围但当前位于参考文献后，不能由同SHA复制创新对象。'),('v10_right_independent_data_recipient',rights,'当前明确为其他自行取数、未依赖原保护数据的申请人；同办法创新持有人待遇不能捐给该对象。')]:cs.append({'name':name,'semantic_input':u,'expected':{'I':0},'hard_assertion':True,'synthetic':True,'must_not_add_v10_positive':True,'semantic_reason':why})
p=A/'additional-counter-controls-fixed-before-attempt02.json'
with p.open('x') as f:json.dump({'cases':cs,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'no_old_control_changed':True},f,ensure_ascii=False,indent=2);f.write('\n')
with (A/'additional-counter-control-seal.json').open('x') as f:json.dump({'files':[{'path':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in [p,Path(__file__).resolve()]],'self_excluded':True},f,ensure_ascii=False,indent=2);f.write('\n')
# Static implementation repairs after counter expectations are frozen.
p=V/'relations.py';s=p.read_text();s=s.replace("actual=re.search(r'经确认的试点项目[，,][^。\\n]*受理临床试验申请后\\d+个工作日内完成审评审批[。]',raw)","actual=re.search(r'经确认的试点项目[，,][^。\\n]*受理临床试验申请后\\d+个工作日内完成审评审批[^。\\n]*[。]',raw)")
needle="        if not re.search(r'符合《[^》]+》中给予药品试验数据保护条件',norm(current['text'])):return\n"
s=s.replace(needle,needle+"        if re.search(r'其他申请人[^。；;]{0,40}自行取得[^。；;]{0,35}未依赖他人受保护数据',norm(current['text'])):return\n",1);p.write_text(s)
p=V/'run_finite_controls.py';s=p.read_text();s=s.replace("extra.append(AUD/'new-controls-fixed-before-edit.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])","extra.append(AUD/'new-controls-fixed-before-edit.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])\nextra.append(AUD/'additional-counter-controls-fixed-before-attempt02.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])")
s=s.replace("'new_counter_control_N':10","'new_counter_control_N':12")
s=s.replace("row['no_unproved_v10_positive']=not any(p['basis_path'].startswith('v10_') for d in ['I','F'] for p in row['candidate']['decisions'][d]['details'].get('positive_candidates',[])) and not any(row['candidate']['decisions'][d]['basis_path'].startswith('v10_') for d in ['I','F'])","row['no_unproved_v10_positive']=not any(r['kind']=='v10_IF_relationship' for r in row['candidate']['relations'])")
p.write_text(s)
print('2 additional counter controls frozen; actual operative review statement closure corrected')
