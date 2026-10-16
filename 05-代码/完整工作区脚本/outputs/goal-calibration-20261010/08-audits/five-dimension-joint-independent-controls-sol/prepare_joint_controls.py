#!/usr/bin/env python3
"""Preseal independent joint controls, source geometry and manual bases only.

This preparation script never imports an algorithm, constructs RelationView,
calls judge, reads outcome files, or changes any owner material.  Candidate
binding and execution deliberately await ROOT's final joint algorithm seal.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'
CONTRACT_SOURCE = ROOT / '08-audits/SE-Ec-v2-independent-controls-sol/code-snapshot/source_packet.py'
CONTRACT_EVIDENCE = ROOT / '08-audits/SE-Ec-v2-independent-controls-sol/code-snapshot/evidence.py'
CONTRACT_SE_RELATIONS = ROOT / '08-audits/SE-Ec-v2-independent-controls-sol/code-snapshot/relations.py'
CONTRACT_IF_RELATIONS = ROOT / '06-coding/rule-v20-semantic-audit-repair-sol/versions/v2/relations.py'
CONTRACT_SE_DIMENSIONS = ROOT / '08-audits/SE-Ec-v2-independent-controls-sol/code-snapshot/dimensions.py'
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
                             'source_version_id': 'SYNTHETIC-JOINT-2026-V1',
                             'synthetic_control_not_policy_original': True}}

    def context(self, i, cid, kind='source_paragraph', **structure):
        loc = self.locators[i]
        return {'context_id': cid, 'kind': kind, 'text': self.paragraphs[i],
                'source_document': 'SOURCE-' + self.sha, 'source_ref': self.ref(i),
                'structure': {'paragraph_id': loc['paragraph_id'],
                              'source_paragraph_id': loc['source_paragraph_id'],
                              'sequence_index': loc['sequence_index'],
                              'component_id': loc['component_id'],
                              'source_version_id': 'SYNTHETIC-JOINT-2026-V1', **structure}}

    def geometry(self, cid, kind, **structure):
        return {'context_id': cid, 'kind': kind, 'text': '',
                'source_document': 'SOURCE-' + self.sha,
                'source_ref': {'sha256': self.sha, 'source_resource_id': 'SOURCE-' + self.sha,
                               'locator': {'kind': 'synthetic_bound_geometry',
                                           'component_id': structure.get('component_id', 'JOINT-COMPONENT'),
                                           'source_utf8_absolute_path': str(self.path)}},
                'structure': {'component_id': 'JOINT-COMPONENT',
                              'source_version_id': 'SYNTHETIC-JOINT-2026-V1', **structure}}

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
                              'source_version_id': 'SYNTHETIC-JOINT-2026-V1',
                              'document_title': self.title, 'document_year': 2026,
                              'locator': {'kind': 'synthetic_complete_UTF8_snapshot',
                                          'unicode_code_point_interval_half_open': [0, len(self.raw)],
                                          'utf8_byte_interval_half_open': [0, len(self.raw.encode('utf-8'))],
                                          'physical_line_interval_inclusive': [1, self.raw.count('\n')],
                                          'source_utf8_absolute_path': str(self.path)}})
        result = {'common_source_bundle_version': {'status': 'synthetic_source_only_joint_control'},
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


five_members = [
    '（一）应核验本药用药后肝损伤的风险证据。',
    '（二）应核验本药降低疾病复发率的疗效证据。',
    '（三）应比较本药的药品价格与治疗成本。',
    '（四）应评价本药新作用机制的技术新颖性。',
    '（五）应说明收入较低患者能否负担并持续获得所需药物。',
]

# A: substantive head vs organisational head; source members are identical.
doc = Document(['申请药品必须就下列内容提供实质证据：', *five_members,
                '第二节 附件编号管理。', '下列条目依次列出：', *five_members,
                '第三节 页码编排。'], '实质证据与索引列示联合控制（合成）')
active = closed_group(doc, list(range(0, 6)), 'ACTIVE')
pure = closed_group(doc, list(range(7, 13)), 'INDEX')
add('substantive_five_content_head', doc.packet(0, active + pure), expected(1,1,1,1,1),
    '当前独立要求提供药品五类实质内容，完整确指成员分别成立；不是由标题汇总。',
    [7,9,15,22,23,39,58,62,84,94,104,118,147], 'A')
add('organisational_head_same_five_members', doc.packet(7, active + pure), expected(),
    '相同实质文字已供，但当前仅组织列示，没有本单元独立评价、条件或后果，不复制成员标签。',
    [9,22,39,42,58,62], 'A')

# B: same complete source, choose one exact member; brothers cannot donate.
parent_for_e = doc.context(0, 'DIRECT-HEAD-E', 'parent_paragraph',
                           target_paragraph_id=doc.locators[2]['paragraph_id'])
parent_for_s = doc.context(0, 'DIRECT-HEAD-S', 'parent_paragraph',
                           target_paragraph_id=doc.locators[1]['paragraph_id'])
add('selected_effect_member_in_five_content_group', doc.packet(2, active + [parent_for_e]), expected(E=1),
    '当前只核验复发率的药物效果证据，直接父谓词不使风险、价格、技术新颖性或患者负担兄弟项在本记录成立。',
    [7,15,22,39,42,56,58,94,96], 'B')
add('selected_risk_member_in_same_five_content_group', doc.packet(1, active + [parent_for_s]), expected(S=1),
    '同一完整原文改以风险证据成员为当前；风险议题成立，疗效及其他兄弟成员不继承。',
    [7,15,22,39,42,56,58,84,86], 'B')

# C: implementation of a specific mechanism vs current operational standard.
programme = [
    '创新研发辅导计划',
    '第一条 本计划仅面向创新药的上市前研发项目，纳入后的研究方案反馈由专门团队提供。',
    '第二条 对纳入创新研发辅导计划的项目，现开放该计划的研究方案反馈服务。',
    '第六条 维持反馈资格的药品须同时满足以下实质条件：',
    *five_members,
    '第七条 申请表按日期顺序归档。',
    '第八条 为维持创新研发辅导计划的研究方案反馈资格，药品须满足本计划第六条全部实质条件。',
    '第二章 常规档案管理',
]
pdoc = Document(programme, '创新研发辅导计划联合控制（合成）')
pscope = programme_contexts(pdoc, list(range(0,11)), 'PLAN')
standard6 = closed_group(pdoc, list(range(3,9)), 'ARTICLE6', 'cited_reference', '第六条')
add('current_named_feedback_does_not_copy_parallel_conditions', pdoc.packet(2, pscope + standard6), expected(I=1),
    '当前开放同版同阶段研发反馈服务，已供创新药研发对象、纳入后可用服务和直接联系；没有当前标准核验，不展开并行资格中的安全、效果、费用、患者负担。',
    [9,13,22,42,44,46,52,124,127,135,137,139], 'C',
    [{'kind':'relation_specific_consumption', 'rule':'mechanism_object_and_service_are_not_operational_standard_conditions'},
     {'kind':'only_IF_consumer_intersection', 'rule':'a_linked_unit_may_only_feed_affected_dimensions_intersect_IF_when_only_IF_is_true'}])
add('current_operational_standard_in_same_feedback_plan', pdoc.packet(10, pscope + standard6), expected(1,1,1,1,1),
    '当前明确以第六条全部实质条件维持具体反馈资格，完整同版条件按实际内容逐维成立；与单纯开放服务路径分开。',
    [9,13,22,39,40,41,44,50,124,125,147,151,162], 'C')

# D: one arrangement has different actual recipients. An opportunity for one
# branch is not an opportunity for all other branches in the programme.
scope_doc = Document([
    '分类优先审评程序',
    '一、适用范围',
    '（一）创新药上市前研发项目。',
    '（二）临床急需且现实供药不足的药品。',
    '二、支持安排',
    '对本程序中的创新药研发项目，审评时限由普通程序的六十日缩短为四十日。',
    '对本程序中的临床急需且现实供药不足药品，依该保障缺口优先配置审评资源。',
    '三、档案管理',
], '分类优先审评程序联合控制（合成）')
sc = programme_contexts(scope_doc, list(range(0,7)), 'PRIORITY')
gate = [{'kind':'only_IF_consumer_intersection',
         'rule':'every_consumed_relation_with_only_IF_true_is_limited_to_affected_dimensions_intersection_I_F'},
        {'kind':'no_unrelated_branch_donation',
         'rule':'an_opportunity_for_one_explicit_object_cannot_consume_the_other_object_branch'}]
add('innovation_timed_review_not_other_object_supply_gap', scope_doc.packet(5, sc), expected(I=1),
    '当前把相对普通程序缩短审评时限用于明确创新研发对象；另一对象的供药缺口已可见，但未与本记录资源机会相连，不能借F。',
    [9,13,22,32,42,44,46,124,127,155,164,170], 'D', gate)
add('supply_gap_priority_not_other_object_innovation', scope_doc.packet(6, sc), expected(F=1),
    '当前实际依明确现实供药缺口优先配置资源，满足上游按需机会关系；另一对象为创新研发并不使本分支自动成为创新支持。供药不足不推成无有效药。',
    [9,13,22,32,42,44,98,124,147,151,154,155,170], 'D', gate)

# E: literally identical text is a closure boundary or the fixed current row.
boundary_text = '第八条 应评价本药的用药风险、疗效、治疗成本、技术新颖性与患者可负担性。'
edoc = Document([
    '药品须满足本规范第七条的药物效果证据要求。',
    '第七条 应证明本药的疾病控制效果证据充分。',
    boundary_text,
    '附录标题',
    boundary_text,
    '附录结束。',
], '原文角色与重复文字联合控制（合成）', {3:'APPENDIX',4:'APPENDIX',5:'APPENDIX'})
ecs = [edoc.context(1, 'ARTICLE7', 'cited_article', article='第七条'),
       edoc.context(2, 'CLOSURE-NEXT8', 'following_heading', article='第八条'),
       edoc.context(4, 'REMOTE-SAME-LITERAL', 'source_paragraph')]
add('five_content_literal_only_article7_boundary', edoc.packet(0, ecs), expected(E=1),
    '第八条的五类实质文字只证明第七条结束；相同字面在附录重复，均不是当前第七条的成员。当前只援引药物效果证据。',
    [22,23,39,40,42,56], 'E',
    [{'kind':'closure_quote_no_label_donation',
      'context_ids':['CLOSURE-NEXT8','REMOTE-SAME-LITERAL'],
      'rule':'boundary_or_unrelated_literal_duplicate_must_not_supply_positive_content'}])
add('same_five_content_literal_is_now_current', edoc.packet(2, ecs), expected(1,1,1,1,1),
    '字面不变但记录位置选择第八条本身，当前实质要求评价五维；另一案例的边界用途不使本记录内容被全局去重删除。',
    [7,9,11,13,22,23,56,84,94,104,118,147,158,162], 'E',
    [{'kind':'role_and_position_not_literal_global_dedup',
      'rule':'the_current_occurrence_is_not_deleted_because_the_same_text_was_a_boundary_elsewhere'}])

# F: a current, precise anaphor excludes a same-paragraph brother topic.
effect_now = '应核验上述复发率疗效信息是否充分。'
risk_now = '应核验上述肝损伤风险信息是否充分。'
full_f = ('本药的用药风险资料记载肝损伤发生率。'
          '本药的疗效资料记载疾病复发率。' + effect_now + risk_now)
fdoc = Document([full_f, '本段结束，下一段处理附件编号。'], '同段明确指示联合控制（合成）')
fcs = [fdoc.context(0, 'FULL-CURRENT-PARAGRAPH', 'parent_paragraph',
                   unit_id='SYNTHETIC-ONE-PARAGRAPH', target_paragraph_id='p0001')]
add('precise_recurrence_anaphor_excludes_liver_risk', fdoc.packet(0, fcs, current_text=effect_now), expected(E=1),
    '当前明确承接复发率疗效资料，仅补足这个疗效对象，不能把同段肝损伤风险资料或另一核验句复制进来。',
    [15,22,23,39,42,94,96,100], 'F')
add('precise_liver_risk_anaphor_excludes_recurrence_effect', fdoc.packet(0, fcs, current_text=risk_now), expected(S=1),
    '同一完整段落改选肝损伤风险核验句为当前，有限指示对象排除同段疗效资料和另一核验句。',
    [15,22,23,39,42,84,86,90], 'F')

# G: resolving one exact reference may not clear a different stopped request.
gdoc = Document([
    '第十条 药品须核验过敏反应风险证据。',
    '第十一条 申报材料页码应连续。',
    '第十二条 药品须比较治疗费用是否合理。',
    '第十三条 附件以日期编排。',
    '药品必须符合本规范第十条和第十二条的实质条件。',
], '两个确指条件的独立依赖联合控制（合成）')
g10 = [gdoc.context(0, 'ARTICLE10', 'cited_article', article='第十条'),
       gdoc.context(1, 'ARTICLE11-BOUNDARY', 'following_heading', article='第十一条')]
g12 = [gdoc.context(2, 'ARTICLE12', 'cited_article', article='第十二条'),
       gdoc.context(3, 'ARTICLE13-BOUNDARY', 'following_heading', article='第十三条')]
requests = [{'kind':'independent_dependency_preservation',
             'resolved_reference':'第十条', 'stopped_reference':'第十二条',
             'rule':'a_resolution_receipt_can_close_only_its_exact_request_scope_and_must_not_blanket_clear_other_stopped_requests'},
            {'kind':'receipt_literal_source_match',
             'rule':'every_claimed_resolved_receipt_must_point_to_the_exact_supplied_version_reference_and_complete_scope'}]
add('article10_supplied_article12_still_stopped',
    gdoc.packet(4, g10, deliver_full=False, undelivered=(2,3)),
    expected(None,None,None,None,None),
    '当前同时要求两条实质条件；第十条已供且闭合，第十二条关键范围未交付，不能把第一条成功补足变成所有依赖已解。未知条件的消费者保持NULL，不能补0。保存的合成原件不是候选的可见资源。',
    [22,23,25,39,40,41,50], 'G', requests)
add('both_exact_articles_supplied_independently_closed', gdoc.packet(4, g10 + g12), expected(S=1,Ec=1),
    '同一合成原件中第二条范围现在实际交付，两条完整要求分别涉及风险证据和治疗费用；闭合边界的页码/附件安排不贡献其他维度，收据须按各确指范围匹配。',
    [7,13,22,23,39,40,41,84,86,104,106], 'G',
    [{'kind':'receipt_literal_source_match',
      'rule':'distinct_reference_resolutions_need_exact_reference_and_source_scope_receipts_not_a_global_resolved_flag'}])

# H: denial of the property vs denial of an inference from formal filenames.
negative_content = ('现有证据尚不能确认本药肝损伤风险较低，亦未证实其降低疾病复发率的疗效；'
                    '应核验本药治疗费用是否合理；应评价本药所称新作用机制是否具有技术新颖性；'
                    '应查明患者是否因无力支付药费而不能持续获得所需治疗。')
formal_content = ('药物安全性、有效性、经济性、创新性和公平性五个栏目均仅用作附件文件名，'
                  '不据附件名推定任何药品评价或支持安排；本条仅核验文件是否已签章。')
hdoc = Document([negative_content, formal_content], '完整否定范围联合控制（合成）')
add('uncertain_or_negative_properties_are_topics', hdoc.packet(0, []), expected(1,1,1,1,1),
    '否定优势或证据不足仍是风险/效果/技术新颖性议题，费用核验和患者无力支付也有独立关系；不声称药品已具优势或障碍已经证实。',
    [9,15,29,30,31,33,84,94,96,104,106,118,122,123,147,156,162], 'H')
add('formal_filename_inference_explicitly_denied', hdoc.packet(1, []), expected(),
    '否定的是从文件名推定实质评价/支持的整个关系，当前实际操作仅签章核验；不能只摘维度词把否定推断改成评价要求。',
    [9,11,15,29,30,33,90,110,131,158], 'H')

# I: disjunctive whole condition has a substantive branch; a formal brother
# does not inherit it even while the complete OR group remains visible.
idoc = Document([
    '本药符合以下任一条件的，可以申请优先审评：',
    '（一）目标疾病尚无有效治疗药物可供选择。',
    '（二）申报表的页码连续。',
    '第二节 文件传送步骤。',
], '并列或分支联合控制（合成）')
ics = closed_group(idoc, [0,1,2], 'OR')
ics[0]['structure']['group_operator'] = 'OR'
ics.append(idoc.context(0, 'OR-DIRECT-PARENT', 'parent_paragraph',
                        target_paragraph_id=idoc.locators[2]['paragraph_id'], group_operator='OR'))
add('whole_OR_has_effect_gap_and_need_opportunity', idoc.packet(0, ics), expected(E=1,F=1),
    '当前实际以任一分支给申请机会，第一分支明确无有效治疗选项并连接针对性优先审评；E与上游F分别有依据。第二分支不会被改写为无有效药或公平需要。',
    [7,13,29,31,32,39,41,50,62,94,96,147,154,155,170], 'I')
add('formal_OR_member_does_not_inherit_effect_gap', idoc.packet(2, ics), expected(),
    '当前仅是页码连续分支，即使直接父句提供优先程序机会，也未由本分支表达效果缺口或按需保障关系；不借第一分支的E/F。',
    [9,15,22,32,39,41,42,50,58,164,170], 'I')

# J: a real named current service vs a mere archived membership state.
jdoc = Document([
    '创新方案协作计划',
    '第一条 本计划面向创新药上市前研发，纳入者可获得专门团队的研究方案书面反馈。',
    '第二条 纳入该计划的创新药研发项目，可获得该计划提供的上市前研究方案书面反馈。',
    '第三条 档案表记载甲项目曾被列入创新方案协作计划；本句仅要求更新该项目的档案行号。',
    '第二章 日常档案事务',
], '支持行动与历史身份联合控制（合成）')
jcs = programme_contexts(jdoc, [0,1,2,3], 'FEEDBACK')
add('named_service_actual_current_access', jdoc.packet(2, jcs), expected(I=1),
    '当前向明确创新药研发对象实际开放上市前方案反馈，可用机制与对象直接相连；不要求服务已被使用或是首次设立。',
    [9,22,44,46,52,124,127,133,135,137,139], 'J')
add('archived_membership_and_row_number_only', jdoc.packet(3, jcs), expected(),
    '共同材料已有同版支持定义，但当前仅记历史成员状态并更新档案行号，没有独立支持设立/适用行动；不能把身份或已看见机制当当前待遇。',
    [9,15,22,41,42,44,46,52,131,135], 'J')

assert len(cases) == 20 and len({c['name'] for c in cases}) == 20
assert sorted({c['pair_group'] for c in cases}) == list('ABCDEFGHIJ')


def validate_geometry(case):
    """Only literal/shape validation; no imports from any algorithm module."""
    packet = case['synthetic_bundle']; row = packet['source_record']
    document = case['synthetic_documents'][0]
    raw = document['text']; rawbytes = raw.encode('utf-8')
    assert digest(rawbytes) == row['source_ref']['sha256'] == document['binding']['sha256']
    assert Path(document['binding']['path']).read_bytes() == rawbytes
    assert set(packet) == {'common_source_bundle_version','source_record','source_documents',
                           'explicit_or_primary_source_resources',
                           'preserved_historical_neutral_source_supplements','source_full_text_resources',
                           'source_asset_locations','source_locator_bases','source_reference_index',
                           'source_provenance_addenda'}
    uu = row['source_ref']['locator']['unicode_code_point_interval_half_open']
    bb = row['source_ref']['locator']['utf8_byte_interval_half_open']
    assert raw[uu[0]:uu[1]] == row['text']
    assert rawbytes[bb[0]:bb[1]].decode('utf-8') == row['text']
    ids = {c['context_id']:c for c in row['contexts']}
    assert len(ids) == len(row['contexts'])
    text_N = 0; geometry_N = 0
    for ctx in row['contexts']:
        assert ctx['source_ref']['sha256'] == document['binding']['sha256']
        if ctx['text']:
            loc = ctx['source_ref']['locator']; a,b = loc['unicode_code_point_interval_half_open']
            x,y = loc['utf8_byte_interval_half_open']
            assert raw[a:b] == ctx['text'] and rawbytes[x:y].decode('utf-8') == ctx['text']
            first,last = loc['physical_line_interval_inclusive']
            assert raw[:a].count('\n')+1 == first
            assert last == first + ctx['text'].count('\n')
            for field in ('paragraph_id','sequence_index','component_id'):
                assert ctx['structure'][field] == loc[field]
            text_N += 1
        else:
            geometry_N += 1
        for group in ctx['structure'].get('child_groups', []):
            g = group['ordered_context_ids']
            assert g and len(g) == len(set(g)) and all(cid in ids for cid in g)
        if ctx['kind'] == 'boundary_container':
            st = ctx['structure']; container = ids[st['parent_context_id']]
            member_groups = [g for g in container['structure']['child_groups'] if g['position'] in ('members','contexts')]
            assert len(member_groups) == 1
            members = [ids[cid] for cid in member_groups[0]['ordered_context_ids']]
            assert st['first_paragraph'] == members[0]['structure']['paragraph_id']
            assert st['last_paragraph'] == members[-1]['structure']['paragraph_id']
            assert [c['structure']['sequence_index'] for c in members] == list(range(
                members[0]['structure']['sequence_index'],members[-1]['structure']['sequence_index']+1))
            children = [ids[cid] for cid in st['text_child_context_ids']]
            assert len(children) == 1
            child = children[0]
            assert child['structure']['paragraph_id'] == st['next_paragraph_id']
            assert child['structure']['sequence_index'] == members[-1]['structure']['sequence_index']+1
            assert all(c['structure']['component_id'] == st['component_id'] for c in [*members,child])
    for leaf in packet['source_full_text_resources']:
        assert leaf['text'] == raw and leaf['text_utf8_sha256'] == digest(rawbytes)
    unavailable = document['undelivered_paragraph_indexes_zero_based']
    assert not unavailable or not packet['source_full_text_resources']
    for i in unavailable:
        target = document['paragraph_locators'][i]['paragraph_id']
        assert all(c['structure'].get('paragraph_id') != target for c in row['contexts'])
    vals = case['expected_values_fixed_before_execution']
    assert set(vals) == set(DIMENSIONS)
    assert all(v is None or (type(v) is int and v in (0,1)) for v in vals.values())
    return {'name':case['name'], 'source_geometry_valid':True,
            'literal_text_context_N':text_N, 'textless_geometry_context_N':geometry_N,
            'current_anchor_unicode_byte_line_match':True,
            'all_supplied_quotes_have_exact_synthetic_original_coordinates':True,
            'unavailable_source_paragraphs_not_delivered':unavailable,
            'candidate_algorithm_called':False}


manual_binding = binding(MANUAL)
assert manual_binding['sha256'] == MANUAL_SHA
manual_lines = MANUAL.read_text(encoding='utf-8').splitlines(keepends=True)
selected = sorted({n for c in cases for n in c['manual_lines']})
quotes = []; offset = 0
for n, line in enumerate(manual_lines, 1):
    if n in selected:
        quotes.append({'line_1based':n, 'unicode_span_half_open':[offset,offset+len(line)], 'quote':line})
    offset += len(line)
write('manual-basis-quotes.json', {'binding':manual_binding,'quotes':quotes,
                                  'no_manual_or_dimension_change':True})

# These are abstract route truth tables, not fake classified policy records and
# not injected resolved-source evidence.  They constrain future observations.
consumer_vectors = [
    {'only_IF_consumers':True, 'affected_dimensions':['I'], 'allowed':['I']},
    {'only_IF_consumers':True, 'affected_dimensions':['F'], 'allowed':['F']},
    {'only_IF_consumers':True, 'affected_dimensions':['S','E','Ec','I'], 'allowed':['I']},
    {'only_IF_consumers':True, 'affected_dimensions':['S','E','Ec'], 'allowed':[]},
    {'only_IF_consumers':True, 'affected_dimensions':['Ec','F'], 'allowed':['F']},
    {'only_IF_consumers':False, 'affected_dimensions':['E','F'], 'allowed':['E','F']},
]
for v in consumer_vectors:
    allowed = set(v['affected_dimensions']) & (set(('I','F')) if v['only_IF_consumers'] else set(DIMENSIONS))
    assert v['allowed'] == [d for d in DIMENSIONS if d in allowed]
contract_bindings = [binding(p) for p in (CONTRACT_SOURCE,CONTRACT_EVIDENCE,CONTRACT_SE_RELATIONS,CONTRACT_IF_RELATIONS,CONTRACT_SE_DIMENSIONS)]
assert [b['sha256'] for b in contract_bindings] == [
    '637332307d059e7f03af94441aaf4a012843c0541b549a2820b386b370c80611',
    '5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3',
    '13ef52a6190ddcff6288c00f5122cfa9ebdbec2add8ee3bde15b5888fd68c313',
    '13f5eb351d39a8b8cf12bff8e6a4976570baf3719a4be85d216933f406e02bc2',
    'fd7d32569d604474ad6d102ead96759260b137e294bfc6b03991cc652b395483',
]
write('source-relation-interface-contract.json', {
    'status':'independent_contract_read_static_no_candidate_execution',
    'source_only_packet_keys':sorted(cases[0]['synthetic_bundle']),
    'source_contract_bindings':contract_bindings,
    'manual_binding':manual_binding,
    'read_scope':[
        'SourcePacket semantic_unit: raw fields preserved, administrative id removed, exact neutral resource aliases',
        'SourcePacket source inventory: availability is not reading/use/applicability',
        'RelationView public relation envelope, request objects, literal source roles, bounded current-source/reference geometry',
        'evidence validate_decisions: exact five decisions, complete current positive proposition, literal context refs, specific NULL need',
        'Existing IF and SE relation/dimensions consumer declarations read as interface shape; no output or owner expected table read for this task',
    ],
    'abstract_consumer_vectors_not_extra_classified_cases':consumer_vectors,
    'consumer_vector_execution_status':'not_executed_against_final_joint_candidate',
    'required_execution_constraints':[
        'No injected relation receipt, no post-hoc label donation, no mutation of source packet or algorithm',
        'Consume a linked relation only in affected_dimensions; only_IF further intersects that set with I/F',
        'Literal closure boundaries are proof of scope and cannot become members by same-text lookup',
        'Current exact references/actions select roles, components, stages and branches; source availability alone cannot select them',
        'Every resolved receipt must close one exact reference and source/version/scope; keep every different stopped request and its affected consumer route',
        'A positive dimension keeps whole current proposition plus literal needed source relations; unresolved necessary dependency keeps NULL',
        'If a closed final candidate exposes no neutral executable consumer-gate probe, record that probe not executed; do not manufacture resolved source relations to satisfy it',
    ],
    'final_candidate_not_bound_yet':True,
    'current_merge_baseline_not_tested_or_endorsed':True,
})

checks = [validate_geometry(c) for c in cases]
write('controls20-fixed-before-execution.json', {
    'status':'independent_unexecuted_joint_controls_fixed_before_final_algorithm',
    'case_N':20, 'paired_groups_N':10, 'dimensions':list(DIMENSIONS),
    'manual_binding':manual_binding, 'candidate_algorithm_binding':None,
    'expectation_basis':'frozen_manual_and_source_relation_contract_not_owner_targets',
    'cases':cases,
    'no_formal_human_reference':True,
    'expected_changes_after_candidate_execution_allowed':False,
    'no_synthetic_result_submitted_as_corpus_prediction':True,
})
write('literal-geometry-preparation-check.json', {
    'status':'mechanical_preparation_only', 'case_N':20, 'cases':checks,
    'all_saved_synthetic_UTF8_source_SHA_and_current_context_coordinates_match':True,
    'candidate_judge_attempts_N':0, 'RelationView_instances_N':0,
    'SourcePacket_module_calls_N':0, 'real_source_records_classified_N':0,
    'no_full77_800_4481_execution':True,
})
write('read-and-exposure-boundary.json', {
    'status':'preparation_only_wait_final_joint_algorithm_seal',
    'actual_task_reads':[
        'frozen manual L1-170; exact lines used by each fixed control separately saved',
        'frozen source_packet.py general source-only unit/inventory contract',
        'frozen evidence.py complete literal evidence validator',
        'old sealed IFv2/SEv2 relations and SEv2 dimensions public envelope/source role/current geometry/consumer declaration excerpts',
        'old own preparation script for geometry fixture shape, including already exposed old control declarations in the same excerpt; no old outcome or owner expected-table file read, and those old targets not adopted as new case targets',
        'own 20 new full synthetic originals, all delivered contexts/current coordinates and finite geometry',
    ],
    'input_source_SHA_bindings':contract_bindings+[manual_binding],
    'owner_or_ROOT_final_expected_tables_read':False,
    'owner77_800_replay_labels_read':False,
    'main_LLM_partial_output_read':False,
    'neutral_projection_applied':False,
    'current_merge_baseline_code_or_expected_table_read':False,
    'candidate_algorithm_imported_or_run':False,
    'actual_human_validation_performed':False,
    'new_controls_are_not_for_tuning_the_pending_merge':True,
    'disclosure_to_ROOT_before_final_algorithm_seal':'case count, seal SHA, preparation status only; no case content or expected values',
    'postseal_control_mutation_allowed':False,
})
with (OUT/'README.txt').open('x',encoding='utf-8') as stream:
    stream.write(
        '联合五维独立控制：准备完成，等待最终联合算法封存\n\n'
        '本目录固定20项独立联合接口控制，组成10组正反/角色对照。预期依据冻结共同手册5ea7与既有来源关系契约，'
        '在任何最终联合算法导入、RelationView构造或judge调用之前保存。本次分类执行次数为0。'
        'ROOT当前merge-baseline01及待修几何代码均未读取、未运行、未背书。\n\n'
        'controls20-fixed-before-execution.json保存五维预期、当前完整命题、每个已供语境的原文与结构、'
        '完整合成UTF8原件及实际字符/字节/行坐标、未交付范围、手册依据和接口约束。'
        '同一完整来源在不同当前位置或关系角色下使用，不能按字面全局去重或转移维度。'
        'synthetic-source-documents全部是真正落盘的合成原件，不是政策原件、主语料预测或真人参照。'
        '其中故意不交付的范围只留在独立原件证据中，未来候选只能收到synthetic_bundle，不能读取整个case或合成原件文件自行补足。\n\n'
        'literal-geometry-preparation-check仅核对包键、完整记录、精确引文、SHA、坐标、容器及连续边界；'
        '未调用任何候选模块。source-relation-interface-contract的消费者真值表是抽象契约约束，'
        '不是额外分类样本，不伪造程序已解析的关系或收据。最终算法实际执行时应核查已生成且实际消费的关系；'
        '若没有可用的中性消费门控探针，应明确未执行该探针，不得注入假resolved关系冒充端到端结果。\n\n'
        '收到ROOT最终联合算法seal后，另存execution目录，先核候选全部绑定与本准备seal，'
        '每项只向候选提供完整source-only包，经SourcePacket→RelationView→judge→validate_decisions一次执行，'
        '逐项保存五维原输出、NULL/异常、source_requests、实际resolved收据、关系轨迹、读取与使用差异。'
        '逐条核验current与所有证据的字面、位置、版本、角色和实际补足关系。原预期与本准备文件保持不变，'
        '任何失败都保留。仅做这些有限控制，不跑全77/800/4481。\n\n'
        'ROOT及所有者在最终算法封存前只接收数量、SHA与准备状态，不发送具体病例及预期用于调合并。'
        '候选执行后的控制为公开开发暴露，不把修复后复放称独立验证；AI合成控制不是正式真人效度或信度检验。\n'
    )

members = [binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
seal = {'status':'independent_joint_controls_presealed_unexecuted_wait_final_joint_algorithm',
        'prepared_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'case_N':20, 'paired_groups_N':10, 'candidate_judge_attempts_N':0,
        'candidate_algorithm_binding':None, 'manual_binding':manual_binding,
        'output_members':members, 'seal_self_excluded':True,
        'expected_and_case_content_not_disclosed_before_final_algorithm_seal':True,
        'owner_or_ROOT_files_modified':False}
write('preparation-seal.json', seal)
for member in members:
    actual = binding(member['path'])
    assert actual == member
print(json.dumps({'case_N':20, 'preparation_status':seal['status'],
                  'candidate_judge_attempts_N':0, 'seal':binding(OUT/'preparation-seal.json')},ensure_ascii=False))
