"""Read-only XLSX original -> independent derived records. No coding or statistics."""
import argparse
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import posixpath
import re
import sys
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
VERSION = 'formal800-xlsx-reception-1'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
CONTRACT = HERE / 'bindings.json'


def file_binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    import hashlib
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def dependencies():
    b = json.loads(CONTRACT.read_text())
    common = b['dependencies']['interface_common']
    receiver = b['dependencies']['human_receiver']
    for x in (common, receiver):
        if file_binding(x['path']) != x:
            raise ValueError('sealed reused helper changed: ' + x['path'])
    sys.path.insert(0, str(Path(common['path']).parent))
    import interface_common
    spec = importlib.util.spec_from_file_location('_xlsx_existing_receiver', receiver['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return b, interface_common, module


BIND, COMMON, OLD = dependencies()
parse_json, digest, require = COMMON.parse_json, COMMON.digest, COMMON.require


def load_bound(key):
    return parse_json(COMMON.verify_binding(BIND['inputs'][key]))


def load_rows(key):
    return OLD.lines(COMMON.verify_binding(BIND['inputs'][key]))


def text_value(node):
    # Exclude phonetic annotations: only actual text runs are concatenated.
    return ''.join(x.text or '' for x in node.findall('s:t', NS) + node.findall('s:r/s:t', NS))


def read_xlsx(raw):
    """Keep OOXML types, payloads and formulas, without evaluating cached formulas."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(len(z.namelist()) == len(set(z.namelist())), 'duplicate ZIP members')
        require(sum(x.file_size for x in z.infolist()) < 64 * 1024 * 1024, 'XLSX exceeds finite reader limit')
        root = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {x.attrib['Id']: x.attrib for x in rels}
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [text_value(x) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        sheets = {}
        for sheet in root.findall('s:sheets/s:sheet', NS):
            require(sheet.attrib['name'] not in sheets, 'duplicate worksheet name')
            rel = targets[sheet.attrib[RNS + 'id']]
            require(rel.get('TargetMode') != 'External', 'external worksheet unsupported')
            target = rel['Target']
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            require(member.startswith('xl/'), 'worksheet member outside workbook')
            xml = ET.fromstring(z.read(member))
            cells, duplicates = {}, []
            for row in xml.findall('s:sheetData/s:row', NS):
                for c in row.findall('s:c', NS):
                    addr = c.attrib.get('r', '')
                    require(re.fullmatch(r'[A-Z]+[1-9][0-9]*', addr), 'invalid cell address: ' + addr)
                    if addr in cells:
                        duplicates.append(addr)
                    typ = c.attrib.get('t', 'n')
                    v, f = c.find('s:v', NS), c.find('s:f', NS)
                    payload = v.text if v is not None else None
                    resolved = payload
                    if typ == 's' and payload is not None:
                        require(payload.isdigit() and int(payload) < len(strings), 'invalid shared string: ' + addr)
                        resolved = strings[int(payload)]
                    elif typ == 'inlineStr':
                        inline = c.find('s:is', NS)
                        resolved = text_value(inline) if inline is not None else ''
                    cells[addr] = {'address': addr, 'present': True, 'cell_type': typ,
                                   'raw_v': payload, 'text': resolved if typ in ('s', 'inlineStr', 'str') else None,
                                   'formula': None if f is None else {'text': f.text, 'attributes': f.attrib},
                                   'style_index': c.attrib.get('s'), 'resolved_value': resolved}
            sheets[sheet.attrib['name']] = {'cells': cells, 'duplicates': duplicates,
                                           'merged': [x.attrib.get('ref') for x in xml.findall('s:mergeCells/s:mergeCell', NS)]}
        return sheets


def cell(cells, addr):
    return cells.get(addr, {'address': addr, 'present': False, 'cell_type': None, 'raw_v': None,
                            'text': None, 'formula': None, 'style_index': None, 'resolved_value': None})


def blank(c):
    return c['formula'] is None and c['cell_type'] not in ('b', 'e', 'd') and c['resolved_value'] in (None, '')


def comparable(c):
    # Identical source text/IDs, while accepting normal shared/inline storage rewrites.
    return c['resolved_value'], c['formula'], 'text' if c['cell_type'] in ('s', 'inlineStr', 'str') else c['cell_type']


def normalize(c):
    if c['formula'] is not None:
        return None, 'invalid', 'formula_not_allowed'
    if c['cell_type'] in ('b', 'e', 'd'):
        return None, 'invalid', 'boolean_error_or_date_not_allowed'
    if blank(c):
        return None, 'unfilled', 'blank_preserved'
    if c['cell_type'] in ('s', 'inlineStr', 'str') and c['resolved_value'] in ('0', '1'):
        return int(c['resolved_value']), 'filled', 'exact_excel_text_0_1'
    if c['cell_type'] == 'n':
        try:
            number = Decimal(c['raw_v'])
            if number.is_finite() and number in (Decimal(0), Decimal(1)):
                return int(number), 'filled', 'numeric_0_1'
        except (InvalidOperation, TypeError):
            pass
    return None, 'invalid', 'only_numeric_or_exact_text_0_1_allowed'


def preflight():
    # Only metadata/seals/blank forms and issued templates; no packet/source prose opened.
    for binding in BIND['inputs'].values():
        COMMON.verify_binding(binding)
    for seal_key, keys in [('source_seal', ['mapping', 'draw_contract', 'labels_A', 'labels_B', 'submission_A', 'submission_B', 'index_A', 'index_B']),
                           ('delivery_seal', ['workbook_manifest', 'template_A', 'template_B'])]:
        sealed = {x['absolute_path']: x for x in load_bound(seal_key)['members']}
        for key in keys:
            actual = BIND['inputs'][key]
            entry = sealed.get(actual['path'])
            require(entry is not None and entry['sha256'] == actual['sha256'] and entry['bytes'] == actual['bytes'], 'original sealed member differs: ' + key)
    manifest = load_bound('workbook_manifest')
    mapping, draw = load_bound('mapping'), load_bound('draw_contract')
    require(draw['sample_n'] == 800 and len(mapping['records']) == 800, '800 sample contract differs')
    selected = draw['selected_record_ids_in_frame_order']
    require([x['source_id'] for x in mapping['records']] == selected and len(set(selected)) == 800, 'draw/mapping identity differs')
    require(digest(('\n'.join(selected) + '\n').encode()) == draw['selected_ID_UTF8_LF_sha256'], 'draw ordered ID hash differs')
    specs = {x['side']: x for x in manifest['workbooks']}
    side_data = {}
    for side in 'AB':
        spec = specs[side]
        require(spec['file']['sha256'] == BIND['inputs']['template_' + side]['sha256'], 'issued workbook manifest binding differs')
        sheets = read_xlsx(COMMON.verify_binding(BIND['inputs']['template_' + side]))
        require(set(sheets) == {spec['worksheet']}, 'issued template sheet contract differs')
        cells = sheets[spec['worksheet']]['cells']
        rows, index, sub = load_rows('labels_' + side), load_bound('index_' + side), load_bound('submission_' + side)
        require(index['side'] == side and index['record_N'] == 800 and len(rows) == 800, 'side count differs')
        require(sub['record_N'] == 800 and sub['dimensions_N'] == 4000, 'blank submission counts differ')
        require(sub['packet_file_sha256'] == spec['packet_input']['sha256'] and sub['manual_sha256'] == spec['manual']['sha256'], 'packet/manual contract differs')
        bids = [x['blind_id'] for x in rows]
        require(bids == [x['blind_id'] for x in index['entries']] and len(set(bids)) == 800, 'labels/index order differs')
        bundle = {x['blind_id']: x['source_bundle_canonical_sha256'] for x in index['entries']}
        for i, row in enumerate(rows):
            OLD.exact(row, {'blind_id', 'source_bundle_canonical_sha256', 'completion_status', 'dimensions'}, 'blank row')
            OLD.exact(row['dimensions'], DIMS, 'five dimensions')
            require(row['completion_status'] == 'unfilled' and row['source_bundle_canonical_sha256'] == bundle[row['blind_id']], 'blank binding differs')
            for j, dim in enumerate(DIMS):
                n = 2 + i * 5 + j
                OLD.exact(row['dimensions'][dim], OLD.DIM_KEYS, 'existing dimension shape')
                require(row['dimensions'][dim]['value'] is None, 'blank labels contain values')
                require(cell(cells, 'A' + str(n))['resolved_value'] == bids[i] and cell(cells, 'C' + str(n))['resolved_value'] == dim, 'issued A/C differs from packet index')
                require(blank(cell(cells, 'D' + str(n))) and blank(cell(cells, 'E' + str(n))), 'issued D/E not blank')
        side_map = {x[side + '_blind_id']: x['source_id'] for x in mapping['records']}
        require(set(side_map) == set(bids) and len(side_map) == 800, 'mapping blind set differs')
        side_data[side] = {'spec': spec, 'cells': cells, 'bids': bids, 'bundle': bundle, 'source': side_map, 'submission': sub}
    for x in mapping['records']:
        require(side_data['A']['bundle'][x['A_blind_id']] == side_data['B']['bundle'][x['B_blind_id']], 'A/B same-source bundle differs')
    return manifest, mapping, side_data


def inspect(side, raw, data):
    issues, normalized = [], []
    sheet_name = data['spec']['worksheet']
    def issue(code, addr, message, **extra):
        issues.append(dict(code=code, sheet=sheet_name, cell=addr, message=message, **extra))
    try:
        sheets = read_xlsx(raw)
        if set(sheets) != {sheet_name}:
            issue('sheet_set_changed', None, 'expected one exact issued worksheet', actual=list(sheets))
        if sheet_name not in sheets:
            return {'side': side, 'content_valid': False, 'issues': issues, 'counts': {}}, []
        sheet, template = sheets[sheet_name], data['cells']
        cells = sheet['cells']
        for addr in sheet['duplicates']:
            issue('duplicate_cell_address', addr, 'duplicate OOXML cell is ambiguous')
        for ref in sheet['merged']:
            issue('merged_input_cells', ref, 'issued flat row contract cannot be merged')
        for col in 'ABCDE':
            addr = col + '1'
            if comparable(cell(cells, addr)) != comparable(cell(template, addr)):
                issue('header_changed', addr, 'header differs from issued template')
        seen = {}
        for n in range(2, 4002):
            bid, dim = cell(cells, 'A' + str(n))['resolved_value'], cell(cells, 'C' + str(n))['resolved_value']
            for col in 'ABC':
                addr = col + str(n)
                if comparable(cell(cells, addr)) != comparable(cell(template, addr)):
                    issue('template_binding_changed', addr, 'A/B/C value or issued row order differs', column=col)
            if bid not in data['source']:
                issue('unknown_blind_id', 'A' + str(n), 'blind ID absent from assigned packet index', actual=bid)
            if dim not in DIMS:
                issue('unknown_dimension', 'C' + str(n), 'dimension must be S/E/Ec/I/F', actual=dim)
            key = (bid, dim)
            if key in seen:
                issue('duplicate_blind_dimension', 'A' + str(n), 'blind/dimension repeats', first_cell='A' + str(seen[key]), dimension_cell='C' + str(n))
            seen[key] = n
            d, e = cell(cells, 'D' + str(n)), cell(cells, 'E' + str(n))
            value, status, method = normalize(d)
            if status == 'invalid':
                issue('invalid_value', d['address'], method, original_cell=d)
            reason = None if blank(e) else e['resolved_value']
            if e['formula'] is not None or (not blank(e) and e['cell_type'] not in ('s', 'inlineStr', 'str')):
                issue('invalid_reason_type', e['address'], 'reason must be literal free text; formula/boolean/number unsupported', original_cell=e)
            if status == 'filled':
                try:
                    OLD.nonempty(reason, e['address'])
                except ValueError:
                    issue('missing_reason', e['address'], 'existing submission contract requires nonempty reason for both 0 and 1')
            expected_bid = cell(template, 'A' + str(n))['resolved_value']
            expected_dim = cell(template, 'C' + str(n))['resolved_value']
            normalized.append({'side': side, 'sheet': sheet_name, 'row': n, 'blind_id': bid, 'dimension': dim,
                               'expected_blind_id': expected_bid, 'expected_dimension': expected_dim,
                               'source_bundle_canonical_sha256': data['bundle'][expected_bid],
                               'value': value, 'completion_status': status, 'reason': reason,
                               'normalization': method, 'value_cell': d, 'reason_cell': e,
                               'derived_record': True, 'not_original_human_file': True})
        for bid in data['bids']:
            for dim in DIMS:
                if (bid, dim) not in seen:
                    issue('missing_blind_dimension', None, 'assigned dimension absent', blind_id=bid, dimension=dim)
        for addr, c in cells.items():
            m = re.fullmatch(r'([A-Z]+)([0-9]+)', addr)
            if (m.group(1) not in set('ABCDE') or int(m.group(2)) > 4001) and not blank(c):
                issue('extra_input_cell', addr, 'nonempty cell outside issued A1:E4001')
        counts = dict(Counter(x['completion_status'] for x in normalized))
        return {'side': side, 'content_valid': not issues, 'issues': issues, 'counts': counts,
                'expected_rows': 4000, 'expected_blind_ids': 800, 'fully_filled': counts.get('filled') == 4000 and not issues}, normalized
    except (ValueError, KeyError, IndexError, ET.ParseError, zipfile.BadZipFile) as e:
        issue('unreadable_xlsx', None, str(e))
        return {'side': side, 'content_valid': False, 'issues': issues, 'counts': {}, 'fully_filled': False}, []


def declared_qualification(side, report, raw, data, release, declarations):
    pending, issues = [], []
    if not report['content_valid']:
        pending.append('content_invalid')
    if not report.get('fully_filled'):
        pending.append('4000_values_and_reasons_not_complete')
    if release is None:
        pending.append('actual_release_not_supplied')
    else:
        try:
            require(release['status'] == 'frozen_for_execution', 'release status not frozen_for_execution')
            require(release['source_package_sha256'] == BIND['inputs']['source_seal']['sha256'], 'release source package differs')
            require(release['template_sha256'][side] == BIND['inputs']['template_' + side]['sha256'], 'release assigned template differs')
            require(release['packet_file_sha256'][side] == data['submission']['packet_file_sha256'], 'release packet differs')
            COMMON.verify_binding(release['manual'])
            OLD.nonempty(release['manual_version'], 'release manual version')
        except (ValueError, KeyError, OSError, TypeError) as e:
            issues.append('release: ' + str(e))
    sub = declarations.get(side)
    if sub is None:
        pending.append('actual_human_independence_declaration_not_supplied')
    else:
        try:
            require(sub['completion_status'] == 'complete' and sub['human_coding_completed'] is True, 'actual human completion not declared')
            require(sub['actual_actor_type'] == 'real_human_independent', 'independent human actor not declared')
            OLD.nonempty(sub['executor_code'], 'actual executor declaration')
            require(sub['xlsx_sha256'] == digest(raw), 'declaration XLSX byte SHA differs')
            require(sub['packet_file_sha256'] == data['submission']['packet_file_sha256'], 'declaration packet differs')
            require(sub['record_N'] == 800 and sub['dimensions_N'] == 4000, 'declaration counts differ')
            require(release is not None and sub['manual_sha256'] == release['manual']['sha256'], 'declaration released manual differs')
            start, end = OLD.timevalue(sub['actual_started_at']), OLD.timevalue(sub['actual_submitted_at'])
            require(start <= end, 'declared time order differs')
            expected = {'own_first_judgment', 'machine_answers_unseen', 'peer_answers_unseen', 'no_discussion_before_seal'}
            OLD.exact(sub['independence_declaration'], expected, 'existing independence declaration')
            require(all(v is True for v in sub['independence_declaration'].values()), 'independence not affirmatively declared')
            require(sub['AI_assistance']['label_drafting_used'] is False, 'AI label drafting declared/unknown')
            OLD.nonempty(sub['AI_assistance']['description'], 'actual AI involvement description')
            OLD.nonempty(sub['prior_development_exposure'], 'actual prior exposure')
        except (ValueError, KeyError, OSError, TypeError) as e:
            issues.append('human declaration: ' + str(e))
    eligible = not pending and not issues
    return {'status': 'content_received_on_bound_declarations' if eligible else 'qualification_pending',
            'content_reception_complete': eligible, 'eligible_for_downstream_content_handoff': eligible,
            'pending': pending, 'issues': issues, 'human_identity_independence_start_time_authenticated': False,
            'structured_evidence_automatically_validated': False, 'coordinator_evidence_review': 'required',
            'semantic_accuracy': 'not_evaluated', 'human_validation_complete': False, 'formal_validation_complete': False}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n')


def run(a):
    manifest, mapping, data = preflight()
    inputs = {s: Path(getattr(a, 'xlsx_' + s.lower())).resolve() for s in 'AB'}
    raw = {s: p.read_bytes() for s, p in inputs.items()}
    external, declarations, release = {}, {}, None
    if a.release:
        require(a.release_sha256, 'explicit release SHA required when release supplied')
        external['release.json'] = Path(a.release).read_bytes()
        require(digest(external['release.json']) == a.release_sha256, 'release expected SHA differs')
        release = parse_json(external['release.json'])
    for s in 'AB':
        p = getattr(a, 'declaration_' + s.lower())
        if p:
            external['declaration-' + s + '.json'] = Path(p).read_bytes()
            declarations[s] = parse_json(external['declaration-' + s + '.json'])
    dest = Path(a.out).resolve()
    require(HERE == dest.parent or HERE in dest.parents, 'output must stay inside adapter-owned directory')
    require(not dest.exists(), 'original first reception destination exists; never overwrite')
    dest.mkdir(parents=True, mode=0o700)
    reports, rows = {}, {}
    for s in 'AB':
        original = dest / ('original-' + s + '.xlsx')
        original.write_bytes(raw[s])
        original.chmod(0o400)
        reports[s], rows[s] = inspect(s, raw[s], data[s])
        qualification = declared_qualification(s, reports[s], raw[s], data[s], release, declarations)
        if a.command == 'dry-run':
            qualification.update(status='dry_run_no_actual_reception', content_reception_complete=False,
                                 eligible_for_downstream_content_handoff=False)
        reports[s].update(input_original={'path': str(inputs[s]), 'sha256': digest(raw[s]), 'bytes': len(raw[s])},
                          archived_original=file_binding(original), qualification=qualification)
        write_lines(dest / ('derived-' + s + '.jsonl'), rows[s])
    if all(s in declarations for s in 'AB') and declarations['A'].get('executor_code') == declarations['B'].get('executor_code'):
        for s in 'AB':
            q = reports[s]['qualification']
            q.update(status='qualification_pending', content_reception_complete=False, eligible_for_downstream_content_handoff=False)
            q['issues'].append('same declared executor for independent A/B; coordinator must resolve actual independence')
    for name, value in external.items():
        p = dest / name
        p.write_bytes(value)
        p.chmod(0o400)
    aligned, differences, todos = [], [], []
    if all(reports[s]['content_valid'] for s in 'AB'):
        lookup = {s: {(x['blind_id'], x['dimension']): x for x in rows[s]} for s in 'AB'}
        for record in mapping['records']:
            for dim in DIMS:
                left, right = [lookup[s][record[s + '_blind_id'], dim] for s in 'AB']
                pending = left['completion_status'] != 'filled' or right['completion_status'] != 'filled'
                status = 'pending' if pending else 'disagreement' if left['value'] != right['value'] else 'agreement'
                pair = {'source_id': record['source_id'], 'dimension': dim, 'status': status,
                        'source_bundle_canonical_sha256': left['source_bundle_canonical_sha256'],
                        'A': {k: left[k] for k in ('blind_id', 'row', 'value', 'reason', 'completion_status')},
                        'B': {k: right[k] for k in ('blind_id', 'row', 'value', 'reason', 'completion_status')},
                        'independent_first_judgments_unchanged': True, 'automatic_adjudication': False,
                        'qualification': 'see per-side report; alignment is not eligibility proof'}
                aligned.append(pair)
                if status == 'disagreement':
                    differences.append(pair)
                if status in ('pending', 'disagreement'):
                    todos.append(dict(pair, required_action='await_actual_independent_input' if pending else 'coordinator_adjudication',
                                      adjudicated_value=None, adjudication_reason=None, adjudicator=None,
                                      dry_run=a.command == 'dry-run'))
    private = dest / 'coordinator-private'
    write_lines(private / 'source-aligned.jsonl', aligned)
    write_lines(private / 'disagreements.jsonl', differences)
    write_lines(private / 'adjudication-todo.jsonl', todos)
    result = {'version': VERSION, 'command': a.command,
              'status': 'content_rejected' if any(not x['content_valid'] for x in reports.values()) else
                        'dry_run_mechanical_check' if a.command == 'dry-run' else 'originals_archived_content_parsed',
              'sides': reports, 'alignment_rows': len(aligned), 'disagreement_rows': len(differences), 'pending_todo_rows': len(todos),
              'alignment_withheld_due_to_content_errors': any(not x['content_valid'] for x in reports.values()),
              'actual_human_coding_claimed_by_parser': False, 'formal_validation_complete': False,
              'statistics_or_CI_calculated': False, 'source_prose_semantically_inspected': False,
              'derived_JSON_is_original_human_file': False, 'first_original_overwrite_allowed': False,
              'compatibility': 'XLSX D/E and free-text reason received; legacy JSON unchanged. No new sidecar requirement.',
              'source_version': manifest['version'], 'binding_contract': file_binding(CONTRACT)}
    write_json(dest / 'report.json', result)
    members = [file_binding(p) for p in sorted(dest.rglob('*')) if p.is_file()]
    seal = {'version': VERSION, 'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'input_bindings': BIND['inputs'], 'reused_helper_bindings': BIND['dependencies'],
            'adapter_code': file_binding(Path(__file__)),
            'input_xlsx': {s: reports[s]['input_original'] for s in 'AB'}, 'output_members': members,
            'original_byte_copies_verified': all(file_binding(dest / ('original-' + s + '.xlsx'))['sha256'] == digest(raw[s]) for s in 'AB'),
            'self_hash_policy': 'seal excludes itself', 'overwrite_allowed': False}
    write_json(dest / 'seal.json', seal)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('dry-run', 'receive'))
    for name in ('xlsx-a', 'xlsx-b', 'out'):
        p.add_argument('--' + name, required=True)
    for name in ('release', 'release-sha256', 'declaration-a', 'declaration-b'):
        p.add_argument('--' + name)
    a = p.parse_args()
    try:
        r = run(a)
        print(json.dumps({'status': r['status'], 'out': str(Path(a.out).resolve()),
                          'counts': {s: r['sides'][s]['counts'] for s in 'AB'},
                          'issues': {s: len(r['sides'][s]['issues']) for s in 'AB'},
                          'qualification': {s: r['sides'][s]['qualification']['status'] for s in 'AB'}}, ensure_ascii=False))
        return 2 if r['status'] == 'content_rejected' else 0
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(json.dumps({'status': 'rejected', 'reason': str(e), 'formal_validation_complete': False}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
