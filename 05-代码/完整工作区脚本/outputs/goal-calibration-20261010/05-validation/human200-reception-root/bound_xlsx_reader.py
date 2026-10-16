"""Existing reader/normalizer unchanged; inspect shape adapted800 to200 only."""
import io,re,zipfile
from collections import Counter
from decimal import Decimal,InvalidOperation
from types import SimpleNamespace
import xml.etree.ElementTree as ET
DIMS=('S','E','Ec','I','F')
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def nonempty(v,where):require(isinstance(v,str) and bool(v.strip()),'nonempty string required: '+where)

OLD=SimpleNamespace(nonempty=nonempty)

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

def _normalize_binary(c):
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

def normalize(c, reason_cell=None):
    value, status, method = _normalize_binary(c)
    literal = (reason_cell is not None and reason_cell['formula'] is None
               and reason_cell['cell_type'] in ('s', 'inlineStr', 'str'))
    reason = reason_cell['resolved_value'] if literal else None
    if status == 'filled' and isinstance(reason, str) and reason.startswith('待定'):
        return value, 'invalid', 'binary_pending_marker_conflict'
    if status != 'unfilled' or reason_cell is None or blank(reason_cell):
        return value, status, method
    if not literal:
        return None, 'invalid', 'nonliteral_null_reason_not_allowed'
    for prefix in ('待定：', '待定:'):
        if reason.startswith(prefix):
            if reason[len(prefix):].strip():
                return None, 'lawful_null', 'explicit_pending_prefix_with_nonempty_missing_reason'
            return None, 'incomplete', 'pending_prefix_without_missing_reason'
    return None, 'incomplete', 'blank_D_ordinary_reason_needs_clarification'

def inspect(side, raw, data):
    issues, normalized, completion_warnings = [], [], []
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
        for n in range(2, 1002):
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
            value, status, method = normalize(d, e)
            if status == 'invalid':
                if method == 'binary_pending_marker_conflict':
                    issue('binary_pending_marker_conflict', e['address'], method, value_cell=d, reason_cell=e)
                elif method == 'nonliteral_null_reason_not_allowed':
                    issue('invalid_null_reason', e['address'], method, original_cell=e)
                else:
                    issue('invalid_value', d['address'], method, original_cell=d)
            if status == 'incomplete':
                completion_warnings.append({'code': method, 'sheet': sheet_name, 'cell': e['address'], 'value_cell': d['address'], 'requires_clarification': True})
            reason = None if blank(e) else e['resolved_value']
            if e['formula'] is not None or (not blank(e) and e['cell_type'] not in ('s', 'inlineStr', 'str')):
                issue('invalid_reason_type', e['address'], 'reason must be literal free text; formula/boolean/number unsupported', original_cell=e)
            if status in ('filled', 'lawful_null'):
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
                               'finished_judgment': status in ('filled', 'lawful_null'),
                               'normalization': method, 'value_cell': d, 'reason_cell': e,
                               'derived_record': True, 'not_original_human_file': True})
        for bid in data['bids']:
            for dim in DIMS:
                if (bid, dim) not in seen:
                    issue('missing_blind_dimension', None, 'assigned dimension absent', blind_id=bid, dimension=dim)
        for addr, c in cells.items():
            m = re.fullmatch(r'([A-Z]+)([0-9]+)', addr)
            if (m.group(1) not in set('ABCDE') or int(m.group(2)) > 1001) and not blank(c):
                issue('extra_input_cell', addr, 'nonempty cell outside issued A1:E1001')
        counts = dict(Counter(x['completion_status'] for x in normalized))
        return {'side': side, 'content_valid': not issues, 'issues': issues, 'counts': counts,
                'expected_rows': 1000, 'expected_blind_ids': 200, 'fully_filled': counts.get('filled') == 1000 and not issues,
                'fully_completed': counts.get('filled', 0) + counts.get('lawful_null', 0) == 1000 and not issues,
                'completion_warnings': completion_warnings}, normalized
    except (ValueError, KeyError, IndexError, ET.ParseError, zipfile.BadZipFile) as e:
        issue('unreadable_xlsx', None, str(e))
        return {'side': side, 'content_valid': False, 'issues': issues, 'counts': {}, 'fully_filled': False}, []
