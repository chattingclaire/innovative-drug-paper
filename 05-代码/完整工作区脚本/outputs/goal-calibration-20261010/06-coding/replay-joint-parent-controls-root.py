"""Replay exact fixed developer controls on a new joint candidate; never a gold test."""
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--candidate',required=True)
parser.add_argument('--out',required=True)
args=parser.parse_args()
candidate=Path(args.candidate).resolve();out=Path(args.out).resolve()
SE=ROOT/'06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'
IF=ROOT/'06-coding/rule-v20-semantic-audit-repair-sol/versions/v3'
AUDIT=ROOT/'08-audits/SE-Ec-v2-independent-controls-sol'
def load(p):return json.loads(Path(p).read_text())
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(b):assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},b['path']
def save(p,v):
    with p.open('x',encoding='utf8') as h:json.dump(v,h,ensure_ascii=False,indent=2);h.write('\n')
def import_exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

assert not out.exists(),'Do not replace actual execution'
for p,key in ((IF/'delivery-seal.json','members'),(SE/'delivery-seal.json','files'),(AUDIT/'output-seal.json','output_members'),(candidate/'pre-execution-seal.json','output_members')):
    for b in load(p)[key]:exact(b)
module_bindings=[bind(candidate/(n+'.py')) for n in ('source_packet','source_receipts','evidence','relations','dimensions')]
mods={n:import_exact(n,candidate/(n+'.py')) for n in ('evidence','source_packet','source_receipts','relations','dimensions')}
helper=import_exact('joint_SE_synthetic_helper',SE/'semantic_selfcheck.py')
source_bindings=[];cases=[]
def add(suite,name,unit,expected,origin,reason=None):
    assert 'id' not in unit and 'labels' not in unit and 'expected' not in unit
    cases.append(dict(suite=suite,name=name,semantic_input=copy.deepcopy(unit),expected=expected,original_control_artifact=origin,manual_reason=reason,nonhuman_development_control=True))

