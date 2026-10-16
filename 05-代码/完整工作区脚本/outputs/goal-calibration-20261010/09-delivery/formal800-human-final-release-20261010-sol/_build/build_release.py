"""Copy already drawn human materials; freeze new editorial inputs; no coding."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
DEST = Path(__file__).resolve().parent.parent
ROOT = DEST.parent.parent
OLD = ROOT / '09-delivery/formal800-human-workbooks-prerelease-sol'
SOURCE = ROOT / '05-validation/full800-common-v15-prerelease-sol'
ADAPTER = ROOT / '05-validation/formal800-xlsx-reception-adapter-sol'
FREEZE = ROOT / '03-manual/full4481-common-release-20261010-root/common-input-freeze.json'
VERSION = 'formal800-human-final-release-20261010-1'
inputs, copied, modified_indices = {}, [], []


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': digest(raw)}


def read_input(p, expected=None):
    raw = p.read_bytes()
    b = {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': digest(raw)}
    if expected:
        assert b['bytes'] == expected['bytes'] and b['sha256'] == expected['sha256'], str(p)
    inputs[str(p.resolve())] = b
    return raw


def save_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        assert json.loads(p.read_text()) == value, 'different partial-build JSON: ' + str(p)
        return
    with p.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def copy(p, destination, expected=None):
    raw = read_input(p, expected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == raw, 'different partial-build copy: ' + str(destination)
    else:
        with destination.open('xb') as f:
            f.write(raw)
    assert digest(destination.read_bytes()) == digest(raw)
    copied.append({'input': str(p.resolve()), 'output': str(destination.resolve()), 'sha256': digest(raw), 'bytes': len(raw)})


assert not (DEST / 'release.json').exists(), 'release already exists; never overwrite'
old_seal = json.loads(read_input(OLD / 'seal.json'))
source_seal = json.loads(read_input(SOURCE / 'seal.json'))
old_members = {x['absolute_path']: x for x in old_seal['members']}
source_members = {x['absolute_path']: x for x in source_seal['members']}
freeze = json.loads(read_input(FREEZE))
assert freeze['manual']['sha256'] == '5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
assert freeze['prompt']['sha256'] == '69c8291200aa960502c240dc24a6671ca9a8c6b0aad95998e0af611b6ea2ffc9'
assert freeze['protocol']['sha256'] == '50d9bc8f36ace5e366fbd19392e6d7cfb2bfaaf8202b7582e8ea05725667ca20'
for key, b in freeze.items():
    if isinstance(b, dict) and 'path' in b and 'sha256' in b:
        read_input(Path(b['path']), b)  # Hash validation only, never source prose/label inspection.
for key, name in [('manual', 'manual.txt'), ('prompt', 'execution-prompt.txt'), ('protocol', 'common-execution-protocol.txt')]:
    for folder in ('common-freeze', 'coder-A', 'coder-B'):
        copy(Path(freeze[key]['path']), DEST / folder / name, freeze[key])
copy(FREEZE, DEST / 'common-freeze/original-common-input-freeze.json')

for side in 'AB':
    original = OLD / ('coder-' + side)
    target = DEST / ('coder-' + side)
    copy(original / ('formal800-' + side + '-pre-release.xlsx'), target / ('formal800-' + side + '-frozen.xlsx'), old_members[str((original / ('formal800-' + side + '-pre-release.xlsx')).resolve())])
    for p in sorted((original / 'materials').iterdir()):
        assert p.is_file() and p.suffix in ('.html', '.json')
        copy(p, target / 'materials' / p.name, old_members[str(p.resolve())])
    for name in ('packet.jsonl', 'packet-index.json', 'labels.blank.jsonl', 'submission.blank.json', 'manifest.json'):
        p = SOURCE / ('coder-' + side) / name
        if p.exists():
            copy(p, DEST / 'coordinator-private/original-preparation-metadata' / ('coder-' + side) / name, source_members[str(p.resolve())])
for p in sorted((OLD / 'shared-source/source-files').iterdir()):
    copy(p, DEST / 'shared-source/source-files' / p.name, old_members[str(p.resolve())])
for relative in ('coder-A/source-assets-index.json', 'coder-B/source-assets-index.json', 'shared-source/delivery-source-assets-index.json'):
    p = OLD / relative
    obj = json.loads(read_input(p, old_members[str(p.resolve())]))
    for item in obj['files']:
        item['original_delivery_prepared_absolute_path'] = item['prepared_absolute_path']
        item['prepared_absolute_path'] = str((DEST / item['prepared_relative_path']).resolve())
        assert binding(Path(item['prepared_absolute_path']))['sha256'] == item['sha256']
    obj.update(version=VERSION, status='released_for_independent_human_coding',
               original_index_binding=inputs[str(p.resolve())])
    save_json(DEST / relative, obj)
    modified_indices.append(relative)
copy(OLD / 'material-pages-index.json', DEST / 'material-pages-index.json', old_members[str((OLD / 'material-pages-index.json').resolve())])
for name in ('mapping.json', 'draw-contract.json'):
    p = SOURCE / 'coordinator-private' / name
    copy(p, DEST / 'coordinator-private' / name, source_members[str(p.resolve())])
copy(SOURCE / 'seal.json', DEST / 'coordinator-private/original-source-package-seal.json')
copy(OLD / 'seal.json', DEST / 'coordinator-private/original-delivery-seal.json')

spec = importlib.util.spec_from_file_location('_actual_xlsx_adapter', ADAPTER / 'adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
read_input(ADAPTER / 'adapter.py')
read_input(ADAPTER / 'bindings.json')
_, mapping, data = adapter.preflight()
assert len(mapping['records']) == 800
draw = json.loads((DEST / 'coordinator-private/draw-contract.json').read_bytes())
assert draw['sample_n'] == 800 and draw['domain_sample_n'] == {'remaining': 600, 'exposed': 200}
assert len(draw['selected_strata']) == 41

links, errors, external, readbacks = [], [], [], {}


def link_check(origin, target):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        external.append({'origin': str(origin.relative_to(DEST)), 'target': target})
        return
    if not parts.path:
        return
    resolved = (origin.parent / unquote(parts.path)).resolve()
    within = resolved == DEST or DEST in resolved.parents
    exists = within and resolved.is_file()
    links.append({'origin': str(origin.relative_to(DEST)), 'target': target, 'reachable': exists})
    if not exists:
        errors.append(links[-1])


class Links(HTMLParser):
    def __init__(self, origin):
        super().__init__(convert_charrefs=True)
        self.origin = origin

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                link_check(self.origin, value)


for side in 'AB':
    workbook = DEST / ('coder-' + side) / ('formal800-' + side + '-frozen.xlsx')
    report, parsed = adapter.inspect(side, workbook.read_bytes(), data[side])
    assert report['content_valid'] and report['counts'] == {'unfilled': 4000}
    assert len(parsed) == 4000 and len({r['blind_id'] for r in parsed}) == 800
    assert all(r['value'] is None and r['reason'] is None for r in parsed)
    readbacks[side] = {'workbook': binding(workbook), 'rows': 4000, 'blind_N': 800,
                       'unfilled_values_N': 4000, 'blank_reasons_N': 4000,
                       'template_exact_ABC_order': True, 'content_issues': report['issues']}
    with zipfile.ZipFile(workbook) as z:
        relations = ET.fromstring(z.read('xl/worksheets/_rels/sheet1.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in relations if r.attrib.get('Type', '').endswith('/hyperlink')}
        sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        nspace = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        side_links = sheet_xml.findall('s:hyperlinks/s:hyperlink', nspace)
        assert len(side_links) == 4000 and len(targets) == 800
        for link in side_links:
            rid = link.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            link_check(workbook, targets[rid])
    pages = list((DEST / ('coder-' + side) / 'materials').glob('*.html'))
    assert len(pages) == 800
    for p in pages:
        parser = Links(p)
        parser.feed(p.read_text())  # href/src only; no policy text or labels inspected.
assert not errors, errors[:10]

release = {'version': VERSION, 'status': 'frozen_for_execution',
           'material_status': 'released_for_independent_human_coding',
           'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'source_package_sha256': inputs[str((SOURCE / 'seal.json').resolve())]['sha256'],
           'template_sha256': {s: readbacks[s]['workbook']['sha256'] for s in 'AB'},
           'packet_file_sha256': {s: data[s]['submission']['packet_file_sha256'] for s in 'AB'},
           'manual': binding(DEST / 'common-freeze/manual.txt'),
           'manual_version': '五维共同编码手册 v1.3F-r1：本次生产编码冻结版',
           'execution_prompt': binding(DEST / 'common-freeze/execution-prompt.txt'),
           'execution_protocol': binding(DEST / 'common-freeze/common-execution-protocol.txt'),
           'common_input_freeze': inputs[str(FREEZE.resolve())],
           'production_source_package_sha256': freeze['source_package_seal']['sha256'],
           'workbooks': {s: readbacks[s]['workbook'] for s in 'AB'},
           'sample_n': 800, 'dimensions_per_side': 4000, 'strata_N': 41,
           'domain_sample_n': draw['domain_sample_n'],
           'sampling_changed': False, 'original_source_and_blind_order_changed': False,
           'real_people_assigned': False, 'actually_distributed': False,
           'actual_human_coding_started': False, 'actual_human_submissions_N': 0,
           'formal_validation_complete': False,
           'status_meaning': 'materials frozen and available for independent human coding; no delivery, execution, identity, or submission claim'}
save_json(DEST / 'release.json', release)
save_json(DEST / 'workbook-manifest.json', {'version': VERSION, 'status': release['material_status'],
                                         'release': binding(DEST / 'release.json'), 'sides': readbacks,
                                         'original_workbook_bytes_preserved': True,
                                         'worksheet_name_preserved': '初判-pre-release',
                                         'no_review_columns_added': True})
save_json(DEST / 'mechanical-readback.json', {'status': 'passed', 'sides': readbacks,
                                          'total_unfilled_values_N': 8000, 'total_blank_reasons_N': 8000,
                                          'relative_link_N': len(links), 'unreachable_relative_links_N': len(errors),
                                          'external_reference_link_N': len(external),
                                          'relative_link_targets': sorted(set(x['target'] for x in links)),
                                          'semantic_source_or_gold_or_machine_output_reads_N': 0,
                                          'existing_16_control_tests_rerun': False})
save_json(DEST / 'coordinator-private/reception-contract.json', {
    'adapter': inputs[str((ADAPTER / 'adapter.py').resolve())],
    'bindings': inputs[str((ADAPTER / 'bindings.json').resolve())],
    'release': binding(DEST / 'release.json'), 'command': 'receive',
    'original_candidates_byte_identical': True, 'new_adapter_framework_required': False,
    'no_sidecar_required': True, 'actually_received': False})

guide = '''本包材料已按本次共同冻结版准备，可用于正式800条独立人类编码。材料状态不表示已经分发、已开始编码或已有真人结果。
本方目录含同字节正式manual.txt、execution-prompt.txt和common-execution-protocol.txt，请先完整阅读。工作簿保留原模板字节与工作表名“初判-pre-release”；本次有效发布状态由包根release.json与正式手册绑定确定。
A列盲号链接本方materials完整材料；B列是原条款正文；C列是S/E/Ec/I/F。仅填D的0/1和E自由文字理由，说明原文片段/允许语境位置、药物或用药对象和直接关系。不要改变A/B/C、表头、原行顺序，不加复核栏。每条五维独立判，填0也写理由。
未完成或确指关键材料不足，D留空，E记录待定原因与具体补材，不能把缺材填0。空白作为unfilled保留，接收器不会猜补或变成0。
保持本方coder目录与shared-source在同一根目录，不改变相对路径。不能看另一方初判、机器答案或Gold，不请求AI代填。保存原始初判XLSX后再组织补材、讨论或裁定，初判版本不能覆盖。
完成后提交保存的原始XLSX，并如实说明执行者、是否本人独立初判、是否看过另一方/机器答案、是否讨论、是否用AI草拟标签、既往开发接触情况及实际起止/提交信息。可直接用文字说明，由协调员将原始说明保存并绑定原件SHA。无须另填JSON或sidecar，也无须增加复核栏。
'''
for side in 'AB':
    (DEST / ('coder-' + side) / '填写说明.txt').write_text(guide)

readme = '''正式800条人类独立编码的本次冻结材料已准备完成。released_for_independent_human_coding仅表示材料冻结可用；实际分发、两名真人安排、独立执行和提交尚未发生，本次没有创建真人标签。

A/B各800个盲号、4000行五维，D的8000个值和E的8000个理由全部空白。抽样沿原41层、remaining600/exposed200及原纳入概率；原ID、各方presentation order、材料页、原始JSON、原source资产和XLSX全部逐字节保留。51来源与既有来源版本不重新构建。工作簿沿用原表名“初判-pre-release”以保留已验证模板字节；实际release.json绑定本次冻结手册/提示/协议。没有真人复核栏。

给每名编码者本方coder-A或coder-B目录以及shared-source，放在同一个根目录并保持相对路径。每方目录有正式manual.txt、execution-prompt.txt、common-execution-protocol.txt、填写说明、XLSX和全部材料。协调员保留另一方目录、release.json与coordinator-private；不要把A/B初判或coordinator-private映射材料互相交给编码者。包内源引用保留原始身份，但“可用材料”不构成已阅读/已使用声明。

实际返回时只收原始XLSX与真实执行说明，可由用户文字形成已绑定receipt。协调员保留原文说明，按实际事实保存既有字段：executor_code、actual_actor_type=real_human_independent、completion_status、human_coding_completed、actual_started_at/actual_submitted_at、prior_development_exposure、AI_assistance及四项independence_declaration（own_first_judgment、machine_answers_unseen、peer_answers_unseen、no_discussion_before_seal）。原件SHA、packet SHA、manual SHA和800/4000计数由协调员机械绑定，不要求编码者填技术JSON或sidecar。未知字段不得造填，内容仍能保存解析，资格状态如实待确认。

原件→派生接收入口使用已存在05-validation/formal800-xlsx-reception-adapter-sol/adapter.py，精确release SHA见coordinator-private/reception-contract.json。命令：

    python3 /ABS/05-validation/formal800-xlsx-reception-adapter-sol/adapter.py receive --xlsx-a /实际返回/A.xlsx --xlsx-b /实际返回/B.xlsx --release /本包绝对路径/release.json --release-sha256 /本包release实际SHA --declaration-a /协调员已保存真实A声明.json --declaration-b /协调员已保存真实B声明.json --out /ABS/05-validation/formal800-xlsx-reception-adapter-sol/receptions/新首件目录

其中/ABS为本项目outputs/goal-calibration-20261010的绝对路径，SHA是字符串而非文件路径。必须用尚不存在的接收目录；接收器保存原始XLSX bytes与SHA，保留独立A/B，按私有source_id对齐并产生分歧/待定清单，不自动合并成裁定。未收到声明或有待填时不称正式内容接收完成，不计算指标或CI。真实接收命令尚未运行。

机械核对见mechanical-readback.json，原件及最终发布绑定见seal.json。未重跑既有16项控制，没有读Gold、机器first/labels/metrics或新裁定标签。
'''
(DEST / 'README.md').write_text(readme.replace('/ABS', str(ROOT)))

save_json(DEST / 'copy-ledger.json', {'version': VERSION, 'exact_byte_copies': copied,
                                   'metadata_indices_rebased_only': modified_indices,
                                   'manual_prompt_protocol_binding': {k: freeze[k] for k in ('manual', 'prompt', 'protocol')},
                                   'semantic_source_reads': False, 'XLSX_authoring_or_value_changes': False})
save_json(DEST / 'read-ledger.json', {'input_bindings': list(inputs.values()),
                                   'scope': 'metadata and blank forms; raw byte copy/hash; template equality; href/src-only reachability scan',
                                   'excluded': 'Gold, new rule/native first, machine labels/metrics, adjudication labels',
                                   'requested_model': 'GPT-6.1 Sol', 'requested_reasoning': 'ultra',
                                   'provider_model_and_effort_independently_verified': False})
for p, b in inputs.items():
    assert binding(Path(p)) == b, 'original input changed: ' + p
members = [binding(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name != 'seal.json']
save_json(DEST / 'seal.json', {'version': VERSION, 'status': release['material_status'],
                             'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                             'input_bindings': list(inputs.values()), 'members': members,
                             'members_N': len(members), 'release': binding(DEST / 'release.json'),
                             'self_hash_policy': 'seal excludes itself', 'old_inputs_unchanged': True,
                             'sampling_changed': False, 'actual_human_submissions_N': 0,
                             'actually_distributed': False, 'formal_validation_complete': False})
print(json.dumps({'status': release['material_status'], 'root': str(DEST),
                  'release': binding(DEST / 'release.json'), 'members_N': len(members),
                  'unfilled_values': 8000, 'blank_reasons': 8000,
                  'relative_links_checked': len(links), 'unreachable': len(errors),
                  'actual_human_submissions_N': 0}, ensure_ascii=False))
