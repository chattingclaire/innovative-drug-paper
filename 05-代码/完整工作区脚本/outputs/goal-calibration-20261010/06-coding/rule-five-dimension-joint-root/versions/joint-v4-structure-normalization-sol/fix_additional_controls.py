"""ROOT-authorized two corrected positives and six semantic controls, before edits."""
import copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
P=Path(__file__).resolve().parent;G=P.parents[3];B=P.parent/'joint-v3-interface-sol'
def bind(p):
    p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def write(name,x):
    with (P/name).open('x',encoding='utf8')as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
full=json.loads((B/'controls18-fixed-before-edit.json').read_bytes())['cases'][6]['synthetic_input']
two=[]
for representation in ('integer','digit_string'):
    unit=copy.deepcopy(full)
    for c in unit['contexts']:
        st=c.get('structure',{})
        if st.get('article')=='第十条':value=10
        elif st.get('article')=='第十一条':value=11
        else:continue
        st['article']=value if representation=='integer'else str(value)
    two.append(dict(name=representation+' preserves original current and next article numbers',synthetic_input=unit,expected=dict.fromkeys(('S','E','Ec','I','F'),1),reason='原文第十条与真实下一条第十一条分别保留10/11；只改变元数据等价表达，不改变原文、段号、跨度或原末界。'))
write('controls2-numbering-positive-fixed.json',dict(identity='nonhuman newly authorized positives; original six conflicting fixtures retained',at_utc=datetime.now(timezone.utc).isoformat(),cases=two,new_actual_source_ids=[]))

def plain(text):
    sha=hashlib.sha256(text.encode()).hexdigest();ref=dict(sha256=sha,source_resource_id='SOURCE-'+sha,locator=dict(component_id='body',unicode_code_point_interval_half_open=[0,len(text)]))
    return dict(text=text,source_ref=ref,contexts=[dict(context_id='CURRENT',kind='paragraph',text=text,source_ref=copy.deepcopy(ref),structure=dict(component_id='body',paragraph_id='p1',sequence_index=0))])

def programme(current):
    texts=['专项研发协作计划','本计划的支持对象是创新药上市前研发项目，纳入后可预约专门团队获得研究方案反馈。',current,'申请表中的名称按统一字符格式填写。','二、文书管理']
    raw='\n'.join(texts)+'\n';sha=hashlib.sha256(raw.encode()).hexdigest();contexts=[];offset=0
    for i,t in enumerate(texts):
        ref=dict(sha256=sha,source_resource_id='SOURCE-'+sha,locator=dict(component_id='body',paragraph_id='p'+str(i+1),sequence_index=i,unicode_code_point_interval_half_open=[offset,offset+len(t)]))
        st=dict(component_id='body',paragraph_id='p'+str(i+1),sequence_index=i)
        contexts.append(dict(context_id='P'+str(i),kind='source_paragraph'if i<4 else'following_heading',text=t,source_ref=ref,structure=st));offset+=len(t)+1
    contexts[-1]['structure'].update(scope_context_ids=['P0','P1','P2','P3'],component_first_paragraph='p1',component_last_paragraph='p4',follows_context_id='P3')
    ref=copy.deepcopy(contexts[0]['source_ref']);ref['locator']={'component_id':'body'}
    contexts.append(dict(context_id='CONTAINER',kind='source_paragraph',text='',source_ref=ref,structure=dict(component_id='body',first_paragraph='p1',last_paragraph='p4')))
    c=copy.deepcopy(contexts[2]);c['kind']='paragraph';c['context_id']='CURRENT';contexts.append(c)
    return dict(text=current,source_ref=copy.deepcopy(c['source_ref']),contexts=contexts)
six=[]
def add(name,u,i=0,f=0,reason=''):
    six.append(dict(name=name,synthetic_input=u,expected=dict(S=0,E=0,Ec=0,I=i,F=f),reason=reason))
add('admitted same-plan current premarket feedback',programme('已纳入本计划的项目可预约团队对上市前研究方案给予书面反馈。'),i=1,reason='同版同组件完整唯一计划定义及纳入后实际机会，当前本计划指代和上市前阶段直接对应；不要求当前重复全名。')
add('same-plan postmarket routine feedback is not RND',programme('已纳入本计划的项目可预约团队对上市后日常监测方案给予书面反馈。'),reason='当前明确另一阶段常规服务，不能借上市前创新研发定义。')
add('same current semicolon anaphor comparative review convenience',plain('创新药研发项目可申请专用审评通道；其审评时限相较普通程序缩短十日。'),i=1,reason='同一完整当前命题明确对象和实际相对基准便利；分号后其承接同一研发项目。')
add('semicolon different drug cannot borrow innovation beneficiary',plain('创新药研发项目可申请专用审评通道；另一个药品的审评时限相较普通程序缩短十日。'),reason='时限便利明确属于另一药品，没有同一对象指代联系。')
add('substantive patient continuing treatment supply obstacle information',plain('须核验目标患者是否因药品供应不稳定而无法持续得到所需治疗。'),f=1,reason='当前实质要求核验具体持续治疗保障缺口；议题关注不要求补偿措施已经设置。')
add('ordinary logistics accessibility field and signature format',plain('须核验药品物流记录的可及性字段和签章格式是否完整。'),reason='只有物流、可及性栏目和格式，没有目标患者所需治疗的具体持续获取障碍。')
assert len(six)==6
write('controls6-semantic-fixed-before-edit.json',dict(identity='nonhuman finite semantic development controls, not independent truth',at_utc=datetime.now(timezone.utc).isoformat(),cases=six,new_actual_source_ids=[],hidden_v4_controls_read=False))
snap=P/'numbering-before-semantic-code-snapshot';snap.mkdir()
for n in ('source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py'):(snap/n).write_bytes((P/n).read_bytes())
manual=G/'03-manual/full4481-common-release-20261010-root/manual.txt';text=manual.read_text();lines=text.splitlines(keepends=True);quotes=[]
for line in (9,11,15,40,41,52,124,127,135,137,139,147,151,158,170,214):
    a=sum(map(len,lines[:line-1]));q=lines[line-1].rstrip('\r\n');b=a+len(q);assert text[a:b]==q
    ua,ub=len(text[:a].encode()),len(text[:b].encode());assert manual.read_bytes()[ua:ub].decode()==q
    quotes.append(dict(line=line,text=q,unicode_code_point_interval_half_open=[a,b],utf8_byte_interval_half_open=[ua,ub]))
write('additional-control-pre-edit-seal.json',dict(at_utc=datetime.now(timezone.utc).isoformat(),new_numbering2=bind(P/'controls2-numbering-positive-fixed.json'),new_semantic6=bind(P/'controls6-semantic-fixed-before-edit.json'),five_modules=[bind(snap/n)for n in ('source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py')],builder=bind(__file__),manual=bind(manual),manual_quotes=quotes,definition_changed=False,new_actual_source_ids=[]))
print('Two corrected numbering and six semantic controls fixed; numbering-stage code snapshot saved.')
