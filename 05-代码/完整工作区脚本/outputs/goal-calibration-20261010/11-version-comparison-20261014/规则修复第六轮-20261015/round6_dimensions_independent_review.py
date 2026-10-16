"""Independent semantic boundary probes; synthetic in-memory inputs only."""
from pathlib import Path
import json,hashlib,copy
P=Path(__file__).resolve().parent
ns={'__file__':str(P/'round6_dimensions_tests.py')}
exec((P/'round6_dimensions_tests.py').read_text().split('results=[]')[0],ns)
globals().update({k:ns[k] for k in ['units','RelationView','judge','validate_decisions','current','variant','fix','walk']})
results=[]
def probe(name,k,u,expected,explanation):
 before=hashlib.sha256((P/'code/dimensions.py').read_bytes()).hexdigest()
 if not name.startswith('original_'):
  sha=u['source_ref']['sha256']; synthetic=hashlib.sha256(('INDEPENDENT_SYNTHETIC:'+name).encode()).hexdigest()
  u=fix(walk(u,lambda s:s.replace(sha,synthetic)))
 v=RelationView(u); ds=judge(v); validate_decisions(v.unit,ds)
 labels={k:d['value'] for k,d in ds.items()}
 results.append({'name':name,'target':k,'current':u['text'],'expected':expected,'labels':labels,'passed':all(labels[d]==n for d,n in expected.items()) and (name!='catalogue_not_actual_requirement' or '还明确提出增设目录' not in ds['Ec']['reason']),'explanation':explanation,'decisions':ds,'requests':v.material_requests,'sha':before})
for k,w in [('03423',{'S':1,'E':1}),('03919',{'S':1}),('03780',{'Ec':1})]:probe('original_'+k,k,units[k],w,'unchanged baseline')
u=units['03423']
probe('elderly_scope_excludes_list','03423',current(u,u['text'].rstrip('。')+'，但此处考虑的特征仅指身高体重，下列用药风险和药效变化不属于本项考虑范围。'),{'S':None,'E':None},'The additional conflicting scope is unresolved, and should not yield a positive inherited list label; NULL accepted.')
probe('elderly_mixed_independent_admin','03423',current(u,u['text'].rstrip('。')+'，文员仅填写收文编号。'),{'S':1,'E':1},'The substantive consideration remains; unrelated clerk duty cannot erase it.')
probe('elderly_later_revocation','03423',current(u,u['text'].rstrip('。')+'；前述内容仅为表格栏目名称，不构成实际药物开发要求。'),{'S':0,'E':0},'Explicitly makes previous content a form heading.')
for k in ['03423','03919']:
 u=units[k];x=copy.deepcopy(u)
 x['structure']={**x.get('structure',{}),'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 for r in x['source_bundle']['source_full_text_resources']:
  r['component_id']='B';r['structure']={'component_id':'B'}
 probe('raw_other_component_'+k,k,x,{'S':None,**({'E':None} if k=='03423' else {})},'Raw source component differs from current and projections.')
u=units['03919']
old='优化安全性信息的报告流程,明确相关责任方'
probe('report_different_network_project','03919',current(u,u['text'].replace(old,'针对另一个网络安全项目，优化安全性信息的报告流程，明确相关责任方')) ,{'S':0},'Current safety-report object is explicitly another network-security project.')
probe('report_mixed_clerk','03919',current(u,u['text'].replace(old,old+'，文员仅填写收文编号')),{'S':1},'Current actual safety reporting remains alongside unrelated filing.')
probe('report_form_retraction','03919',current(u,u['text']+'前述优化安全性信息报告流程仅为栏目名称，不形成实际报告要求。'),{'S':0},'Explicit postposed form-only reclassification of the current report action.')
u=units['03780']
probe('catalogue_mixed_clerk','03780',current(u,u['text'].rstrip('。')+'，文员仅填写收文编号。'),{'Ec':1},'Substantive establishment plus independent filing.')
probe('catalogue_form_retraction','03780',current(u,u['text'].rstrip('。')+'；前述增设目录仅为栏目名称，不形成实际设立要求。'),{'Ec':0},'Postposed clear form-only reclassification of current establishment.')
probe('catalogue_not_actual_requirement','03780',current(u,u['text'].replace('明确提出增设','没有明确提出增设')),{'Ec':1},'Negative substantive establishment discussion may retain Ec under manual, but the reason must preserve its direction rather than claim a positive requirement.')
report={'scope':'independent synthetic boundary review, not validation or source edits','dimensions_sha256':hashlib.sha256((P/'code/dimensions.py').read_bytes()).hexdigest(),'passed':sum(r['passed'] for r in results),'total':len(results),'cases':results}
(P/'round6-dimensions-independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passed'],'total':report['total'],'cases':[{k:r[k] for k in ['name','expected','labels','passed']} for r in results]},ensure_ascii=False,indent=2))
