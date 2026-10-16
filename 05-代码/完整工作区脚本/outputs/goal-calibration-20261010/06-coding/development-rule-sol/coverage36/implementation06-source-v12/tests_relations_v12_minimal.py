"""Only the ten predeclared source relation controls, no actual fixture judge."""
import unittest
from relations import RelationView, canonical, digest
A, B = 'a' * 64, 'b' * 64

def c(cid, text, sha=A, kind='source_resource_text', headings=None):
    return {'context_id': cid, 'kind': kind, 'text': text, 'source_ref':
        {'sha256': sha, 'source_resource_id': 'DOC', 'locator': {'paragraph': cid}},
        'structure': {'source_resource_id': cid, 'heading_path': headings or []}}

def base(text, missing=False, printed=True, sha=A, target=A, edition=True):
    cs = [c('P', '同时满足以下条件的药品，可以简易续约。', target, headings=['规则二简易续约', '一、条件']),
          c('M1', '1.独家药品。', target), c('M2', '2.药品费用不得超过费用预算；市场价格变化除外。', target),
          c('SUB', '（1）调整支付范围的预算；不调整的除外。', target)]
    if missing: cs.pop(2)
    doc = {'source_resource_id': 'DOC', 'source_sha256': target, 'document_title': '2025年谈判药品续约规则',
        'document_year': 2025, 'source_texts': [{'source_resource_id': x['context_id'], 'text': x['text']} for x in cs],
        'source_geometry': {'group': {'parent_resource_id': 'P', 'numbered_members': ['M1', 'M2'],
          'member2_submembers': ['SUB'], 'operator': 'all', 'operator_printed': '同时满足以下条件' if printed else ''}}}
    ref = {'source_field': 'text', 'source_field_text_sha256': digest(text), 'literal_reference': '简易续约',
        'resource_id': 'DOC', 'reference_source_sha256': sha, 'target_source_sha256': target,
        'binding_scope': 'same_edition_document_reference' if edition else 'candidate_only',
        'target_title_and_year': doc['document_title'] if edition else ''}
    b = {'source_record': {'contexts': []}, 'explicit_or_primary_source_resources': [doc],
        'preserved_historical_neutral_source_supplements': [], 'source_full_text_resources': [], 'source_reference_index': [ref]}
    origins = {x['context_id']: {'source_resource_id': x['context_id'], 'source_bundle_pointer':
        '/explicit_or_primary_source_resources/0/source_texts/' + str(i), 'origin_inventory_resource_id': 'DOC',
        'origin_inventory_view': 'document_bundle', 'origin_inventory_view_sha256': digest(canonical(doc))} for i, x in enumerate(cs)}
    return {'text': text, 'contexts': cs, 'source_ref': {'sha256': sha}, 'source_bundle': b, 'derived_context_origins': origins}

def historical(text, fragment, kind='2024试点工作方案正文', title='优化创新药临床试验审评审批试点工作方案'):
    obj = {'text': fragment, 'source_title': title, 'source_sha256': B, 'document_date': '2024-07-31',
        'document_number': '正式发布号', 'source_document_kind': kind, 'original_url': 'https://example.test/official'}
    b = {'source_record': {'contexts': []}, 'explicit_or_primary_source_resources': [],
        'preserved_historical_neutral_source_supplements': [obj], 'source_full_text_resources': [], 'source_reference_index': []}
    return {'text': text, 'contexts': [c('H', fragment, B, 'historical_source_fragment')], 'source_ref': {'sha256': A},
        'source_bundle': b, 'derived_context_origins': {'H': {'source_resource_id': 'SUP', 'source_bundle_pointer':
        '/preserved_historical_neutral_source_supplements/0', 'origin_inventory_resource_id':
        'HISTORICALSOURCE-' + digest(canonical(obj))[:20], 'origin_inventory_view': 'text'}}}

