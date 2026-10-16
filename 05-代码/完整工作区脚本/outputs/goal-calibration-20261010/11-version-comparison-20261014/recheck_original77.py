"""Read original confirmed77 and saved old outputs only. No new200 inputs."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import openpyxl

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
HIST = ROOT/'07-statistics/native-v17-rule-v19-human-confirmed77-root'
DIMS = ('S','E','Ec','I','F')
NAMES = dict(zip(DIMS, ('安全性','有效性','经济性','创新性','公平性')))
KEYS = ('kappa','precision','recall','F1')
def read(p): return json.loads(p.read_text())
def binding(p):
    b=p.read_bytes()
    return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(b): assert binding(Path(b['path']))=={k:b[k] for k in ('path','bytes','sha256')}, b['path']
prior=read(HIST/'metrics.json')
for b in read(HIST/'seal.json')['members']: verify(b)
references=[]
for b in prior['reference_bindings']:
    verify(b)
    w=openpyxl.load_workbook(b['path'],read_only=True,data_only=True)
    h={}
    for row in w['编码表'].iter_rows(min_row=7,max_row=391,values_only=True):
        rid,dept,dim,value=row[:4]
        d=dim.split()[0]
        assert d in DIMS and type(value) is int and value in (0,1)
        assert d not in h.setdefault(rid,{})
        h[rid][d]=value
    w.close()
    assert len(h)==77 and all(set(x)==set(DIMS) for x in h.values())
    references.append(h)
assert references[0]==references[1]
human=references[0]
oldrule=ROOT/'06-coding/rule-full4481-v2-root/run4481-first'
oldllm=ROOT/'07-statistics/original-whole-batch-native-full4481-cap13-root'
bindings={'calibration_rule':prior['rule_predictions'],
          'calibration_LLM':binding(HIST/'derived-native-predictions.jsonl'),
          'full4481_rule':read(oldrule/'seal.json')['prediction_binding'],
          'full4481_LLM':next(b for b in read(oldllm/'seal.json')['files'] if Path(b['path']).name=='selected-records.jsonl')}
data={}
for key,b in bindings.items():
    verify(b)
    rows=[json.loads(line) for line in Path(b['path']).open()]
    assert len(rows)==len({r['id'] for r in rows})==(77 if key.startswith('calibration') else 4481)
    assert set(human)<={r['id'] for r in rows}
    data[key]={r['id']:r['labels'] for r in rows}

def calc(key,d):
    cells=[0,0,0,0];null=[]
    for rid,h in human.items():
        m=data[key][rid][d]
        if m is None:
            null.append(rid);continue
        assert type(m) is int and m in (0,1)
        cells[{(1,1):0,(1,0):1,(0,1):2,(0,0):3}[(m,h[d])]]+=1
    a,b,c,t=map(Fraction,cells);n=a+b+c+t
    ratio=lambda x,y: x/y if y else None
    po=(a+t)/n;pe=((a+b)*(a+c)+(c+t)*(b+t))/n**2
    values={'kappa':ratio(po-pe,1-pe),'precision':ratio(a,a+b),'recall':ratio(a,a+c),'F1':ratio(2*a,2*a+b+c)}
    return {'output':key,'dimension':d,'N':77,'binary_N':int(n),'NULL_ids':null,'TP_FP_FN_TN':cells,
            'metrics':{k:None if v is None else float(v) for k,v in values.items()}}
results=[calc(key,d) for key in data for d in DIMS]
for row in results:
    if row['output'].startswith('calibration'):
        method=row['output'].split('_')[1]
        prev=prior['comparisons'][method+'_vs_confirmed_reference']['dimensions'][row['dimension']]
        assert row['TP_FP_FN_TN']==[prev['four_cells'][k] for k in ('TP','FP','FN','TN')]
        assert all(abs(row['metrics'][k]-prev['metrics'][k])<1e-12 for k in KEYS)
changes={method:[{'id':rid,'dimension':d,'human':human[rid][d],
                 'calibration':data['calibration_'+method][rid][d],'full':data['full4481_'+method][rid][d]}
                 for rid in human for d in DIMS if data['calibration_'+method][rid][d]!=data['full4481_'+method][rid][d]] for method in ('rule','LLM')}
report={'scope':'Original77 only; development calibration and original full outputs on the same77',
        'reference_N':77,'reference_dimension_N':385,'source_bindings':bindings,
        'reference_bindings':prior['reference_bindings'],'original_metrics_binding':binding(HIST/'metrics.json'),
        'checks':{'original_reference_hashes':'passed','saved_source_seals':'passed','historical40_metrics_reproduced':'passed'},
        'comparisons':results,'changes_during_full_execution_on_same77':changes,
        'new200_read':False,'model_inference_runs':0,'source_modified':False,
        'heldout_validation':False,'reference_used_for_development':True,
        'script':binding(Path(__file__))}
(OUT/'原77条复算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
labels={'calibration_rule':'当时77条规则','calibration_LLM':'当时77条LLM','full4481_rule':'旧4481输出中的同77条规则','full4481_LLM':'旧4481输出中的同77条LLM'}
lines=['# 原77条校准结果复算','',
       '使用原77条、385项人工标注，重新计算已保存的旧版输出。未使用后来200条，未重跑模型，未修改人工结果或论文。', '',
       '原77条参与了编码手册、规则和提示词调整，因此这些指标说明开发校准表现。4481条是随后全量编码的分析材料；两种规模承担不同作用。', '',
       '|输出|维度|二元条数|待定|κ|精确率|召回率|F1|','|---|---|---:|---:|---:|---:|---:|---:|']
for x in results:
    vals=[labels[x['output']],NAMES[x['dimension']],str(x['binary_N']),str(len(x['NULL_ids']))]+['—' if x['metrics'][k] is None else f"{x['metrics'][k]:.3f}" for k in KEYS]
    lines.append('|'+'|'.join(vals)+'|')
lines+=['','当时77条的40项κ/精确率/召回率/F1已全部复现原报告。上表后两组直接从初次4481条全量文件提取同77条，用于区分校准批次和全量批次的输出。','',
        '论文可以先说明人工校准及其结果，再报告最终采用版本的4481条全量分析。77条不能写成未参与方案调整的样本，也不能由77条指标直接推出4481条的准确率。','',
        '后来的200条核验是检查未参与调整材料的另一个环节，不表示77条作废。是否进行这种检查取决于要支持的结论，并无本项目已核实的“必须人工验证两次”的要求。','']
(OUT/'原77条复算说明.md').write_text('\n'.join(lines))
print(json.dumps({'results':results,'changes':changes,'out':str(OUT)},ensure_ascii=False,indent=2))
