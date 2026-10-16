"""One-off metadata/digest scope preparation. Never imports or runs the coder."""
import ast
import collections
import datetime
import hashlib
import json
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INTERFACE = ROOT / '05-validation/formal-freeze-interface-v1-sol'
SAMPLE = ROOT / '05-validation/full800-real-blindpack-sol'
COMPONENT = ROOT / '05-validation/formal-component-freeze-v1-root'
LEDGER = []


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, role, semantic=False):
    p = Path(path).resolve()
    raw = p.read_bytes()
    b = {'path': str(p), 'sha256': digest(raw), 'bytes': len(raw)}
    LEDGER.append(dict(b, read_kind=role, body_or_context_semantic_read=semantic,
                       image_pixel_interpretation=False, model_call=False))
    return raw, b


def metadata(path):
    raw, b = read(path, 'administrative_metadata_or_code_binding')
    return json.loads(raw), b


def normalize(entry):
    return {'path': str(Path(entry.get('absolute_path', entry.get('path'))).resolve()),
            'sha256': entry['sha256'], 'bytes': entry['bytes']}


def verify(entry, role='opaque_file_bytes_identity_only'):
    expected = normalize(entry)
    raw, actual = read(expected['path'], role)
    assert actual == expected, ('exact_binding_mismatch', expected, actual)
    return actual, raw


