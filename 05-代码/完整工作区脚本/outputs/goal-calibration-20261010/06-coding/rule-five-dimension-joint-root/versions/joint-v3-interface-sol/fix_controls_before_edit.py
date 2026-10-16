"""Freeze finite source-only controls and manual basis before candidate edits."""
import copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent
G=P.parents[3]
MANUAL=G/'03-manual/full4481-common-release-20261010-root/manual.txt'
DIMS=('S','E','Ec','I','F')
def bind(path):
 p=Path(path).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def dump(name,value):
 with (P/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def source(current,extras=()):
 parts=[current]+[x[1] for x in extras];raw='\n'.join(parts);sha=hashlib.sha256(raw.encode()).hexdigest();contexts=[];pos=0
 for index,(kind,text,structure) in enumerate([('paragraph',current,{'paragraph_id':'p1','sequence_index':1})]+list(extras)):
  st={'component_id':'body',**structure};ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'component_id':st['component_id'],'unicode_code_point_interval_half_open':[pos,pos+len(text)]}}
  contexts.append({'context_id':'CTX-'+str(index),'kind':kind,'text':text,'source_ref':ref,'structure':st});pos+=len(text)+1
 return {'text':current,'contexts':contexts,'source_ref':copy.deepcopy(contexts[0]['source_ref'])}, {sha:raw}
def zero(**values):return {d:values.get(d,0) for d in DIMS}
cases=[]
def add(name,text,expect,reason,extras=(),ops=()):
 unit,docs=source(text,extras)
 cases.append({'name':name,'synthetic_input':unit,'synthetic_documents':docs,'post_view_operations':list(ops),'expected':expect,'manual_reason':reason,'input_kind':'synthetic_finite_near_neighbour','no_unprovided_file_read_allowed':True})
add('current innovation RND feedback service','本中心为创新药研发项目开放研发技术反馈服务。',zero(I=1),'I3: current explicit innovation RND object, available technical feedback service and beneficiary connection.')
add('innovation object receipt-status notice','本中心为创新药研发项目发送受理状态通知。',zero(),'A receipt notice is not actual RND technical support.')
add('other product feedback service','创新药研发为讨论对象，本中心为其他药品研发项目开放研发技术反馈服务。',zero(),'The actual service belongs to another drug object.')
add('current innovative RND comparative review convenience','创新药研发项目相较普通程序缩短审评时限。',zero(I=1),'I3: innovation RND subject receives an explicitly comparative review convenience; no conclusion from number alone.')
add('innovation numeric deadline alone','创新药研发项目的审评时限为60日。',zero(),'The number alone does not prove an accelerated support arrangement.')
add('ordinary administrative time innovation modifier','药品审评办公室创新排班方式，值班记录提交时限缩短。',zero(),'The innovation modifies administrative work, not drug innovation or RND support.')
full='第十条 药品应评价安全性、有效性、经济性、创新性和公平性。'
end='第十一条 文件递交时应签章。'
extras=[('cited_article',full,{'article':'第十条','paragraph_id':'p10','sequence_index':10}),('source_paragraph',end,{'article':'第十一条','paragraph_id':'p11','sequence_index':11})]
add('complete operational five-dimensional standard','本药品必须满足本办法第十条实质标准，方可取得申请资格。',zero(S=1,E=1,Ec=1,I=1,F=1),'Current requirement uses a complete same-version exact standard; each dimension consumes only its actual content.',extras)
add('nonoperative parallel article contents','本药品的文件递交时须核对签章。',zero(),'A complete parallel standard is available but has no current operative reference.',extras)
clause1='第十条第一款 药品应评价创新性。';clause2='第十条第二款 药品应评价公平性。'
add('explicit clause rejects boundary sibling content','本药品必须满足本办法第十条第一款实质标准。',zero(I=1),'The next clause proves closure only and cannot donate its F content.',[('cited_article',clause1,{'article':'第十条','clause':'第一款','paragraph_id':'p10','sequence_index':10}),('cited_article',clause2,{'article':'第十条','clause':'第二款','paragraph_id':'p11','sequence_index':11})])
risk='第十条 药品应核验过敏风险。'
partial=[('cited_article',risk,{'article':'第十条','paragraph_id':'p10','sequence_index':10}),('source_paragraph',end,{'article':'第十一条','paragraph_id':'p11','sequence_index':11})]
add('missing second standard keeps independent risk','本药品必须满足本办法第十条和第十二条实质标准，方可取得申请资格。',{'S':1,'E':None,'Ec':None,'I':None,'F':None},'An independent delivered closed allergy criterion supports S; missing article12 makes the remaining unknown branches NULL and cannot be cleared by article10 resolution.',partial)
add('unprovided exact standard path remains missing','本药品必须满足本办法第十二条实质标准。',{d:None for d in DIMS},'An exact necessary standard is absent; the synthetic source ref never authorizes opening unavailable originals.')
for name,scope,ifonly,expect in [('typed I consumer only',['I'],False,zero(I=1)),('typed F consumer only',['F'],False,zero(F=1)),('only IF intersects incompatible SE subset',['S','E','Ec'],True,zero()),('only IF intersects mixed subset',['S','I','F'],True,zero(I=1,F=1))]:
 quote='本药品的创新性和公平性应作实质评价。'
 op={'kind':'cited_standard','context_id':'CTX-1','usage':'finite supplied substantive information relation','reason':'synthetic typed consumer interface only','details':{'relation_subtype':'synthetic_typed_consumer_control','affected_dimensions':scope,'only_IF_consumers':ifonly},'synthetic_test_API_operation_not_source_claim':True}
 add(name,'本药品须提交实质报告。',expect,'Typed dimensions and only_IF restrictions intersect; the generic evaluation consumer must respect the intersection.',[('source_paragraph',quote,{'paragraph_id':'p2','sequence_index':2})],[op])
