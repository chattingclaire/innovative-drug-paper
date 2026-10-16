"""Preserve A/C history and prepare eight independent T first judgments on v12."""
from pathlib import Path
from copy import deepcopy
import datetime
import hashlib
import json
import random
import statistical_core_r3 as c
import reference_bindings_r3 as b
from prepare_final_reference_and_third_r3 import validate_semantics_shape
from final_binding_io_r3 import MATERIAL_FIELDS,validate_effective_reference

RUN=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
REF=RUN/'reference'
ADMIN=RUN/'admin'
TDIR=RUN/'confirmation/agent-T'


def bd(path):return {'path':str(path),'sha256':c.sha(path)}
def put(path,data):assert not path.exists();c.write_json(path,data)
def putjl(path,rows):
    assert not path.exists();path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))


def main():
    reread_freeze=c.read(ADMIN/'source_rereading_v12_freeze.json')
    assert c.sha(RUN/'effective_blind_inputs_v11.jsonl')==reread_freeze['old_inputs_sha256']
    assert c.sha(RUN/'effective_blind_inputs_v12.jsonl')==reread_freeze['new_inputs_sha256']
    assert c.read(RUN/'audit/independent_source_material_v12_qa.json')['all_checks_pass'] is True
    v11=c.jsonl(RUN/'effective_blind_inputs_v11.jsonl');v12=c.jsonl(RUN/'effective_blind_inputs_v12.jsonl')
    design=c.read(ADMIN/'confirmation_sampling_PRIVATE.json');sample={r['original_id']:r for r in design['sample']}
    selected=list(sample);mapping=b.mapping_index(bd(ADMIN/'PRIVATE_mapping.json'))
    changed={rid for rid in selected if any(v11[rid][k]!=v12[rid][k] for k in MATERIAL_FIELDS)}
    assert changed=={'RECODE25-01432','RECODE25-04388'}
    protected={str(path):c.sha(path) for path in [
        *[RUN/f'confirmation/agent-{coder}/结果-{i:02d}.json' for coder in 'AC' for i in range(1,9)],
        *[REF/f'agent_{coder}_{stage}.jsonl' for coder in 'AC' for stage in ('first_v9','final_v11')],
        ADMIN/'third_agent_mapping_PRIVATE.json',ADMIN/'third_agent_selection_policy_freeze_PRIVATE.json',
        TDIR/'材料-v11.json',TDIR/'本方结果-v11.json',TDIR/'结果-v11.json',
        RUN/'confirmation/agent-C/技术订正记录.json']}
    final_refs={};audit={};quote_audit={};new_bindings={}
    for coder in 'AC':
        directory=RUN/f'confirmation/agent-{coder}';qa=c.read(directory/'补料复读QA-v12.json')
        packet=directory/'补充材料-v12.json';result=directory/'补料复读结果-v12.json'
        assert bd(packet)=={k:v for k,v in reread_freeze['packets'][coder].items() if k in ('path','sha256')}
        assert c.sha(RUN/'confirmation/结果schema-v12.json')==reread_freeze['schema_sha256']
        expected=qa['output_files_sha256'][str(result)] if coder=='A' else qa['result_sha256']
        assert c.sha(result)==expected
        loaded=b.load_submission(bd(result),bd(packet),bd(RUN/'confirmation/结果schema-v12.json'),coder,'v12',mapping)
        assert set(loaded)==changed
        prior=c.jsonl(REF/f'agent_{coder}_final_v11.jsonl');first=c.jsonl(REF/f'agent_{coder}_first_v9.jsonl')
        final=deepcopy(prior);per_coder={};quotes=[]
        for rid,item in loaded.items():
            source=next(row for row in c.read(packet)['rows'] if row['id']==item['row']['id'])
            assert all(source[k]==v12[rid][k] for k in MATERIAL_FIELDS)
            quotes.append({'original_id':rid,'evidence':validate_semantics_shape(item['row'],source)})
            old_audit=deepcopy(prior[rid]['annotation_provenance'])
            history=old_audit.get('effective_history',[deepcopy(old_audit['effective'])])
            history.append(deepcopy(item['provenance']))
            merged_audit={**old_audit,'v11_effective':deepcopy(old_audit['effective']),
                'effective':deepcopy(item['provenance']),'effective_history':history,
                'reread_applied':True,'v12_source_only_reread_applied':True,
                'v11_to_v12_label_change_dimensions':[d for d in c.DIMS if prior[rid]['labels'][d]!=item['row']['labels'][d]],
                'label_change_dimensions':[d for d in c.DIMS if first[rid]['labels'][d]!=item['row']['labels'][d]]}
            new=deepcopy(item['row']);new['blind_id']=new['id'];new['id']=rid
            new['annotation_provenance']=merged_audit;new['effective_material_version']='v12'
            final[rid]=new;per_coder[rid]=merged_audit
        for row in final.values():row['effective_material_version']='v12'
        checked=validate_effective_reference(final,{'sample':sample,'llm_inputs':v12})
        assert len(checked)==240
        final_refs[coder]=final;audit[coder]=per_coder;quote_audit[coder]=quotes
        new_bindings[coder]={'prior_v11':bd(REF/f'agent_{coder}_final_v11.jsonl'),
            'reread_result':bd(result),'reread_packet':bd(packet),'reread_qa':bd(directory/'补料复读QA-v12.json')}
    old_policy=c.read(ADMIN/'third_agent_selection_policy_freeze_PRIVATE.json')
    old_mapping=c.read(ADMIN/'third_agent_mapping_PRIVATE.json')
    old_reviewed=set(old_policy['mixed_original_id_order'])
    assert len(old_reviewed)==51 and not old_reviewed&changed
    old_packet=c.read(TDIR/'材料-v11.json');old_map={row['blind_id']:row for row in old_mapping}
    assert all(all(row[k]==v12[old_map[row['id']]['original_id']][k] for k in MATERIAL_FIELDS) for row in old_packet['rows'])
    a=final_refs['A'];cc=final_refs['C']
    disagreements={rid for rid in selected if any(a[rid]['labels'][d]!=cc[rid]['labels'][d] for d in c.DIMS)}
    assert disagreements-old_reviewed<=changed
    pools={group:sorted(rid for rid in selected if sample[rid]['group']==group and rid not in old_reviewed
                         and rid not in changed and all(a[rid]['labels'][d]==cc[rid]['labels'][d] for d in c.DIMS))
           for group in c.GROUPS}
    rng=random.Random(2026100734)
    controls={group:rng.sample(pools[group],2) for group in c.GROUPS}
    appended=sorted(changed|{rid for values in controls.values() for rid in values})
    assert len(appended)==8 and not set(appended)&old_reviewed
    new_mapping=[];rows=[]
    for number,rid in enumerate(appended,52):
        blind=f'AV3-T-{number:04d}'
        new_mapping.append({'coder':'T','blind_id':blind,'original_id':rid,
            'unit_text_sha256':hashlib.sha256(v12[rid]['text'].encode()).hexdigest()})
        rows.append({'id':blind,**{key:deepcopy(v12[rid][key]) for key in MATERIAL_FIELDS}})
    rng.shuffle(rows);new_map_by_blind={row['blind_id']:row for row in new_mapping}
    mixed_additional=[new_map_by_blind[row['id']]['original_id'] for row in rows]
    combined_mapping=old_mapping+new_mapping
    additional_packet=TDIR/'增补材料-v12.json';put(additional_packet,{'material_version':'v12','rows':rows})
    schema=deepcopy(c.read(TDIR/'结果schema-v11.json'))
    schema['title']='Five-dimension independent coder T result v12'
    schema['properties']['material_version']['const']='v12'
    put(TDIR/'增补结果schema-v12.json',schema)
    instructions='''# 五维独立编码任务\n\n本次是对本方增补材料-v12.json中每个单元的独立首次判读。只读本目录增补材料-v12.json、增补结果schema-v12.json，以及../../protocol/完整五维手册-v1.3.md和../../protocol/共用操作说明-v1.4.md。不要读取admin、reference、statistics、其他编码员、机器提示或输出，也不要重读本方其他材料或既有结果。\n\n本人逐条阅读当前text及全部递归contexts，含各版本后缀、后项、父对象、列头、引用条文、边界与对象证书，按手册独立判断S/E/Ec/I/F。五项可同时为1或全0；逐维给理由，每个1有当前单元连续逐字证据，依赖语境时另引实际上下文。上下文仅消解当前单元的明确关系，不复制全部维度。保存I/F子类、S质量依据及issues。实质缺材显式待定，完整材料的边界争议保留独立0/1判断，不能查看其他答案后调整。\n\n程序只展示/序列化本人判断并核验覆盖、schema、引文和SHA，不得用词表或规则替代逐条语义判断。输出本目录增补首次结果-v12.json，coder=T、material_version=v12，遵循增补结果schema-v12.json，按材料原顺序，绑定材料实际SHA256。另存增补完成清单与QA-v12.json，记录真实时间、AI身份、模型修订可得性和实际读取范围。保留本次首次文件，后续订正另存；不要打开证书指向的外部路径或链接。\n\n政策标题或措辞可能识别部门，相邻语境可能有历史接触，不能声称来源身份完全盲法、新文件外验或真人验证。\n'''
    task=TDIR/'增补任务说明-v12.md';assert not task.exists();task.write_text(instructions)
    map_path=ADMIN/'third_agent_mapping_combined_PRIVATE_v12.json';put(map_path,combined_mapping)
    review_pi=[]
    for rid in appended:
        group=sample[rid]['group'];fixed=rid in changed
        review_pi.append({'original_id':rid,'selection_role':'designated_changed_material' if fixed else 'random_hidden_agreement_review',
            'group':group,'conditional_review_pool_n':2 if fixed else len(pools[group]),
            'conditional_review_sample_n':2,'conditional_review_inclusion_probability':1.0 if fixed else 2/len(pools[group]),
            'population_analysis_weight':None})
    append_freeze={'created_at':datetime.datetime.now().astimezone().isoformat(),'seed':2026100734,
        'status':'append_first_submission_design_frozen_before_T_judgment','material_version':'v12',
        'original_policy_freeze':bd(ADMIN/'third_agent_selection_policy_freeze_PRIVATE.json'),
        'original_mapping':bd(ADMIN/'third_agent_mapping_PRIVATE.json'),'source_only_increment_freeze':bd(ADMIN/'source_rereading_v12_freeze.json'),
        'source_changed_designated_original_ids':sorted(changed),'new_AC_disagreements_needing_T_original_ids':sorted(disagreements-old_reviewed),
        'eligible_unreviewed_complete_agreement_pools_by_group':pools,'random_controls_by_group':controls,
        'additional_first_submission_original_ids':appended,'additional_packet_original_id_order':mixed_additional,
        'mixed_original_id_order':old_policy['mixed_original_id_order']+mixed_additional,
        'reviewed_original_id_n':59,'original51_materials_exactly_match_v12':True,
        'review_inclusion_probabilities':review_pi,
        'pi_scope':'Conditional review-audit selection probabilities only, given fixed designated source changes and current unreviewed agreement pools; not policy-population sampling probabilities and never used as classification/prevalence weights.',
        'selection_algorithm':'Sample2 from sorted NMPA/NHSA/NHC pools in that order using random.Random2026100734; sort the8 selected original IDs, assignT0052..T0059, then shuffle packet rows with the same generator.',
        'resolution_policy':'third_for_every_reviewed_dimension','additional_first_submissions_not_rereads':True,
        'machine_outputs_or_metrics_used_to_select':False,
        'bindings':{'additional_packet':bd(additional_packet),'additional_schema':bd(TDIR/'增补结果schema-v12.json'),
            'additional_task':bd(task),'combined_mapping':bd(map_path),'v12_input':bd(RUN/'effective_blind_inputs_v12.jsonl')},
        'original51_judgment':bd(TDIR/'本方结果-v11.json')}
    freeze_path=ADMIN/'third_agent_append_selection_policy_freeze_PRIVATE_v12.json';put(freeze_path,append_freeze)
    for coder in 'AC':putjl(REF/f'agent_{coder}_final_v12.jsonl',[final_refs[coder][rid] for rid in selected])
    put(REF/'A_C合并与逐字证据QA-v12.json',{'status':'pass','material_version':'v12','per_coder_n':240,
        'changed_original_ids_symmetrically_reread':sorted(changed),'bindings':new_bindings,
        'annotation_increment_provenance':audit,'literal_quote_audit':quote_audit,
        'all240_effective_material_rows_match_v12':True,'C_reason_only_technical_correction_preserved':True,
        'original_source_and_first_v11_files_unchanged':all(c.sha(p)==digest for p,digest in protected.items()),
        'protected_files_sha256':protected,'all_final_labels_binary':True,
        'output_sha256':{str((REF/f'agent_{coder}_final_v12.jsonl').relative_to(RUN)):c.sha(REF/f'agent_{coder}_final_v12.jsonl') for coder in 'AC'},
        'append_review_freeze':bd(freeze_path),'script_sha256':c.sha(Path(__file__))})
    assert all(c.sha(p)==digest for p,digest in protected.items())
    print(json.dumps({'status':'ready_for_independent_T_additional_first','n':8,'packet':str(additional_packet),
        'packet_sha256':c.sha(additional_packet),'combined_reviewed_n':59,'freeze':str(freeze_path)},ensure_ascii=False))


if __name__=='__main__':main()
