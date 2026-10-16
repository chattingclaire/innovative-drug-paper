"""Predeclared synthetic finite-relation contrasts; no actual fixture runs."""
import copy
import unittest

from relations import RelationView


SHA = 'a' * 64
OTHER_SHA = 'b' * 64


def ctx(cid, kind, text=None, structure=None, source=SHA):
    result = {'context_id': cid, 'kind': kind, 'structure': structure or {},
              'source_ref': {'sha256': source, 'locator': copy.deepcopy(structure or {})}}
    if text is not None:
        result['text'] = text
    return result


def by_id(unit, cid):
    return next(c for c in unit['contexts'] if c['context_id'] == cid)


def article_unit():
    current = '原研药品登记行 | 符合第四条第二款情形的，数据保护期为2年。'
    contexts = [ctx('CTX-current', 'paragraph', current)]
    contexts += [ctx('CTX-root', 'cited_reference_group', structure={
        'child_groups': [{'position': 'references', 'ordered_context_ids': ['CTX-cite4', 'CTX-cite9']}]})]
    for cid, ids in [('CTX-cite4', ['CTX-c4p1', 'CTX-c4p2']),
                     ('CTX-cite9', ['CTX-c9p1', 'CTX-c9p2', 'CTX-c9p3', 'CTX-c9p4'])]:
        contexts.append(ctx(cid, 'cited_reference', structure={
            'parent_context_id': 'CTX-root',
            'child_groups': [{'position': 'contexts', 'ordered_context_ids': ids}]}))
    texts = {
        'CTX-c4p1': '第四条 境内未上市的原研药品首次提交新适应症注册申请，并按本办法第十二条第三款提交证明药品安全性和有效性的全部试验数据，对全部数据给予5年数据保护期。',
        'CTX-c4p2': '该药品后续增加适应症的，按照本办法第九条执行，对相应保护范围数据给予2年数据保护期。',
        'CTX-c9p1': '第九条 自改良型药品首次上市许可之日起，给予2年数据保护期。',
        'CTX-c9p2': '境外已经上市的改良型药品，给予2年数据保护期。',
        'CTX-c9p3': '本条款中药品的数据保护范围包括证明与已知活性成份药品相比具有明显临床优势的新的临床试验数据，但不包括生物等效性数据。',
        'CTX-c9p4': '在数据保护期内，其他申请人未经持有人同意依赖受保护数据提交的上市申请不予许可；自行取得且未依赖他人数据的除外。',
    }
    for cid, text in texts.items():
        parent = 'CTX-cite4' if cid.startswith('CTX-c4') else 'CTX-cite9'
        contexts.append(ctx(cid, 'ordered_members', text, {'parent_context_id': parent}))
    contexts.append(ctx('CTX-unlinked', 'source_paragraph', '其他仿制药具有新的作用机制，应给予专门支持。'))
    return {'text': current, 'pages': [], 'contexts': contexts, 'attachments': [], 'source_image_attachments': []}


def support_unit(current=None):
    current = current or '对于拟申请附条件批准的改良型药品，可以在探索性临床试验结束前适用本工作规范。'
    ids = ['CTX-scope-heading', 'CTX-scope', 'CTX-stage', 'CTX-current-copy', 'CTX-support']
    contexts = [ctx('CTX-current', 'paragraph', current),
        ctx('CTX-component', 'source_paragraph', structure={'first_paragraph': 'p0100', 'last_paragraph': 'p0104'}),
        ctx('CTX-scope-heading', 'source_paragraph', '一、适用范围及办理支持'),
        ctx('CTX-scope', 'source_paragraph', '适用范围：创新药及改良型药品的研发，特别审批品种除外。'),
        ctx('CTX-stage', 'source_paragraph', '适用条件及研发阶段：探索性临床试验完成后至上市前，按照本工作规范获得沟通交流及审评支持。'),
        ctx('CTX-current-copy', 'source_paragraph', current),
        ctx('CTX-support', 'source_paragraph', '时限要求：沟通交流时限为23日，品种审评时限同优先审评时限为93日，按照单独序列管理。'),
        ctx('CTX-boundary', 'following_heading', '二、其他事项', {
            'component_first_paragraph': 'p0100', 'component_last_paragraph': 'p0104',
            'scope_context_ids': ids, 'follows_context_id': ids[-1]}),
        ctx('CTX-other-section', 'source_paragraph', '所有项目必须提供完整安全性和有效性评价资料。')]
    return {'text': current, 'pages': [], 'contexts': contexts, 'attachments': [], 'source_image_attachments': []}


