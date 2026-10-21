"""Freeze and draw a smaller human probability sample; copy source-only materials."""
import hashlib
import json
import random
import shutil
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
OUT = Path(__file__).resolve().parents[1]
OLD = ROOT / '09-delivery/formal800-human-final-release-v2-20261010-sol'
PRIVATE = ROOT / '05-validation/full800-common-v15-prerelease-sol/coordinator-private'
ALLOC = ROOT / '02-methods/human-small-sample-prospective-allocation-root/allocation-comparison.json'
MACHINE = ROOT / '06-coding/native-full4481-v1-sol/run-manifest.json'
SEED = 2026101001


def bind(p):
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_json(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def verified_copy(source, target, expected=None):
    actual = bind(source)
    if expected and (actual['sha256'] != expected['sha256'] or actual['bytes'] != expected['bytes']):
        raise ValueError(f'Source binding mismatch: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as f:
        f.write(source.read_bytes())
    if bind(target)['sha256'] != actual['sha256']:
        raise ValueError('Copy changed source bytes')
    return {'source': actual, 'destination': bind(target)}


def main():
    if (OUT / 'coordinator-private/pre-draw-freeze.json').exists():
        raise RuntimeError('Do not rerun over an already frozen draw')
    allocation = json.loads(ALLOC.read_text())
    candidate = next(x for x in allocation['candidates'] if x['proposed_records_per_coder'] == 200)
    mapping = json.loads((PRIVATE / 'mapping.json').read_text())['records']
    old_draw = json.loads((PRIVATE / 'draw-contract.json').read_text())
    release = json.loads((OLD / 'release.json').read_text())
    machine = json.loads(MACHINE.read_text())
    pages = json.loads((OLD / 'material-pages-index.json').read_text())['pages']
    if len(mapping) != 800 or len({r['source_id'] for r in mapping}) != 800:
        raise ValueError('Old draw/mapping not uniquely800')
    by_stratum = {}
    for row in mapping:
        by_stratum.setdefault(row['stratum'], []).append(row)
    for row in candidate['strata']:
        old_row = next(s for s in old_draw['selected_strata'] if s['stratum'] == row['stratum'])
        actual_ids = sorted(r['source_id'] for r in by_stratum[row['stratum']])
        if actual_ids != old_row['selected_ids_sorted'] or len(actual_ids) != row['old_n_h']:
            raise ValueError('Original member mapping differs from frozen stratum draw')
    source_jsonl = Path(machine['source_jsonl']['path'])
    if bind(source_jsonl)['sha256'] != machine['source_jsonl']['sha256']:
        raise ValueError('Current machine source binding mismatch')
    for key in ['manual', 'execution_prompt', 'execution_protocol']:
        current = bind(Path(release[key]['path']))
        if current['sha256'] != release[key]['sha256'] or current['bytes'] != release[key]['bytes']:
            raise ValueError('Human common freeze binding mismatch')
    if release['manual']['sha256'] != machine['manual']['sha256'] or release['execution_prompt']['sha256'] != machine['execution_prompt']['sha256']:
        raise ValueError('Human and current machine concept inputs differ')
    frozen_inputs = [bind(p) for p in [ALLOC, PRIVATE/'mapping.json', PRIVATE/'draw-contract.json',
        OLD/'seal.json', OLD/'release.json', OLD/'material-pages-index.json',
        OLD/'shared-source/delivery-source-assets-index.json', MACHINE, Path(__file__)]]
    freeze = {'artifact_type': 'prospective_human200_pre_draw_freeze',
              'at_utc': datetime.now(timezone.utc).isoformat(), 'sample_records_per_coder': 200,
              'sampling_seed': SEED, 'seed_is_not_model_seed': True,
              'algorithm': 'Sorted stratum names; sorted original800 stratum member IDs; Python Random(seed).sample without replacement at fixed new_n_h.',
              'fixed_allocation': candidate, 'input_bindings': frozen_inputs,
              'human_budget_answer_received': False, 'workload_status': 'reversible200 preparation assumption; not a user-confirmed limit',
              'new_human_answers_seen': 0, 'new_machine_predictions_used_for_selection': 0,
              'old800_human_answers_or_distribution_confirmed': False,
              'inferential_scope': {'remaining': '120-record probability validation of the1444 remaining pool',
                                    'exposed': '80-record supplementary fixed-corpus audit of the3037 exposed pool',
                                    'combined': 'Weighted fixed4481 finite-corpus audit; not all unseen generalization'},
              'selection_or_size_uses_passing_scores': False,
              'project_acceptance_targets_changed': False,
              'existing800_packages_or_machine_stability_plan_changed': False,
              'sufficiency_for_five_dimensions_claimed': False}
    # Must precede actual random member selection.
    write_json(OUT/'coordinator-private/pre-draw-freeze.json', freeze)
    rng = random.Random(SEED)
    selected = []
    for row in sorted(candidate['strata'], key=lambda x: x['stratum']):
        pool = sorted(by_stratum[row['stratum']], key=lambda x: x['source_id'])
        for original in rng.sample(pool, row['new_n_h']):
            selected.append({**original, 'original800_n_h': original['n_h'],
                'n_h': row['new_n_h'], 'pi_exact': row['overall_pi_exact'],
                'weight_exact': row['overall_weight_exact'],
                'conditional_new_pi_exact': row['conditional_new_pi_exact'],
                'pi': float(Fraction(row['overall_pi_exact'])), 'weight': float(Fraction(row['overall_weight_exact']))})
    ids = {x['source_id'] for x in selected}
    if len(selected) != 200 or len(ids) != 200 or Counter(x['domain'] for x in selected) != {'remaining':120,'exposed':80}:
        raise ValueError('New draw counts mismatch')
    original_source = {}
    with source_jsonl.open('rb') as f:
        for line in f:
            raw = line.rstrip(b'\r\n')
            sid = json.loads(raw)['source_record']['id']
            if sid in ids:
                original_source[sid] = raw
    if set(original_source) != ids:
        raise ValueError('Current full source is missing selected human IDs')
    draw = {'artifact_type': 'actual_human200_probability_subsample', 'actual_draw_completed': True,
            'at_utc': datetime.now(timezone.utc).isoformat(), 'pre_draw_freeze': bind(OUT/'coordinator-private/pre-draw-freeze.json'),
            'records': selected, 'source_ids_sorted': sorted(ids),
            'human_answers_created': 0, 'human_validation_complete': False,
            'A_B_old_blind_ids_preserved': True, 'new800_weights_not_reused': True,
            'by_department': dict(Counter(x['department'] for x in selected)),
            'by_domain': dict(Counter(x['domain'] for x in selected))}
    write_json(OUT/'coordinator-private/draw-and-mapping.json', draw)
    asset_index = json.loads((OLD/'shared-source/delivery-source-assets-index.json').read_text())
    copy_ledger = []
    safe_assets = []
    for entry in asset_index['files']:
        old_file = Path(entry['prepared_absolute_path'])
        dest = OUT/'shared-source/source-files'/old_file.name
        copy_ledger.append(verified_copy(old_file, dest, entry))
        safe_assets.append({'sha256':entry['sha256'], 'bytes':entry['bytes'],
            'prepared_relative_path':str(dest.relative_to(OUT)), 'resource_kinds':entry['resource_kinds'],
            'image_pixels':entry.get('image_pixels')})
    write_json(OUT/'shared-source/delivery-source-assets-index.json', {'files':safe_assets,'actual_reading_or_use_claimed':False})
    common_names = {'manual':'manual.txt','execution_prompt':'execution-prompt.txt','execution_protocol':'common-execution-protocol.txt'}
    page_lookup = {(p['side'],p['blind_id']):p for p in pages}
    build_data = {'sample_N':200, 'dimensions':['S','E','Ec','I','F'], 'sides':{}}
    materials = []
    for side in ['A','B']:
        coder = OUT/('coder-'+side)
        side_records = sorted(selected,key=lambda x:x[side+'_blind_id'])
        for key,name in common_names.items():
            copy_ledger.append(verified_copy(Path(release[key]['path']),coder/name,release[key]))
        body_rows = []
        for record in side_records:
            blind = record[side+'_blind_id']
            page = page_lookup[side,blind]
            source = OLD/page['json_relative_path']
            raw = source.read_bytes()
            if raw != original_source[record['source_id']] or hashlib.sha256(raw).hexdigest() != page['source_bundle_sha256']:
                raise ValueError('Human material does not match current full machine source bytes')
            copy_ledger.append(verified_copy(source,coder/'materials'/(blind+'.json')))
            html = (OLD/page['html_relative_path']).read_text()
            changes = [
                ('完整v15材料（pre-release）','完整政策材料'),
                ('完整v15材料</h1>','完整政策材料</h1>'),
                ('<p>pre-release。ROOT开发结果和联合freeze完成前，不分发正式判读。</p>', '<p>请按共同手册独立判断五个维度，证据不足时记录具体待定原因。</p>'),
                ('候选手册原文</a>','共同编码手册</a>')]
            for before,after in changes:
                if html.count(before) != 1:
                    raise ValueError('Unexpected material-page presentation header')
                html = html.replace(before,after,1)
            target=coder/'materials'/(blind+'.html')
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as f:f.write(html)
            bundle=json.loads(raw)
            body_rows.append({'blind_id':blind,'body':bundle['source_record']['text']})
            materials.append({'side':side,'blind_id':blind,'source_bundle_sha256':page['source_bundle_sha256'],
                              'source_bundle_bytes':len(raw),'html':bind(target),'json':bind(coder/'materials'/(blind+'.json')),
                              'source_file_SHAs':page['source_file_SHAs'],'source_body_or_context_modified':False,
                              'page_header_only_updated':True})
        guide=('本次准备表包含200条政策材料，每条分别判断S、E、Ec、I、F，共1000行。\n'
            '先阅读manual.txt和共同执行说明，再点A列盲号打开完整材料。B列保留原条款全文，长条款须在完整材料页阅读。\n'
            'D列直接填数值0或1，E列写实际原文依据和判断理由。不加真人复核栏。\n'
            '材料缺失或确实无法判断时，D留空，E以“待定：”开头写明具体原因及所缺材料。只有普通空白或只写“待定：”不算完成。不要把未知填0。\n'
            '每个维度分别判断。不要看另一位编码者或机器答案，不使用AI代填本次真人初判。独立初判完成后保存原文件，再另存讨论或裁定版本。\n'
            '保留本方coder目录与shared-source的相对位置。仅向本方编码者提供本方包。返回填写后的XLSX，并说明两位是否分别独立完成及是否事先讨论。\n'
            '盲号沿用既有随机编号，编号有间隔不表示缺材料。本包没有预填答案。200条是工作量方案，其统计信息量在实际判读后核查。\n')
        with (coder/'填写说明.txt').open('x') as f:f.write(guide)
        build_data['sides'][side]=body_rows
    sequences = [[r['blind_id'] for r in build_data['sides'][s]] for s in ['A','B']]
    if len({tuple(r[side+'_blind_id'] for r in sorted(selected,key=lambda x:x['A_blind_id'])) for side in ['A','B']}) != 2:
        raise ValueError('A/B blind identifiers unexpectedly identical')
    A_order=[x['source_id'] for x in sorted(selected,key=lambda x:x['A_blind_id'])]
    B_order=[x['source_id'] for x in sorted(selected,key=lambda x:x['B_blind_id'])]
    if A_order == B_order:
        raise ValueError('A/B presentation order unexpectedly identical')
    write_json(OUT/'_build/workbook-input.json', build_data)
    write_json(OUT/'material-pages-index.json', {'material_page_N':400,'pages':materials})
    write_json(OUT/'_build/copy-ledger.json', {'copies':copy_ledger,'shared_asset_N':len(safe_assets)})
    print(json.dumps({'status':'actual200_draw_and_source_materials_prepared','records_per_coder':200,
        'remaining_N':120,'exposed_N':80,'A_B_source_order_different':True,
        'machine_source_byte_identity_verified_records':200,'human_results':0},ensure_ascii=False))


if __name__ == '__main__':main()
