"""All-new human ORIGINALS -> ledger fragment; no sampling or statistics.

Real input is gated by the existing dynamic registry before human bytes open.
This candidate does not register a scope, certify people, or emit engine-ready
sealed_project metadata. Existing pinned parsers retain all original states.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = {
    'support': ('10-closure-20261012/current-validation/statistics-handoff/support.py', 'b418b33ffadbae76ad6e1e8ec0659fe78bcd8ac83d7aa2e3387f442b167b36cf'),
    'xlsx': ('10-closure-20261012/current-validation/statistics-handoff/dynamic_xlsx_projection.py', 'aa18b2fd2ba616d74ec90923f4ac762608412217587af63d809c07ca33531f7b'),
    'reader': ('05-validation/human200-reception-root/bound_xlsx_reader.py', 'a3259e7f87c075ccb117799cbbb86533100e9bb0885167ff3df2b1709d3dc6c1'),
    'reference': ('07-statistics/human200-machine-reference-handoff-sol/handoff.py', '65ec6edce057d8504846f9a368027e81e2f246292399e1fdbc3457d8767cfa30'),
    'admission': ('07-statistics/prospective-dynamic-domain-engine-sol/scope_admission.py', '4a8fa6e195b75538b0b9a090d6549a87f7d9fd33e209ca925a22c872b96e8d4d'),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def binding(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def verify(b):
    require(isinstance(b, dict) and set(b) == {'path', 'bytes', 'sha256'}, 'Exact file binding required')
    require(Path(b['path']).is_absolute() and binding(b['path']) == b, 'Bound file changed')
    return Path(b['path']).resolve()


def strict(text):
    def pairs(items):
        d = {}
        for k, v in items:
            require(k not in d, 'Duplicate JSON key'); d[k] = v
        return d
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def load(b):
    return strict(verify(b).read_text())


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def component(name):
    relative, sha = PINS[name]; path = ROOT / relative
    require(binding(path)['sha256'] == sha, 'Frozen dependency changed: ' + name)
    spec = importlib.util.spec_from_file_location('_all_new_' + name, path)
    result = importlib.util.module_from_spec(spec)
    if name == 'xlsx':
        # Only pure parser functions use support; do not call its old dependencies().
        previous = sys.modules.get('support'); sys.modules['support'] = component('support')
        try:
            spec.loader.exec_module(result)
        finally:
            if previous is None: sys.modules.pop('support', None)
            else: sys.modules['support'] = previous
    else:
        spec.loader.exec_module(result)
    return result


def toy_paths(value):
    """A TOY request must never reference real human originals or policy files."""
    if isinstance(value, dict):
        if set(value) == {'path', 'bytes', 'sha256'}:
            require(Path(value['path']).resolve().is_relative_to(HERE / 'controls'),
                    'TOY inputs must stay inside this candidate controls directory')
        else:
            for child in value.values(): toy_paths(child)
    elif isinstance(value, list):
        for child in value: toy_paths(child)


def registered_context(request, synthetic):
    """No human-original binding is dereferenced until this gate returns."""
    if synthetic:
        toy_paths(request); fixture = load(request['fixture_binding']); toy_paths(fixture)
        require(fixture.get('status') == 'NONHUMAN_fixture_not_actual_draw', 'TOY fixture required')
        draw = load(fixture['draw_binding'])
        require(draw.get('status') == 'NONHUMAN_fixture_not_actual_draw', 'TOY draw identity required')
        return draw['records'], fixture['materials'], fixture['draw_binding'], fixture['common_materials_binding'], {}, None
    require('fixture_binding' not in request, 'TOY fixture prohibited in actual mode')
    admission = component('admission')
    selected = admission.registry_entry({'data_role': 'sealed_project', 'metadata': {'scope': request['scope']}})
    require(selected is not None, 'Existing registered_remaining_pool authority required')
    descriptor, authority = selected
    require(request['scope'].get('kind') == 'registered_remaining_pool', 'Remaining scope only')
    checked = admission.validate_registration(descriptor, request['scope'], synthetic=False)
    require(request['scope'].get('population_N') == checked['target_population_N'] and
            request['scope'].get('frame_ids_sha256') == checked['target_ids_sha256'], 'Scope metadata differs')
    materials = load(descriptor['common_materials'])['records']
    return checked['assigned'], materials, descriptor['original_draw'], descriptor['common_materials'], descriptor, authority


def project(request_path, *, synthetic=False):
    request = strict(Path(request_path).read_text())
    require(request.get('schema') == 'all-new-human-projection-v1', 'Wrong projection request schema')
    require(request.get('synthetic_only') is synthetic, 'Actual/TOY mode mismatch')
    methods = request.get('sources', {})
    require(set(methods) in ({'A', 'B'}, {'reference'}, {'A', 'B', 'reference'}),
            'Use A/B first, a separate reference later, or all three received originals')
    assigned, materials, draw_binding, materials_binding, descriptor, authority = registered_context(request, synthetic)
    ids = [r['unit_id'] for r in assigned]
    require(ids and len(set(ids)) == len(ids), 'Duplicate/empty original assigned IDs')
    require(all(i.startswith('TOY-') is synthetic for i in ids), 'TOY/actual unit identity differs')
    materialby = {r['unit_id']: r['source_bundle_sha256'] for r in materials}
    require(len(materialby) == len(materials) and set(ids) <= set(materialby), 'Material identity coverage differs')
    assignment = load(request['blind_assignment_binding'])
    require(assignment.get('draw_binding') == draw_binding and assignment.get('common_materials_binding') == materials_binding,
            'Blind assignment binds a different original draw/material manifest')
    require(assignment.get('inherited_human_N') == 0, 'Only all-new human cohort is supported')
    require(set(methods) <= set(assignment['methods']) <= {'A', 'B', 'reference'},
            'Requested methods must exist in fixed blind assignments; unused reference may stay frozen')
    if synthetic: toy_paths(assignment)
    xlsx, reader, reference = component('xlsx'), component('reader'), component('reference')
    outputs, proofs, codes, raw_paths = {}, {}, {}, []
    for method in ('A', 'B', 'reference'):
        if method not in methods: continue
        source = methods[method]; rows = assignment['methods'][method]
        require([r.get('unit_id') for r in rows] == ids, 'Assigned source IDs/order differ')
        bids = [r.get('original_blind_id') for r in rows]
        require(len(set(bids)) == len(ids) and all(isinstance(b, str) and b for b in bids), 'Duplicate/empty blind ID')
        for r in rows:
            require(set(r) == {'unit_id', 'original_blind_id', 'source_bundle_sha256', 'material_locator'}, 'Exact blind/source/material/locator fields required')
            require(r['source_bundle_sha256'] == materialby[r['unit_id']], 'Assigned material SHA differs from original draw source')
            require(isinstance(r['material_locator'], str) and r['material_locator'], 'Material locator required')
        raw = source['raw_binding']; raw_paths.append(raw['path'])
        require(len(set(raw_paths)) == len(raw_paths), 'A/B/reference must retain separate original files')
        receipt = None
        if synthetic:
            codes[method] = source['identity_code']
            require(codes[method].startswith('TOY-'), 'Explicit NONHUMAN identity required')
        else:
            receipt = load(descriptor['_ROOT_admitted_submission_receipts'][method])
            require(receipt.get('status') in ('ROOT_reviewed_actual_method_source_for_projection',
                                              'ROOT_reviewed_actual_method_submission') and receipt.get('control_or_synthetic') is False,
                    'Existing registry must bind actual original-source intake or completed reception')
            if receipt['status'] == 'ROOT_reviewed_actual_method_source_for_projection':
                require(receipt.get('joined_projection_sha256') is None,
                        'Source-only intake must not claim a reviewed normalized projection')
            require(receipt.get('registration_id') == request['scope']['registration_id'] and receipt.get('method') == method,
                    'Receipt scope/method differs')
            for key, expected in [('draw_binding', draw_binding), ('original_bytes_binding', raw),
                                  ('common_manual_binding', descriptor['common_manual']), ('common_materials_binding', materials_binding),
                                  ('blind_assignment_binding', request['blind_assignment_binding'])]:
                require(receipt.get(key) == expected, 'Reviewed original mapping differs: ' + key)
            for flag in ('identity_and_freeze_reviewed', 'actual_human_execution_reviewed', 'first_submission_locked'):
                require(receipt.get(flag) is True, 'Actual source review incomplete: ' + flag)
            require(receipt.get('machine_answers_visible') is False and receipt.get('auto_agreement_or_AI_substitution') is False,
                    'Actual human/machine blinding and no substitution required')
            require(receipt.get('independent_initial_before_discussion' if method in ('A', 'B') else 'actual_human_adjudication_reviewed') is True,
                    'Actual initial/adjudication provenance required')
            verify(receipt['human_identity_evidence_binding']); codes[method] = receipt['reviewed_identity_code']
            require(isinstance(codes[method], str) and codes[method].strip(), 'Reviewed human identity missing')
        if method in ('A', 'B'):
            require(source['format'] == 'frozen_dynamic_xlsx', 'New A/B require issued dynamic Excel originals')
            if receipt is not None:
                require(receipt.get('issued_template_binding') == source['template_binding'], 'Reviewed issued template differs')
            template = xlsx.read_workbook(reader, verify(source['template_binding']).read_bytes())
            for index, r in enumerate(rows):
                for offset in range(5):
                    cell = reader.cell(template[xlsx.SHEET]['cells'], 'B' + str(2 + index * 5 + offset))
                    require(cell['resolved_value'] == r['material_locator'], 'Template material locator differs from bound mapping')
            parser_rows = [{k: r[k] for k in ('unit_id', 'original_blind_id', 'source_bundle_sha256')} for r in rows]
            outputs[method], proofs[method] = xlsx.project_dynamic_xlsx(raw, source['template_binding'], parser_rows, reader)
        else:
            require(source['format'] == 'blind_five_slot_jsonl_v1', 'True reference must be a separate original five-slot JSONL')
            original = [strict(line) for line in verify(raw).read_text().splitlines() if line.strip()]
            require(len(original) == len(rows) and [r.get('blind_id') for r in original] == bids,
                    'Reference original must retain every fixed blind ID/order')
            outputs[method] = {r['unit_id']: reference.reference_output(v, r, {codes[method]}) for r, v in zip(rows, original)}
            proofs[method] = {'original': raw, 'original_method_statuses': [r['method_status'] for r in original],
                              'every_assigned_row_retained': True, 'no_AB_agreement_or_AI_reference_generated': True}
        require(set(outputs[method]) == set(ids), 'Original projection omitted assigned rows')
        projected = canonical([{'unit_id': i, 'output': outputs[method][i]} for i in sorted(ids)])
        if receipt is not None and receipt['status'] == 'ROOT_reviewed_actual_method_submission':
            require(projected == receipt['joined_projection_sha256'], 'Projection differs from registry-reviewed original')
        proofs[method]['joined_projection_sha256'] = projected
        proofs[method]['projection_review_pending'] = receipt is None or receipt['status'] == 'ROOT_reviewed_actual_method_source_for_projection'
        proofs[method]['original_bytes_sha256_for_future_input_seal'] = raw['sha256']
    if 'A' in codes: require(codes['A'] != codes['B'], 'A and B require distinct identities')
    records = [{'unit_id': r['unit_id'], 'stratum_id': r['stratum_id'], 'department': r['department'],
                'outputs': {m: outputs[m][r['unit_id']] for m in outputs}} for r in assigned]
    return {'artifact_type': 'all_new_human_ledger_fragment_NOT_engine_admission',
            'data_role': 'synthetic_projection_only' if synthetic else 'received_projection_only',
            'synthetic_only': synthetic, 'source_request_binding': binding(request_path),
            'draw_binding': draw_binding, 'blind_assignment_binding': request['blind_assignment_binding'],
            'inherited_human_N': 0, 'assigned_N': len(ids), 'records': records, 'method_provenance': proofs,
            'identity_codes_from': 'explicit_NONHUMAN_fixture' if synthetic else 'existing_registry_reviewed_receipts',
            'existing_scope_authority': authority, 'scope_or_human_independence_certified_by_this_helper': False,
            'engine_input_metadata_generated': False, 'actual_statistics_executed': False,
            'sample_drawn': False, 'ROOT_registry_written_or_adopted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True); parser.add_argument('--output', required=True)
    parser.add_argument('--synthetic-control', action='store_true'); args = parser.parse_args()
    result = project(args.request, synthetic=args.synthetic_control)
    out = Path(args.output).resolve()
    require(out.is_relative_to(HERE) and not out.exists(), 'Use a new output within this candidate directory')
    with out.open('x') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')


if __name__ == '__main__': main()
