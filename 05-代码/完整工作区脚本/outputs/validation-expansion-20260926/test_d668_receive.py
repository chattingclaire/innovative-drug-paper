"""Synthetic-only administrative QA. Reads code dependencies, never study labels."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('d668_admin_synthetic', HERE / 'd668_receive.py')
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else admin.encoded(value)
    path.write_bytes(data)
    return {'path': str(path), 'sha256': admin.sha(data), 'byte_count': len(data)}


def fixture(root):
    root = root.resolve()
    release = root / 'synthetic-release'
    freeze = {'status': 'frozen_for_D668_supplementary_AI_content_analysis', 'phase': 'D668',
              'sampling_seed': 2026092607, 'sample_budget': 668,
              'protocol_version': 'SYNTHETIC-ONLY-v1', 'release_directory': str(release), 'files': {}}
    source = {'admin_receiver': HERE / 'd668_receive.py',
              'results_bridge': HERE / 'V600-frozen-inputs/results_bridge.py',
              'legacy_results_helpers': HERE / 'V600-frozen-inputs/legacy_results_helpers.py'}
    for key, path in source.items():
        data = path.read_bytes()
        freeze['files'][key] = {'path': str(path), 'sha256': admin.sha(data), 'byte_count': len(data)}
    for key in admin.STATIC_DOCS:
        freeze['files'][key] = put(root / 'synthetic-inputs' / (key + '.md'), b'SYNTHETIC QA ONLY\n')
    outputs = {}
    for coder in ('A', 'C'):
        for key, name in admin.STATIC_DOCS.items():
            rel = f'agent-{coder}/{name}'
            outputs[rel] = put(release / rel, b'SYNTHETIC QA ONLY\n')['sha256']
        for batch in range(1, 28):
            packet = {'protocol_version': freeze['protocol_version'], 'purpose': 'supplementary_AI_content_analysis',
                      'batch': batch, 'total_batches': 27,
                      'rows': [{'id': f'D668-{i:04d}', 'text': 'SYNTHETIC QA ONLY'}
                               for i in range((batch - 1) * 25 + 1, min(batch * 25, 668) + 1)]}
            rel = f'agent-{coder}/材料-{batch:02d}.json'
            outputs[rel] = put(release / rel, packet)['sha256']
    outputs['抽样清单-研究者.json'] = put(release / '抽样清单-研究者.json', {'synthetic': True})['sha256']
    freeze_path = root / 'synthetic-freeze.json'
    freeze_sha = put(freeze_path, freeze)['sha256']
    seal = {'status': 'drawn', 'release_status': 'ready_for_blind_review', 'phase': 'D668',
            'freeze_manifest_sha256': freeze_sha, 'input_hashes': {k: v['sha256'] for k, v in freeze['files'].items()},
            'n': 668, 'N_star': 3393, 'output_files': outputs}
    put(release / '封存信息.json', seal)
    return freeze_path, release


def result(release, coder, batch):
    raw = (release / f'agent-{coder}/材料-{batch:02d}.json').read_bytes()
    packet = json.loads(raw)
    dims = ('S', 'E', 'Ec', 'I', 'F')
    return {'coder': coder, 'identity': {'kind': 'AI', 'name': 'SYNTHETIC QA ONLY'},
            'protocol_version': packet['protocol_version'], 'protocol_acknowledged': True,
            'completed_at': datetime.now(timezone.utc).isoformat(), 'input_packet_sha256': admin.sha(raw),
            'batch': batch, 'total_batches': 27, 'rule_questions': [],
            'rows': [{'id': row['id'], 'labels': {d: 0 for d in dims},
                      'dimension_reasons': {d: '合成校验，不是研究结果' for d in dims},
                      'evidence': '合成证据', 'rationale': '合成判断', 'material_issue': '无',
                      'fairness_subtypes': [], 'innovation_subtypes': [], 'safety_quality_basis': 'no_quality_basis',
                      'input_assessment': {'status': 'sufficient', 'basis': '合成材料'}} for row in packet['rows']]}


def run():
    checks = []
    with tempfile.TemporaryDirectory(prefix='d668-admin-synthetic-') as tmp:
        root = Path(tmp)
        freeze, release = fixture(root)
        receipts = root / 'synthetic-receipts'
        report = admin.receive(freeze, release, receipts)
        assert not report['structural_errors'] and report['performance_computed'] is False
        assert all(v['validated_rows'] == 0 for v in report['summary'].values())
        checks.append('empty_submission_inventory_is_administrative_only')
        for coder in ('A', 'C'):
            for batch in range(1, 28):
                put(release / f'agent-{coder}/结果-{batch:02d}.json', result(release, coder, batch))
        report = admin.receive(freeze, release, receipts)
        assert not report['structural_errors']
        assert all(v['validated_rows'] == 668 and len(v['validated_batches']) == 27 for v in report['summary'].values())
        checks.append('all_54_batches_1336_synthetic_rows_validated')
        original = (receipts / 'agent-A/结果-01.json').read_bytes()
        repeat = admin.receive(freeze, release, receipts)
        assert not repeat['structural_errors']
        assert (receipts / 'agent-A/结果-01.json').read_bytes() == original
        checks.append('repeat_reception_preserves_first_bytes')
        current = release / 'agent-A/结果-01.json'
        current.write_bytes(current.read_bytes() + b' ')
        changed = admin.receive(freeze, release, receipts)
        assert changed['structural_errors'] and (receipts / 'agent-A/结果-01.json').read_bytes() == original
        checks.append('source_change_rejected_first_bytes_retained')
    with tempfile.TemporaryDirectory(prefix='d668-admin-invalid-synthetic-') as tmp:
        root = Path(tmp); freeze, release = fixture(root); receipts = root / 'synthetic-receipts'
        doc = result(release, 'A', 1); doc['rows'][0]['labels']['I'] = None
        file = release / 'agent-A/结果-01.json'; put(file, doc)
        report = admin.receive(freeze, release, receipts)
        assert report['structural_errors'] and (receipts / 'agent-A/结果-01.json').read_bytes() == file.read_bytes()
        checks.append('invalid_labels_archived_before_rejection_never_imputed')
        context = admin.prepare(freeze, release)
        variants = []
        bad = result(release, 'A', 1); bad['rows'].reverse(); variants.append(bad)
        bad = result(release, 'A', 1); bad['completed_at'] = '2026-09-26T00:00:00'; variants.append(bad)
        bad = result(release, 'A', 1); bad['identity']['kind'] = 'human'; variants.append(bad)
        bad = result(release, 'A', 1); bad['rows'].pop(); variants.append(bad)
        bad = result(release, 'A', 1); bad['rows'][0]['input_assessment']['status'] = 'context_insufficient'; variants.append(bad)
        bad = result(release, 'A', 1); bad['rows'][0]['labels']['F'] = 1; variants.append(bad)
        for bad in variants:
            try: admin.validate_submission(admin.encoded(bad), 'agent-A/结果-01.json', context)
            except admin.AdminError: pass
            else: raise AssertionError('invalid synthetic document accepted')
        checks.append('order_timezone_AI_identity_missing_rows_assessment_subtype_rejected')
        packet = release / 'agent-C/材料-01.json'; packet.write_bytes(packet.read_bytes() + b' ')
        try: admin.prepare(freeze, release)
        except admin.AdminError: pass
        else: raise AssertionError('packet tamper accepted')
        checks.append('sealed_material_tamper_rejected')
    return {'status': 'passed', 'synthetic_only': True, 'real_sampling_performed': False,
            'real_labels_read': False, 'created_at': datetime.now(timezone.utc).isoformat(),
            'checks': checks, 'receiver_sha256': admin.sha((HERE / 'd668_receive.py').read_bytes()),
            'test_source_sha256': admin.sha(Path(__file__).read_bytes())}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); report = run()
    with args.output.open('xb') as handle: handle.write(admin.encoded(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
