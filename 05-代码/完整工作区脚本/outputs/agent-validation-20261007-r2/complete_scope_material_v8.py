"""Source-only completion of two verified scope/list structures; no labels read."""
from pathlib import Path
import copy, hashlib, json, unicodedata, re
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC', s) if not c.isspace() and not unicodedata.category(c).startswith('P'))
def dump(p, d): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')

ll = jl(HERE/'effective_blind_inputs_v7.jsonl'); rr = jl(HERE/'rule_inputs_shared_v7.jsonl')
lb = {r['id']:r for r in ll}; rb = {r['id']:r for r in rr}
cde_ids = [f'RECODE25-{i:05d}' for i in range(4149,4200)]
ri = rb[cde_ids[0]]['input']; source = Path(ri['source']); candidate = Path(ri['candidate_file'])
assert sha(source) == ri['source_sha256'] and sha(candidate) == ri['candidate_sha256']
paras = json.loads(candidate.read_text())['paragraphs']
section = [p for p in paras if 2 <= int(p['id'][1:]) <= 11]
assert len(section) == 10 and paras[11]['text'] == '二、工作流程'
pdf = PdfReader(source)
page_texts = [re.sub(r'(?m)^\s*—\s*\d+\s*—\s*$', '', pdf.pages[i].extract_text()) for i in (0,1)]
full = norm('\n'.join(page_texts))
for p in section: assert norm(p['text']) in full, p['id']
scope_parts = [{**p, 'source_path':str(source), 'source_sha256':sha(source),
                'candidate_path':str(candidate), 'candidate_sha256':sha(candidate),
                'relationship':'Actual section 1 governing scope, qualifications, and time limits. Current-unit proposition still controls coding.'} for p in section]
for rid in cde_ids:
    c = lb[rid]['contexts']
    c['verified_scope_context_v8'] = copy.deepcopy(scope_parts)
    c['verified_context_certificates']['verified_scope_context_v8'] = {
        'source_path':str(source), 'source_sha256':sha(source),
        'candidate_path':str(candidate), 'candidate_sha256':sha(candidate),
        'source_pages':[1,2], 'first_paragraph':'p0002', 'last_paragraph':'p0011',
        'next_structure':'二、工作流程', 'source_normalized_substring_verified':True,
        'normalization':'NFKC, ignore whitespace/Unicode punctuation; remove only independently reread standalone PDF page-number lines — 1 — and — 2 —.',
        'usage':'Resolve explicit references to this work specification and the actual eligibility/time-limit predicate; never copy all scope dimensions into routine workflow units.'}
    rb[rid]['input']['llm_v29_shared_context'] = copy.deepcopy(c)
    rb[rid]['input']['verified_scope_context_v8'] = copy.deepcopy(scope_parts)

nmpa_ids = [f'RECODE25-{i:05d}' for i in range(4605,4611)]
ri = rb[nmpa_ids[0]]['input']; source2 = Path(ri['source']); candidate2=Path(ri['candidate_file'])
assert sha(source2)==ri['source_sha256'] and sha(candidate2)==ri['candidate_sha256']
head=lb['RECODE25-04604']; full2=norm(source2.read_text())
structure=[{'id':x,'text':lb[x]['text'],'source_path':str(source2),'source_sha256':sha(source2)} for x in ['RECODE25-04604']+nmpa_ids]
for p in structure: assert norm(p['text']) in full2
for rid in nmpa_ids:
    c=lb[rid]['contexts']
    parent={**structure[0], 'paragraph_id':head['contexts']['paragraph_context'][0]['paragraph_id'],
            'relationship':'Article 68 governing predicate for the six enumerated priority-review eligibility categories.'}
    c['verified_parent_context']=[parent]
    c['verified_context_certificates']['verified_parent_list_v8']={
        'source_path':str(source2),'source_sha256':sha(source2),
        'candidate_path':str(candidate2),'candidate_sha256':sha(candidate2),
        'complete_source_structure':copy.deepcopy(structure),
        'boundary':'Article 68 only, ending before Article 69',
        'usage':'Resolve current child as eligibility condition for priority review; do not copy sibling attributes or infer actual insurance coverage.'}
    rb[rid]['input']['llm_v29_shared_context']=copy.deepcopy(c)
    rb[rid]['input']['verified_parent_context']=copy.deepcopy(c['verified_parent_context'])
    rb[rid]['input']['verified_parent_list_v8']=copy.deepcopy(c['verified_context_certificates']['verified_parent_list_v8'])

for name, rows in [('effective_blind_inputs_v8.jsonl',ll),('rule_inputs_shared_v8.jsonl',rr)]:
    (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text()); affected=cde_ids+nmpa_ids
for coder in ('A','C'):
    rows=[{**lb[m['original_id']],'id':m['blind_id']} for m in mapping if m['coder']==coder and m['original_id'] in affected]
    dump(HERE/'confirmation'/f'agent-{coder}'/'补充材料-v8.json',{'purpose':'Source-only scope completion of existing four units. Preserve all earlier submissions. Independently reread all five dimensions under the unchanged v1.3 + v1.4 standard; no machine results or expected labels supplied.','rows':rows})
base=jl(HERE.parent/'recall-revision-20261007/effective_blind_inputs_v30_v3.jsonl')
changed=[a['id'] for a,b in zip(ll,base) if a!=b]
assert len(affected)==57 and len(changed)==84 and all(a['text']==b['text'] for a,b in zip(ll,base))
new_batches=[166,167,168,185]
patch=[r for k in new_batches for r in ll[(k-1)*25:k*25]]
(HERE/'llm-v31/affected_complete_batches_v8.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in patch))
dump(HERE/'material_v8_manifest.json',{'source_v7_manifest_sha256':sha(HERE/'material_v7_manifest.json'),
    'affected_ids_incremental':affected,'total_affected_ids_from_v3':changed,'total_changed_from_v3':84,
    'unit_text_changes':0,'unaffected_v3_n':4840,'current_reference_incremental_ids':[m['original_id'] for m in mapping if m['coder']=='A' and m['original_id'] in affected],
    'new_original_batches':new_batches,'final_changed_original_batches':[57,58,68,90,133,166,167,168,185],
    'new_llm_input_sha256':sha(HERE/'effective_blind_inputs_v8.jsonl'),'new_rule_input_sha256':sha(HERE/'rule_inputs_shared_v8.jsonl'),
    'source_only_material_change':True,'no_labels_or_metrics_used':True,
    'source_files':{str(p):sha(p) for p in (Path(rb[cde_ids[0]]['input']['source']),Path(rb[nmpa_ids[0]]['input']['source']))}})
print(json.dumps({'incremental':57,'total':84,'current_reference_affected':4,'new_full_batches':new_batches},ensure_ascii=False))
