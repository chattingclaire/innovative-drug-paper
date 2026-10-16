"""Authenticate a restored table row before resolving its column meaning.

This is a material adapter after a reported header omission. It introduces
no construct or reference-label lookup. A numeric term has meaning only
through its source-bound column; negative eligibility still describes the
substantive exclusive right under operation note v1.4, I.3.
"""
import hashlib
import json
import re
from pathlib import Path
from rule_support import RuleView

RELEASE = 'v32.1-verified-table-material-adapter-20261007-candidate01'
BASIS = 'CAL-5D-20260926-v1.3 I; 共用操作说明v1.4 创新性第3条：专有试验数据保护权利范围、期限及实质适用条件'


def _sha(path):
    p = Path(path)
    if not p.is_file():
        raise ValueError('table context source file is missing')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError('verified table context: ' + message)


def verified_rows(record):
    """Return only rows bound to image, structured source and candidate unit."""
    certs = record.get('verified_table_context_v4', [])
    shared = record.get('llm_v29_shared_context', {}).get('verified_table_context_v4', [])
    _require(certs == shared, 'rule and shared column contexts differ')
    _require(isinstance(certs, list), 'certificate collection must be a list')
    if not certs:
        return []
    _require(len(certs) == 1, 'one source row must have one table certificate')
    _require(record.get('unit_type') == 'normative_table_row', 'target is not a normative table row')
    source_path = record.get('unit_source') or record.get('source', '')
    source_sha = record.get('unit_source_sha256') or record.get('source_sha256')
    _require(record.get('source') == source_path and record.get('source_sha256') == source_sha,
             'source components disagree')
    _require(_sha(source_path) == source_sha, 'structured source SHA does not match')
    candidate_path = record.get('candidate_file', '')
    _require(_sha(candidate_path) == record.get('candidate_sha256'), 'candidate SHA does not match')
    source = json.loads(Path(source_path).read_text())
    candidate = json.loads(Path(candidate_path).read_text())
    _require(candidate.get('source_sha256') == source_sha
             and Path(candidate.get('source', '')).resolve() == Path(source_path).resolve(),
             'candidate is not bound to this structured source')
    units = [u for u in candidate.get('unit_candidates', []) if u.get('id') == record.get('unit_id')]
    _require(len(units) == 1, 'candidate unit identity is ambiguous')
    unit = units[0]
    _require(unit.get('type') == 'normative_table_row' and unit.get('text') == record.get('unit_text'),
             'candidate unit type/text differs')
    paragraphs = [p for p in candidate.get('paragraphs', []) if p.get('id') == unit.get('paragraph_id')]
    _require(len(paragraphs) == 1, 'candidate paragraph identity is ambiguous')
    paragraph = paragraphs[0]
    rows = []
    for cert in certs:
        _require(isinstance(cert, dict) and cert.get('kind') == 'verified_table_title_columns_v4',
                 'unknown certificate kind')
        _require(cert.get('source_structured_sha256') == source_sha, 'certificate source SHA differs')
        title = cert.get('table_title')
        columns = cert.get('column_names')
        cells = cert.get('raw_row_cells')
        _require(isinstance(title, str) and bool(title.strip()) and isinstance(columns, list)
                 and len(columns) == 4 and all(isinstance(x, str) and x.strip() for x in columns),
                 'invalid title/column order')
        _require(cert.get('text') == title + '；列名：' + ' | '.join(columns), 'literal header text differs')
        _require(isinstance(cells, list) and len(cells) == len(columns)
                 and all(isinstance(x, str) for x in cells), 'invalid row cells')
        _require(record.get('unit_text') == ' | '.join(cells), 'current unit is not the exact certified row')
        matches = [(i, t) for i, t in enumerate(source.get('tables', []))
                   if t.get('title') == title and t.get('source_image') == cert.get('source_image')]
        _require(len(matches) == 1, 'table title/image does not identify one source table')
        table_index, table = matches[0]
        row_index = cert.get('row_index_zero_based')
        _require(type(row_index) is int and 0 <= row_index < len(table.get('rows', [])), 'invalid source row index')
        _require(table['rows'][row_index] == cells and table.get('columns') == columns,
                 'source row/column mapping differs')
        _require(table.get('source_sha256') == cert.get('source_image_sha256')
                 and _sha(cert.get('source_image', '')) == cert.get('source_image_sha256'),
                 'source image SHA does not match')
        _require(table.get('source_url') == cert.get('source_url')
                 and source.get('source_url') == cert.get('source_document_url')
                 and table.get('visually_checked') is True, 'source URL/visual provenance differs')
        _require(unit.get('table_title') == title and unit.get('columns') == columns
                 and unit.get('cells') == cells, 'candidate unit table mapping differs')
        _require(paragraph.get('text') == record['unit_text'] and paragraph.get('cells') == cells
                 and paragraph.get('columns') == columns and paragraph.get('table_title') == title
                 and paragraph.get('source_image') == cert['source_image']
                 and paragraph.get('line_ids') == [f'tables:{table_index + 1}:row:{row_index + 1}'],
                 'candidate paragraph source line does not bind this row')
        candidate_tables = [t for t in candidate.get('structured_tables', [])
                            if t.get('title') == title and t.get('source_image') == cert['source_image']]
        _require(len(candidate_tables) == 1 and candidate_tables[0] == table,
                 'candidate structured table differs from original source')
        rows.append({'certificate': cert, 'paragraph_id': paragraph['id'],
                     'source_lines': paragraph['line_ids'], 'source_path': source_path,
                     'source_sha256': source_sha, 'candidate_path': candidate_path,
                     'candidate_sha256': record['candidate_sha256'], 'unit_id': record['unit_id']})
    return rows


def describes_exclusive_data_right(cert):
    """A term or explicit exclusion in the actual protection-term column."""
    columns = cert['column_names']
    if '数据保护期' not in columns or not re.search(r'药品|生物制品', cert['table_title']):
        return False
    cells = cert['raw_row_cells']
    term = cells[columns.index('数据保护期')].strip()
    if re.fullmatch(r'[0-9一二三四五六七八九十]+年', term):
        return True
    return term in {'—', '－', '-', '–'} and '不给予数据保护' in cells[columns.index('备注')]


def revise(record, result):
    rows = verified_rows(record)
    if result.get('judgement_status') == 'undetermined':
        return result
    view = RuleView(record, result)
    for row in rows:
        cert = row['certificate']
        if not describes_exclusive_data_right(cert):
            continue
        dependency = {k: v for k, v in row.items() if k != 'certificate'}
        dependency.update({'kind': 'verified_current_table_exclusive_data_right_column',
                           'antecedent_text': cert['text'], 'table_title': cert['table_title'],
                           'column_names': cert['column_names'], 'raw_row_cells': cert['raw_row_cells'],
                           'source_image': cert['source_image'], 'source_image_sha256': cert['source_image_sha256'],
                           'source_url': cert['source_url'], 'row_index_zero_based': cert['row_index_zero_based'],
                           'scope_usage': 'Only this exact authenticated row and its actual column meaning; no title-wide propagation.'})
        item = view.add('V321_I_verified_table_exclusive_data_right_term_or_exclusion', 'I',
                        0, len(view.text), 'research_support', BASIS, dependency)
        item['rule_release'] = RELEASE
    return result
