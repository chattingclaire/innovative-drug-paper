"""Check new overlay against inherited constructed controls and purpose guard."""
import json
import sys
import hashlib
from pathlib import Path
R = Path(__file__).resolve().parent
sys.path.insert(0, str(R/'runtime'))
from rules_repair_v37 import revise
from rule_support import rebuild

def seed(text, dims, rule='inherited_constructed_expected_route'):
    return {'judgement_status': 'determined', 'suppressions': [],
            'evidence': [{'dimension': d, 'rule': rule, 'start': 0, 'end': len(text),
                          'text': text, 'matching_text': text,
                          'subtype': 'research_support' if d == 'I' else 'access' if d == 'F' else None}
                         for d in dims]}

rows = []
for name in ('legacy_v35_controls.json', 'inherited67_controls.json', 'constructed_controls_results.json'):
    packet = json.loads((R/name).read_text())
    for row in packet['rows']:
        text = row.get('constructed_text', row.get('text'))
        if 'expected' in row:
            expected = set(row['expected'])
        else:
            expected = {d for d in ('F', 'S') if row.get('expected_new_'+d)}
        record = {'unit_text': text, **(row.get('context_fixture') or {})}
        actual = rebuild(revise(record, seed(text, expected)))
        got = {d for d, value in actual['labels'].items() if value}
        assert got == expected, (name, row['name'], got, expected, actual)
        for e in actual['evidence']+actual['suppressions']:
            if 'start' in e:
                assert text[e['start']:e['end']] == e['text']
        rows.append({'control_packet': name, 'name': row['name'],
                     'expected_overlay_dimensions': sorted(expected), 'actual': sorted(got), 'pass': True})

freeze = json.loads((R/'purpose_scope_supplement_controls_freeze.json').read_text())
assert hashlib.sha256(Path(freeze['path']).read_bytes()).hexdigest() == freeze['sha256']
purpose = []
for row in json.loads(Path(freeze['path']).read_text())['rows']:
    text = row['text']
    result = seed(text, [])
    for quote, rule in ((row['purpose_quote'], 'V27_I_data_protection_purpose'),
                        (row['other_quote'], 'V28_I_protection_lifecycle')):
        if quote is None:
            continue
        a = text.index(quote)
        result['evidence'].append({'dimension': 'I', 'rule': rule, 'start': a,
                                  'end': a+len(quote), 'text': quote, 'matching_text': quote,
                                  'subtype': 'research_support'})
    actual = rebuild(revise({'unit_text': text}, result))
    suppressed = any(e.get('suppressed_rule') == 'V27_I_data_protection_purpose' for e in actual['suppressions'])
    assert suppressed == row['expected_purpose_suppressed'], (row, actual)
    assert actual['labels']['I'] == row['expected_I'], (row, actual)
    purpose.append({'name': row['name'], 'constructed_text': text, 'purpose_suppressed': suppressed,
                    'expected_purpose_suppressed': row['expected_purpose_suppressed'],
                    'actual_I': actual['labels']['I'], 'pass': True})

report = {'all_checks_pass': True, 'inherited_overlay_n': len(rows),
          'purpose_preservation_n': len(purpose), 'not_independent_validation': True,
          'test_scope': 'Overlay-only preservation of existing constructed expectations using seeded inherited routes; original four module/control tests separately reproduce the inherited expectations.',
          'rows': rows, 'purpose_rows': purpose,
          'purpose_frozen_controls_sha256': freeze['sha256'],
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(R/'patch_overlay_controls_results_v37.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ('all_checks_pass', 'inherited_overlay_n', 'purpose_preservation_n')}, ensure_ascii=False))
