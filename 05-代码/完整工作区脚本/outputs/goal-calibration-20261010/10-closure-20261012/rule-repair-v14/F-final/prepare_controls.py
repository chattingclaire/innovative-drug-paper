from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];V=R/'06-coding/rule-five-dimension-joint-root/versions';B=V/'joint-v14f-form-gap-root';C=V/'joint-v14fb-form-gap-scope-root';OLD=HERE.parent/'F'
def bind(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(n,d):
 with (HERE/n).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
summary=json.loads((OLD/'candidate-summary.json').read_text())
for x in summary['core_files']:assert bind(Path(x['path']))==x
assert not C.exists();shutil.copytree(B,C,ignore=shutil.ignore_patterns('__pycache__'))
oldcontrols=json.loads((OLD/'form-gap-controls-fixed-before-edit.json').read_text());prototype=oldcontrols['cases'][0]['semantic_input']
def fixture(t):
 u=copy.deepcopy(prototype);old=u['text'];u['text']=t
 for ctx in u['contexts']:
  if ctx['kind'] in ('paragraph','source_textleaf'):
   assert ctx['text'].count(old)==1;ctx['text']=ctx['text'].replace(old,t)
 leaf=next(c for c in u['contexts'] if c['kind']=='source_textleaf');sha=hashlib.sha256(leaf['text'].encode()).hexdigest();leaf['source_ref']['locator']['unicode_code_point_interval_half_open']=[0,len(leaf['text'])]
 for obj in [u]+u['contexts']:obj['source_ref']['sha256']=sha;obj['source_ref']['source_resource_id']='SOURCE-'+sha
 return u
rows=[
 ('postposed_new_form_requirement_waived','(2)对于该药新剂型，现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型的条件无需满足。',0,'免除针对新适宜剂型的实质资格，不能凭被提及的词组构造缺口—适宜安排关系。'),
 ('postposed_gap_requirement_still_required','(2)对于该药新剂型，现有上市剂型均不适用于儿童人群的条件仍须满足，新剂型属于儿童人群适宜剂型。',1,'后置谓语确认实质缺口资格仍须满足。'),
 ('postposed_paper_waiver_only','(2)对于该药新剂型，现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型，纸质副本无需重复提交。',1,'独立材料提交豁免不取消既有当前实质资格。'),
 ('coordinated_paper_waiver_and_gap_proof','(2)对于该药新剂型，无需重复提交纸质副本并应当证明现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型。',1,'协调连接后的独立证明义务支配真实缺口；前一个否定仅支配重复递交。')]
cases=[{'name':n,'semantic_input':fixture(t),'expected':{'F':e},'hard_assertion':True,'is_human_reference':False,'fixture_only':True,'semantic_reason':why} for n,t,e,why in rows]
save('additional-scope-controls-fixed-before-edit.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'fixed_before_algorithm_edit':True,'cases':cases,'N':len(cases),'manual_basis':'冻结手册151–172：当前真实缺口须支配优先机会；材料形式豁免不取消独立实质资格；真实资格豁免不可按词组冒充。','original24_and_independent2_expected_unchanged':True})
paths=[OLD/'form-gap-controls-fixed-before-edit.json',OLD/'independent-controls-fixed-before-execution.json',HERE/'additional-scope-controls-fixed-before-edit.json'];entries=[]
for p in paths:
 d=json.loads(p.read_text());cs=d.get('real_cases',[])+d.get('cases',[]);entries.append({'binding':bind(p),'case_names':[c['name'] for c in cs],'N':len(cs),'select':'all real_cases + cases; no filtering or expectation edits'})
assert [x['N'] for x in entries]==[24,2,4]
save('fixed-input-index.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'purpose':'Unified ROOT integration may consume these exact controls without copying or relabelling. Original353 are deliberately not rerun in this bounded task.','entries':entries,'N':30,'expected_before_algorithm_edit':True,'shared353_rerun':False})
save('preparation.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'base_files':summary['core_files'],'base_summary':bind(OLD/'candidate-summary.json'),'author_external_review':bind(OLD/'independent-review.json'),'author_external_failed_results':bind(OLD/'independent-control-results.json'),'input_index':bind(HERE/'fixed-input-index.json'),'only_mutable_algorithm_file':'relations.py','only_mutable_helper':'RelationView._v14_form_gap_qualification','mutable_dimension':'F','protected_full_decisions':['S','E','Ec','I'],'source_state_equal_required':['material_requests','source_requests','source_events','private_I_requests'],'formal_validation':False,'production_execution':False,'adoption':False})
print('fixed',sum(x['N'] for x in entries))
