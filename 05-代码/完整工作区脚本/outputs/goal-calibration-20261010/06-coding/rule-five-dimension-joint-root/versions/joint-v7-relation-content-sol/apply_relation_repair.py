from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'relations.py';s=p.read_text()
old="        self._add('cited_standard', completion['evidence'], '当前以明确临床优势作为申请程序的操作性条件，承接同源同版完整定义及并列分支；疾病严重程度、宗旨和其他工作章节不被补入', relation_subtype='operative_value_complete_definition', resolution_path='primary_literal_complete_operative_value_definition', current_criterion_anchor=self.current_anchor(criterion.start(), criterion.end()), current_application_anchor=self.current_anchor(application.start(), application.end()), defined_value_expression=criterion.group(), action_scope='current_application_criterion_consumes_definition', **details)"
new=old+"""
        receipt = completion.get('neutral_scope_receipt')
        if receipt:
            proof = receipt['closure_proof']
            proof_only = proof['boundary_quotes'] + proof['identity_quotes'] + proof['proof_only_quotes']
            self._add('cited_standard', receipt['content_evidence'] + proof_only, '当前申请的实质临床优势条件消费同版有限完整定义；安全/疗效分支须由定义原文成立，边界和标题仅作证明', relation_subtype='SE_operative_value_complete_definition', affected_dimensions=['S','E','Ec'], SE_scope_verified=True, closure_proof=proof, standard_text=receipt['standard_text'], current_operative_anchor=receipt['current_operative_anchor'], current_source_snapshot_span=receipt['current_source_snapshot_span'], defined_value_expression=criterion.group(), version_binding={'established':True,'binding':'exact_same_primary_literal_snapshot','source_sha256':completion['source_sha256']}, action_scope='current_application_criterion_consumes_definition', not_whole_file_inheritance=True)
        else:
            self.material_requests.append({'path':'cited_standard','reference':criterion.group(),'missing':completion.get('neutral_scope_problem') or '操作性临床优势定义尚未核明有限内容和真实边界','dimensions':['S','E','Ec']})
"""
assert s.count(old)==1;s=s.replace(old,new)
old="affected_dimensions=['I'] if timed_review else ['I', 'F'], negation_and_withdrawal_retained=True)"
new="affected_dimensions=([] if timed_review else ['F']) if re.search('仿制药', text) and not re.search('创新药|改良型新药|创新研发|新药研发', text) else (['I'] if timed_review else ['I', 'F']), explicit_generic_object_excludes_borrowed_innovation=bool(re.search('仿制药', text) and not re.search('创新药|改良型新药|创新研发|新药研发', text)), negation_and_withdrawal_retained=True)"
assert s.count(old)==1;s=s.replace(old,new)
old="relation_subtype='complete_table_basic_protection_definition', protection_branch='base_table_arrangement'"
new="relation_subtype='complete_table_basic_protection_definition', affected_dimensions=['S','E','Ec'], SE_scope_verified=True, closure_proof={'boundary_quotes':[], 'scope_kind':'finite_same_article_object_duration_and_explicit_scope_definition', 'source_sha256':current['source_ref']['sha256'], 'whole_article_condition_not_inherited':True, 'exact_resource_identity_and_original_clause_ordinals_verified':True}, protection_branch='base_table_arrangement'"
assert s.count(old)==1;s=s.replace(old,new)
# A full condition reference needs strict original order and a real next article.
needle="    def _operative_references(self):"
helper="""    def _closed_reference_scope(self, container, members, article):
        if container.get('kind') != 'cited_reference':
            return None
        contexts = []
        for child, span, text in members:
            if child in contexts or span != (0, len(child.get('text',''))):
                return None
            contexts.append(child)
        proof = self._se_group_proof(container, contexts)
        if not proof:
            return None
        heading = re.match(ARTICLE_REFERENCE, norm(contexts[0]['text']))
        if not heading or ordinal_number(heading.group(1)) != article:
            return None
        for index, c in enumerate(contexts, 1):
            supplied_clause = self._supplied_clause_number(c)
            if supplied_clause is not None and supplied_clause != index:
                return None
            if index > 1 and not self._se_next_geometry(contexts[index-2], c):
                return None
        if not any((re.match(ARTICLE_REFERENCE, norm(q['text'])) and ordinal_number(re.match(ARTICLE_REFERENCE, norm(q['text'])).group(1)) == article + 1) for q in proof['boundary_quotes']):
            return None
        return dict(proof, original_clause_count=len(contexts), ordered_context_ids=[c['context_id'] for c in contexts], positional_clause_selection_verified=True)

"""
assert s.count(needle)==1;s=s.replace(needle,helper+needle)
# Old IF relation remains where no complete original-reference proof; only proof
# backed exact chains become SE consumers. Never clear their unresolved request.
old="            container, members = candidates[0]\n            if clause is not None"
new="            container, members = candidates[0]\n            chain_proofs = []\n            proof = self._closed_reference_scope(container, members, article)\n            if proof:\n                chain_proofs.append(proof)\n            if clause is not None"
assert s.count(old)==1;s=s.replace(old,new)
old="                    donor, donor_members = donors[0]\n                    further_clause"
new="                    donor, donor_members = donors[0]\n                    donor_proof = self._closed_reference_scope(donor, donor_members, further_article)\n                    if donor_proof:\n                        chain_proofs.append(donor_proof)\n                    else:\n                        proof = None\n                    further_clause"
assert s.count(old)==1;s=s.replace(old,new)
old="            self._add('cited_standard', evidence, '当前以精确条款条件决定实质保护待遇"
new="            scope_verified = bool(proof and len(chain_proofs) == len(chain))\n            boundary_quotes = [q for pr in chain_proofs for q in pr['boundary_quotes']] if scope_verified else []\n            self._add('cited_standard', evidence + boundary_quotes, '当前以精确条款条件决定实质保护待遇"
assert s.count(old)==1;s=s.replace(old,new)
old="relation_subtype='finite_operational_article_reference', protection_branch="
new="relation_subtype='finite_operational_article_reference', SE_scope_verified=scope_verified, affected_dimensions=['S','E','Ec','I','F'], closure_proof={'boundary_quotes':boundary_quotes,'reference_scope_proofs':chain_proofs,'scope_verified':scope_verified,'finite_reference_depth':2}, protection_branch="
assert s.count(old)==1;s=s.replace(old,new)
# Duplicate raw SE entry must not override a fully verified finite chain with
# a broader whole-article or sibling-clause consumption.
old="        for number, clause in requested:\n            grouped = {}"
new="        for number, clause in requested:\n            resolved = [r for r in self.relations if r.get('relation_subtype') == 'finite_operational_article_reference' and r.get('SE_scope_verified') and r.get('reference_chain') and r['reference_chain'][0].get('article') == number and r['reference_chain'][0].get('clause') == clause]\n            if len(resolved) == 1:\n                continue\n            grouped = {}"
assert s.count(old)==1;s=s.replace(old,new)
old="            nextid = bst.get('next_paragraph_id')"
new="            nextid, next_ok = self._se_geometry_value(boundary, 'next_paragraph_id')\n            candidate, candidate_ok = self._se_geometry_value(boundary, 'next_candidate_paragraph_id')\n            if not next_ok or not candidate_ok or (nextid and candidate and nextid != candidate):\n                continue\n            nextid = nextid or candidate"
assert s.count(old)==1;s=s.replace(old,new)
old="        if not substantial:\n            return\n        options = []\n        for container in self.contexts:"
new="        substantial = substantial or re.search('(?:符合|满足|具备).{0,45}(?:纳入|进入).{0,20}(?:范围|续约|谈判|待遇|支持)|(?:申请|申报|纳入).{0,65}(?:需|须|应|必须)(?:同时)?(?:符合|满足|具备).{0,20}(?:下列|以下).{0,12}条件', current)\n        if not substantial:\n            return\n        options = []\n        for container in self.contexts:"
assert s.count(old)==1;s=s.replace(old,new)
old="            if re.search('(?:费用|药费).{0,50}"
idx=s.index(old,s.index('    def _se_direct_content_parents'))
addition="""            if re.search('(?:主动|企业主动)(?:申请|申报)调整(?:医保|限定)?支付范围[^。；;]{0,20}药品', self.norm) and re.search('(?:以下|下列|这些).{0,12}(?:情况|情形).{0,15}(?:须|需|应|必须).{0,12}(?:申报|申请).{0,12}(?:方可|才能).{0,8}调整[:：]?$', norm(raw)):
                self._add('parent_predicate', [self._quote(c, '当前支付范围成员承接同源直接父句的申报—方可调整后果')], '父句的调整对象由当前支付范围成员唯一补足；普通申报名单或异版父句不成立', relation_subtype='SE_elliptical_payment_adjustment_member', affected_dimensions=['Ec'], shared_predicate=raw, member_text=self.text, parent_scope_binding=binding, elliptical_payment_object_from_current=True)
"""
s=s[:idx]+addition+s[idx:];p.write_text(s)
p=P/'dimensions.py';s=p.read_text();old="    return bool(identity and (not actual) and (not parent_payment))";new="    elliptical_payment = bool(identity and re.search('(?:以下|下列|这些).{0,12}(?:情况|情形).{0,15}(?:须|需|应|必须).{0,12}(?:申报|申请).{0,12}(?:方可|才能).{0,8}调整[:：]?$', inherited))\n    return bool(identity and (not actual) and (not parent_payment) and (not elliptical_payment))";assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
print('patched scoped relations and economic identity gate')
