from pathlib import Path
import hashlib,json,shutil,copy,datetime
root=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
v2=root/'06-coding/rule-v20-semantic-audit-repair-sol/versions/v2'
v3=v2.parent/'v3'
v3.mkdir(exist_ok=False)
names=['source_packet','source_receipts','evidence','relations','dimensions']
for name in names+['regression_tests','interface_common']:
 shutil.copyfile(v2/(name+'.py'),v3/(name+'.py'))
def bind(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,x):
 (v3/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
audit=root/'08-audits/IF-v2-independent-controls-sol'
raw=(audit/'controls-fixed-before-execution.json').read_bytes()
(v3/'independent20-original-controls.json').write_bytes(raw)
sha='a'*64
ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{}}
def ctx(cid,kind,text,locator=None,structure=None):
 rr=copy.deepcopy(ref);rr['locator']=locator or {}
 return {'context_id':cid,'kind':kind,'text':text,'source_ref':rr,'structure':structure or {}}
def unit(text,contexts=None,locator=None):
 rr=copy.deepcopy(ref);rr['locator']=locator or {}
 return {'text':text,'source_ref':rr,'contexts':contexts or [ctx('current','paragraph',text,locator)]}
def full(text,raw):
 return unit(text,[ctx('current','paragraph',text),ctx('literal','source_textleaf',raw,{'unicode_code_point_interval_half_open':[0,len(raw)],'utf8_byte_interval_half_open':[0,len(raw.encode())]})])
