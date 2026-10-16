"""Fixed before first execution: true closure, clause scope and content controls."""
import json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from semantic_selfcheck import unit,context
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
P=Path(__file__).resolve().parent

def article(current='符合《药物条件规定》第七条规定的药品可以申请。',missing=False,wrong_sha=False,wrong_parent=False):
    cs=[context(current)]
    for t,cid,pid,i in [('第七条 药品应当符合以下条件：','CTX-H','p001',0),('（一）应核验本药过敏反应风险。','CTX-S','p002',1),('（二）应提供患者疾病控制效果证据。','CTX-E','p003',2),('（三）应证明本药治疗费用合理。','CTX-Ec','p004',3)]:
        c=context(t,'cited_article',cid,{'article':'第七条','clause':str(i) if i else '', 'paragraph_id':pid,'sequence_index':i});c['source_ref']['sha256']='b'*64;c['source_ref']['source_resource_id']='SOURCE-REF';cs.append(c)
    ids=[c['context_id'] for c in cs[1:]]
    cs.extend([
      {'context_id':'CTX-G','kind':'cited_reference','source_ref':cs[1]['source_ref'],'structure':{'child_groups':[{'position':'contexts','ordered_context_ids':ids},{'position':'structure_boundary','ordered_context_ids':['CTX-B']}] }},
      {'context_id':'CTX-B','kind':'boundary_container','source_ref':cs[1]['source_ref'],'structure':{'parent_context_id':'CTX-OTHER' if wrong_parent else 'CTX-G','first_paragraph':'p001','last_paragraph':'p004','next_paragraph_id':'p005','text_child_context_ids':['CTX-NEXT']}},
      context('第八条 药品应按规定格式签章。','boundary','CTX-NEXT',{'paragraph_id':'p005'}),
    ])
    cs[-1]['source_ref']={'sha256':('c' if wrong_sha else 'b')*64,'source_resource_id':'SOURCE-REF','locator':{}}
    if missing:cs=[c for c in cs if c['context_id']!='CTX-Ec'];cs[-3]['structure']['child_groups'][0]['ordered_context_ids'].remove('CTX-Ec')
    docs=[{'source_sha256':'b'*64,'byte_SHA_verified':True,'source_title_lines_verbatim_extraction_candidates':['药物条件规定','2024年3月1日']}]
    return unit(current,cs,docs)

def section(wrong_sha=False,wrong_address=False,missing=False):
    u=article();u['text']='符合本方案第一部分所列条件的药品可以申请。';u['contexts'][0]['text']=u['text'];u['source_bundle']['source_record']['text']=u['text']
    for c in u['contexts']:
        if c['context_id']=='CTX-G':c['structure']['reference_address']='第二部分' if wrong_address else '第一部分'
        if c['context_id']=='CTX-NEXT' and wrong_sha:c['source_ref']['sha256']='c'*64
    if missing:
        u['contexts']=[c for c in u['contexts'] if c['context_id']!='CTX-Ec'];u['source_bundle']['source_record']['contexts']=u['contexts']
        next(c for c in u['contexts'] if c['context_id']=='CTX-G')['structure']['child_groups'][0]['ordered_context_ids'].remove('CTX-Ec')
    return u

CASES=[
 ('article_complete_with_real_boundary',article(),{'S':1,'E':1,'Ec':1},'原件组首末和同源下一段明确且全部成员给出'),
 ('article_missing_period_final_member',article(missing=True),{'S':None,'E':None,'Ec':None},'各成员句号也不能补未供最后一项'),
 ('article_wrong_boundary_source',article(wrong_sha=True),{'S':None,'E':None,'Ec':None},'边界另一来源不能闭合同版'),
 ('article_wrong_boundary_parent',article(wrong_parent=True),{'S':None,'E':None,'Ec':None},'仅存在boundary不足，须父容器直接边'),
 ('article_clause_only_effect',article('符合《药物条件规定》第七条第二款规定的药品可以申请。'),{'S':0,'E':1,'Ec':0},'确指第二款不借第一第三款'),
 ('article_unknown_clause_no_expand',article('符合《药物条件规定》第七条第四款规定的药品可以申请。'),{'S':None,'E':None,'Ec':None},'缺指定款次不能把整条答案替代'),
 ('section_actual_closed_scope',section(),{'S':1,'E':1,'Ec':1},'地址第一部分与同源边界完整'),
 ('section_wrong_address',section(wrong_address=True),{'S':None,'E':None,'Ec':None},'其他部分不能为当前确指提供条件'),
 ('section_wrong_boundary_source',section(wrong_sha=True),{'S':None,'E':None,'Ec':None},'章节同源边界须实核'),
 ('section_missing_last_member',section(missing=True),{'S':None,'E':None,'Ec':None},'章节仅childgroups存在不足'),
]
for name,text,expected,basis in [
 ('actual_risk_evidence_submission','应提交本药安全性证据，并解释肝损伤信号。',{'S':1},'实际证据/解释与纯上传分开'),
 ('actual_safety_evidence_only','申请人应提交本药安全性证据。',{'S':1},'提交对象是证据内容而非文件名'),
 ('actual_effect_evidence_only','申请人应提交本药疾病控制效果证据。',{'E':1},'实质疗效证据要求'),
 ('risk_evidence_with_filename','应核验本药安全性信息表中的肝损伤信号，文件名须采用编号。',{'S':1},'混合形式句保留独立内容命题'),
 ('safe_effective_title_identity','该药品已经获得“安全有效产品”的称号。',{'S':0,'E':0},'名称身份不等于实质判断'),
 ('latin_other_word_near_miss','药品申报系统的TEAM字段仅供机构编码。',{'S':0},'AE不可从英文其他词中截出'),
 ('negative_efficacy_content','无证据证明该药能够达到疾病控制效果，应补充分层疗效估计。',{'E':1},'否定内容仍是效果'),
 ('non_drug_data_risk','药品研究应评估数据泄漏和数据库损毁风险。',{'S':0},'风险主体为数据'),
]:CASES.append((name,unit(text),expected,basis))
for name,current,paragraph,expected in [
 ('same_paragraph_other_cost','如协商不能达成一致，以主管机构的记录为准。','本药基金实际支出存在分歧。另一药品如协商不能达成一致，以主管机构的记录为准。',{'Ec':0}),
 ('same_paragraph_other_risk','这些特殊指标应报告。','本药安全性观察指标应核验。另一药品这些特殊指标应报告。',{'S':0,'E':0}),
 ('same_paragraph_other_effect','应说明试验药物需求。','其他药物使用患者获益的临床终点。应说明试验药物需求。',{'E':0}),
]:CASES.append((name,unit(current,[context(paragraph)]),expected,'同段独立药物/事项不能互借'))

def run():
    out=[]
    for name,u,expected,basis in CASES:
        v=RelationView(u);d=judge(v);validate_decisions(u,d);a={dim:d[dim]['value'] for dim in expected}
        out.append({'name':name,'synthetic_input':u,'expected_fixed_before_execution':expected,'manual_rationale':basis,'actual':a,'passed':a==expected,'decisions':d,'relations':v.traces()})
    result={'non_human_development_control':True,'test_N':len(out),'failed_N':sum(not x['passed'] for x in out),'tests':out,'formal_gate':False}
    with (P/sys.argv[1]).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'test_N':len(out),'failed':[x['name'] for x in out if not x['passed']]},ensure_ascii=False))
if __name__=='__main__':run()
