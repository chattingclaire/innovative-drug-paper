#!/usr/bin/env python3
"""Verify immutable inputs and preseal independent expectations; no judge."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
V2 = ROOT / '06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'
OLD = ROOT / '08-audits/SE-Ec-repair-independent-controls-sol'
EXPECTED_ALGORITHM = '88eead7588d2e8353a4de6768cedd42a95ba4cb75c3dc819f6dd05aec9f5ac32'
EXPECTED_CANDIDATE = 'a630f5b6c3da8a2a91bd9fd0375caf890d5dfaef83ef2a81df3d8ab062cfc0dd'
EXPECTED_DELIVERY = '39a87613fc07027fe97a7e739535d6101da0d248c8b84a1c573a6f699cba1d47'


def bind(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(Path(path).read_bytes())


def write(name, value):
    with (OUT / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


verified = {}


def exact(item):
    actual = bind(item['path'])
    assert all(actual[k] == item[k] for k in ('sha256', 'bytes') if k in item), item['path']
    verified[actual['path']] = actual
    return actual


candidate = load(V2 / 'candidate-seal.json')
delivery = load(V2 / 'delivery-seal.json')
assert bind(V2 / 'candidate-seal.json')['sha256'] == EXPECTED_CANDIDATE
assert bind(V2 / 'delivery-seal.json')['sha256'] == EXPECTED_DELIVERY
assert delivery['candidate_seal_sha256'] == EXPECTED_CANDIDATE
assert candidate['algorithm_sha256'] == EXPECTED_ALGORITHM
assert len(delivery['files']) == 74
for item in delivery['files']:
    exact(item)
for item in [candidate['manual'], *candidate['code'], *candidate['regression_artifacts']]:
    exact(item)
algorithm = load(V2 / 'algorithm-bindings.json')
assert algorithm['algorithm_sha256'] == EXPECTED_ALGORITHM
assert algorithm['five_modules'] == candidate['code']
assert algorithm['manual'] == candidate['manual']
old_seal = load(OLD / 'output-seal.json')
for item in old_seal['output_members']:
    exact(item)
for p in (V2 / 'delivery-seal.json', OLD / 'output-seal.json'):
    exact(bind(p))
snapshot = OUT / 'code-snapshot'; snapshot.mkdir(exist_ok=False)
snapshots = []
for item in candidate['code']:
    p = snapshot / Path(item['path']).name
    with p.open('xb') as stream:
        stream.write(Path(item['path']).read_bytes())
    assert bind(p)['sha256'] == item['sha256']
    snapshots.append({'owner_binding': item, 'independent_snapshot': bind(p)})
with (OUT / 'legacy20-controls.json').open('xb') as stream:
    stream.write((OLD / 'controls-fixed-before-execution.json').read_bytes())
assert bind(OUT / 'legacy20-controls.json')['sha256'] == bind(OLD / 'controls-fixed-before-execution.json')['sha256']
old20 = load(OUT / 'legacy20-controls.json')
assert len(old20['cases']) == 20

manual = Path(candidate['manual']['path']).read_text().splitlines(keepends=True)
lines_selected = [9, 11, 15, 22, 23, 25, 29, 30, 31, 39, 40, 41, 42, 44,
                  50, 52, 58, 62, 84, 86, 88, 90, 94, 96, 98, 100, 104, 106,
                  108, 110, 112, 114]
offset = 0; quote_rows = []
for n, line in enumerate(manual, 1):
    if n in lines_selected:
        quote_rows.append({'line_1based': n, 'start': offset, 'end': offset + len(line), 'quote': line})
    offset += len(line)
write('manual-basis-quotes.json', {'binding': candidate['manual'], 'quotes': quote_rows,
                                  'new_control_basis': 'Frozen manual5ea7; no new dimension, method or threshold.'})


def context(cid, kind, text, pid, sequence, component='C-SCOPE', **extra):
    return {'context_id': cid, 'kind': kind, 'text': text,
            'structure': {'paragraph_id': pid, 'sequence_index': sequence,
                          'component_id': component, **extra}}


def bundle(current, contexts, current_cid='CURRENT', inserted_gaps=None):
    """Bound internally consistent synthetic text coordinates, never policy originals."""
    contexts = copy.deepcopy(contexts)
    inserted_gaps = inserted_gaps or {}
    pieces, intervals, cursor = [], {}, 0
    for c in contexts:
        gap = inserted_gaps.get(c['context_id'], '')
        if gap:
            pieces.append(gap); cursor += len(gap)
        if not c.get('text'):
            continue
        intervals[c['context_id']] = [cursor, cursor + len(c['text'])]
        pieces.append(c['text'] + '\n'); cursor += len(c['text']) + 1
    raw = ''.join(pieces)
    key = hashlib.sha256(raw.encode()).hexdigest()
    for c in contexts:
        st = c['structure']; loc = {k: st[k] for k in ('paragraph_id', 'sequence_index', 'component_id')}
        if c['context_id'] in intervals:
            loc['unicode_code_point_interval_half_open'] = intervals[c['context_id']]
        c['source_ref'] = {'sha256': key, 'source_resource_id': 'SOURCE-SYNTHETIC-' + key,
                           'locator': loc}
    anchor = next(c for c in contexts if c['context_id'] == current_cid)
    assert current in anchor['text']
    ref = copy.deepcopy(anchor['source_ref'])
    row = {'id': 'SYNTHETIC-NOT-A-FORMAL-RECORD', 'text': current,
           'source_ref': ref, 'contexts': contexts, 'pages': []}
    result = {'common_source_bundle_version': {'status': 'synthetic_independent_control'},
              'source_record': row, 'source_documents': [],
              'explicit_or_primary_source_resources': [],
              'preserved_historical_neutral_source_supplements': [],
              'source_full_text_resources': [], 'source_asset_locations': [],
              'source_locator_bases': {}, 'source_reference_index': [],
              'source_provenance_addenda': []}
    return result, {'sha256': key, 'text': raw, 'is_synthetic': True,
                    'is_original_policy': False, 'unprovided_literal_gaps': inserted_gaps}


def article_case(member_texts, current=None, omit=(), remote=False, different_component=False):
    current = current or '符合《合成核验条件》第十条规定的药品可申请。'
    cs = [context('CURRENT', 'paragraph', current, 'p0000', -1, 'C-ACTION')]
    all_members = [context('HEAD', 'cited_article', '第十条 药品应符合以下条件：', 'p0001', 0, article='第十条')]
    for i, text in enumerate(member_texts, 1):
        all_members.append(context(f'MEMBER-{i}', 'cited_article', text, f'p{i+1:04d}', i, article='第十条'))
    members = [c for c in all_members if c['context_id'] not in omit]
    if different_component:
        assert len(members) == 1
    next_pid = 'p0099' if remote else f'p{len(all_members)+1:04d}'
    next_seq = 99 if remote else len(all_members)
    following = context('NEXT', 'following_heading', '第十一条 药品价格及疾病控制效果另作实质评价。',
                        next_pid, next_seq, 'C-OTHER' if different_component else 'C-SCOPE')
    cs += members
    if len(all_members) > 1:
        cs += [context('CONTAINER', 'cited_reference', '', 'geometry', -2,
                       child_groups=[{'position': 'contexts', 'ordered_context_ids': [c['context_id'] for c in members]},
                                     {'position': 'structure_boundary', 'ordered_context_ids': ['BOUNDARY']}]),
               context('BOUNDARY', 'boundary_container', '', 'boundary', -3,
                       parent_context_id='CONTAINER', first_paragraph=all_members[0]['structure']['paragraph_id'],
                       last_paragraph=all_members[-1]['structure']['paragraph_id'],
                       next_paragraph_id=next_pid, text_child_context_ids=['NEXT'])]
    cs += [following]
    gaps = {'NEXT': '（四）尚有未提供的并列条件。\n'} if remote else None
    return bundle(current, cs, inserted_gaps=gaps)


def single_article(different_component=False):
    current = '符合《合成核验条件》第十条规定的药品可申请。'
    cs = [context('CURRENT', 'paragraph', current, 'p0000', 0, 'C-ACTION'),
          context('HEAD', 'cited_article', '第十条 药品须提供充分的安全性证据。', 'p0001', 1, article='第十条'),
          context('NEXT', 'following_heading', '第十一条 应核验药品疗效与治疗费用。', 'p0002', 2,
                  'C-OTHER' if different_component else 'C-SCOPE')]
    return bundle(current, cs)


def clause_case(missing=False, other_component=False):
    current = '申请药品须符合《合成核验条件》第十条第二款规定。'
    cs = [context('CURRENT', 'paragraph', current, 'p0000', 0, 'C-ACTION'),
          context('C1', 'cited_article', '第十条 第一款 应评价药品的疗效和费用。', 'p0001', 1, article='第十条', clause='一'),
          context('C2', 'cited_article', '第二款 药品须核验过敏反应风险。', 'p0002', 2, article='第十条', clause='二')]
    if not missing:
        cs.append(context('C3', 'cited_article', '第三款 应评价药品价格和疾病控制效果。', 'p0003', 3,
                          'C-OTHER' if other_component else 'C-SCOPE', article='第十条', clause='三'))
    return bundle(current, cs)


def list_case(texts, pure=False, repeated_boundary=False):
    current = '列示如下：' if pure else '符合以下条件的药品可申请：'
    cs = [context('CURRENT', 'ordered_members', current, 'p0001', 0)]
    for i, text in enumerate(texts, 1):
        cs.append(context(f'MEMBER-{i}', 'ordered_members', text, f'p{i+1:04d}', i))
    ids = [c['context_id'] for c in cs]
    next_pid = f'p{len(cs)+1:04d}'
    boundary_text = '药品治疗费用及疾病控制效果应另作评价。'
    cs += [context('CONTAINER', 'ordered_list', '', 'geometry', -1,
                   child_groups=[{'position': 'members', 'ordered_context_ids': ids},
                                 {'position': 'structure_boundary', 'ordered_context_ids': ['BOUNDARY']}]),
           context('BOUNDARY', 'boundary_container', '', 'boundary', -2,
                   parent_context_id='CONTAINER', first_paragraph='p0001',
                   last_paragraph=f'p{len(ids):04d}', next_paragraph_id=next_pid,
                   text_child_context_ids=['NEXT']),
           context('NEXT', 'following_heading', boundary_text, next_pid, len(ids))]
    if repeated_boundary:
        cs.append(context('REMOTE-DUPLICATE', 'paragraph', boundary_text, 'p0099', 99, 'C-OTHER'))
    return bundle(current, cs)


def parent_case(payment=False, wrong_target=False, other_component=False):
    current = '（一）成人患者的数据分别列示。'
    parent = ('本药治疗费用符合以下条件可由基金支付：' if payment else '应整理本药的安全性信息：')
    cs = [context('CURRENT', 'paragraph', current, 'p0002', 2, 'C-CURRENT'),
          context('PARENT', 'parent_paragraph', parent, 'p0001', 1,
                  'C-OTHER' if other_component else 'C-CURRENT',
                  target_paragraph_id='p0999' if wrong_target else 'p0002')]
    return bundle(current, cs)


new = []


def add(name, pair, expected, reason, lines, category):
    b, doc = pair
    new.append({'name': name, 'synthetic_bundle': b, 'synthetic_documents': [doc],
                'expected': expected, 'manual_reason': reason, 'manual_lines': lines,
                'control_category': category, 'is_human_reference': False})


NULL = {'S': None, 'E': None, 'Ec': None}
ZERO = {'S': 0, 'E': 0, 'Ec': 0}
THREE = {'S': 1, 'E': 1, 'Ec': 1}
members = ['（一）应核验本药过敏反应风险；', '（二）应提供本药疾病控制效果证据；', '（三）应证明本药治疗费用合理。']
add('closed_article_all_three', article_case(members), THREE, '当前实质申请条件明确确指已供完整同版条文，三项均有实际内容。', [39,40,41,84,94,104], 'true_closed_positive')
add('single_article_boundary_does_not_donate', single_article(), {'S':1,'E':0,'Ec':0}, '下一条仅证明本条闭合，本条只有安全证据；后条疗效/费用不捐献。', [22,40,42], 'adjacent_boundary_negative')
add('article_missing_middle_member', article_case(members, omit=('MEMBER-2',)), NULL, '确指整体条件组中段缺失，成员序列0/1/3不完整，不能填0或部分当全组。', [23,25,39,41], 'missing_middle')
add('article_missing_last_member', article_case(members, omit=('MEMBER-3',)), NULL, '容器声明的真实末成员未提供，下一段不能替代末成员。', [23,25,39], 'missing_last')
add('article_remote_next_boundary_unprovided_condition', article_case(members, remote=True), NULL, '末成员到所谓下一段之间实际缺一并列条件；远段不能闭合当前范围。', [22,23,25,39], 'remote_boundary_negative')
add('single_article_next_other_component', single_article(True), NULL, '段号相邻但组件不同，另一组件第十一条不是当前第十条的同一原件末界。', [22,25,40,41], 'component_boundary_negative')
add('explicit_clause2_only_safety', clause_case(), {'S':1,'E':0,'Ec':0}, '明确第二款仅核安全风险；第一/三款效果费用不继承，第三款仅闭合。', [22,32,40,42], 'clause_scope_positive_negative')
add('explicit_clause2_missing_next_boundary', clause_case(missing=True), NULL, '只有第二款句号，没有原文末范围或相邻下一款证据，保持缺材。', [23,25,40], 'clause_missing_closure')
add('explicit_clause2_next_other_component', clause_case(other_component=True), NULL, '不同组件的第三款不能证明第二款闭合，条款地址相同也不够。', [22,25,40,41], 'clause_component_negative')
add('boundary_literal_duplicated_elsewhere', list_case(['应核验本药过敏反应风险。'], repeated_boundary=True), {'S':1,'E':0,'Ec':0}, '相同疗效/费用文字在边界和另组件重复，仍不属于当前条件成员。', [22,39,42,58], 'role_duplicate_boundary_negative')
add('two_member_positions_identical_literal', list_case(['药品疗效证据应当充分。','药品疗效证据应当充分。']), {'S':0,'E':1,'Ec':0}, '两个原文位置同字面成员均属所指完整范围，同维一次；价格边界不捐献。', [39,56,58,94], 'role_duplicate_member_positive')
add('safety_parent_wrong_target', parent_case(wrong_target=True), ZERO, '安全内容父句明确指向另一段，当前数据成员不能继承。', [22,42,58], 'parent_target_negative')
add('safety_parent_other_component_reused_pid', parent_case(other_component=True), ZERO, '另一组件重用段号不建立当前直接父谓词；当前只列数据。', [22,42,58], 'parent_component_negative')
current = '专家就药品测算评估的思路进行交流。'
add('remote_preceding_price_method_other_component', bundle(current, [
    context('CURRENT','paragraph',current,'p0050',50,'C-CURRENT'),
    context('REMOTE','preceding_paragraph','前期开展基金测算与药物经济学测算评估，提出医保支付标准评估意见。','p0001',1,'C-OLD-STAGE')]), ZERO,
    '另一阶段远段只是经济方法背景，不是当前一般方法交流的直接定义。', [9,22,42,46,108], 'remote_stage_negative')
current = '应核验上述疗效指标是否充分。'
raw = '本药的安全性观察指标为肝损伤发生率。另设本药的疗效观察指标为疾病控制率。' + current
add('effect_indicator_not_safety_sibling', bundle(current,[context('CURRENT','paragraph',raw,'p0001',1)]), {'S':0,'E':1,'Ec':0},
    '当前明确疗效指标，只由同段疗效定义补足，不继承同药并列安全指标。', [15,22,39,42,94], 'same_paragraph_sibling_negative')
add('pure_structure_closed_list_stays_zero', list_case(members,pure=True), ZERO, '组织性列示不因已闭合且成员实质而汇总标签。', [58,60,62], 'pure_structure_negative')
add('direct_payment_child_condition', parent_case(payment=True), {'S':0,'E':0,'Ec':1}, '当前成员与直接父句组成费用条件—基金支付关系，不要求支付已批准。', [9,22,106,114], 'parent_payment_positive')
add('payment_parent_other_component_reused_pid', parent_case(payment=True,other_component=True), ZERO, '另一组件费用父句不能给当前自足成员补支付后果。', [22,42,58,114], 'parent_payment_component_negative')
current = '应汇总本药AE（不良事件）发生率，并核验严重程度。'
add('AE_current_substantive_not_filename', bundle(current,[context('CURRENT','paragraph',current,'p0001',1)]), {'S':1,'E':0,'Ec':0}, '当前要求本药不良事件发生率内容，不是报告名或文件操作。', [9,15,84,86,90], 'AE_content_positive')
current = '本药资料中的AAE编码列仅用于定位附件，采用字母与数字排序。'
add('AAE_identifier_not_AE_event', bundle(current,[context('CURRENT','paragraph',current,'p0001',1)]), ZERO, 'AAE是附件检索代码，不能把内部AE字母或排序解释为药物风险。', [9,15,84,90], 'AE_identifier_negative')
assert len(new) == 20 and len({c['name'] for c in new}) == 20
write('new20-fixed-before-execution.json', {'status':'independent_synthetic_expectations_fixed_before_execution','case_N':20,
                                          'manual_binding':candidate['manual'],'cases':new,
                                          'no_owner_expected_table_used_as_new_semantic_target':True})

# Four owner-disclosed closure problems: copy only required input/old expectation,
# never adopt owner observed labels as independent targets.
closure = []
for name in ('complete_explicit_article_condition','different_title_same_substance'):
    suite = load(V2 / 'legacy42-final-scope.json')
    row = next(c for c in suite['tests'] if c['name'] == name)
    closure.append({'name':name,'synthetic_input':row['synthetic_input'],
                    'expected':NULL,'historical_expected_unchanged':row['expected_fixed_before_execution'],
                    'manual_reason':'仅heading+编号成员+末句句号，无实际容器/原件末界；按缺确指范围保留NULL。',
                    'manual_lines':[23,25,39,40,41], 'owner_original_input_path':str(V2/'semantic_selfcheck.py'),
                    'synthetic_only':True})
suite = load(V2 / 'controls40-final-scope.json')
row = next(c for c in suite['tests'] if c['name'] == 'complete_renewal_total')
actual_input = exact(row['input_binding'])
closure.append({'name':'complete_renewal_total','bound_source_bundle':load(actual_input['path']),
                'source_binding':actual_input,'expected':{'Ec':None},
                'historical_expected_unchanged':row['expected_fixed_before_v2_edit'],
                'manual_reason':'当前要求同时满足完整续约条件；原包只有9个孤立有序成员，缺闭合容器/末界。原句无自足费用条件，不将部分成员当完整组。',
                'manual_lines':[23,25,39,41,106], 'synthetic_only':False,
                'only_finite_original_packet_read':'A450 current and supplied9members; no prediction or human result file'})
write('owner-closure3-fixed-before-execution.json', {'case_N':3,'cases':closure,
    'fourth_case_reuses_legacy20_execution':'complete_explicit_article_three_dimensions',
    'owner_disclosure_only':'Owner named4 missing closures. Historical expected fields retained as provenance, independent missing-material expectations fixed here.'})

# Static function scope changes, no execution.
diff = []
for module in ('source_packet','source_receipts','evidence','relations','dimensions'):
    v1_path = V2.parents[1] / f'{module}.py'
    v2_path = V2 / f'{module}.py'
    def functions(path):
        src=path.read_text();tree=ast.parse(src)
        return {f.name:(ast.dump(f,include_attributes=False),f.lineno,f.end_lineno)
                for f in ast.walk(tree) if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef))}
    a,b=functions(v1_path),functions(v2_path)
    diff.append({'module':module,'v1':bind(v1_path),'v2':bind(v2_path),
                 'added_or_changed_functions':[{'name':k,'lines':[b[k][1],b[k][2]],
                                              'new':k not in a} for k in b if k not in a or b[k][0]!=a[k][0]]})
write('read-only-function-diff.json',diff)
write('sealed-input-verification.json',{'owner_delivery_members_N':74,'all_members_SHA_bytes_matched':True,
    'algorithm_sha256':EXPECTED_ALGORITHM,'algorithm_manifest_file_binding':bind(V2/'algorithm-bindings.json'),
    'candidate_seal_binding':bind(V2/'candidate-seal.json'),'delivery_seal_binding':bind(V2/'delivery-seal.json'),
    'old20_and_all_old_audit_members_matched':True,'files':[verified[k] for k in sorted(verified)],
    'code_snapshots':snapshots,'sealed_outputs_hashed_not_all_semantically_read':True})
pre_inputs = [bind(OUT / n) for n in ('legacy20-controls.json','new20-fixed-before-execution.json',
                                    'owner-closure3-fixed-before-execution.json','manual-basis-quotes.json',
                                    'sealed-input-verification.json','read-only-function-diff.json','prepare_controls.py')]
pre_inputs += [x['independent_snapshot'] for x in snapshots]
write('pre-execution-seal.json',{'status':'independent_controls_presealed_before_any_candidate_judge',
                               'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               'inputs':pre_inputs,'algorithm_sha256':EXPECTED_ALGORITHM,
                               'legacy_case_N':20,'new_synthetic_case_N':20,'owner_additional_closure_case_N':3,
                               'owner_fourth_closure_case_already_in_legacy20':True,
                               'expected_changes_after_execution_allowed':False})
print(json.dumps({'owner74_inputs_verified':True,'legacy20_preserved':True,'new20_presealed':True,
                  'owner_closure3_plus_reused_fourth_presealed':True,
                  'preseal':bind(OUT/'pre-execution-seal.json')},ensure_ascii=False))
