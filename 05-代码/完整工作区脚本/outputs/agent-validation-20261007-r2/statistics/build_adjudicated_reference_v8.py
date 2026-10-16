"""Derive a third-agent candidate without overwriting independent A/C submissions."""
import datetime
from statistical_core import *
from current_material_context import load_current_context

def strings(value):
    if isinstance(value,str):return [value]
    if isinstance(value,list):return [s for item in value for s in strings(item)]
    if isinstance(value,dict):return [s for item in value.values() for s in strings(item)]
    return []

def main():
    ctx=load_current_context();a=jsonl(RUN/'reference/agent_A_final_v8.jsonl');c=jsonl(RUN/'reference/agent_C_final_v8.jsonl')
    mapping_path=RUN/'admin/adjudication_mapping_PRIVATE.json';mapping={r['blind_id']:r for r in read(mapping_path)}
    assert len(mapping)==43 and Counter(r['selection'] for r in mapping.values())==Counter({'disagreement':19,'random_agreement_audit':24})
    paths=ctx['source_paths']+[RUN/'reference/agent_A_final_v8.jsonl',RUN/'reference/agent_C_final_v8.jsonl',mapping_path,Path(__file__)]
    selected={}
    for i in range(1,4):
        result_path=RUN/f'adjudication/结果-{i:02d}.json';packet_path=RUN/f'adjudication/材料-{i:02d}.json'
        assert result_path.exists(),f'All43 actual adjudication candidates not yet complete: {result_path}'
        result=read(result_path);assert result['reviewer']=='independent_AI_adjudicator' and result['input_packet_sha256']==sha(packet_path)
        paths.extend([result_path,packet_path])
        for row in result['rows']:
            assert row['id'] in mapping and row['id'] not in selected
            assert set(row['labels'])==set(DIMS) and all(binary(row['labels'][d]) for d in DIMS)
            rid=mapping[row['id']]['original_id'];unit=ctx['llm_inputs'][rid]
            context=strings(unit['contexts'])
            for evidence in row['evidence']:
                assert evidence['dimension'] in DIMS and row['labels'][evidence['dimension']]==1
                corpus=[unit['text']] if evidence['source']=='unit' else context
                assert evidence['quote'] and any(evidence['quote'] in text for text in corpus),(rid,evidence)
            selected[row['id']]=row
    assert set(selected)==set(mapping)
    before={str(path):sha(path) for path in paths};by_original={mapping[k]['original_id']:row for k,row in selected.items()}
    disagreements={rid for rid in a if a[rid]['labels']!=c[rid]['labels']}
    assert disagreements=={r['original_id'] for r in mapping.values() if r['selection']=='disagreement'}
    newmap_path=RUN/'admin/adjudication_v8_mapping_PRIVATE.json';newmap={r['blind_id']:r for r in read(newmap_path)}
    newresult_path=RUN/'adjudication-v8/结果-01.json';newpacket_path=RUN/'adjudication-v8/独立源复读材料.json'
    nr=read(newresult_path);assert nr['reviewer']=='independent_AI_adjudicator' and nr['input_packet_sha256']==sha(newpacket_path)
    assert len(newmap)==len(nr['rows'])==4 and {newmap[r['id']]['original_id'] for r in nr['rows']}==set(ctx['final_source_reread_sample_ids'])
    for row in nr['rows']:
        rid=newmap[row['id']]['original_id'];unit=ctx['llm_inputs'][rid]
        assert set(row['labels'])==set(DIMS) and all(binary(row['labels'][d]) for d in DIMS)
        for evidence in row['evidence']:
            corpus=[unit['text']] if evidence['source']=='unit' else strings(unit['contexts'])
            assert row['labels'][evidence['dimension']]==1 and evidence['quote'] and any(evidence['quote'] in text for text in corpus),(rid,evidence)
        by_original[rid]=row
    assert len(by_original)==46
    paths.extend([newmap_path,newresult_path,newpacket_path])
    before.update({str(path):sha(path) for path in (newmap_path,newresult_path,newpacket_path)})
    final=[];audit_changes=[];issues=[]
    for rid in ctx['sample']:
        if rid in by_original:
            r=by_original[rid];labels=r['labels'];origin='third_expert_AI_adjudication_candidate'
            if rid not in disagreements and labels!=a[rid]['labels']:
                audit_changes.append({'id':rid,'original_A_C_labels':a[rid]['labels'],'adjudication_candidate_labels':labels})
            if r.get('issues'):issues.append({'id':rid,'issues':r['issues']})
        else:
            assert a[rid]['labels']==c[rid]['labels'];labels=a[rid]['labels'];origin='independent_A_C_consensus_not_third_agent_audited'
        final.append({'id':rid,'labels':labels,'reference_origin':origin,'human_ground_truth':False,'adjudication_record':by_original.get(rid)})
    published_path=RUN/'reference/adjudicated_candidate_reference_v8.jsonl';binding_path=RUN/'reference/training_guide_binding_v8.json'
    published=jsonl(published_path);binding=read(binding_path)
    assert set(published)==set(ctx['sample']) and binding['reference_sha256']==sha(published_path)
    assert all(published[r['id']]['labels']==r['labels'] for r in final)
    assert binding['human_validation_completed'] is False
    before.update({str(published_path):sha(published_path),str(binding_path):sha(binding_path)})
    paths.extend([published_path,binding_path])
    target=OUT/'adjudicated_agent_reference_candidate_v8.jsonl'
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in final))
    qa={'status':'completed_AI_agent_candidate_reference_not_human_gold','created_at':datetime.datetime.now().astimezone().isoformat(),'n':300,
        'third_agent_reviewed_n':46,'source_only_v8_independent_reread_n':4,'total_review_executions_n':47,'all_disagreement_units_reviewed_n':19,'random_agreement_audit_n':24,'agreement_audit_overrides':audit_changes,
        'remaining_consensus_n':254,'final_material_version':'v8','unresolved_human_review_flags_retained':issues,'published_candidate_all_1500_labels_independently_matched':True,'A_C_before_adjudication_not_overwritten':True,'human_validation_completed':False,
        'candidate_path':str(target),'candidate_sha256':sha(target),'source_sha256':before}
    write_json(OUT/'裁决候选参照来源核验-v8.json',qa)
    assert before=={str(path):sha(path) for path in paths}
    print(json.dumps({k:v for k,v in qa.items() if k not in ('source_sha256','unresolved_human_review_flags_retained','agreement_audit_overrides')},ensure_ascii=False))

if __name__=='__main__':main()
