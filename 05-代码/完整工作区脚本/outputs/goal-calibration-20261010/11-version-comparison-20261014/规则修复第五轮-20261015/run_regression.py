#!/usr/bin/env python3
"""277-unit rule regression; no all-corpus inference, no reference in judge inputs.

Candidate scores on the disclosed 200 are DEVELOPMENT DIAGNOSTICS, never a new
independent validation. This script does not edit classifier source or references.
"""
import argparse,copy,csv,datetime,hashlib,importlib,json,sys,traceback
from collections import Counter
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DIMS=('S','E','Ec','I','F')
NAMES=dict(zip(DIMS,('安全性','有效性','经济性','创新性','公平性')))
MODULES=('source_packet','source_receipts','evidence','relations','dimensions')
BASE=ROOT/'06-coding/full4481-rule-production-adapter-sol'
SEMANTIC=ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl'
OLD=ROOT/'06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
REFERENCE77=ROOT/'11-version-comparison-20261014/原77条复算.json'
REFERENCE200=ROOT/'09-delivery/真人核验确认-200条-20261013/真人核验结果.json'
DRAW=ROOT/'09-delivery/独立真人判读-200条-20261013/管理员留存-勿发编码者/draw.json'
GUARDS=HERE/'generalization_guards.json'
def read(p):return json.loads(Path(p).read_text())
def binding(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def metrics(cells):
 a,b,c,t=map(Fraction,cells);n=a+b+c+t
 div=lambda x,y:x/y if y else None
 pe=div((a+b)*(a+c)+(c+t)*(b+t),n*n)
 out={'kappa':None if not n else div((a+t)/n-pe,1-pe),'precision':div(a,a+b),'recall':div(a,a+c),'F1':div(2*a,2*a+b+c),'agreement':div(a+t,n)}
 return {k:None if v is None else float(v) for k,v in out.items()}
def refs():
 import openpyxl
 frozen=read(REFERENCE77);parts=[]
 for b in frozen['reference_bindings']:
  assert binding(b['path'])=={k:b[k] for k in ('path','bytes','sha256')}
  book=openpyxl.load_workbook(b['path'],read_only=True,data_only=True);h={}
  for row in book['编码表'].iter_rows(min_row=7,max_row=391,values_only=True):
   rid,dept,dim,value=row[:4];d=dim.split()[0];assert d in DIMS and type(value) is int and value in (0,1)
   h.setdefault(rid,{})[d]=value
  book.close();assert len(h)==77 and all(set(x)==set(DIMS) for x in h.values());parts.append(h)
 assert parts[0]==parts[1]
 h200={r['unit_id']:{d:r['judgments'][d]['value'] for d in DIMS} for r in read(REFERENCE200)['records']}
 weights={r['unit_id']:Fraction(r['sampling_weight_exact']) for r in read(DRAW)['records']}
 assert len(h200)==200 and h200.keys()==weights.keys() and sum(weights.values())==1151
 assert not parts[0].keys() & h200.keys()
 return {'77':parts[0],'200':h200},weights,frozen['reference_bindings']
def load_modules(code_dir):
 for name in MODULES:sys.modules.pop(name,None)
 sys.path.insert(0,str(code_dir))
 try:return importlib.import_module('relations'),importlib.import_module('dimensions'),importlib.import_module('evidence')
 finally:sys.path.pop(0)
def predict(code_dir,units,guards):
 before={name:binding(code_dir/(name+'.py')) for name in MODULES}
 relations,dimensions,evidence=load_modules(code_dir)
 results={}
 for rid,unit in units.items():
  assert not {'id','labels','decisions','reference'} & unit.keys()
  # administrative identity is kept only in the calling loop and output mapping.
  semantic=copy.deepcopy(unit)
  try:
   view=relations.RelationView(semantic);decisions=dimensions.judge(view);evidence.validate_decisions(view.unit,decisions)
   labels={d:decisions[d]['value'] for d in DIMS};assert all(v is None or type(v) is int and v in (0,1) for v in labels.values())
   results[rid]={'labels':labels,'decisions':decisions,'implementation_error':None}
  except Exception as exc:
   results[rid]={'labels':{d:None for d in DIMS},'decisions':None,'implementation_error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc()}
 guard_results=[]
 for case in guards:
  # Synthetic IDs and expectations are never included in the semantic view.
  unit={'text':case['text'],'contexts':copy.deepcopy(case.get('contexts',[]))}
  try:
   view=relations.RelationView(unit);decisions=dimensions.judge(view);evidence.validate_decisions(view.unit,decisions)
   vals={d:decisions[d]['value'] for d in DIMS};err=None
  except Exception as exc:vals={d:None for d in DIMS};err=type(exc).__name__+': '+str(exc)
  guard_results.append({'name':case['name'],'purpose':case['purpose'],'text':case['text'],'expected':case['expected'],'observed':vals,'passed':all(vals[d]==v for d,v in case['expected'].items()) and err is None,'error':err})
 after={name:binding(code_dir/(name+'.py')) for name in MODULES}
 if before!=after:raise RuntimeError('Classifier code changed during run. Re-run once editing stops; no mixed-version result saved.')
 return results,guard_results,before
def summarize(pred,ref,weights):
 out=[]
 for d in DIMS:
  cells=[0]*4;wcells=[Fraction(0)]*4;null=[];errors=[]
  for rid,h in ref.items():
   row=pred[rid];m=row['labels'][d]
   if row.get('implementation_error'):errors.append(rid);continue
   if m is None:null.append(rid);continue
   idx={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[m,h[d]];cells[idx]+=1;wcells[idx]+=weights[rid]
  out.append({'dimension':d,'N':len(ref),'binary_N':sum(cells),'NULL_ids':null,'technical_error_ids':errors,'TP_FP_FN_TN':cells,'raw_metrics':metrics(cells),'design_weighted_cells_exact':list(map(str,wcells)),'design_weighted_metrics':metrics(wcells),'NULL_weight_exact':str(sum(weights[rid] for rid in null)),'technical_error_weight_exact':str(sum(weights[rid] for rid in errors))})
 return out
def difference(pred,old,references,units):
 changes=[]
 for sample,ref in references.items():
  for rid,h in ref.items():
   for d in DIMS:
    a,b=old[rid]['labels'][d],pred[rid]['labels'][d]
    if a==b and not pred[rid]['implementation_error']:continue
    status=('technical_error' if pred[rid]['implementation_error'] else 'resolved_reference_disagreement' if a!=h[d] and b==h[d] else 'new_reference_disagreement' if a==h[d] and b!=h[d] else 'changed_but_still_disagrees')
    changes.append({'sample':sample,'id':rid,'dimension':d,'old':a,'candidate':b,'reference':h[d],'status':status,'text':units[rid]['text'],'decision':None if pred[rid]['decisions'] is None else pred[rid]['decisions'][d]})
 return changes
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--code-dir',type=Path,default=HERE/'code');parser.add_argument('--output',type=Path,default=None);parser.add_argument('--baseline-only',action='store_true');parser.add_argument('--semantic-overrides',type=Path,default=None);args=parser.parse_args()
 out=args.output or HERE/('run-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
 if out.exists():raise SystemExit('Output already exists; choose a fresh directory to preserve prior diagnostics.')
 ref,weights,ref_bindings=refs();ids=set(ref['77'])|set(ref['200']);units={};old={}
 for path,key,dest in [(SEMANTIC,'semantic_unit',units),(OLD,None,old)]:
  with path.open() as f:
   for line in f:
    x=json.loads(line)
    if x['id'] in ids:dest[x['id']]=x[key] if key else x
 assert units.keys()==old.keys()==ids and len(ids)==277
 guards=read(GUARDS)['cases'];base,baseguards,basebindings=predict(BASE,units,guards)
 mismatches=[{'id':rid,'dimension':d,'computed':base[rid]['labels'][d],'saved':old[rid]['labels'][d],'error':base[rid]['implementation_error']} for rid in ids for d in DIMS if base[rid]['labels'][d]!=old[rid]['labels'][d] or base[rid]['implementation_error']]
 out.mkdir(parents=True);save(out/'baseline-reproduction.json',{'code':basebindings,'selected_unit_N':277,'mismatch_N':len(mismatches),'mismatches':mismatches,'passed':not mismatches,'guards':baseguards})
 if mismatches:raise SystemExit('Baseline reproduction failed; see baseline-reproduction.json. Candidate not run.')
 candidate_units=copy.deepcopy(units)
 overrides={}
 if args.semantic_overrides:
  if args.baseline_only:raise ValueError('Baseline reproduction cannot use enriched input')
  overrides=read(args.semantic_overrides)
  assert overrides and set(overrides)<=set(units)
  for rid,u in overrides.items():
   assert u['text']==units[rid]['text'] and u['source_ref']==units[rid]['source_ref']
   assert u.get('contexts',[])[:len(units[rid].get('contexts',[]))]==units[rid].get('contexts',[])
   candidate_units[rid]=u
 same_input,same_guards,same_code=(base,baseguards,basebindings) if args.baseline_only else predict(args.code_dir.resolve(),units,guards)
 candidate,guardresults,codebindings=predict(args.code_dir.resolve(),candidate_units,guards) if overrides else (same_input,same_guards,same_code)
 assert codebindings==same_code
 input_changes=difference(candidate,same_input,ref,candidate_units)
 baseline_metrics={s:summarize(base,h,{rid:Fraction(1) for rid in h} if s=='77' else weights) for s,h in ref.items()}
 candidate_metrics={s:summarize(candidate,h,{rid:Fraction(1) for rid in h} if s=='77' else weights) for s,h in ref.items()}
 changes=difference(candidate,old,ref,units)
 report={'purpose':'77条开发回归 + 已披露200条开发诊断；候选版本没有新的独立验证','candidate_independent_validation':False,'baseline_role':'此前固定旧版输出的独立检验记录不被本次覆盖','model_calls':0,'classified_real_unit_N':277,'full4481_inference':False,'input_contract':'judge(RelationView(semantic_unit)); no administrative id or reference labels passed','inputs':{'semantic_units':binding(SEMANTIC),'old_predictions':binding(OLD),'reference77':ref_bindings,'reference200':binding(REFERENCE200),'sample_draw':binding(DRAW),'guard_cases':binding(GUARDS),'script':binding(Path(__file__))},'code':codebindings,'baseline_reproduction_passed':True,'baseline_metrics':baseline_metrics,'candidate_metrics':candidate_metrics,'change_counts':dict(Counter(x['status'] for x in changes)),'changes':changes,'generalization_guards':guardresults}
 report['input_enrichment']={'applied':bool(overrides),'record_ids':sorted(overrides),'overrides_binding':binding(args.semantic_overrides) if overrides else None,'same_code_input_effect_changes':input_changes,'same_code_input_effect_counts':dict(Counter(x['status'] for x in input_changes))}
 report['candidate_original_input_metrics']={s:summarize(same_input,h,{rid:Fraction(1) for rid in h} if s=='77' else weights) for s,h in ref.items()}
 report['candidate_original_input_changes']=difference(same_input,old,ref,units)
 save(out/'candidate-original-input-predictions.json',same_input)
 save(out/'report.json',report);save(out/'candidate-predictions.json',candidate)
 rows=[]
 for phase,metrics_ in [('旧版',baseline_metrics),('候选',candidate_metrics)]:
  for sample,items in metrics_.items():
   for x in items:
    for weighting in ['raw','design_weighted'] if sample=='200' else ['raw']:
     rows.append({'版本':phase,'样本':sample,'口径':weighting,'维度':NAMES[x['dimension']],'可比数':x['binary_N'],'待定数':len(x['NULL_ids']),'技术失败数':len(x['technical_error_ids']),'TP_FP_FN_TN':'/'.join(map(str,x['TP_FP_FN_TN'] if weighting=='raw' else x['design_weighted_cells_exact'])),**x[weighting+'_metrics']})
 with (out/'metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 fmt=lambda v:'—' if v is None else f'{v:.3f}'
 lines=['# 规则候选开发回归诊断','','77条用于校准回归；200条已经用于本轮调整，候选在该批上的结果属于开发诊断，不是候选的独立验证。原始旧版独立检验记录保留不变。','','|版本|样本|口径|维度|可比/待定/技术失败|TP/FP/FN/TN|κ|P|R|F1|','|---|---|---|---|---|---|---:|---:|---:|---:|']
 for x in rows:lines.append('|'+ '|'.join([x['版本'],x['样本'],x['口径'],x['维度'],f'{x["可比数"]}/{x["待定数"]}/{x["技术失败数"]}',x['TP_FP_FN_TN']]+[fmt(x[k]) for k in ('kappa','precision','recall','F1')])+'|')
 lines+=['',f'原生产代码在277条上逐项复现旧规则：{not mismatches}。',f'变化类型：{dict(Counter(x["status"] for x in changes))}。',f'自拟泛化保护用例通过{sum(x["passed"] for x in guardresults)}/{len(guardresults)}。','这些自拟用例用于发现明显过度泛化，不替代未参与调整材料的验证；测试期望来自明确语义，不是按人工作答反向调标签。','技术失败与合法待定分别列出；两者均不当作负例。200条设计权重仅对应原1151条抽样框。','逐条变化、新增分歧和消除分歧详见report.json；本次没有更改原始标签或论文。']
 if overrides:lines+=['','本轮含已声明同版原件上下文补全，另保存同代码、原输入对照；规则变化与输入补全分开记录，原始输入未覆盖。',str(report['input_enrichment']['same_code_input_effect_counts'])]
 (out/'summary.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'output':str(out.resolve()),'baseline_reproduction':True,'changes':report['change_counts'],'guards_pass':sum(x['passed'] for x in guardresults),'guards_N':len(guardresults)},ensure_ascii=False))
if __name__=='__main__':main()
