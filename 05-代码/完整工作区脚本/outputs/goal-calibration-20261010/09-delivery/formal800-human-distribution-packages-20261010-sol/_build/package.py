#!/usr/bin/env python3
"""Byte-preserving, side-isolated distribution archives of the sealed v2 release."""
from pathlib import Path
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from io import BytesIO
import json
import posixpath
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / '09-delivery/formal800-human-final-release-v2-20261010-sol'
DEST = Path(__file__).resolve().parents[1]
RELEASE_SHA = '8e96dfc55ff63cd77df0bca97774a909306a3a1327445b48c55924808037b758'


def digest(raw):
    return sha256(raw).hexdigest()


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def save_json(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def readme(side):
    return f'''正式 800 独立人工编码材料 — 编码员 {side}（v2）

请先完整解压 ZIP，保留 coder-{side} 与 shared-source 的相对位置；不要直接在 ZIP 内打开工作簿。
打开 coder-{side}/formal800-{side}-frozen.xlsx，并阅读同目录 manual.txt、execution-prompt.txt、common-execution-protocol.txt、填写说明.txt 和 合法待定填写补充.txt。工作簿材料链接在完整解压后可用。

本次冻结材料身份：v2 release.json 的 SHA-256
{RELEASE_SHA}
该身份绑定本次冻结手册、执行提示、协议和合法待定的输入表示补充。包内原工作簿及材料按原字节复制。

每个盲号有五个维度。只填写 D/E，保持 A/B/C、盲号、维度和行顺序原样，不新增复核栏：
• 可判为二元时，D 填 0 或 1，E 填判断理由。
• 关键材料不足时，D 留空，E 必须以“待定：具体缺失理由”填写，例如“待定：缺少判断该关系所需的条款原文”。“待定:”半角冒号同样可用。不要把示例当作实际理由。
• D/E 全空表示尚未填写。D 空而 E 是普通说明或仅“待定：”，仍需补充；D 已填 0/1 时，不应再写与其矛盾的待定说明。
理由可用自由文字描述对象、关系、引文位置；材料缺失须说明具体缺什么，按同目录冻结手册判断。

请双方各自独立完成，不互看对方的判断，不以机器结果或裁定答案代填。提交前保存未经协商的原始填写 XLSX；协调员另行处理分歧和待定，不改写独立初判原件。
真实执行说明可以由本人或用户以文字提供给协调员并绑定接收记录；无需另建 sidecar 文件，也无需新增工作簿栏。说明实际执行身份及独立执行情况，不能把本包或空白模板当作已执行证明。

本 ZIP 仅表示材料已准备供分发。它不声明已经分发、真人已经启动或完成；现有模板全部仍为空白。
'''.encode('utf-8')


def check_links(archive, side):
    names = set(archive.namelist())
    counts = {'relative_links_checked': 0, 'external_links_skipped': 0,
              'fragment_links_skipped': 0, 'broken_relative_links': 0}
    errors = []

    def link(origin, target):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            counts['external_links_skipped'] += 1
            return
        if not parsed.path:
            counts['fragment_links_skipped'] += 1
            return
        counts['relative_links_checked'] += 1
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(origin), unquote(parsed.path)))
        okay = not resolved.startswith('../') and not resolved.startswith('/') and resolved in names
        if not okay:
            counts['broken_relative_links'] += 1
            errors.append({'origin': origin, 'target': target, 'resolved': resolved})

    class LinksOnly(HTMLParser):
        def __init__(self, origin):
            super().__init__()
            self.origin = origin

        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in ('href', 'src') and value:
                    link(self.origin, value)

    workbook_name = f'coder-{side}/formal800-{side}-frozen.xlsx'
    with zipfile.ZipFile(BytesIO(archive.read(workbook_name))) as workbook:
        relations = ET.fromstring(workbook.read('xl/worksheets/_rels/sheet1.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in relations
                   if r.attrib.get('Type', '').endswith('/hyperlink')}
        sheet = ET.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
        links = sheet.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}hyperlinks/'
                              '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}hyperlink')
        assert len(links) == 4000 and len(targets) == 800
        for item in links:
            rid = item.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            link(workbook_name, targets[rid])
    html_names = sorted(n for n in names if n.startswith(f'coder-{side}/materials/') and n.endswith('.html'))
    assert len(html_names) == 800
    for name in html_names:
        LinksOnly(name).feed(archive.read(name).decode('utf-8'))
    assert not errors, errors[:10]
    counts.update({'workbook_hyperlinks': len(links), 'distinct_workbook_targets': len(targets),
                   'html_files_scanned_for_href_src_only': len(html_names)})
    # Captured source-site HTML is an unchanged original document, not the
    # generated offline packet UI. Retain its original site references as-is.
    snapshots = {'html_files': 0, 'external_references': 0, 'fragment_references': 0,
                 'relative_references': 0, 'relative_references_to_pack_members': 0,
                 'original_site_relative_references_not_bundled': 0}

    class SnapshotLinksOnly(HTMLParser):
        def __init__(self, origin):
            super().__init__()
            self.origin = origin

        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key not in ('href', 'src') or not value:
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc:
                    snapshots['external_references'] += 1
                elif not parsed.path:
                    snapshots['fragment_references'] += 1
                else:
                    snapshots['relative_references'] += 1
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(self.origin), unquote(parsed.path)))
                    field = ('relative_references_to_pack_members' if target in names
                             else 'original_site_relative_references_not_bundled')
                    snapshots[field] += 1

    for name in sorted(n for n in names if n.startswith('shared-source/') and n.endswith('.html')):
        snapshots['html_files'] += 1
        SnapshotLinksOnly(name).feed(archive.read(name).decode('utf-8'))
    counts['relative_link_scope'] = 'workbook and generated coder materials HTML'
    counts['unchanged_original_source_html_references'] = snapshots
    return counts


