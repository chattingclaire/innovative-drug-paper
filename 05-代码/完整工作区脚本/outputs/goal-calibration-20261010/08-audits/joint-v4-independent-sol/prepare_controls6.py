#!/usr/bin/env python3
"""Prepare six independent neutral-number/source-scope controls; no candidate import."""
from __future__ import annotations
import copy
import datetime
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
MANUAL=ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'
SOURCE_CONTRACT=ROOT/'08-audits/five-dimension-joint-v3-independent-sol/execution-joint-v3-interface-sol/attempt02/code-snapshot/source_packet.py'
DIMENSIONS=('S','E','Ec','I','F')
MANUAL_SHA='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
DOCUMENTS=OUT/'synthetic-source-documents'
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
                             'source_version_id': 'SYNTHETIC-HIDDEN-NUMBER-SCOPE-2026-V1',
                             'synthetic_control_not_policy_original': True}}

    def context(self, i, cid, kind='source_paragraph', **structure):
        loc = self.locators[i]
        return {'context_id': cid, 'kind': kind, 'text': self.paragraphs[i],
                'source_document': 'SOURCE-' + self.sha, 'source_ref': self.ref(i),
                'structure': {'paragraph_id': loc['paragraph_id'],
                              'source_paragraph_id': loc['source_paragraph_id'],
                              'sequence_index': loc['sequence_index'],
                              'component_id': loc['component_id'],
                              'source_version_id': 'SYNTHETIC-HIDDEN-NUMBER-SCOPE-2026-V1', **structure}}

    def geometry(self, cid, kind, **structure):
        return {'context_id': cid, 'kind': kind, 'text': '',
                'source_document': 'SOURCE-' + self.sha,
                'source_ref': {'sha256': self.sha, 'source_resource_id': 'SOURCE-' + self.sha,
                               'locator': {'kind': 'synthetic_bound_geometry',
                                           'component_id': structure.get('component_id', 'JOINT-COMPONENT'),
                                           'source_utf8_absolute_path': str(self.path)}},
                'structure': {'component_id': 'JOINT-COMPONENT',
                              'source_version_id': 'SYNTHETIC-HIDDEN-NUMBER-SCOPE-2026-V1', **structure}}

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
                              'source_version_id': 'SYNTHETIC-HIDDEN-NUMBER-SCOPE-2026-V1',
                              'document_title': self.title, 'document_year': 2026,
                              'locator': {'kind': 'synthetic_complete_UTF8_snapshot',
                                          'unicode_code_point_interval_half_open': [0, len(self.raw)],
                                          'utf8_byte_interval_half_open': [0, len(self.raw.encode('utf-8'))],
                                          'physical_line_interval_inclusive': [1, self.raw.count('\n')],
                                          'source_utf8_absolute_path': str(self.path)}})
        result = {'common_source_bundle_version': {'status': 'synthetic_source_only_hidden_number_scope_control'},
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


cases=[]
def add(name,pair,want,reason,lines,group):
    packet,doc=pair
    assert set(want)==set(DIMENSIONS)
    cases.append({'name':name,'pair_group':group,'synthetic_bundle':packet,'synthetic_documents':[doc],
                  'expected_values_fixed_before_execution':want,'manual_reason':reason,'manual_lines':lines,
                  'actual_classification_executed':False,'synthetic_development_control_not_human_reference':True,
                  'interface_assertions_fixed_before_execution':[
                      '结构编号只帮助定位，不能凭元数据覆盖实质原文头或移动来源几何',
                      '完整范围与当前确指须独立核对，不能从兄弟成员捐献标签',
                      '不注入关系、only_IF flag、typed消费者、路径或resolvedreceipt'],
                  'not_a_formal_accuracy_or_reliability_observation':True})

# A: identical complete legal source and current proposition; neutral representation alone changes.
doc=Document([
    '药品咨询资格复核规范',
    '第三十一条 维持药品咨询资格，须核验该药给药后过敏反应风险证据。',
    '第三十二条 申请书字体按统一格式设置。',
    '本药须符合本规范第三十一条的实质条件，方可维持咨询资格。',
    '第二章 文书归档',
], '中性编号表示与同一原文要求（合成）')
for name,number in [('article_number_integer_same_original',31),('article_number_chinese_literal_same_original','第三十一条')]:
    cs=closed_group(doc,[1], 'A-ARTICLE31',article=number)
    add(name,doc.packet(3,cs),expected(S=1),
        '当前直接以同版第三十一条实质条件维持资格，原文只要求核验药物过敏风险；整数或中文条号只是中性表示，不改变S议题或复制其他维度。',
        [7,9,13,15,22,23,39,40,41,44,50,84,86], 'A')

# B: wrong structure number cannot convert an actual different original article into the current standard.
doc=Document([
    '药品咨询资格复核补充规范',
    '第三十二条 维持药品咨询资格，须核验药品的用药风险证据。',
    '第三十三条 附件按日期编号。',
    '本药须符合本规范第三十一条的实质条件，方可维持咨询资格。',
    '本药须符合本规范第三十二条的实质条件，方可维持咨询资格。',
    '第二章 文件格式',
], '原文头与中性编号冲突及确指范围（合成）')
wrong=closed_group(doc,[1], 'B-WRONG-NUMBER',article=31)
correct=closed_group(doc,[1], 'B-CORRECT-NUMBER',article='第三十二条')
add('structure31_original_head32_current31_unresolved',doc.packet(3,wrong),expected(None,None,None,None,None),
    '当前确指31条，但实际唯一连续头为32条；结构字段误写31不能把该兄弟原文当31条标准。已供完整资源没有可唯一核明的31条实质原文，保留确指缺材NULL，不能凭错误编号填S=1或凭未见内容填0。',
    [9,22,23,25,39,40,41,44,50], 'B')
add('original_head32_structure32_current32_resolved',doc.packet(4,correct),expected(S=1),
    '同一实际来源改为当前确指32条，结构号与原文头一致且范围闭合，当前使用该用药风险条件，S成立；不存在由元数据创建原文的步骤。',
    [7,9,13,22,23,39,40,41,50,84,86], 'B')

# C: exact clause, complete article vs omitted middle clause, no brother substitution.
doc=Document([
    '第四十一条 药品咨询资格证据分款规定如下：',
    '第一款 申请药品须核验其给药后过敏反应风险证据。',
    '第二款 申请药品须证明其降低疾病复发率的疗效。',
    '第三款 申请药品须核验治疗费用是否合理。',
    '第四十二条 附件依收件日期归档。',
    '本药须满足本规范第四十一条第二款的实质条件。',
], '确指款与中段缺失的完整范围控制（合成）')
complete=closed_group(doc,list(range(4)), 'C-ARTICLE41',article=41)
for i,c in enumerate(complete[:4]):
    if i:c['structure']['clause']=i
add('exact_second_clause_complete_inventory',doc.packet(5,complete),expected(E=1),
    '当前只确指第41条第二款，条头、三个款次及真实下一条均完整可供，第二款是药物降低复发率效果条件；第一款风险与第三款费用不能复制，完整材料也不扩大当前确指范围。',
    [7,9,13,22,23,39,40,41,42,50,94,96], 'C')
missing=copy.deepcopy(complete)
missing=[c for c in missing if c['context_id']!='C-ARTICLE41-TEXT-2']
for c in missing:
    for child in c.get('structure',{}).get('child_groups',[]):
        child['ordered_context_ids']=[cid for cid in child['ordered_context_ids'] if cid!='C-ARTICLE41-TEXT-2']
add('exact_second_clause_missing_middle_inventory',doc.packet(5,missing,deliver_full=False,undelivered=(2,)),expected(None,None,None,None,None),
    '当前确指第二款，实际只交付条头与第一/三款及末界，关键中间第二款未供，也无完整snapshot；不能把外层first/last/next当中段已经齐全，不从兄弟风险或费用替代，当前没有独立维度阳性，五维保留未知。独立保存的第二款原件不成为候选资源。',
    [9,22,23,25,39,40,41,42,50], 'C')

assert len(cases)==6 and len({c['name'] for c in cases})==6
assert binding(MANUAL)['sha256']==MANUAL_SHA
manual_raw=MANUAL.read_text(encoding='utf-8');ml=manual_raw.splitlines(keepends=True)
quotes=[]
for number in sorted({n for c in cases for n in c['manual_lines']}):
    start=sum(map(len,ml[:number-1]));text=ml[number-1]
    assert manual_raw[start:start+len(text)]==text
    quotes.append({'line_1based':number,'unicode_span_half_open':[start,start+len(text)],'quote':text})
write('manual-basis-quotes.json',{'binding':binding(MANUAL),'quotes':quotes,'no_definition_change':True})
write('controls6-fixed-before-execution.json',{'status':'hidden_independent_neutral_number_scope_controls_prepared',
    'case_N':6,'paired_groups_N':3,'dimensions':list(DIMENSIONS),'manual_binding':binding(MANUAL),
    'candidate_algorithm_binding':None,'cases':cases,'no_formal_human_reference':True,
    'expected_changes_after_candidate_execution_allowed':False,
    'future_owner_or_ROOT_answer_tables_not_read':True})
checks=[]
for case in cases:
    packet=case['synthetic_bundle'];d=case['synthetic_documents'][0]
    raw=Path(d['binding']['path']).read_bytes();original=raw.decode('utf-8')
    assert digest(raw)==d['binding']['sha256']
    rows=[('current',packet['source_record']['text'],packet['source_record']['source_ref'])]
    rows += [('context:'+c['context_id'],c['text'],c['source_ref']) for c in packet['source_record']['contexts'] if c['text']]
    for role,text,ref in rows:
        loc=ref['locator'];a,b=loc['unicode_code_point_interval_half_open'];ba,bb=loc['utf8_byte_interval_half_open']
        assert ref['sha256']==d['binding']['sha256'] and original[a:b]==text and raw[ba:bb].decode('utf-8')==text
        assert original[:a].count('\n')+1==loc['physical_line_interval_inclusive'][0]
        checks.append({'case':case['name'],'role':role,'text':text,'source_ref':ref,'exact_literal_geometry_verified':True})
    if d['undelivered_paragraph_indexes_zero_based']:
        assert packet['source_full_text_resources']==[]
        assert not any(c['source_ref'].get('locator',{}).get('sequence_index') in d['undelivered_paragraph_indexes_zero_based'] for c in packet['source_record']['contexts'] if c['text'])
write('literal-geometry-preparation-check.json',{'status':'pass_no_algorithm_executed','cases_N':6,'checks':checks,
    'deliberate_neutral_number_original_head_conflict_not_erased':True,
    'missing_middle_not_hidden_by_complete_snapshot':True})
write('read-and-execution-boundary.json',{'manual':binding(MANUAL),'source_packet_contract':binding(SOURCE_CONTRACT),
    'geometry_helper':binding(ROOT/'08-audits/five-dimension-joint-independent-controls-sol/prepare_joint_controls.py'),
    'preparation_reads':['frozen manual lines','already sealed SourcePacket neutral structure shape','own original source-geometry helper'],
    'future_v4_code_or_owner_expected_read':False,'ROOT_expected_table_read':False,
    'main_LLM_partial_or_real_human_or_cohort_labels_read':False,
    'source_packet_or_RelationView_or_judge_calls_N':0,'no_relation_unit_receipt_or_consumer_flag_injection':True,
    'no_new_actual_policy_IDs':True,'expected_fixed_before_final_candidate_seal':True})
with (OUT/'README.txt').open('x',encoding='utf-8') as stream:
    stream.write('六项全新独立中性编号/原文范围控制，三组成对。完整原文、实际交付几何及预期先固定，暂不向ROOT或开发者公开病例与预期。\n'
                 '只用SourcePacket可供中性结构，无关系/路径/消费者/收据注入。未供中段保留为未供，不由已保存独立原件倒填。\n'
                 '候选最终封存后各一次并逐条即时JSONL保存；构造失败亦为实际失败，不用judge数断言阻止记录。原12不作为本轮独立控制。\n'
                 '本准备不导入或执行未来算法，不产生真人参照、policy新ID、整批预测或正式统计验证。\n')
write('preparation-readback.json',{'cases_N':6,'paired_groups_N':3,'synthetic_original_documents_N':len(list(DOCUMENTS.glob('*.txt'))),
    'manual_SHA_verified':True,'input_geometry_literal_checked':True,'candidate_judge_attempts_N':0,
    'expected_and_source_fixed':True,'candidate_binding':None})
members=[binding(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
seal={'status':'hidden6_prepared_await_final_v4_seal','prepared_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'case_N':6,'paired_groups_N':3,'candidate_judge_attempts_N':0,'candidate_algorithm_binding':None,
    'manual_binding':binding(MANUAL),'output_members':members,'seal_self_excluded':True,
    'case_and_expected_content_not_disclosed_before_final_candidate_seal':True,'ROOT_or_owner_files_modified':False}
write('preparation-seal.json',seal)
for member in members:assert binding(member['path'])==member
print(json.dumps({'case_N':6,'paired_groups_N':3,'candidate_judge_attempts_N':0,'preparation_seal':binding(OUT/'preparation-seal.json'),'members_N':len(members)},ensure_ascii=False))
