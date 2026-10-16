"""Current59-reviewed AI candidate at v12; explicitly not a pending v13 final."""
from pathlib import Path
import datetime
import json
import statistical_core_r3 as c
import final_binding_io_r3 as io
import reference_bindings_r3 as b

RUN=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
REF=RUN/'reference'


def bd(path):return {'path':str(path),'sha256':c.sha(path)}
def putjl(path,rows):
    assert not path.exists();path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))


def main():
    tdir=RUN/'confirmation/agent-T'
    assert c.sha(tdir/'增补首次结果-v12.json')=='8946621fc2e52aa5cc097a514341748b28e4d4cb7d3688f0d3dabbe3e4931097'
    metadata=RUN.parent/'validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
    manifest={'stage':'current_v12_candidate_only_pending_v13_source_freeze','root_final_bindings_confirmed':True,
        'material':{'version':'v12','source_qa':bd(RUN/'audit/independent_source_material_v12_qa.json'),
            'rule_inputs':bd(RUN/'rule_inputs_shared_v12.jsonl'),'llm_inputs':bd(RUN/'effective_blind_inputs_v12.jsonl')},
        'sampling_design':bd(RUN/'admin/confirmation_sampling_PRIVATE.json'),'metadata':bd(metadata),
        'references':{coder:bd(REF/f'agent_{coder}_final_v12.jsonl') for coder in 'AC'},
        'third':{'policy_freeze':bd(RUN/'admin/third_agent_append_selection_policy_freeze_PRIVATE_v12.json'),
            'mapping':bd(RUN/'admin/third_agent_mapping_combined_PRIVATE_v12.json'),
            'first':{'result':bd(tdir/'本方结果-v11.json'),'packet':bd(tdir/'材料-v11.json'),
                'schema':bd(tdir/'结果schema-v11.json'),'material_version':'v11'},
            'additional_first_submissions':[{'result':bd(tdir/'增补首次结果-v12.json'),
                'packet':bd(tdir/'增补材料-v12.json'),'schema':bd(tdir/'增补结果schema-v12.json'),'material_version':'v12'}],
            'rereads':[]}}
    ctx=io.context_from_manifest(manifest);refs,audit=io.final_references(manifest,ctx)
    policy=b.bound_json(manifest['third']['policy_freeze']);mapping=b.mapping_index(manifest['third']['mapping'])
    specs=[manifest['third']['first'],*manifest['third']['additional_first_submissions']]
    loaded=[b.load_submission(spec['result'],spec['packet'],spec['schema'],'T',spec['material_version'],mapping) for spec in specs]
    third,third_audit=b.merge_coder(loaded,[],policy['mixed_original_id_order'],[])
    assert len(third)==59 and not any(row['reread_applied'] for row in third_audit.values())
    assert sum(row['first']['material_version']=='v11' for row in third_audit.values())==51
    assert sum(row['first']['material_version']=='v12' for row in third_audit.values())==8
    original_policy=b.bound_json(policy['original_policy_freeze'])
    original_disagreements=set(original_policy['disagreement_original_ids'])
    original_random={rid for ids in original_policy['agreement_review_original_ids'].values() for rid in ids}
    added_random={rid for ids in policy['random_controls_by_group'].values() for rid in ids}
    source_increment=set(policy['source_changed_designated_original_ids'])
    ledger=[];all_changed_agreements=[];counts={d:{'AC_agree_T_same':0,'AC_agree_T_changed':0,
        'AC_disagree_T_matches_A':0,'AC_disagree_T_matches_C':0} for d in c.DIMS}
    for rid in policy['mixed_original_id_order']:
        a,cc,t=refs['A'][rid],refs['C'][rid],third[rid];dimensions={}
        for dim in c.DIMS:
            av,cv,tv=a['labels'][dim],cc['labels'][dim],t['labels'][dim]
            kind=('AC_agree_T_same' if av==cv==tv else 'AC_agree_T_changed' if av==cv else
                  'AC_disagree_T_matches_A' if tv==av else 'AC_disagree_T_matches_C')
            counts[dim][kind]+=1
            dimensions[dim]={'A':av,'C':cv,'T':tv,'category':kind,
                'effective_candidate_value':refs['candidate'][rid]['labels'][dim],
                'A_reason':a['dimension_reasons'][dim],'C_reason':cc['dimension_reasons'][dim],
                'T_reason':t['dimension_reasons'][dim],
                'T_literal_evidence':[item for item in t['evidence'] if item['dimension']==dim]}
            assert refs['candidate'][rid]['labels'][dim]==tv
        role=('original_any_dimension_disagreement' if rid in original_disagreements else
              'original_random_complete_agreement' if rid in original_random else
              'v12_designated_source_change' if rid in source_increment else 'v12_random_hidden_agreement')
        row={'original_id':rid,'T_blind_id':t['blind_id'],'text':ctx['llm_inputs'][rid]['text'],
             'source_title':ctx['llm_inputs'][rid]['source_title'],'pages':ctx['llm_inputs'][rid]['pages'],
             'review_selection_private':role,'T_actual_first_material_version':third_audit[rid]['first']['material_version'],
             'T_provenance':third_audit[rid],'dimensions':dimensions,'T_issues':t['issues']}
        ledger.append(row)
        if rid in original_random|added_random and any(item['category']=='AC_agree_T_changed' for item in dimensions.values()):
            all_changed_agreements.append(row)
        t['annotation_provenance']=third_audit[rid]
        t['current_comparable_material_version']='v12'
    current_disagreements={rid for rid in ctx['sample'] if any(refs['A'][rid]['labels'][d]!=refs['C'][rid]['labels'][d] for d in c.DIMS)}
    assert current_disagreements<=set(third)
    candidate_path=REF/'candidate_reference_v12_STAGE.jsonl'
    third_path=REF/'agent_T_first59_current_v12_STAGE.jsonl'
    putjl(candidate_path,[refs['candidate'][rid] for rid in ctx['sample']])
    putjl(third_path,[third[rid] for rid in policy['mixed_original_id_order']])
    bind_path=OUT/'T参照59-v12阶段绑定.json';assert not bind_path.exists();c.write_json(bind_path,manifest)
    result={'status':'pass_current59_reviewed_candidate_v12_stage','stage':manifest['stage'],
        'created_at':datetime.datetime.now().astimezone().isoformat(),'candidate_n':240,'reviewed_n':59,
        'first_v11_n':51,'additional_independent_first_v12_n':8,'actual_reread_n':0,
        'all_reviewed_dimensions_used_n':295,'current_AC_disagreement_case_n':len(current_disagreements),
        'all_current_AC_disagreements_covered':True,'frozen_policy':policy['resolution_policy'],
        'dimension_ledger_counts':counts,'all_reviewed_case_ledger':ledger,
        'all_random_agreement_changes_retained':all_changed_agreements,
        'random_agreement_changed_case_n':len(all_changed_agreements),'reference_QA':audit,
        'bindings':manifest,'bindings_sha256':c.sha(bind_path),'candidate':bd(candidate_path),
        'third_first59':bd(third_path),'additional_completion_qa':bd(tdir/'增补完成清单与QA-v12.json'),
        'script_sha256':c.sha(Path(__file__)),'machine_predictions_or_metrics_used':False,
        'limits':['Current candidate is v12-stage only. Pending v13 source material may require A/C/T reread before final binding.',
                  'All reviewed dimensions use independent T, including random-agreement changes; no majority or machine-performance selection.',
                  'Additional8 are independent first submissions, never relabeled as rereads; original51 provenance/material equality retained.']}
    target=REF/'T59候选v12阶段逐例核验与变更_PRIVATE.json';assert not target.exists();c.write_json(target,result)
    print(json.dumps({'status':result['status'],'reviewed_n':59,'candidate_n':240,
        'current_AC_disagreements':len(current_disagreements),'random_agreement_changed_case_n':len(all_changed_agreements),
        'candidate':str(candidate_path),'QA':str(target)},ensure_ascii=False))


if __name__=='__main__':main()