def reference_relations(view):
    return [r for r in view.linked('cited_standard')
            if r['details'].get('relation_subtype') == 'finite_operational_article_reference']


def support_relations(view):
    return [r for r in view.linked('named_mechanism')
            if r['details'].get('relation_subtype') == 'bounded_rule_preapplication_authorization']


class FiniteArticleReferenceTests(unittest.TestCase):
    def test_nested_reference_uses_only_target_antecedent_scope_permission(self):
        rel = reference_relations(RelationView(article_unit()))[0]
        self.assertEqual(rel['details']['reference_chain'][0]['article'], 4)
        self.assertEqual(rel['details']['reference_chain'][1]['article'], 9)
        self.assertEqual(set(rel['details']['context_ids']), {'CTX-c4p1', 'CTX-c4p2', 'CTX-c9p3', 'CTX-c9p4'})
        self.assertIn('但不包括生物等效性', rel['details']['standard_text'])
        self.assertIn('自行取得且未依赖', rel['details']['standard_text'])

    def test_arabic_article_numbers_use_same_general_relation(self):
        unit = article_unit()
        unit['text'] = unit['text'].replace('第四条第二款', '第14条第2款')
        by_id(unit, 'CTX-current')['text'] = unit['text']
        by_id(unit, 'CTX-c4p1')['text'] = by_id(unit, 'CTX-c4p1')['text'].replace('第四条', '第14条')
        rel = reference_relations(RelationView(unit))[0]
        self.assertEqual(rel['details']['reference_chain'][0]['article'], 14)

    def test_no_independent_improved_drug_grants_or_unlinked_sibling(self):
        rel = reference_relations(RelationView(article_unit()))[0]
        self.assertNotIn('CTX-c9p1', rel['details']['context_ids'])
        self.assertNotIn('CTX-c9p2', rel['details']['context_ids'])
        self.assertNotIn('CTX-unlinked', rel['details']['context_ids'])

    def test_local_drug_antecedent_missing_requests_material(self):
        unit = article_unit()
        by_id(unit, 'CTX-c4p1')['text'] = '第四条 申请材料应签字盖章。'
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(any('药品指代' in r['missing'] for r in view.material_requests))

    def test_navigation_reference_does_not_expand(self):
        unit = article_unit()
        unit['text'] = '原研药品的数据保护文件详见第四条第二款。'
        by_id(unit, 'CTX-current')['text'] = unit['text']
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_reported_identity_does_not_expand(self):
        unit = article_unit()
        unit['text'] = '该原研药品已符合第四条第二款条件并列入材料名单。'
        by_id(unit, 'CTX-current')['text'] = unit['text']
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_foreign_source_target_rejected(self):
        unit = article_unit()
        by_id(unit, 'CTX-c4p2')['source_ref']['sha256'] = OTHER_SHA
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(view.material_requests)

    def test_known_component_conflict_rejected(self):
        unit = article_unit()
        by_id(unit, 'CTX-current')['structure']['component_id'] = 'current-component'
        by_id(unit, 'CTX-cite4')['structure']['component_id'] = 'other-component'
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_missing_exact_clause_requests_material(self):
        unit = article_unit()
        unit['text'] = unit['text'].replace('第二款', '第五款')
        by_id(unit, 'CTX-current')['text'] = unit['text']
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(any('款次' in r['missing'] for r in view.material_requests))

    def test_secondary_scope_and_permission_both_required(self):
        for cid in ('CTX-c9p3', 'CTX-c9p4'):
            with self.subTest(cid=cid):
                unit = article_unit()
                by_id(unit, cid)['text'] = '本条的材料接收渠道为电子系统。'
                view = RelationView(unit)
                self.assertFalse(reference_relations(view))
                self.assertTrue(any('数据范围' in r['missing'] for r in view.material_requests))

    def test_next_article_not_copied(self):
        unit = article_unit()
        cite = by_id(unit, 'CTX-cite9')
        cite['structure']['child_groups'][0]['ordered_context_ids'].append('CTX-next-article')
        unit['contexts'].append(ctx('CTX-next-article', 'ordered_members',
            '第十条 其他创新药必须验证治疗优势，并提供专门团队。', {'parent_context_id': 'CTX-cite9'}))
        rel = reference_relations(RelationView(unit))[0]
        self.assertNotIn('CTX-next-article', rel['details']['context_ids'])

    def test_general_further_reference_is_not_recursive(self):
        unit = article_unit()
        by_id(unit, 'CTX-c4p2')['text'] = '该药品后续增加适应症的，详见本办法第九条，对相应保护范围数据给予2年数据保护期。'
        rel = reference_relations(RelationView(unit))[0]
        self.assertEqual(len(rel['details']['reference_chain']), 1)
        self.assertEqual(set(rel['details']['context_ids']), {'CTX-c4p1', 'CTX-c4p2'})

    def test_no_antecedent_internal_or_third_hop_reference_expansion(self):
        unit = article_unit()
        by_id(unit, 'CTX-c9p3')['text'] += '按照第十五条核验其他材料。'
        rel = reference_relations(RelationView(unit))[0]
        self.assertEqual(len(rel['details']['reference_chain']), 2)
        unexpanded = [x['reference'] for x in rel['details']['unexpanded_references']]
        self.assertIn('第十二条第三款', unexpanded)
        self.assertIn('第十五条', unexpanded)

    def test_exact_current_and_context_offsets(self):
        unit = article_unit()
        rel = reference_relations(RelationView(unit))[0]
        self.assertEqual(rel['current_anchor']['text'], unit['text'])
        for key in ('current_condition_anchor', 'current_consequence_anchor'):
            a = rel['details'][key]
            self.assertEqual(unit['text'][a['start']:a['end']], a['text'])
        for a in rel['context_evidence']:
            self.assertEqual(by_id(unit, a['context_id'])['text'][a['start']:a['end']], a['text'])

    def test_other_current_branch_consequence_not_borrowed(self):
        unit = article_unit()
        unit['text'] = '原研药品符合第四条第二款的，应填写栏目；另一药品的数据保护期为3年。'
        by_id(unit, 'CTX-current')['text'] = unit['text']
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_other_drug_subject_consequence_not_borrowed(self):
        unit = article_unit()
        unit['text'] = '原研药品符合第四条第二款的，应填写栏目，另一药品的数据保护期为3年。'
        by_id(unit, 'CTX-current')['text'] = unit['text']
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_secondary_scope_merely_refers_to_third_article_requests_material(self):
        unit = article_unit()
        by_id(unit, 'CTX-c9p3')['text'] = '本条款药品的数据保护范围按照第十五条执行。'
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(view.material_requests)

    def test_secondary_permission_field_format_is_not_rights_consequence(self):
        unit = article_unit()
        by_id(unit, 'CTX-c9p4')['text'] = '在数据保护期内，上市许可字段应按统一格式填写。'
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(view.material_requests)

    def test_current_protection_period_form_requirement_not_consequence(self):
        unit = article_unit()
        unit['text'] = '符合第四条第二款情形的，数据保护期为必填字段。'
        by_id(unit, 'CTX-current')['text'] = unit['text']
        self.assertFalse(reference_relations(RelationView(unit)))

    def test_secondary_exact_clause_does_not_borrow_unaddressed_scope(self):
        unit = article_unit()
        by_id(unit, 'CTX-c4p2')['text'] = by_id(unit, 'CTX-c4p2')['text'].replace('第九条执行', '第九条第一款执行')
        view = RelationView(unit)
        self.assertFalse(reference_relations(view))
        self.assertTrue(view.material_requests)


