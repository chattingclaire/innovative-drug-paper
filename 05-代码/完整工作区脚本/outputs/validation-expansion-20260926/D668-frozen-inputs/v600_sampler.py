"""New V600 sampler. No study reads on import; actual draw requires a new freeze.

Frozen helpers preserve the original metadata, allocation and material cleaning
rules. This module never parses machine predictions or reference labels. A
failed draw leaves an exclusive attempt directory; it must not be silently
removed or retried with a different seed or frame.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

PHASE = 'V600'
SEED = 2026092605
BUDGET = 600
REQUIRED = {'corpus', 'adapter', 'classification', 'exposure', 'protocol',
            'baseline_dictionary', 'baseline_predictions', 'candidate_dictionary',
            'candidate_predictions', 'sampler', 'sample_helpers', 'survey_metrics',
            'paired_version_metrics', 'results_bridge', 'legacy_results_helpers',
            'analysis_plan', 'reviewer_instructions', 'protocol_clarifications'}
STATIC_DOCS = {'protocol': '五维共用编码协议.md',
               'reviewer_instructions': '评审任务说明.md',
               'protocol_clarifications': '共同执行澄清.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def load_helpers(raw):
    namespace = {'__name__': '_frozen_sample_helpers', '__file__': '<frozen sample_holdout.py>'}
    exec(compile(raw, namespace['__file__'], 'exec'), namespace)
    return namespace


def material_contexts(unit, fields, helpers):
    """Keep explicit object-scope evidence visible to both original AI coders."""
    scope_field = 'verified_object_scope'
    require(scope_field not in unit or isinstance(unit[scope_field], list), 'Object scopes must be a list')
    require(not unit.get(scope_field) or scope_field in fields,
            'Object scope exists but is omitted from released fields')
    result = {f: helpers['clean_context'](unit[f]) for f in fields if f != scope_field and unit.get(f)}
    if unit.get(scope_field):
        scopes = unit[scope_field]
        require(isinstance(scopes, list), 'Object scopes must be a list')
        required = {'kind', 'source_sha256', 'unit_text_sha256', 'text', 'text_sha256', 'locator',
                    'verification', 'normalization', 'source_hash_field', 'required_branch_text'}
        validated = []
        for scope in scopes:
            require(isinstance(scope, dict) and set(scope) == required, 'Unexpected object-scope fields')
            require(isinstance(scope['kind'], str) and scope['kind'] in {
                'drug_clinical_trial', 'drug_regulatory_research', 'anticancer_drug_development',
                'anticancer_drug_safety_dossier', 'negotiated_drug_renewal'}, 'Unreviewed object-scope kind')
            renewal = scope['kind'] == 'negotiated_drug_renewal'
            source_field = 'unit_source_sha256' if renewal else 'source_sha256'
            require(scope['source_hash_field'] == source_field, 'Invalid scope kind/source_hash_field combination')
            require(scope['required_branch_text'] == '规则二简易续约' if renewal else scope['required_branch_text'] is None,
                    'Invalid scope kind/required_branch_text combination')
            require(all(isinstance(scope[k], str) and re.fullmatch('[0-9a-f]{64}', scope[k])
                        for k in ('source_sha256', 'unit_text_sha256', 'text_sha256')), 'Valid scope hashes required')
            require(scope['source_sha256'] == unit.get(source_field), 'Scope/source component mismatch')
            if renewal:
                branch_field = 'verified_rule_branch_context'
                branch = unit.get(branch_field)
                require(isinstance(branch, dict) and isinstance(branch.get('text'), str),
                        'Renewal branch must be a single object with text')
                require(re.sub(r'\s+', '', branch['text']) == scope['required_branch_text'], 'Renewal branch mismatch')
                require(branch_field in fields, 'Renewal scope supporting branch omitted from released fields')
                require(isinstance(result.get(branch_field), dict)
                        and result[branch_field].get('text') == branch['text'], 'Renewal branch text lost during material cleaning')
            require(scope['unit_text_sha256'] == sha(unit['unit_text'].encode()), 'Stale scope target hash')
            require(isinstance(scope['text'], str) and scope['text'].strip(), 'Empty scope quote')
            require(scope['text_sha256'] == sha(scope['text'].encode()), 'Scope quote hash mismatch')
            require(isinstance(scope['verification'], str) and scope['verification'].strip(), 'Scope verification required')
            locator = scope['locator']
            require(isinstance(locator, dict), 'Scope locator must be an object')
            if scope['kind'] == 'drug_clinical_trial':
                require(scope['normalization'] == 'none' and set(locator) == {'article', 'line', 'source'}, 'Unexpected text scope locator/normalization')
                require(all(type(locator[k]) is int and locator[k] > 0 for k in ('article', 'line')), 'Invalid scope article/line')
            else:
                require(scope['normalization'] == 'remove_extraction_whitespace' and set(locator) == {'physical_pages', 'source'}, 'Unexpected PDF scope locator/normalization')
                pages = locator['physical_pages']
                require(isinstance(pages, list) and pages and all(type(p) is int and p > 0 for p in pages)
                        and len(pages) == len(set(pages)), 'Invalid scope physical pages')
            require(isinstance(locator['source'], str) and Path(locator['source']).is_absolute(), 'Absolute scope source locator required')
            # These checks bind the supplied evidence to the supplied corpus.
            # Independent source verification belongs in the frozen provenance.
            validated.append(read_json(encode(scope)))
        result[scope_field] = validated
    return result


def construct(corpus, adapter, classification, exposure, fields, helpers):
    """Pure fixed-design construction; do not call on study inputs before freeze."""
    require(isinstance(fields, list) and fields and len(fields) == len(set(fields)), 'Unique explicit context fields required')
    require(set(fields) <= set(helpers['DEFAULT_CONTEXT_FIELDS']) | {'verified_object_scope'}, 'Unreviewed context field')
    require(isinstance(exposure.get('exclusions'), list), 'Exclusion list required')
    require(isinstance(exposure.get('provisional_eligible_ids'), list), 'Eligible list required')
    exclusions = set(exposure['exclusions'])
    eligible = set(exposure['provisional_eligible_ids'])
    require(len(exclusions) == len(exposure['exclusions']), 'Duplicate excluded ID')
    require(len(eligible) == len(exposure['provisional_eligible_ids']), 'Duplicate eligible ID')
    all_ids = {r['review_id'] for r in corpus if r['count_as_analysis_unit'] is True}
    require(not exclusions & eligible and exclusions | eligible == all_ids, 'Exposure must partition all analysis IDs')
    units, pools, meta = helpers['frame'](corpus, adapter, classification, exposure)
    # Validate the complete input contract before any random selection; a
    # missing scope field cannot pass merely because affected units are unpicked.
    for unit in corpus:
        if 'verified_object_scope' in unit:
            material_contexts(unit, fields, helpers)
    counts = {h: len(rows) for h, rows in sorted(pools.items())}
    allocation = helpers['allocate'](counts, BUDGET)
    strata = {h: {'N_h': N, 'n_h': allocation[h], 'pi': allocation[h] / N,
                  'weight': N / allocation[h]} for h, N in counts.items()}
    rng = random.Random(SEED)
    selected = []
    for h in sorted(pools):
        selected.extend(rng.sample(sorted(pools[h]), allocation[h]))
    rng.shuffle(selected)
    rows, materials = [], []
    for i, key in enumerate(selected, 1):
        unit = units[key]
        blind_id = f'{PHASE}-{i:04d}'
        h = meta[key]['stratum']
        rows.append({'id': blind_id, 'review_id': key, **meta[key], **strata[h],
                     'unit_text_sha256': sha(unit['unit_text'].encode())})
        materials.append({'id': blind_id, 'text': unit['unit_text'],
                          'source_title': unit['original_file_stem'], 'pages': unit['pages'],
                          'contexts': material_contexts(unit, fields, helpers),
                          'input_assessment': helpers['clean_assessment'](unit.get('input_assessment', {'status': 'not_assessed'})),
                          'context_usage': '只编码text；使用核验语境消解对象、条件、指代，不复制上级全标签。nearest_preceding_heading和immediately_preceding_paragraph仅表示位置相邻，未经核验不可自动当有效父级。材料不足保留待定。'})
    require(len(selected) == len(set(selected)) == min(BUDGET, len(eligible)), 'Invalid sample size or duplicated ID')
    require(set(selected) <= eligible and not set(selected) & exclusions, 'Excluded ID selected')
    plan = {'phase': PHASE, 'status': 'drawn', 'seed': SEED, 'N_star': len(eligible),
            'n': len(selected), 'strata': strata, 'random_generator': 'python.random.Random/MT19937',
            'python_version': sys.version, 'ordering': 'lexical strata; lexical source IDs; sample then shuffle with same RNG',
            'scope': '仅代表最终排除已知暴露后的有限候选框；不是未见原文证书，不外推原完整语料或未来政策。'}
    return {'plan': plan, 'rows': rows, 'not_selected_ids': sorted(eligible - set(selected))}, materials


def draw(freeze_path, destination):
    require(freeze_path.is_absolute() and destination.is_absolute(), 'Absolute paths required')
    require(not destination.exists(), 'Output already exists; no redraw')
    attempt = destination.with_name('.' + destination.name + '.partial')
    require(not attempt.exists(), 'Prior attempt exists; no silent retry')
    freeze_bytes = freeze_path.read_bytes()
    frozen = read_json(freeze_bytes)
    require(frozen.get('status') == 'frozen_for_paired_reference_label_holdout', 'New final freeze required')
    for key, value in {'phase': PHASE, 'sampling_seed': SEED, 'bootstrap_seed': 2026092606, 'sample_budget': BUDGET}.items():
        require(type(frozen.get(key)) is type(value) and frozen[key] == value, 'Unexpected frozen ' + key)
    require(isinstance(frozen.get('files'), dict) and REQUIRED <= set(frozen['files']), 'Missing freeze files')
    require(isinstance(frozen.get('protocol_version'), str) and frozen['protocol_version'], 'Protocol version required')
    snapshots = {}
    for name, entry in frozen['files'].items():
        path = Path(entry['path'])
        require(path.is_absolute(), 'Frozen path must be absolute')
        raw = path.read_bytes()
        require(sha(raw) == entry['sha256'], 'Frozen input changed: ' + name)
        snapshots[name] = raw
    require(sha(Path(__file__).read_bytes()) == frozen['files']['sampler']['sha256'], 'Running sampler differs from freeze')
    helpers = load_helpers(snapshots['sample_helpers'])
    # One freeze manifest in this study directory has one recorded draw attempt,
    # even if a second invocation supplies a different destination path.
    ledger = freeze_path.parent / ('.V600-sampling-attempt-' + sha(freeze_bytes) + '.json')
    with ledger.open('x') as handle:
        json.dump({'freeze_sha256': sha(freeze_bytes), 'freeze_path': str(freeze_path),
                   'destination': str(destination), 'created_at': datetime.now(timezone.utc).isoformat()}, handle)
    # Mark the sole attempt BEFORE any study sample selection.
    attempt.mkdir()
    corpus = [read_json(line) for line in snapshots['corpus'].splitlines() if line.strip()]
    mapping, materials = construct(corpus, read_json(snapshots['adapter']), read_json(snapshots['classification']),
                                   read_json(snapshots['exposure']), frozen['context_fields'], helpers)
    plan = mapping['plan']
    plan.update(created_at=datetime.now(timezone.utc).isoformat(), freeze_manifest_sha256=sha(freeze_bytes),
                input_hashes={name: entry['sha256'] for name, entry in frozen['files'].items()})
    (attempt / '抽样清单-研究者.json').write_bytes(encode(mapping))
    batch_count = math.ceil(len(materials) / 25)
    for coder in ('A', 'C'):
        directory = attempt / ('agent-' + coder)
        directory.mkdir()
        for name, filename in STATIC_DOCS.items():
            (directory / filename).write_bytes(snapshots[name])
        for batch in range(batch_count):
            packet = {'protocol_version': frozen['protocol_version'], 'purpose': 'reference_label_holdout_AI_independent',
                      'batch': batch + 1, 'total_batches': batch_count, 'rows': materials[batch * 25:(batch + 1) * 25]}
            (directory / f'材料-{batch + 1:02d}.json').write_bytes(encode(packet))
    require(freeze_path.read_bytes() == freeze_bytes, 'Freeze changed during draw; quarantine attempt')
    for name, entry in frozen['files'].items():
        require(Path(entry['path']).read_bytes() == snapshots[name], 'Input changed during draw; quarantine attempt: ' + name)
    for path in (attempt / 'agent-A').iterdir():
        require(path.read_bytes() == (attempt / 'agent-C' / path.name).read_bytes(), 'A/C materials differ')
    seal = dict(plan)
    seal['release_status'] = 'ready_for_blind_review'
    seal['output_files'] = {str(p.relative_to(attempt)): sha(p.read_bytes()) for p in sorted(attempt.rglob('*')) if p.is_file()}
    (attempt / '封存信息.json').write_bytes(encode(seal))
    require(not destination.exists(), 'Destination appeared during draw; quarantine attempt')
    attempt.rename(destination)
    return {'status': 'drawn_once', 'phase': PHASE, 'N': plan['N_star'], 'n': plan['n'], 'directory': str(destination)}


def self_test():
    helpers = load_helpers(Path(__file__).with_name('sample_holdout.py').read_bytes())
    corpus = [{'review_id': f'fiction-{i:04d}', 'count_as_analysis_unit': True,
               'original_file_stem': 'fiction-a' if i < 400 else 'fiction-b',
               'unit_text': f'构造资料 {i}，非政策原文。', 'pages': [1],
               'paragraph_context': {'text': '构造语境', 'labels': {'I': 1}}} for i in range(800)]
    adapter = {'documents': [{'id': 'fiction-' + x, 'group': g, 'publication_date': '2025-01-01', 'series': 'fiction'}
                             for x, g in [('a', 'NHSA'), ('b', 'NMPA')]]}
    classification = {'rows': [{'original_file': 'fiction-' + x + '.pdf', 'analysis_group': g}
                               for x, g in [('a', 'NHSA'), ('b', 'NMPA')]]}
    exposure = {'exclusions': [], 'provisional_eligible_ids': [r['review_id'] for r in corpus]}
    mapping, packets = construct(corpus, adapter, classification, exposure, ['paragraph_context'], helpers)
    require(mapping['plan']['n'] == 600 and len(mapping['not_selected_ids']) == 200, 'Wrong synthetic sample count')
    require(all(h['n_h'] == 300 for h in mapping['plan']['strata'].values()), 'Wrong allocation')
    require(all(row['contexts'] == {'paragraph_context': {'text': '构造语境'}} for row in packets), 'Answer key leaked')
    reverse, _ = construct(list(reversed(corpus)), adapter, classification, exposure, ['paragraph_context'], helpers)
    require(reverse == mapping, 'Source-order dependent sample')
    scoped = dict(corpus[0], source_sha256='f' * 64)
    quote = '构造适用范围，非政策原文。'
    scope = {'kind': 'drug_clinical_trial', 'source_sha256': 'f' * 64,
             'unit_text_sha256': sha(scoped['unit_text'].encode()), 'text': quote,
             'text_sha256': sha(quote.encode()), 'locator': {'article': 2, 'line': 5, 'source': '/fiction/source.txt'},
             'verification': '仅用于合成结构检查', 'normalization': 'none',
             'source_hash_field': 'source_sha256', 'required_branch_text': None}
    scoped['verified_object_scope'] = [scope]
    require(material_contexts(scoped, ['verified_object_scope'], helpers)['verified_object_scope'] == [scope], 'Scope evidence lost')
    checked_kinds = ['drug_clinical_trial']
    for kind in ('drug_regulatory_research', 'anticancer_drug_development', 'anticancer_drug_safety_dossier', 'negotiated_drug_renewal'):
        pdf_scope = dict(scope, kind=kind, normalization='remove_extraction_whitespace',
                         locator={'physical_pages': [1, 2], 'source': '/fiction/component.pdf'})
        pdf_unit = dict(scoped, verified_object_scope=[pdf_scope])
        pdf_fields = ['verified_object_scope']
        if kind == 'negotiated_drug_renewal':
            pdf_unit['unit_source_sha256'] = 'e' * 64
            pdf_unit['verified_rule_branch_context'] = {'text': '规 则二\n简易续约', 'verification': '构造分支', 'source_sha256': 'e' * 64}
            pdf_scope.update(source_hash_field='unit_source_sha256', source_sha256='e' * 64, required_branch_text='规则二简易续约')
            pdf_fields.append('verified_rule_branch_context')
        contexts = material_contexts(pdf_unit, pdf_fields, helpers)
        require(contexts['verified_object_scope'] == [pdf_scope], 'PDF scope evidence lost')
        if kind == 'negotiated_drug_renewal':
            require(contexts['verified_rule_branch_context'] == pdf_unit['verified_rule_branch_context'], 'Renewal branch evidence lost')
        checked_kinds.append(kind)
    rejected = {}
    def reject_scope(name, unit, fields, needle):
        try:
            material_contexts(unit, fields, helpers)
        except ValueError as exc:
            require(needle in str(exc), 'Wrong synthetic scope rejection: ' + name)
            rejected[name] = str(exc)
        else:
            raise AssertionError('Invalid scope accepted: ' + name)
    # pdf_unit/pdf_scope now form an invented component-bound renewal pair.
    reject_scope('renewal_main_announcement_hash', dict(pdf_unit, verified_object_scope=[dict(pdf_scope, source_sha256='f' * 64)]), pdf_fields, 'component mismatch')
    reject_scope('renewal_scope_wrong_source_field', dict(pdf_unit, verified_object_scope=[dict(pdf_scope, source_hash_field='source_sha256')]), pdf_fields, 'source_hash_field')
    reject_scope('renewal_wrong_branch', dict(pdf_unit, verified_rule_branch_context={'text': '规则一常规续约'}), pdf_fields, 'branch mismatch')
    reject_scope('renewal_branch_list', dict(pdf_unit, verified_rule_branch_context=[pdf_unit['verified_rule_branch_context']]), pdf_fields, 'single object')
    reject_scope('renewal_supporting_branch_not_released', pdf_unit, ['verified_object_scope'], 'omitted from released fields')
    reject_scope('scope_extra_key', dict(pdf_unit, verified_object_scope=[dict(pdf_scope, extra='unreviewed')]), pdf_fields, 'Unexpected object-scope fields')
    reject_scope('scope_old_eight_keys', dict(scoped, verified_object_scope=[{k: v for k, v in scope.items() if k not in {'source_hash_field', 'required_branch_text'}}]), ['verified_object_scope'], 'Unexpected object-scope fields')
    try:
        material_contexts(scoped, ['paragraph_context'], helpers)
    except ValueError:
        pass
    else:
        raise AssertionError('Scope silently omitted')
    scoped['verified_object_scope'][0]['unit_text_sha256'] = '0' * 64
    try:
        material_contexts(scoped, ['verified_object_scope'], helpers)
    except ValueError:
        pass
    else:
        raise AssertionError('Stale scope accepted')
    for x in ({'exclusions': [corpus[0]['review_id']], 'provisional_eligible_ids': exposure['provisional_eligible_ids']},
              {'exclusions': [], 'provisional_eligible_ids': exposure['provisional_eligible_ids'][:-1]}):
        try:
            construct(corpus, adapter, classification, x, ['paragraph_context'], helpers)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid exposure partition accepted')
    return {'status': 'synthetic_only_checks_passed', 'real_sample_drawn': False,
            'checks': ['fixed_size_and_strata', 'material_answer_filter', 'source_order_invariant', 'invalid_exposure_rejected',
                       'scope_visible_to_coders', 'silent_scope_omission_rejected', 'stale_scope_rejected',
                       'five_ten_field_scope_kinds_preserved', 'renewal_component_and_branch_jointly_released'],
            'scope_kinds': checked_kinds, 'scope_rejected_cases': rejected}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    if args.self_test:
        require(args.freeze is None and args.destination is None, 'Synthetic QA accepts no study paths')
        print(json.dumps(self_test(), ensure_ascii=False))
    else:
        require(args.freeze is not None and args.destination is not None, 'Explicit final freeze and new destination required')
        print(json.dumps(draw(args.freeze, args.destination), ensure_ascii=False))
