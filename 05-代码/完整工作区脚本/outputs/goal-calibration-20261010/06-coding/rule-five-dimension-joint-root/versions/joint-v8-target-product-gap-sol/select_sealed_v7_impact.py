"""Read-only generic impact selection; never imports or executes a classifier.

Run only after complete v7 seal. JSON goes to stdout; the caller freezes it in a
new output directory. No ID whitelist or final-label predicate is used.
"""
from pathlib import Path
import argparse, hashlib, json, sys
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
REFERENCE = '单品种未上市与按需优先机会'
DIMS = ('S','E','Ec','I','F')
KEYS = {'value','basis_path','current_anchor','current_proposition','context_evidence','reason','needed_material','rule_conflict','details'}

def binding(p):
    p=Path(p).resolve(); b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(b):
    observed=binding(b['path'])
    if any(observed[k]!=b[k] for k in ('path','bytes','sha256')): raise ValueError('frozen binding changed: '+b['path'])
    return observed
def marker_paths(x,path='$'):
    result=[]
    if isinstance(x,str):
        if REFERENCE in x: result.append(path)
    elif isinstance(x,dict):
        for k,v in x.items():result.extend(marker_paths(v,path+'/'+str(k)))
    elif isinstance(x,list):
        for i,v in enumerate(x):result.extend(marker_paths(v,path+'/'+str(i)))
    return result
def complete(ds):
    return isinstance(ds,dict) and set(ds)==set(DIMS) and all(isinstance(ds[d],dict) and set(ds[d])==KEYS for d in DIMS)
def classify_record(row):
    # Search final decisions, candidate diagnostics, requests and every other
    # serialized field. Superset matches are harmless; omitted matches are not.
    paths=marker_paths(row)
    failures=bool(row.get('implementation_errors'))
    intact=complete(row.get('decisions')) and complete(row.get('candidate_decisions_diagnostic_only'))
    if intact:
        intact=row['decisions']==row['candidate_decisions_diagnostic_only'] and isinstance(row.get('labels'),dict) and set(row['labels'])==set(DIMS) and all(row['labels'][d]==row['decisions'][d]['value'] for d in DIMS)
        f=row['decisions']['F'];details=f.get('details')
        if f['value']==1:intact=intact and isinstance(details,dict) and isinstance(details.get('unresolved_semantic_boundaries'),list)
        if f['value'] is None and f.get('basis_path')=='manual_relation_boundary':intact=intact and bool(f.get('needed_material')) and isinstance(f.get('rule_conflict'),dict) and isinstance(f['rule_conflict'].get('boundary_requests'),list)
    reasons=[]
    if paths:reasons.append('original_boundary_marker_anywhere_in_full_serialized_record')
    if failures:reasons.append('technical_failure_not_eligible_for_reuse')
    if not intact:reasons.append('incomplete_or_nonidentical_final_and_candidate_decisions_not_eligible_for_reuse')
    return {'id':row.get('id'),'recompute':bool(reasons),'reasons':reasons,'marker_paths':paths,'final_F_value':row.get('decisions',{}).get('F',{}).get('value') if isinstance(row.get('decisions'),dict) else None}

def main():
    a=argparse.ArgumentParser();a.add_argument('--run-directory',required=True);args=a.parse_args()
    run=Path(args.run_directory).resolve();seal=json.loads((run/'seal.json').read_bytes());execution=json.loads((run/'execution.json').read_bytes())
    if seal.get('status') not in {'sealed_complete_production_provisional_rule_run','sealed_failed_execution_attempt'}:raise ValueError('v7 has not completed and sealed')
    if seal.get('source_packet_unchanged') is not True or seal.get('no_reference_read') is not True:raise ValueError('old input/source binding not eligible for partial reuse')
    for group in ('implementation_files','material_bindings','control_inputs'):
        for b in seal[group]:verify(b)
    predictions=run/'predictions.jsonl';verify(seal['prediction_binding'])
    if Path(seal['prediction_binding']['path']).resolve()!=predictions:raise ValueError('seal points to another prediction stream')
    sealed_outputs={Path(x['path']).resolve():x for x in seal['output_files']}
    for p in (run/'execution.json',run/'freeze.json',predictions):
        if p not in sealed_outputs:raise ValueError('required final dependency absent from output seal')
        verify(sealed_outputs[p])
    freeze=json.loads((run/'freeze.json').read_bytes());scope=freeze['source_scope']
    if freeze.get('fixed_algorithm_version')!='joint-v7-relation-content-sol':raise ValueError('not the proven v7 algorithm')
    for b in json.loads((P/'pre-edit-freeze.json').read_bytes())['original_v7_code']:
        matching=[x for x in seal['implementation_files'] if x.get('path')==b['path']]
        if len(matching)!=1 or any(matching[0][k]!=b[k] for k in ('bytes','sha256')):raise ValueError('old v7 algorithm differs from proven branch')
    for b in json.loads((P/'candidate-freeze.json').read_bytes())['candidate_modules']:verify(b)
    global_errors=[e for e in execution.get('implementation_errors',[]) if not isinstance(e,dict) or not e.get('id')]
    if global_errors:raise ValueError('global old execution failure: partial reuse is not proved; repair or full recomputation required')
    rows=[]
    with predictions.open() as f:
        for line in f:
            if not line.endswith('\n'):raise ValueError('unfinished prediction line')
            rows.append(json.loads(line))
    ids=[r.get('id') for r in rows];expected=scope['approved_record_ids']
    if len(ids)!=4481 or len(set(ids))!=4481 or ids!=expected or execution.get('actual_record_N')!=4481 or seal.get('record_N')!=4481:raise ValueError('complete ordered 4481 population not sealed; do not freeze an interim affected set')
    selected=[classify_record(r) for r in rows]
    print(json.dumps({'operation':'read_only_impact_selection_no_recode','old_prediction_binding':binding(predictions),'old_seal_binding':binding(run/'seal.json'),'old_execution_binding':binding(run/'execution.json'),'old_freeze_binding':binding(run/'freeze.json'),'candidate_freeze_binding':binding(P/'candidate-freeze.json'),'selector_binding':binding(__file__),'record_N':len(rows),'selected_N':sum(x['recompute'] for x in selected),'affected_records':[x for x in selected if x['recompute']],'reusable_N':sum(not x['recompute'] for x in selected),'selection_rule':'old full-record boundary marker OR technical failure OR incomplete diagnostic; no final-null restriction and no ID whitelist','affected_set_is_sufficient_not_asserted_minimal':True,'requires_same_packets_same_adapter_source_evidence_and_production_wrapper':True,'new_inference_calls':0,'formal_validation_complete':False},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