class MinimalRelations(unittest.TestCase):
    def test_complete_named_conditions(self):
        v = RelationView(base('符合简易续约条件的药品，可以纳入目录。'))
        r = v.linked('cited_standard')[0]
        self.assertEqual(r['details']['group_operator'], 'all')
        self.assertIn('市场价格变化除外', r['details']['content']); self.assertIn('不调整的除外', r['details']['content'])
        self.assertEqual(len(r['context_evidence']), 4); self.assertTrue(r['used_source_views']); self.assertTrue(v.source_view_events)
    def test_missing_required_member(self):
        v = RelationView(base('符合简易续约条件的药品，可以纳入目录。', missing=True))
        self.assertFalse(v.linked('cited_standard')); self.assertTrue(v.material_requests)
        self.assertEqual(v.source_requests[0]['affected_dimensions'], ['S', 'E', 'Ec', 'I', 'F'])
    def test_unprinted_operator(self):
        v = RelationView(base('符合简易续约条件的药品，可以纳入目录。', printed=False))
        self.assertFalse(v.linked('cited_standard')); self.assertEqual(v.source_requests[0]['stop_reason'], 'source_operator_not_visible')
    def test_current_member_scope(self):
        v = RelationView(base('1.独家药品。'))
        self.assertEqual(len(v.linked('parent_predicate')), 1); self.assertFalse(v.linked('cited_standard'))
        self.assertNotIn('费用预算', v.linked('parent_predicate')[0]['details']['content'])
        self.assertFalse(v.linked('source_group_scope')[0]['details']['dimension_inheritance'])
    def test_bare_applicability(self):
        v = RelationView(base('本文件适用于简易续约材料归档。'))
        self.assertFalse(v.linked('cited_standard')); self.assertFalse(v.source_requests)
    def test_example_role(self):
        u = base('符合简易续约条件的药品，可以纳入目录。')
        u['contexts'][1]['structure']['source_role'] = 'right_side_example'
        v = RelationView(u); self.assertFalse(v.linked('cited_standard')); self.assertTrue(v.source_requests)
        self.assertNotIn('M1', [e['context_id'] for r in v.traces() for e in r['context_evidence']])
    def test_neutral_historical_mechanism(self):
        v = RelationView(historical('2024年组织开展优化创新药临床试验审评审批试点工作方案。',
            '本方案适用于1类创新药，疫苗除外。审评时限缩短至30个工作日。'))
        self.assertEqual(len(v.linked('named_mechanism')), 1)
        self.assertIn('疫苗除外', v.linked('named_mechanism')[0]['details']['object_definition'])
        self.assertTrue(v.linked('named_mechanism')[0]['used_source_views'])
    def test_historical_version_mismatch(self):
        v = RelationView(historical('2025年组织开展优化创新药临床试验审评审批试点工作方案。',
            '本方案适用于1类创新药。审评时限缩短至30个工作日。'))
        self.assertFalse(v.linked('named_mechanism')); self.assertTrue(v.material_requests)
    def test_neutral_official_explainer(self):
        u = historical('建立县域中心药房，完善药品供应。', '县域中心药房药品可及性差，供药不稳定。鼓励建设县域中心药房，保障药品供给。',
            kind='同政策官方政策解读', title='基层药品管理意见政策解读')
        u['source_bundle']['preserved_historical_neutral_source_supplements'][0].update(
            policy_document_date='2024-11-14', policy_document_number='同政策正式号')
        v = RelationView(u); self.assertEqual(len(v.linked('policy_explanation')), 1)
        self.assertIn('不稳定', v.linked('policy_explanation')[0]['details']['problem_text'])
    def test_same_edition_reference(self):
        text = '符合简易续约条件的药品，可以纳入目录。'
        self.assertTrue(RelationView(base(text, sha=A, target=B)).linked('cited_standard'))
        v = RelationView(base(text, sha=A, target=B, edition=False))
        self.assertFalse(v.linked('cited_standard')); self.assertEqual(v.source_requests[0]['stop_reason'], 'reference_edition_ambiguous')

if __name__ == '__main__': unittest.main(verbosity=2)
