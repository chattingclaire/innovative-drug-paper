"""Fixed consumer and source-binding checks; no corpus labels."""
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from semantic_selfcheck import unit,context
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
P=Path(__file__).resolve().parent

def linked(dims=None,ifonly=False,kind='parent_predicate'):
 text='该品种应按要求执行。';u=unit(text,[context(text),context('本药安全性证据应核验，治疗费用应测算。','source_paragraph','CTX-REL')]);v=RelationView(u)
 details={'relation_subtype':'SE_test_consumer_permission','shared_predicate':'本药安全性证据应核验，治疗费用应测算。','affected_dimensions':dims,'only_IF_consumers':ifonly}
 if kind=='price_arrangement':details.update(relation_subtype='same_edition_price_node_content_definition',version_binding={'established':True},direct_mapping=True)
 v._add(kind,[v._quote(v.by_id['CTX-REL'],'显式受限关系测试')],'测试仅指定消费者',**details)
 return u,v

CASES=[]
for name,dims,ifonly,kind,expected in [
 ('SE_only_relation_no_IF',['S','Ec'],False,'parent_predicate',{'S':1,'Ec':1,'I':0,'F':0}),
 ('I_only_relation_no_SE',['I'],False,'parent_predicate',{'S':0,'Ec':0}),
 ('IF_flag_and_SE_list_intersection_empty',['S','Ec'],True,'parent_predicate',{'S':0,'E':0,'Ec':0,'I':0,'F':0}),
 ('price_relation_explicit_I_only',['I'],False,'price_arrangement',{'Ec':0}),
 ('price_relation_only_IF',['I','F'],True,'price_arrangement',{'Ec':0}),
]:CASES.append((name,*linked(dims,ifonly,kind),expected))
for name,current,para,sha,component in [
 ('foreign_same_paragraph_no_content','如协商不能达成一致，以医保方数据为准。','本药基金实际支出存在分歧。如协商不能达成一致，以医保方数据为准。','b'*64,None),
 ('other_component_same_paragraph_no_content','如协商不能达成一致，以医保方数据为准。','本药基金实际支出存在分歧。如协商不能达成一致，以医保方数据为准。','a'*64,'other'),
]:
 u=unit(current,[context(current),context(para,'paragraph','CTX-NOM')]);u['contexts'][1]['source_ref']['sha256']=sha
 if component:u['source_ref']['locator']['component_id']='current';u['contexts'][1]['structure']['component_id']=component
 CASES.append((name,u,RelationView(u),{'Ec':0}))

out=[]
for name,u,v,expected in CASES:
 d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in expected};out.append({'name':name,'synthetic_input':u,'expected_fixed_before_execution':expected,'actual':a,'passed':a==expected,'decisions':d,'relations':v.traces()})
with (P/sys.argv[1]).open('x') as f:json.dump({'test_N':len(out),'failed_N':sum(not t['passed'] for t in out),'tests':out,'formal_gold':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'test_N':len(out),'failed':[(t['name'],t['actual']) for t in out if not t['passed']]},ensure_ascii=False))
