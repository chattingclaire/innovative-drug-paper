"""Freeze actual consistent-order counterparts following ROOT independent reread."""
import copy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
old={c['name']:c for c in json.loads((P/'geometry-controls-fixed-before-edit.json').read_text())['cases']}
cases=[]
def clone(oldname,newname,expect):
    c=copy.deepcopy(old[oldname]);c.update(name=newname,expected=expect,manual_reason='手册限定必要语境与当前承接；已供同源位置冲突不能据角色或target强连。无跨度保留冻结有界结构接口，但不宣称原文邻接独立核定。');cases.append(c);return c
def correct(c):
    r=c['synthetic_bundle']['source_record'];cur=next(x for x in r['contexts'] if x['context_id']=='CURRENT');parent=next(x for x in r['contexts'] if x['context_id']=='PARENT')
    raw=parent['text']+'\n'+cur['text']+'\n';sha=hashlib.sha256(raw.encode()).hexdigest()
    parent['source_ref']['locator']['unicode_code_point_interval_half_open']=[0,len(parent['text'])]
    cur['source_ref']['locator']['unicode_code_point_interval_half_open']=[len(parent['text'])+1,len(raw)-1]
    r['source_ref']=copy.deepcopy(cur['source_ref'])
    for z in [r]+r['contexts']:
        z['source_ref']['sha256']=sha;z['source_ref']['source_resource_id']='SOURCE-SYNTHETIC-'+sha
    c['synthetic_documents']=[{'sha256':sha,'text':raw,'is_synthetic':True,'is_original_policy':False}]
    return c
correct(clone('near_payment_parent','consistent_original_order_payment_parent',{'S':0,'E':0,'Ec':1}))
correct(clone('near_safety_parent','consistent_original_order_safety_parent',{'S':1,'E':0,'Ec':0}))
clone('near_payment_parent','contradictory_source_order_payment_parent',{'S':0,'E':0,'Ec':0})
clone('near_safety_parent','contradictory_source_order_safety_parent',{'S':0,'E':0,'Ec':0})
c=clone('near_payment_parent','no_span_bounded_target_payment_parent',{'S':0,'E':0,'Ec':1})
r=c['synthetic_bundle']['source_record']
for z in [r]+r['contexts']:z['source_ref']['locator'].pop('unicode_code_point_interval_half_open',None)
with (P/'root-position-controls-fixed.json').open('x',encoding='utf8') as f:json.dump({'status':'fixed_after_ROOT_independent_position_review_before_position_patch','cases':cases,'case_N':len(cases),'original_expectations_and_fixtures_unchanged':True},f,ensure_ascii=False,indent=2);f.write('\n')
