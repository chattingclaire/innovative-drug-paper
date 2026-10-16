"""Exactly two list-trigger controls: source requests/relations only, no judge."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import source_packet
from relations import RelationView

WORK = Path(__file__).resolve().parent


def abbreviation_source():
    scope = json.loads((WORK / 'source-scope-v12.json').read_text())
    entry = scope['complete_bundle_snapshot']
    data = Path(entry['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['sha256']: raise AssertionError('Source-only snapshot SHA mismatch')
    selected = [line for line in data.splitlines() if b'"id":"RECODE25-00652"' in line]
    if len(selected) != 1: raise AssertionError('Approved source-only selection not unique')
    bundle = json.loads(selected[0])
    if bundle['source_record']['id'] != 'RECODE25-00652': raise AssertionError('Source-only selected wrong row')
    return bundle


def complete_mixed_unit(intro):
    text = '研究试点（以下简称项目）申请应符合' + intro + '条件。'
    members = ['（一）仅在研究方案获得同意后参加试点。', '（二）不符合条件的品种不得参与。']
    source_ref = {'sha256': 'a' * 64, 'source_resource_id': 'SOURCE-' + 'a' * 64,
                  'locator': {'physical_pages': [1]}}
    def context(cid, kind, content='', structure=None):
        result = {'context_id': cid, 'kind': kind, 'source_document': 'D-synthetic',
                  'source_ref': copy.deepcopy(source_ref), 'structure': structure or {}}
        if content: result['text'] = content
        return result
    contexts = [context('CTX-CURRENT', 'paragraph', text),
                context('CTX-M1', 'ordered_members', members[0], {'parent_context_id': 'CTX-CURRENT', 'sequence_index': 1}),
                context('CTX-M2', 'ordered_members', members[1], {'parent_context_id': 'CTX-CURRENT', 'sequence_index': 2}),
                context('CTX-END', 'boundary'),
                context('CTX-LIST', 'ordered_list', structure={'child_groups': [
                    {'position': 'contexts', 'ordered_context_ids': ['CTX-CURRENT', 'CTX-M1', 'CTX-M2', 'CTX-END']}]} )]
    return {'text': text, 'pages': [1], 'source_ref': source_ref, 'contexts': contexts}, members


class NecessaryListControls(unittest.TestCase):
    def test_abbreviation_only_has_no_substantive_list_request(self):
        bundle = abbreviation_source()
        original = copy.deepcopy(bundle)
        self.assertEqual(bundle['source_record']['text'].count('以下'), 1)
        self.assertEqual(bundle['source_record']['text'].count('以下简称'), 1)
        view = RelationView(source_packet.semantic_unit(bundle))
        self.assertFalse(view.linked('substantive_list'))
        self.assertFalse([r for r in view.material_requests if r.get('path') == 'substantive_list'])
        self.assertFalse([r for r in view.source_requests if r.get('path') == 'substantive_list'])
        self.assertEqual(bundle, original)

    def test_abbreviation_and_real_intro_reads_complete_qualified_list(self):
        for intro in ('以下', '下列'):
            unit, members = complete_mixed_unit(intro)
            original = copy.deepcopy(unit)
            view = RelationView(unit)
            relations = view.linked('substantive_list')
            with self.subTest(intro=intro):
                self.assertEqual(len(relations), 1)
                relation = relations[0]
                self.assertEqual(relation['details']['member_texts'], members)
                self.assertEqual([e['text'] for e in relation['context_evidence']], members)
                self.assertEqual(relation['details']['shared_predicate'], unit['text'])
                self.assertTrue(relation['details']['full_scope'])
                self.assertFalse([r for r in view.material_requests if r.get('path') == 'substantive_list'])
                self.assertFalse([r for r in view.source_requests if r.get('path') == 'substantive_list'])
                self.assertEqual(unit, original)


if __name__ == '__main__': unittest.main(verbosity=2)