def write_json(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_jsonl(name, rows):
    with (HERE / name).open('x', encoding='utf8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    assert not (HERE / 'scope.json').exists(), 'preparation already exists; never overwrite'
    prepared_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    component, component_binding = metadata(COMPONENT / 'component-freeze.json')
    component_seal, component_seal_binding = metadata(COMPONENT / 'seal.json')
    assert len(component_seal['members']) == 13
    assert component_binding in [normalize(x) for x in component_seal['members']]
    assert component['component_freeze_complete'] is True
    draw, draw_binding = metadata(SAMPLE / 'coordinator-private/draw-contract.json')
    index, index_binding = metadata(SAMPLE / 'shared-source/source-resource-index.json')
    template, template_binding = metadata(INTERFACE / 'rule-scope.template.json')
    algorithms, algorithms_binding = metadata(INTERFACE / 'algorithm-bindings.json')
    formal_manual, formal_manual_binding = metadata(INTERFACE / 'formal-manual-binding.json')
    old_scope, old_scope_binding = metadata(ROOT / '06-coding/rule-v17-bounded-role-merge-development-sol/source-scope.json')
    sample_seal, sample_seal_binding = metadata(SAMPLE / 'seal.json')
    sample_members = sample_seal.get('members', sample_seal.get('files', sample_seal.get('output_files')))
    assert isinstance(sample_members, list), 'unrecognized actual source seal membership shape'
    sample_member_bindings = [normalize(x) for x in sample_members]
    assert index_binding in sample_member_bindings
    assert normalize(index['common_source_file']) in sample_member_bindings

    expected_N = component['source_and_sample']['sample_N']
    order = draw['selected_record_ids_in_frame_order']
    assert draw['actual_drawn'] is True and draw['sampling_execution'] == 'completed'
    assert expected_N == draw['sample_n'] == index['record_N'] == 800
    assert len(order) == len(set(order)) == expected_N
    assert order == [x['source_id'] for x in index['per_record']]
    order_raw = ('\n'.join(order) + '\n').encode('utf8')
    assert digest(order_raw) == draw['selected_ID_UTF8_LF_sha256']
    identity_by_id = {}
    for stratum in draw['selected_strata']:
        assert len(stratum['selected_ids_sorted']) == stratum['n_h']
        for rid in stratum['selected_ids_sorted']:
            assert rid not in identity_by_id
            identity_by_id[rid] = {k: stratum[k] for k in
                                  ('domain', 'department', 'stratum', 'N_h', 'n_h', 'pi_exact', 'weight_exact')}
    assert set(identity_by_id) == set(order)
    domain_counts = dict(collections.Counter(identity_by_id[r]['domain'] for r in order))
    dept_counts = dict(collections.Counter(identity_by_id[r]['department'] for r in order))
    assert domain_counts == draw['domain_sample_n'] == component['source_and_sample']['domain_sample_N']
    assert dept_counts == draw['department_n'] == component['source_and_sample']['department_sample_N']
    assert domain_counts == {'remaining': 600, 'exposed': 200}
    assert draw['sampling_seed'] == component['source_and_sample']['seed'] == 20261010

    materials = {}
    def include(binding):
        b = normalize(binding)
        previous = materials.setdefault(b['path'], b)
        assert previous == b, 'conflicting material identity'
        return b

    source_packet, source_raw = verify(index['common_source_file'])
    assert source_raw.count(b'\n') == expected_N and source_raw.endswith(b'\n')
    del source_raw
    include(source_packet)
    manual, _ = verify(component['manual'])
    assert manual == normalize(formal_manual['manual']) == normalize(template['manual'])
    assert formal_manual['manual_version'] == '1.3F'
    include(manual)
    provenance_materials = [component_binding, component_seal_binding, draw_binding,
                            index_binding, sample_seal_binding]
    for b in provenance_materials:
        include(b)
    interface_seal_members = None
    for b in (component['source_and_sample']['actual_pre_draw_freeze'],
              component['source_and_sample']['source_v14_seal'],
              component['component_seals']['manual'],
              component['component_seals']['human_rule_interface']):
        actual, raw = verify(b)
        include(actual)
        if actual['path'] == normalize(component['component_seals']['human_rule_interface'])['path']:
            interface_seal_members = [normalize(x) for x in json.loads(raw)['files']]
    assert draw_binding == normalize(component['source_and_sample']['actual_draw_contract'])
    assert sample_seal_binding == normalize(component['source_and_sample']['preparation_seal'])
    assert algorithms_binding == normalize(template['algorithm_bindings'])

    source_base = Path(old_scope['v12_source_base']).resolve()
    for name in ('source_reading_protocol_v12.py', 'source-reading-protocol-v12.json',
                 'current-source-schema-v12.json'):
        entries = [x for x in old_scope['material_bindings'] if Path(x['path']).name == name]
        assert len(entries) == 1
        actual, _ = verify(entries[0], 'unchanged_protocol_dependency_bytes_identity')
        assert Path(actual['path']).parent == source_base
        include(actual)

    asset_rows = []
    for item in index['deduplicated_files']:
        candidates = [('original_absolute_path', p) for p in item['original_absolute_paths']]
        candidates += [('prepared_same_SHA_copy', item['prepared_absolute_path'])]
        for role, p in candidates:
            b, _ = verify({'path': p, 'sha256': item['sha256'], 'bytes': item['bytes']})
            include(b)
            asset_rows.append(dict(b, binding_role=role, resource_kinds=item['resource_kinds'],
                                   original_source_ids=item['source_ids'],
                                   source_content_or_pixel_read_claimed=False))
    assert not any('/04-calibration/' in p or Path(p).name == 'reference.jsonl' for p in materials)
    assert len(index['deduplicated_files']) == 133

    expected_modules = ['source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions']
    assert [x['module'] for x in algorithms['modules']] == expected_modules
    code_bindings = []
    code_syntax = []
    for name in ('rule_driver.py', 'interface_common.py'):
        raw, b = read(INTERFACE / name, 'actual_driver_code_static_read')
        ast.parse(raw, filename=b['path'])
        code_bindings.append(b)
        code_syntax.append({'path': b['path'], 'syntax_parsed': True, 'executed_or_imported': False})
    for entry in algorithms['modules']:
        b, raw = verify(entry, 'unchanged_algorithm_code_syntax_only')
        ast.parse(raw, filename=b['path'])
        code_bindings.append(dict(b, module=entry['module']))
        code_syntax.append({'path': b['path'], 'syntax_parsed': True, 'executed_or_imported': False})
    code_bindings += [algorithms_binding, formal_manual_binding]
    for b in [template_binding, algorithms_binding, formal_manual_binding] + code_bindings[:2]:
        assert normalize(b) in interface_seal_members, 'driver/interface dependency differs from sealed member'
    run_out = HERE / 'run800-first'
    assert not run_out.exists()

    order_doc = {'version': 'fixed800-original-frame-order-binding-1',
                 'record_N': expected_N, 'draw_contract': draw_binding,
                 'source_resource_index': index_binding,
                 'selected_ID_UTF8_LF_sha256': digest(order_raw),
                 'source_index_order_equals_draw_contract': True,
                 'actual_source_JSONL_record_ids_checked_by_driver_only_after_ROOT_authorizes_run': True,
                 'approved_record_ids': order}
    write_json('record-order.json', order_doc)
    identity_rows = [dict(order_1based=n, id=rid, **identity_by_id[rid],
                          stratum_is_frozen_sampling_metadata_not_candidate_or_reference_label=True)
                     for n, rid in enumerate(order, 1)]
    write_jsonl('administrative-sample-identity.jsonl', identity_rows)
    write_json('asset-bindings.json', {'version': 'exact_original_and_shared_asset_bindings-1',
                                     'source_resource_index': index_binding,
                                     'deduplicated_file_N': len(index['deduplicated_files']),
                                     'original_unique_path_N': len({x['path'] for x in asset_rows if x['binding_role']=='original_absolute_path'}),
                                     'prepared_unique_path_N': len({x['path'] for x in asset_rows if x['binding_role']=='prepared_same_SHA_copy'}),
                                     'bindings': asset_rows,
                                     'file_bytes_identity_is_not_text_or_pixel_read_use': True})
    scope = dict(template)
    scope.update(status='frozen_for_execution', execution_purpose='formal_validation_candidate',
                 output_directory=str(run_out), source_packet=source_packet,
                 source_package_seal=sample_seal_binding, source_version='source-v14 fixed probability800 literal/shared source unchanged',
                 manual=manual, manual_version='1.3F', algorithm_bindings=algorithms_binding,
                 approved_record_ids=order, expected_record_N=expected_N, expected_dimension_N=5*expected_N,
                 max_actual_cohort_inference_runs=1, v12_source_base=str(source_base),
                 complete_bundles_canonical_sha256=source_packet['sha256'],
                 source_manifest_sha256=index_binding['sha256'],
                 material_bindings=[materials[p] for p in sorted(materials)],
                 component_freeze=component_binding, component_freeze_seal=component_seal_binding,
                 actual_draw_contract=draw_binding, source_resource_index=index_binding,
                 algorithm_module_bindings=algorithms['modules'],
                 fixed_original_ID_UTF8_LF_sha256=digest(order_raw),
                 domain_sample_N=domain_counts, department_sample_N=dept_counts,
                 source_context_overlap=component['source_and_sample']['source_context_overlap'],
                 source_context_overlap_identity_source='Inherited exact ROOT component declaration; no new per-record overlap inference',
                 no_reference_input=True, no_gold_input=True, no_scoring=True,
                 no_full4481_recoding=True, private_machine_prediction_only=True,
                 credible_reference_needed_before_comparison_not_before_private_prediction=True,
                 component_false_authorization_fields_are_historical_not_reused_as_release=True,
                 no_statistics_or_acceptance=True, no_human_distribution=True,
                 source_assets_available_not_actual_read_use=True, actual_image_pixel_reads_expected=0,
                 current_scope_preparation_only=True, execution_authorization='pending_ROOT_explicit_scope_SHA_input_order_confirmation',
                 scope_status_means_binding_ready_not_permission_to_run=True,
                 provider_model_id=None, provider_reasoning_setting=None,
                 requested_preparation_model='GPT-6.1 Sol', requested_preparation_reasoning_effort='ultra',
                 fixed_rule_program_makes_model_calls=False)
    write_json('scope.json', scope)
    scope_raw, scope_binding = read(HERE / 'scope.json', 'new_scope_administrative_binding')
    command = [sys.executable, str(INTERFACE / 'rule_driver.py'), '--scope', scope_binding['path'],
               '--scope-sha256', scope_binding['sha256'], '--input', source_packet['path'],
               '--input-sha256', source_packet['sha256'], '--out', str(run_out)]
    write_json('execution-command.json', {'argv': command, 'shell_display': shlex.join(command),
                                        'executed': False, 'ROOT_confirmation_required': True,
                                        'scope': scope_binding, 'input': source_packet,
                                        'max_actual_cohort_inference_runs': 1})
    preflight = {'version': 'frozen-rule800-metadata-only-preflight-1', 'prepared_at_utc': prepared_at,
                 'status': 'metadata_identity_static_code_preflight_passed_waiting_ROOT_execution_confirmation',
                 'component_seal_member_N': 13, 'repeated_all_component_or_full800_seal_member_QA': False,
                 'scope': scope_binding, 'source_packet': source_packet, 'source_resource_index': index_binding,
                 'record_N': expected_N, 'dimension_N': 5*expected_N,
                 'actual_draw_order_equals_source_index_order': True, 'unique_ID_N': len(set(order)),
                 'opaque_input_UTF8_LF_row_N': expected_N, 'source_body_JSONL_not_parsed_or_interpreted_in_preparation': True,
                 'actual_source_JSONL_ID_order_checked_at_authorized_run': 'pending',
                 'domain_sample_N': domain_counts, 'department_sample_N': dept_counts,
                 'source_context_overlap': scope['source_context_overlap'],
                 'material_binding_N': len(materials), 'asset_file_SHA_N': len(index['deduplicated_files']),
                 'original_asset_path_N': 138, 'prepared_asset_path_N': 133,
                 'original_asset_paths_missing_or_forbidden': [], 'asset_hash_or_byte_mismatch': [],
                 'driver_static_contract_reviewed': ['scope/order/count', 'manual1.3F exact component',
                    'algorithm five fixed modules', 'finite source facade', 'literal leaf original path integrity',
                    'original receipt resolver', 'no reference/calibration read', 'first-output no overwrite',
                    'failures and legal null preserved; no retry'],
                 'code_syntax_only': code_syntax, 'code_bindings': code_bindings,
                 'new_run_output_exists': False, 'actual_cohort_inference_runs': 0, 'model_calls': 0,
                 'old77_runs': 0, 'sample_redraws': 0, 'new_labels': 0, 'reference_reads': 0,
                 'actual_image_pixel_reads': 0, 'formal_or_human_validation_complete': False,
                 'preflight_does_not_claim_runtime_receipt_or_dimension_success': True,
                 'remaining_blocker': 'ROOT has not yet confirmed actual scope SHA / input / original order for the sole execution',
                 'technical_blocker_detected_in_metadata_or_static_preflight': None}
    write_json('preflight.json', preflight)
    write_json('provenance.json', {'version': 'AI-rule800-candidate-preparation-provenance-1',
               'identity': 'AI /root/pilot01_a_sol', 'requested_model': 'GPT-6.1 Sol',
               'requested_reasoning_effort': 'ultra', 'actual_provider_model_id': None,
               'actual_provider_reasoning_setting': None, 'provider_identity_status': 'not independently observable',
               'history': 'Previously participated in exposed AI development coding, source recovery, workflow preparation, and rule-v15/v16/v17 development. Not a new blind human coder.',
               'current_role': 'metadata-only preparation for frozen rule candidate800; no reference/gold/score reading in this task',
               'component_freeze': component_binding, 'component_freeze_seal': component_seal_binding,
               'actual_draw_contract': draw_binding, 'source_package_seal': sample_seal_binding,
               'algorithm_manifest': algorithms_binding, 'algorithm_modules': algorithms['modules'],
               'manual': manual, 'old_scope_read_only': old_scope_binding, 'template_read_only': template_binding,
               'original_readers_and_blindpack_files_unchanged': True,
               'human_A_B_machine_candidate_access': 'No distribution; these output files remain coordinator/machine-only. Existing blindpack files untouched.',
               'current_execution_authorization': 'Preparation only; ROOT explicit scope SHA/input/order confirmation is still required',
               'source_manifest_field_binding_explanation': 'source_manifest_sha256 is this full800 source-resource-index SHA; the finite facade uses it as material identity, not the old77 manifest.',
               'complete_bundles_canonical_sha256_binding_explanation': 'Retained legacy field name stores the exact shared800 source JSONL file SHA; this is a file binding, not a new canonicalization.',
               'statistical_status': 'Fixed probability sample drawn once, with600 remaining and200 exposed;800 is not wholly unseen. No score, reference, population CI, human or overall validation produced.',
               'source_context_overlap': scope['source_context_overlap'],
               'no_new_individual_overlap_or_exposure_claim': True,
               'historical_native_attempts': '13 terminal contexts unchanged; no reset/retry/model/chat',
               'actual_cohort_inference_runs': 0, 'model_calls': 0, 'formal_acceptance_or_human_execution': False})
    write_json('input-read-ledger.json', {'read_events': LEDGER,
                                       'actual_source_body_or_CTX_semantic_read_N': 0,
                                       'actual_image_pixel_read_N': 0,
                                       'asset_hashing_is_not_reader_or_runtime_use_receipt': True})
    report = f'''已准备冻结规则800候选的显式scope，尚未执行推断。只读既有driver/template/v17 scope、ROOT13成员组件freeze及已封存行政索引；原算法、手册、source、packet、空表均未修改。\n\nscope SHA256：{scope_binding['sha256']}（{scope_binding['bytes']} B）。输入原共享800裸bundle JSONL SHA256：{source_packet['sha256']}（{source_packet['bytes']} B）。顺序严格取原draw contract的frame order，800个唯一ID；ID UTF8 LF串SHA256：{digest(order_raw)}。source index顺序相同；实际JSONL内部ID/order由唯一获授权运行的driver核对，准备阶段没有解析正文。\n\n保留600 remaining与200 exposed，三部门384/340/76和原41层身份。原ROOT已知重叠声明为registered remaining同主源43条、selected remaining来源/语境重叠16条；未新增逐例重叠推断，不称800全未曝光。行政domain/stratum/pi/weight独立存档，不输入任何参照标签。\n\n原五模块逐SHA/bytes和语法核查通过；1.3F实际SHA为{manual['sha256']}。来源索引133个不同SHA文件的138个原始绝对路径、133个shared字节副本实际可达且身份匹配。scope material bindings共{len(materials)}个路径，按旧resolver绑定原路径并保留shared副本。未将字节hash称为读图、正文判读、source use或运行收据。\n\n真正入口仍是封存rule_driver.py的--scope/--scope-sha256/--input/--input-sha256/--out；argv另存execution-command.json。新输出仅run800-first，该目录尚不存在。scope的frozen_for_execution是现有driver的绑定状态值；本任务执行授权明确仍pending，必须等ROOT核准这个scope SHA、输入和原顺序后，才允许唯一一次800运行。未检测到当前metadata/static code接点的实际阻塞；不预称运行/维度/收据成功。\n\n实际推断0、model calls0、重抽0、旧77运行0、新label0、参照/score读取0。若唯一执行出现全局或逐维技术失败、null或空状态，保存真实首件与尝试，不补0、不重试。本批是规则候选先行预测，不形成参照、人工验收分数或4481全库结果。真人身份及独立首判仍pending。\n\n准备者为AI，已有曝光开发与源恢复/规则开发历史。请求配置GPT-6.1 Sol ultra；实际provider model/reasoning没有独立可核遥测，均保持unknown。\n'''
    with (HERE / 'report.md').open('x', encoding='utf8') as stream:
        stream.write(report)
    members = []
    for p in sorted(HERE.iterdir()):
        if p.is_file():
            raw = p.read_bytes()
            members.append({'path': str(p), 'sha256': digest(raw), 'bytes': len(raw)})
    write_json('preparation-seal.json', {'version': 'frozen-rule800-scope-preparation-seal-1',
               'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'members': members, 'scope': scope_binding, 'preparation_only': True,
               'ROOT_execution_confirmation_pending': True, 'actual_cohort_inference_runs': 0,
               'model_calls': 0, 'formal_or_human_validation_complete': False})
    print(json.dumps({'preparation_status': preflight['status'], 'scope': scope_binding,
                      'material_binding_N': len(materials), 'record_N': expected_N,
                      'domain_sample_N': domain_counts, 'actual_cohort_inference_runs': 0,
                      'model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
