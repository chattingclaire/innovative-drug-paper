"""The one predeclared approved full-row source integration; no reference."""
import hashlib
import json
import traceback
from pathlib import Path
from source_packet import semantic_unit, source_inventory
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

base = Path(__file__).parent
binding = json.loads((base / 'branch-control-material-binding-v09.json').read_text())
declared = json.loads((base / 'v09-purpose-branch-predeclaration.json').read_text())
view = None
report = {'status': 'started', 'binding': binding, 'control_expectations': declared['approved_single_source_integration']}
try:
    payload = Path(binding['one_selected_source_control_path']).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == binding['one_selected_source_control_sha256']
    assert hashlib.sha256((base / 'source_packet.py').read_bytes()).hexdigest() == binding['source_packet_sha256']
    bundle = json.loads(payload)
    unit = semantic_unit(bundle)
    view = RelationView(unit)
    decisions = judge(view)
    validate_decisions(unit, decisions)
    labels = {d: v['value'] for d, v in decisions.items()}
    basic = [r for r in view.traces() if r['details'].get('protection_branch') == 'base_table_arrangement']
    exceptions = [r for r in view.traces() if r['details'].get('protection_branch') == 'conditional_table_exception']
    inventory = {r['resource_id']: r for r in source_inventory(bundle)}
    event_checks = [e['resource_id'] in inventory and e['source_sha256'] == inventory[e['resource_id']]['source_sha256']
        and e['view_sha256'] == inventory[e['resource_id']]['available_views'].get(e['view']) for e in view.source_view_events]
    read_keys = {(e['resource_id'], e['view']) for e in view.source_view_events}
    use_checks = [((u['resource_id'], u['view']) in read_keys) for r in view.source_relation_traces for u in r['used_source_views']]
    checks = {
        'expected_labels': labels == declared['approved_single_source_integration']['expected_labels'],
        'one_basic_branch': len(basic) == 1,
        'one_exception_branch': len(exceptions) == 1,
        'basic_six_year_current_anchor': bool(basic and basic[0]['details']['current_consequence_anchor']['text'] == '6年'),
        'basic_explicit_appendix_and_article_definition': bool(basic and [s['article'] for s in basic[0]['details']['reference_chain']] == [3, 5]),
        'basic_trial_data_safety_efficacy_definition': bool(basic and any('用于证明药品安全性、有效性' in e['text'] for e in basic[0]['context_evidence'])),
        'four_year_exception_chain_only_seven_two_to_six': bool(exceptions and [(s['article'], s['clause']) for s in exceptions[0]['details']['reference_chain']] == [(7, 2), (6, None)]),
        'first_indication_not_transferred': not any('首次提交境内外均未获批的新适应症' in e['text'] for r in basic + exceptions for e in r['context_evidence']),
        'complete_fixed_row_propositions': all(r['current_anchor']['text'] == unit['text'] for r in basic + exceptions),
        'source_view_hashes_exact_inventory': bool(event_checks) and all(event_checks),
        'selected_use_has_actual_read': bool(use_checks) and all(use_checks),
    }
    report.update(status='pass' if all(checks.values()) else 'failed', checks=checks, labels=labels,
        current_full_text=unit['text'], decisions=decisions, relation_traces=view.traces(),
        source_relation_traces=view.source_relation_traces, source_view_events=view.source_view_events,
        source_requests=view.source_requests, material_requests=view.material_requests)
except Exception as error:
    report.update(status='technical_failure', error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    if view:
        report.update(source_view_events=view.source_view_events, relation_traces=view.traces(), source_requests=view.source_requests)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['status'] == 'pass' else 1)
