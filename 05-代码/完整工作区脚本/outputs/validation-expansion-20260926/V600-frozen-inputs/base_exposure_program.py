"""Text-only planning audit after H600/R200. No labels, predictions or sampling."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from sample_holdout import frame

ROOT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).strip('。.!！?？;；')


def source_texts(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'text' and isinstance(item, str):
                yield item
            else:
                yield from source_texts(item)
    elif isinstance(value, list):
        for item in value:
            yield from source_texts(item)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Never overwrite an exposure audit'
    manifest_path = ROOT / '最终冻结清单.json'
    frozen = json.loads(manifest_path.read_text())
    inputs = {str(manifest_path): sha(manifest_path)}
    paths = {}
    for name in ('corpus', 'exposure', 'adapter', 'classification'):
        info = frozen['files'][name]
        path = Path(info['path'])
        assert sha(path) == info['sha256'], name
        inputs[str(path)] = info['sha256']
        paths[name] = path
    corpus = [json.loads(line) for line in paths['corpus'].read_text().splitlines()]
    units = {row['review_id']: row for row in corpus if row['count_as_analysis_unit'] is True}
    assert len(units) == 4924
    old = json.loads(paths['exposure'].read_text())
    prior = set(old['exclusions'])
    assert prior <= units.keys()
    target_origins = defaultdict(list)
    contexts = defaultdict(set)
    context_inputs = []
    phase_counts = {}
    for phase, expected in (('H600', 600), ('R200', 200)):
        mapping_path = ROOT / phase / '抽样清单-研究者.json'
        seal_path = ROOT / phase / '封存信息.json'
        mapping = json.loads(mapping_path.read_text())
        seal = json.loads(seal_path.read_text())
        assert sha(mapping_path) == seal['output_files'][mapping_path.name]
        inputs[str(mapping_path)] = sha(mapping_path)
        inputs[str(seal_path)] = sha(seal_path)
        assert len(mapping['rows']) == expected
        index = {row['id']: row for row in mapping['rows']}
        assert len(index) == expected
        phase_counts[phase] = expected
        seen = set()
        for path in sorted((ROOT / phase / 'agent-A').glob('材料-*.json')):
            relative = str(path.relative_to(ROOT / phase))
            assert sha(path) == seal['output_files'][relative]
            peer = path.parent.parent / 'agent-C' / path.name
            peer_relative = str(peer.relative_to(ROOT / phase))
            assert sha(peer) == seal['output_files'][peer_relative]
            assert path.read_bytes() == peer.read_bytes()
            inputs[str(peer)] = sha(peer)
            inputs[str(path)] = sha(path)
            context_inputs.append(relative)
            for row in json.loads(path.read_text())['rows']:
                assert row['id'] in index and row['id'] not in seen
                seen.add(row['id'])
                key = index[row['id']]['review_id']
                assert key in units and row['text'] == units[key]['unit_text']
                target_origins[key].append(row['id'])
                for text in [row['text'], *source_texts(row['contexts'])]:
                    normalized = norm(text)
                    if normalized:
                        contexts[normalized].add(row['id'])
        assert seen == set(index)
    targets = set(target_origins)
    assert len(targets) == 800 and not targets & prior
    normalized = {key: norm(row['unit_text']) for key, row in units.items()}
    target_norms = defaultdict(list)
    for key in sorted(targets):
        target_norms[normalized[key]].append(key)
    duplicate_exposure = {}
    for key, text in normalized.items():
        if key not in prior | targets and text in target_norms:
            duplicate_exposure[key] = target_norms[text]
    # Same threshold as the first-round frozen exposure audit. One hop from
    # newly observed target/exact-duplicate seeds; no recursive closure.
    seeds = targets | set(duplicate_exposure)
    grams = {key: set(text[i:i + 5] for i in range(len(text) - 4))
             for key, text in normalized.items() if len(text) >= 30}
    postings = defaultdict(set)
    for key, values in grams.items():
        for value in values:
            postings[value].add(key)
    near = defaultdict(list)
    for key in sorted(seeds & grams.keys()):
        counts = Counter(other for value in grams[key] for other in postings[value]
                         if other not in prior | seeds)
        for other, overlap in counts.items():
            ratio = min(len(normalized[key]), len(normalized[other])) / max(len(normalized[key]), len(normalized[other]))
            if ratio < .75:
                continue
            dice = 2 * overlap / (len(grams[key]) + len(grams[other]))
            if dice >= .85:
                near[other].append({'seed_id': key, 'dice': round(dice, 6)})
    target_exclusions = prior | seeds | set(near)
    target_remaining = set(units) - target_exclusions
    # Context visibility is a separately reported conservative sensitivity.
    # Substring matching is mechanical exposure, not proof of semantic identity.
    visible_context = {}
    for key in sorted(target_remaining):
        text = normalized[key]
        matches = set(contexts.get(text, set()))
        if len(text) >= 20:
            for body, origins in contexts.items():
                if text in body:
                    matches.update(origins)
        if matches:
            visible_context[key] = sorted(matches)
    visible_context_near = defaultdict(list)
    context_known = set(visible_context)
    context_candidates = target_remaining - context_known
    for key in sorted(context_known & grams.keys()):
        counts = Counter(other for value in grams[key] for other in postings[value]
                         if other in context_candidates)
        for other, overlap in counts.items():
            ratio = min(len(normalized[key]), len(normalized[other])) / max(len(normalized[key]), len(normalized[other]))
            if ratio < .75:
                continue
            dice = 2 * overlap / (len(grams[key]) + len(grams[other]))
            if dice >= .85:
                visible_context_near[other].append({'seed_id': key, 'dice': round(dice, 6)})
    after_context_units = context_candidates - visible_context_near.keys()
    # Source bodies need not correspond exactly to a segmented analysis unit.
    # Match all displayed target/context bodies directly as additional seeds;
    # do not rely only on the subset mapped to known unit IDs above.
    displayed_source_near = defaultdict(list)
    for body, origins in sorted(contexts.items()):
        if len(body) < 30:
            continue
        body_grams = {body[i:i + 5] for i in range(len(body) - 4)}
        counts = Counter(other for value in body_grams for other in postings.get(value, ())
                         if other in after_context_units)
        for other, overlap in counts.items():
            ratio = min(len(body), len(normalized[other])) / max(len(body), len(normalized[other]))
            if ratio < .75:
                continue
            dice = 2 * overlap / (len(body_grams) + len(grams[other]))
            if dice >= .85:
                displayed_source_near[other].append({
                    'displayed_source_normalized_sha256': hashlib.sha256(body.encode()).hexdigest(),
                    'source_blind_ids': sorted(origins), 'dice': round(dice, 6)})
    conservative_remaining = after_context_units - displayed_source_near.keys()
    adapter = json.loads(paths['adapter'].read_text())
    classification = json.loads(paths['classification'].read_text())
    variants = {}
    for name, eligible in (('target_and_near_duplicate_exclusion', target_remaining),
                           ('also_exclude_visible_context_candidates', conservative_remaining)):
        if eligible:
            _, pools, meta = frame(corpus, adapter, classification, {'provisional_eligible_ids': sorted(eligible)})
            counts = {key: len(values) for key, values in sorted(pools.items())}
            groups = dict(Counter(value['group'] for value in meta.values()))
        else:
            counts, groups = {}, {}
        variants[name] = {'N': len(eligible), 'group_counts': groups, 'stratum_counts': counts,
                          'candidate_ids': sorted(eligible)}
    assert all(sha(Path(path)) == digest for path, digest in inputs.items())
    result = {
        'status': 'planning_only_exposure_inventory_no_sample_no_new_predictions',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'analysis_units': len(units), 'prior_frozen_exclusions': len(prior),
        'newly_observed_target_counts': phase_counts, 'new_unique_targets': len(targets),
        'new_exact_duplicate_exclusions': len(duplicate_exposure),
        'new_near_duplicate_exclusions': len(near),
        'additional_visible_context_candidates': len(visible_context),
        'additional_context_near_duplicate_candidates': len(visible_context_near),
        'additional_displayed_source_near_candidates': len(displayed_source_near),
        'rules': {'normalization': 'NFKC, whitespace removal, terminal sentence punctuation removal',
                  'near': 'min30 normalized characters, length ratio>=.75, character5gram Dice>=.85; one hop from new target/exact duplicate seeds',
                  'context': 'exact normalized displayed target/context text, or substring for unit length>=20; policy text fields only; plus one-hop near matches from directly visible corpus-unit seeds and directly from all displayed policy text bodies at the same .85/.75/min30 thresholds'},
        'limitations': ['Not a certificate that raw text was never seen; entire corpus may have been processed or inspected previously.',
                       'No labels or dictionary predictions were opened by this audit.',
                       'Context visibility is not itself a reference-label exposure or verified semantic equivalence; both inventories are reported before selecting a design.',
                       'New v24 development additions outside the frozen corpus/known800 must still be registered before the next freeze.',
                       'No candidate frame chosen, no sample drawn, no acceptance threshold or inference to original4924 implied.'],
        'input_hashes': inputs, 'script_sha256': sha(Path(__file__)),
        'target_origins': dict(target_origins), 'exact_duplicate_exclusions': duplicate_exposure,
        'near_duplicate_exclusions': dict(near), 'visible_context_candidates': visible_context,
        'visible_context_near_duplicate_candidates': dict(visible_context_near),
        'displayed_source_near_candidates': dict(displayed_source_near),
        'variants': variants,
    }
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: result[key] for key in ('status', 'analysis_units', 'prior_frozen_exclusions',
          'new_unique_targets', 'new_exact_duplicate_exclusions', 'new_near_duplicate_exclusions',
          'additional_visible_context_candidates', 'additional_context_near_duplicate_candidates',
          'additional_displayed_source_near_candidates')}, ensure_ascii=False))
    print(json.dumps({name: {k: v for k, v in variant.items() if k != 'candidate_ids'}
                      for name, variant in variants.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
