#!/usr/bin/env python3
from pathlib import Path
from fractions import Fraction
import json,hashlib,math,zipfile,xml.etree.ElementTree as ET,ast
OUT=Path(__file__).resolve().parent
M=OUT.parent;R=M.parent;ROOT=R.parents[1]
DOC=ROOT/'outputs/final-three-department-20261008-adopted-results/论文修订稿-三部门实测结果版.docx'
CFG=M/'measurement-adapter-v3/采用方法_ROOT_CONFIRMED-v6.json'
PAY=M/'measurement-adapter-v4/actual-payload-ready-v6-report-v5/manuscript_measurement_payload.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
checks=[]
def ck(name,test):
 checks.append({'check':name,'pass':bool(test)})
 if not test: raise AssertionError(name)
bindings={}
def read_binding(b):
 p=Path(b['path']);ck('SHA '+str(p),sha(p)==b['sha256']);bindings[str(p)]=b
 return json.loads(p.read_text())
cfg=json.loads(CFG.read_text());p=json.loads(PAY.read_text());ck('root adopted binding exact',p['root_adoption_binding']==bind(CFG));ck('payload ready',p['status']=='ready_for_authoring');ck('DOCX expected original SHA',sha(DOC)=='dd23f6e6e426d0a914eb206fb85ee152bdb0400700e769d8c28390efecb7226f')
classification=read_binding(cfg['methods']['rules']['classification']);ck('same two method classification source',cfg['methods']['rules']['classification']==cfg['methods']['LLM']['classification'])
ac=read_binding(cfg['AC_statistics']);manifest=read_binding(cfg['reference_manifest']);design=read_binding(manifest['sampling_design']);stats_manifest=read_binding(cfg['AC_statistics_manifest']);mathqa=read_binding(cfg['mathematical_QA']);freeze=read_binding(cfg['AC_statistics_freeze'])
for b in [cfg['methods'][role][key] for role in ['rules','LLM'] for key in ['statistics_QA','execution_binding']]: read_binding(b)
for b in manifest['references'].values():
 if isinstance(b,dict) and 'path'in b and 'sha256'in b:
  pp=Path(b['path']);ck('reference SHA '+pp.name,sha(pp)==b['sha256']);bindings[str(pp)]=b
core=R/'statistics/statistical_core_r3.py'; corebinding=stats_manifest['statistical_code']['statistical_core_r3.py'];ck('core source SHA',bind(core)==corebinding);bindings[str(core)]=corebinding
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with zipfile.ZipFile(DOC)as z: body=ET.fromstring(z.read('word/document.xml')).find(w+'body')
ts=body.findall(w+'tbl');ps=body.findall(w+'p');rows=[[''.join(t.text or '' for t in tc.iter(w+'t')) for tc in tr.findall(w+'tc')]for tr in ts[1].findall(w+'tr')]
ck('DOCX table2 exact payload rows',rows==p['tables']['2']['rows']);ck('10 data rows',len(rows)==11)
keys=['kappa','precision','recall','f1'];points=[];cis=0
def metric_exact(cell):
 tp,fp,fn,tn=[Fraction(cell[x]) for x in ['TP','FP','FN','TN']];n=tp+fp+fn+tn
 def ratio(a,b):return a/b if b else None
 agree=ratio(tp+tn,n); l=ratio(tp+fp,n);r=ratio(tp+fn,n);pe=l*r+(1-l)*(1-r)
 return {'kappa':ratio(agree-pe,1-pe),'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'f1':ratio(2*tp,2*tp+fp+fn)}
def getrow(source,ptr): return source['comparisons'][int(ptr.rsplit('/',1)[1])]
for i,ar in enumerate(p['tables']['2']['audit'],1):
 item={'dimension':ar['dimension'],'method_role':ar['method_role'],'method_id':ar['method_id'],'values':{}}
 for ref in ['A','C']:
  r=ar['references'][ref];s=getrow(classification,r['row_json_pointer']);ck(f'selector{i}/{ref}',all(s[k]==v for k,v in r['selector'].items()));ck(f'n180{i}/{ref}',s['unit_frame_n']==s['paired_n']==180 and s['excluded_pending_n']==0)
  ck(f'raw cells{i}/{ref}',s['raw_confusion']==r['raw_cells']);ck(f'weighted cells{i}/{ref}',all(math.isclose(s['weighted_confusion'][k],float(Fraction(v)),rel_tol=1e-12,abs_tol=1e-12)for k,v in r['exact_weighted_cells'].items()))
  exact=metric_exact(r['exact_weighted_cells']);vout={}
  for col,k in enumerate(keys,2):
   a=r['metrics'][k];v=exact[k];ck(f'exact fraction{i}/{ref}/{k}',str(v)==a['exact_fraction']);ck(f'source point{i}/{ref}/{k}',math.isclose(float(v),s['metrics'][k]['estimate'],rel_tol=1e-12,abs_tol=1e-12) and math.isclose(float(v),a['estimate'],rel_tol=1e-12,abs_tol=1e-12));display=f'{float(v):.3f}';ck(f'DOCX displayed value{i}/{ref}/{k}',rows[i][col].split('/')[['A','C'].index(ref)]==display);ck(f'CI source equality{i}/{ref}/{k}',a['ci95_primary']==s['metrics'][k]['ci95_primary']);cis+=1
   vout[k]={'estimate':float(v),'exact_fraction':str(v),'display_3dp':display,'ci95_primary':a['ci95_primary']}
  item['values']['A' if ref=='A' else 'B']={'original_reference':ref,'source_selector':r['selector'],'source_row_json_pointer':r['row_json_pointer'],'raw_four_cells':r['raw_cells'],'exact_weighted_four_cells':r['exact_weighted_cells'],'metrics':vout}
 points.append(item)
acs=[]
for dim,d in p['AC_before_third_audit']['dimensions'].items():
 s=getrow(ac,d['row_json_pointer']);ck('AC selector '+dim,all(s[k]==v for k,v in d['selector'].items()));cells=dict(zip(['TP','FP','FN','TN'],[d['exact_weighted_cells'][k]for k in ['A1_C1','A1_C0','A0_C1','A0_C0']]));v=metric_exact(cells)['kappa'];a=d['metrics']['kappa'];ck('AC exact '+dim,str(v)==a['exact_fraction'] and math.isclose(float(v),s['metrics']['kappa']['estimate'],rel_tol=1e-12));ck('AC CI '+dim,a['ci95_primary']==s['metrics']['kappa']['ci95_primary']);acs.append({'dimension':dim,'estimate':float(v),'exact_fraction':str(v),'display_3dp':f'{float(v):.3f}','ci95_primary':a['ci95_primary'],'source_row_json_pointer':d['row_json_pointer']})
acdisplay='、'.join(x['display_3dp']for x in acs);p52=''.join(t.text or ''for t in ps[52].iter(w+'t'));ck('DOCX paragraph52 AC five kappa matches',acdisplay in p52)
ck('sampling frame counts',design['frame_N_by_group']=={'NMPA':947,'NHSA':760,'NHC':60});ck('sampling counts',design['probability_sample_n_by_group']=={'NMPA':60,'NHSA':60,'NHC':60} and design['probability_n']==180 and design['challenge_n']==60)
ck('all240 exposed',classification['provenance']['all240_exposed'] is True and ac['provenance']['all240_exposed'] is True)
constants={}
for node in ast.parse(core.read_text()).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name)and target.id in ['B','BASE_SEED']:
    try:constants[target.id]=ast.literal_eval(node.value)
    except Exception:pass
