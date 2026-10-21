from pathlib import Path
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
import json
import subprocess

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
AI = ROOT.parent / 'ai-audit800-20261010'
BASE = Path(__file__).resolve().parent
OUT = BASE / 'complete-review-reception-root'
HASHES, JSONS, TEXTS = {}, {}, {}
COUNTS = Counter()

def sha(p):
    p = str(p)
    if p not in HASHES:
        h = hashlib.sha256()
        with Path(p).open('rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk)
        HASHES[p] = h.hexdigest()
    return HASHES[p]

def binding(p):
    return {'path': str(Path(p).resolve()), 'bytes': Path(p).stat().st_size, 'sha256': sha(p)}

def data(p):
    p = str(p)
    if p not in JSONS:
        JSONS[p] = json.loads(Path(p).read_text())
    return JSONS[p]

def text(p):
    p = str(p)
    if p not in TEXTS:
        TEXTS[p] = Path(p).read_text()
    return TEXTS[p]

def pointer(obj, p):
    for key in p.lstrip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        if key:
            obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj

def bindings_in(obj):
    if isinstance(obj, dict):
        p = obj.get('path', obj.get('file'))
        if isinstance(p, str) and 'sha256' in obj and Path(p).is_file():
            assert sha(p) == obj['sha256'], p
            if 'bytes' in obj:
                assert Path(p).stat().st_size == obj['bytes'], p
            COUNTS['file_bindings_exact'] += 1
        for x in obj.values():
            bindings_in(x)
    elif isinstance(obj, list):
        for x in obj:
            bindings_in(x)

def located_quote(e):
    p = e.get('file', e.get('material_path', e.get('path')))
    q = e.get('quote', e.get('text'))
    assert p and isinstance(q, str) and q
    obj = None
    if e.get('json_pointer'):
        obj = pointer(data(p), e['json_pointer'])
        actual = obj if isinstance(obj, str) else obj['text']
        assert q in actual
        if e.get('local_unicode_span_half_open'):
            start, end = e['local_unicode_span_half_open']
            assert actual[start:end] == q
    elif 'context_index' in e:
        obj = data(p)['source_record']['contexts'][e['context_index']]
        assert obj['context_id'] == e['context_id']
        assert obj['text'] == q
        actual = obj['text']
    elif e.get('physical_pages_1based'):
        pages = e['physical_pages_1based']
        assert len(pages) == 1
        actual = subprocess.check_output(['pdftotext','-f',str(pages[0]),'-l',str(pages[0]),'-layout',p,'-'],text=True)
        assert actual == q
        assert sha(p) == e['source_sha256']
        COUNTS['PDF_original_page_quote_reextractions'] += 1
    else:
        actual = text(p)
        lines = e.get('line_range_1based_inclusive')
        if not lines:
            lines = e.get('source_ref', {}).get('locator', {}).get('lines')
        if lines:
            lo, hi = lines
            assert '\n'.join(actual.splitlines()[lo-1:hi]) == q
        elif e.get('local_unicode_span_half_open'):
            start, end = e['local_unicode_span_half_open']
            assert actual[start:end] == q
        else:
            assert q in actual
        expected = e.get('source_sha256', e.get('source_ref',{}).get('sha256',e.get('locator',{}).get('source_sha256')))
        if expected:
            assert sha(p) == expected
    if isinstance(obj, dict):
        loc = obj.get('locator', {})
        original = loc.get('snapshot_absolute_path')
        interval = loc.get('unicode_code_point_interval_half_open')
        if original and interval:
            assert sha(original) == loc['snapshot_sha256']
            assert text(original)[interval[0]:interval[1]] == obj['text']
            COUNTS['bounded_original_snapshot_span_matches'] += 1
    COUNTS['located_continuous_quote_matches'] += 1

def rows(p):
    v = data(p)
    return v if isinstance(v, list) else v['rows']

with (AI/'与规则法分歧清单.csv').open(encoding='utf-8-sig',newline='') as f:
    original = list(csv.DictReader(f))
expected = {(x['原记录号'],x['维度']): x for x in original}
assert len(original) == len(expected) == 278
files = ['joined-review.json','safety89-sol/reviews.json','effectiveness49-sol/reviews-scoped.json','economic87-sol/reviews.json']
groups = {f: rows(BASE/f) for f in files}
all_disagreements = [x for group in groups.values() for x in group if x['ai'] != x['rule']]
assert len(all_disagreements) == len({(x['source_id'],x['dimension']) for x in all_disagreements}) == 278
assert {(x['source_id'],x['dimension']) for x in all_disagreements} == set(expected)
for x in all_disagreements:
    old = expected[x['source_id'],x['dimension']]
    current = x.get('current_text',x.get('current_original'))
    assert x['ai'] == int(old['本轮AI值']) and x['rule'] == int(old['规则法值'])
    assert current == old['当前完整命题']
    m = data(AI/'source-A/coder-A/materials'/f"{x['blind_id']}.json")
    assert m['source_record']['id'] == x['source_id'] and m['source_record']['text'] == current
    assert x['review_value'] in (None,0,1,'未定')
    COUNTS['disagreement_original_pair_current_and_material_exact'] += 1

for dirname in ['safety89-sol','economic87-sol']:
    manifest = data(BASE/dirname/'manifest.json')
    assert manifest['source_input_hashes_before_output'] == manifest['source_input_hashes_after_output']
    for p, expected_sha in manifest['source_input_hashes_before_output'].items():
        assert sha(p) == expected_sha
        COUNTS['agent_before_after_and_ROOT_current_input_SHA_exact'] += 1
    group = rows(BASE/dirname/'reviews.json')
    assert group == [json.loads(s) for s in text(BASE/dirname/'reviews.jsonl').splitlines()]
    for x in group:
        assert x['is_human_review'] is False
        assert sha(x['manual_file']) == x['manual_sha256']
        for e in x['actual_context_evidence'] + x['manual_evidence']:
            located_quote(e)

for fn in ['effectiveness49-sol/input-bindings.json','effectiveness49-sol/output-seal.json','effectiveness49-sol/human-review-scope-supplement-seal.json','full4481-rule-positive-review-sol/input-bindings.json','joined-review.json']:
    bindings_in(data(BASE/fn))
e_rows = rows(BASE/'effectiveness49-sol/reviews-scoped.json')
assert e_rows == [json.loads(s) for s in text(BASE/'effectiveness49-sol/reviews-scoped.jsonl').splitlines()]
old_e = rows(BASE/'effectiveness49-sol/reviews.json')
assert [(x['source_id'],x['dimension'],x['ai'],x['rule'],x['review_value']) for x in old_e] == [(x['source_id'],x['dimension'],x['ai'],x['rule'],x['review_value']) for x in e_rows]
assert sum(x['needs_human_review'] for x in e_rows) == 2
assert all(x['formal_reference_validation_pending'] for x in e_rows)
for x in e_rows:
    for e in x['context_quotes']:
        located_quote(e)
    assert sha(x['manual_binding']['path']) == x['manual_binding']['sha256']
    assert hashlib.sha256(x['current_text'].encode()).hexdigest() == x['current_text_sha256']

full = rows(BASE/'full4481-rule-positive-review-sol/reviews.json')
assert full == [json.loads(s) for s in text(BASE/'full4481-rule-positive-review-sol/reviews.jsonl').splitlines()]
predictions = {}
with (ROOT/'06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl').open() as f:
    for line in f:
        item = json.loads(line)
        predictions[item['id']] = item
actual_full_positive = {(sid,d) for sid, item in predictions.items() for d in ('I','F') if item['labels'][d] == 1}
assert len(actual_full_positive) == 102
assert {(x['source_id'],x['dimension']) for x in full} == actual_full_positive
targets = {x['source_id'] for x in full}
delivered = {}
with (ROOT/'06-coding/rule-full4481-v2-root/run4481-first/delivered-complete-source-bundles.jsonl').open() as f:
    for line in f:
        obj = json.loads(line)
        if obj['source_record']['id'] in targets:
            delivered[obj['source_record']['id']] = obj
assert set(delivered) == targets
for x in full:
    assert x['is_true_human_review'] is False
    assert x['rule'] == predictions[x['source_id']]['labels'][x['dimension']] == 1
    assert sha(x['packet_file']) == x['packet_sha256']
    packet = data(x['packet_file'])['source_bundle']
    assert packet == delivered[x['source_id']]
    assert packet['source_record']['text'] == x['current_text'] == x['current_quote']
    assert hashlib.sha256(x['current_text'].encode()).hexdigest() == x['current_text_sha256']
    assert sha(x['manual_file']) == x['manual_sha256']
    for e in x['used_context_quotes']:
        located_quote(e)
    for c in x['manual_clauses']:
        if isinstance(c,dict) and 'line_1based' in c:
            assert text(x['manual_file']).splitlines()[c['line_1based']-1] == c['text']
            COUNTS['full_positive_manual_line_matches'] += 1
    if x.get('prior_review'):
        p = x['prior_review']
        assert sha(p['file']) == p['sha256'] and sha(p['prior_material_file']) == p['prior_material_sha256']
        assert data(p['prior_material_file']) == packet
        assert p['original_review']['review_value'] == x['review_value']
        COUNTS['whole_bundle_old_review_reuse_preserved'] += 1
    COUNTS['full_rule_positive_original_packet_and_delivered_match'] += 1

negative = rows(BASE/'common-negative30-root/reviews.json')
assert len(negative) == len({(x['source_id'],x['dimension']) for x in negative}) == 60
assert len({x['source_id'] for x in negative}) == 30
bindings_in(data(BASE/'common-negative30-root/validation-and-summary.json'))
for x in negative:
    assert x['ai'] == x['rule'] == 0
    assert data(x['material_path'])['source_record']['text'] == x['current_text'] == x['current_quote']
    for e in x['used_context_quotes']:
        located_quote({'file':x['material_path'], **e})

def classify(x):
    a = x['assessment']
    if '待核' in a:
        return 'boundary_pending'
    if a == '规则遗漏依据':
        return 'rule_false_negative_review_suggestion'
    if a == '规则过度纳入':
        return 'rule_false_positive_review_suggestion'
    if a == 'AI不符合现手册':
        return 'auxiliary_AI_error_review_suggestion'
    raise AssertionError(a)

class_counts = Counter(classify(x) for x in all_disagreements)
assert dict(class_counts) == {'boundary_pending':20,'rule_false_negative_review_suggestion':230,'auxiliary_AI_error_review_suggestion':7,'rule_false_positive_review_suggestion':21}
null_N = sum(x['review_value'] is None for x in all_disagreements)
undetermined_text_N = sum(x['review_value'] == '未定' for x in all_disagreements)
assert null_N == 10 and undetermined_text_N == 8
by_dim = {d:dict(Counter(classify(x) for x in all_disagreements if x['dimension']==d)) for d in ('S','E','Ec','I','F')}
targeted = defaultdict(list)
for fn, group in [*groups.items(),('full4481-rule-positive-review-sol/reviews.json',full),('common-negative30-root/reviews.json',negative)]:
    for x in group:
        if x['needs_human_review']:
            targeted[x['source_id'],x['dimension']].append((fn,x))
items = []
for (sid, dim), occurrences in sorted(targeted.items()):
    items.append({'source_id':sid,'dimension':dim,'blind_ids':sorted({x['blind_id'] for _,x in occurrences if 'blind_id' in x}),
        'complete_current':occurrences[0][1].get('current_text',occurrences[0][1].get('current_original')),
        'original_judgments_and_AI_review_suggestions':[{'audit_file':str(BASE/fn),'ai_original':x.get('ai'),'rule_original':x.get('rule'),'review_value':x['review_value'],'assessment':x['assessment'],'reason':x['reason'],'specific_question':x.get('human_review_question',x.get('targeted_review_issue',x.get('human_review_note')))} for fn,x in occurrences],
        'actual_human_result':None,'purpose':'targeted_development_calibration_not_independent_formal_validation',
        'material_files':sorted({str(AI/'source-A/coder-A/materials'/f"{x['blind_id']}.json") if 'blind_id' in x else x['packet_file'] for _,x in occurrences})})

unique_records = sorted({x['source_id'] for group in [*groups.values(),full,negative] for x in group})
OUT.mkdir(exist_ok=False)
def save(name,v):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
summary = {'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ROOT_mechanical_reception_passed',
    'identity':'nonhuman_source_based_semantic_reviews_not_human_reference_or_accuracy',
    'auxiliary_AI_rule_disagreement_slots':278,'unique_disagreement_records':len({x['source_id'] for x in all_disagreements}),
    'classification_counts':dict(class_counts),'by_dimension':by_dim,'NULL_review_suggestions':null_N,'literal_undetermined_text_review_suggestions':undetermined_text_N,'nonbinary_review_suggestions':null_N+undetermined_text_N,'provisional_zero_boundaries':2,
    'full_rule_IF_positive_slots':102,'full_rule_IF_positive_records':81,'full_rule_IF_assessment_counts':dict(Counter(x['assessment'] for x in full)),
    'negative_draw_records':30,'negative_IF_slots':60,'negative_review_counts':dict(Counter(str(x['review_value']) for x in negative)),
    'negative_draw_confirmed_shared_omissions':0,'negative_draw_unresolved_records':1,
    'negative_sample_general_recall_inference_permitted':False,
    'targeted_calibration_slots':len(items),'targeted_calibration_unique_records':len({x['source_id'] for x in items}),
    'ROOT_checks':dict(COUNTS),'actual_agent_reads_not_proven_by_hash_alone':True,
    'original_labels_modified':False,'primary_LLM_partial_labels_read':False,'human_accuracy_computed':False,'formal_acceptance_claimed':False,
    'next_action':'Repair general rule logic on unchanged frozen common input; preserve pending boundaries and separately review neutral common material projection.'}
save('summary.json',summary)
save('targeted-human-calibration-items.json',{'status':'prepared_AI_suggestions_only_actual_human_results_missing','items':items})
save('future-development-exposure-overlay.json',{'purpose':'prospective_overlay_for_future_repair_versions_only','historical_current_freeze_domains_unchanged':True,'reviewed_current_source_ids':unique_records,'N':len(unique_records),'direct_semantic_review_includes_agent_reads':True,'additional_context_resources_not_counted_as_current_record_independence':True})
report = ['五维机器分歧与阳性审查：ROOT接收报告','',f'800条辅助AI与规则法原始分歧278项（{summary["unique_disagreement_records"]}条）：230项支持规则漏判，21项支持规则过度纳入，7项支持辅助AI误判，20项边界待核。20项含18个未定建议（10个null、8个文字“未定”）与2项暂定0；保留原值。',
    '这是已看双方标签的AI语义审查，不是真人参照，不是完整编码准确率或验收通过。',
    '', '全量规则法创新性/公平性102项阳性、81条：98项有据，2项过度纳入，2项未定。与800条内既有阳性审查重叠13项，不能相加充当独立样本。',
    '预先分层随机抽取的共同阴性30条（60个I/F项）：58项支持0，2项同条边界未定。未发现明确共同遗漏，不能推断总体召回率已足够。',
    '',f'已收敛为{len(items)}个条款×维度定向校准问题，涉及{summary["targeted_calibration_unique_records"]}条。完整材料与原值/建议另见targeted-human-calibration-items.json；尚未生成真人答案。正式独立抽样检验另行保留。',
    '本次ROOT核验原始CSV范围与标签、所有当前文本、源包字节SHA、命名位置连续引文、同版PDF物理页重提取、规则真实交付包一致性、旧审查复用和E49范围补充。哈希和引文核验不证明语义正确，也不证明真人身份。',
    '', '通用规则修复并行实施；当前冻结全量LLM不换手册/材料/答案，不对部分标签做比较或调参。完整论文写作仍在方法和指标验收之后。']
(OUT/'核验结论.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
inputs = [binding(BASE/fn) for fn in files+['full4481-rule-positive-review-sol/reviews.json','common-negative30-root/reviews.json']]
save('reception-seal.json',{'input_members':inputs,'output_members':[binding(OUT/name) for name in ['summary.json','targeted-human-calibration-items.json','future-development-exposure-overlay.json','核验结论.txt']],'receiver_script':binding(Path(__file__)), 'source_input_current_SHA_bindings':[{'path':p,'sha256':s} for p,s in sorted(HASHES.items())]})
print(json.dumps(summary,ensure_ascii=False))
