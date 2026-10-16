"""Render the authorized sealed development77 source package; no coding execution."""
import copy
import datetime
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

CODING = Path(__file__).resolve().parent
RUNTIME = CODING / 'protocol-necessary-read-v3'
SOURCE = CODING.parent / '01-review/context-projection-sol/full-frame-preflight/development77-common-v13'
DESTINATION = CODING / 'development77-native-inputs-v3'
sys.path.insert(0, str(RUNTIME))
import packet_builder as pb
import native_records as nr

EXPECTED = {
    RUNTIME / 'delivery-seal.json': 'c0c2090afd60723cbc771667793933da7673b830c0052f6d99de0aa97de4f296',
    SOURCE / 'delivery-seal.json': 'a298e7a6326f19bb2239a2bb845fc3beb2b0c2320f90c72980ef25f23900757a',
    SOURCE / 'common-source-bundles.jsonl': '60350a6cbd71648286c9c347659fff6d30b26caa3fd9d29058da1c265fd6dcc1',
    SOURCE / 'source-resource-index.json': '02ccbc15e8e2cc1a49e0dcb11f2cb61f8f2fb9366011ec0ec22c29ed073d1670',
}
for path, digest in EXPECTED.items():
    pb.require(pb.file_sha(path) == digest, 'authorized sealed input changed: ' + path.name)
runtime_seal = pb.parse((RUNTIME / 'delivery-seal.json').read_bytes())
for item in runtime_seal['files']:
    pb.require(pb.file_sha(item['path']) == item['sha256'], 'sealed v3 runtime member changed')
source_seal = pb.parse((SOURCE / 'delivery-seal.json').read_bytes())
for item in source_seal['output_files']:
    pb.require(pb.file_sha(item['absolute_path']) == item['sha256'], 'sealed development source member changed')
binding = pb.parse((RUNTIME / 'parent-binding.json').read_bytes())
pb.load_owner(binding)  # Seal/schema/profile binding only; does not call lookup.
budget = pb.parse((RUNTIME / 'operational-budget.json').read_bytes())
pb.check_budget(budget)
manual = (RUNTIME / 'manual-v1.3.txt').read_bytes()
pb.require(pb.sha(manual) == 'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f', 'execution manual must be exact v1.3')
output_schema = (RUNTIME / 'output-item.schema.json').read_bytes()
frames = pb.load_frame_bindings(binding)
costs = {row['id']: row for row in pb.parse((RUNTIME / 'frame-render-costs.json').read_bytes())['ordered_records']}
asset_metadata = pb.parse((RUNTIME / 'budget-source-metadata.json').read_bytes())
asset_lookup = asset_metadata['asset_lookup']
source_index = pb.parse((SOURCE / 'source-resource-index.json').read_bytes())
bundles = [pb.parse(line) for line in (SOURCE / 'common-source-bundles.jsonl').read_bytes().splitlines() if line.strip()]
ids = [bundle['source_record']['id'] for bundle in bundles]
pb.require(len(ids) == len(set(ids)) == 77 and ids == source_index['fixed_record_ids_in_input_order'], 'sealed fixed77 order incomplete/changed')
order_lf_sha = pb.sha(('\n'.join(ids) + '\n').encode())
pb.require(order_lf_sha == '096de8c3d1f133e2604799dda43dcd4848f503393581d95112271b4e385f5ed2', 'fixed old41 plus old36 order changed')
packets = []
for bundle, uid in zip(bundles, ids):
    digest = pb.sha(pb.canonical(bundle)); frozen = frames[uid]
    pb.require(digest == frozen['new_bundle_sha256'] and len(pb.canonical(bundle)) == frozen['new_bundle_utf8_bytes'], 'development bundle differs from sealed whole-frame binding')
    pb.require(set(pb.BUNDLE_KEYS) <= set(bundle) and set(bundle) <= set(pb.BUNDLE_KEYS) | {'source_bundle_extension'}, 'complete old ten roots/optional extension required')
    pb.require(bundle['common_source_bundle_version']['version'] == 'v12' and ('source_bundle_extension' in bundle) is frozen['extension_available'], 'original base version/extension identity changed')
    packet = {'packet_version': 'native-full-source-3', 'source_id': uid, 'output_id': 'B-' + uid.split('-')[1],
              'source_bundle_sha256': digest, 'source_bundle': copy.deepcopy(bundle),
              'verified_asset_files': [copy.deepcopy(asset_lookup[key]['entry']) for key in costs[uid]['verified_asset_keys']]}
    pb.require(len(pb.canonical(packet)) == costs[uid]['R_array_element_bytes'], 'actual full packet render differs from exact v3 cost catalog')
    packets.append(packet)

