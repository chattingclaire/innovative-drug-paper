"""Merge only completed source-only v14 replacement submissions, never relabel.

Run after the root has dispatched independent reviewers and all four explicitly
named result files exist. Output remains a reference stage, not final statistics.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import datetime
import json
import statistical_core_r3 as c
import reference_bindings_r3 as b
import final_binding_io_r3 as io
from prepare_final_reference_and_third_r3 import validate_semantics_shape

RUN=c.RUN


def bd(path):return {'path':str(Path(path).resolve()),'sha256':c.sha(path)}
def put(path,value):
    assert not path.exists(),f'Preserve existing output: {path}'
    c.write_json(path,value)
def putjl(path,rows):
    assert not path.exists(),f'Preserve existing output: {path}'
    path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))


def complete_spec(prepared):
    spec={k:deepcopy(prepared[k]) for k in ('packet','schema','material_version','reviewer_identity')}
    spec['result']=bd(prepared['expected_result_path'])
    spec['reviewer_qa']=bd(prepared['expected_qa_path'])
    # Technical evidence is preserved; semantic decisions come exclusively from
    # the reviewer's unmodified submitted result, independently checked below.
    c.read(spec['reviewer_qa']['path'])
    return spec


def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze-sha256',required=True);args=p.parse_args()
    freeze_path=RUN/'admin/source_rereading_v14_freeze.json'
    assert c.sha(freeze_path)==args.freeze_sha256
    freeze=c.read(freeze_path)
    source=io.bound_jsonl(freeze['new_input'])
    assert io.bound(freeze['source_qa'])['all_checks_pass'] is True
    assert all(c.sha(path)==h for path,h in freeze['protected_historical_file_sha256'].items())
    mapping=b.mapping_index(freeze['A_C_mapping'])
    old_manifest=c.read(RUN/'statistics/T参照59-v12阶段绑定.json')
    design=io.bound(old_manifest['sampling_design']);sample={r['original_id']:r for r in design['sample']}
    changed=set(freeze['source_changed_sample_ids'])
    merged={};audit={};literal={};specs={}
    for coder in 'AC':
        spec=complete_spec(freeze['packets'][coder]);specs[coder]=spec
        loaded=io.submission_with_reviewer_identity(spec,coder,mapping)
        assert set(loaded)==changed
        prior=io.bound_jsonl(old_manifest['references'][coder]);first=c.jsonl(RUN/f'reference/agent_{coder}_first_v9.jsonl')
        final=deepcopy(prior);literal[coder]=[];audit[coder]={}
        for rid,item in loaded.items():
            packet=io.bound(spec['packet']);row_source=next(x for x in packet['rows'] if x['id']==item['row']['id'])
            assert all(row_source[k]==source[rid][k] for k in io.MATERIAL_FIELDS)
            quote_check=validate_semantics_shape(item['row'],row_source)
            assert all(c.binary(item['row']['labels'][d]) for d in c.DIMS)
            previous=deepcopy(prior[rid]['annotation_provenance'])
            history=deepcopy(previous.get('effective_history',[previous['effective']]))
            history.append(deepcopy(item['provenance']))
            provenance={**previous,'v12_effective':deepcopy(previous['effective']),
                'effective':deepcopy(item['provenance']),'effective_history':history,
                'reread_applied':True,'v14_replacement_source_rereview_applied':True,
                'v12_to_v14_label_change_dimensions':[d for d in c.DIMS if prior[rid]['labels'][d]!=item['row']['labels'][d]],
                'label_change_dimensions':[d for d in c.DIMS if first[rid]['labels'][d]!=item['row']['labels'][d]]}
            row=deepcopy(item['row']);row['blind_id']=row['id'];row['id']=rid
            row['annotation_provenance']=provenance;final[rid]=row
            audit[coder][rid]=provenance;literal[coder].append({'id':rid,'evidence':quote_check})
        for row in final.values():row['effective_material_version']='v14'
        io.validate_effective_reference(final,{'sample':sample,'llm_inputs':source})
        merged[coder]=final
    # Assemble all T first submissions and only the exact material-changed reread.
    policy=io.bound(freeze['reference_policy']);tmap=b.mapping_index(freeze['mapping'])
    t_first=complete_spec(freeze['packets']['T_first']);t_reread=complete_spec(freeze['packets']['T_reread'])
    third={**deepcopy(old_manifest['third']),'policy_freeze':freeze['reference_policy'],'mapping':freeze['mapping'],
        'additional_first_submissions':deepcopy(old_manifest['third']['additional_first_submissions'])+[t_first],
        'rereads':[t_reread]}
    first_specs=[third['first'],*third['additional_first_submissions']]
    loaded_first=[io.submission_with_reviewer_identity(s,'T',tmap) for s in first_specs]
    loaded_reread=[io.submission_with_reviewer_identity(t_reread,'T',tmap)]
    t_final,t_audit=b.merge_coder(loaded_first,loaded_reread,policy['mixed_original_id_order'],
        freeze['source_changed_existing_T_ids'])
    assert len(t_final)==66
    for rid,row in t_final.items():
        provenance=t_audit[rid]['effective'];packet=io.bound({'path':provenance['packet_path'],'sha256':provenance['packet_sha256']})
        row_source=next(x for x in packet['rows'] if x['id']==provenance['blind_id'])
        assert all(row_source[k]==source[rid][k] for k in io.MATERIAL_FIELDS)
        validate_semantics_shape(row,row_source)
        assert all(c.binary(row['labels'][d]) for d in c.DIMS)
        row['annotation_provenance']=t_audit[rid];row['effective_material_version']='v14'
    candidate=b.assemble_candidate(merged['A'],merged['C'],t_final,policy['mixed_original_id_order'],policy['resolution_policy'])
    disagreements=[rid for rid in sample if any(merged['A'][rid]['labels'][d]!=merged['C'][rid]['labels'][d] for d in c.DIMS)]
    assert set(disagreements)<=set(t_final)
    assert all(c.sha(path)==h for path,h in freeze['protected_historical_file_sha256'].items())
    # Only publish after every submission and the full candidate assemble pass.
    for coder in 'AC':putjl(RUN/f'reference/agent_{coder}_final_v14.jsonl',[merged[coder][rid] for rid in sample])
    putjl(RUN/'reference/agent_T_first66_current_v14_STAGE.jsonl',[t_final[rid] for rid in policy['mixed_original_id_order']])
    putjl(RUN/'reference/candidate_reference_v14_STAGE.jsonl',[candidate[rid] for rid in sample])
    manifest=deepcopy(old_manifest)
    manifest['stage']='v14_reference_stage_after_replacement_source_rereviews_pending_execution'
    manifest['material']={'version':'v14','source_qa':freeze['source_qa'],
        'rule_inputs':bd(RUN/'rule_inputs_shared_v14.jsonl'),'llm_inputs':freeze['new_input']}
    manifest['references']={r:bd(RUN/f'reference/agent_{r}_final_v14.jsonl') for r in 'AC'}
    manifest['third']=third
    manifest['reviewer_identity_note']='A/C role streams include replacement-agent source rereviews for two units each. T includes seven new first submissions and one replacement source rereview. These are not the original individual agents, and no human validation is claimed.'
    ctx=io.context_from_manifest(manifest);rebuilt,rebuilt_audit=io.final_references(manifest,ctx)
    assert rebuilt['candidate']==candidate
    binding_path=RUN/'statistics/T参照66-v14阶段绑定.json';put(binding_path,manifest)
    ledger=[]
    old_candidate=c.jsonl(RUN/'reference/candidate_reference_v12_STAGE.jsonl')
    for rid in sample:
        dims=[d for d in c.DIMS if old_candidate[rid]['labels'][d]!=candidate[rid]['labels'][d]]
        if dims:ledger.append({'id':rid,'changed_dimensions':dims,
            'before':old_candidate[rid]['labels'],'after':candidate[rid]['labels'],
            'new_reference_reason':{d:t_final[rid]['dimension_reasons'][d] for d in dims} if rid in t_final else None})
    qa={'status':'pass_v14_reference_stage_replacement_provenance_and_literal_QA','all_checks_pass':True,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'source_freeze':bd(freeze_path),
        'binding':bd(binding_path),'reviewed_T_n':66,'T_v14_new_first_n':7,'T_v14_source_reread_n':1,
        'AC_v14_source_reread_n_each':2,'AC_disagreement_n':len(disagreements),'all_AC_disagreements_T_covered':True,
        'replacement_identity_note':manifest['reviewer_identity_note'],'A_C_replacement_specs':specs,
        'A_C_increment_provenance':audit,'A_C_literal_evidence_QA':literal,'T_binding_audit':rebuilt_audit['T'],
        'candidate_change_ledger':ledger,'all_effective_material_rows_match_v14':True,
        'all_historical_files_unchanged':True,'machine_predictions_or_scores_used':False,'human_validation_completed':False,
        'output_bindings':{r:manifest['references'][r] for r in 'AC'}|{
            'candidate':bd(RUN/'reference/candidate_reference_v14_STAGE.jsonl'),
            'T':bd(RUN/'reference/agent_T_first66_current_v14_STAGE.jsonl')},'script_sha256':c.sha(Path(__file__))}
    put(RUN/'reference/A_C_T合并与逐字证据QA-v14.json',qa)
    print(json.dumps({'status':qa['status'],'binding':str(binding_path),'candidate_changed_case_n':len(ledger)},ensure_ascii=False))


if __name__=='__main__':main()
