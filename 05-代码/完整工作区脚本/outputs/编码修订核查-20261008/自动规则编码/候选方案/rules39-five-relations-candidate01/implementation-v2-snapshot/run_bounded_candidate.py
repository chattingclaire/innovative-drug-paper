"""Only frozen synthetic31 + fixed old180; no CLI option for full corpus."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from reserved_context_redactor import ReservedRedactor, digest_file

ROOT = Path('/PROJECT_ROOT')
BASE = Path(__file__).resolve().parent
OUT = BASE/'audit-run01'
DIMS = ('S','E','Ec','I','F')


def write(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def field_diff(before, after, path='$'):
    if type(before) is not type(after):
        return [{'path': path, 'before': before, 'after': after}]
    if isinstance(before, dict):
        diffs = []
        for k in sorted(set(before)|set(after)):
            if k not in before:
                diffs.append({'path':path+'.'+k,'kind':'added','after':after[k]})
            elif k not in after:
                diffs.append({'path':path+'.'+k,'kind':'removed','before':before[k]})
            else:
                diffs.extend(field_diff(before[k], after[k], path+'.'+k))
        return diffs
    if isinstance(before, list):
        # Preserve full changed arrays, including removed evidence, not just labels.
        return [] if before == after else [{'path': path, 'before': before, 'after': after}]
    return [] if before == after else [{'path': path, 'before': before, 'after': after}]


def check_prediction(inp, pred):
    for e in pred.get('evidence', []):
        assert inp['unit_text'][e['start']:e['end']] == e['text']
        assert e['dimension'] in DIMS
    if pred['judgement_status'] != 'undetermined':
        assert all(type(pred['labels'][d]) is int and pred['labels'][d] in (0,1) for d in DIMS)
        assert pred['labels'] == {d:int(any(e['dimension']==d for e in pred['evidence'])) for d in DIMS}


def main():
    started = time.time()
    if OUT.exists():
        raise FileExistsError('Bounded output directory already exists; refusing overwrite')
    OUT.mkdir()
    freeze=json.loads((BASE/'implementation_freeze_v2.json').read_text())
    for rel, sha in freeze['files'].items():
        assert digest_file(BASE/rel)==sha, rel
    guard=ReservedRedactor(ROOT)
    source38=ROOT/'outputs/coding-revision-20261008-r4/rules-v38-development/runtime'
    sys.path.insert(0,str(BASE/'runtime'))
    old = load_module('bounded_source38', source38/'policy_coding_v27.py')
    new = load_module('bounded_candidate39', BASE/'runtime/policy_coding_v27.py')
    controls=json.loads((BASE/'design-v2/controls_FULL5_FROZEN.json').read_text())['controls']
    control_results=[]
    for c in controls:
        p=new.code_unit(c['input']);check_prediction(c['input'],p)
        if c.get('expected_material_issue'):
            checks={'judgement_status':p.get('judgement_status')==c['expected_judgement_status'], 'missing_reference_gate':p.get('current_reference_gate_v39',{}).get('publishable') is False, 'labels_not_published':all(p['labels'][d] is None for d in DIMS)}
        else:
            checks={'full5':p['labels']==c['expected_labels']}
            for dim, expected in c.get('expected_subtype_requirements',{}).items():
                checks['subtypes_'+dim]=p['fairness_subtypes' if dim=='F' else 'innovation_subtypes']==expected
            if 'expected_safety_quality_basis' in c:
                checks['safety_quality_basis']=p.get('safety_quality_basis')==c['expected_safety_quality_basis']
                checks['safety_subtypes']=p.get('safety_subtypes')==c['expected_safety_subtypes']
        control_results.append({'id':c['id'],'expected_labels':c['expected_labels'],'checks':checks,'passed':all(checks.values()),'prediction':p})
    write(OUT/'controls_results_PRIVATE.json',guard.walk(control_results,'synthetic_controls'))
    # Always report failures; never alter frozen expectations to match output.
    summary={'control_n':len(control_results),'control_pass_n':sum(c['passed'] for c in control_results),'control_failures':[{'id':c['id'],'checks':c['checks'],'actual_labels':c['prediction']['labels']} for c in control_results if not c['passed']]}
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    if summary['control_failures']:
        summary['status']='CONTROL_FAILURE_STOPPED_BEFORE_OLD180'
        write(OUT/'bounded_summary.json',summary)
        raise SystemExit(2)
    sampling=ROOT/'outputs/coding-revision-20261007-r3/admin/confirmation_sampling_PRIVATE.json'
    sample=json.loads(sampling.read_text())['sample']
    ids={r['original_id'] for r in sample if r['component']=='probability_canonical'}
    assert len(ids)==180
    ruleinput=ROOT/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
    selected=[]
    for line in ruleinput.open():
        row=json.loads(line)
        if row['original_id'] in ids:selected.append(row)
    assert len(selected)==180 and {r['original_id'] for r in selected}==ids
    frozen38file=ROOT/'outputs/coding-revision-20261008-r4/rules-v38-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
    frozen38={}
    for line in frozen38file.open():
        row=json.loads(line)
        if row['original_id'] in ids:frozen38[row['original_id']]=row['prediction']
    assert len(frozen38)==180
    predictions=[];machine_predictions=[];changed=[];baseline_differences=[];tally=collections.Counter()
    for index,row in enumerate(selected,1):
        rid=row['original_id'];inp=row['input']
        # No original text is printed. Guarded views are the only semantic artifacts.
        oldp=old.code_unit(inp);newp=new.code_unit(inp)
        check_prediction(inp,oldp);check_prediction(inp,newp)
        bd=field_diff(frozen38[rid],oldp)
        if bd:baseline_differences.append({'original_id':rid,'changes':bd})
        delta=field_diff(oldp,newp)
        label_changes={d:{'before':oldp['labels'][d],'after':newp['labels'][d]} for d in DIMS if oldp['labels'][d]!=newp['labels'][d]}
        for d in label_changes:tally[d]+=1
        prediction={'original_id':rid,'id':row['id'],'prediction':newp}
        machine_predictions.append(prediction)
        predictions.append(guard.walk(prediction,rid,'$.candidate_output'))
        material_delta=[x for x in delta if x['path']!='$.version']
        if material_delta:
            changed.append(guard.walk({'original_id':rid,'input':inp,'label_changes':label_changes,'all_field_changes':delta,'before':oldp,'after':newp},rid,'$.changed_unit'))
        if index%30==0:print(json.dumps({'old180_completed':index,'label_changed_cells_so_far':dict(tally)},ensure_ascii=False),flush=True)
    with (OUT/'candidate39_old180_predictions_MACHINE_RAW_NO_SEMANTIC_READING.jsonl').open('x') as f:
        for p in machine_predictions:f.write(json.dumps(p,ensure_ascii=False)+'\n')
    with (OUT/'candidate39_old180_predictions_REDACTED_PRIVATE.jsonl').open('x') as f:
        for p in predictions:f.write(json.dumps(p,ensure_ascii=False)+'\n')
    write(OUT/'old180_all_field_changes_REDACTED_PRIVATE.json',{'includes_all_nonversion_field_changes':True,'version_changed_all_180':True,'changed_units':changed})
    write(OUT/'old180_reproduced38_vs_frozen38_REDACTED_PRIVATE.json',guard.walk(baseline_differences,'old38_reproduction'))
    write(OUT/'redaction_contact_METADATA_ONLY.json',{'bindings':guard.bindings,'contacts':guard.contacts,'prior_exposure_disclosure':'Earlier old180 diagnostic review before this guard exposed reserved03216/03222 in00919 supplied article context; no reserved predictions/labels/human answers read. Guard now precedes all semantic projections. No zero-context-exposure claim.'})
    summary.update({'old180_n':180,'dimension_cells':900,'source38_reproduction_difference_units':len(baseline_differences),'candidate_nonversion_change_units':len(changed),'label_changed_cells':dict(tally),'label_changes':[{'original_id':c['original_id'],'label_changes':c['label_changes']} for c in changed if c['label_changes']],'all_180_version_changed':True,'elapsed_seconds':round(time.time()-started,3),'source_bindings':{'sampling_sha256':digest_file(sampling),'rule_input_sha256':digest_file(ruleinput),'source38_predictions_sha256':digest_file(frozen38file)},'no_full4924_run':True,'no_AB_T_consumed_by_classifier':True,'status':'BOUNDED_DEVELOPMENT_REVIEW_REQUIRED'})
    write(OUT/'bounded_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
