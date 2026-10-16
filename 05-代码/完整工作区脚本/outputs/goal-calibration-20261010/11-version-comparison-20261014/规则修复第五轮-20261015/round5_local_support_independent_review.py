"""Independent read-only probes: source fixtures remain unchanged."""
from pathlib import Path
import copy,hashlib,json,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
e={'__file__':str(P/'round5_local_support_tests.py')};exec((P/'round5_local_support_tests.py').read_text().split('results = []')[0],e)
units=e['units'];current=e['current'];replace=e['replace_strings'];out=[]
before={name:hashlib.sha256((P/'code'/name).read_bytes()).hexdigest() for name in ['dimensions.py','relations.py']}
def synthetic(u):
 old=u['source_ref']['sha256'];sha=hashlib.sha256(('SYNTHETIC_INDEPENDENT_REVIEW'+json.dumps(u,ensure_ascii=False,sort_keys=True)).encode()).hexdigest();u=replace(u,old,sha)
 def walk(x):
  if isinstance(x,list):return [walk(v) for v in x]
  if isinstance(x,dict):
   d={k:walk(v) for k,v in x.items()}
   if isinstance(d.get('text'),str):
    for field in ['text_sha256','text_utf8_sha256']:
     if field in d:d[field]=hashlib.sha256(d['text'].encode()).hexdigest()
   return d
  return x
 return walk(u)
def record(name,key,u,expected):
 v=e['RelationView'](u);d=e['judge'](v);e['validate_decisions'](v.unit,d);decision=d['I'];paths=[decision['basis_path']]+[x['basis_path'] for x in decision.get('details',{}).get('additional_evidence',[])]
 actual=e['PATHS'][key] in paths
 out.append({'name':name,'target':key,'current':u['text'],'expected_path':expected,'actual_path':actual,'I':decision['value'],'passed':actual==expected,'decision':decision})
for key,u in units.items():record('original_'+key,key,u,True)
# Clearly another project cannot inherit the preceding project's technical
# research feedback merely because the phrase "沟通交流过程中" repeats.
u=units['04169']
record('other_project_administrative_meeting','04169',synthetic(current(u,'另一个项目的行政沟通交流过程中,必要时应邀请中检院、核查中心参加。')),False)
# An explicit object qualification after the named service cannot be ignored.
u=copy.deepcopy(units['04189'])
for c in u['contexts']:
 if c['kind']=='paragraph':
  c['text']=c['text'].replace('药审中心优先组织专家咨询会(鼓励线上会议)', '药审中心优先组织专家咨询会(该优先安排只适用于其他项目，当前会议按普通流程组织)')
record('priority_only_for_other_projects','04189',synthetic(u),False)
# A clerical restriction on the secretary's own task does not cancel the
# parallel, still-explicit substantive technical service.
for key in ['03452','04169']:
 u=units[key]
 record('actual_service_plus_secretary_record_'+key,key,synthetic(current(u,u['text'].rstrip('。')+'，秘书仅记录会议开始时间。')),True)
# Preserve the original current service but explicitly close its own scope
# differently from the supplied innovation subsection.
u=units['04169'];record('current_service_for_postmarketing_only','04169',synthetic(current(u,'上市后常规服务的沟通交流过程中,必要时应邀请中检院、核查中心参加。')),False)
# Full scope member missing must not become an assumed zero or positive.
for key in ['04169','04189']:
 u=copy.deepcopy(units[key]);boundary=next(c for c in u['contexts'] if c.get('structure',{}).get('scope_context_ids'))
 cid=boundary['structure']['scope_context_ids'][2];u['contexts']=[c for c in u['contexts'] if c['context_id']!=cid]
 record('missing_scope_member_'+key,key,synthetic(u),False)
after={name:hashlib.sha256((P/'code'/name).read_bytes()).hexdigest() for name in before};assert before==after
report={'scope':'independent finite implementation review; no source/label/code edits','code_sha256':before,'passed':sum(r['passed'] for r in out),'total':len(out),'cases':out}
(P/'round5-local-support-independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passed'],'total':len(out),'cases':[{k:r[k] for k in ['name','actual_path','I','passed']} for r in out]},ensure_ascii=False,indent=2))