class BoundedApplicableSupportTests(unittest.TestCase):
    def test_current_early_authorization_uses_closed_component_support(self):
        rel = support_relations(RelationView(support_unit()))[0]
        self.assertIn('23日', rel['details']['direct_mechanism'])
        self.assertIn('特别审批品种除外', rel['details']['object_definition'])
        self.assertEqual(set(rel['details']['context_ids']), {'CTX-scope', 'CTX-stage', 'CTX-support'})

    def test_current_restriction_preserves_negation(self):
        unit = support_unit('对于拟申请附条件批准的创新药，不得在探索性临床试验完成前适用本工作规范。')
        rel = support_relations(RelationView(unit))[0]
        self.assertIn('不得', rel['details']['current_authorization_anchor']['text'])
        self.assertEqual(rel['current_anchor']['text'], unit['text'])

    def test_group_identity_or_arrangement_name_alone_not_support(self):
        for text in ('罕见病药品列入本工作规范对象名单。',
                     '创新药的本工作规范名称应当填写完整。',
                     '拟申请的创新药已有本工作规范适用身份。'):
            with self.subTest(text=text):
                self.assertFalse(support_relations(RelationView(support_unit(text))))

    def test_foreign_source_support_rejected(self):
        unit = support_unit()
        by_id(unit, 'CTX-support')['source_ref']['sha256'] = OTHER_SHA
        self.assertFalse(support_relations(RelationView(unit)))

    def test_unclosed_or_wrong_component_support_rejected(self):
        for field in ('component_last_paragraph', 'follows_context_id'):
            with self.subTest(field=field):
                unit = support_unit()
                by_id(unit, 'CTX-boundary')['structure'][field] = 'wrong-boundary'
                self.assertFalse(support_relations(RelationView(unit)))
        unit = support_unit()
        by_id(unit, 'CTX-current')['structure']['component_id'] = 'current-component'
        by_id(unit, 'CTX-support')['structure']['component_id'] = 'different-component'
        self.assertFalse(support_relations(RelationView(unit)))

    def test_complete_closed_body_no_qualifying_content_no_speculative_request(self):
        for cid in ('CTX-scope', 'CTX-stage', 'CTX-support'):
            with self.subTest(cid=cid):
                unit = support_unit()
                by_id(unit, cid)['text'] = '本工作规范仅说明一般归档要求。'
                view = RelationView(unit)
                self.assertFalse(support_relations(view))
                self.assertFalse(view.material_requests)

    def test_communication_form_and_trial_obligations_not_actual_support(self):
        unit = support_unit()
        by_id(unit, 'CTX-support')['text'] = '沟通交流采取电话或视频形式，申请人应当提供完整试验安全性和有效性资料。'
        self.assertFalse(support_relations(RelationView(unit)))

    def test_following_section_support_not_borrowed(self):
        unit = support_unit()
        by_id(unit, 'CTX-support')['text'] = '本规范中的材料格式应规范。'
        by_id(unit, 'CTX-other-section')['text'] = '沟通交流时限为23日，审评时限为93日。'
        self.assertFalse(support_relations(RelationView(unit)))

    def test_parallel_safety_effect_obligations_not_copied(self):
        rel = support_relations(RelationView(support_unit()))[0]
        self.assertNotIn('CTX-other-section', rel['details']['context_ids'])
        self.assertNotIn('安全性和有效性评价资料', rel['details']['content'])

    def test_current_copy_missing_from_closed_component_rejected(self):
        unit = support_unit()
        by_id(unit, 'CTX-current-copy')['text'] = '另一种药品申请的独立说明。'
        self.assertFalse(support_relations(RelationView(unit)))

    def test_exact_current_authorization_and_quote_offsets(self):
        unit = support_unit()
        rel = support_relations(RelationView(unit))[0]
        self.assertEqual(rel['current_anchor']['text'], unit['text'])
        a = rel['details']['current_authorization_anchor']
        self.assertEqual(unit['text'][a['start']:a['end']], a['text'])
        for a in rel['context_evidence']:
            self.assertEqual(by_id(unit, a['context_id'])['text'][a['start']:a['end']], a['text'])

    def test_local_this_that_rule_anaphor_with_closed_component(self):
        unit = support_unit('对于拟申请附条件批准的创新药，可以在探索性临床试验完成前适用该工作规范。')
        self.assertTrue(support_relations(RelationView(unit)))

    def test_bare_rule_noun_explicit_scope_grant_and_restriction(self):
        from dimensions import judge
        for action in ('可以', '不得'):
            with self.subTest(action=action):
                unit = support_unit('对于拟申请附条件批准的创新药，' + action + '在探索性临床试验结束前适用本规范。')
                by_id(unit, 'CTX-scope')['text'] = '本规范适用于创新药研发，上市后常规服务除外。'
                by_id(unit, 'CTX-stage')['text'] = '一般在探索性临床试验完成后至批准上市前适用本规范。'
                by_id(unit, 'CTX-support')['text'] = '本规范为研发项目提供研究方案反馈，实行单独序列优先审评并缩短办理时限。'
                view = RelationView(unit)
                self.assertTrue(support_relations(view))
                self.assertEqual({dim: result['value'] for dim, result in judge(view).items()},
                                 {'S': 0, 'E': 0, 'Ec': 0, 'I': 1, 'F': 0})

    def test_closed_bare_rule_body_form_only_has_no_speculative_unknown(self):
        from dimensions import judge
        unit = support_unit('对于拟申请附条件批准的创新药，可以在探索性临床试验结束前适用本规范。')
        by_id(unit, 'CTX-scope')['text'] = '本规范适用于创新药研发。'
        by_id(unit, 'CTX-stage')['text'] = '一般在探索性临床试验完成后至批准上市前适用本规范。'
        by_id(unit, 'CTX-support')['text'] = '本规范仅规定签字盖章和电话提交形式，不设置研究反馈或优先审评机会。'
        view = RelationView(unit)
        self.assertFalse(support_relations(view))
        self.assertFalse(view.material_requests)
        self.assertEqual(judge(view)['I']['value'], 0)

    def test_closed_component_listed_source_text_missing_requests_material(self):
        unit = support_unit()
        by_id(unit, 'CTX-support').pop('text')
        view = RelationView(unit)
        self.assertFalse(support_relations(view))
        self.assertTrue(any(r['path'] == 'named_mechanism' for r in view.material_requests))

    def test_same_source_known_other_component_service_not_borrowed(self):
        unit = support_unit()
        by_id(unit, 'CTX-current-copy')['structure']['component_id'] = 'bound-component'
        by_id(unit, 'CTX-support')['structure']['component_id'] = 'other-component'
        view = RelationView(unit)
        self.assertFalse(support_relations(view))
        self.assertTrue(view.material_requests)

    def test_broken_scope_id_or_empty_source_text_requests_material(self):
        for problem in ('empty-source-text', 'missing-scope-context'):
            with self.subTest(problem=problem):
                unit = support_unit()
                if problem == 'empty-source-text':
                    by_id(unit, 'CTX-support')['text'] = ''
                else:
                    by_id(unit, 'CTX-boundary')['structure']['scope_context_ids'][1] = 'CTX-missing'
                view = RelationView(unit)
                self.assertFalse(support_relations(view))
                self.assertTrue(any(r['path'] == 'named_mechanism' for r in view.material_requests))


