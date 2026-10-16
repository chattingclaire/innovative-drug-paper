"""Repair a verified list predicate missing from four child-unit contexts.

Source-only correction discovered by literal-evidence QA. No label or metric input.
"""
from pathlib import Path
import copy
import hashlib
import json
import unicodedata

HERE = Path(__file__).resolve().parent

def jl(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKC', s)
                   if not c.isspace() and not unicodedata.category(c).startswith('P'))

ll = jl(HERE / 'effective_blind_inputs_v6.jsonl')
rr = jl(HERE / 'rule_inputs_shared_v6.jsonl')
lb = {r['id']: r for r in ll}
rb = {r['id']: r for r in rr}
head = lb['RECODE25-02237']
cert = head['contexts']['verified_context_certificates']['verified_following_list_v27']
source = Path(rb[head['id']]['input']['source'])
assert sha(source) == cert['source_sha256']
source_text = norm(source.read_text())
for part in cert['contexts']:
    assert norm(part['text']) in source_text
    assert sha(Path(part['candidate_path'])) == part['candidate_sha256']
assert cert['structure_boundary']['all_paragraphs_in_interval_included']
assert cert['structure_boundary']['first_paragraph'] == 'p0004'
assert cert['structure_boundary']['last_paragraph'] == 'p0007'
parent = copy.deepcopy(cert['contexts'][0])
parent['relationship'] = 'Verified governing predicate for the three enumerated conditions; includes the continuation within item three.'
affected = [f'RECODE25-{i:05d}' for i in range(2238, 2242)]
for rid in affected:
    assert norm(lb[rid]['text']) in source_text
    c = lb[rid]['contexts']
    c['verified_parent_context'] = [copy.deepcopy(parent)]
    c['verified_context_certificates']['verified_parent_list_v7'] = {
        'source_path': str(source), 'source_sha256': sha(source),
        'original_unit_sha256': hashlib.sha256(lb[rid]['text'].encode()).hexdigest(),
        'complete_source_structure': copy.deepcopy(cert),
        'usage': 'Resolve this child item as an eligibility condition for the 30-day trial-review channel. Do not transfer dimensions from sibling items or the heading.'
    }
    rb[rid]['input']['llm_v29_shared_context'] = copy.deepcopy(c)
    rb[rid]['input']['verified_parent_context'] = copy.deepcopy(c['verified_parent_context'])
    rb[rid]['input']['verified_parent_list_v7'] = copy.deepcopy(c['verified_context_certificates']['verified_parent_list_v7'])
for name, rows in [('effective_blind_inputs_v7.jsonl', ll), ('rule_inputs_shared_v7.jsonl', rr)]:
    (HERE / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
mapping = json.loads((HERE / 'admin/PRIVATE_mapping.json').read_text())
future = json.loads((HERE / 'admin/future_human_sampling_PRIVATE.json').read_text())
assert not any(m['original_id'] in affected for m in mapping)
assert not any(m['original_id'] in affected for m in future['sample'])
base = jl(HERE.parent / 'recall-revision-20261007/effective_blind_inputs_v30_v3.jsonl')
changed = [a['id'] for a, b in zip(ll, base) if a != b]
assert len(ll) == 4924 and len(changed) == 27
assert all(a['text'] == b['text'] for a, b in zip(ll, base))
assert {r['id'] for r in ll[2225:2250]}.issuperset(affected)
batch = ll[2225:2250]
(HERE / 'llm-v31/affected_complete_batch_v7.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in batch))
manifest = {
    'source_path': str(source), 'source_sha256': sha(source),
    'source_url': 'https://mpa.shaanxi.gov.cn/zfxxgk/fdzdgknr/wjtz/zswj/202509/t20250917_3568335.html',
    'source_structure': 'section 3, p0004-p0007, before section 4',
    'affected_ids_incremental': affected, 'total_affected_ids_from_v3': changed,
    'total_changed_from_v3': 27, 'unit_text_changes': 0, 'unaffected_v3_n': 4897,
    'new_llm_input_sha256': sha(HERE / 'effective_blind_inputs_v7.jsonl'),
    'new_rule_input_sha256': sha(HERE / 'rule_inputs_shared_v7.jsonl'),
    'final_changed_original_batches': [57, 58, 68, 90, 133],
    'source_v6_manifest_sha256': sha(HERE / 'material_v6_manifest.json'),
    'current_300_reference_intersection': [], 'future_240_human_intersection': [],
    'selection_not_based_on_labels': True,
    'replacement': 'Unconditional real re-execution of the complete original batch 90 for I/F and for S/E/Ec, with their respective frozen prompts. Keep original failed attempts and split repair attempts.'
}
(HERE / 'material_v7_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'incremental_changed': 4, 'total_changed': 27,
                  'new_original_batch': 90, 'current_reference_unchanged': True,
                  'future_human_unchanged': True}, ensure_ascii=False))
