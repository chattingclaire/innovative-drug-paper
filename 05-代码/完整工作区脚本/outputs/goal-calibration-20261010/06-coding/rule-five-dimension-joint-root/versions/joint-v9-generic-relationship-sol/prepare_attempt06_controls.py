from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent
ref={'sha256':'a'*64,'source_resource_id':'SOURCE-'+'a'*64,'locator':{}}
def bind(p):b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def ctx(cid,kind,text,structure):return {'context_id':cid,'kind':kind,'source_document':'NEUTRAL','source_ref':dict(ref,locator=structure.copy()),'structure':structure,'text':text}
def case(name,text,expected,contexts=[]):return {'name':name,'semantic_input':{'text':text,'source_ref':ref,'contexts':contexts},'expected':expected,'hard_assertion':True,'synthetic':True,'semantic_reason':'在代码修改前固定的实际受益对象与直接父治理关系反例；不依据模型标签或分数'}
cs=[case('named_other_need_beneficiary','药品甲无有效治疗手段，药品乙实行优先审评。',{'F':0}),case('named_same_need_beneficiary','药品甲无有效治疗手段，药品甲实行优先审评。',{'F':1}),case('named_other_need_advantage_beneficiary','药品甲无有效治疗手段，药品乙凭临床优势实行优先审评。',{'F':0}),case('AI_ordinary_recording_not_RND_support','药品研发采用AI进行普通材料录入，按时提交备案。',{'I':0})]
parent='一、纳入技术研发通道的药物临床试验申请，应为1类创新药临床试验，并需满足以下条件之一：'
member='（一）重点创新药品种。'
items=[ctx('N0','ordered_members',parent,{'paragraph_id':'p0','sequence_index':0,'source_lines':[1],'parent_context_id':'G'}),ctx('N1','ordered_members',member,{'paragraph_id':'p1','sequence_index':1,'source_lines':[3],'parent_context_id':'G'})]
boundary=ctx('B','boundary','二、其他常规事项。',{'source_lines':[5],'parent_context_id':'BC'})
bc=ctx('BC','boundary_container','',{'first_paragraph':'p0','last_paragraph':'p1','parent_context_id':'G','child_groups':[{'position':'next_structure','ordered_context_ids':['B']}]})
group=ctx('G','source_list','',{'child_groups':[{'position':'contexts','ordered_context_ids':['N0','N1']},{'position':'structure_boundary','ordered_context_ids':['BC']}]})
base=[ctx('CP','paragraph',member,{'paragraph_id':'p1','sequence_index':0}),ctx('PP','parent_paragraph',parent,{'paragraph_id':'p0','sequence_index':0})]+items+[group,bc,boundary]
cs.append(case('direct_parent_closed_ordered_member',member,{'I':1},base))
cs.append(case('parent_role_without_governing_edge',member,{'I':0},base[:2]))
wrong=json.loads(json.dumps(base));wrong[3]['text']='（一）其他常规药品。'
cs.append(case('ordered_group_different_actual_member',member,{'I':0},wrong))
value={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':cs,'expected_frozen_before_edit':True}
q=P/'supplemental-controls-before-attempt06.json';q.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
seal={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controls':bind(q),'pre_edit_actual_code':[bind(P/(n+'.py')) for n in ['evidence','source_packet','source_receipts','relations','dimensions']],'attempt05_preserved':bind(P/'attempt05-frozen-controls/output-seal.json')}
(P/'supplemental-seal-before-attempt06.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
