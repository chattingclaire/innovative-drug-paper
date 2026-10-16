"""Read saved v5 S3 outputs and source bytes; never import candidate modules."""
from pathlib import Path
import hashlib
import json
import unicodedata

D = Path(__file__).resolve().parent
ROOT = D.parents[1]
SOURCE = ROOT / '00-baseline/source-files/980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt'

def bind(p):
    p = Path(p).resolve(); b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def write(name, value):
    with (D / name).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')

def norm(text):
    return ''.join(unicodedata.normalize('NFKC', c) for c in text if not c.isspace())

def quotes(value, path=''):
    if isinstance(value, dict):
        if {'context_id', 'start', 'end', 'text'} <= value.keys():
            yield path, value
        for k, v in value.items():
            yield from quotes(v, path + '/' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from quotes(v, path + '/' + str(i))

raw = SOURCE.read_bytes(); text = raw.decode('utf8', errors='strict')
source_binding = bind(SOURCE)
assert source_binding['sha256'] == '980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036'
rows = json.loads((D / 'execution-results.json').read_bytes())
readback = []; scopes = []; consumers = []; context_checks = []; anchors = []
for row in rows:
    rid = row['record_id']
    unit = json.loads((D / 'semantic-units' / (rid + '.json')).read_bytes())
    contexts = {c['context_id']: c for c in unit['contexts']}
    for c in contexts.values():
        if c['kind'] != 'source_textleaf': continue
        ref = c['source_ref']; loc = ref['locator']; a, b = loc['unicode_code_point_interval_half_open']
        assert loc['snapshot_absolute_path'] == str(SOURCE)
        assert loc['snapshot_sha256'] == ref['sha256'] == source_binding['sha256']
        assert text[a:b] == c['text']
        assert loc['utf8_byte_interval_half_open'] == [len(text[:a].encode()), len(text[:b].encode())]
        context_checks.append({'record_id': rid, 'context_id': c['context_id'], 'unicode_interval': [a,b], 'exact_leaf_and_byte_interval': True})
    unique = {}
    for path, q in quotes(row):
        c = contexts[q['context_id']]; a, b = q['start'], q['end']
        assert isinstance(a, int) and isinstance(b, int) and 0 <= a < b <= len(c['text'])
        assert c['text'][a:b] == q['text']
        ref = q.get('source_ref', c['source_ref']); loc = ref['locator']
        assert ref == c['source_ref']
        key = (q['context_id'], a, b, q['text'])
        if key not in unique:
            item = {'record_id': rid, 'context_id': q['context_id'], 'text': q['text'], 'context_interval': [a,b], 'occurrence_paths': [], 'context_literal_match': True}
            if 'snapshot_absolute_path' in loc:
                l0, l1 = loc['unicode_code_point_interval_half_open']; s, e = l0+a, l0+b
                assert loc['snapshot_absolute_path'] == str(SOURCE)
                assert source_binding['sha256'] == loc['snapshot_sha256'] == ref['sha256']
                assert text[l0:l1] == c['text'] and text[s:e] == q['text']
                item.update(original_source=source_binding, actual_unicode_interval=[s,e], actual_utf8_interval=[len(text[:s].encode()),len(text[:e].encode())], actual_line_range_1based=[text[:s].count('\n')+1,text[:e].count('\n')+(0 if text[:e].endswith('\n') else 1)], original_literal_and_identity_match=True)
            else:
                item.update(original_literal_and_identity_match=False, scope='exact original packet context only; no new snapshot-coordinate claim')
            unique[key] = item
        unique[key]['occurrence_paths'].append(path)
    readback.extend(unique.values())
    typed = [r for r in row['trace']['relations'] if r['details'].get('relation_subtype') == 'SE_primary_literal_operational_standard']
    assert len(typed) == 1
    rel = typed[0]; details = rel['details']; proof = details['closure_proof']
    assert details['affected_dimensions'] == ['S','E','Ec'] and details['SE_scope_verified'] is True
    assert details['version_binding']['source_sha256'] == proof['source_sha256'] == source_binding['sha256']
    assert proof['actual_next_normative_boundary'] is True and proof['EOF_is_not_closure'] is True
    ca, cb = proof['content_snapshot_span']; ba, bb = proof['actual_next_boundary_snapshot_span']; ua, ub = proof['current_snapshot_span']
    assert details['standard_text'] == text[ca:cb]
    assert proof['current_exact_raw_text'] == text[ua:ub] and norm(text[ua:ub]) == norm(unit['text'])
    assert ba == proof['group_snapshot_span'][1] and cb <= ba
    content_spans = proof['content_quote_snapshot_spans']
    assert content_spans[0][0] == ca and content_spans[-1][1] == cb
    assert all(content_spans[i][1] == content_spans[i+1][0] for i in range(len(content_spans)-1))
    boundary_texts = [q['text'] for q in proof['boundary_quotes']]
    assert boundary_texts == [text[ba:bb]]
    source_line = 15 if rid != 'RECODE25-00045' else 33
    safety = text.splitlines(keepends=True)[source_line-1]
    assert safety.rstrip('\r\n') in details['standard_text']
    typed_units = [u for u in row['natural_units'] if u['details'].get('relation_subtype') == 'SE_primary_literal_operational_standard']
    excluded_quotes = proof['boundary_quotes'] + proof['identity_quotes'] + proof['proof_only_quotes']
    assert all(norm(q['text']) != u['text'] for q in excluded_quotes for u in typed_units)
    typed_positive = [p for p in row['accepted_positive_consumers'] if p['unit_details'].get('relation_subtype') == 'SE_primary_literal_operational_standard']
    assert {p['dimension'] for p in typed_positive} == {'S','E'}
    assert all(p['dimension'] in {'S','E','Ec'} and p['consumer_contract_matched'] for p in typed_positive)
    s_positive = [p for p in typed_positive if p['dimension']=='S']; assert len(s_positive)==1
    assert '安全性' in s_positive[0]['unit_text']
    assert all(p['consumer_contract_matched'] for p in row['accepted_positive_consumers'])
    for dim, dec in row['decisions_first_v5_execution'].items():
        for field in ('current_anchor','current_proposition'):
            q = dec.get(field)
            if q:
                assert unit['text'][q['start']:q['end']] == q['text']
                anchors.append({'record_id':rid,'dimension':dim,'field':field,'quote':q,'saved_current_literal_match':True})
    requests = [r for r in row['trace']['source_requests'] if r.get('resolution_path')=='primary_literal_complete_operative_standard']
    assert len(requests)==1 and requests[0]['dependency_status']=='resolved'
    assert row['trace']['material_requests']==[]
    report = {'record_id':rid, 'current':unit['text'], 'actual_S':row['actual_S'], 'expected_historical_S':row['expected_S'], 'standard_family':details['standard_family'], 'content_snapshot_span':[ca,cb], 'content_line_range_1based':[text[:ca].count('\n')+1,text[:cb].count('\n')+(0 if text[:cb].endswith('\n') else 1)], 'standard_current_relationship':details['action_scope'], 'safety_original_line':source_line, 'safety_original_quote':safety, 'actual_S_positive_consumer_unit':s_positive[0], 'boundary_quote':text[ba:bb], 'boundary_snapshot_span':[ba,bb], 'boundary_and_identity_and_proof_only_not_generated_as_typed_content_units':True, 'typed_units_N':len(typed_units), 'typed_positive_dimensions':sorted({p['dimension'] for p in typed_positive}), 'same_version_snapshot_and_literal_current_verified':True, 'request_status':'resolved', 'remaining_material_requests':[], 'not_risk_occurred_or_all_conditions_failed':True}
    if rid=='RECODE25-00045':
        tail = text[cb:ba]
        assert '品种清单' in tail and tail not in details['standard_text']
        assert not any('品种清单' in u['text'] for u in typed_units)
        report.update(status_list_tail_snapshot_span=[cb,ba], status_list_tail_text=tail, status_list_not_consumed_as_standard=True)
    if rid=='RECODE25-00038':
        report['OR_reading'] = '完整当前或命题保留；S依据实质纳入标准后果分支，未交书面说明的手续分支本身不证明S，未另建/执行拆分病例'
    scopes.append(report)
    consumers.extend({'record_id':rid, **p} for p in row['accepted_positive_consumers'])
only_if = [u for row in rows for u in row['natural_units'] if u['details'].get('only_IF_consumers')]
summary = {'saved_cases_checked_N':3, 'source_textleaf_geometry_checks_N':len(context_checks), 'unique_context_quotes_checked_N':len(readback), 'quote_occurrences_checked_N':sum(len(q['occurrence_paths']) for q in readback), 'raw_snapshot_verified_unique_quotes_N':sum(q['original_literal_and_identity_match'] for q in readback), 'packet_only_unique_quotes_N':sum(not q['original_literal_and_identity_match'] for q in readback), 'current_anchor_checks_N':len(anchors), 'typed_SE_units_N':sum(s['typed_units_N'] for s in scopes), 'typed_SE_positive_consumers_N':sum(p['unit_details'].get('relation_subtype')=='SE_primary_literal_operational_standard' for p in consumers), 'accepted_positive_consumers_N':len(consumers), 'consumer_contract_mismatch_N':sum(not p['consumer_contract_matched'] for p in consumers), 'natural_only_IF_units_N':len(only_if), 'only_IF_positive_intersection_tested':bool(any(p['unit_details'].get('only_IF_consumers') for p in consumers)), 'only_IF_coverage_limit':'未生成only_IF单位，本S3不检验only_IF正消费者交集；未注入构造关系', 'additional_candidate_calls_N':0, 'semantic_read_scope':'逐条完整当前命题；原件具名突破性程序标题及第3–38行必要同版范围/条件/终止/真实边界；全源字节及15个leaf范围是机械校验，不声称语义读完其他程序', 'actual_S':[r['actual_S'] for r in rows]}
write('trace-original-quote-readback.json',readback)
write('source-leaf-geometry-readback.json',context_checks)
write('saved-current-anchor-readback.json',anchors)
write('standard-consumer-and-boundary-readback.json',scopes)
write('accepted-consumer-path-readback.json',consumers)
write('trace-readback-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