newrows=[r[:]for r in rows];newrows[0]=[x.replace('A/C','A/B')for x in newrows[0]]
result={'status':'PASS_VERIFIED_EXISTING_PROXY180_VALUES_NOT_HUMAN240','identity':{'A':'original AI-agent reference A','B':'display alias for original AI-agent reference C; source data retain C','human_validation':False,'all_240_old_confirmation_rows_exposed_development':True,'scope':'table2 uses only the 180 probability canonical representatives; separate60challenge are not pooled','future_human240':'separate unexecuted memo; none of its sampling weights or proposed intervals apply here'},'input_bindings':[bind(DOC),bind(CFG),bind(PAY)]+list(bindings.values()),'verification_script':bind(Path(__file__)),'checks_summary':{'all_pass':all(x['pass']for x in checks),'checks_n':len(checks),'table2_point_n':80,'same_source_CI_n':cis,'AC_kappa_n':5,'no_new_bootstrap_run':True,'no_labels_changed':True,'DOCX_modified':False},'table2_display_rows_A_B':newrows,'table2_values':points,'A_B_before_adjudication_kappa':acs,'A_B_kappa_sentence_values':acdisplay,'sampling_design':{'frame_N_by_group':design['frame_N_by_group'],'sample_n_by_group':design['probability_sample_n_by_group'],'sampling':'within-department SRSWOR canonical representative units, not random member sampling within family','canonical_scope':design['probability_scope'],'weights_exact':{'NMPA':'947/60','NHSA':'38/3','NHC':'1'},'NHC_frame_census':True,'challenge_n':60,'challenge_composition':design['challenge_sample_n_by_group'],'challenge_in_table2':False,'seed':design['seed'],'not_frame_of_all4481_or_future_human240':True},'existing_actual_interval_design':{'mechanism':'department_unit_rescaled_SRSWOR','replicates':5000,'replicate_draws':'M_h ~ Multinomial(59;1/60,...,1/60)','replicate_factor':'1 + sqrt(1-60/N_h)*[(60/59)*M_hi-1]','replicate_weight':'original design weight times replicate factor','NHC_factor':1,'finite_population_correction':True,'nonlinear_metrics_recomputed_each_replicate':True,'interval':'numpy.quantile of finite replicates at .025 and .975, default linear interpolation; defined and undefined repetition counts retained','zero_denominator':'NA not 0/1','primary_CIs_not_source_file_cluster_CIs':True,'paired_methods_share_factors':True,'fixed_label_sampling_uncertainty_only':True,'constants_from_actual_core_AST':constants,'code_binding':corebinding,'same_source_table2_CI_count':cis},'scope_note_for_manuscript':'表2为180条概率样本的采样设计加权代理复核结果；A/B为两条独立AI评审流，B对应原始记录C，均非真人编码。斜线前后分别以A、B为参照。既有240条确认材料已用于开发，结果为开发诊断，不能称独立真人验证。','checks':checks}
(OUT/'表2与五维κ_代理180权威绑定.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'output':bind(OUT/'表2与五维κ_代理180权威绑定.json'),'AC_kappa':acdisplay,'point_n':80,'CI_n':cis},ensure_ascii=False))
