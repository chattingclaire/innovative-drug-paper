"""Prepare answer-free replacement-agent packets before any v14 judgments.

Selection depends only on frozen source changes, historical T coverage and A/C
agreement. No machine predictions, scores, or prior T judgments are opened.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import random
import statistical_core_r3 as c
from final_binding_io_r3 import MATERIAL_FIELDS

RUN = c.RUN
ADMIN = RUN/'admin'
SEED = 2026100735
CHANGED = {'RECODE25-03950', 'RECODE25-04388'}


def bd(path):
    return {'path': str(Path(path).resolve()), 'sha256': c.sha(path)}


def put(path, obj):
    assert not path.exists(), f'Preserve existing file: {path}'
    c.write_json(path, obj)


def task_text(coder, kind, packet_name, schema_name, result_name, qa_name):
    role = ('替代独立评审 agent，对来源材料更新后的单元做 source rereview；沿用本方 blind ID 仅为了记录衔接，'
            '不表示你是之前给出首次判断或复读判断的同一 agent。' if kind == 'reread' else
            '新增独立首次评审 agent，本材料中每个单元都是本次新增的 first submission；不得把它们记成复读。')
    return f'''# 五维独立编码任务 v14

你是 {coder} 角色的 AI {role}不是人类评审，不得声称真人验证。只读本目录 {packet_name}、{schema_name}、本任务说明，以及 ../../protocol/完整五维手册-v1.3.md 和 ../../protocol/共用操作说明-v1.4.md。不要读取本方旧材料或结果、admin、reference、statistics、其他评审、规则代码、机器提示或输出；不得打开材料内证书所指的本地路径或外部链接。

逐条阅读当前 text 和全部递归 contexts（包括各版本后缀、后项、父对象、列头、引用条文、边界及对象证书），独立判断 S/E/Ec/I/F。五项可同时为1或全0；逐维写理由，每个1必须有当前单元连续逐字证据，依赖语境时另引真实上下文。只用语境消解当前单元的明确关系，不复制整段维度。保留 I/F 子类、S 质量依据及 issues。实质缺材要写待定；材料完整的语义边界争议须作独立0/1判断，不看其他答案后修改。

程序只能展示、序列化自己的判断，并核验覆盖、schema、逐字引文和SHA，不能用词表或规则生成判断。保存 {result_name}，coder={coder}、material_version=v14，按材料原顺序并绑定当前材料文件真实SHA256。另存 {qa_name}，记录真实时间、AI身份、实际可得的模型信息、读取范围、{'replacement/source-rereview，非原评审本人' if kind == 'reread' else 'replacement/new-first-submission'}、逐字证据位置核验。不得猜测不可得的模型修订号。原记录不覆盖，技术修正也要保留首次提交。

来源标题和文本可能暴露部门身份；不能声称来源身份完全盲法、新文件外验或真人验证。当前任务不给旧判断、其他评审答案、机器结果或分数。
'''


def make_packet(directory, coder, kind, sources, schema_base):
    prefix = '替代来源复读' if kind == 'reread' else '新增首次'
    packet_path = directory/f'{prefix}材料-v14.json'
    schema_path = directory/f'{prefix}结果schema-v14.json'
    task_path = directory/f'{prefix}任务说明-v14.md'
    result_path = directory/f'{prefix}结果-v14.json'
    qa_path = directory/f'{prefix}QA-v14.json'
    put(packet_path, {'material_version': 'v14', 'rows': sources})
    schema = deepcopy(schema_base)
    schema['title'] = f'Five-dimension {coder} v14 {kind} replacement reviewer result'
    schema['properties']['coder'] = {'enum': [coder]}
    schema['properties']['material_version'] = {'const': 'v14'}
    schema['properties']['rows']['items']['properties']['id']['pattern'] = f'^AV3-{coder}-[0-9]{{4}}$'
    put(schema_path, schema)
    assert not task_path.exists()
    task_path.write_text(task_text(coder, kind, packet_path.name, schema_path.name, result_path.name, qa_path.name))
    return {'packet': bd(packet_path), 'schema': bd(schema_path), 'task': bd(task_path),
        'expected_result_path': str(result_path), 'expected_qa_path': str(qa_path),
        'material_version': 'v14', 'reviewer_identity': {'role': coder,
            'review_event': 'replacement_source_rereview' if kind == 'reread' else 'replacement_additional_first_submission',
            'same_agent_as_original_reviewer': False, 'AI_agent': True, 'human_reviewer': False}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-qa', type=Path, required=True)
    parser.add_argument('--source-qa-sha256', required=True)
    parser.add_argument('--input-sha256', required=True)
    args = parser.parse_args()
    assert c.sha(args.source_qa) == args.source_qa_sha256
    assert c.read(args.source_qa)['all_checks_pass'] is True
    input_path = RUN/'effective_blind_inputs_v14.jsonl'
    assert c.sha(input_path) == args.input_sha256
    old = c.jsonl(RUN/'effective_blind_inputs_v13.jsonl')
    new = c.jsonl(input_path)
    assert len(new) == len(old) == 4924 and set(new) == set(old)
    assert all(all(old[rid][k] == new[rid][k] for k in ('id', 'text', 'source_title', 'pages')) for rid in old)
    design_path = ADMIN/'confirmation_sampling_PRIVATE.json'
    design = c.read(design_path)
    sample = {r['original_id']: r for r in design['sample']}
    actual_changed = {rid for rid in sample if any(old[rid][k] != new[rid][k] for k in MATERIAL_FIELDS)}
    assert actual_changed == CHANGED, ('Unexpected reference source-change set', sorted(actual_changed))
    old_policy_path = ADMIN/'third_agent_append_selection_policy_freeze_PRIVATE_v12.json'
    old_policy = c.read(old_policy_path)
    old_tmap_path = ADMIN/'third_agent_mapping_combined_PRIVATE_v12.json'
    old_tmap = c.read(old_tmap_path)
    old_reviewed = set(old_policy['mixed_original_id_order'])
    assert len(old_reviewed) == len(old_tmap) == 59
    assert old_reviewed & CHANGED == {'RECODE25-04388'}
    assert next(x['original_id'] for x in old_tmap if x['blind_id'] == 'AV3-T-0059') == 'RECODE25-04388'
    amap_path = ADMIN/'PRIVATE_mapping.json'
    amap = c.read(amap_path)
    refs = {r: c.jsonl(RUN/f'reference/agent_{r}_final_v12.jsonl') for r in 'AC'}
    assert all(set(rows) == set(sample) for rows in refs.values())
    pools = {g: sorted(rid for rid in sample if sample[rid]['group'] == g and rid not in old_reviewed
        and rid not in CHANGED and all(refs['A'][rid]['labels'][d] == refs['C'][rid]['labels'][d] for d in c.DIMS))
        for g in c.GROUPS}
    rng = random.Random(SEED)
    controls = {g: rng.sample(pools[g], 2) for g in c.GROUPS}
    appended = sorted({'RECODE25-03950'} | {rid for chosen in controls.values() for rid in chosen})
    assert len(appended) == 7 and not set(appended) & old_reviewed
    assert all(rid == 'RECODE25-03950' or old[rid] == new[rid] for rid in appended)
    new_tmap = [{'coder': 'T', 'blind_id': f'AV3-T-{i:04d}', 'original_id': rid,
        'unit_text_sha256': hashlib.sha256(new[rid]['text'].encode()).hexdigest()}
        for i, rid in enumerate(appended, 60)]
    new_trows = [{'id': row['blind_id'], **{k: deepcopy(new[row['original_id']][k]) for k in MATERIAL_FIELDS}}
                 for row in new_tmap]
    rng.shuffle(new_trows)
    map_by_blind = {r['blind_id']: r['original_id'] for r in new_tmap}
    appended_order = [map_by_blind[r['id']] for r in new_trows]
    combined_map_path = ADMIN/'third_agent_mapping_combined_PRIVATE_v14.json'
    # Old records are preserved; new packet/schema/task paths are the only writes.
    protected_paths = [old_policy_path, old_tmap_path, amap_path, design_path,
        *[RUN/f'reference/agent_{coder}_{stage}.jsonl' for coder in 'AC' for stage in ('first_v9', 'final_v11', 'final_v12')],
        *[RUN/f'confirmation/agent-{coder}/结果-{n:02d}.json' for coder in 'AC' for n in range(1, 9)],
        RUN/'confirmation/agent-T/本方结果-v11.json', RUN/'confirmation/agent-T/增补首次结果-v12.json']
    protected = {str(p): c.sha(p) for p in protected_paths}
    ac_packets = {}
    schema_ac = c.read(RUN/'confirmation/结果schema-v12.json')
    for coder in 'AC':
        map_for_coder = {row['original_id']: row['blind_id'] for row in amap if row['coder'] == coder}
        rows = [{'id': map_for_coder[rid], **{k: deepcopy(new[rid][k]) for k in MATERIAL_FIELDS}} for rid in sorted(CHANGED)]
        ac_packets[coder] = make_packet(RUN/f'confirmation/agent-{coder}', coder, 'reread', rows, schema_ac)
    schema_t = c.read(RUN/'confirmation/agent-T/增补结果schema-v12.json')
    t_first = make_packet(RUN/'confirmation/agent-T', 'T', 'first', new_trows, schema_t)
    t_reread = make_packet(RUN/'confirmation/agent-T', 'T', 'reread',
        [{'id': 'AV3-T-0059', **{k: deepcopy(new['RECODE25-04388'][k]) for k in MATERIAL_FIELDS}}], schema_t)
    put(combined_map_path, old_tmap+new_tmap)
    probabilities = [{'original_id': rid, 'group': sample[rid]['group'],
        'selection_role': 'designated_new_source_changed_first' if rid == 'RECODE25-03950' else 'random_unreviewed_complete_agreement',
        'conditional_review_inclusion_probability': 1.0 if rid == 'RECODE25-03950' else 2/len(pools[sample[rid]['group']]),
        'population_analysis_weight': None} for rid in appended]
    policy_path = ADMIN/'third_agent_append_selection_policy_freeze_PRIVATE_v14.json'
    policy = {'status': 'v14_additional_first_and_replacement_rereview_frozen_before_judgment',
        'created_at': datetime.datetime.now().astimezone().isoformat(), 'material_version': 'v14', 'seed': SEED,
        'original_policy_freeze': bd(old_policy_path), 'original_mapping': bd(old_tmap_path),
        'changed_AC_original_ids': sorted(CHANGED), 'existing_T_source_reread_original_ids': ['RECODE25-04388'],
        'source_changed_designated_original_ids': ['RECODE25-03950'],
        'eligible_unreviewed_complete_agreement_pools_by_group': pools, 'random_controls_by_group': controls,
        'new_v14_first_original_ids': appended, 'new_v14_first_packet_original_id_order': appended_order,
        'additional_first_submission_original_ids': old_policy['additional_first_submission_original_ids']+appended,
        'additional_first_submissions_not_rereads': True,
        'mixed_original_id_order': old_policy['mixed_original_id_order']+appended_order, 'reviewed_original_id_n': 66,
        'review_inclusion_probabilities': probabilities,
        'selection_algorithm': 'Sample2 from sorted unreviewed unchanged complete A/C agreement NMPA/NHSA/NHC pools in that order with random.Random(2026100735); add designated03950; sort7 and assignT0060..0066; shuffle7 with same generator.',
        'selection_basis': 'Source-only material changes and frozen A/C agreement/previous T coverage; no machine scores or prediction values enter selection.',
        'preparer_exposure_note': 'Administrative statistics agent previously saw diagnostics; fixed source-designated set and specified seeded selection are replayable, not selected by performance. New reviewers receive answer-free packets only.',
        'machine_outputs_or_metrics_used_to_select': False,
        'resolution_policy': 'third_for_every_reviewed_dimension',
        'policy_detail': 'Every reviewed T dimension replaces A/C, including random agreement changes. Remaining complete agreements retained; no majority or machine-performance selection.',
        'pi_scope': 'Conditional review audit probabilities only; never use as prevalence or policy-population classification weights.',
        'human_validation_completed': False,
        'bindings': {'source_qa': bd(args.source_qa), 'v14_input': bd(input_path), 'combined_mapping': bd(combined_map_path),
            'A_v12': bd(RUN/'reference/agent_A_final_v12.jsonl'), 'C_v12': bd(RUN/'reference/agent_C_final_v12.jsonl'),
            'A_C_replacement_rereads': ac_packets, 'T_additional_first': t_first, 'T_replacement_reread': t_reread},
        'script_sha256': c.sha(Path(__file__))}
    put(policy_path, policy)
    freeze = {'status': 'source_v14_replacement_packets_frozen_before_any_new_judgment',
        'source_qa': bd(args.source_qa), 'old_input': bd(RUN/'effective_blind_inputs_v13.jsonl'), 'new_input': bd(input_path),
        'source_changed_sample_ids': sorted(CHANGED), 'source_changed_existing_T_ids': ['RECODE25-04388'],
        'reference_policy': bd(policy_path), 'mapping': bd(combined_map_path), 'A_C_mapping': bd(amap_path),
        'packets': {'A': ac_packets['A'], 'C': ac_packets['C'], 'T_first': t_first, 'T_reread': t_reread},
        'protected_historical_file_sha256': protected, 'all_historical_files_unchanged': all(c.sha(p) == h for p, h in protected.items()),
        'new_reviewers_are_replacement_agents_not_original_agents': True, 'script_sha256': c.sha(Path(__file__))}
    assert freeze['all_historical_files_unchanged']
    put(ADMIN/'source_rereading_v14_freeze.json', freeze)
    print(json.dumps({'status': 'packets_and_policy_ready_before_judgment', 'freeze': str(ADMIN/'source_rereading_v14_freeze.json'),
        'policy': str(policy_path), 'packets': freeze['packets']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