cases=[]
def add(name,u,i,f,reason):cases.append({'name':name,'synthetic_input':u,'expected':{'I':i,'F':f},'manual_reason':reason,'identity':'nonhuman AI development scope control','expectation_fixed_before_v3_edits':True})
parent='符合下列条件的药品，可以申请优先审评支持：'
text='（一）境内尚无药物获批用于该疾病。'
raw=parent+'\n'+text
add('origin_adjacent_first_need',unit(text,[ctx('current','paragraph',text,{'unicode_code_point_interval_half_open':[len(parent)+1,len(raw)]}),ctx('parent','preceding_paragraph',parent,{'unicode_code_point_interval_half_open':[0,len(parent)]})]),0,1,'实际首项与同源紧邻操作性父句；当前无获批治疗选项连接优先机会。')
remote=parent+'\n第二章 常规材料\n其他药品须填写材料页码。\n'+text
add('origin_remote_role_conflict',unit(text,[ctx('current','paragraph',text,{'unicode_code_point_interval_half_open':[remote.index(text),len(remote)],'chapter_id':'chapter-2'}),ctx('parent','preceding_paragraph',parent,{'unicode_code_point_interval_half_open':[0,len(parent)],'chapter_id':'chapter-1'})]),0,None,'坐标明示跨章远段，不能以preceding角色借用；实际首项缺真实父谓词登记F补材。')
add('origin_other_list_conflict',unit(text,[ctx('current','paragraph',text,{'list_id':'list-B'}),ctx('parent','preceding_paragraph',parent,{'list_id':'list-A'})]),0,None,'定位明确不同清单，禁止继承另一清单的机会；保留F补材。')
name='定向研究服务程序'
scope='本程序适用创新药研发项目。'
text='对纳入定向研究服务程序的项目，药审中心在临床试验阶段提供下一步研究方案反馈。'
raw=name+'\n一、适用范围\n'+scope+'\n二、上市前技术服务\n'+text+'\n三、上市后日常工作\n已上市品种应报送例行监测资料。\n'
add('current_premarketing_feedback',full(text,raw),1,0,'当前临床研发服务与同版适用对象直接相连。')
text='对纳入定向研究服务程序的项目，药审中心在上市后日常监测会议中反馈例行填表说明。'
raw=name+'\n一、适用范围\n'+scope+'\n二、上市前技术服务\n药审中心在临床试验阶段提供下一步研究方案反馈。\n三、上市后日常工作\n'+text+'\n'
add('same_name_other_stage_cannot_borrow',full(text,raw),0,0,'当前明确上市后日常监测与填表说明，不能借临床试验研发反馈。')
text='对定向研究服务程序中的甲类项目，药审中心在临床试验阶段提供普通研究方案反馈。'
raw=name+'\n一、适用范围\n甲类项目为创新药研发项目；乙类项目为用于尚无有效治疗手段疾病的药物项目。\n二、技术服务\n'+text+'\n对乙类项目优先安排研究方案咨询。\n'
add('different_need_object_branch',full(text,raw),1,0,'当前只给创新甲类普通反馈，不借乙类治疗缺口的优先安排。')
text='对定向研究服务程序的甲类和乙类项目，药审中心在临床试验阶段均优先提供研究方案反馈。'
raw=name+'\n一、适用范围\n甲类项目为创新药研发项目；乙类项目为用于尚无有效治疗手段疾病的药物项目。\n二、技术服务\n'+text+'\n'
add('same_priority_applies_each_qualified_branch',full(text,raw),1,1,'当前同一优先服务明确适用甲乙两类，分别保留创新对象与需求缺口。')
text='药审中心不批准依赖该药品受保护数据的申请。'
paragraph='本条创新药具有新作用机制，给予该药品数据保护期。'+text
add('same_article_right_object',unit(text,[ctx('current','paragraph',paragraph),ctx('definition','source_paragraph',paragraph)]),1,0,'同条同一药品的明文创新资格及保护后果承接当前不批准依赖申请。')
paragraph='本条普通药品符合一般数据保密登记条件。'+text
sibling='另一条规定，其他创新药具有新作用机制，给予其数据保护期。'
add('sibling_drug_right_cannot_borrow',unit(text,[ctx('current','paragraph',paragraph),ctx('brother','source_paragraph',sibling)]),0,0,'当前普通药品数据操作，明文不同药品兄弟条款不提供创新资格。')
# Structural document reference: the current question explicitly belongs to a
# different named document despite an incidental acronym elsewhere in its parent.
text='对于普通记录指南未能阐明的具体技术问题，申请人可以与药审中心沟通。'
prior='RDP是创新药临床试验的研究文档。'
container='本段先存档RDP编号。'+text
add('different_named_document_consultation',unit(text,[ctx('current','paragraph',text),ctx('prior','parent_paragraph',prior,structure={'unit_id':'same-parent','sequence_index':0}),ctx('container','parent_paragraph',container,structure={'unit_id':'same-parent','sequence_index':1})]),0,0,'当前问题明确属于另一普通指南，父段仅偶然出现研发文档缩写，不提供相同对象承接。')
text='对于RDP未能阐明的具体技术问题，申请人可以与药审中心沟通。'
add('same_named_document_consultation',unit(text,[ctx('current','paragraph',text),ctx('prior','parent_paragraph',prior,structure={'unit_id':'same-parent','sequence_index':0}),ctx('container','parent_paragraph',text,structure={'unit_id':'same-parent','sequence_index':1})]),1,0,'同一直接父单元唯一研发文档就是当前未解决问题的确指对象。')
text='药品监管会议采用新颖的内部值班流程，要求比较各办公室的排班创新性。'
add('administrative_novelty_owner',unit(text),0,0,'新颖性/创新性修饰内部会议值班及办公室排班，不是药品技术新颖内容。')
write('scope-controls-fixed-before-execution.json',{'identity':'nonhuman AI development; scope controls not independent gold','cases':cases,'case_N':len(cases),'expected_changed':False,'formal_records_used':0,'manual_changed':False})
manual=root/'03-manual/full4481-common-release-20261010-root/manual.txt'
write('v3-input-scope-binding.json',{'identity':'nonhuman AI candidate repair','manual':bind(manual),'origin_modules':[bind(v2/(n+'.py'))for n in names],'origin_regression':bind(v2/'regression_tests.py'),'independent_audit_files':[bind(audit/n)for n in ['controls-fixed-before-execution.json','output-seal.json','findings.json','authority-and-manual-basis.json']],'origin_v2_seal':bind(v2/'delivery/delivery-seal.json'),'scope':'六类已执行问题与有限关系范围守卫；不修改手册、材料、v2；不重跑77/800/4481；foreign预期0/实际NULL保持边界','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(v3)
