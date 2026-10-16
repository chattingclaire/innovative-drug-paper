"""Copy frozen v1 body/templates; only null operation and metadata are extended."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
SOURCE = ROOT / '09-delivery/formal800-human-final-release-20261010-sol'
DEST = ROOT / '09-delivery/formal800-human-final-release-v2-20261010-sol'
VERSION = 'formal800-human-final-release-20261010-2'
inputs, copied = {}, []


def binding(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def input_bytes(p, expected=None):
    raw = p.read_bytes()
    b = binding(p)
    if expected:
        assert b['sha256'] == expected['sha256'] and b['bytes'] == expected['bytes'], str(p)
    inputs[str(p.resolve())] = b
    return raw


def json_write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def copy(p, dest, expected=None):
    raw = input_bytes(p, expected)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as f:
        f.write(raw)
    assert binding(dest)['sha256'] == inputs[str(p.resolve())]['sha256']
    copied.append({'from': str(p.resolve()), 'to': str(dest.resolve()), 'sha256': inputs[str(p.resolve())]['sha256']})


assert not DEST.exists(), 'final v2 already exists; never overwrite'
DEST.mkdir()
seal = json.loads(input_bytes(SOURCE / 'seal.json'))
original_release = json.loads(input_bytes(SOURCE / 'release.json'))
skip = {'release.json', 'README.md', 'workbook-manifest.json', 'mechanical-readback.json', 'copy-ledger.json', 'read-ledger.json', 'coordinator-private/reception-contract.json'}
indices = {'coder-A/source-assets-index.json', 'coder-B/source-assets-index.json', 'shared-source/delivery-source-assets-index.json'}
for entry in seal['members']:
    p = Path(entry['path'])
    relative = p.relative_to(SOURCE).as_posix()
    if relative in skip or relative in indices or relative.startswith('_build/'):
        continue
    copy(p, DEST / relative, entry)
for relative in indices:
    p = SOURCE / relative
    index = json.loads(input_bytes(p))
    for asset in index['files']:
        asset['previous_release_prepared_absolute_path'] = asset['prepared_absolute_path']
        asset['prepared_absolute_path'] = str((DEST / asset['prepared_relative_path']).resolve())
        assert binding(Path(asset['prepared_absolute_path']))['sha256'] == asset['sha256']
    index.update(version=VERSION, previous_release_index_binding=binding(p))
    json_write(DEST / relative, index)
for folder in ('common-freeze', 'coder-A', 'coder-B'):
    copy(HERE / 'input-representation-supplement.txt', DEST / folder / '合法待定填写补充.txt')
copy(SOURCE / 'seal.json', DEST / 'coordinator-private/original-final-v1-seal.json')
copy(SOURCE / 'release.json', DEST / 'coordinator-private/original-final-v1-release.json')

release = dict(original_release)
release.update(version=VERSION, created_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               previous_release=binding(SOURCE / 'release.json'), input_representation_only_changed=True,
               input_representation_supplement=binding(DEST / 'common-freeze/合法待定填写补充.txt'),
               reception_adapter=binding(HERE / 'adapter.py'), statistics_bridge=binding(HERE / 'bridge.py'),
               human_first_driver=binding(HERE / 'human_first_driver.py'))
for key, name in [('manual', 'manual.txt'), ('execution_prompt', 'execution-prompt.txt'), ('execution_protocol', 'common-execution-protocol.txt')]:
    release[key] = binding(DEST / 'common-freeze' / name)
    assert release[key]['sha256'] == original_release[key]['sha256']
release['workbooks'] = {s: binding(DEST / ('coder-' + s) / ('formal800-' + s + '-frozen.xlsx')) for s in 'AB'}
assert all(release['workbooks'][s]['sha256'] == original_release['template_sha256'][s] for s in 'AB')
json_write(DEST / 'release.json', release)

spec = importlib.util.spec_from_file_location('_null_v2_adapter_for_empty_readback', HERE / 'adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
_, mapping, data = adapter.preflight()
readbacks = {}
for side in 'AB':
    path = Path(release['workbooks'][side]['path'])
    report, parsed = adapter.inspect(side, path.read_bytes(), data[side])
    qualification = adapter.declared_qualification(side, report, path.read_bytes(), data[side], release, {})
    assert report['content_valid'] and report['counts'] == {'unfilled': 4000}
    assert not report['fully_completed'] and not qualification['issues']
    assert all(x['value'] is None and x['reason'] is None and x['finished_judgment'] is False for x in parsed)
    readbacks[side] = {'workbook': release['workbooks'][side], 'counts': report['counts'],
                       'content_valid': True, 'fully_completed': False, 'qualification': qualification}
old_mechanical = json.loads(input_bytes(SOURCE / 'mechanical-readback.json'))
json_write(DEST / 'mechanical-readback.json', {'status': 'passed', 'sides': readbacks,
                                            'total_unfilled_values_N': 8000, 'total_blank_reasons_N': 8000,
                                            'relative_link_N': old_mechanical['relative_link_N'],
                                            'unreachable_relative_links_N': 0,
                                            'link_proof': 'v1 validated relative targets plus byte-identical pages/XLSX/assets at identical relative paths',
                                            'existing_16_control_tests_rerun': False, 'actual_human_submissions_N': 0})
json_write(DEST / 'workbook-manifest.json', {'version': VERSION, 'status': release['material_status'],
                                         'release': binding(DEST / 'release.json'), 'sides': readbacks,
                                         'original_workbook_bytes_preserved': True, 'no_review_columns_added': True,
                                         'worksheet_name_preserved': '初判-pre-release'})
json_write(DEST / 'coordinator-private/reception-contract.json', {
    'version': 'formal800-xlsx-lawful-null-reception-2', 'adapter': binding(HERE / 'adapter.py'),
    'statistics_bridge': binding(HERE / 'bridge.py'), 'human_first_driver': binding(HERE / 'human_first_driver.py'),
    'release': binding(DEST / 'release.json'), 'command': 'receive', 'actually_received': False,
    'fully_completed_definition': '4000 filled or lawful_null finished judgments; unfilled/incomplete/invalid never complete',
    'lawful_null_statistics_state': 'semantic_null; existing engine NA and joint_binary unchanged',
    'new_sidecar_or_review_columns_required': False})

text = f'''正式800真人材料v2已冻结可用，真人分发、执行和提交仍为0。此版本仅补“关键材料缺失null”的D/E输入表示和接收/统计衔接，不改变判据、抽样或原空白工作簿。

每方800条五维、4000槽。manual.txt、execution-prompt.txt、common-execution-protocol.txt保留v1同字节正式冻结文件；原材料、盲号、原序和41层remaining600/exposed200不变。工作表名仍“初判-pre-release”，本次状态以release.json为准。

请给编码者本方coder目录及shared-source，保持相对路径，同时读填写说明和合法待定填写补充.txt。D仍只填0/1或留空，E自由文字理由；关键材料缺失时D留空，E以“待定：/待定:”开头，冒号后具体写明缺失材料、无法判断的关系与所需补材，标为完成判断的lawful_null。D/E全空是unfilled；D空普通E或只有待定前缀是incomplete需澄清。0/1与以“待定”开头的理由冲突会拒绝，不代改值。原E和实际单元格类型完整保存。无新列、sidecar或复核栏。

完成内容接收允许二元值与合法null合计覆盖4000槽；真实用户独立执行声明仍必须如实，由协调员保存用户文字并绑定原件SHA，沿用既有声明字段。没有声明或未完成时只保存解析，不称真人接收完成。双方null不算二元一致；null和分歧仍交协调员核验材料或裁定，不从A/B自动造参照。

原release v1、旧adapter、旧统计桥不改。v2实际原件接收用 {HERE / 'adapter.py'} receive，--release指本包release.json并绑定真实SHA，真实声明参数与原接口相同，--out为本补充目录内新的接收目录。接收输出version=formal800-xlsx-lawful-null-reception-2，fully_completed表示4000二元/合法null完成。

统计输入用 {HERE / 'human_first_driver.py'} --convert或--calculate，--upstream-reception实际v2接收目录，--statistics-metadata实际已绑定human_first元数据，--statistics-metadata-sha256其真实SHA，--output-dir本补充目录内新输出目录。没有真实接收/声明/统计元数据则在数值运行前拒绝；本次未运行实际human_first。桥只将lawful_null投影为既有semantic_null，原joint_binary/coverage/NA/5000及seed20261010处理保持，不改变阈值或产生新的总体结果。

release精确SHA与入口绑定见coordinator-private/reception-contract.json。原件及输入输出见seal.json。合法null的理由形式不证明它在共同手册下实质成立，协调员须核验；不强填0/1。没有读取Gold、机器first/labels/metrics或裁定标签，也不运行旧16测试。
'''
(DEST / 'README.md').write_text(text)
json_write(DEST / 'copy-ledger.json', {'version': VERSION, 'copied_original_bytes': copied,
                                   'manual_prompt_protocol_bytes_unchanged': True, 'XLSX_bytes_unchanged': True,
                                   'only_input_representation_added': True})
json_write(DEST / 'read-ledger.json', {'input_bindings': list(inputs.values()),
                                   'scope': 'v1 seal and metadata; byte-copy/hash; original empty XLSX mechanical readback',
                                   'semantic_source_or_Gold_machine_adjudication_reads_N': 0,
                                   'requested_model': 'GPT-6.1 Sol', 'requested_reasoning': 'ultra',
                                   'actual_provider_setting_independently_verified': False})
for p, b in inputs.items():
    assert binding(Path(p)) == b
members = [binding(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name != 'seal.json']
json_write(DEST / 'seal.json', {'version': VERSION, 'status': release['material_status'], 'members': members,
                             'members_N': len(members), 'input_bindings': list(inputs.values()),
                             'new_interface_bindings': {k: release[k] for k in ('input_representation_supplement', 'reception_adapter', 'statistics_bridge', 'human_first_driver')},
                             'release': binding(DEST / 'release.json'), 'self_hash_policy': 'self excluded',
                             'all_old_inputs_unchanged': True, 'actual_human_submissions_N': 0,
                             'sampling_or_semantic_rules_changed': False, 'formal_validation_complete': False})
print(json.dumps({'status': 'v2_material_release_ready', 'root': str(DEST), 'release': binding(DEST / 'release.json'),
                  'members_N': len(members), 'unfilled_values_N': 8000, 'actual_human_submissions_N': 0}, ensure_ascii=False))
