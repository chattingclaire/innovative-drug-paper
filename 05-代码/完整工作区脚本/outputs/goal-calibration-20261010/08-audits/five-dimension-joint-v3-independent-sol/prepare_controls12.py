#!/usr/bin/env python3
"""Prepare twelve independent source-only near-neighbor controls, no algorithm import."""
from __future__ import annotations
import copy
import datetime
import hashlib
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'
SOURCE_CONTRACT = ROOT / '08-audits/five-dimension-joint-independent-controls-sol/execution-joint-v2-geometry01/code-snapshot/source_packet.py'
EVIDENCE_CONTRACT = ROOT / '08-audits/five-dimension-joint-independent-controls-sol/execution-joint-v2-geometry01/code-snapshot/evidence.py'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
MANUAL_SHA = '5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
DOCUMENTS = OUT / 'synthetic-source-documents'
DOCUMENTS.mkdir(exist_ok=False)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def binding(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': digest(raw)}


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def expected(S=0, E=0, Ec=0, I=0, F=0):
    return dict(zip(DIMENSIONS, (S, E, Ec, I, F)))


class Document:
    """An actual saved UTF8 *synthetic* original, independent of its delivery.

    Every paragraph has exact byte/code-point/line coordinates.  A copy of one
    source paragraph may have another context role but its origin cannot move.
    """
    def __init__(self, paragraphs, title, components=None):
        self.title = title
        self.paragraphs = list(paragraphs)
        self.raw = ''.join(text + '\n' for text in self.paragraphs)
        self.sha = digest(self.raw.encode('utf-8'))
        self.path = DOCUMENTS / (self.sha + '.txt')
        if not self.path.exists():
            with self.path.open('xb') as stream:
                stream.write(self.raw.encode('utf-8'))
        assert binding(self.path)['sha256'] == self.sha
        components = components or {}
        self.locators = []
        u = 0; b = 0; line = 1
        for i, text in enumerate(self.paragraphs):
            literal_bytes = text.encode('utf-8')
            loc = {'kind': 'synthetic_exact_UTF8_paragraph',
                   'paragraph_id': f'p{i+1:04d}', 'source_paragraph_id': f'p{i+1:04d}',
                   'sequence_index': i, 'component_id': components.get(i, 'JOINT-COMPONENT'),
                   'unicode_code_point_interval_half_open': [u, u + len(text)],
                   'utf8_byte_interval_half_open': [b, b + len(literal_bytes)],
                   'physical_line_interval_inclusive': [line, line + text.count('\n')],
                   'source_utf8_absolute_path': str(self.path)}
            self.locators.append(loc)
            u += len(text) + 1; b += len(literal_bytes) + 1; line += text.count('\n') + 1
        assert u == len(self.raw) and b == len(self.raw.encode('utf-8'))

    def ref(self, i):
        return {'sha256': self.sha, 'source_resource_id': 'SOURCE-' + self.sha,
                'locator': copy.deepcopy(self.locators[i]),
                'metadata': {'document_title': self.title, 'document_year': 2026,
                             'source_version_id': 'SYNTHETIC-INDEPENDENT-NEIGHBOR-2026-V1',
                             'synthetic_control_not_policy_original': True}}

    def context(self, i, cid, kind='source_paragraph', **structure):
        loc = self.locators[i]
        return {'context_id': cid, 'kind': kind, 'text': self.paragraphs[i],
                'source_document': 'SOURCE-' + self.sha, 'source_ref': self.ref(i),
                'structure': {'paragraph_id': loc['paragraph_id'],
                              'source_paragraph_id': loc['source_paragraph_id'],
                              'sequence_index': loc['sequence_index'],
                              'component_id': loc['component_id'],
                              'source_version_id': 'SYNTHETIC-INDEPENDENT-NEIGHBOR-2026-V1', **structure}}

    def geometry(self, cid, kind, **structure):
        return {'context_id': cid, 'kind': kind, 'text': '',
                'source_document': 'SOURCE-' + self.sha,
                'source_ref': {'sha256': self.sha, 'source_resource_id': 'SOURCE-' + self.sha,
                               'locator': {'kind': 'synthetic_bound_geometry',
                                           'component_id': structure.get('component_id', 'JOINT-COMPONENT'),
                                           'source_utf8_absolute_path': str(self.path)}},
                'structure': {'component_id': 'JOINT-COMPONENT',
                              'source_version_id': 'SYNTHETIC-INDEPENDENT-NEIGHBOR-2026-V1', **structure}}

    def packet(self, current_i, contexts, *, current_text=None, deliver_full=True, undelivered=()):
        current_text = self.paragraphs[current_i] if current_text is None else current_text
        original = self.paragraphs[current_i]
        assert original.count(current_text) == 1
        start = original.index(current_text)
        rowref = self.ref(current_i)
        loc = rowref['locator']
        loc['unicode_code_point_interval_half_open'] = [
            loc['unicode_code_point_interval_half_open'][0] + start,
            loc['unicode_code_point_interval_half_open'][0] + start + len(current_text)]
        start_b = len(original[:start].encode('utf-8'))
        loc['utf8_byte_interval_half_open'] = [
            loc['utf8_byte_interval_half_open'][0] + start_b,
            loc['utf8_byte_interval_half_open'][0] + start_b + len(current_text.encode('utf-8'))]
        contexts = copy.deepcopy(contexts)
        contexts.append(self.context(current_i, 'CURRENT-RECORD-PARAGRAPH', 'paragraph'))
        assert len({c['context_id'] for c in contexts}) == len(contexts)
        resources = []
        if deliver_full:
            assert not undelivered
            resources.append({'kind': 'verbatim_UTF8_snapshot_text',
                              'source_resource_id': 'SYNTHETIC-TXT-' + self.sha,
                              'source_document_resource_id': 'SOURCE-' + self.sha,
                              'source_sha256': self.sha, 'text': self.raw,
                              'text_utf8_sha256': self.sha,
                              'source_version_id': 'SYNTHETIC-INDEPENDENT-NEIGHBOR-2026-V1',
                              'document_title': self.title, 'document_year': 2026,
                              'locator': {'kind': 'synthetic_complete_UTF8_snapshot',
                                          'unicode_code_point_interval_half_open': [0, len(self.raw)],
                                          'utf8_byte_interval_half_open': [0, len(self.raw.encode('utf-8'))],
                                          'physical_line_interval_inclusive': [1, self.raw.count('\n')],
                                          'source_utf8_absolute_path': str(self.path)}})
        result = {'common_source_bundle_version': {'status': 'synthetic_source_only_hidden_v3_neighbor_control'},
                  'source_record': {'id': 'SYNTHETIC-NOT-FORMAL-CODING', 'text': current_text,
                                    'source_ref': rowref, 'contexts': contexts, 'pages': []},
                  'source_documents': [], 'explicit_or_primary_source_resources': [],
                  'preserved_historical_neutral_source_supplements': [],
                  'source_full_text_resources': resources, 'source_asset_locations': [],
                  'source_locator_bases': {}, 'source_reference_index': [],
                  'source_provenance_addenda': []}
        return result, {'binding': binding(self.path), 'is_synthetic': True,
                        'is_original_policy': False, 'title': self.title,
                        'text': self.raw, 'paragraph_locators': copy.deepcopy(self.locators),
                        'delivered_complete_literal_snapshot': deliver_full,
                        'undelivered_paragraph_indexes_zero_based': list(undelivered),
                        'undelivered_material_is_not_a_candidate_resource': True}


def closed_group(doc, indices, prefix='GROUP', kind='ordered_list', article=None):
    """An explicit literal group with exact contiguous first/last/next proof."""
    assert indices == list(range(indices[0], indices[-1] + 1))
    after = indices[-1] + 1
    assert after < len(doc.paragraphs)
    if article is None:
        contexts = [doc.context(i, f'{prefix}-TEXT-{i}', 'ordered_members') for i in indices]
    else:
        contexts = [doc.context(i, f'{prefix}-TEXT-{i}', 'cited_article', article=article) for i in indices]
    ids = [c['context_id'] for c in contexts]
    contexts += [doc.geometry(prefix + '-CONTAINER', kind,
                              child_groups=[{'position': 'members' if article is None else 'contexts',
                                             'ordered_context_ids': ids},
                                            {'position': 'structure_boundary',
                                             'ordered_context_ids': [prefix + '-BOUNDARY']}]),
                 doc.geometry(prefix + '-BOUNDARY', 'boundary_container',
                              parent_context_id=prefix + '-CONTAINER',
                              first_paragraph=doc.locators[indices[0]]['paragraph_id'],
                              last_paragraph=doc.locators[indices[-1]]['paragraph_id'],
                              next_paragraph_id=doc.locators[after]['paragraph_id'],
                              text_child_context_ids=[prefix + '-NEXT']),
                 doc.context(after, prefix + '-NEXT', 'following_heading')]
    return contexts


def programme_contexts(doc, indexes, prefix='PROGRAMME'):
    """A closed component's full paragraphs and real immediately next heading."""
    assert indexes == list(range(indexes[0], indexes[-1] + 1))
    after = indexes[-1] + 1
    cs = [doc.context(i, f'{prefix}-P-{i}', 'source_paragraph') for i in indexes]
    ids = [c['context_id'] for c in cs]
    cs += [doc.geometry(prefix + '-COMPONENT', 'source_paragraph',
                        first_paragraph=doc.locators[indexes[0]]['paragraph_id'],
                        last_paragraph=doc.locators[indexes[-1]]['paragraph_id'],
                        child_groups=[{'position': 'scope_members', 'ordered_context_ids': ids}]),
           doc.context(after, prefix + '-NEXT', 'following_heading', scope_context_ids=ids,
                       component_first_paragraph=doc.locators[indexes[0]]['paragraph_id'],
                       component_last_paragraph=doc.locators[indexes[-1]]['paragraph_id'],
                       follows_context_id=ids[-1])]
    return cs


cases = []
def add(name, pair, result, reason, lines, group, constraints=None):
    packet, document = pair
    assert set(result) == set(DIMENSIONS)
    cases.append({'name': name, 'pair_group': group,
                  'synthetic_bundle': packet, 'synthetic_documents': [document],
                  'expected_values_fixed_before_execution': result,
                  'manual_reason': reason, 'manual_lines': lines,
                  'interface_assertions_fixed_before_execution': constraints or [],
                  'actual_classification_executed': False,
                  'synthetic_development_control_not_human_reference': True,
                  'not_a_formal_accuracy_or_reliability_observation': True})

# A: one source definition, actual post-admission technical service vs applicant formatting.
doc = Document([
    '上市前方案研讨计划',
    '第一条 本计划的对象为创新药上市前研发项目；纳入者可向专门团队预约研究方案反馈。',
    '第二条 已纳入本计划的项目，现可预约该团队对上市前研究方案提供书面反馈。',
    '第三条 申请人须将本计划申请表中的项目名称按统一字符格式填写。',
    '第二章 日常文书事务',
], '当前反馈安排与申请人格式近邻（合成）')
cs = programme_contexts(doc, list(range(4)), 'A-PLAN')
add('admitted_projects_current_feedback', doc.packet(2, cs), expected(I=1),
    '当前允许已纳入项目预约实质研究方案反馈，同版同阶段定义已供，明确创新研发对象与可用安排的直接关系。',
    [9,22,44,46,52,124,127,135,137,139], 'A',
    ['不得从本计划全域背景继承其他维度', '保留纳入后阶段和当前可预约服务'])
add('applicant_name_character_format', doc.packet(3, cs), expected(),
    '当前只有申请人填写项目名称的字符格式；具名支持定义可见却未被当前用于开放、适用或实质条件核验。',
    [9,15,22,42,46,52,131], 'A')

# B: explicit relative acceleration vs same ordinary baseline deadline.
doc = Document([
    '研发审评办理与专门支持规定',
    '第一条 普通程序中的所有申请，包括创新药研发项目，共同审评办理时限为三十日。',
    '第二条 创新药研发项目可申请专门通道；本条将其审评时限相对第一条普通程序由三十日缩短为二十日。',
    '第三条 普通程序中的创新药研发项目亦按第一条共同三十日办理时限处理。',
    '第二章 归档格式',
], '相对缩时与普通共同期限近邻（合成）')
cs = programme_contexts(doc, list(range(4)), 'B-TIME')
add('relative_ordinary_review_time_shortened', doc.packet(2, cs), expected(I=1),
    '当前向创新研发对象提供可申请通道并明示相对普通程序缩时，实际便利成立；不根据单个数字猜加速。',
    [9,22,44,124,127,131,137,170], 'B')
add('ordinary_common_deadline_no_special_support', doc.packet(3, cs), expected(),
    '当前明确普通程序的创新申请与所有申请同用三十日，并无本记录专门通道、优先、加快或相对便利；另一条专门支持未被当前适用。',
    [9,22,42,44,124,127,131,170], 'B')

# C: exact complete operative standard vs co-visible but inapplicable attachment inventory.
five = [
    '（一）须证明本药过敏反应风险的监测证据完整。',
    '（二）须核验本药减轻疾病症状的疗效证据。',
    '（三）须说明本药治疗费用及药品价格是否合理。',
    '（四）须评价本药作用机制是否具有实质技术新颖性。',
    '（五）须说明患者能否负担药费并持续得到所需药物。',
]
doc = Document([
    '药品研究咨询资格规范',
    '第四条 取得研究咨询资格须同时满足以下实质条件：', *five,
    '第五条 文件页码按顺序编排。',
    '第六条 申请药品只有实质满足本规范第四条的全部条件，方可取得本条规定的研究咨询资格。',
    '第七条 第四条材料随卷供查；本条仅登记这些附件的文件编号。',
    '第二章 档案保存',
], '确指实质条件与并行可见材料近邻（合成）')
cs = closed_group(doc, list(range(1,7)), 'C-ARTICLE4', article=4)
cs += programme_contexts(doc, list(range(10)), 'C-DOC')
add('all_five_exact_standard_operatively_applied', doc.packet(8, cs), expected(1,1,1,1,1),
    '当前把第四条全部实质条件用于取得资格，完整同版确指范围及末界已供；五类内容分别成立，不由资格名称自动赋值。',
    [7,9,13,22,39,40,41,44,50,84,94,104,118,125,147,162], 'C',
    ['五维均可消费当前确指的各自实质内容', '完整条件的边界页码不捐献标签'])
add('visible_standard_attachment_numbers_only', doc.packet(9, cs), expected(),
    '同一第四条已完整可见，当前仅登记其材料文件编号，没有实质条件核验或标准决定待遇的关系；看见不等于适用。',
    [9,11,15,22,39,41,42,44,46], 'C')

# D: keep a known same-dimension positive despite a distinct absent exact reference.
# Saved synthetic originals include omitted material for audit location only; candidate gets no full snapshot.
for tag, known, want in [
    ('risk', '第二十一条 药品须核验其给药后过敏反应风险证据。', expected(S=1,E=None,Ec=None,I=None,F=None)),
    ('form', '第二十一条 题名为“风险证据”的附件，其文件名字符须符合归档格式。', expected(S=None,E=None,Ec=None,I=None,F=None)),
]:
    doc = Document([
        known,
        '第二十二条 申请人联系方式按统一格式填写。',
        '第二十三条 药品须核验其治疗获益证据。',
        '第二十四条 附件依日期归档。',
        '本药必须同时满足本规范第二十一条和第二十三条的实质条件。',
    ], '独立已知要求与另条未供范围近邻（合成）-' + tag)
    cs = closed_group(doc, [0], 'D-ARTICLE21-' + tag, article=21)
    add('known_' + tag + '_with_separate_unprovided_article23',
        doc.packet(4, cs, deliver_full=False, undelivered=(2,3)), want,
        ('第21条已供并闭合且直接要求核验药物风险，同维独立阳性S=1保留；第23条仍未交付，其他未知维度不能记0，且S=1不解掉该请求。'
         if tag == 'risk' else
         '第21条已供并闭合但仅附件文件名格式，不产生S实质正类；第23条未交付，五维均保留未知，不能因文件名风险词填1或因首条纯手续填0。'),
        [7,9,13,15,22,23,25,39,40,41,50,84,86,90], 'D',
        ['第23条及其边界未成为候选资源', '独立已知正类与未解请求同时留存',
         '每个确指依赖按实际范围保留，不能生成全局已解决旗标'])

# E: denying inference from labels vs negative substantive appraisal in the current text.
doc = Document([
    '创新性、公平性两项文字仅作药品申报附件的文件名；本条禁止据名称推断药品评价内容，只核验附件签名是否完整。',
    '现有证据不支持认定本药作用机制具有实质技术新颖性；须核验目标患者是否因药物供应不稳定而无法持续得到所需治疗。',
    '第二节 附件传送',
], '文件名否定推断与真正否定评价近邻（合成）')
cs = [doc.context(i, 'E-LITERAL-' + str(i)) for i in range(3)]
add('labels_denied_inference_signature_only', doc.packet(0, cs), expected(),
    '否定的是由文件名推成药品评价的整个关系，实际只核签名；不能将否定中的评价词与栏目名结合制造I/F。',
    [7,9,11,15,22,29,30,33,131,158], 'E')
add('negative_novelty_and_actual_supply_obstacle_information', doc.packet(1, cs), expected(I=1,F=1),
    '当前否定技术新颖性优势仍是药物技术评价；另要求核验药物供应不稳造成持续治疗障碍，实质公平信息成立。没有药效、风险或费用内容。',
    [9,11,13,22,29,30,31,33,118,147,151,154,158], 'E')

# F: one complete mixed-recipient plan, current role selects only its own mechanism.
doc = Document([
    '双轨药品研发与持续供给支持计划',
    '第一条 第一轨面向创新药上市前研发项目，为其设置专门团队的研究方案书面反馈机会。',
    '第二条 第二轨面向现实供药不足、目标患者无法连续得到所需药物的药品，以持续供给缺口决定优先审评资源配置。',
    '第三条 纳入本计划第一轨的创新药研发项目，现可申请上市前研究方案书面反馈。',
    '第四条 对本计划第二轨中现实供药不足的药品，现按该持续供给缺口优先配置审评资源。',
    '第二章 申请表归档',
], '混合支持对象与当前消费者角色近邻（合成）')
cs = programme_contexts(doc, list(range(5)), 'F-DUAL')
add('current_first_track_innovation_not_supply_branch', doc.packet(3, cs), expected(I=1),
    '当前第一轨明确创新研发对象与反馈申请机会，第二轨公平缺口只是平行可见定义；不同对象和轨道不能捐献F。',
    [7,9,13,22,32,42,44,46,52,124,127,139,155,170], 'F',
    ['如实际自然生成only_IF单位，允许消费者为affected_dimensions与{I,F}交集',
     '不注入flag或构造relation，也不由源容器全可见扩大消费者'])
add('current_second_track_supply_not_innovation_branch', doc.packet(4, cs), expected(F=1),
    '当前第二轨以明确持续供药缺口优先配置资源，F成立；第一轨创新身份与研发反馈不能复制，供药不足亦不等于无有效治疗选项。',
    [7,9,13,22,32,42,44,98,124,147,151,154,155,164,170], 'F',
    ['如实际自然生成only_IF单位，允许消费者为affected_dimensions与{I,F}交集',
     '没有自然only_IF单位则报告未实测，不造resolved条款装作源解析'])

assert len(cases) == 12 and len({c['name'] for c in cases}) == 12
assert binding(MANUAL)['sha256'] == MANUAL_SHA
manual_raw = MANUAL.read_text(encoding='utf-8')
manual_lines = manual_raw.splitlines(keepends=True)
used_lines = sorted({line for case in cases for line in case['manual_lines']})
quote_rows = []
for n in used_lines:
    u = sum(map(len, manual_lines[:n-1])); text = manual_lines[n-1]
    assert manual_raw[u:u+len(text)] == text
    quote_rows.append({'line_1based': n, 'unicode_span_half_open': [u,u+len(text)], 'quote': text})
write('manual-basis-quotes.json', {'binding': binding(MANUAL), 'quotes': quote_rows,
                                 'no_manual_or_dimension_change': True})
write('controls12-fixed-before-execution.json', {
    'status': 'hidden_independent_source_only_controls_prepared_no_candidate_execution',
    'case_N': 12, 'paired_groups_N': 6, 'dimensions': list(DIMENSIONS),
    'manual_binding': binding(MANUAL), 'candidate_algorithm_binding': None,
    'expectation_basis': 'frozen manual substantive threshold and complete current source propositions; no future implementation or owner answers',
    'cases': cases, 'no_formal_human_reference': True,
    'expected_changes_after_candidate_execution_allowed': False,
    'no_synthetic_result_submitted_as_corpus_prediction': True})

checks = []
for case in cases:
    document = case['synthetic_documents'][0]
    original_raw = Path(document['binding']['path']).read_bytes()
    assert digest(original_raw) == document['binding']['sha256']
    original = original_raw.decode('utf-8')
    bundle = case['synthetic_bundle']
    for label, text, ref in [('current', bundle['source_record']['text'], bundle['source_record']['source_ref'])] + [
        ('context:' + c['context_id'], c['text'], c['source_ref']) for c in bundle['source_record']['contexts'] if c['text']]:
        assert ref['sha256'] == document['binding']['sha256']
        loc = ref['locator']; a,b = loc['unicode_code_point_interval_half_open']; c,d = loc['utf8_byte_interval_half_open']
        assert original[a:b] == text and original_raw[c:d].decode('utf-8') == text
        assert original[:a].count('\n')+1 == loc['physical_line_interval_inclusive'][0]
        checks.append({'case': case['name'], 'label': label, 'text': text, 'source_ref': ref,
                       'literal_codepoint_byte_line_and_original_SHA_match': True})
    if document['undelivered_paragraph_indexes_zero_based']:
        assert bundle['source_full_text_resources'] == []
        present = {c['source_ref'].get('locator',{}).get('sequence_index') for c in bundle['source_record']['contexts'] if c['text']}
        assert not present.intersection(document['undelivered_paragraph_indexes_zero_based'])
    assert not any('only_IF_consumers' in c or 'affected_dimensions' in c for c in bundle['source_record']['contexts'])
write('literal-geometry-preparation-check.json', {'status': 'pass_no_algorithm_called', 'case_N': 12,
    'checks_N': len(checks), 'checks': checks, 'byte_codepoint_and_line_intervals_half_open_except_lines': True,
    'missing_material_not_accidentally_in_candidate_inventory': True,
    'no_relation_receipt_or_consumer_flag_injected': True})
write('source-interface-and-exposure-boundary.json', {
    'manual': binding(MANUAL), 'source_packet_contract': binding(SOURCE_CONTRACT),
    'evidence_contract': binding(EVIDENCE_CONTRACT),
    'geometry_helper_source': binding(ROOT/'08-audits/five-dimension-joint-independent-controls-sol/prepare_joint_controls.py'),
    'source_only_packet_keys': sorted(cases[0]['synthetic_bundle']),
    'raw_synthetic_paragraphs_and_bounded_containers_are_input_not_relations': True,
    'source_visible_inventory_is_not_current_applicability': True,
    'consumer_intersection_requirement': 'allowed = affected_dimensions; if only_IF: allowed &= {I,F}',
    'only_IF_gate_dynamic_coverage': 'await_actual_source_parser_generation; no generation means not_exercised',
    'known_positive_and_different_unresolved_reference_both_preserved': True,
    'no_injected_resolved_receipts': True,
    'reads_for_preparation': ['frozen manual specified lines', 'own sealed source-only geometry helpers and SourcePacket/evidence shape',
                              'own previously sealed first-execution semantic defects as problem scope, no answer transplantation'],
    'not_read': ['future v3 algorithm or future owner expectations', 'ROOT new control answers',
                 'owner full77/800 predictions', 'main fullLLM partial labels'],
    'candidate_imports_N': 0, 'SourcePacket_or_RelationView_new_control_execution_N': 0,
    'candidate_judge_attempts_N': 0, 'real_human_or_formal_statistics_N': 0,
    'ROOT_owner_files_modified': False})
with (OUT/'README.txt').open('x',encoding='utf-8') as f:
    f.write('12项联合v3独立近邻控制，6组成对。预期、完整合成原文及实际可供几何先于最终候选固定；ROOT仅接收数量与预封存SHA，尚不发送病例或预期。\n'
            '范围：实际创新研发服务与格式；明示相对缩时与普通期限；五维操作性确指标准与并行可见附件；已知同维正类与另一确指缺材；附件名否定推断与真正否定评价；混合角色与消费者范围。\n'
            '本准备不导入候选、不执行SourcePacket/RelationView/judge、不构造关系或收据，不注入only_IF。缺材原件只为输入定位独立保存；缺失段不作为候选资源。\n'
            '未来最终v3封存后原12各一次执行，保留NULL与全部首次失败，不改预期。only_IF若未由实际来源自然生成，仅报告未实测。合成控制不是真人参照或正式统计验证。\n')
write('preparation-readback.json', {'case_N': 12, 'paired_groups_N': 6,
    'full_saved_synthetic_documents_N': len(list(DOCUMENTS.glob('*.txt'))),
    'candidate_judge_attempts_N': 0, 'expected_fixed_before_final_algorithm_seal': True,
    'manual_SHA_verified': True, 'literal_geometry_checked': True,
    'future_algorithm_not_yet_bound': True})
members = [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('preparation-seal.json', {'status': 'hidden_independent12_prepared_await_final_joint_v3_seal',
    'prepared_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'case_N': 12, 'paired_groups_N': 6,
    'candidate_judge_attempts_N': 0, 'candidate_algorithm_binding': None, 'manual_binding': binding(MANUAL),
    'output_members': members, 'seal_self_excluded': True,
    'expected_and_case_content_not_disclosed_before_final_algorithm_seal': True, 'owner_or_ROOT_files_modified': False})
for member in members:
    assert binding(member['path']) == member
print(json.dumps({'case_N': 12, 'paired_groups_N': 6, 'candidate_judge_attempts_N': 0,
                  'preparation_seal': binding(OUT/'preparation-seal.json'), 'members_N': len(members)},ensure_ascii=False))
