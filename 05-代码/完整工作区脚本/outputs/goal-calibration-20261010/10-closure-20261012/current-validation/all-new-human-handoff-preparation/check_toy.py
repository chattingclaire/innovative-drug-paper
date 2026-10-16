"""Small deterministic NONHUMAN mapping checks, never a sample draw or stats run."""
from pathlib import Path
import copy
import io
import json
import xml.etree.ElementTree as ET
import zipfile
import project_humans as p

HERE = Path(__file__).resolve().parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def save(path, obj):
    with path.open('x') as f: json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')
    return p.binding(path)


def workbook(cells):
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    root = ET.Element('worksheet', xmlns=ns); data = ET.SubElement(root, 'sheetData'); rows = {}
    for address, (kind, value) in cells.items():
        n = ''.join(c for c in address if c.isdigit())
        if n not in rows: rows[n] = ET.SubElement(data, 'row', r=n)
        cell = ET.SubElement(rows[n], 'c', r=address, t=kind)
        if kind == 'inlineStr': ET.SubElement(ET.SubElement(cell, 'is'), 't').text = value
        else: ET.SubElement(cell, 'v').text = str(value)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="独立初判" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', ET.tostring(root, encoding='utf-8'))
    return buffer.getvalue()


def run(run_name='TOY-01'):
    controls = HERE / 'controls'; controls.mkdir(exist_ok=True)
    p.require(run_name.startswith('TOY-') and '/' not in run_name and '\\' not in run_name, 'Use a distinct TOY run name')
    run = controls / run_name; run.mkdir(exist_ok=False)
    ids = ['TOY-UNIT-1', 'TOY-UNIT-2', 'TOY-UNIT-3']
    draw = save(run / 'TOY-draw-metadata.json', {'status': 'NONHUMAN_fixture_not_actual_draw', 'records': [
        {'unit_id': uid, 'stratum_id': 'TOY-h', 'department': 'TOY-department'} for uid in ids]})
    materials = [{'unit_id': uid, 'source_bundle_sha256': str(index + 1) * 64} for index, uid in enumerate(ids)]
    mb = save(run / 'TOY-materials-identity.json', {'status': 'NONHUMAN_material_identity_only', 'records': materials})
    fixture = save(run / 'TOY-fixture.json', {'status': 'NONHUMAN_fixture_not_actual_draw',
        'draw_binding': draw, 'common_materials_binding': mb, 'materials': materials})
    assignment = {'draw_binding': draw, 'common_materials_binding': mb, 'inherited_human_N': 0, 'methods': {}}
    sources = {}
    for method in ('A', 'B', 'reference'):
        assignment['methods'][method] = [{'unit_id': uid, 'original_blind_id': f'TOY-{method}-{i}',
            'source_bundle_sha256': materials[i]['source_bundle_sha256'], 'material_locator': f'TOY-material-{i}'} for i, uid in enumerate(ids)]
        if method == 'reference': continue
        rows = assignment['methods'][method]
        template = {col + '1': ('inlineStr', value) for col, value in zip('ABCDE', ('盲号', '材料', '维度', '值', '理由'))}
        for i, row in enumerate(rows):
            for offset, dim in enumerate(DIMS):
                n = 2 + i * 5 + offset
                template.update({f'A{n}': ('inlineStr', row['original_blind_id']), f'B{n}': ('inlineStr', row['material_locator']), f'C{n}': ('inlineStr', dim)})
        actual = copy.deepcopy(template)
        actual.update({'D2': ('n', '1'), 'E2': ('inlineStr', 'TOY positive'),
                       'D3': ('n', '0'), 'E3': ('inlineStr', 'TOY negative'),
                       'E4': ('inlineStr', '待定：TOY missing evidence'),
                       'D6': ('n', '1'), 'E6': ('inlineStr', 'TOY positive')})
        # Source 2 retains every issued identity row but all five answers blank.
        for n in range(12, 17): actual.update({f'D{n}': ('n', '0'), f'E{n}': ('inlineStr', 'TOY negative')})
        if method == 'B': actual['D2'] = ('n', '0')
        issued = run / f'TOY-{method}-template.xlsx'; issued.write_bytes(workbook(template))
        original = run / f'TOY-{method}-original.xlsx'; original.write_bytes(workbook(actual))
        sources[method] = {'format': 'frozen_dynamic_xlsx', 'raw_binding': p.binding(original),
                           'template_binding': p.binding(issued), 'identity_code': 'TOY-person-' + method}
    raw_ref = []
    for i, assigned in enumerate(assignment['methods']['reference']):
        status = ('completed', 'execution_failure', 'not_returned')[i]
        cells = {dim: {'completion_status': 'filled' if i == 0 else status, 'value': 0 if i == 0 else None,
                       'human_identity_code': 'TOY-person-reference', 'failure_code': 'TOY explicit failure'} for dim in DIMS}
        if i == 0: cells['Ec'].update(completion_status='lawful_null', value=None, null_reason='TOY unresolved')
        raw_ref.append({'blind_id': assigned['original_blind_id'], 'source_bundle_sha256': assigned['source_bundle_sha256'],
                        'method_status': status, 'dimensions': cells})
    refpath = run / 'TOY-reference-original.jsonl'; refpath.write_text(''.join(json.dumps(r) + '\n' for r in raw_ref))
    sources['reference'] = {'format': 'blind_five_slot_jsonl_v1', 'raw_binding': p.binding(refpath), 'identity_code': 'TOY-person-reference'}
    request = {'schema': 'all-new-human-projection-v1', 'synthetic_only': True, 'fixture_binding': fixture,
               'blind_assignment_binding': save(run / 'TOY-blind-assignment.json', assignment), 'sources': sources}
    request_path = run / 'TOY-request.json'; save(request_path, request)
    result = p.project(request_path, synthetic=True); rows = result['records']; cases = []
    assert result['assigned_N'] == 3 and result['inherited_human_N'] == 0
    assert [r['unit_id'] for r in rows] == ids
    assert rows[0]['outputs']['A']['labels'] == {'S': 1, 'E': 0, 'Ec': None, 'I': None, 'F': 1}
    assert rows[0]['outputs']['A']['dimension_status'] == {'I': 'execution_failure'}
    assert rows[1]['outputs']['A'] is None
    assert rows[1]['outputs']['reference']['status'] == 'execution_failure'
    assert rows[2]['outputs']['reference'] is None
    assert rows[0]['outputs']['reference']['labels']['Ec'] is None
    assert result['method_provenance']['A']['slot_completion_counts'] == {'filled': 8, 'lawful_null': 1, 'unfilled': 6}
    assert len(result['method_provenance']['A']['normalized_projection']) == 15
    save(run / 'TOY-ledger-fragment.json', result)
    ab = copy.deepcopy(request); ab['sources'].pop('reference')
    abpath = run / 'TOY-AB-only-request.json'; save(abpath, ab)
    abresult = p.project(abpath, synthetic=True)
    assert all(set(r['outputs']) == {'A', 'B'} for r in abresult['records'])
    ref = copy.deepcopy(request); ref['sources'] = {'reference': ref['sources']['reference']}
    refpath = run / 'TOY-reference-only-request.json'; save(refpath, ref)
    refresult = p.project(refpath, synthetic=True)
    assert all(set(r['outputs']) == {'reference'} for r in refresult['records'])
    assert all(r['outputs']['reference'] == full['outputs']['reference'] for r, full in zip(refresult['records'], rows))
    cases.append({'case': 'zero_inherited_staged_AB_then_reference_preserves_order_NULL_missing_and_failure', 'passed': True})

    def reject(name, alter):
        altered = copy.deepcopy(request); mapping = copy.deepcopy(assignment)
        alter(altered, mapping)
        altered['blind_assignment_binding'] = save(run / (name + '-mapping.json'), mapping)
        path = run / (name + '-request.json'); save(path, altered)
        try: p.project(path, synthetic=True)
        except ValueError as error: cases.append({'case': name, 'passed': True, 'rejection': str(error)})
        else: raise AssertionError('Unexpected acceptance: ' + name)

    reject('duplicate_source_id', lambda q, a: a['methods']['A'][1].update(unit_id=ids[0]))
    reject('duplicate_blind_id', lambda q, a: a['methods']['B'][1].update(original_blind_id='TOY-B-0'))
    reject('wrong_source_id', lambda q, a: a['methods']['A'][0].update(unit_id='TOY-other'))
    reject('material_SHA_mismatch', lambda q, a: a['methods']['A'][0].update(source_bundle_sha256='f' * 64))
    reject('issued_material_locator_mismatch', lambda q, a: a['methods']['A'][0].update(material_locator='TOY-wrong'))
    reject('reference_blind_mapping_mismatch', lambda q, a: a['methods']['reference'][0].update(original_blind_id='TOY-ref-wrong'))
    real = {'schema': 'all-new-human-projection-v1', 'synthetic_only': False,
            'scope': {'kind': 'registered_remaining_pool', 'registration_id': 'UNADOPTED-NO-HUMAN-READ'},
            'sources': {'A': {}, 'B': {}}}
    realpath = run / 'UNADOPTED-real-request-no-originals.json'; save(realpath, real)
    try: p.project(realpath)
    except ValueError as error:
        assert 'Scope has not been ROOT-adopted' in str(error)
        cases.append({'case': 'empty_existing_registry_rejects_before_source_binding_or_human_bytes', 'passed': True, 'rejection': str(error)})
    else: raise AssertionError('Actual empty registry must reject')
    return {'status': 'NONHUMAN_finite_mapping_checks_only', 'case_N': len(cases), 'all_passed': True,
            'cases': cases, 'actual_human_originals_read': 0, 'policy_bodies_read': 0,
            'sampling_or_model_calls': 0, 'statistics_engine_executed': False, 'formal_registration_or_adoption': False,
            'fixture_root': str(run), 'dependency_files_unchanged': all(p.binding(p.ROOT / path)['sha256'] == sha for path, sha in p.PINS.values())}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default='TOY-01'); parser.add_argument('--result', default='toy-check-results.json')
    args = parser.parse_args(); result_path = (HERE / args.result).resolve()
    p.require(result_path.parent == HERE and not result_path.exists(), 'Use a new result filename in this directory')
    result = run(args.run_name); save(result_path, result)
    print(json.dumps({'case_N': result['case_N'], 'all_passed': result['all_passed'], 'actual_statistics_executed': False}))
