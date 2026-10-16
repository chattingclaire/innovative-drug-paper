"""Independent mechanical QA and fixed-factor comparison, never new references.

This script reads completed outputs and input bindings; it never invokes the
classifier, changes labels, or reads any r3 confirmation/admin material.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ('S','E','Ec','I','F')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jl(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def save(path, data):
    assert not path.exists(), 'Never overwrite an audit/release.'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def changes(left, right, inputs):
    out=[]
    for a,b,i in zip(left,right,inputs):
        assert a['id']==b['id']==i['id']
        for d in DIMENSIONS:
            av=a['prediction']['labels'][d];bv=b['prediction']['labels'][d]
            if av==bv:
                continue
            r=i['input']
            out.append({'id':i['id'],'original_id':i['original_id'],'dimension':d,
                        'before':av,'after':bv,'unit_text':r['unit_text'],
                        'unit_text_sha256':hashlib.sha256(r['unit_text'].encode()).hexdigest(),
                        'source_path':r.get('unit_source') or r['source'],
                        'source_sha256':r.get('unit_source_sha256') or r['source_sha256'],
                        'candidate_path':r['candidate_file'],'candidate_sha256':r['candidate_sha256'],
                        'pages':r.get('pages',[]),'paragraph_context':r.get('paragraph_context',[]),
                        'supplied_parent_context':r.get('verified_parent_context',[]),
                        'source_adapter_log':b['prediction'].get('source_context_adaptation_log_v33',[]),
                        'before_evidence':[e for e in a['prediction']['evidence'] if e['dimension']==d],
                        'after_evidence':[e for e in b['prediction']['evidence'] if e['dimension']==d],
                        'after_suppressions':[e for e in b['prediction']['suppressions'] if d in e['dimensions']]})
    counts=Counter((x['dimension'],f"{x['before']}->{x['after']}") for x in out)
    return {'changed_label_cells':len(out),'changed_unique_units':len({x['id'] for x in out}),
            'counts':{f'{d}_{direction}':n for (d,direction),n in sorted(counts.items())},'cases':out}


def main():
    freeze_path=ROOT/'candidate_freeze.json';freeze=json.loads(freeze_path.read_text())
    assert all(sha(p)==s for p,s in freeze['production_code_sha256'].items())
    inputs=jl(freeze['input_path']);llm=jl(freeze['llm_shared_material_path'])
    assert sha(freeze['input_path'])==freeze['input_sha256']
    assert sha(freeze['llm_shared_material_path'])==freeze['llm_shared_material_sha256']
    assert len(inputs)==len(llm)==len({r['id'] for r in inputs})==4924
    for r,l in zip(inputs,llm):
        assert r['id']==l['id'] and r['input']['unit_text']==l['text']
        assert r['input']['llm_v29_shared_context']==l['contexts']
    names=['legacy_v32_1_material_v9','source_adapter_only_material_v9',
           'semantic_only_material_v9','all_predictions_material_v9']
    outputs={};runs={};checks=Counter()
    for name in names:
        path=ROOT/f'{name}.jsonl';rp=path.with_suffix('.run.json')
        run=json.loads(rp.read_text());rows=jl(path)
        assert sha(path)==run['prediction_sha256'] and sha(run['input_path'])==run['input_sha256']==freeze['input_sha256']
        assert run['candidate_freeze_sha256']==sha(freeze_path) and run['n']==4924 and run['pending_n']==0
        assert all(sha(p)==s for p,s in run['runtime_code_sha256'].items())
        assert all(sha(p)==s for p,s in run['actual_source_and_candidate_sha256'].items())
        assert len(rows)==4924 and run['reference_labels_loaded'] is False
        for row,inp in zip(rows,inputs):
            assert row['id']==inp['id'] and row['original_id']==inp['original_id']
            p=row['prediction'];text=inp['input']['unit_text']
            assert p['unit_text_sha256']==hashlib.sha256(text.encode()).hexdigest()
            assert set(p['labels'])==set(DIMENSIONS) and all(type(v)is int and v in (0,1) for v in p['labels'].values())
            assert p['judgement_status']!='undetermined'
            assert p['labels']=={d:int(any(e['dimension']==d for e in p['evidence'])) for d in DIMENSIONS}
            for e in p['evidence']:
                assert text[e['start']:e['end']]==e['text'] and e['dimension'] in DIMENSIONS
                if e['dimension']=='I':assert e.get('subtype') in {'attribute','research_support','qualification_advantage'}
                if e['dimension']=='F':assert e.get('subtype') in {'access','affordability','clinical_management','dimension_information'}
                checks[f'{name}_literal_evidence']+=1
            for e in p['suppressions']:
                if all(k in e for k in ('start','end','text')):
                    assert text[e['start']:e['end']]==e['text'];checks[f'{name}_literal_suppressions']+=1
        outputs[name]=rows;runs[name]={'path':str(rp),'sha256':sha(rp),'prediction_path':str(path),'prediction_sha256':sha(path),
                                     'component_settings':run['component_settings']}
    legacy=outputs[names[0]];adapter=outputs[names[1]];semantic=outputs[names[2]];full=outputs[names[3]]
    prior_path=ROOT.parents[1]/'agent-validation-20261007-r2/rules-v32/material-adapter-v32.1/all_predictions_material_v8.jsonl'
    prior=jl(prior_path)
    effect={
        'material_v8_to_v9_same_frozen_legacy_code':changes(prior,legacy,inputs),
        'adapter_main_effect_legacy_semantics':changes(legacy,adapter,inputs),
        'semantic_main_effect_no_adapter':changes(legacy,semantic,inputs),
        'semantic_effect_with_adapter':changes(adapter,full,inputs),
        'adapter_effect_with_semantic_repairs':changes(semantic,full,inputs),
        'combined_effect_vs_legacy_same_v9_material':changes(legacy,full,inputs)}
    effect_path=ROOT/'factorial_effects_and_source_evidence_v33_v9.json'
    save(effect_path,{'status':'fixed_candidate_actual_2x2_effects','reference_or_confirmation_metrics_used':False,
                      'interpretation':'Label-change decomposition only, not accuracy or independent validation. Adapter and semantic changes may interact.',
                      'input_sha256':freeze['input_sha256'],'runs':runs,'comparisons':effect})
    source_rows=[r for r in full if r['prediction'].get('source_context_adaptation_log_v33')]
    assert len(source_rows)==209
    adapter_fields=Counter(log['field'] for r in source_rows for log in r['prediction']['source_context_adaptation_log_v33'])
    assert dict(adapter_fields)=={'verified_document_object_v9':152,'verified_scope_context_v8':51,'verified_parent_list_v8':6}
    qa={'status':'passed_actual_same_material_4924_frozen_candidate_QA','n':4924,
        'input_path':freeze['input_path'],'input_sha256':freeze['input_sha256'],
        'llm_material_path':freeze['llm_shared_material_path'],'llm_material_sha256':freeze['llm_shared_material_sha256'],
        'all_4924_raw_unit_text_and_shared_contexts_equal_between_methods':True,
        'all_output_ids_order_and_original_ids_equal_input':True,'all_labels_rebuilt_from_literal_current_unit_evidence':True,
        'all_production_code_and_input_source_hashes_unchanged':True,
        'all_209_new_source_context_rows_authenticated_and_exposed_by_typed_role':True,
        'source_adapter_field_rows':dict(adapter_fields),'checks':dict(checks),'runs':runs,
        'candidate_freeze_path':str(freeze_path),'candidate_freeze_sha256':sha(freeze_path),
        'factorial_effects_path':str(effect_path),'factorial_effects_sha256':sha(effect_path),
        'no_new_r3_confirmation_admin_or_metrics_read':True,'no_labels_or_frozen_artifacts_modified':True}
    qa_path=ROOT/'actual_execution_QA_material_v9.json';save(qa_path,qa)
    release={'status':'released_frozen_candidate_for_new_confirmation','version':freeze['version'],
        'source_material_version':'v9','n':4924,'pending_n':0,
        'prediction_path':runs[names[3]]['prediction_path'],'prediction_sha256':runs[names[3]]['prediction_sha256'],
        'run_manifest_path':runs[names[3]]['path'],'run_manifest_sha256':runs[names[3]]['sha256'],
        'candidate_freeze_path':str(freeze_path),'candidate_freeze_sha256':sha(freeze_path),
        'input_path':freeze['input_path'],'input_sha256':freeze['input_sha256'],
        'llm_material_path':freeze['llm_shared_material_path'],'llm_material_sha256':freeze['llm_shared_material_sha256'],
        'actual_QA_path':str(qa_path),'actual_QA_sha256':sha(qa_path),
        'factorial_effects_path':str(effect_path),'factorial_effects_sha256':sha(effect_path),
        'r2_reference_identity':'exposed AI-agent development/training material, not human or independent confirmation',
        'new_r3_confirmation_accessed':False,'manual_or_reference_labels_changed':False,
        'validation_status':'Await separate frozen-candidate confirmation; this release is not a declaration of metric adequacy.'}
    release_path=ROOT/'release_material_v9_manifest.json';save(release_path,release)
    print(json.dumps({'QA_path':str(qa_path),'QA_sha256':sha(qa_path),'release_path':str(release_path),
                      'release_sha256':sha(release_path),'factorial_effect_counts':{k:{a:b for a,b in v.items() if a!='cases'} for k,v in effect.items()}},ensure_ascii=False))


if __name__=='__main__':main()
