"""Bind A/C original+reread judgments; prepare answer-free third-agent material.

No machine outputs are read. Original source and judgment files are untouched.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import datetime
import hashlib
import json
import random
import re
import statistical_core_r3 as c
import reference_bindings_r3 as binding

RUN=Path(__file__).resolve().parents[1]
REF=RUN/'reference'
THIRD=RUN/'confirmation/agent-T'
ADMIN=RUN/'admin'
EXPECTED_INPUT_SHA={
    'effective_blind_inputs_v11.jsonl':'13688745bab15d78b6b8cb7492011a38162ea0d740d5131a1307f65bc66538d3',
    'rule_inputs_shared_v11.jsonl':'7ef9c4031ba77b14cf10e523ab912292defff6ab60c08b0d948cc0dc36673bf2'}


def read(path):return json.loads(Path(path).read_text())
def bd(path):return {'path':str(path),'sha256':c.sha(path)}
def put(path,obj):
    assert not path.exists(),f'No overwrite: {path}'
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def put_jsonl(path,rows):
    assert not path.exists(),f'No overwrite: {path}'
    path.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows))
def strings(value,path):
    if isinstance(value,str):yield path,value
    elif isinstance(value,dict):
        for k,v in value.items():yield from strings(v,path+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from strings(v,f'{path}[{i}]')


def validate_semantics_shape(row,source):
    """Literal-source and annotation-consistency checks, not semantic relabeling."""
    evidence_audit=[]
    for item in row['evidence']:
        fields=[('text',source['text'])] if item['source']=='unit' else list(strings(source['contexts'],'contexts'))
        matches=[{'field':field,'start':text.index(item['quote']),
                  'end':text.index(item['quote'])+len(item['quote'])}
                 for field,text in fields if item['quote'] in text]
        assert matches,(row['id'],'nonverbatim_quote',item)
        evidence_audit.append({**item,'matches':matches})
    for dim in c.DIMS:
        assert row['dimension_reasons'][dim].strip()
        if row['labels'][dim]==1:
            assert any(x['dimension']==dim and x['source']=='unit' for x in row['evidence']),(row['id'],dim,'missing_positive_unit_quote')
    for dim,key in [('I','innovation_subtypes'),('F','fairness_subtypes')]:
        assert bool(row[key])==(row['labels'][dim]==1),(row['id'],dim,'subtype_consistency')
    if row['labels']['S']==0:assert row['safety_quality_basis']=='no_quality_basis'
    if row['labels']['S']=='待定':assert row['safety_quality_basis']=='undetermined'
    if row['labels']['S']==1:assert row['safety_quality_basis']!='undetermined'
    return evidence_audit


def main():
    for name,digest in EXPECTED_INPUT_SHA.items():assert c.sha(RUN/name)==digest
    source_qa=RUN/'audit/independent_source_material_v11_qa.json'
    assert read(source_qa)['all_checks_pass'] is True
    freeze=read(ADMIN/'confirmation_packet_freeze.json')
    mapping_bd=bd(ADMIN/'PRIVATE_mapping.json')
    assert mapping_bd['sha256']==freeze['mapping_sha256']
    mapping=binding.mapping_index(mapping_bd)
    design=read(ADMIN/'confirmation_sampling_PRIVATE.json')
    selected=[r['original_id'] for r in design['sample']]
    groups={r['original_id']:r['group'] for r in design['sample']}
    v9=c.jsonl(RUN/'effective_blind_inputs_v9.jsonl')
    v11=c.jsonl(RUN/'effective_blind_inputs_v11.jsonl')
    assert set(v9)==set(v11) and all(v9[rid]['text']==v11[rid]['text'] for rid in v9)
    changed={rid for rid in selected if v9[rid]!=v11[rid]}
    all_refs={};all_audit={};source_bindings={};literal_audit={};first_hashes={}
    for coder in 'AC':
        directory=RUN/f'confirmation/agent-{coder}'
        qa=read(directory/'补料复读QA-v11.json')
        packets=[];records=[];evidence=[]
        for k in range(1,9):
            result=directory/f'结果-{k:02d}.json';packet=directory/f'材料-{k:02d}.json'
            assert c.sha(packet)==freeze['packets'][str(packet.relative_to(RUN))]
            if coder=='A':assert c.sha(result)==qa['first_submissions_hash_check']['before'][str(result)]
            else:assert c.sha(result)==next(r['sha256'] for r in qa['first_results_preservation'] if r['file']==result.name)
            loaded=binding.load_submission(bd(result),bd(packet),bd(RUN/'confirmation/结果schema.json'),coder,'v9',mapping)
            packets.append(loaded);records.append({'result':bd(result),'packet':bd(packet)})
            for row,source in zip(read(result)['rows'],read(packet)['rows']):
                evidence.append({'blind_id':row['id'],'stage':'first_v9',
                                 'evidence':validate_semantics_shape(row,source)})
            first_hashes[str(result)]=c.sha(result)
        first,first_audit=binding.merge_coder(packets,[],selected,[])
        reread_path=directory/'补料复读结果-v11.json';reread_packet=directory/'补充材料-v11.json'
        if coder=='A':assert c.sha(reread_path)==qa['output_files_sha256'][str(reread_path)]
        else:assert c.sha(reread_path)==qa['result_sha256']
        reread=binding.load_submission(bd(reread_path),bd(reread_packet),bd(RUN/'confirmation/结果schema-v11.json'),coder,'v11',mapping)
        assert set(reread)==changed,(coder,'not_all_changed_material_reread',set(reread),changed)
        for row,source in zip(read(reread_path)['rows'],read(reread_packet)['rows']):
            evidence.append({'blind_id':row['id'],'stage':'reread_v11',
                             'evidence':validate_semantics_shape(row,source)})
        final,audit=binding.merge_coder(packets,[reread],selected,changed)
        # Every unchanged unit's full material must remain identical to v11;
        # every changed unit was symmetrically reread using the exact v11 row.
        for packet in records:
            for source in read(packet['packet']['path'])['rows']:
                rid=mapping[coder,source['id']]['original_id']
                target=v11[rid]
                if rid not in changed:
                    assert all(source[k]==target[k] for k in ('text','source_title','pages','contexts','context_usage'))
        for source in read(reread_packet)['rows']:
            rid=mapping[coder,source['id']]['original_id']
            assert all(source[k]==v11[rid][k] for k in ('text','source_title','pages','contexts','context_usage'))
        if coder=='C':
            correction_path=directory/'技术订正记录.json'
            for correction in read(correction_path):
                assert correction['labels_changed'] is False
                rid=mapping[coder,correction['id']]['original_id']
                assert rid not in changed
                old_labels=deepcopy(final[rid]['labels'])
                final[rid]['dimension_reasons'].update(correction['dimension_reasons'])
                assert final[rid]['labels']==old_labels
                audit[rid]['effective_technical_correction']={**bd(correction_path),
                    'changed_fields':['dimension_reasons.I','dimension_reasons.F'],
                    'labels_changed':False}
        for rid,row in final.items():
            evidence.append({'original_id':rid,'stage':'effective_final_v11',
                             'evidence':validate_semantics_shape(row,v11[rid])})
            row['effective_material_version']='v11'
            row['annotation_provenance']=audit[rid]
        assert len(first)==len(final)==240
        all_refs[coder]={'first':first,'final':final};all_audit[coder]=audit
        literal_audit[coder]=evidence
        source_bindings[coder]={'first':records,'reread_result':bd(reread_path),
            'reread_packet':bd(reread_packet),'reread_qa':bd(directory/'补料复读QA-v11.json')}
    assert binding.require_symmetric_reread(all_audit['A'],all_audit['C'],changed)
    a=all_refs['A']['final'];cc=all_refs['C']['final']
    assert all(c.binary(row['labels'][d]) for rows in (a,cc) for row in rows.values() for d in c.DIMS)
    disagreements=sorted(rid for rid in selected if any(a[rid]['labels'][d]!=cc[rid]['labels'][d] for d in c.DIMS))
    agreement_pool={g:sorted(rid for rid in selected if groups[rid]==g and rid not in disagreements) for g in c.GROUPS}
    rng=random.Random(2026100733)
    agreement_review={g:rng.sample(agreement_pool[g],8) for g in c.GROUPS}
    third_ids=sorted(set(disagreements)|{rid for ids in agreement_review.values() for rid in ids})
    rng.shuffle(third_ids)
    third_rows=[];third_mapping=[]
    for i,rid in enumerate(third_ids,1):
        blind=f'AV3-T-{i:04d}'
        third_rows.append({'id':blind,**{k:deepcopy(v11[rid][k]) for k in ('text','source_title','pages','contexts','context_usage')}})
        third_mapping.append({'coder':'T','blind_id':blind,'original_id':rid,
            'unit_text_sha256':hashlib.sha256(v11[rid]['text'].encode()).hexdigest()})
    schema=deepcopy(read(RUN/'confirmation/结果schema-v11.json'))
    schema['title']='Five-dimension independent coder T result v11'
    schema['properties']['coder']['enum']=['T']
    schema['properties']['rows']['items']['properties']['id']['pattern']='^AV3-T-[0-9]{4}$'
    instructions='''# 五维独立编码任务\n\n执行者为AI agent，本任务不是已完成的真人验证。只读本目录材料-v11.json、结果schema-v11.json，以及../../protocol/完整五维手册-v1.3.md和../../protocol/共用操作说明-v1.4.md。不得读取其他编码员、admin、reference、statistics或机器规则、提示及其输出。\n\n本人逐条读当前text及全部递归contexts，包含所有版本后缀、父对象、列头、后项、引用条文、边界与对象证书；不要因某数组为空而漏读其他字段。按手册独立判断S/E/Ec/I/F，可以多标签或全0。上下文只消解当前单元的明确关系，不能复制其全部维度。每维写理由，每个1必须含当前单元连续逐字引文；依赖语境时另引实际上下文。保留I/F子类、S质量依据与问题记录。程序只能展示/序列化本人判断并核对覆盖、schema、引文与SHA，不能用词表或规则代替逐条语义判读。\n\n材料有实质缺字、对象或条件不足时显式待定并说明，完整材料下的边界争议保留独立0/1判断与理由。不能猜测或读取他人答案后调整。输出本目录结果-v11.json，coder=T，按材料原顺序完整提交，绑定材料实际SHA256，协议CAL-5D-20260926-v1.3、操作v1.4、material_version=v11，遵循结果schema-v11.json。另写完成清单与QA，记录实际时间、身份、模型修订可得性及读取范围。原始提交保留，技术订正另存。\n\n源标题或措辞可能识别部门，同源相邻材料可能有历史接触，不能声称来源身份完全盲法、新文件外验或真人实施。不要打开材料证书中的外部文件或链接。\n'''
    REF.mkdir(exist_ok=True);THIRD.mkdir(exist_ok=True)
    for coder in 'AC':
        put_jsonl(REF/f'agent_{coder}_first_v9.jsonl',[all_refs[coder]['first'][rid] for rid in selected])
        put_jsonl(REF/f'agent_{coder}_final_v11.jsonl',[all_refs[coder]['final'][rid] for rid in selected])
    packet_path=THIRD/'材料-v11.json';put(packet_path,{'material_version':'v11','rows':third_rows})
    put(THIRD/'结果schema-v11.json',schema)
    task_path=THIRD/'任务说明.md';assert not task_path.exists();task_path.write_text(instructions)
    mapping_path=ADMIN/'third_agent_mapping_PRIVATE.json';put(mapping_path,third_mapping)
    third_freeze={'created_at':datetime.datetime.now().astimezone().isoformat(),'seed':2026100733,
        'selection_algorithm':'Within NMPA/NHSA/NHC in that order, sample8 from sorted complete A/C agreement IDs using one random.Random; then sort all selected IDs and shuffle with the same generator.',
        'disagreement_original_ids':disagreements,'agreement_pool_original_ids':agreement_pool,
        'agreement_review_original_ids':agreement_review,'mixed_original_id_order':third_ids,
        'n_disagreement':len(disagreements),'n_agreement_review':24,'n_total':len(third_ids),
        'resolution_policy':'third_for_every_reviewed_dimension',
        'policy_detail':'All independently reviewed T dimensions replace A/C on every reviewed case, including random agreement reviews. Remaining A/C agreeing values are retained. No majority vote or machine-score selection.',
        'human_validation_completed':False,'machine_predictions_read':False,
        'bindings':{'packet':bd(packet_path),'schema':bd(THIRD/'结果schema-v11.json'),
            'task':bd(task_path),'mapping':bd(mapping_path),'v11_inputs':bd(RUN/'effective_blind_inputs_v11.jsonl'),
            'A_final':bd(REF/'agent_A_final_v11.jsonl'),'C_final':bd(REF/'agent_C_final_v11.jsonl')},
        'handbook':bd(RUN/'protocol/完整五维手册-v1.3.md'),'operational':bd(RUN/'protocol/共用操作说明-v1.4.md')}
    put(ADMIN/'third_agent_selection_policy_freeze_PRIVATE.json',third_freeze)
    put(REF/'A_C合并与逐字证据QA-v11.json',{'status':'pass','first_submission_preserved':True,
        'source_inputs_sha256':EXPECTED_INPUT_SHA,'source_qa':bd(source_qa),'mapping':mapping_bd,
        'reread_original_ids':sorted(changed),'symmetric_reread':True,'all_final_labels_binary':True,
        'per_coder_first_and_final_n':240,'source_bindings':source_bindings,'provenance_by_coder':all_audit,
        'literal_evidence_audit':literal_audit,'technical_correction_changes_labels':False,
        'machine_predictions_read':False,'first_result_hashes_after':{p:c.sha(p) for p in first_hashes},
        'output_sha256':{str(p.relative_to(RUN)):c.sha(p) for p in REF.glob('agent_*.jsonl')},
        'script_sha256':c.sha(Path(__file__))})
    assert all(c.sha(p)==digest for p,digest in first_hashes.items())
    print(json.dumps({'packet':str(packet_path),'n':len(third_ids),'n_disagreement':len(disagreements),
                      'n_random_agreement':24,'packet_sha256':c.sha(packet_path),'status':'ready'},ensure_ascii=False))


if __name__=='__main__':main()
