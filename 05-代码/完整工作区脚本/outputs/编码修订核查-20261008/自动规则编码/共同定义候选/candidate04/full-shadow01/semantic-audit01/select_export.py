#!/usr/bin/env python3
"""Frozen, one-attempt development coverage selection; no model execution.

Labels and selection metadata are written only to sealed/selection.json.
Source text is exported only for selected, fully bound nonprotected records.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'outputs').is_dir())
SHADOW = HERE.parent
BINDING_SHA = '157cd723de676a3009de046bf6bd5b2868bf9a384b384721ab5e82a72d9d810b'
DESIGN_SHA = '071e8f229a6b37f59744480a42d36408ed72adf13fbcaf2672f2749ccf6bcd8e'
OLD = ROOT / 'outputs/编码修订核查-20261008/自动规则编码/候选方案/rules39-five-relations-candidate01/full-run01/all_predictions_material_v14_shadow_MACHINE_RAW_NO_SEMANTIC_READING.jsonl'
OLD_SHA = '8d771b5f68f2f23f860bcdebdb4ffce4b5905053ea3757ce263dafa15b6fc2dd'
GROUP = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
GROUP_SHA = 'e35c0b3643093ecc3a41dfd0c3cf50aca27a43aea7fa2b4594d5cf7857ce3fb2'
SEED = 2026100901
DEPTS = ('NMPA', 'NHSA', 'NHC')
BUCKETS = (('I_changed', 6), ('F_changed', 6), ('I_unchanged_zero', 3),
           ('F_unchanged_zero', 3), ('current_IF_positive', 4))
METHODS = {'EXACT_NORMALIZED_EXISTING_UNIT_OR_PARAGRAPH',
           'EXPLICIT_CANDIDATE_UNIT_ID_EXACT_NORMALIZED_CONTENT',
           'EXISTING_STRUCTURED_TABLE_ROW_AND_FIELD_BINDING',
           'NORMALIZED_SEGMENT_IN_EXISTING_PARAGRAPH'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text_digest(value):
    return digest(value.encode('utf-8'))


def checked_bytes(path, expected):
    value = Path(path).read_bytes()
    if digest(value) != expected:
        raise ValueError('source_hash_mismatch')
    return value


def save(path, obj, exclusive=True):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def unique_index(rows, key='id'):
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError('duplicate_key')
        result[row[key]] = row
    return result


def jsonlines(data):
    return [json.loads(line) for line in data.decode('utf-8').splitlines() if line]


def binary(value):
    return type(value) is int and value in (0, 1)


def in_bucket(row, bucket):
    old, new = row['old'], row['new']
    if bucket.endswith('_changed'):
        d = bucket[0]
        return binary(old.get(d)) and binary(new.get(d)) and old[d] != new[d]
    if bucket.endswith('_unchanged_zero'):
        d = bucket[0]
        return binary(old.get(d)) and binary(new.get(d)) and old[d] == new[d] == 0
    return any(binary(new.get(d)) and new[d] == 1 for d in ('I', 'F'))


def select(rows, seed=SEED):
    """Exact frozen order; unique IDs; deficits stay deficits."""
    rng = random.Random(seed)
    selected, used, details = [], set(), []
    for bucket, quota in BUCKETS:
        eligible = [r for r in rows if r['id'] not in used and in_bucket(r, bucket)
                    and r['department'] in DEPTS]
        by_dept = {d: sorted([r['id'] for r in eligible if r['department'] == d])
                   for d in DEPTS}
        counts = {d: len(by_dept[d]) for d in DEPTS}
        for d in DEPTS:
            rng.shuffle(by_dept[d])
        picked = []
        while len(picked) < quota and any(by_dept.values()):
            for d in DEPTS:
                if by_dept[d] and len(picked) < quota:
                    uid = by_dept[d].pop(0)
                    picked.append(uid)
                    used.add(uid)
                    selected.append({'id': uid, 'bucket': bucket})
        details.append({'bucket': bucket, 'quota': quota, 'eligible_by_department': counts,
                        'selected_ids': picked, 'shortfall': quota - len(picked)})
    rng.shuffle(selected)
    for n, row in enumerate(selected, 1):
        row['blind_id'] = f'SA01-{n:03d}'
    return selected, details


def safety(row, available, all_rows):
    if row['id'] != available['id'] or row['canonical_family_id'] != available['canonical_family_id']:
        raise ValueError('pool_binding_disagreement')
    if row['review_status'] != 'AVAILABLE_IN_BOUNDED_DEVELOPMENT_POOL':
        raise ValueError('not_available')
    if not row['current_candidate_binding_verified']:
        raise ValueError('unverified_candidate')
    for flag in ('original_protected267_current_member', 'unmapped_dependency_field_paths',
                 'protected_dependency_family_ids', 'protected_embedded_or_context_unit_ids',
                 'isolation_reasons'):
        if row[flag]:
            raise ValueError('unsafe_or_unmapped_dependency')
    if row['confirmed_development_exposure']:
        return 'DIRECT_ID_REGISTER'
    members = row.get('canonical_family_registered_development_members', [])
    if (row['development_exposure_basis'] != 'CANONICAL_EXACT_NORMALIZED_FAMILY_ALIAS'
            or not members):
        raise ValueError('unregistered_development_exposure')
    # A listed direct exposed member must have exactly the same canonical family.
    if not any(m in all_rows and all_rows[m]['confirmed_development_exposure']
               and all_rows[m]['canonical_family_id'] == row['canonical_family_id'] for m in members):
        raise ValueError('alias_without_bound_direct_member')
    return 'CANONICAL_EXACT_NORMALIZED_FAMILY_ALIAS'


def resolve_path(record, path):
    tokens = [m.group(0) for m in re.finditer(r'[^.\[\]]+|\[\d+\]', path)]
    value, ancestors = record, []
    for token in tokens:
        ancestors.append(value)
        value = value[int(token[1:-1])] if token.startswith('[') else value[token]
    return value, ancestors


def neutral_role(path):
    # These are source-structure descriptions, never feature names or machine opinions.
    if 'table' in path.lower():
        if 'column_names' in path:
            return '表格列名'
        if 'raw_row_cells' in path:
            return '表格行单元'
        if 'table_title' in path:
            return '表格标题'
        return '表格原文'
    if 'nearest_preceding_heading' in path:
        return '最近前置标题'
    if 'immediately_preceding_paragraph' in path:
        return '紧邻前段'
    if '.paragraph_context' in path:
        return '所在原段'
    if 'structure_boundary' in path or 'next_boundary' in path or 'next_component_boundary' in path:
        return '后续结构边界原文'
    if 'explicitly_cited' in path:
        return '原文所引内容'
    if 'following' in path:
        return '后续原文'
    return '关联原文'


def text_field_allowed(path):
    prefix = 'input.llm_v29_shared_context.'
    if not path.startswith(prefix):
        return False
    return bool(re.search(r'\.(text|original_unit_text|required_branch_text|'
                          r'next_paragraph_text|next_candidate_paragraph_text|'
                          r'next_component_boundary_text|table_title)$|'
                          r'\.(column_names|raw_row_cells)\[\d+\]$', path))


def export_record(record, bound, blind_id, source_hashes):
    inp = record['input']
    text = inp['unit_text']
    if not isinstance(text, str) or not text.strip() or text_digest(text) != bound['current_unit_text_sha256']:
        raise ValueError('current_full_unit_binding_failed')
    if inp['unit_id'] != bound['candidate_unit_id'] or inp['candidate_sha256'] != bound['candidate_sha256']:
        raise ValueError('current_candidate_metadata_mismatch')
    if source_hashes.get(str(Path(inp['candidate_file']).resolve())) != inp['candidate_sha256']:
        raise ValueError('candidate_source_not_preverified')
    contexts, verification = [], []
    # Different documents remain distinguished; actual IDs/filenames stay sealed.
    documents = {str(Path(inp['candidate_file']).resolve()): 'A'}
    seen = set()
    for dep in bound['dependencies']:
        if not dep['mapped'] or dep['protected_full_normalized_match_ids'] or not dep['bindings']:
            raise ValueError('context_dependency_not_safe')
        path = dep['field_path']
        if not text_field_allowed(path):
            raise ValueError('non_source_text_dependency_field')
        value, ancestors = resolve_path(record, path)
        if not isinstance(value, str) or text_digest(value) != dep['field_text_sha256']:
            raise ValueError('actual_context_hash_mismatch')
        locations = []
        for binding in dep['bindings']:
            if binding['method'] not in METHODS:
                raise ValueError('unknown_context_binding_method')
            candidate = str(Path(binding['candidate_path']).resolve())
            if source_hashes.get(candidate) != binding['candidate_sha256']:
                raise ValueError('context_candidate_source_not_preverified')
            if candidate not in documents:
                documents[candidate] = chr(ord('A') + len(documents))
            locations.append(documents[candidate])
        pages = []
        for ancestor in reversed(ancestors):
            if isinstance(ancestor, dict) and isinstance(ancestor.get('pages'), list):
                if all(type(p) is int for p in ancestor['pages']):
                    pages = ancestor['pages']
                    break
        # Exact repeats add no text; all original paths remain recorded as consumed.
        key = (tuple(sorted(set(locations))), value)
        duplicate = key in seen or (locations == ['A'] and value == text)
        verification.append({'field_path': path, 'field_text_sha256': dep['field_text_sha256'],
                             'duplicate_exact_text': duplicate, 'source_bindings': dep['bindings']})
        if duplicate:
            continue
        seen.add(key)
        contexts.append({'context_id': f'C{len(contexts) + 1:02d}', 'source_documents': sorted(set(locations)),
                         'relation': neutral_role(path), 'pages': pages, 'text': value,
                         'text_sha256': dep['field_text_sha256'],
                         'source_candidate_sha256': sorted({b['candidate_sha256'] for b in dep['bindings']})})
    if not bound['dependencies']:
        raise ValueError('no_shared_context_dependency_audit')
    return {'blind_id': blind_id, 'unit': {'source_document': 'A', 'pages': inp.get('pages', []), 'text': text,
                                         'text_sha256': bound['current_unit_text_sha256'],
                                         'source_sha256': bound['source_sha256'],
                                         'source_candidate_sha256': bound['candidate_sha256']},
            'contexts': contexts}, verification


BLIND_PREAMBLE = '''# 共同定义有限开发语义审读包

本包用于开发覆盖审查。请依据同一版《共用编码规则》审读完整单元，结合所附原语境判断实际对象、指代、条件和适用范围；分别记录 I、F 的判断、原文依据及必要的其他维度问题。原语境只用于关系解析，不能将其中内容自动传播到当前单元。

如材料仍不足，请记录不足及需要补充的原文，不将不足直接记为 0。两名审读者应各自完成记录后再对照；本次 AI 审读不作为真人专家或独立效度样本，不估计准确率或 κ。

文档 A 是当前单元来源；B 等表示另一个已绑定来源。相同来源的完全重复文本只展示一次。盲编号只用于回传；不提供旧/新机器判断、模型理由或期望答案。
'''


def markdown(rows):
    parts = [BLIND_PREAMBLE]
    for row in rows:
        unit = row['unit']
        pages = '、'.join(map(str, unit['pages'])) or '未标页码'
        parts.append(f"\n## {row['blind_id']}\n\n当前完整单元（文档 A，页 {pages}）：\n\n{unit['text']}\n")
        for context in row['contexts']:
            pages = '、'.join(map(str, context['pages'])) or '未标页码'
            docs = '、'.join(context['source_documents'])
            parts.append(f"\n{context['context_id']} {context['relation']}（文档 {docs}，页 {pages}）：\n\n{context['text']}\n")
    return '\n'.join(parts)


def run():
    if (HERE / 'attempt-ledger.json').exists():
        raise RuntimeError('one_attempt_ledger_already_exists_no_redraw')
    freeze = json.loads((HERE / 'design-freeze.json').read_text())
    checked_bytes(HERE / 'design.md', DESIGN_SHA)
    assert freeze['design_sha256'] == DESIGN_SHA and freeze['seed'] == SEED
    binding_bytes = checked_bytes(SHADOW / 'migration_development_binding_v1.json', BINDING_SHA)
    binding = json.loads(binding_bytes)
    available = unique_index(binding['available_development_pool'])
    bound = unique_index(binding['unit_family_and_dependency_bindings'])
    isolated_ids = {r['id'] for r in binding['isolated_development_candidates']}
    if len(available) != 468 or set(available) & isolated_ids:
        raise ValueError('pool_size_or_isolation_mismatch')
    bases = {uid: safety(bound[uid], row, bound) for uid, row in available.items()}
    source_hashes = {}
    for source in binding['source_bindings']:
        path = Path(source['path']).resolve()
        checked_bytes(path, source['sha256'])
        source_hashes[str(path)] = source['sha256']
    run_info = json.loads((SHADOW / 'all_predictions.run.json').read_text())
    current_bytes = checked_bytes(SHADOW / 'all_predictions.jsonl', run_info['output_sha256'])
    old_bytes = checked_bytes(OLD, OLD_SHA)
    group_bytes = checked_bytes(GROUP, GROUP_SHA)
    input_bytes = checked_bytes(run_info['input'], run_info['input_sha256'])
    if source_hashes.get(str(Path(run_info['input']).resolve())) != run_info['input_sha256']:
        raise ValueError('shared_input_not_in_audited_binding')
    sealed = HERE / 'sealed'
    sealed.mkdir(mode=0o700, exist_ok=True)
    sealed.chmod(0o700)
    old_umask = os.umask(0o077)
    try:
        ledger = {'started_at': now(), 'status': 'one_attempt_started_before_label_parse_and_selection',
                  'seed': SEED, 'design_sha256': DESIGN_SHA, 'binding_sha256': BINDING_SHA,
                  'program_sha256': digest(Path(__file__).read_bytes()),
                  'old_predictions_sha256': OLD_SHA, 'current_predictions_sha256': run_info['output_sha256'],
                  'input_sha256': run_info['input_sha256'], 'group_metadata_sha256': GROUP_SHA,
                  'python_version': sys.version, 'no_model_or_rule_execution': True}
        save(HERE / 'attempt-ledger.json', ledger)
        # First access to individual machine labels in this task.
        old = unique_index(jsonlines(old_bytes))
        current = unique_index(jsonlines(current_bytes))
        inputs = unique_index(jsonlines(input_bytes))
        group_rows = json.loads(group_bytes)['rows']
        group_map = {}
        for r in group_rows:
            stem = Path(r['original_file']).stem
            if stem in group_map and group_map[stem] != r['analysis_group']:
                raise ValueError('conflicting_department_metadata')
            group_map[stem] = r['analysis_group']
        selection_rows = []
        for uid in sorted(available):
            inp = inputs[uid]['input']
            for machine in (old[uid], current[uid]):
                if machine['prediction']['unit_text_sha256'] != bound[uid]['current_unit_text_sha256']:
                    raise ValueError('machine_input_unit_hash_mismatch')
            selection_rows.append({'id': uid, 'department': group_map[inp['original_file_stem']],
                                   'old': {d: old[uid]['prediction']['labels'].get(d) for d in ('I', 'F')},
                                   'new': {d: current[uid]['prediction']['labels'].get(d) for d in ('I', 'F')},
                                   'exposure_basis': bases[uid]})
        selected, strata = select(selection_rows)
        selection_index = unique_index(selection_rows)
        log = {'scope': 'development_coverage_not_accuracy_or_human_validation', 'seed': SEED,
               'design_sha256': DESIGN_SHA, 'source_hashes': source_hashes,
               'label_and_department_projection': selection_rows, 'strata': strata,
               'selected': selected, 'exports': [], 'post_selection_isolated': []}
        # Preserve the actual draw before attempting context rendering. No redraw.
        save(sealed / 'selection.json', log)
        blind = []
        for draw in selected:
            uid = draw['id']
            try:
                row, consumed = export_record(inputs[uid], bound[uid], draw['blind_id'], source_hashes)
                blind.append(row)
                log['exports'].append({'id': uid, 'blind_id': draw['blind_id'],
                                       'exposure_basis': selection_index[uid]['exposure_basis'],
                                       'current_full_unit_sha256': bound[uid]['current_unit_text_sha256'],
                                       'consumed_context_fields': consumed})
            except (ValueError, KeyError, TypeError) as exc:
                log['post_selection_isolated'].append({'id': uid, 'blind_id': draw['blind_id'],
                                                        'reason': str(exc), 'replacement': False})
        save(sealed / 'selection.json', log, exclusive=False)
        blind_dir = HERE / 'blind'
        blind_dir.mkdir(exist_ok=False)
        data = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in blind).encode('utf-8')
        md = markdown(blind).encode('utf-8')
        jsonpath, mdpath = blind_dir / 'review_packet.jsonl', blind_dir / 'review_packet.md'
        jsonpath.write_bytes(data)
        mdpath.write_bytes(md)
        completion = {'status': 'blinded_development_packet_complete', 'completed_at': now(),
                      'selected_n': len(selected), 'exported_n': len(blind),
                      'post_selection_isolated_n': len(selected) - len(blind),
                      'redraw_or_replacement': False, 'both_reviewers_use_identical_files': True,
                      'scope': 'development_coverage_only_no_accuracy_estimation',
                      'blind_files': [{'path': str(jsonpath), 'sha256': digest(data)},
                                      {'path': str(mdpath), 'sha256': digest(md)}],
                      'program_sha256': ledger['program_sha256'], 'design_sha256': DESIGN_SHA,
                      'binding_sha256': BINDING_SHA}
        save(HERE / 'completion.json', completion)
        print(json.dumps(completion, ensure_ascii=False, indent=2))
    finally:
        os.umask(old_umask)


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        # Never expose a candidate text/value via an exception representation.
        if (HERE / 'sealed').is_dir():
            error_file = HERE / 'sealed' / ('error-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '.json')
            save(error_file, {'at': now(), 'type': type(exc).__name__, 'reason': str(exc)})
            error_file.chmod(0o600)
        print('Stopped: ' + type(exc).__name__ + '; inspect restricted error record. No redraw.', file=sys.stderr)
        raise SystemExit(1)