class SyntheticDimensionInterfaceTests(unittest.TestCase):
    def test_finite_condition_to_substantive_data_scope_dimensions(self):
        from dimensions import judge
        decisions = judge(RelationView(article_unit()))
        self.assertEqual({dim: result['value'] for dim, result in decisions.items()},
                         {'S': 1, 'E': 1, 'Ec': 0, 'I': 1, 'F': 0})

    def test_support_to_i3_without_parallel_obligations_or_group_f(self):
        from dimensions import judge
        unit = support_unit()
        by_id(unit, 'CTX-scope')['text'] = '适用范围：用于治疗罕见病的创新药及改良型药品的研发，特别审批品种除外。'
        decisions = judge(RelationView(unit))
        self.assertEqual({dim: result['value'] for dim, result in decisions.items()},
                         {'S': 0, 'E': 0, 'Ec': 0, 'I': 1, 'F': 0})

    def test_reordered_protected_data_scope_and_period_permission(self):
        from dimensions import judge
        unit = article_unit()
        by_id(unit, 'CTX-c4p2')['text'] = '该药品后续新增适应症，按照本办法第九条的保护数据范围和许可要求执行。'
        by_id(unit, 'CTX-c9p3')['text'] = '改良型新药受保护的数据包括证明其与既有药品相比具有明显临床优势的新的临床试验数据，药代动力学数据除外。'
        by_id(unit, 'CTX-c9p4')['text'] = '保护期间，其他申请人未经持有人同意，不得依赖受保护数据申请上市许可；独立取得的数据不受此限。'
        view = RelationView(unit)
        rel = reference_relations(view)[0]
        self.assertEqual(len(rel['details']['reference_chain']), 2)
        self.assertIn('药代动力学数据除外', rel['details']['qualification_text'])
        self.assertIn('独立取得的数据不受此限', rel['details']['standard_text'])
        self.assertEqual({dim: result['value'] for dim, result in judge(view).items()},
                         {'S': 1, 'E': 1, 'Ec': 0, 'I': 1, 'F': 0})


if __name__ == '__main__':
    unittest.main(verbosity=2)
