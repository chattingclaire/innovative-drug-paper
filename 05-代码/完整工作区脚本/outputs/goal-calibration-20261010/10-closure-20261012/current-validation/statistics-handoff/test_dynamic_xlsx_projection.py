"""Finite NONHUMAN workbook controls; original study workbooks are never read."""
import copy
import io
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dynamic_xlsx_projection import DIMS, project_dynamic_xlsx
from support import binding, dependencies, module, save_new

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def workbook(cells, *, relative=True, merged=False):
    buffer = io.BytesIO()
    root = ET.Element('worksheet', xmlns=NS); data = ET.SubElement(root, 'sheetData')
    rows = {}
    for address, spec in cells.items():
        n = ''.join(ch for ch in address if ch.isdigit())
        row = rows.setdefault(n, ET.SubElement(data, 'row', r=n)) if n not in rows else rows[n]
        kind, value = spec
        cell = ET.SubElement(row, 'c', r=address, t='n' if kind == 'formula' else kind)
        if kind == 'inlineStr':
            ET.SubElement(ET.SubElement(cell, 'is'), 't').text = value
        elif kind == 'formula':
            ET.SubElement(cell, 'f').text = value; ET.SubElement(cell, 'v').text = '1'
        else:
            ET.SubElement(cell, 'v').text = str(value)
    if merged:
        ET.SubElement(ET.SubElement(root, 'mergeCells', count='1'), 'mergeCell', ref='D2:D3')
    target = 'worksheets/sheet1.xml' if relative else '/xl/worksheets/sheet1.xml'
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="独立初判" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{target}"/></Relationships>')
        archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(root, encoding='utf-8'))
    return buffer.getvalue()


def run():
    deps = dependencies(); reader = module('_TOY_dynamic_xlsx_original_reader', deps['legacy_reader'])
    assignments = [{'unit_id': f'TOY-NONHUMAN-{i}', 'original_blind_id': f'TOY-BLIND-{i}',
                    'source_bundle_sha256': str(i + 1) * 64} for i in range(2)]
    template = {col + '1': ('inlineStr', name) for col, name in zip('ABCDE', ('盲号', '材料', '维度', '值', '理由'))}
    for i, assignment in enumerate(assignments):
        for j, dim in enumerate(DIMS):
            n = 2 + i * 5 + j
            template.update({f'A{n}': ('inlineStr', assignment['original_blind_id']),
                             f'B{n}': ('inlineStr', 'TOY-NONHUMAN-material-' + str(i)),
                             f'C{n}': ('inlineStr', dim)})
    original = copy.deepcopy(template)
    original.update({'D2': ('n', '1'), 'E2': ('inlineStr', 'TOY explicit positive'),
                     'D3': ('inlineStr', '0'), 'E3': ('inlineStr', 'TOY explicit negative'),
                     'E4': ('inlineStr', '待定：TOY missing evidence'),
                     'D6': ('n', '1'), 'E6': ('inlineStr', 'TOY explicit positive')})
    cases = []
    with tempfile.TemporaryDirectory(prefix='NONHUMAN-dynamic-xlsx-') as temporary:
        directory = Path(temporary)
        issued = directory / 'TOY-template.xlsx'; issued.write_bytes(workbook(template))
        def project(cells, **kwargs):
            path = directory / 'TOY-original.xlsx'; path.write_bytes(workbook(cells, **kwargs))
            return project_dynamic_xlsx(binding(path), binding(issued), assignments, reader)
        output, proof = project(original)
        assert output['TOY-NONHUMAN-0'] == {'status': 'completed', 'labels': {'S': 1, 'E': 0, 'Ec': None, 'I': None, 'F': 1},
                    'dimension_status': {'I': 'execution_failure'}, 'failure_code': 'unfilled_or_incomplete_original_human_slot'}
        assert output['TOY-NONHUMAN-1'] is None
        assert proof['slot_completion_counts'] == {'filled': 3, 'lawful_null': 1, 'unfilled': 6}
        assert len(proof['normalized_projection']) == 10 and not proof['fully_completed']
        cases.append({'case': 'relative_target_preserves_binary_null_partial_and_whole_nonresponse', 'passed': True})
        absolute, _ = project(original, relative=False)
        assert absolute == output
        cases.append({'case': 'absolute_and_relative_worksheet_targets_same_projection', 'passed': True})
        changes = [
            ('changed_blind_id', 'A2', ('inlineStr', 'TOY-wrong')),
            ('changed_material_locator', 'B2', ('inlineStr', 'TOY-wrong')),
            ('changed_dimension', 'C2', ('inlineStr', 'F')),
            ('changed_header', 'D1', ('inlineStr', 'TOY-wrong')),
            ('formula_label', 'D2', ('formula', '1+0')),
            ('boolean_label', 'D2', ('b', '1')),
            ('formula_reason', 'E2', ('formula', '1+0')),
            ('missing_reason', 'E2', ('inlineStr', '')),
            ('binary_pending_conflict', 'E2', ('inlineStr', '待定：TOY')),
            ('extra_input_column', 'F2', ('n', '1')),
            ('extra_input_row', 'D12', ('n', '1')),
        ]
        for name, address, value in changes:
            changed = copy.deepcopy(original); changed[address] = value
            try:
                project(changed)
            except ValueError as error:
                cases.append({'case': name, 'passed': True, 'rejected_reason': str(error)})
            else:
                raise AssertionError('Unexpectedly accepted: ' + name)
        try:
            project(original, merged=True)
        except ValueError as error:
            cases.append({'case': 'merged_input_cells', 'passed': True, 'rejected_reason': str(error)})
        else:
            raise AssertionError('Merged cells unexpectedly accepted')
        assert binding(deps['legacy_reader']['path']) == deps['legacy_reader']
    return {'data_role': 'NONHUMAN_controls_only', 'case_N': len(cases), 'all_passed': all(c['passed'] for c in cases),
            'cases': cases, 'actual_human_originals_read': False, 'sample_drawn': False,
            'original_reader_file_unchanged': True, 'actual_statistics_executed': False}


if __name__ == '__main__':
    result = run()
    output = Path(__file__).with_name('dynamic-xlsx-controls.json')
    save_new(output, result)
    print(f"{result['case_N']} finite NONHUMAN workbook controls passed; {output}")