for run in load(SE/'regression-reception.json')['runs']:
    path=Path(run['artifact']['path']);exact(run['artifact']);source_bindings.append(bind(path))
    data=load(path)
    for index,case in enumerate(data.get('tests',[data])):
        expected=next(case[k] for k in ('expected_fixed_before_v2_edit','expected_fixed_before_execution','expected') if k in case)
        if 'synthetic_input' in case:unit=copy.deepcopy(case['synthetic_input'])
        elif 'material_path' in case:
            raw=Path(case['material_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==case['material_sha256']
            source_bindings.append(bind(case['material_path']))
            unit=mods['source_packet'].semantic_unit(json.loads(raw))
        elif case.get('input_kind')=='actual_frozen_material':
            p=case['input_binding'];raw=Path(p['path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==p['sha256']
            source_bindings.append(bind(p['path']))
            unit=mods['source_packet'].semantic_unit(json.loads(raw))
        else:
            assert case['input_kind'] in ('synthetic_near_miss_or_scope_control','synthetic_sibling_boundary')
            text=case['source_current']
            contexts=None
            if case['input_kind']=='synthetic_sibling_boundary':
                contexts=[helper.context(text),helper.context(case['unrelated_context'],'preceding_paragraph','CTX-OTHER')]
            unit=helper.unit(text,contexts)
        if 'source_current' in case:assert unit['text']==case['source_current']
        add('SE_parent156',case['name'],unit,expected,dict(binding=bind(path),index=index),case.get('manual_rationale',case.get('manual_reason')))
assert len(cases)==156
for filename in ('independent20-original-controls.json','scope-controls-fixed-before-execution.json','right-scope-controls-fixed-before-terminal-patch.json'):
    path=IF/filename;source_bindings.append(bind(path))
    for index,case in enumerate(load(path)['cases']):
        add('IF_parent36',case['name'],case['synthetic_input'],case['expected'],dict(binding=bind(path),index=index),case.get('manual_reason'))
assert len(cases)==192
for suite,filename in (('legacy20','legacy20-controls.json'),('new20','new20-fixed-before-execution.json'),('owner_closure3','owner-closure3-fixed-before-execution.json')):
    path=AUDIT/filename;source_bindings.append(bind(path))
    for index,case in enumerate(load(path)['cases']):
        if 'synthetic_input' in case:unit=copy.deepcopy(case['synthetic_input'])
        else:
            if 'source_binding' in case:
                exact(case['source_binding']);source_bindings.append(case['source_binding'])
            unit=mods['source_packet'].semantic_unit(copy.deepcopy(case.get('synthetic_bundle',case.get('bound_source_bundle'))))
        add('SE_independent_exposed43_'+suite,case['name'],unit,case['expected'],dict(binding=bind(path),index=index),case.get('manual_reason'))
assert len(cases)==235
source_bindings.append(bind(SE/'semantic_selfcheck.py'))
source_bindings=list({b['path']:b for b in source_bindings}.values())
out.mkdir()
save(out/'controls-fixed-before-joint-execution.json',dict(status='historical_fixed_developer_controls_not_new_independent_sample',case_N=len(cases),cases=cases,parent_expected_unchanged=True,full77_800_4481_runs=False))
save(out/'pre-execution-seal.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_module_bindings=module_bindings,parent_control_and_actual_source_bindings=source_bindings,controls=bind(out/'controls-fixed-before-joint-execution.json'),runner=bind(__file__),original_source_selection_and_targets_unchanged=True))
cache={};results=[]
for case in cases:
    unit=copy.deepcopy(case['semantic_input']);key=hashlib.sha256(canonical(unit)).hexdigest()
    row=dict(suite=case['suite'],name=case['name'],expected=case['expected'],semantic_input_sha256=key,reused_identical_input_execution=key in cache)
    if key not in cache:
        try:
            view=mods['relations'].RelationView(unit)
            decisions=mods['dimensions'].judge(view)
            mods['evidence'].validate_decisions(unit,decisions)
            assert canonical(unit)==canonical(case['semantic_input']),case['name']
            cache[key]=dict(decisions=decisions,relation_traces=view.traces(),source_requests=view.source_requests,material_requests=view.material_requests,evidence_validation_passed=True)
        except Exception as error:
            cache[key]=dict(error=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()),evidence_validation_passed=False)
    row.update(copy.deepcopy(cache[key]))
    if 'error' in row:row['passed']=False;row['mismatches']=[]
    else:
        row['observed']={dim:row['decisions'][dim]['value'] for dim in case['expected']}
        row['mismatches']=[dict(dimension=dim,expected=value,observed=row['observed'][dim]) for dim,value in case['expected'].items() if value!=row['observed'][dim]]
        row['passed']=not row['mismatches']
    results.append(row)
assert [bind(b['path']) for b in module_bindings]==module_bindings
for b in source_bindings:exact(b)
suites={}
for suite in sorted({c['suite'] for c in cases}):
    rows=[x for x in results if x['suite']==suite]
    suites[suite]=dict(cases=len(rows),matched=sum(x['passed'] for x in rows),exceptions=sum('error'in x for x in rows),mismatched_dimensions=sum(len(x['mismatches']) for x in rows),failed_names=[x['name'] for x in rows if not x['passed']])
summary=dict(status='actual_joint_developer_replay_not_formal_validation',case_N=len(cases),unique_semantic_input_executions=len(cache),matched=sum(x['passed'] for x in results),exceptions=sum('error'in x for x in results),evidence_validated_cases=sum(x['evidence_validation_passed'] for x in results),suites=suites,code=module_bindings,original_expectations_retained=True,new_human_or_gold_created=False,main_LLM_labels_read=False,whole_cohort_runs=0)
save(out/'results.json',results);save(out/'summary.json',summary)
save(out/'output-seal.json',dict(output_members=[bind(p) for p in sorted(out.iterdir()) if p.is_file()],self_excluded=True))
print(json.dumps({k:v for k,v in summary.items() if k!='code'},ensure_ascii=False))
