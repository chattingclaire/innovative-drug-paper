"""Project a frozen, variable-size blind Excel form with the original normalizer.

Call only after the actual assignment, material and original-file review.
No sampling, adjudication or independent authority is provided here.
"""
from collections import Counter
import posixpath
import re
from support import require, verify, canonical

DIMS = ('S', 'E', 'Ec', 'I', 'F')
SHEET = '独立初判'


def read_workbook(reader_module, raw):
    # The frozen reader omitted this import in its relative-relationship branch.
    # Supply the standard library dependency; do not change its OOXML parser,
    # normalization functions, source file or stored human bytes.
    if not hasattr(reader_module, 'posixpath'):
        reader_module.posixpath = posixpath
    require(reader_module.posixpath is posixpath, 'Unexpected worksheet path resolver')
    return reader_module.read_xlsx(raw)


def project_dynamic_xlsx(raw_binding, template_binding, assignments, reader_module):
    require(isinstance(assignments, list) and assignments, 'Nonempty frozen assignments required')
    ids, blind_ids = [], []
    for row in assignments:
        require(set(row) == {'unit_id', 'original_blind_id', 'source_bundle_sha256'},
                'Assignments must bind exact unit/blind/material identity')
        require(all(isinstance(row[k], str) and row[k] for k in row), 'Empty assignment identity')
        require(re.fullmatch(r'[0-9a-f]{64}', row['source_bundle_sha256']) is not None,
                'Original source material SHA required')
        ids.append(row['unit_id']); blind_ids.append(row['original_blind_id'])
    require(len(set(ids)) == len(ids) and len(set(blind_ids)) == len(blind_ids),
            'Duplicate unit or blind ID in frozen assignment')
    template = read_workbook(reader_module, verify(template_binding).read_bytes())
    actual = read_workbook(reader_module, verify(raw_binding).read_bytes())
    require(set(template) == set(actual) == {SHEET}, 'Expected one exact issued worksheet')
    maximum_row = 1 + len(assignments) * len(DIMS)
    for name, book in (('template', template), ('original', actual)):
        sheet = book[SHEET]
        require(not sheet['duplicates'], name + ' contains duplicate OOXML cells')
        require(not sheet['merged'], name + ' contains merged input cells')
        for address, cell in sheet['cells'].items():
            match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', address)
            require(match is not None, 'Invalid worksheet cell address')
            if match[1] not in 'ABCDE' or len(match[1]) != 1 or int(match[2]) > maximum_row:
                require(reader_module.blank(cell), name + ' has data outside the issued form')
    expected_cells, actual_cells = template[SHEET]['cells'], actual[SHEET]['cells']
    get = reader_module.cell
    for col in 'ABCDE':
        before, after = get(expected_cells, col + '1'), get(actual_cells, col + '1')
        require(before['formula'] is None and not reader_module.blank(before), 'Issued header must be literal')
        require(reader_module.comparable(before) == reader_module.comparable(after), 'Issued header changed')
    output, normalized = {}, []
    for index, assignment in enumerate(assignments):
        labels, dimension_status, unfinished = {}, {}, 0
        for offset, dimension in enumerate(DIMS):
            n = 2 + index * len(DIMS) + offset
            a, b, c = [get(expected_cells, col + str(n)) for col in 'ABC']
            require(a['resolved_value'] == assignment['original_blind_id'] and c['resolved_value'] == dimension,
                    'Issued template does not match fixed assignment order/dimensions')
            require(not reader_module.blank(b), 'Issued material locator is missing')
            for col in 'ABC':
                before, after = get(expected_cells, col + str(n)), get(actual_cells, col + str(n))
                require(before['formula'] is None, 'Issued identity/material fields must be literal')
                require(reader_module.comparable(before) == reader_module.comparable(after),
                        'Original blind ID, material locator or dimension differs from issued template')
            require(all(reader_module.blank(get(expected_cells, col + str(n))) for col in 'DE'),
                    'Issued template must not contain prefilled judgments or reasons')
            d, e = get(actual_cells, 'D' + str(n)), get(actual_cells, 'E' + str(n))
            value, status, normalization = reader_module.normalize(d, e)
            require(status in ('filled', 'lawful_null', 'unfilled', 'incomplete'),
                    'Invalid human value/reason: ' + normalization)
            require(e['formula'] is None and (reader_module.blank(e) or e['cell_type'] in ('s', 'inlineStr', 'str')),
                    'Reason must be literal text, not formula/number/boolean')
            reason = None if reader_module.blank(e) else e['resolved_value']
            if status in ('filled', 'lawful_null'):
                reader_module.OLD.nonempty(reason, 'E' + str(n))
            else:
                require(value is None, 'Unfinished judgment cannot carry a label')
                dimension_status[dimension] = 'execution_failure'; unfinished += 1
            labels[dimension] = value
            normalized.append({'unit_id': assignment['unit_id'], 'blind_id': assignment['original_blind_id'],
                               'source_bundle_sha256': assignment['source_bundle_sha256'],
                               'row': n, 'dimension': dimension, 'value': value, 'completion_status': status,
                               'normalization': normalization, 'reason': reason})
        if unfinished == len(DIMS):
            result = None
        else:
            result = {'status': 'completed', 'labels': labels}
            if dimension_status:
                result.update(dimension_status=dimension_status,
                              failure_code='unfilled_or_incomplete_original_human_slot')
        output[assignment['unit_id']] = result
    counts = dict(Counter(row['completion_status'] for row in normalized))
    return output, {'original': raw_binding, 'issued_template': template_binding,
                    'worksheet': SHEET, 'assigned_N': len(assignments), 'assigned_slot_N': len(normalized),
                    'slot_completion_counts': counts,
                    'fully_completed': all(row['completion_status'] in ('filled', 'lawful_null') for row in normalized),
                    'relative_worksheet_standard_library_dependency_supplied': True,
                    'normalization': 'unchanged frozen reader.normalize and nonempty reason contract',
                    'every_assigned_row_retained': True, 'unfinished_never_imputed': True,
                    'normalized_projection': normalized, 'output_projection_sha256': canonical(output),
                    'actual_human_identity_or_statistics_authority_claimed': False}