manifest = pb.freeze_inputs(packets, binding, budget, manual, output_schema, DESTINATION)
pb.save_exclusive(DESTINATION / Path(__file__).name, Path(__file__).read_bytes())
checks = []
for batch in manifest['batches']:
    raw = {v: Path(batch['prompts'][v]['path']).read_bytes() for v in ['R', 'W', 'H']}
    pb.require(raw['R'].split(b'\n', 1)[1] == raw['H'].split(b'\n', 1)[1], 'H differs beyond first heading')
    pb.require(manual in raw['R'] and manual in raw['W'] and manual in raw['H'], 'actual execution manual missing')
    for v in ['R', 'W', 'H']:
        pb.require(b'(condition,batch)' not in raw[v] and b'R1/R2/R3' not in raw[v] and b'"thread_id"' not in raw[v], 'execution identity leaked into initial prompt')
    indexes = {v: pb.parse(Path(batch['display_files'][v]['path']).read_bytes()) for v in ['R', 'W']}
    pb.require([x['source_id'] for x in indexes['R']] == batch['source_ids'] == [x['source_id'] for x in indexes['W']], 'display index order differs')
    for r, w in zip(indexes['R'], indexes['W']):
        compact = pb.parse(Path(r['complete_packet_file']['path']).read_bytes())
        indented = pb.parse(Path(w['complete_packet_file']['path']).read_bytes())
        pb.require(pb.canonical(compact) == pb.canonical(indented), 'W presentation changes original packet values')
        pb.require(pb.sha(pb.canonical(compact['source_bundle'])) == r['source_bundle_sha256'] == w['source_bundle_sha256'], 'saved complete source hash mismatch')
    metrics = batch['metrics']
    gate_metrics = dict(metrics); gate_metrics['worst_prompt_bytes'] = gate_metrics['conservative_full_material_presentation_bytes']
    pb.require(pb.within_budget(gate_metrics, budget), 'actual saved batch exceeds exact full-material budget')
    pb.require(metrics['actual_initial_prompt_max_bytes'] <= metrics['conservative_full_material_presentation_bytes'], 'index prompt exceeds complete-material accounting')
    checks.append({'batch_id': batch['batch_id'], 'units': batch['expected_n'], 'complete_packet_values_unchanged': True,
                   'R1_R2_R3_same_prompt_binding': True, 'H_heading_only': True, 'manual_v1_3_exact': True,
                   'complete_material_budget_passed': True, 'execution_identity_in_initial_prompt': False})

ledger = nr.blank_ledger()
ledger['plan'].update({'owner_binding_sha256': pb.file_sha(RUNTIME / 'parent-binding.json'), 'manual_sha256': pb.sha(manual),
    'batching_manifest_sha256': pb.file_sha(DESTINATION / 'batching-manifest.json'), 'global_order_sha256': manifest['global_order_sha256'],
    'ordered_batches': [b['batch_id'] for b in manifest['batches']], 'source_sample_selection': None,
    'necessary_scope_schema_sha256': pb.file_sha(RUNTIME / 'necessary-source-scope.schema.json'),
    'uniform_reading_protocol_sha256': binding['uniform_protocol']['sha256']})
