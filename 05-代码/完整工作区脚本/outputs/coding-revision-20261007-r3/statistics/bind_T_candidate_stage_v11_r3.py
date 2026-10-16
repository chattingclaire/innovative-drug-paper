"""Explicit v11-stage candidate; preserve every reviewed T dimension, no scoring."""
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
    metadata=RUN.parent/'validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
    tdir=RUN/'confirmation/agent-T'
    assert c.sha(tdir/'本方结果-v11.json')==c.sha(tdir/'结果-v11.json')
    manifest={'stage':'v11_candidate_only_pending_v12_AC_reread','root_final_bindings_confirmed':True,
        'material':{'version':'v11','source_qa':bd(RUN/'audit/independent_source_material_v11_qa.json'),
            'rule_inputs':bd(RUN/'rule_inputs_shared_v11.jsonl'),'llm_inputs':bd(RUN/'effective_blind_inputs_v11.jsonl')},
        'sampling_design':bd(RUN/'admin/confirmation_sampling_PRIVATE.json'),'metadata':bd(metadata),
        'references':{coder:bd(REF/f'agent_{coder}_final_v11.jsonl') for coder in 'AC'},
        'third':{'policy_freeze':bd(RUN/'admin/third_agent_selection_policy_freeze_PRIVATE.json'),
            'mapping':bd(RUN/'admin/third_agent_mapping_PRIVATE.json'),
            'first':{'result':bd(tdir/'本方结果-v11.json'),'packet':bd(tdir/'材料-v11.json'),
                'schema':bd(tdir/'结果schema-v11.json'),'material_version':'v11'},'rereads':[]}}
    ctx=io.context_from_manifest(manifest);refs,audit=io.final_references(manifest,ctx)
    policy=b.bound_json(manifest['third']['policy_freeze']);mapping=b.mapping_index(manifest['third']['mapping'])
    loaded=b.load_submission(**{'result_binding':manifest['third']['first']['result'],
        'packet_binding':manifest['third']['first']['packet'],'schema_binding':manifest['third']['first']['schema'],
        'coder':'T','material_version':'v11','mapping':mapping})
    third,third_audit=b.merge_coder([loaded],[],policy['mixed_original_id_order'],[])
    records=[];changed_agreements=[];counts={d:{'AC_agree_T_same':0,'AC_agree_T_changed':0,
        'AC_disagree_T_matches_A':0,'AC_disagree_T_matches_C':0} for d in c.DIMS}
    for rid in policy['mixed_original_id_order']:
        a=refs['A'][rid];cc=refs['C'][rid];t=third[rid]
        dimension_ledger={}
        for dim in c.DIMS:
            av,cv,tv=a['labels'][dim],cc['labels'][dim],t['labels'][dim]
            category=('AC_agree_T_same' if av==cv==tv else 'AC_agree_T_changed' if av==cv else
                      'AC_disagree_T_matches_A' if tv==av else 'AC_disagree_T_matches_C')
            counts[dim][category]+=1
            dimension_ledger[dim]={'A':av,'C':cv,'T':tv,'category':category,
                'effective_candidate_value':refs['candidate'][rid]['labels'][dim],
                'A_reason':a['dimension_reasons'][dim],'C_reason':cc['dimension_reasons'][dim],
                'T_reason':t['dimension_reasons'][dim],
                'T_literal_evidence':[e for e in t['evidence'] if e['dimension']==dim]}
            assert refs['candidate'][rid]['labels'][dim]==tv
        record={'original_id':rid,'T_blind_id':t['blind_id'],'text':ctx['llm_inputs'][rid]['text'],
            'source_title':ctx['llm_inputs'][rid]['source_title'],'pages':ctx['llm_inputs'][rid]['pages'],
            'review_selection_private':('any_dimension_AC_disagreement' if rid in policy['disagreement_original_ids']
                                        else 'random_complete_agreement_review'),
            'dimensions':dimension_ledger,'T_issues':t['issues'],
            'T_subtypes':{'I':t['innovation_subtypes'],'F':t['fairness_subtypes'],
                          'S_quality_basis':t['safety_quality_basis']}}
        records.append(record)
        if record['review_selection_private']=='random_complete_agreement_review' and any(
            item['category']=='AC_agree_T_changed' for item in dimension_ledger.values()):changed_agreements.append(record)
    selected=list(ctx['sample'])
    putjl(REF/'agent_T_first_v11.jsonl',[third[rid] for rid in policy['mixed_original_id_order']])
    putjl(REF/'candidate_reference_v11_STAGE.jsonl',[refs['candidate'][rid] for rid in selected])
    bindpath=OUT/'T参照v11阶段绑定.json';assert not bindpath.exists();c.write_json(bindpath,manifest)
    result={'stage':manifest['stage'],'created_at':datetime.datetime.now().astimezone().isoformat(),
        'status':'pass_v11_stage_candidate_binding','frozen_resolution_policy':policy['resolution_policy'],
        'T_reviewed_n':51,'all_reviewed_dimensions_used_n':255,'candidate_n':240,
        'random_agreement_review_n':24,'random_agreement_case_changed_by_T_n':len(changed_agreements),
        'dimension_ledger_counts':counts,'reviewed_case_ledger':records,
        'random_agreement_changes_all_retained':changed_agreements,
        'material_qa':audit,'bindings':manifest,'binding_manifest_sha256':c.sha(bindpath),
        'candidate_sha256':c.sha(REF/'candidate_reference_v11_STAGE.jsonl'),
        'T_first_sha256':c.sha(REF/'agent_T_first_v11.jsonl'),
        'T_completion_qa':bd(tdir/'完成清单与QA-v11.json'),'script_sha256':c.sha(Path(__file__)),
        'machine_outputs_or_accuracy_read':False,
        'limits':['This is a v11-stage AI-agent candidate, pending A/C reread of changed v12 material.',
                  'All reviewed T values retained, including changes to random A/C agreements; no majority vote or metric-based reference selection.',
                  'The ledger documents differing judgments and actual reasons; it does not declare T semantic truth or human validation.']}
    qa_path=REF/'T候选v11阶段逐例分歧与随机一致变更_PRIVATE.json';assert not qa_path.exists();c.write_json(qa_path,result)
    print(json.dumps({'status':result['status'],'candidate_n':240,'T_n':51,
                      'random_agreement_case_changed_by_T_n':len(changed_agreements),
                      'candidate':str(REF/'candidate_reference_v11_STAGE.jsonl'),'qa':str(qa_path)},ensure_ascii=False))


if __name__=='__main__':main()
