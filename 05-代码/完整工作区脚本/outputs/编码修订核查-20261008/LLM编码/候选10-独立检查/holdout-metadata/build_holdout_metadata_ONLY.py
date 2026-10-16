"""Frozen metadata draw; mechanical in-memory text contact checks; no models.

Never print or serialize input text, protected indexes, prediction rows or labels.
Only creates new outputs under this directory. Rerun into a new empty directory.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import unicodedata
from collections import Counter, defaultdict

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE = ROOT / 'outputs/编码修订核查-20261008/LLM编码'
HERE = Path(__file__).resolve().parent
R3 = ROOT / 'outputs/coding-revision-20261007-r3'
R4 = ROOT / 'outputs/coding-revision-20261008-r4'
SCOPE = BASE / '候选09-分步判读/PRIVATE09/partial-rerun-feasibility'


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def canonical_sha(obj):
    return sha_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def family_norm(text):
    text = unicodedata.normalize('NFKC', text)
    return ''.join(c for c in text if not c.isspace() and not unicodedata.category(c).startswith('P'))


def leaves(obj, path='root'):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, value in obj.items():
            yield from leaves(value, path + '.' + k)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from leaves(value, f'{path}[{i}]')


def main(out):
    plan = json.loads((HERE / 'selection_plan_PREDECLARED.json').read_text())
    bindings = []

    def bind(path, role, fields=None):
        path = Path(path)
        item = {'path': str(path), 'sha256': sha(path), 'role': role}
        if fields is not None:
            item['fields_mechanically_used'] = fields
        bindings.append(item)
        return path

    def meta(path, role, fields):
        return json.loads(bind(path, role, fields).read_text())

    def input_rows(path, role):
        path = bind(path, role, ['id', 'text and context leaves: mechanical memory only'])
        if path.suffix == '.jsonl':
            data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        else:
            obj = json.loads(path.read_text())
            data = obj['rows'] if isinstance(obj, dict) else obj
        assert isinstance(data, list) and all(isinstance(r, dict) for r in data)
        return [(str(path), r) for r in data]

    prompt = bind(BASE / '候选10-手册条款应用/stageB_prompt.txt', 'hash only; prompt not read')
    assert sha(prompt) == plan['binding_prompt_sha256']
    bind(SCOPE / 'scope_spec_PREDECLARED.json', 'fixed five trigger definitions; no predictions')
    scope_path = bind(SCOPE / 'all4924_scope_provenance_METADATA_ONLY_PRIVATE.jsonl', 'candidate frame metadata only')
    scope = [json.loads(line) for line in scope_path.read_text().splitlines()]
    assert len(scope) == 4924
    registry = meta(R4 / 'validation-state-audit/future_human_v5_development_exclusion_metadata.json',
                    'protected IDs/families metadata only', ['all_registered_members_of_reserved_families_unit_ids', 'reserved_family_metadata'])
    reserved = set(registry['all_registered_members_of_reserved_families_unit_ids'])
    assert len(reserved) == 267
    prior = meta(R3 / 'admin/future_human_v5_sampling_PRIVATE.json', 'historical exclusion metadata only',
                 ['known_development_excluded_ids', 'current_training_excluded_ids', 'additional_units_excluded_by_normalized_text', 'all_eligible_families'])
    evidence = meta(R3 / 'admin/confirmation_exclusion_evidence_PRIVATE.json', 'legacy control exclusion metadata only',
                    ['categories', 'additional_same_normalized_text_IDs'])
    exposed = meta(R3 / 'admin/confirmation_sampling_PRIVATE.json', 'old240 participation metadata only, including probability old180',
                   ['sample[].original_id', 'sample[].component'])
    known11 = meta(BASE / '候选09-独立检查/known11_source_extraction_and_protection_metadata.json', '09 initial11 participation metadata only',
                   ['fixed_order', 'model_input.path', 'model_input.sha256'])
    design07 = meta(BASE / '候选方案/design_freeze.json', 'locate frozen input sources only', ['files[].path', 'source_bindings[].path'])
    prep08 = meta(BASE / '候选08-命题与证据判定/preparation_manifest.json', 'locate frozen input sources only', ['core_files[].path', 'source_bindings[].path'])
    execution08 = meta(BASE / '候选08-命题与证据判定/candidate08_execution_plan_PROPOSED.json', '08 reviewed146 input paths only', ['runs[].input_binding.path', 'runs[].n'])
    # These two files were accidentally over-projected during initial discovery.
    # Project IDs only now; their reviewed contents are never emitted again.
    incident_paths = [
        BASE / '候选方案/semantic-review/independent-additional9/review_manifest.json',
        BASE / '候选方案/additional_known_checks_source_metadata.json',
    ]
    incident = []
    incident_ids = set()
    for p in incident_paths:
        obj = meta(p, 'incident: ID-only projection; no text or labels emitted', ['recursive dictionaries: exact key id only'])
        ids = set()
        def get_ids(x):
            if isinstance(x, dict):
                if isinstance(x.get('id'), str) and x['id'].startswith('RECODE25-'):
                    ids.add(x['id'])
                for v in x.values():
                    get_ids(v)
            elif isinstance(x, list):
                for v in x:
                    get_ids(v)
        get_ids(obj)
        incident_ids |= ids
        incident.append({'path': str(p), 'sha256': sha(p), 'actually_tool_visible_current_ids': sorted(ids),
                         'description': 'Initial discovery projected these two files too broadly; they contain review text/individual labels despite metadata/manifest filenames. No protected267 original was output. All identifiable current IDs and families excluded.'})

    categories = {
        'protected267': reserved,
        'historical_known_development': set(prior['known_development_excluded_ids']),
        'current_training': set(prior['current_training_excluded_ids']),
        'v5_same_normalized_text': set(prior['additional_units_excluded_by_normalized_text']),
        'legacy_explicit_controls': set(evidence['categories']['explicit_legacy_rule_regression_control_IDs']),
        'legacy_prior_reserved_and_development_union': set().union(*map(set, evidence['categories'].values())),
        'legacy_same_normalized_text': set(evidence['additional_same_normalized_text_IDs']),
        'exposed240': {r['original_id'] for r in exposed['sample']},
        'known09_initial11': {i for i in known11['fixed_order'] if i.startswith('RECODE25-')},
        'current_discovery_incident': incident_ids,
    }
    assert len(categories['exposed240']) == 240
    # Actual old180 is mechanically located through component participation, not labels.
    old180_n = sum(r['component'] == 'probability_canonical' for r in exposed['sample'])
    assert old180_n == 180

    history = []
    p07 = BASE / '候选方案/exposed240_inputs_UNCHANGED.jsonl'
    assert str(p07) in {r['path'] for r in design07['files']}
    history.extend(input_rows(p07, '07 exposed240 input content: mechanical contact screening only'))
    history.extend(input_rows(Path(known11['model_input']['path']), '09 initial11 input content: mechanical contact screening only'))
    assert sha(known11['model_input']['path']) == known11['model_input']['sha256']
    input_participation = set()
    reviewed08_counts = []
    prep08_paths = {r['path'] for r in prep08['core_files']} | {r['path'] for r in prep08['source_bindings']}
    for run in execution08['runs']:
        p = Path(run['input_binding']['path'])
        assert str(p) in prep08_paths
        rows = input_rows(p, '08 previously reviewed inputs: mechanical contact screening only')
        assert len(rows) == run['n']
        reviewed08_counts.append(run['n'])
        history.extend(rows)
        input_participation |= {r['id'] for _, r in rows if r.get('id', '').startswith('RECODE25-')}
    assert sorted(reviewed08_counts) == [16, 20, 24, 24, 62, 240]
    categories['08_input_real_participation'] = input_participation

    redactor_path = bind(R4 / 'validation-state-audit/reserved_context_redactor.py', 'frozen in-memory protected screening helper')
    assert sha(redactor_path) == '64dad9725532096b9f46544edf87789fda04b1c9048f00d0e1eee240334edf73'
    spec = importlib.util.spec_from_file_location('reserved_redactor_frozen', redactor_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    redactor = module.ReservedContextRedactor(ROOT)
    original_path = bind(R3 / 'effective_blind_inputs_v14.jsonl', 'mechanical in-memory source row binding/family/contact only')
    assert sha(original_path) == '6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
    original_lines = original_path.read_bytes().splitlines()
    original = {r['id']: r for r in map(json.loads, original_lines)}
    assert len(original) == 4924
    family = {uid: 'TEXTFAM-' + sha_bytes(family_norm(r['text']).encode()) for uid, r in original.items()}
    members = defaultdict(list)
    for uid, fid in family.items():
        members[fid].append(uid)
    # Existing family metadata is cross-checked, never replaced or rewritten.
    for f in prior['all_eligible_families']:
        for uid in f['members']:
            assert family[uid] == f['family_id']
    excluded_ids = set().union(*categories.values())
    excluded_family_ids = {family[uid] for uid in excluded_ids if uid in family}
    excluded_by_family = {uid for uid in original if family[uid] in excluded_family_ids}
    eligible_prior_family_ids = {f['family_id'] for f in prior['all_eligible_families']}
    groups = plan['groups_in_fixed_order']
    frame = [r for r in scope if r['selected_for_proposed_review'] and r['source_group'] in groups]
    metadata_frame = [r for r in frame if r['id'] not in excluded_by_family and family[r['id']] in eligible_prior_family_ids]
    seed = plan['seed']
    def rank(r):
        return sha_bytes((seed + '\0' + r['id']).encode()), r['id']
    metadata_frame.sort(key=rank)
    selected = []
    selected_families = set()
    cells = []
    def pick(pool, reason):
        pool = [r for r in pool if family[r['id']] not in selected_families]
        if not pool:
            return False
        r = min(pool, key=rank)
        selected.append((r, reason))
        selected_families.add(family[r['id']])
        return True
    for g in groups:
        for t in plan['trigger_order']:
            pool = [r for r in metadata_frame if r['source_group'] == g and t in r['trigger_ids']]
            picked = pick(pool, {'phase': 'department_trigger_coverage', 'group': g, 'trigger': t})
            cells.append({'group': g, 'trigger': t, 'metadata_eligible_unit_n': len(pool), 'picked_new_family': picked})
    while len(selected) < plan['maximum_target_units']:
        progress = False
        for g in groups:
            if len(selected) >= plan['maximum_target_units']:
                break
            progress |= pick([r for r in metadata_frame if r['source_group'] == g], {'phase': 'department_round_robin_fill', 'group': g})
        if not progress:
            break
    assert len(selected) <= 20

    # Historical known ID rows are used as a conservative input-contact proxy,
    # plus the exact frozen07/08/09 request inputs above. No predictions loaded.
    development_ids = (categories['historical_known_development'] | categories['current_training'] |
                       categories['legacy_explicit_controls'] | categories['exposed240'] |
                       categories['known09_initial11'] | categories['08_input_real_participation'] | incident_ids)
    history += [(str(original_path), original[uid]) for uid in sorted(development_ids) if uid in original]
    history_current = {}
    for source, row in history:
        text = row.get('text')
        if isinstance(text, str) and module.normalized(text):
            key = (row.get('id', ''), sha_bytes(text.encode()))
            history_current.setdefault(key, (source, module.normalized(text)))
    # Deduplicate leaves by hash; retain the first deterministic metadata locator.
    history_leaves = {}
    for source, row in history:
        for path, text in leaves(row):
            norm = module.normalized(text)
            if norm:
                digest = sha_bytes(text.encode())
                history_leaves.setdefault(digest, (source, row.get('id', ''), path, norm))

    screened = []
    admitted = []
    for s, reason in selected:
        uid = s['id']
        row = original[uid]
        assert canonical_sha(row) == s['original_input_row_canonical_sha256']
        source_line = original_lines[s['original_input_line_1based'] - 1]
        assert json.loads(source_line)['id'] == uid
        prot = redactor.audit_object_no_full_match(row)['hit_metadata']
        target_norm = module.normalized(row['text'])
        contacts = []
        for digest, (source, history_id, path, norm) in history_leaves.items():
            if target_norm and target_norm in norm:
                contacts.append({'direction': 'target_current_in_prior_development_input', 'history_current_id': history_id,
                                 'source_path': source, 'field_path': path, 'context_sha256': digest,
                                 'target_normalized_text_sha256': sha_bytes(target_norm.encode())})
        target_leaves = [(path, sha_bytes(text.encode()), module.normalized(text)) for path, text in leaves(row)]
        for (history_id, text_sha), (source, history_norm) in history_current.items():
            for path, digest, norm in target_leaves:
                if history_norm in norm:
                    contacts.append({'direction': 'prior_development_current_in_target_input', 'history_current_id': history_id,
                                     'source_path': source, 'field_path': path, 'context_sha256': digest,
                                     'history_current_text_sha256': text_sha})
        status = ('PENDING_PROTECTED_CONTEXT_NOT_ADMITTED' if prot else
                  'EXCLUDED_CONFIRMED_FULL_NORMALIZED_DEVELOPMENT_CONTACT' if contacts else
                  'ELIGIBLE_UNDER_CHECKED_RECORDS_ONLY')
        record = {k: s[k] for k in ['id', 'source_group', 'original_input_line_1based', 'original_input_row_canonical_sha256', 'original_input_source_sha256', 'trigger_ids', 'source_file_stem_UTF8_sha256']}
        record.update({'family_id': family[uid], 'source_raw_line_sha256': sha_bytes(source_line), 'fixed_rank_sha256': rank(s)[0],
                       'metadata_selection_reason': reason, 'eligibility_status': status,
                       'protected_full_normalized_match_n': len(prot), 'protected_match_metadata_only': prot,
                       'known_development_contact_n': len(contacts), 'known_development_contact_metadata_only': contacts})
        screened.append(record)
        if status == 'ELIGIBLE_UNDER_CHECKED_RECORDS_ONLY':
            admitted.append(record)
    incident_family_ids = sorted({family[i] for i in incident_ids if i in family})
    incident_family_members = sorted({m for fid in incident_family_ids for m in members[fid]})
    result = {
        'status': 'FROZEN_METADATA_ONLY_NO_MODEL_CALLS_NO_ANSWERS',
        'selection_plan_path': str(HERE / 'selection_plan_PREDECLARED.json'),
        'selection_plan_sha256': sha(HERE / 'selection_plan_PREDECLARED.json'),
        'prompt_sha256_hash_only': sha(prompt),
        'scope_union_n_all_four_groups': sum(r['selected_for_proposed_review'] for r in scope),
        'three_department_trigger_union_n': len(frame),
        'metadata_eligible_draw_frame_unit_n': len(metadata_frame),
        'metadata_eligible_draw_frame_family_n': len({family[r['id']] for r in metadata_frame}),
        'metadata_eligible_draw_frame_n_by_group': dict(Counter(r['source_group'] for r in metadata_frame)),
        'drawn_n': len(selected), 'mechanically_screened_n': len(screened), 'admitted_n': len(admitted),
        'admitted_n_by_group': dict(Counter(r['source_group'] for r in admitted)),
        'status_counts': dict(Counter(r['eligibility_status'] for r in screened)),
        'coverage_cell_metadata': cells,
        'exclusion_source_category_counts': {k: len(v) for k, v in categories.items()},
        'excluded_ID_union_n': len(excluded_ids), 'excluded_current_family_member_n': len(excluded_by_family),
        'old180_located_by_participation_metadata_n': old180_n,
        '08_previously_reviewed_synthetic_n': sum(n for n in reviewed08_counts if n != 240),
        'development_current_patterns_n': len(history_current), 'deduplicated_development_input_leaves_n': len(history_leaves),
        'no_replacement_after_mechanical_screen': True,
        'draw_frame_is_before_context_screen_not_probability_estimation_denominator': True,
        'all_population_context_eligibility_denominator_claimed': False,
        'admitted_ids_disclosed_to_prompt_author': False,
        'new_model_calls': 0, 'new_Codex_CLI_invocations': 0, 'answers_generated': 0,
        'limitation': 'Checked historical metadata are not exhaustive. Contact checks detect full normalized units, not arbitrary partial excerpts/paraphrases. v14 rows of historical known IDs are a conservative present-material proxy; earlier variants are not exhaustively reconstructed. Any admitted target is an internal checking target under these checked records only, not human independent validity or a probability population metric.',
    }

    out.mkdir(parents=True, exist_ok=True)
    files = {
        'source_bindings_METADATA_ONLY.json': bindings,
        'exclusion_register_METADATA_ONLY_PRIVATE.json': {'category_IDs': {k: sorted(v) for k, v in categories.items()}, 'propagated_current_family_member_IDs': sorted(excluded_by_family)},
        'discovery_output_contact_incident_METADATA_ONLY_PRIVATE.json': {'records': incident, 'identifiable_family_ids': incident_family_ids, 'excluded_identifiable_family_members': incident_family_members},
        'selection_summary_METADATA_ONLY.json': result,
    }
    for name, obj in files.items():
        p = out / name
        assert not p.exists(), 'Refusing to overwrite any existing file'
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    for name, rows in [('drawn_screened20_METADATA_ONLY_PRIVATE.jsonl', screened), ('admitted_holdout_METADATA_ONLY_PRIVATE.jsonl', admitted)]:
        p = out / name
        assert not p.exists(), 'Refusing to overwrite any existing file'
        p.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows))
    manifest = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    manifest.update({'builder_sha256': sha(__file__), 'plan_sha256': sha(HERE / 'selection_plan_PREDECLARED.json')})
    (out / 'freeze_manifest_METADATA_ONLY.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    # Counts and artifact hashes only, never IDs or source leaves.
    print(json.dumps({'drawn_n': len(screened), 'admitted_n': len(admitted), 'status_counts': result['status_counts'],
                      'summary_sha256': sha(out / 'selection_summary_METADATA_ONLY.json'),
                      'admitted_sample_sha256': sha(out / 'admitted_holdout_METADATA_ONLY_PRIVATE.jsonl'),
                      'source_bindings_sha256': sha(out / 'source_bindings_METADATA_ONLY.json')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=HERE / 'freeze-v1')
    args = parser.parse_args()
    main(args.out)
