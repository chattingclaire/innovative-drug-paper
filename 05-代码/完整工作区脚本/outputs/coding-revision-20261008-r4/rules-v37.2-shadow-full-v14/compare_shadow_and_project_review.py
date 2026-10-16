"""Mechanical machine-output comparison; no human/reference labels are opened.

Reserved family members never enter the manual-review projection. Their texts
are used only by a mechanical redaction filter for overlapping context, and
their machine predictions are used only for aggregate change counts.
"""
from pathlib import Path
import collections
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DEV = OUT.parent / 'rules-v37.2-development'
BASE = ROOT / 'outputs/coding-revision-20261007-r3/rules-v36.2-development/all_predictions_material_v14.jsonl'
INPUT = ROOT / 'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
PRED = OUT / 'all_predictions_material_v14_shadow.jsonl'
EXCLUSION = DEV / 'future_human_development_exclusion_metadata_frozen.json'
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    data = {r['id']: r for r in rows}
    assert len(data) == len(rows) == 4924
    return data


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    old, new, inputs = read_jsonl(BASE), read_jsonl(PRED), read_jsonl(INPUT)
    assert old.keys() == new.keys() == inputs.keys()
    meta = json.loads(EXCLUSION.read_text())
    reserved = set(meta['all_registered_members_of_reserved_families_unit_ids'])
    assert len(reserved) == 267 and reserved <= inputs.keys()
    # Mechanical privacy filter: no reserved sentence or machine prediction is
    # printed or included in the manual projection, even through context.
    reserved_texts = sorted({inputs[k]['input']['unit_text'] for k in reserved}, key=len, reverse=True)
    redaction_counts = collections.Counter()

    def redact(value):
        if isinstance(value, dict):
            return {k: redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        if not isinstance(value, str):
            return value
        for text in reserved_texts:
            if text and text in value:
                redaction_counts['exact_reserved_text_occurrences'] += value.count(text)
                value = value.replace(text, '[预留成员原句已机械遮蔽]')
        return value

    all_changes, review = [], []
    counts = collections.Counter()
    direction = collections.Counter()
    all_direction = collections.Counter()
    for key in sorted(inputs):
        before, after = old[key]['prediction'], new[key]['prediction']
        assert set(before['labels']) == set(after['labels']) == set(DIMS)
        assert all(before['labels'][d] in (0, 1) and after['labels'][d] in (0, 1) for d in DIMS)
        changed = [d for d in DIMS if before['labels'][d] != after['labels'][d]]
        if not changed:
            continue
        is_reserved = key in reserved
        group = 'reserved267_aggregate_only' if is_reserved else 'nonreserved_manual_review'
        counts[group + '_units'] += 1
        all_changes.append({'id': key, 'changed_dimensions': changed, 'reserved267': is_reserved})
        for d in changed:
            tag = f"{d}:{before['labels'][d]}->{after['labels'][d]}"
            direction[(group, tag)] += 1
            all_direction[tag] += 1
        if is_reserved:
            continue
        unit = inputs[key]['input']
        review.append(redact({
            'id': key,
            'changed_dimensions': changed,
            'machine_changes': {d: {'v36.2': before['labels'][d], 'v37.2': after['labels'][d]} for d in changed},
            'unit_text': unit['unit_text'],
            'source': unit['source'],
            'pages': unit['pages'],
            'paragraph_context': unit.get('paragraph_context'),
            'nearest_preceding_heading': unit.get('nearest_preceding_heading'),
            'immediately_preceding_paragraph': unit.get('immediately_preceding_paragraph'),
            'llm_v29_shared_context': unit.get('llm_v29_shared_context'),
            'old_changed_dimension_evidence': [e for e in before['evidence'] if e.get('dimension') in changed],
            'new_changed_dimension_evidence': [e for e in after['evidence'] if e.get('dimension') in changed],
            'new_changed_dimension_suppressions': [e for e in after['suppressions'] if e.get('dimension') in changed],
            'object_scope_dependencies': after.get('object_scope_dependencies'),
            'typed_contexts_v34': after.get('typed_contexts_v34'),
            'source_context_adaptation_log_v33': after.get('source_context_adaptation_log_v33'),
            'review_flags': after.get('review_flags'),
        }))
    summary = {
        'status': 'shadow_development_only_not_adopted',
        'n': 4924,
        'dimensions': list(DIMS),
        'inputs_sha256': sha(INPUT),
        'baseline_predictions_sha256': sha(BASE),
        'shadow_predictions_sha256': sha(PRED),
        'exclusion_metadata_sha256': sha(EXCLUSION),
        'reserved_family_members_n': 267,
        'changed_units_n': len(all_changes),
        'changed_dimension_cells_n': sum(all_direction.values()),
        'counts_by_review_group': dict(counts),
        'changes_by_dimension_direction_all': dict(all_direction),
        'changes_by_dimension_direction_and_group': {g: {k: v for (gg, k), v in direction.items() if gg == g}
                                                     for g in ('nonreserved_manual_review', 'reserved267_aggregate_only')},
        'manual_review_projection_n': len(review),
        'overlapping_context_reserved_text_redactions': dict(redaction_counts),
        'known_previously_exposed_exception': {'id': 'RECODE25-01353', 'included_in_projection': False,
                                             'instruction': 'Root permits only a separately flagged check of the previously exposed target.'},
        'reference_or_human_labels_loaded': False,
        'scores_or_kappa_computed': False,
    }
    save('changes_all_ids_dimensions.json', all_changes)
    save('mechanical_comparison_summary.json', summary)
    save('nonreserved_changes_manual_review_projection.json', review)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
