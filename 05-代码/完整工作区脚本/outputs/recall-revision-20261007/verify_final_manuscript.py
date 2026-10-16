"""Independent document/data binding and citation checks; no authoring."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from fractions import Fraction
from collections import Counter
import json,re,hashlib,argparse
from verify_composite_material_binding import verify as verify_composite_material
OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[1]
DIMS=['S','E','Ec','I','F']
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def text(x):return ''.join(x.xpath('.//w:t/text()',namespaces=N)).replace('\u2060','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ids(t):
 out=[]
 for part in t[1:-1].split(','):
  v=re.split('[–—-]',part);out.extend(range(int(v[0]),int(v[-1])+1))
 return out
def read(p):return json.loads(Path(p).read_text())
def resolved(p):
 p=Path(p)
 return p.resolve() if p.is_absolute() else (PROJECT/p).resolve()
def verify_sources(data):
 for p,h in data.get('source_sha256',{}).items():assert sha(resolved(p))==h,('Source binding changed',p)
def narrative_checks(manifest,stats,attention,complete):
 """Recompute numerical prose independently, without importing its builder."""
 u=manifest['paragraph_changes'];rule=attention['method_bindings']['rule']['method']
 llm=attention['method_bindings']['llm'].get('method')
 primary=attention['primary']
 def q(g,d,m=rule):return Fraction(primary[m][g]['dimensions'][d]['attention_share']['exact_fraction'])*100
 def fmt(x):return f'{float(x):.2f}'
 def rec(m,d,ref='C',group='ALL'):
  return next(x for x in stats['records'] if (x['frame'],x['group'],x['method'],x['reference'],x['dimension'])==('main1057',group,m,ref,d))
 def kv(m,d,ref='C',group='ALL'):return rec(m,d,ref,group)['metrics']['kappa']['estimate']
 def perc(i):return re.findall(r'(-?\d+(?:\.\d+)?)%',u[str(i)])
 def check(i,wanted):assert perc(i)==[fmt(x) for x in wanted],('Numerical prose mismatch',i,perc(i),wanted)
 equal_nhc=q('NHC','S')==q('NHC','F')
 for i in [1,6,65,104]:
  if '各占' in u[str(i)] or '各为' in u[str(i)] or 'each account' in u[str(i)]:
   assert equal_nhc,('NHC safety and fairness cannot share one displayed value',i)
 for i in [1,6,104]:check(i,[q('NMPA','S'),q('NMPA','E'),q('NHSA','Ec'),q('NHC','S'),q('NHC','F')])
 check(65,[q(g,d) for g in ['NMPA','NHSA','NHC'] for d in DIMS])
 for i in [1,6,65,74,104]:
  assert not re.search(r'两维合计|两项合计|(?:安全性与有效性|安全性与公平性|安全有效)合计|together account',u[str(i)]),('Composite dimension claim retained',i)
 check(73,[q(g,'I') for g in ['NMPA','NHSA','NHC']])
 diffs=[q('NMPA','S')-q('NHSA','S'),q('NMPA','E')-q('NHSA','E'),q('NHSA','Ec')-q('NMPA','Ec'),
  q('NHSA','Ec')-q('NHC','Ec'),q('NHC','F')-q('NMPA','F'),q('NHC','F')-q('NHSA','F')]
 assert re.findall(r'(-?\d+\.\d+)个百分点',u['73'])==[fmt(x) for x in diffs]
 check(74,[q(g,d,m) for g,d in [('NMPA','S'),('NHSA','Ec'),('NHC','S'),('NHC','F')] for m in ['A_AI_reference','C_AI_reference']])
 rk=[kv(rule,d,r) for d in DIMS for r in ['A','C']]
 expected_k=[kv('A_C',d) for d in DIMS]+[min(rk),max(rk)]
 if complete:
  lk=[kv(llm,d,r) for d in DIMS for r in ['A','C'] if kv(llm,d,r)is not None]
  expected_k += [min(lk),max(lk),kv(llm,'I','A','NMPA'),kv(llm,'I','C','NMPA'),
    kv(llm,'F','A','NHSA'),kv(llm,'F','C','NHSA'),kv(llm,'E','C','NHSA')]
 expected_k += [kv(rule,'Ec','A','NMPA'),kv('A_C','E','C','NHSA')]
 assert re.findall(r'(?<!\d)-?\d+\.\d{3}(?!\d)',u['54'])==[f'{x:.3f}' for x in expected_k],('Kappa prose mismatch',u['54'],expected_k)
 if '各确认2条' in u['54']:
  for ref in ['A','C']:
   x=rec(rule,'Ec',ref,'NMPA')['confusion']
   assert x['TP']+x['FN']==2 and x['FP']+x['FN']==1
  assert kv(rule,'Ec','A','NMPA')==kv(rule,'Ec','C','NMPA')
 if '1条分歧在于纳入诊疗方案' in u['54']:
  x=rec('A_C','E','C','NHSA')['cross_tab'];assert list(x.values())[1]+list(x.values())[2]==1
 assert str(stats['population_n']) in u['47']
 for g in ['NMPA','NHSA','NHC']:assert str(stats['population_by_group'][g]) in u['47']
 assert str(stats['frame_n']['main1057']) in u['49'] and str(stats['frame_n']['main1057']) in u['56']
 assert all(str(stats['frame_by_group']['main1057'][g]) in u['59'] for g in ['NMPA','NHSA','NHC'])
 assert str(stats['bootstrap']['repetitions']) in u['112']
 methods=[rule]+([llm] if complete else [])+['A_AI_reference','C_AI_reference']
 stable=all(attention['sensitivities'][m]['primary_dominant_dimensions']['NMPA']==['S']
  and attention['sensitivities'][m]['primary_dominant_dimensions']['NHSA']==['Ec'] for m in methods)
 if complete and '均保留药监安全性和医保经济性占比最高' in u['1']:assert stable
 if '来源及定义边界检验与逐条目剔除均保留' in u['74']:
  for m in methods:
   sm=attention['sensitivities'][m]
   tests=[sm['primary_dominant_dimensions']]+list(sm['scenario_dominant_dimensions'].values())+[x['dominant_dimensions'] for x in sm['leave_one_policy_file_out']]
   assert all(x['NMPA']==['S'] and x['NHSA']==['Ec'] for x in tests)
 if '在规则与A/C结果中' in u['74'] and '经济性超过安全性' in u['74']:
  for m in [rule,'A_AI_reference','C_AI_reference']:
   sm=attention['sensitivities'][m]
   scenarios=[sm['scenarios']['exclude_all_joint_publications']['NHC']]+[x['distribution']['NHC'] for x in sm['leave_one_policy_file_out'] if '加强用药安全管理' in x['discarded_file']]
   assert len(scenarios)==2
   for x in scenarios:assert Fraction(x['dimensions']['Ec']['attention_share']['exact_fraction'])>Fraction(x['dimensions']['S']['attention_share']['exact_fraction'])
 if complete:
  pairs={m:{(tuple(x['pair']),x['dimension']):x['observed_direction'] for x in attention['comparisons'][m]} for m in [rule,llm]}
  n=len(pairs[rule]);same=sum(pairs[rule][k]==pairs[llm][k] for k in pairs[rule])
  assert re.search(rf'三部门{n}项同维度比较中有{same}项点估计方向一致',u['74'])
  stability=read(OUT/'llm-v30/stability_comparison_v30.json')
  assert stability['status']=='computed_from_new_actual_model_calls' and stability.get('candidate')=='03'
  sample_info=stability['actual_source_paths']['sample'];sample_path=Path(sample_info['path'])
  assert sha(sample_path)==sample_info['sha256']==stability['sample_sha256']
  sample=[json.loads(x) for x in sample_path.read_text().splitlines()]
  whole={x['id']:x for x in map(json.loads,(OUT/'effective_blind_inputs_v30_v3.jsonl').read_text().splitlines())}
  assert len(sample)==stability['n'] and all(x==whole[x['id']] for x in sample)
  for name,info in stability['actual_source_paths'].items():
   if name!='sample':assert sha(Path(info['predictions_path']))==info['predictions_sha256']
  assert stability['production_predictions_sha256']==sha(Path(attention['method_bindings']['llm']['path']))
  assert stability['final_full_input_material_version']=='v3'
  assert stability['final_full_input_sha256']==sha(OUT/'effective_blind_inputs_v30_v3.jsonl')
  sample_qa=read(stability['sample_material_v3_identity_QA_path'])
  assert sha(Path(stability['sample_material_v3_identity_QA_path']))==stability['sample_material_v3_identity_QA_sha256']
  assert sample_qa['status']=='passed' and sample_qa['all_36_original_sample_rows_equal_final_v3'] is True
  reps=[next(x for x in stability['comparisons'] if x['comparison_identity']==key) for key in ['strict_same_prompt_same_36_row_batch_repeat','equivalent_prompt_dimension_order_perturbation_same_36_row_batch']]
  assert perc(111)==[fmt(x['all_five_labels_exact_agreement']*100) for x in reps]
  composite=verify_composite_material(attention['method_bindings']['llm']['path'],attention['method_bindings']['rule']['inputs'])
  assert f"每批最多{composite['batch_size']}条" in u['111'] and f"最终选中{composite['selected_batch_count']}批" in u['111']
  assert str(composite['n']) in u['111'] and str(stats['population_n']) in u['111']
 return {'numerical_paragraphs_checked':[1,6,47,49,54,56,59,65,73,74,104,111,112],'NHC_equal_share_claim_checked':equal_nhc,'rare_class_counts_and_claims_checked':True,'sensitivity_claims_checked':True,'stability_material_and_actual_output_binding_checked':complete,'composite_selected_request_binding':composite if complete else None}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');args=ap.parse_args()
 folder=OUT/'preview' if args.preview else OUT
 f=folder/'论文修订稿-三部门版.docx';memo=folder/'校核与待确认事项.docx'
 manifest=json.loads((folder/'文稿生成与证据绑定.json').read_text())
 stats=json.loads((OUT/'三部门编码指标.json').read_text());attention=json.loads((OUT/'三部门注意力分布与敏感性.json').read_text())
 verify_sources(stats);verify_sources(attention)
 for p,h in manifest['source_sha256'].items():assert sha(Path(p))==h,('Manuscript source binding changed',p)
 assert stats['method_bindings']['rule']==attention['method_bindings']['rule']
 assert stats['method_bindings']['llm']['path']==attention['method_bindings']['llm']['path']
 rule_release=read(OUT/'rules-v31/release_completed_material_v3.json')
 assert sha(Path(attention['method_bindings']['rule']['rules']))==rule_release['prediction_sha256']
 assert sha(Path(attention['method_bindings']['rule']['inputs']))==rule_release['input_sha256']
 if not args.preview:
  assert manifest['status']=='actual_results_bound'
  assert Path(attention['method_bindings']['llm']['path']).resolve().is_relative_to(OUT.resolve())
 narrative=narrative_checks(manifest,stats,attention,not args.preview)
 root=E.fromstring(ZipFile(f).read('word/document.xml'));body=root.find('w:body',N);ps=body.findall('w:p',N);tables=body.findall('w:tbl',N)
 assert len(tables)==4
 assert manifest['output_sha256'][str(f)]==sha(f) and manifest['output_sha256'][str(memo)]==sha(memo)
 memo_xml=E.fromstring(ZipFile(memo).read('word/document.xml'))
 memo_paragraphs=[text(p) for p in memo_xml.xpath('.//w:body/w:p',namespaces=N)]
 memo_summary=next(p for p in memo_paragraphs if p.startswith('主规则描述为'))
 rule_method=attention['method_bindings']['rule']['method']
 def mq(g,d):return Fraction(attention['primary'][rule_method][g]['dimensions'][d]['attention_share']['exact_fraction'])*100
 memo_percentages=[mq('NMPA','S'),mq('NMPA','E'),mq('NHSA','Ec'),mq('NHC','S'),mq('NHC','F')]
 assert re.findall(r'(-?\d+(?:\.\d+)?)%',memo_summary)==[f'{float(x):.2f}' for x in memo_percentages]
 assert not re.search(r'两维合计|两项合计|(?:安全性与有效性|安全性与公平性|安全有效)合计|together account',memo_summary)
 assert 'AI agent' in '\n'.join(memo_paragraphs)
 full=text(body);assert not re.search(r'\{[A-Z_]+\}',full)
 # Manifest claims must also be present in the actual document after citation remapping.
 def normalized(t):return re.sub(r'\s+','',re.sub(r'\[\d+(?:[,–—-]\d+)*\]','[]',t))
 actual_paragraphs={normalized(text(p)) for p in body.xpath('.//w:p',namespaces=N)}
 removed={28,29,66,67,68,109,113,114,115,116,117,118,119,120}
 for i,t in manifest['paragraph_changes'].items():
  if int(i) not in removed:assert normalized(t) in actual_paragraphs,('Manifest paragraph missing from actual DOCX',i)
 check_full='\n'.join(text(p) for p in body.xpath('.//w:p',namespaces=N) if not args.preview or not text(p).startswith('内部排版预览'))
 for old in ['旧LLM','v28.2','中央综合','综合政策','阳性维度','κ≥0.80','60项单参照','30项比较','H427的A/C']:
  assert old not in check_full,f'Old process or inconsistent term left in manuscript: {old}'
 if not args.preview:
  for unclosed in ['内部排版预览','待闭合','尚未闭合','尚无新全量']:
   assert unclosed not in full
 assert 'AI agent' in full,'Reference provenance must remain true'
 # Rebuild all table 2 point estimates from the statistical records.
 cn=['安全性','有效性','经济性','创新性','公平性'];dims=['S','E','Ec','I','F'];records=stats['records'];rule=attention['method_bindings']['rule']['method'];llm=attention['method_bindings']['llm'].get('method')
 table_values=[[[text(c) for c in r.findall('w:tc',N)] for r in t.findall('w:tr',N)] for t in tables]
 t2=table_values[1];assert len(t2)==11
 checked=0
 for row in t2[1:]:
  dim=dims[cn.index(row[0])];method=rule if row[1]=='自动规则' else llm
  if args.preview and row[2]=='待闭合':continue
  for ci,key in enumerate(['kappa','precision','recall','f1'],2):
   expected=[]
   for ref in ['A','C']:
    r=next(r for r in records if (r['frame'],r['group'],r['method'],r['reference'],r['dimension'])==('main1057','ALL',method,ref,dim));v=r['metrics'][key]['estimate']
    expected.append('—' if v is None else f'{v*100:.1f}' if key in ['precision','recall'] else f'{v:.3f}')
   assert row[ci]=='/'.join(expected),(dim,method,key,row[ci],expected);checked+=2
 # Independently verify denominators and all displayed percentages in table 3.
 t3=table_values[2];mapping={'药监':'NMPA','医保':'NHSA','卫健':'NHC'};methods={'规则':rule,'LLM':llm,'A':'A_AI_reference','C':'C_AI_reference'}
 for row in t3[1:]:
  g=mapping[row[0]];m=methods[row[1]];x=attention['primary'][m][g]
  counts=[Fraction(x['dimensions'][d]['weighted_known_hit_count']['exact_fraction']) for d in dims];den=sum(counts)
  assert Fraction(x['weighted_five_dimension_known_hit_sum']['exact_fraction'])==den
  assert row[2]==(f'{float(den):.2f}' if m.endswith('_reference') else f'{float(den):.0f}')
  shares=[c/den for c in counts];assert sum(shares)==1
  for val,share in zip(row[3:],shares):assert val==f'{float(share)*100:.2f}';checked+=1
  assert abs(sum(float(v) for v in row[3:])-100)<=.020001
 assert table_values[3]==manifest['tables']['4']
 figures=read(OUT/'图表数据与来源.json')
 assert figures['source_sha256']==sha(OUT/'三部门注意力分布与敏感性.json')
 assert len(figures['figure2_data'])==15 and figures['method']==rule
 for item in figures['figure2_data']:
  value=attention['primary'][rule][item['group']]['dimensions'][item['dimension']]['attention_share']
  assert Fraction(item['exact_fraction'])==Fraction(value['exact_fraction'])
 for media,filename in [('word/media/image3.png','图1-制度逻辑与注意力分析框架.png'),('word/media/image4.png','图2-三部门五维注意力占比.png')]:
  assert hashlib.sha256(ZipFile(f).read(media)).hexdigest()==sha(OUT/filename),('Embedded figure differs',filename)
 # Confirm actual first-appearance citation order, accounting for ranges/tables.
 ref_start=next(i for i,p in enumerate(ps) if text(p)=='参考文献');refs=ps[ref_start+1:];nums=[]
 for p in refs:
  match=re.match(r'^\[(\d+)\]',text(p));assert match;nums.append(int(match[1]))
 assert nums==list(range(1,len(nums)+1))
 observed=[];after_refs=False
 for block in body:
  if block.tag=='{'+N['w']+'}p' and text(block)=='参考文献':break
  for pp in ([block] if block.tag=='{'+N['w']+'}p' else block.xpath('.//w:p',namespaces=N)):
   for token in re.findall(r'\[\d+(?:[,–—-]\d+)*\]',text(pp)):
    for rid in ids(token):
     assert rid in nums
     if rid not in observed:observed.append(rid)
 assert observed==nums
 # Journal type rules verified directly on the final generated table runs.
 for t in tables[1:]:
  for r in t.xpath('.//w:r',namespaces=N):
   v=r.find('w:rPr/w:sz',N);assert v is not None and v.get('{'+N['w']+'}val')=='21'
 report={'status':'passed','main_sha256':sha(f),'memo_sha256':sha(memo),'statistics_sha256':sha(OUT/'三部门编码指标.json'),'attention_sha256':sha(OUT/'三部门注意力分布与敏感性.json'),'manuscript_manifest_sha256':sha(folder/'文稿生成与证据绑定.json'),'checked_table_values':checked,'table_count':len(tables),'reference_count':len(nums),'citations_first_appearance_valid':True,'five_shares_sum_exactly_one':True,'rounded_share_max_sum_error_pp':.02,'AI_provenance_retained':True,'old_process_values_removed':True,'table_font_pt':10.5,'numerical_prose_checks':narrative,'memo_numeric_summary_and_identity_checked':True,'embedded_figure_data_and_hashes_checked':True,'all_manifest_and_statistics_source_hashes_verified':True,'scope':'Machine checks do not substitute for actual page-image review, policy/literature source checks or human validation.'}
 (folder/'最终文稿数据与引用核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
