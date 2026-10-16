import json,hashlib
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def at(obj,p):
    for s in p.strip('/').split('/'):
        if s:obj=obj[int(s)] if isinstance(obj,list) else obj[s]
    return obj
rows=json.loads((HERE/'reviews.json').read_text());scope=json.loads((HERE/'scope.json').read_text())
binding=json.loads((HERE/'input-bindings.json').read_text());errors=[];checks=Counter();cache={}
def data(p):
    if p not in cache:cache[p]=json.loads(Path(p).read_text())
    return cache[p]
assert len(rows)==102
assert len({(r['source_id'],r['dimension']) for r in rows})==102
assert len({r['source_id'] for r in rows})==81
expected={(x['source_id'],x['dimension']) for x in scope['items']}
assert {(r['source_id'],r['dimension']) for r in rows}==expected
for x in binding['frozen_inputs']:
    assert sha(x['file'])==x['sha256'];checks['input_file_sha_matches']+=1
for r in rows:
    assert r['rule']==1 and r['dimension'] in ['I','F']
    assert r['review_value'] in [0,1,'未定']
    assert r['is_true_human_review'] is False and r['metadata_only_not_label_evidence'] is True
    p=r['packet_file'];d=data(p);b=d['source_bundle'];assert sha(p)==r['packet_sha256'];checks['packet_sha_matches_dimension_items']+=1
    assert b['source_record']['text']==r['current_text']==r['current_quote'];checks['complete_current_quotes_exact']+=1
    assert hashlib.sha256(r['current_text'].encode()).hexdigest()==r['current_text_sha256'];checks['current_text_sha_matches']+=1
    if r.get('prior_review'):
        pr=r['prior_review'];assert sha(pr['file'])==pr['sha256'];assert sha(pr['prior_material_file'])==pr['prior_material_sha256']
        old=data(pr['prior_material_file']);assert old==b;checks['reused_entire_source_bundle_equal']+=1
        assert pr['original_review']['review_value']==r['review_value'];checks['old_review_value_preserved']+=1
    for e in r['used_context_quotes']:
        q=e.get('text',e.get('quote'));f=e['file'];p=e.get('json_pointer');assert q
        if p:
            obj=at(data(f),p);raw=obj if isinstance(obj,str) else obj['text'];assert q in raw,(r['source_id'],p)
            if e.get('local_unicode_span_half_open'):
                a,z=e['local_unicode_span_half_open'];assert raw[a:z]==q
            checks['context_quotes_exact_in_named_JSON_leaf']+=1
            # When a verbatim source resource supplies original source offsets,
            # check that bounded source text against its actual frozen bytes.
            if isinstance(obj,dict):
                loc=obj.get('locator',{})
                source=loc.get('snapshot_absolute_path');rng=loc.get('unicode_code_point_interval_half_open')
                if source and rng:
                    assert sha(source)==loc['snapshot_sha256'];orig=Path(source).read_text()
                    assert orig[rng[0]:rng[1]]==obj['text'];checks['verbatim_bounded_original_snapshot_matches']+=1
        else:
            raw=Path(f).read_text();assert q in raw
            a,z=e['local_unicode_span_half_open'];assert raw[a:z]==q
            assert sha(f)==e['locator']['source_sha256'];checks['outside_bounded_JSON_same_package_original_quote_verified']+=1
    for c in r.get('manual_clauses',[]) if isinstance(r.get('manual_clauses'),list) else []:
        if isinstance(c,dict) and 'line_1based' in c:
            lines=Path(r['manual_file']).read_text().splitlines();assert lines[c['line_1based']-1]==c['text'];checks['manual_clause_quotes_exact']+=1

# Match every selected packet to the actually delivered rule bundle without
# reading or comparing any formal LLM partial result.
targets={r['source_id'] for r in rows};delivered={}
file=next(x['file'] for x in binding['frozen_inputs'] if x['file'].endswith('/delivered-complete-source-bundles.jsonl'))
with Path(file).open() as f:
    for line in f:
        b=json.loads(line);sid=b['source_record']['id']
        if sid in targets:delivered[sid]=b
assert set(delivered)==targets
for sid,b in delivered.items():
    r=next(x for x in rows if x['source_id']==sid);assert data(r['packet_file'])['source_bundle']==b;checks['packet_exact_equal_rule_delivered_bundle_unique_records']+=1

for x in binding['frozen_inputs']:assert sha(x['file'])==x['sha256']
new=sum(not bool(r.get('prior_review')) for r in rows);old=len(rows)-new
assert new==89 and old==13
validation=dict(status='passed',review_dimension_items=102,unique_records=81,new_actual_read_dimension_items=89,
    prior_review_reuse_dimension_items=13,check_counts=dict(checks),errors=[],
    source_inputs_unchanged_at_validation=True,original_workbook_written=False,rule_rerun=False,
    formal_LLM_partial_output_read=False,new_Codex_CLI_launched=False,
    limitation='Exact quote/hash/equality checks validate provenance; nonhuman semantic judgments are not ground truth or human accuracy estimates. Old F reviews preserve their available-context trace without claiming every trace quote was actually used.')
(HERE/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(validation,ensure_ascii=False,indent=2))
