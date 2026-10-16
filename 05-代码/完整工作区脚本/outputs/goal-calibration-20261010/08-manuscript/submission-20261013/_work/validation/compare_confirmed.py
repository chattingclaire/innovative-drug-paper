"""Frozen-label arithmetic for the 2026-10-13 human-confirmed 200.

Descriptive human verification comparison, NOT a formal admission or independent
two-human reliability result. No sampler, model, policy-semantic read, or edits to
source submissions. Reuses only frozen mathematical functions.
"""
import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json, math
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'_deps'))
import numpy as np
import openpyxl

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
ISSUED = ROOT/'09-delivery/独立真人判读-200条-20261013/管理员留存-勿发编码者'
HUMAN = ROOT/'09-delivery/真人核验确认-200条-20261013'
DIMS = ('S','E','Ec','I','F')
METRICS = ('kappa','Precision','Recall','F1')
NAMES = {'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}

def read(p): return json.loads(p.read_text())
def binding(p):
    p=p.resolve(); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def verify(b):
    assert binding(Path(b['path'])) == {k:b[k] for k in ('path','bytes','sha256')}, b['path']
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

freeze=read(ISSUED/'sampling-freeze.json')
draw=read(ISSUED/'draw.json'); blind=read(ISSUED/'blind-assignment.json')
verify(draw['sampling_freeze_binding']); verify(blind['draw_binding']);verify(blind['common_materials_binding'])
for b in freeze['inputs'].values(): verify(b)
for b in freeze['method_locks'].values(): verify(b)
for k in ('source_bundles','source_bindings','manual'): verify(freeze[k])
assert draw['sample_N']==200 and draw['population_N']==1151 and draw['scope']=='registered_remaining_pool'
assert freeze['scope']['remaining_N']==1151 and freeze['scope']['exposed_N']==3330
strata={h['id']:h for h in freeze['strata']}
rows=draw['records']; ids=[r['unit_id'] for r in rows]
assert len(ids)==len(set(ids))==200
assert Counter(r['stratum_id'] for r in rows)==Counter({k:h['n'] for k,h in strata.items()})
for r in rows:
    h=strata[r['stratum_id']]
    assert r['unit_id'] in h['member_ids']
    assert r['department']==h['department'] and r['population_N']==h['N'] and r['sample_n']==h['n']
    assert Fraction(r['inclusion_probability_exact'])==Fraction(h['n'],h['N'])
    assert Fraction(r['sampling_weight_exact'])==Fraction(h['N'],h['n'])
exact_weights=[Fraction(r['sampling_weight_exact']) for r in rows]
assert sum(exact_weights)==1151
human_json=read(HUMAN/'真人核验结果.json')
humans={r['unit_id']:r for r in human_json['records']}
assert len(humans)==200 and set(humans)==set(ids)
assert human_json['confirmation']['independently_blinded_human_submissions']==0
xlsx_checks={}
for role in ('A','B'):
    mapping={r['original_blind_id']:r for r in blind['methods'][role]}
    assert len(mapping)==200 and {r['unit_id'] for r in mapping.values()}==set(ids)
    p=HUMAN/f'编码者{role}结果/真人核验确认-{role}-200条.xlsx'
    w=openpyxl.load_workbook(p,read_only=True,data_only=True)
    data=list(w['真人核验结果'].values); count=Counter();seen=set()
    for record in data[1:]:
        bid,locator,dim,value=record[:4]
        assert bid in mapping and dim in DIMS and type(value) is int and value in (0,1)
        m=mapping[bid]; rid=m['unit_id']; key=(rid,dim)
        assert key not in seen and locator==m['material_locator'];seen.add(key)
        assert humans[rid][f'{role}_id']==bid
        assert humans[rid]['judgments'][dim]['value']==value
        count[dim]+=value
    assert len(seen)==1000 and dict(count)==human_json['positive_counts']
    w.close();xlsx_checks[role]={'binding':binding(p),'matched_dimension_slots_N':len(seen),'positive_counts':dict(count)}
machine_check_path=ROOT/'10-closure-20261012/human-review-comparison/v17-preparation/compare.py'
checker=module(machine_check_path,'_confirmed_machine_inputs')
machines,machine_bindings=checker.paired_inputs(checker.RULE_DEFAULT,checker.LLM_DEFAULT)
engine_path=ROOT/'07-statistics/prospective-dynamic-domain-engine-sol/metrics_engine.py'
engine=module(engine_path,'_confirmed_math_only')
prep={'kind':'stratified_srswor','strata':strata,'stratum_ids':np.array([r['stratum_id'] for r in rows]),
      'weights':np.array([float(w) for w in exact_weights]),'records':rows}
W=engine.rao_wu_weights(prep,5000,20261010)
assert W.shape==(5000,200) and np.allclose(W.sum(axis=1),1151)
shared_hash=hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest()
H=np.array([[humans[rid]['judgments'][d]['value'] for d in DIMS] for rid in ids],dtype=np.int8)
assert np.all(np.isin(H,[0,1]))
joined=[]
for i,r in enumerate(rows):
    joined.append({**r,'human_confirmed':dict(zip(DIMS,map(int,H[i]))),
                   'rule':machines['rule'][r['unit_id']]['labels'],
                   'LLM':machines['LLM'][r['unit_id']]['labels']})
comparisons=[]
for method in ('rule','LLM'):
    M=np.array([[2 if machines[method][rid]['labels'][d] is None else machines[method][rid]['labels'][d]
                 for d in DIMS] for rid in ids],dtype=np.int8)
    for j,d in enumerate(DIMS):
        pair=M[:,j]*4+H[:,j]
        X=np.stack([(pair==cat).astype(float) for cat in (5,4,1,0)],axis=1)
        raw=np.bincount(pair,minlength=16).reshape(4,4)
        weighted=np.bincount(pair,weights=prep['weights'],minlength=16).reshape(4,4)
        exact=[sum(w for w,cat0 in zip(exact_weights,pair) if cat0==cat) for cat in (5,4,1,0)]
        rawcells=[int(raw[1,1]),int(raw[1,0]),int(raw[0,1]),int(raw[0,0])]
        mets=engine.exact_metrics(exact);rmets=engine.exact_metrics(rawcells)
        reps=engine.vector_metrics(W@X)
        values={k:None if v is None else float(v) for k,v in mets.items()}
        rawvalues={k:None if v is None else float(v) for k,v in rmets.items()}
        intervals={k:engine._interval(values[k],reps[k],True,False) for k in METRICS}
        V=engine.analytic_covariance(prep,X);grads=engine.metric_gradients([float(x) for x in exact])
        item={'method':method,'dimension':d,'dimension_name':NAMES[d],
              'assigned_sample_N':200,'assigned_weighted_N':1151,
              'human_positive_raw_N':int(H[:,j].sum()),
              'human_positive_weighted_total':float(prep['weights']@H[:,j]),
              'raw':engine._table_summary(raw,True),'design_weighted':engine._table_summary(weighted),
              'weighted_four_exact_fractions':[str(v) for v in exact],
              'raw_metrics':rawvalues,'design_weighted_metrics':values,'weighted_CI95':intervals,
              'weighted_sampling_SE':{k:None if grads[k] is None else math.sqrt(max(0.,float(grads[k]@V@grads[k]))) for k in METRICS},
              'finite_count_guards':{name:engine.finite_category_guard(prep,(pair==cat).astype(int)) for name,cat in [('FP',4),('FN',1)]},
              'point_targets_0_8_descriptive_only':{k:mets[k] is not None and mets[k]>=Fraction(4,5) for k in METRICS}}
        assert item['raw']['any_execution_failure']==0
        # Separate elementary formula verifies the imported metric result.
        for cells,expected_values in [(rawcells,rawvalues),(exact,values)]:
            a,b,c,tn=map(float,cells);total=a+b+c+tn
            po=(a+tn)/total;pe=((a+b)*(a+c)+(c+tn)*(b+tn))/total**2
            independent={'kappa':(po-pe)/(1-pe),'Precision':a/(a+b),
                         'Recall':a/(a+c),'F1':2*a/(2*a+b+c)}
            assert all(abs(independent[k]-expected_values[k])<1e-12 for k in METRICS)
        comparisons.append(item)
attention={}
for method in ('human_confirmed','rule','LLM'):
    state=H if method=='human_confirmed' else np.array([[2 if machines[method][rid]['labels'][d] is None else machines[method][rid]['labels'][d] for d in DIMS] for rid in ids])
    K=prep['weights']@(state==1);U=prep['weights']@(state==2)
    bounds=engine.attention_bounds(K,U,1151)
    attention[method]={d:{'raw_positive_N':int((state[:,j]==1).sum()),
         'raw_null_N':int((state[:,j]==2).sum()),'weighted_positive_total':float(K[j]),
         'weighted_null_total':float(U[j]),**bounds[d]} for j,d in enumerate(DIMS)}
bindings={'sampling_freeze':binding(ISSUED/'sampling-freeze.json'),'draw':binding(ISSUED/'draw.json'),
          'blind_assignment':binding(ISSUED/'blind-assignment.json'),'human_json':binding(HUMAN/'真人核验结果.json'),
          'math_core':binding(engine_path),'machine_input_checker':binding(machine_check_path),
          'analysis_script':binding(Path(__file__)),**machine_bindings}
result={'schema':'human-confirmed200-descriptive-comparison-v1','created_at_utc':datetime.now(timezone.utc).isoformat(),
        'analysis_role':'descriptive_comparison_after_AI_assisted_human_confirmation',
        'formal_validation_complete':False,'independent_AB_human_kappa_calculated':False,
        'scope':{'population_N':1151,'sample_N':200,'full_frame_N':4481,'inference':'remaining_pool_only',
                 'reference_process':human_json['confirmation'],'human_pending_N':0,'human_semantic_null_N':0},
        'design_strata':[{k:v for k,v in h.items() if k!='member_ids'} for h in strata.values()],
        'source_bindings':bindings,'xlsx_verification':xlsx_checks,
        'sampling_uncertainty':{'replicates':5000,'seed':20261010,'generation_count':1,
          'shared_weights_sha256':shared_hash,'sum_of_weights_each_replicate':1151,
          'method':'Frozen FPC-rescaled Rao-Wu one-stage stratified SRSWOR; one shared W across all methods/dimensions; percentile quantile method linear.',
          'scope':'Approximate marginal95 sampling intervals conditional on the observed human-confirmed labels, not uncertainty of reference correctness or independent annotation.',
          'raw_metric_CI':'Not reported: raw metrics describe disproportionate sample rather than population estimate.',
          'degenerate_rule':'No [1,1] population CI claimed for noncensus degenerate metrics; finite FP/FN count guards are separate count intervals, not metric intervals.'},
        'comparisons':comparisons,'same_sample_design_weighted_attention':attention,
        'arithmetic_crosscheck':'All 80 raw/weighted kappa/P/R/F1 scalars checked against separate elementary formulas; tolerance 1e-12.'}
save('comparison.json',result);save('joined-labels-and-weights.json',joined)
compact=[{'method':x['method'],'dimension':x['dimension'],'name':x['dimension_name'],
          'N_binary':x['raw']['comparable_binary_total'],'N_null':x['raw']['one_or_both_semantic_null_no_failure'],
          'human_positive_N':x['human_positive_raw_N'],'raw':{k:x['raw_metrics'][k] for k in METRICS},
          'weighted':{k:x['design_weighted_metrics'][k] for k in METRICS},
          'weighted_CI95':{k:x['weighted_CI95'][k]['CI95'] for k in METRICS},
          'raw_TP_FP_FN_TN':x['raw']['binary_four_order_a_b_c_d']} for x in comparisons]
save('table2-compact.json',{'rows':compact,'sample_N':200,'target_population_N':1151,
                         'human_positive_counts':human_json['positive_counts'],
                         'description':'按预先固定抽样权重计算的机器编码与人工核验结果对照；A/B为同一核验结果的编号版本。'})
fmt=lambda x:'—' if x is None else f'{x:.3f}'
lines=['# 200条人工核验对照结果','',
       '本批200条来自1151条剩余材料，沿用五层抽样概率和权重。人工核验结果在AI辅助复核后由用户确认；A、B文件是同一结果的编号导出。两种机器编码均使用抽样前冻结结果，本次只做统计对照。','',
       '200条、1000项人工核验均完整。人工正例依次为安全性27、有效性13、经济性20、创新性32、公平性16。','',
       '|方法|维度|有效二元样本|机器待定|TP/FP/FN/TN|原始κ|原始P|原始R|原始F1|加权κ|加权P|加权R|加权F1|',
       '|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in compact:
    vals=[('规则' if x['method']=='rule' else 'LLM'),x['name'],str(x['N_binary']),str(x['N_null']),
          '/'.join(map(str,x['raw_TP_FP_FN_TN'])),*[fmt(x['raw'][k]) for k in METRICS],*[fmt(x['weighted'][k]) for k in METRICS]]
    lines.append('| '+' | '.join(vals)+' |')
lines+=['','加权指标的抽样推断范围为1151条剩余材料，不外推为4481条全库的独立准确率。机器待定保留在样本分母及完整状态表中，仅从对应维度的二元混淆矩阵排除；技术失败为0。','',
        '区间使用原冻结数学核心、5000次共同权重Rao–Wu有限总体修正重抽样。数值为边际95%抽样区间；若非普查维度出现退化分布，则不把[1,1]当作总体精度保证。完整区间、四格、权重与输入文件校验值见comparison.json。','']
lines+=['## 同一样本的加权覆盖率与注意力份额','',
        'p为已知正例加权总数除以1151；q为该维已知正例加权总数除以五维已知正例加权合计。机器待定未改成0，p/q对应已知部分；完整JSON同时提供待定取0或1形成的界限。','',
        '|方法|维度|加权已知正例|加权待定|p（%）|q（%）|','|---|---|---:|---:|---:|---:|']
for method,bydim in attention.items():
    for dim,x in bydim.items():
        lines.append('| '+' | '.join([{'human_confirmed':'人工核验','rule':'规则','LLM':'LLM'}[method],NAMES[dim],
            fmt(x['weighted_positive_total']),fmt(x['weighted_null_total']),
            fmt(100*x['known_hit_coverage']),fmt(100*x['known_hit_attention_share'])])+' |')
(OUT/'人工核验对照说明.md').write_text('\n'.join(lines))
print(json.dumps({'output':str(OUT),'rows':compact,'W_sha256':shared_hash},ensure_ascii=False,indent=2))
