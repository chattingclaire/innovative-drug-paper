"""Append complete law text to three source-selected list leads; no labels loaded."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PATCH = BASE / 'runtime/literal_failure_diagnosis02/suggested_source_context_patch02.json'
LLM = BASE / '共用纯来源材料02/source_only_with_scope02.jsonl'
RULE = BASE / '共同材料修订01/rule_inputs_shared_material_revision01.jsonl'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert sha(PATCH) == 'e18ccdf7260ec12b758eb9a4cdc591a088e9852fa93ce3a8f421edde5baf03eb'
    patch = json.loads(PATCH.read_text())
    assert sha(LLM) == patch['target_frozen_input_sha256'] == '7eb8323f81bbed844cc19d9859e1c5faf432f18094201130e91d91e5743ecfa1'
    assert sha(RULE) == '53719b5cfde4df7421cabb0229fc6065e951f0741248a1af6a56e6e0232ad18d'
    for key in ('source_pdf', 'source_body_text', 'source_candidate'):
        assert sha(patch[key]['path']) == patch[key]['sha256']
    by_id = {p['id']: p for p in patch['proposed_patch']}
    assert set(by_id) == {'RECODE25-00929', 'RECODE25-01956', 'RECODE25-02286'}
    rule_lines = RULE.read_text().splitlines(keepends=True)
    llm_lines = LLM.read_text().splitlines(keepends=True)
    rule_rows = {r['id']: r for r in map(json.loads, rule_lines)}
    source_lines = Path(patch['source_body_text']['path']).read_text().splitlines()
    changed = []
    for i, line in enumerate(llm_lines):
        row = json.loads(line)
        rid = row['id']
        if rid not in by_id:
            continue
        p = by_id[rid]
        assert row['text'] == p['relation']['current_unit_text']
        assert any(c.get('text') == p['relation']['direct_list_reference_text'] for c in row['contexts'])
        contexts = p['contexts_to_append']
        assert len(contexts) == 10
        donor = rule_rows[p['relation']['same_source_member_unit_id']]['input']['llm_v29_shared_context']['explicitly_cited_articles_v10']
        assert len(donor) == 10
        for c, raw, verified in zip(contexts, donor, patch['source_verification_per_complete_article_segment']):
            assert c['text'] == raw['text']
            assert c['structure']['paragraph_id'] == raw['paragraph_id'] == verified['paragraph_id']
            a, b = verified['official_text_character_span_0_based']
            assert source_lines[verified['official_text_line'] - 1][a:b] == c['text']
        assert ''.join(c['text'] for c in contexts[:6]) == source_lines[20]
        assert ''.join(c['text'] for c in contexts[6:]) == source_lines[22]
        assert not set(c['context_id'] for c in contexts) & set(c['context_id'] for c in row['contexts'])
        row['contexts'].extend(copy.deepcopy(contexts))
        llm_lines[i] = json.dumps(row, ensure_ascii=False) + '\n'
        r = json.loads(rule_lines[i])
        assert r['id'] == rid and r['input']['unit_text'] == row['text']
        shared = r['input']['llm_v29_shared_context']
        assert not shared.get('explicitly_cited_articles_v10')
        shared['explicitly_cited_articles_v10'] = copy.deepcopy(donor)
        rule_lines[i] = json.dumps(r, ensure_ascii=False) + '\n'
        changed.append({'id': rid, 'line': i + 1, 'appended_contexts': 10,
                        'relation': p['relation'], 'source_verification': patch['source_verification_per_complete_article_segment']})
    assert len(changed) == 3
    outputs = {'llm_inputs': ROOT / 'source_only_with_scope03.jsonl',
               'rule_inputs': ROOT / 'rule_inputs_material03.jsonl'}
    for key, lines in (('llm_inputs', llm_lines), ('rule_inputs', rule_lines)):
        with outputs[key].open('x') as out:
            out.writelines(lines)
    report = {'status': 'complete_actual_source_patch_not_label_validation',
              'manual_sha256': '5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c',
              'base_llm': {'path': str(LLM), 'sha256': sha(LLM)},
              'base_rules': {'path': str(RULE), 'sha256': sha(RULE)},
              'patch': {'path': str(PATCH), 'sha256': sha(PATCH)},
              'outputs': {k: {'path': str(p), 'sha256': sha(p)} for k, p in outputs.items()},
              'n': 4924, 'changed': changed,
              'all_other_lines_byte_identical': True, 'current_text_changed': False,
              'labels_or_metrics_read': False, 'model_or_coder_called': False,
              'unresolved_source_ids_not_silently_repaired': ['RECODE25-00064']}
    with (ROOT / 'material_patch_execution03.json').open('x') as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write('\n')
    print(json.dumps({'n': 4924, 'changed_ids': sorted(by_id), 'outputs': report['outputs']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
