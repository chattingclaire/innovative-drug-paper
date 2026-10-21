import sys,pathlib,json,copy,hashlib
sys.dont_write_bytecode=True
P=pathlib.Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/11-version-comparison-20261014/规则修复第四轮-20261015')
e={'__file__':str(P/'round4_relations_tests.py')};exec((P/'round4_relations_tests.py').read_text().split('results=[]')[0],e)
run=e['run'];transform=e['transform'];units=e['units'];out=[]
def record(name,u):
 v,l=run(u);r=[r for r in v.traces() if r['details'].get('relation_subtype') in [e['REVIEW'],e['TRIAL']]]
 out.append({'name':name,'text':u['text'],'labels':l,'relations':[x['details'].get('relation_subtype') for x in r]})
for s in ['04377','01456','04589','04614']:record('original_'+s,units['RECODE25-'+s])
u=copy.deepcopy(units['RECODE25-04377']);u['source_ref']['sha256']='f'*64;record('review_unit_cross_source',u)
u=copy.deepcopy(units['RECODE25-01456']);u.setdefault('structure',{})['component_id']='A'
for c in u['contexts']:c.setdefault('structure',{})['component_id']='A'
doc=u['source_bundle']['source_full_text_resources'][0];doc['structure']={'component_id':'A'}
for p in doc['paragraphs']:p['structure']={'component_id':'B'}
record('trial_raw_paragraphs_cross_component',u)
u=units['RECODE25-01456']
for name,old,new in [
 ('trial_uncertain_admission','最终将纳入','不一定最终将纳入'),
 ('trial_need_branch_excluded','或②在境内尚无药物获批拟开发的罕见疾病适应症；','或②在境内尚无药物获批拟开发的罕见疾病适应症（此分支不在本试点纳入范围）；'),
 ('trial_service_other_object','实施框架将成为该品种罕见疾病适应症的临床研发档案','其他试点品种的实施框架将成为其他品种罕见疾病适应症的临床研发档案'),
]:record(name,transform(u,old,new))
print(json.dumps(out,ensure_ascii=False,indent=2));(P/'round4-relations-review-probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