def main():
    assert digest((SOURCE / 'release.json').read_bytes()) == RELEASE_SHA
    release_binding = binding(SOURCE / 'release.json')
    source_seal_binding = binding(SOURCE / 'seal.json')
    source_seal = json.loads((SOURCE / 'seal.json').read_text())
    sealed = {item['path']: item for item in source_seal['members']}
    inputs = [release_binding, source_seal_binding]
    source_files = {}
    for folder in ('coder-A', 'coder-B', 'shared-source'):
        for path in sorted((SOURCE / folder).rglob('*')):
            if path.is_dir():
                continue
            assert path.is_file() and not path.is_symlink(), str(path)
            raw = path.read_bytes()
            original = sealed[str(path)]
            assert len(raw) == original['bytes'] and digest(raw) == original['sha256'], str(path)
            member = path.relative_to(SOURCE).as_posix()
            source_files[member] = raw
            inputs.append({**binding(path), 'package_member': member})
    assert sum(n.startswith('coder-A/') for n in source_files) == 1607
    assert sum(n.startswith('coder-B/') for n in source_files) == 1607
    assert sum(n.startswith('shared-source/') for n in source_files) == 159
    packages = []
    for side in ('A', 'B'):
        prefix = f'coder-{side}/'
        expected = {n: raw for n, raw in source_files.items()
                    if n.startswith(prefix) or n.startswith('shared-source/')}
        expected['先读我.txt'] = readme(side)
        path = DEST / f'formal800-{side}-independent.zip'
        with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, raw in sorted(expected.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 10, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, raw, compresslevel=9)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names)) == len(expected) == 1767
            assert set(names) == set(expected)
            assert archive.testzip() is None
            inventory = []
            for name in sorted(names):
                raw = archive.read(name)
                assert raw == expected[name], name
                inventory.append({'member': name, 'bytes': len(raw), 'sha256': digest(raw)})
            links = check_links(archive, side)
        packages.append({'coder': side, 'archive': binding(path),
                         'allowed_roots': [f'coder-{side}', 'shared-source', '先读我.txt'],
                         'file_members': len(expected), 'source_members_byte_identical': 1766,
                         'source_counts': {f'coder-{side}': 1607, 'shared-source': 159},
                         'root_readme': {'member': '先读我.txt', 'bytes': len(expected['先读我.txt']),
                                         'sha256': digest(expected['先读我.txt'])},
                         'member_inventory_sha256': digest(canonical(inventory)),
                         'workbook_input': binding(SOURCE / f'coder-{side}/formal800-{side}-frozen.xlsx'),
                         'links': links})
    manifest = {'version': 'formal800-independent-distribution-packages-1',
                'status': 'prepared_for_distribution', 'distributed': False,
                'human_execution_started_claimed': False, 'actual_human_submissions': 0,
                'release_identity': release_binding, 'source_seal': source_seal_binding,
                'packages': packages,
                'scope': 'Byte copies, archive member equality and existing relative-link reachability only.',
                'exclusions': 'Each archive contains only its own coder directory, shared-source and root readme.',
                'AI_provenance': {'author': 'Codex AI', 'requested_model': 'GPT-6.1 Sol',
                                  'requested_reasoning_effort': 'ultra',
                                  'provider_configuration_independently_verified': False}}
    save_json(DEST / 'package-manifest.json', manifest)
    outputs = [binding(Path(__file__).resolve()), binding(DEST / 'package-manifest.json')]
    outputs += [p['archive'] for p in packages]
    save_json(DEST / 'seal.json', {'version': 'formal800-distribution-package-seal-1',
              'release_sha256': RELEASE_SHA, 'input_members': inputs, 'output_members': outputs,
              'status': 'prepared_for_distribution', 'seal_self_excluded': True,
              'inputs_unchanged_verified': True, 'new_originals_written_with_no_overwrite': True})
    # Recheck every original input after packaging; no source path is written.
    for item in inputs:
        current = binding(Path(item['path']))
        assert current['bytes'] == item['bytes'] and current['sha256'] == item['sha256']
    print(json.dumps({'release_sha256': RELEASE_SHA,
                      'packages': [{'coder': p['coder'], 'sha256': p['archive']['sha256'],
                                    'bytes': p['archive']['bytes'], 'members': p['file_members'],
                                    'links': p['links']} for p in packages],
                      'seal': binding(DEST / 'seal.json')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
