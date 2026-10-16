"""One-time V600 freeze assembly. Performs no random selection or statistics."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys, platform, collections
import numpy as np
import sample_paired_holdout as sampler
import paired_holdout_results as bridge

O = Path(__file__).resolve().parent
P = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
D = P / '后验证开发-v24'
V = D / '同输入接入预览-v4-development-24-candidate-17'
tracked = {}

def read(p):
    p = Path(p).resolve(); raw = p.read_bytes(); digest = bridge.sha(raw)
    assert str(p) not in tracked or tracked[str(p)] == digest, 'Changing input'
    tracked[str(p)] = digest
    return raw

def js(p): return json.loads(read(p))

def main():
    manifest = O / 'V600-最终冻结清单.json'
    target = O / 'V600-frozen-inputs'; partial = O / '.V600-freeze.partial'
    assert not any(p.exists() for p in [manifest, target, partial, O / 'V600'])
    handoff = js(D / 'candidate17冻结交接清单.json')
    assert handoff['candidate_sha256'] == 'bd14ffab886876c383a4464151e82878b44e7fd61db189cd70ef0aaab13f4af3'
    for f in handoff['files']: assert bridge.sha(read(f['path'])) == f['sha256']
    for p, h in handoff['source_files_verified'].items(): assert bridge.sha(read(p)) == h
    review = js(O / '候选修订-有限代码手册审查.json')
    assert review['status'] == 'bounded_review_closed_candidate17_not_independent_validation'
    assert review['candidate17_sha256'] == handoff['candidate_sha256']
    paths = {
        'corpus': V / '统一文本复核包-适用范围预览.jsonl', 'adapter': V / '统计输入接入准备.json',
        'classification': P / '部门归属与年度系列-冻结v1.json', 'metadata': P / '55条部门与系列映射-核验中.json',
        'protocol': O / 'frozen-inputs/protocol--五维共用编码协议.md',
        'baseline_dictionary': P / 'policy_coding_v4_development.py', 'baseline_predictions': V / '旧版逐单元预测.json',
        'candidate_dictionary': D / 'policy_coding_v4_development.py', 'candidate_predictions': V / '新版逐单元预测.json',
        'sampler': O / 'sample_paired_holdout.py', 'sample_helpers': O / 'sample_holdout.py',
        'survey_metrics': O / 'survey_metrics.py', 'paired_version_metrics': O / 'paired_version_metrics.py',
        'results_bridge': O / 'paired_holdout_results.py', 'legacy_results_helpers': O / 'holdout_results.py',
        'paired_sensitivity': O / 'paired_sensitivity.py', 'admin_receiver': O / 'receive_paired_submissions.py',
        'reviewer_instructions': O / 'V600-评审任务说明.md', 'protocol_clarifications': O / 'V600-共同执行澄清v1.md',
        'scope_attacher': D / 'attach_object_scope.py', 'scope_registry': D / '对象适用范围登记.json',
        'statistics_adapter': D / 'policy_statistics_adapter.py', 'original_statistics_program': P / 'policy_statistics.py',
        'same_input_builder': D / 'build_same_input_preview.py', 'same_input_handoff': D / 'candidate17冻结交接清单.json',
        'same_input_builder_qa': V / '同输入接入QA.json',
        'candidate_manual_review': O / '候选修订-有限代码手册审查.json', 'candidate_manual_review_report': O / '候选修订-有限代码手册审查.md',
        'sec_finite_status': D / 'SEC有限实现状态-candidate15.json', 'if_finite_status': D / 'IF有限开发需求清单.json',
        'development_scope': D / '开发范围与证据.json', 'development_fixture_sources': D / '沿用开发例句来源.json',
        'boundary_tests': D / 'test_v24_boundaries.py', 'development_tests': D / 'test_policy_coding_v4_development.py',
        'base_exposure_audit': O / '修订版剩余池-暴露预审v3.json', 'additional_exposure_audit': O / '修订版剩余池-新增源文暴露预审v5.json',
        'base_exposure_program': O / 'audit_revision_exposure.py', 'additional_exposure_program': O / 'audit_additional_source_exposure.py',
        'scope_read_register': D / '适用范围查证新增暴露.json', 'renewal_read_register': D / '续约规则源文核验与暴露登记.json',
        'coordinator_read_register': O / '协调者元数据检查-附带原文暴露登记.json',
        'scope_source_review': O / '新增源文暴露与范围证据-独立审查.json', 'renewal_source_review': O / '续约适用范围-独立源文审查.json',
        'protocol_alignment': O / 'V600-协议对齐记录.json', 'protocol_alignment_report': O / 'V600-协议对齐记录.md',
        'sampler_methods_review': O / 'V600抽样发包工具-方法审查.md', 'paired_metrics_methods_review': O / '新轮预备工具-方法审查.md',
        'shared_docs_methods_review': O / 'V600共同说明发包-增量审查.md',
        'bridge_qa': O / 'paired_holdout_results-QA-v4.json', 'sensitivity_qa': O / 'paired_sensitivity-冻结加载QA.json',
        'sensitivity_methods_review': O / 'V600敏感性程序-独立审查.md', 'receiver_qa': O / 'receive_paired_submissions-QA-v1.json',
        'component_exposure_qa': O / '新增源文暴露-组件页连接QA.json', 'allocation_preview': O / 'V600-分层分配预览v2-未抽样.json',
        'original_freeze': O / '最终冻结清单.json', 'original_corpus': O / 'frozen-inputs/corpus--统一文本复核包-语境v2.jsonl',
        'freeze_assembler': Path(__file__),
    }
    for c in ['A', 'C']:
        paths[f'coder_{c}_protocol_ack'] = O / f'V600-preparation/agent-{c}/协议理解确认.json'
        paths[f'coder_{c}_clarification_ack'] = O / f'V600-preparation/agent-{c}/共同澄清确认.json'
    raws = {k: read(p) for k, p in paths.items()}
    old = bridge.unique_rows([json.loads(l) for l in raws['original_corpus'].splitlines()], 'review_id', 'old')
    corpus = [json.loads(l) for l in raws['corpus'].splitlines()]
    new = bridge.unique_rows(corpus, 'review_id', 'new')
    assert set(old) == set(new)
    assert all({k: v for k, v in r.items() if k != 'verified_object_scope'} == old[key] for key, r in new.items())
    analysis = {k: r for k, r in new.items() if r['count_as_analysis_unit'] is True}
    assert (len(corpus), len(analysis)) == (5545, 4924)
    helpers = sampler.load_helpers(raws['sample_helpers'])
    fields = list(helpers['DEFAULT_CONTEXT_FIELDS']) + ['verified_object_scope']
    scopes = collections.Counter()
    for r in corpus:
        for scope in sampler.material_contexts(r, fields, helpers).get('verified_object_scope', []): scopes[scope['kind']] += 1
    adapter = json.loads(raws['adapter']); binding = adapter['binding']
    assert bridge.adapter_digest_json(binding) == adapter['binding_sha256'] == handoff['binding_sha256']
    for k in ['corpus', 'classification', 'metadata']: assert binding['input_sha256'][k] == bridge.sha(raws[k])
    assert bridge.adapter_digest_json({'documents': adapter['documents'], 'units': adapter['units']}) == binding['prepared_payload_sha256']
    assert bridge.adapter_digest_json(adapter['verified_files']) == binding['verified_files_sha256']
    for p, h in adapter['verified_files'].items(): assert bridge.sha(read(p)) == h
    fingerprints = {k: bridge.adapter_digest_json(r) for k, r in analysis.items()}
    assert fingerprints == binding['analysis_unit_fingerprints']
    prepared = bridge.unique_rows(adapter['units'], 'id', 'adapter')
    assert set(prepared) == set(analysis) and all(prepared[k]['record_sha256'] == fingerprints[k] for k in analysis)
    legacy = bridge.source_module(raws['legacy_results_helpers'], 'legacy_results_helpers')
    versions = {'baseline': 'v4-development-23', 'candidate': handoff['candidate_version']}
    for tag, version in versions.items():
        bridge.dictionary_version(raws[tag + '_dictionary'], version, tag)
        predictions = json.loads(raws[tag + '_predictions']); rows = bridge.unique_rows(predictions['rows'], 'id', tag)
        assert set(rows) == set(analysis) and predictions['binding_sha256'] == adapter['binding_sha256']
        assert predictions['coder_sha256'] == bridge.sha(raws[tag + '_dictionary']) and predictions['codebook_sha256'] == bridge.sha(raws['protocol'])
        for k, r in rows.items():
            assert r['version'] == version and r['record_sha256'] == fingerprints[k] and r['unit_text_sha256'] == bridge.sha(analysis[k]['unit_text'].encode())
            _, pending = legacy.machine_labels(r)
            assert pending or r['input_assessment_status'] not in {'context_insufficient', 'text_problem'}
    aliases = {'paired_holdout_results': 'results_bridge'}
    for name in ['bridge_qa', 'sensitivity_qa', 'receiver_qa']:
        for k, h in json.loads(raws[name])['code_sha256'].items(): assert bridge.sha(raws[aliases.get(k, k)]) == h, (name, k)
    assert bridge.sha(raws['additional_exposure_program']) == json.loads(raws['additional_exposure_audit'])['script_sha256']
    for c in ['A', 'C']: assert read(O / f'V600-preparation/agent-{c}/V600-共同执行澄清v1.md') == raws['protocol_clarifications']
    exposure = json.loads(raws['additional_exposure_audit'])
    for p, h in exposure['input_hashes'].items(): assert bridge.sha(read(p)) == h
    eligible = set(exposure['provisional_eligible_ids']); excluded = set(exposure['exclusions'])
    assert len(eligible) == 1531 and len(excluded) == 3393 and not eligible & excluded and eligible | excluded == set(analysis)
    exposure.update(status='final_known_development_exposure_inventory', finalized_at=datetime.now(timezone.utc).isoformat(),
        final_reconciliation={'original_corpus_sha256': bridge.sha(raws['original_corpus']), 'frozen_corpus_sha256': bridge.sha(raws['corpus']),
        'original_ids_and_all_original_fields_unchanged': True, 'new_fields_only': ['verified_object_scope'],
        'candidate_handoff_sha256': bridge.sha(raws['same_input_handoff']), 'no_new_exposure_statement': handoff['no_new_exposure'],
        'scope_source_registrations_included': True, 'eligible_field_name_retained_for_sampler_contract': 'provisional_eligible_ids',
        'scope': 'Final finite known-exposure-excluded frame only; no certificate of all historical unseen material.'})
    raws['exposure'] = bridge.encoded(exposure)
    _, pools, _ = helpers['frame'](corpus, adapter, json.loads(raws['classification']), exposure)
    counts = {h: len(v) for h, v in sorted(pools.items())}; alloc = helpers['allocate'](counts, 600)
    assert {h: {'N_h': n, 'n_h': alloc[h], 'weight': n / alloc[h]} for h, n in counts.items()} == json.loads(raws['allocation_preview'])['strata']
    plan = read(O / 'V600-验证方案-抽样前登记草案.md').decode()
    old_status = '日期：2026-09-26。状态：已选定设计方向，程序和开发尚待闭合；未冻结、未抽样、未产生新参考编码或性能结果。最终冻结清单必须另行保存全部文件实际字节哈希，本草案不是已经执行的预注册证书。'
    assert old_status in plan
    plan = plan.replace(old_status, '日期：2026-09-26。状态：抽样前正式冻结；与本次V600最终冻结清单一起保存。冻结时未抽样、未产生新参考编码或性能结果。所列样本量、设计、定义和分析方案在查看新评审结果前固定。')
    plan = plan.replace('当前在暴露预审v3的1632条基础上', '最终在暴露预审v3的1632条基础上').replace('暂有1531条候选', '有1531条候选').replace('这个数字在开发交接及完整性审查前仍为暂定', '该最终框已完成开发交接及完整性审查').replace('以暂定N=1531', '以冻结N=1531')
    plan = plan.replace('## 尚未执行的步骤', '## 执行状态').replace('以上箭头表示待执行依赖，不表示已经完成。', '冻结时，有限开发、有界代码审查、源文暴露审计、同输入接入和程序准备已完成。抽样、两位首次独立编码、成对统计及据结果修改正文尚未执行。')
    plan += '\n\n冻结版本：v4-development-23 与 v4-development-24-candidate-17；手册 CAL-5D-20260926-v1.3，附共同执行澄清v1。两个版本收到相同新增scope证据，但v23实现不消费该字段；这属于版本实现差异，须报告。当前实质实现局限以封存SEC/IF状态及有界审查记录为准，不宣称通用语义问题全部解决。\n'
    raws['analysis_plan'] = plan.encode()
    raws['final_input_preflight'] = bridge.encoded({'status': 'all_final_input_checks_passed_before_sampling',
        'checked_at': datetime.now(timezone.utc).isoformat(), 'corpus_records': 5545, 'analysis_units': 4924,
        'original_fields_unchanged': True, 'scope_counts': dict(scopes), 'source_file_hashes_verified': len(handoff['source_files_verified']),
        'binding_sha256': adapter['binding_sha256'], 'final_frame_N': 1531, 'excluded_n': 3393, 'sample_budget': 600, 'strata_n': len(counts),
        'paired_predictions_same_records_and_protocol_verified': True, 'all_prediction_record_context_hashes_recomputed': True,
        'program_QA_current_hashes_verified': True, 'bounded_candidate_review_closed': True,
        'sample_drawn': False, 'new_reference_labels_read': False, 'performance_computed': False, 'source_snapshot_hashes': tracked.copy()})
    assert sampler.REQUIRED <= set(raws)
    assert all(bridge.sha(Path(p).read_bytes()) == h for p, h in tracked.items()), 'Input changed before freeze'
    partial.mkdir(); entries = {}
    for k, raw in raws.items():
        suffix = paths[k].suffix if k in paths else '.md' if k == 'analysis_plan' else '.json'
        name = k + suffix
        with (partial / name).open('xb') as f: f.write(raw)
        assert (partial / name).read_bytes() == raw
        entries[k] = {'path': str(target / name), 'sha256': bridge.sha(raw), 'byte_count': len(raw)}
        if k in paths: entries[k]['source_path'] = str(paths[k])
    assert all(bridge.sha(Path(p).read_bytes()) == h for p, h in tracked.items()), 'Input changed during freeze'
    partial.rename(target)
    frozen = {'status': 'frozen_for_paired_reference_label_holdout', 'phase': 'V600', 'created_at': datetime.now(timezone.utc).isoformat(),
        'sampling_seed': 2026092605, 'bootstrap_seed': 2026092606, 'sample_budget': 600, 'population_N': 1531,
        'protocol_version': 'CAL-5D-20260926-v1.3', 'baseline_version': versions['baseline'], 'candidate_version': versions['candidate'],
        'context_fields': fields, 'files': entries, 'runtime': {'python': sys.version, 'numpy': np.__version__, 'platform': platform.platform()},
        'reviewer_contexts': {'A': '/root/v600_expert_a', 'C': '/root/v600_expert_c',
            'identity': 'AI following human content-analysis workflow; not real-human experts', 'mutually_blind_answers': True},
        'analysis_scope': 'Final finite known-exposure-excluded frame only. Original H600/R200 unchanged; no consensus or real-human gold reference.',
        'sampling_attempt_policy': 'One attempt ledger per full freeze hash; no redraw for outcomes, pending labels, or sparse positives.'}
    with manifest.open('xb') as f: f.write(bridge.encoded(frozen))
    assert all(bridge.sha(Path(v['path']).read_bytes()) == v['sha256'] for v in entries.values())
    print(json.dumps({'status': frozen['status'], 'files': len(entries), 'N': 1531, 'n_budget': 600,
        'manifest': str(manifest), 'manifest_sha256': bridge.sha(manifest.read_bytes()), 'sample_drawn': False}, ensure_ascii=False))

if __name__ == '__main__': main()