ledger['authorized_development_material'] = {'records': 77, 'source_package_seal_sha256': EXPECTED[SOURCE / 'delivery-seal.json'],
    'fixed_order_UTF8_LF_sha256': order_lf_sha, 'execution_preparation_only': True, 'formal_sample_selected': False}
ledger['new_coding_chats_created'] = 0
nr.check_telemetry(ledger)
pb.save_exclusive(DESTINATION / 'execution-ledger.blank.json', pb.canonical(ledger))
preflight = {'state': 'development77_candidate_inputs_frozen_not_executed', 'record_n': 77, 'batch_n': len(checks),
             'old41_plus_old36_original_order_preserved': True, 'fixed_order_UTF8_LF_sha256': order_lf_sha,
             'parent_runtime_seal_sha256': EXPECTED[RUNTIME / 'delivery-seal.json'], 'source_package_seal_sha256': EXPECTED[SOURCE / 'delivery-seal.json'],
             'execution_manual_sha256': pb.sha(manual), 'source_package_historical_manual_binding_modified': False,
             'checks': checks, 'source_lookup_calls': 0, 'model_calls_by_preparation': 0, 'coding_chats_created': 0,
             'actual_read_receipts_created': 0, 'policy_text_emitted_to_preparation_model': False, 'formal_sample_selected': False,
             'actual_provider_telemetry': None, 'labels_created': False}
pb.save_exclusive(DESTINATION / 'render-input-preflight.json', pb.canonical(preflight))
readme = ('# Development77 native v3 candidate inputs\n\n'
          '固定 old41 + old36 的原始 77 条顺序已按 v3 操作预算冻结。每条完整来源包保存于 packets 的 compact/indented 两个等值文件；初始提示交付其完整文件定位、SHA 和来源包全值 SHA。R1/R2/R3 共用 prompt-R，W 使用 prompt-W，H 仅改首行标题。\n\n'
          '执行手册为逐字 v1.3。来源 package 的 v1.1 历史绑定未被修改或误用为执行手册。全部原 CTX、新增公共段落及原图/几何定位保留；文件可用和机械 hash 核验没有生成实际语义阅读或看图收据。\n\n'
          '这是开发候选输入与分批清单，尚未创建编码对话、运行模型或产生标签；正式样本未抽取。原生 provider 容量与 telemetry 仍为 null。分批预算以完整 R/W/H 呈现而非较小的初始文件索引提示计算。完整第一份输出不得为满足规划预留而截断或重判。\n')
pb.save_exclusive(DESTINATION / 'README.md', readme.encode())
files = [{'path': str(p.resolve()), 'sha256': pb.file_sha(p), 'bytes': p.stat().st_size}
         for p in sorted(DESTINATION.rglob('*')) if p.is_file()]
seal = {'seal_type': 'development77-native-v3-candidate-inputs', 'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'files': files, 'parent_runtime_seal_sha256': EXPECTED[RUNTIME / 'delivery-seal.json'],
        'source_package_seal_sha256': EXPECTED[SOURCE / 'delivery-seal.json'], 'records': 77, 'batches': len(checks),
        'actual_model_calls': 0, 'coding_chats_created': 0, 'formal_sample_selected': False, 'actual_provider_telemetry': None}
pb.save_exclusive(DESTINATION / 'delivery-seal.json', pb.canonical(seal))
print(json.dumps({'state': preflight['state'], 'records': 77, 'batches': len(checks),
                  'seal_sha256': pb.file_sha(DESTINATION / 'delivery-seal.json'),
                  'batching_manifest_sha256': pb.file_sha(DESTINATION / 'batching-manifest.json'),
                  'preflight_sha256': pb.file_sha(DESTINATION / 'render-input-preflight.json'),
                  'v3_runtime_seal_unchanged': pb.file_sha(RUNTIME / 'delivery-seal.json') == EXPECTED[RUNTIME / 'delivery-seal.json']}))
