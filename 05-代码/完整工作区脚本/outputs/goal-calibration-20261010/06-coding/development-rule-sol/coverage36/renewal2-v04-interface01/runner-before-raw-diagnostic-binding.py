"""Fixed development inference with freezing before coder imports.

Run with python -B. A run creates a new directory and refuses to overwrite any
run. First output is hashed and sealed before the separate evaluator is used.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import types

VERSION = 'development-rule-sol-implementation04-renewal2-interface01'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
EXPECTED_N = None
AUTHORIZED_SOURCE_BY_N = {
    2: '0abd018875edb2ae41cc4a7aff3c7ba5d4194895d575517fd51ea5261983c799',
}
AUTHORIZED_DESIGN_SHA256 = 'ff022f5a9d803ed28befedd5a1218011ed06dfab4493c9ac2a04c4ce9f44482b'
INFERENCE_FILES = ('runner.py', 'source_packet.py', 'evidence.py', 'relations.py', 'dimensions.py')
CODER_MODULES = ('source_packet', 'evidence', 'relations', 'dimensions')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_jsonl(path, rows):
    with Path(path).open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')


def load_frozen_coders(implementation, code):
    """Execute audited, frozen source bytes without importing an earlier pyc."""
    bindings = {Path(item['path']).stem: item for item in code}
    if any(name in sys.modules for name in CODER_MODULES):
        raise ValueError('coder modules were loaded before the inference freeze')
    loaded = {}
    for name in CODER_MODULES:
        path = implementation / (name + '.py')
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != bindings[name]['sha256']:
            raise ValueError('coder changed between freeze and import: ' + name)
        module = types.ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = ''
        sys.modules[name] = module
        try:
            exec(compile(payload, str(path), 'exec'), module.__dict__)
        except BaseException:
            del sys.modules[name]
            raise
        loaded[name] = module
    return loaded


def technical_diagnostics(rows, predictions, errors):
    """Retain all five slots only for a complete authorized fixture failed attempt.

    Technical failures have no substitute rule value. Original decisions,
    including rule nulls, remain verbatim and do not become valid metrics.
    """
    if len(rows) != EXPECTED_N or len(predictions) != EXPECTED_N:
        return None
    source_ids = [row['id'] for row in rows]
    if len(set(source_ids)) != EXPECTED_N or source_ids != [row['id'] for row in predictions]:
        return None
    global_errors = [error for error in errors if 'id' not in error]
    sources = {row['id']: row for row in rows}
    result = []
    for prediction in predictions:
        record_errors = prediction['implementation_errors']
        decisions = prediction.get('decisions')
        for dimension in DIMENSIONS:
            decision = decisions.get(dimension) if isinstance(decisions, dict) else None
            failed = bool(global_errors or record_errors or decision is None)
            result.append({
                'id': prediction['id'], 'dimension': dimension,
                'source_record': sources[prediction['id']],
                'source_text': sources[prediction['id']].get('text', ''),
                'source_contexts': sources[prediction['id']].get('contexts', []),
                'status': 'technical_failure' if failed else 'retained_rule_decision',
                'technical_failure': failed,
                'rules_null': not failed and decision.get('value') is None,
                'rule_not_executed': decision is None,
                'rule_value': decision.get('value') if isinstance(decision, dict) else None,
                'retained_rule_decision': decision,
                'implementation_errors': record_errors,
                'global_implementation_errors': global_errors,
                'comparison_eligible': False,
                'interpretation': 'failed_attempt_diagnostic_only_not_valid_comparison_metrics',
            })
    return result


def raw_failure_diagnostics(source, errors):
    """Keep source-only technical slots after full loader failure.

    These raw rows never enter the rule engine. The original predictions and
    unsuccessful execution remain intact; None here is no executed rule value.
    """
    raw = [json.loads(line) for line in Path(source).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(raw) != EXPECTED_N or any(not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] for row in raw):
        raise ValueError('raw failure diagnostic source identities/count unavailable')
    if len({row['id'] for row in raw}) != EXPECTED_N:
        raise ValueError('raw failure diagnostic source identities are not unique')
    return [{'id': row['id'], 'dimension': dimension, 'source_record': row,
             'source_text': row.get('text'), 'source_contexts': row.get('contexts'),
             'status': 'technical_failure', 'technical_failure': True,
             'rule_not_executed': True, 'rules_null': False,
             'retained_rule_decision': None, 'rule_value': None,
             'implementation_errors': [], 'global_implementation_errors': errors,
             'comparison_eligible': False,
             'interpretation': 'source_only_structural_failure_slot_not_a_rule_null_or_zero'}
            for row in raw for dimension in DIMENSIONS]


def main():
    global EXPECTED_N
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--manual', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--source-sha256', required=True, help='authorized fixture content SHA; scope gate only')
    parser.add_argument('--expected-n', required=True, type=int)
    parser.add_argument('--approved-output-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    source, manual, manifest = (Path(v).resolve() for v in (args.source, args.manual, args.manifest))
    root, out = (Path(v).resolve() for v in (args.approved_output_root, args.out))
    implementation = Path(__file__).resolve().parent
    if root not in out.parents or out.exists():
        raise ValueError('output must be a new child directory of the explicitly approved root')
    if digest(manifest) != AUTHORIZED_DESIGN_SHA256:
        raise ValueError('use the explicitly authorized two-record source design')
    design = json.loads(manifest.read_text(encoding='utf-8'))
    if source != Path(design['source']['path']).resolve() or manual != Path(design['manual']['path']).resolve():
        raise ValueError('source/manual paths differ from the frozen source design')
    if design['n'] != args.expected_n or design['dimension_n'] != args.expected_n * len(DIMENSIONS):
        raise ValueError('source design scope differs from fixed two-record execution')
    if digest(manual) != design['manual']['sha256'] or digest(source) != design['source']['sha256']:
        raise ValueError('source/manual digest differs from authorized design')
    resource = Path(design['resource']['path']).resolve()
    if digest(resource) != design['resource']['sha256']:
        raise ValueError('source resource digest differs from authorized design')
    resource_data = json.loads(resource.read_text(encoding='utf-8'))
    extra = [{'path': str(resource), 'sha256': design['resource']['sha256'], 'role': 'complete_source_text_and_geometry_resource'}]
    source_seal = Path(design['source_seal']).resolve()
    extra.append({'path': str(source_seal), 'sha256': digest(source_seal), 'role': 'supplied_source_only_delivery_seal'})
    snapshot = Path(resource_data['snapshot']).resolve()
    extra.append({'path': str(snapshot), 'sha256': resource_data['snapshot_sha256'], 'role': 'original_source_pdf_integrity_only'})
    for asset in design['source_page_assets']:
        extra.append({'path': str(Path(asset['path']).resolve()), 'sha256': asset['sha256'], 'role': 'original_source_page_asset', 'physical_page': asset['physical_page'], 'source_pdf_sha256': asset['source_pdf_sha256']})
    if len({entry['path'] for entry in extra}) != len(extra):
        raise ValueError('duplicate source material binding')
    for entry in extra:
        material = Path(entry['path'])
        if digest(material) != entry['sha256']:
            raise ValueError('source material digest mismatch: ' + entry['path'])
        entry['bytes'] = material.stat().st_size
    if args.expected_n not in AUTHORIZED_SOURCE_BY_N or args.source_sha256 != AUTHORIZED_SOURCE_BY_N[args.expected_n]:
        raise ValueError('use the explicitly authorized two-record common-source material binding')
    EXPECTED_N = args.expected_n
    if digest(source) != args.source_sha256:
        raise ValueError('source differs from explicitly authorized development fixture')
    code = [{'path': str(implementation / name), 'sha256': digest(implementation / name)}
            for name in INFERENCE_FILES]
    inputs = {'source_path': str(source), 'source_sha256': digest(source),
              'manual_path': str(manual), 'manual_sha256': digest(manual),
              'fixture_manifest_path': str(manifest), 'fixture_manifest_sha256': digest(manifest)}
    out.mkdir(parents=False)
    freeze = {'status': 'frozen_before_coder_import_and_inference', 'runtime_version': VERSION,
              'created_at_utc': now(), 'scope': 'two_updated_common_material_records_only_without_reference_comparison',
              'expected_n': args.expected_n, 'implementation_files': code, 'extra_material_files': extra, **inputs,
              'reference_input': None, 'no_legacy_runtime_import': True,
              'coder_role': 'AI_rule_runtime',
              'interpretation': '开发诊断；不是真人参照信度或独立总体效度检验'}
    write_json(out / 'freeze.json', freeze)
    reads = []
    allowed = {source, manual, manifest} | {Path(c['path']) for c in code}
    allowed.update(Path(entry['path']) for entry in extra)
    stdlib = Path(os.__file__).resolve().parent

    def audit(event, params):
        if event != 'open' or not params or isinstance(params[0], int):
            return
        target = Path(os.fsdecode(params[0])).resolve()
        mode = params[1] if len(params) > 1 else None
        flags = params[2] if len(params) > 2 else 0
        writing = isinstance(mode, str) and any(x in mode for x in 'wax+')
        writing |= bool(flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if out not in target.parents:
                raise PermissionError('inference write outside its new run directory')
        else:
            if target.name == 'reference.jsonl':
                raise PermissionError('development reference is forbidden during inference')
            if target not in allowed and out not in target.parents and stdlib not in target.parents:
                raise PermissionError('unapproved inference read: ' + str(target))
            reads.append(str(target))

    sys.addaudithook(audit)
    rows = []
    predictions = []
    errors = []
    started = now()
    try:
        modules = load_frozen_coders(implementation, code)
        load_fixture = modules['source_packet'].load_fixture
        semantic_unit = modules['source_packet'].semantic_unit
        validate_decisions = modules['evidence'].validate_decisions
        RelationView = modules['relations'].RelationView
        judge = modules['dimensions'].judge
        if tuple(modules['evidence'].DIMENSIONS) != DIMENSIONS:
            raise ValueError('coder dimension order differs from the sealed protocol')
        rows = load_fixture(source, manifest)
        if len(rows) != args.expected_n:
            raise ValueError('record count differs from authorized scope')
        # Manual bytes are verified by source loader; this module's declared
        # rules implement v1.1 rather than interpreting manual as executable code.
        for row in rows:
            result = {'id': row['id'], 'labels': None, 'decisions': None,
                      'relation_traces': [], 'implementation_errors': []}
            try:
                unit = semantic_unit(row)
                view = RelationView(unit)
                decisions = judge(view)
                validate_decisions(unit, decisions)
                result.update(labels={d: decisions[d]['value'] for d in DIMENSIONS},
                              decisions=decisions, relation_traces=view.traces(),
                              material_requests=view.material_requests)
            except Exception as error:
                detail = {'id': row['id'], 'type': type(error).__name__, 'message': str(error),
                          'traceback': traceback.format_exc()}
                errors.append(detail)
                result['implementation_errors'].append(detail)
            predictions.append(result)
    except Exception as error:
        errors.append({'type': type(error).__name__, 'message': str(error),
                       'traceback': traceback.format_exc()})
    pred_path = out / 'predictions.jsonl'
    write_jsonl(pred_path, predictions)
    # Recheck sources and executable modules after inference, before sealing.
    stale = [c['path'] for c in code if digest(c['path']) != c['sha256']]
    for name in ('source', 'manual', 'fixture_manifest'):
        if digest(inputs[name + '_path']) != inputs[name + '_sha256']:
            stale.append(inputs[name + '_path'])
    for entry in extra:
        if digest(entry['path']) != entry['sha256']:
            stale.append(entry['path'])
    if stale:
        errors.append({'type': 'ChangedDependency', 'paths': stale})
    complete = not errors and len(predictions) == args.expected_n
    technical = technical_diagnostics(rows, predictions, errors) if not complete else None
    if not complete and technical is None:
        try:
            technical = raw_failure_diagnostics(source, errors)
        except Exception as diagnostic_error:
            errors.append({'type': 'RawFailureDiagnosticUnavailable', 'message': str(diagnostic_error)})
    technical_binding = {'technical_diagnostics_path': None, 'technical_diagnostics_sha256': None,
                         'technical_diagnostics_n': 0, 'technical_failure_dimension_n': 0}
    if technical is not None:
        technical_path = out / 'technical-diagnostics.jsonl'
        write_jsonl(technical_path, technical)
        technical_binding.update(technical_diagnostics_path=str(technical_path),
                                 technical_diagnostics_sha256=digest(technical_path),
                                 technical_diagnostics_n=len(technical),
                                 technical_failure_dimension_n=sum(row['technical_failure'] for row in technical))
    execution = {'status': 'completed' if complete else 'failed_development_attempt',
                 'started_at_utc': started, 'finished_at_utc': now(),
                 'attempted_record_n': len(rows), 'output_record_n': len(predictions),
                 'implementation_errors': errors, 'read_paths': sorted(set(reads)),
                 'reference_was_input': False, 'runtime_version': VERSION,
                 'comparison_eligible': complete, **technical_binding}
    write_json(out / 'execution.json', execution)
    seal = {'status': 'sealed_development_predictions' if complete else 'sealed_failed_development_attempt',
            'sealed_at_utc': now(), 'prediction_path': str(pred_path),
            'prediction_sha256': digest(pred_path), 'prediction_n': len(predictions),
            'decision_n': sum(len(r['labels']) for r in predictions if isinstance(r['labels'], dict)),
            'implementation_files': code, 'runtime_version': VERSION, 'extra_material_files': extra, **inputs,
            'freeze_sha256': digest(out / 'freeze.json'), 'execution_sha256': digest(out / 'execution.json'),
            'no_reference_read': not any(Path(p).name == 'reference.jsonl' for p in reads),
            'complete': complete, 'implementation_error_n': len(errors),
            'comparison_eligible': complete, **technical_binding}
    write_json(out / 'seal.json', seal)
    print(json.dumps({k: seal[k] for k in ('status', 'prediction_n', 'decision_n', 'prediction_sha256', 'implementation_error_n', 'technical_diagnostics_n')}, ensure_ascii=False))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
