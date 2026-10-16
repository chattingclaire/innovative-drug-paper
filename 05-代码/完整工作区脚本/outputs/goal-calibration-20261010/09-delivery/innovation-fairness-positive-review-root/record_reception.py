"""Record this delivery without changing frozen predictions or prior judgments."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def binding(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b),
            'sha256': hashlib.sha256(b).hexdigest()}


def save_new(p, d):
    with p.open('x') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    at = datetime.now(timezone.utc).isoformat()
    saved = json.loads((HERE / 'saved-readback.json').read_text())
    workbook = HERE / '创新性与公平性-全部阳性查看表.xlsx'
    assert saved['workbook'] == binding(workbook)
    counts = json.loads((HERE / 'input-and-material-reception.json').read_text())['counts']
    audit = ROOT / '08-audits/ai800-disagreement-semantic-root'
    joined = json.loads((audit / 'joined-review.json').read_text())
    extra = json.loads((audit / 'remaining-positive271-sol/reviews.json').read_text())
    assert joined['label_slots_reviewed'] == 66 and len(extra) == 2
    assert all(r['source_id'] == 'RECODE25-04592' and r['review_value'] == 1
               for r in extra)
    campaign = ROOT / '06-coding/native-full4481-v1-sol'
    selected = list(campaign.glob('batch-*/root-selection.json'))
    n = sum(len(json.loads((p.parent / 'first.json').read_text())['records'])
            for p in selected)
    record = {
        'at_utc': at,
        'kind': 'actual all-positive extraction, source-based review and saved workbook verification',
        'counts': counts,
        '800_positive_slots_AI_reviewed': 68,
        'AI_review_is_human_adjudication': False,
        '800_53_disagreement_assessment_counts': joined['assessment_counts'],
        '800_53_supported_rule_omissions': 41,
        '800_53_suggested_AI_zero': 5,
        '800_53_undetermined_boundaries': 7,
        'full4481_rule_positive_slots_extracted': 102,
        'full4481_new_rule_positive_semantic_review_status': 'agent reviewing; not received or counted as completed here',
        'full4481_rule_positives_are_fullLLM_union': False,
        'original_values_and_frozen_sources_modified': False,
        'all170_native_links_and_saved_cell_values_verified': True,
        'workbook': binding(workbook),
        'readback': binding(HERE / 'saved-readback.json'),
        'source_consumption_addendum': {
            'record': 'RECODE25-04592', 'blind_id': 'A-000271',
            'auxiliary_AI': {'I': 1, 'F': 1},
            'rule_frozen_values': {'I': None, 'F': None},
            'independent_AI_review': {'I': 1, 'F': 1},
            'finding': 'same-version full original exists, but necessary article59 condition was not consumed through the rule finite source interface',
            'source_version_equality_proves_equal_consumer_coverage': False,
            'preserve_current_NULL_and_prepare_neutral_material_interface_revision': True,
            'review': binding(audit / 'remaining-positive271-sol/reviews.json')},
        'formal4481_count_only_observation': {
            'selected_terminal_batches': len(selected), 'selected_records': n,
            'not_yet_selected_records': 4481 - n,
            'controller_session': 62929, 'latest_specific_handle_poll': 'live, no terminal result',
            'partial_label_comparison_performed': False},
        'paper_or_formal_acceptance_complete': False,
        'remaining': ['finish S/E/Ec discrepancy review and full rule I/F positive review',
                      'adjudicate finite boundary questions and repair general rules/material consumption in a separately frozen candidate',
                      'inspect a diagnostic sample of common negatives for shared omissions',
                      'complete true-human independent reference, weighted validation, stability and downstream robustness before final manuscript']}
    out = ROOT / 'logs/root-all-positive-review-delivery-reception-20261010.json'
    save_new(out, record)
    p = ROOT / 'progress.json'
    progress = json.loads(p.read_text())
    progress['ai800_all_positive_review_delivery_actual'] = record
    progress['updated_at_utc'] = at
    progress['current_goal_turn_classification'] = {
        'type': 'substantive new semantic evidence and completed user-viewable artifact',
        'stopped_goal': False, 'same_blocking_condition_recurred': False,
        'new_work': 'two remaining I/F positive slots reviewed; all68 sample positives and all102 full rule positives extracted; 170 saved links/cell rows verified',
        'receipt': str(out)}
    tmp = p.with_suffix('.reception.tmp')
    tmp.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(p)
    print(json.dumps({'receipt': str(out), 'positive_slots_reviewed': 68,
                      'rule_full_positive_slots_extracted': 102,
                      'goal_complete': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
