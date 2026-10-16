"""Read-only post-execution audit; separate immutable phase snapshots.

No model, labels, metrics, A/B/C/T or prompt edits. Independent16 remains in a
separate projection for the independent reviewer, with no expected answers here.
"""
import argparse
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
from candidate08_support import (HERE, ROOT, OLD05, OLD06, OLD07, RUNTIME, DIMS,
    read, sha, binding, dump_new, verify_freeze)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inputs(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.suffix=='.jsonl' else read(path)['rows']


def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def changed_fields(old,new):
    return [field for field in sorted(set(old)|set(new)) if field not in old or field not in new or canonical(old[field])!=canonical(new[field])]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',required=True,choices=['new-controls','inherited-controls','exposed240'])
    args=parser.parse_args()
    _,plan=verify_freeze()
    phases=[p['phase'] for p in plan['phases']]
    phase_index=phases.index(args.phase)
    expected_keys=[k for p in plan['phases'][:phase_index+1] for k in p['run_keys']]
    helper=module('candidate08_v2_json_input_audit',HERE/'technical_audit_json_adapter.py')
    redactor=module('candidate08_reserved_redactor',ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py').ReservedContextRedactor()
    adapter={'candidate05_prompt':{'sha256':sha(HERE/'candidate08_prompt_PROPOSED.txt')},
        'runtime':{n:{'sha256':sha(RUNTIME/n)} for n in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']}}
    outputs,technical,new_issues240={},[],[]
    for run in plan['runs']:
        folder=RUNTIME/run['run_name']
        if run['run_key'] not in expected_keys:
            assert not folder.exists(), 'Audit phase must match chronological scope; later phase already exists.'
            continue
        actual,qa=helper.audit_run(folder,{'n':run['n'],'batch_size':25,'logical_batches':run['logical_requests'],'input':run['input_binding']['path']},adapter)
        outputs[run['run_key']]={r['id']:r for r in actual}
        qa['run_key']=run['run_key']
        technical.append(qa)
        if run['run_key']=='exposed240':
            new_issues240=read(folder/'all_predictions.json')['issue_records']
    assert sum(r['actual_attempts'] for r in technical)<=sum(r['logical_batches'] for r in technical)*3<=51
    out=HERE/'execution-audit'/args.phase
    out.mkdir(parents=True,exist_ok=True)
    qa={'status':'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING','audit_phase':args.phase,
        'design_freeze_sha256':sha(HERE/'design_freeze.json'),'model_requested':'gpt-5.6-sol','reasoning_effort':'medium',
        'actual_logical_requests':sum(r['logical_batches'] for r in technical),'actual_attempts':sum(r['actual_attempts'] for r in technical),
        'completed_run_keys':expected_keys,'NOT_RUN':[k for k in plan['scope_run_keys'] if k not in expected_keys],
        'runs':technical,'all_selected_raw_bound_to_unique_completed_agent_message':True,
        'first_technically_valid_selection_verified':True,'semantic_or_metric_selection':False,
        'independent_human_validation':False,'labels_or_manuscript_modified':False}
    dump_new(out/'candidate08_technical_QA.json',qa)
    projections=[]
    expectations=read(HERE/'synthetic130_expected_PRIVATE_PROPOSED.json')['tests']
    control_outputs={}
    for key in ['new24','inherited62','inherited24','inherited20']:
        control_outputs.update(outputs.get(key,{}))
    controls=[]
    for test in expectations:
        actual=control_outputs.get(test['input']['id'])
        if actual is None:continue
        fields={k:canonical(actual[k])!=canonical(test[k]) for k in ['fairness_subtypes','innovation_subtypes','safety_quality_basis']}
        controls.append({**test,'candidate08_intact_actual_row':actual,
            'mechanical_different_dimensions':[d for d in DIMS if actual['labels'][d]!=test['labels'][d]],
            'mechanical_additional_field_mismatches':fields,
            'semantic_review_required_even_if_mechanically_matching':True})
    projections.append(('candidate08_author_and_inherited_controls_PRIVATE.json',{'tests':controls,
        'all130_count':130,'actual_available_count':len(controls),'not_run_expected_ids':[t['input']['id'] for t in expectations if t['input']['id'] not in control_outputs],
        'inherited_expectations_not_modified':True,'raw_expectation_match_not_semantic_truth':True}))
    independent=next(r for r in plan['runs'] if r['run_key']=='independent16')
    from pathlib import Path
    independent_inputs=inputs(Path(independent['input_binding']['path']))
    assert len(independent_inputs)==16
    projections.append(('candidate08_independent16_FOR_INDEPENDENT_REVIEW_ONLY_PRIVATE.json',{'input_binding':independent['input_binding'],
        'rows':[{'input':i,'candidate08_intact_actual_row':outputs['independent16'][i['id']]} for i in independent_inputs],
        'independent_expected_answers_not_read_or_copied':True,'not_external_human_validity':True}))
    all240,changes,mandatory=[],[],[]
    if 'exposed240' in outputs:
        sources={r['id']:r for r in inputs(HERE/'exposed240_inputs_UNCHANGED.jsonl')}
        assert not any(redactor.is_reserved(i) for i in sources)
        histories={}
        for name,b in read(OLD05/'historical_comparison_freeze.json')['frozen_files'].items():
            assert sha(b['path'])==b['sha256']
            if name.endswith('_rows'):histories[name]={r['id']:r for r in inputs(Path(b['path']))}
        history_folders={'candidate05_intact_actual_rows':OLD05/'runtime-v2/exposed240-candidate05-first-run',
            'candidate06_intact_actual_rows':OLD06/'runtime-unchanged-v2/exposed240-candidate06-first-run',
            'candidate07_intact_actual_rows':OLD07/'runtime-unchanged-v2/exposed240-candidate07-first-run'}
        prior_issues={}
        for name,folder in history_folders.items():
            histories[name]={r['id']:r for r in inputs(folder/'all_predictions.jsonl')}
            prior_issues[name]=read(folder/'all_predictions.json')['issue_records']
        assert all(set(h)==set(sources) for h in histories.values())
        for ident,source in sources.items():
            new=outputs['exposed240'][ident]
            prior={k:v[ident] for k,v in histories.items()}
            old_notes={k:[n for n in v if n['id']==ident] for k,v in prior_issues.items()}
            new_notes=[n for n in new_issues240 if n['id']==ident]
            fields={k:changed_fields(v,new) for k,v in prior.items()}
            issue_change={k:canonical(v)!=canonical(new_notes) for k,v in old_notes.items()}
            entry={'id':ident,'input':source,'candidate08_intact_actual_row':new,'historical_intact_rows':prior,
                'changed_dimensions_vs_each_history':{k:[d for d in DIMS if v['labels'][d]!=new['labels'][d]] for k,v in prior.items()},
                'changed_output_fields_vs_each_history':fields,'candidate08_issue_records':new_notes,
                'available_historical_issue_records':old_notes,'issue_records_changed_vs_available_history':issue_change,
                'older03_04_issue_records_not_available_in_row_snapshot':True,'semantic_truth_not_inferred_from_agreement':True}
            all240.append(entry)
            if any(fields.values()) or any(issue_change.values()):changes.append(entry)
        gates=read(HERE/'predeclared_acceptance_PROPOSED.json')
        mids=set(gates['mandatory_review_ids'])
        assert len(mids)==42 and mids<=set(sources)
        mandatory=[r for r in all240 if r['id'] in mids]
        projections.extend([('candidate08_all240_comparison_REDACTED_PRIVATE.json',{'rows':all240,'all_rows_full_semantic_review_required':True}),
            ('candidate08_all_changes_REDACTED_PRIVATE.json',{'rows':changes}),
            ('candidate08_mandatory42_REDACTED_PRIVATE.json',{'rows':mandatory,'review_even_if_unchanged':True,'boundary_cells_not_forced':True})])
    redactions=[]
    for name,obj in projections:
        clean,hits=redactor.redact_object(obj)
        assert redactor.audit_object_no_full_match(clean)['no_remaining_full_normalized_reserved_unit_match']
        path=out/name
        dump_new(path,clean)
        redactions.append({'projection':binding(path),'hits_ID_and_field_path_only':[{'reserved_unit_id':h['reserved_unit_id'],'field_path':h['locator']} for h in hits],
            'post_projection_no_full_normalized_match':True})
    dump_new(out/'candidate08_human_review_redaction_metadata.json',{'original_model_inputs_and_outputs_unmodified':True,
        'records':redactions,'limitation':'Full normalized reserved originals only; partial quotes/paraphrases may escape detection. Protected index not serialized.'})
    print(json.dumps({'status':qa['status'],'phase':args.phase,'logical_requests':qa['actual_logical_requests'],
        'attempts':qa['actual_attempts'],'controls_for_author_review':len(controls),'independent_controls':16,
        'all240':len(all240),'changed_rows_all_fields':len(changes),'mandatory':len(mandatory)},ensure_ascii=False))


if __name__=='__main__':main()