add('five-dimensional filename with formal check','药品附件文件名称为《安全性有效性经济性创新性公平性报告》，不得从文件名推断实质内容，仅核对签章。',zero(),'Dimension words belong only to a filename and are explicitly denied as substantive content; the current action only checks seals.')
add('filename plus independent innovation evaluation','药品附件文件名称为《创新性公平性报告》，仅核对签章；此外应实质评价药品创新性。',zero(I=1),'An independent current I evaluation survives; the filename does not establish F.')
add('ordinary public design guideline','创新药研发可参考本技术指导原则完善设计。',zero(),'A general public reference cannot be relabelled as an actual dedicated support service.')
assert len(cases)==18
raw=MANUAL.read_bytes();text=raw.decode();assert bind(MANUAL)['sha256']=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
phrases=['当前把具名标准作为申请或实质待遇的条件时，可用共同材料中同版该标准的确切定义及完整并列范围解释其内容；不要求当前逐项重写定义。','创新/改良研发须是该安排的对象选择条件、支持目标或实际适用依据；须保存对象、当前支持安排及二者关系。','时限用于实质支持须有原文加快/优先关系、明确相对基准或合规具名机制联系，不能仅凭数字猜更快。','只有栏目名、字段非空、格式或材料流转不成立。','五维逐一判断，不能因I/F难判把其他可判维也清空。']
quotes=[]
for phrase in phrases:
 assert text.count(phrase)==1,phrase;a=text.index(phrase);b=a+len(phrase)
 quotes.append({'text':phrase,'unicode_interval_half_open':[a,b],'UTF8_interval_half_open':[len(text[:a].encode()),len(text[:b].encode())],'line_1based':text[:a].count('\n')+1,'source':bind(MANUAL)})
dump('manual-basis-fixed-before-edit.json',{'manual':bind(MANUAL),'quotes':quotes,'manual_changed':False})
dump('controls18-fixed-before-edit.json',{'status':'fixed_before_any_joint_v3_module_edits','at_utc':datetime.now(timezone.utc).isoformat(),'case_N':len(cases),'cases':cases,'expectations_are_nonhuman_development_assertions_not_gold':True,'new_actual_source_ids':[]})
dump('control-pre-edit-seal.json',{'builder':bind(__file__),'controls':bind(P/'controls18-fixed-before-edit.json'),'manual_basis':bind(P/'manual-basis-fixed-before-edit.json'),'baseline_modules':[bind(P/(n+'.py')) for n in ['relations','dimensions','source_packet','source_receipts','evidence']],'case_N':18,'new_actual_source_ids':[]})
print('Fixed 18 controls, manual5ea7 and unchanged baseline modules.')
