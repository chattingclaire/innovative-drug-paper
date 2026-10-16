"""Strict final manifest IO, context equality and frozen third-reference policy."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json
import statistical_core_r3 as c
import reference_bindings_r3 as b
from prepare_final_reference_and_third_r3 import validate_semantics_shape

MATERIAL_FIELDS=('text','source_title','pages','contexts','context_usage')


def bound(binding):return b.bound_json(binding)
def bound_jsonl(binding):
    if c.sha(binding['path'])!=binding['sha256']:raise ValueError('JSONL SHA mismatch: '+binding['path'])
    return c.jsonl(binding['path'])


def submission_with_reviewer_identity(item,coder,mapping):
    """Keep replacement-reviewer identity explicit without altering judgments."""
    loaded=b.load_submission(item['result'],item['packet'],item['schema'],coder,
                             item['material_version'],mapping)
    if 'reviewer_identity' in item:
        identity=deepcopy(item['reviewer_identity'])
        if identity.get('review_event','').startswith('replacement_'):
            assert identity.get('same_agent_as_original_reviewer') is False
            assert identity.get('AI_agent') is True and identity.get('human_reviewer') is False
        for value in loaded.values():value['provenance']['reviewer_identity']=identity
    if 'reviewer_qa' in item:
        bound(item['reviewer_qa'])
        for value in loaded.values():
            value['provenance']['reviewer_identity_and_execution_qa']=deepcopy(item['reviewer_qa'])
    return loaded


def context_from_manifest(manifest):
    if manifest.get('root_final_bindings_confirmed') is not True:
        raise ValueError('Root must confirm final paths/SHA/material version before tables')
    material=manifest['material']
    source_qa=bound(material['source_qa'])
    if source_qa.get('all_checks_pass') is not True:raise ValueError('Final source QA not passed')
    rule_inputs=bound_jsonl(material['rule_inputs']);llm_inputs=bound_jsonl(material['llm_inputs'])
    assert len(rule_inputs)==len(llm_inputs)==4924 and set(rule_inputs)==set(llm_inputs)
    for rid in rule_inputs:
        assert rule_inputs[rid]['input']['unit_text']==llm_inputs[rid]['text']
        assert rule_inputs[rid]['input']['llm_v29_shared_context']==llm_inputs[rid]['contexts']
    design=bound(manifest['sampling_design']);sample={r['original_id']:r for r in design['sample']}
    assert len(sample)==240 and design['frame_N_by_group']==c.EXPECTED_ELIGIBLE
    metadata=bound(manifest['metadata']);meta={Path(r['original_file']).stem:r for r in metadata['rows']}
    groups={rid:meta[r['input']['original_file_stem']]['analysis_group'] for rid,r in rule_inputs.items()}
    sources={rid:r['input'].get('unit_source',r['input']['source']) for rid,r in rule_inputs.items()}
    assert Counter(groups.values())==Counter({'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443})
    assert Counter((r['component'],r['group']) for r in sample.values())==Counter(
        {('probability_canonical',g):60 for g in c.GROUPS}|{('enriched_challenge',g):30 for g in ('NMPA','NHSA')})
    for rid,row in sample.items():
        assert groups[rid]==row['group']
        if row['component']=='probability_canonical':
            assert row['sample_n']==60 and row['canonical_frame_N']==c.EXPECTED_ELIGIBLE[row['group']]
            assert abs(row['analysis_weight']-row['canonical_frame_N']/60)<1e-12
        else:assert row['analysis_weight'] is None
    return {'design':design,'sample':sample,'inputs':rule_inputs,'llm_inputs':llm_inputs,
            'metadata':meta,'groups':groups,'sources':sources,'material_version':material['version']}


def validate_effective_reference(rows,ctx):
    assert set(rows)==set(ctx['sample'])
    packets={};checked=[]
    for rid,row in rows.items():
        provenance=row['annotation_provenance']['effective']
        path=provenance['packet_path'];digest=provenance['packet_sha256']
        if (path,digest) not in packets:
            packet=bound({'path':path,'sha256':digest})
            packets[path,digest]={r['id']:r for r in packet['rows']}
        source=packets[path,digest][provenance['blind_id']]
        assert all(source[k]==ctx['llm_inputs'][rid][k] for k in MATERIAL_FIELDS),(rid,'reference_material_not_final')
        validate_semantics_shape(row,ctx['llm_inputs'][rid])
        assert all(c.binary(row['labels'][d]) for d in c.DIMS)
        checked.append(rid)
    return checked


def final_references(manifest,ctx):
    refs={};audit={}
    for coder in 'AC':
        rows=bound_jsonl(manifest['references'][coder])
        audit[coder]={'material_ids_checked':validate_effective_reference(rows,ctx),
                      'reference_binding':manifest['references'][coder]}
        refs[coder]=rows
    third=manifest['third'];policy=bound(third['policy_freeze'])
    assert policy['resolution_policy']=='third_for_every_reviewed_dimension'
    reviewed=policy['mixed_original_id_order'];mapping=b.mapping_index(third['mapping'])
    first_specs=[third['first'],*third.get('additional_first_submissions',[])]
    first_loaded=[];first_sources={};initial_coverage=set();additional_first_ids=[]
    for index,item in enumerate(first_specs):
        packet_loaded=submission_with_reviewer_identity(item,'T',mapping)
        assert not initial_coverage&set(packet_loaded),'Additional first submissions overlap already judged T IDs'
        initial_coverage.update(packet_loaded);first_loaded.append(packet_loaded)
        if index:additional_first_ids.extend(packet_loaded)
        for row in bound(item['packet'])['rows']:
            first_sources[mapping['T',row['id']]['original_id']]=row
    assert initial_coverage==set(reviewed)
    if policy.get('additional_first_submissions_not_rereads') is True:
        assert set(additional_first_ids)==set(policy['additional_first_submission_original_ids'])
    changed={rid for rid in reviewed if any(first_sources[rid][k]!=ctx['llm_inputs'][rid][k] for k in MATERIAL_FIELDS)}
    rereads=[]
    for item in third.get('rereads',[]):
        rereads.append(submission_with_reviewer_identity(item,'T',mapping))
    final,audit_t=b.merge_coder(first_loaded,rereads,reviewed,changed)
    for rid,row in final.items():
        provenance=audit_t[rid]['effective'];packet=bound({'path':provenance['packet_path'],'sha256':provenance['packet_sha256']})
        source=next(r for r in packet['rows'] if r['id']==provenance['blind_id'])
        assert all(source[k]==ctx['llm_inputs'][rid][k] for k in MATERIAL_FIELDS),(rid,'T_material_not_final')
        validate_semantics_shape(row,ctx['llm_inputs'][rid])
        assert all(c.binary(row['labels'][d]) for d in c.DIMS)
    candidate=b.assemble_candidate(refs['A'],refs['C'],final,reviewed,policy['resolution_policy'])
    refs['candidate']=candidate
    audit['T']={'policy_binding':third['policy_freeze'],'mapping_binding':third['mapping'],
                'reviewed_original_ids':reviewed,'material_changed_reread_original_ids':sorted(changed),
                'additional_independent_first_submission_original_ids':additional_first_ids,
                'first_submission_bindings':first_specs,
                'provenance':audit_t,'all_dimensions_replaced_on_all_reviewed_cases':True}
    return refs,audit


def final_methods(manifest,ctx):
    methods={}
    for name in ('rules','LLM'):
        entry=manifest['methods'][name]
        assert entry['frozen_method_id']==('rules-v33' if name=='rules' else 'LLM-v32-candidate02'), 'Post-exposure development methods require a separate diagnostic pipeline'
        assert entry['material_version']==ctx['material_version']
        rows=bound_jsonl(entry['output'])
        assert len(rows)==4924 and set(rows)==set(ctx['inputs'])
        assert all(c.binary(c.label(row,d)) for row in rows.values() for d in c.DIMS)
        qa=bound(entry['execution_qa'])
        assert qa.get('all_checks_pass') is True or qa.get('status') in ('pass','pass_independent_execution_QA')
        assert qa.get('final_output_sha256',entry['output']['sha256'])==entry['output']['sha256']
        methods[name]=rows
    return methods
