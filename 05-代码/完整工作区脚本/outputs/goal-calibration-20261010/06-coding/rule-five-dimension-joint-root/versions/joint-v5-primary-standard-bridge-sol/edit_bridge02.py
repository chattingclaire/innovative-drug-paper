from pathlib import Path
P=Path(__file__).resolve().parent
r=P/'relations.py';s=r.read_text()
old="        return {'evidence': evidence, 'standard_text': raw[ga:gb], 'programme_name': name, 'standard_family': family, 'source_sha256': primary, 'selected_group_snapshot_span': [ga, gb], 'programme_block_snapshot_span': [title.end(), end], 'selected_leaf_spans': selected, 'not_whole_file_inheritance': True}\n"
new="""        completion = {'evidence': evidence, 'standard_text': raw[ga:gb], 'programme_name': name, 'standard_family': family, 'source_sha256': primary, 'selected_group_snapshot_span': [ga, gb], 'programme_block_snapshot_span': [title.end(), end], 'selected_leaf_spans': selected, 'not_whole_file_inheritance': True}
        receipt, problem = self._primary_standard_scope_receipt(raw, intervals, title, end, ga, gb, family, candidates)
        completion['neutral_scope_receipt'] = receipt
        completion['neutral_scope_problem'] = problem
        return completion

    def _primary_standard_scope_receipt(self, raw, intervals, title, programme_end, ga, gb, family, candidates):
        '''Prove a source-only finite standard and its actual next boundary.

        EOF is not a boundary. One unique current occurrence and supplied
        component/coordinate consistency are necessary; an integer address,
        a programme name, or a resolved request alone cannot supply this proof.
        '''
        primary = self.unit.get('source_ref', {}).get('sha256')
        if hashlib.sha256(raw.encode('utf8')).hexdigest() != primary:
            return None, '所供字面叶拼接与同一原件字节SHA不能核对'
        if any(not self._se_same_geometry(c, self.unit) for _, _, c in intervals) or any(not self._se_same_geometry(c, self.unit) for c in candidates):
            return None, '所供同SHA当前、标准种子与字面叶组件缺失冲突或不能同源绑定'
        block = raw[title.end():programme_end]
        view, offsets = matching_view(block)
        occurrences = list(re.finditer(re.escape(self.norm), view))
        if len(occurrences) != 1:
            return None, '当前完整操作命题在同一原件具名组件内未唯一定位'
        a, b = raw_span(offsets, occurrences[0].start(), occurrences[0].end())
        current_span = [title.end() + a, title.end() + b]
        supplied = self.unit.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
        if supplied is not None and (not isinstance(supplied, list) or len(supplied) != 2 or any(type(x) is not int for x in supplied) or not supplied[0] <= current_span[0] < current_span[1] <= supplied[1]):
            return None, '已供当前原文区间与实际唯一操作命题位置冲突'
        for c in candidates:
            cv = norm(c.get('text', ''))
            found = list(re.finditer(re.escape(cv), view)) if cv else []
            if len(found) != 1:
                return None, '当前确指标准的种子在同一原件具名组件内未唯一定位'
            x, y = raw_span(offsets, found[0].start(), found[0].end())
            source_span = c.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
            if source_span is not None and (not isinstance(source_span, list) or len(source_span) != 2 or any(type(v) is not int for v in source_span) or not source_span[0] <= title.end()+x < title.end()+y <= source_span[1]):
                return None, '已供标准种子的原文区间与唯一同版位置冲突'
        # gb must start an actual supplied next normative heading. A leaf or
        # programme-block end by itself is never accepted as a scope boundary.
        line_end = raw.find('\\n', gb)
        line_end = len(raw) if line_end < 0 else line_end
        boundary_text = raw[gb:line_end]
        normative_heading = re.fullmatch(r'[ \\t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])[ \\t]*[^\\n]{2,}', boundary_text)
        next_programme = re.fullmatch(PROGRAMME_HEADING_RE, boundary_text)
        if gb >= len(raw) or not (normative_heading or next_programme):
            return None, '同版有限标准组后未见实际下一规范边界；EOF/有限叶截止不能证明闭合'
        numbered = list(re.finditer(r'(?m)^[ \\t]*(\\d+)[.、．][^\\n]*', raw[ga:gb]))
        if not numbered or [int(m.group(1)) for m in numbered] != list(range(1, len(numbered)+1)):
            return None, '明确条件成员的原文编号未从首项连续闭合提供'
        content_end = gb
        if family == 'termination':
            last = numbered[-1]
            content_end = ga + last.end()
            # A physical continuation is included only until the enumerated
            # member's actual final punctuation. An independent next paragraph
            # is not an additional unnumbered termination condition.
            while not re.search(r'[。；;][ \\t]*$', raw[ga+last.start():content_end]):
                next_end = raw.find('\\n', content_end+1, gb)
                next_end = gb if next_end < 0 else next_end
                if next_end <= content_end:
                    return None, '末项终止条件的实际原文段落未闭合'
                content_end = next_end
            if not re.search(r'[。；;][ \\t]*$', raw[ga+last.start():content_end]):
                return None, '末项终止条件的实际原文段落未闭合'
        def quotes(lo, hi, role):
            result=[]
            for x,y,c in intervals:
                left,right=max(x,lo),min(y,hi)
                if left<right:
                    result.append(self._quote(c, role, (left-x,right-x)))
            return result
        content = quotes(ga, content_end, '当前操作性援引的完整有限标准成员及直接定义，未跨到下一边界')
        boundary = quotes(gb, line_end, '实际下一规范标题，只证明有限标准闭合，不捐实质内容')
        identity = quotes(title.start(), title.end(), '同一原件具名组件标题，仅核身份，不从名称赋维')
        current_quote = quotes(*current_span, '同一snapshot唯一当前实质操作命题，仅核当前承接与原文定位')
        tail = quotes(content_end, gb, '编号终止条件后的独立段落，仅证明连续到下一边界，不作为编号条件内容') if content_end < gb else []
        if not content or not boundary or not current_quote:
            return None, '有限标准、实际下一边界或当前命题的精确原文引文未完整覆盖'
        proof = {'source_sha256':primary, 'actual_next_normative_boundary':True,
                 'closure_basis':'contiguous supplied raw snapshot; actual numbered members and actual next normative heading',
                 'group_snapshot_span':[ga,gb], 'content_snapshot_span':[ga,content_end],
                 'actual_next_boundary_snapshot_span':[gb,line_end], 'current_snapshot_span':current_span,
                 'current_exact_raw_text':raw[current_span[0]:current_span[1]],
                 'current_coordinate_grade':'supplied_range_consistent_and_unique_raw_occurrence' if supplied is not None else 'unique_same_snapshot_literal_occurrence_without_supplied_current_range',
                 'boundary_quotes':boundary, 'identity_quotes':identity, 'proof_only_quotes':current_quote+tail,
                 'only_original_numbered_termination_members':family=='termination', 'EOF_is_not_closure':True,
                 'source_component_conflicts_rejected':True, 'finite_reference_depth':1}
        return {'content_evidence':content,'closure_proof':proof,'standard_text':raw[ga:content_end],
                'current_operative_anchor':self.proposition(),'current_source_snapshot_span':current_span,
                'boundary_only_tail_snapshot_span':[content_end,gb] if content_end<gb else None}, None
"""
assert s.count(old)==1;s=s.replace(old,new)
old="            self._bounded_primary_support_roles(completion, same_source)\n"
new="""            receipt = completion.get('neutral_scope_receipt')
            if receipt:
                proof = receipt['closure_proof']
                proof_only = proof['boundary_quotes'] + proof['identity_quotes'] + proof['proof_only_quotes']
                self._add('cited_standard', receipt['content_evidence'] + proof_only, '当前操作性标准核验/资格后果精确承接同一原件有限完整标准；真实下一规范边界与标题/独立尾段仅作闭合证明', relation_subtype='SE_primary_literal_operational_standard', affected_dimensions=['S','E','Ec'], SE_scope_verified=True, closure_proof=proof, standard_text=receipt['standard_text'], current_operative_anchor=receipt['current_operative_anchor'], current_source_snapshot_span=receipt['current_source_snapshot_span'], standard_family=family, version_binding={'established':True,'binding':'exact_same_primary_literal_snapshot','source_sha256':completion['source_sha256']}, action_scope='standard_review_or_eligibility_consequence', norm_start=0, norm_end=len(self.norm), not_whole_file_inheritance=True)
            else:
                request = {'path':'cited_standard','reference':self.text,'current_text':self.text,'missing':completion.get('neutral_scope_problem') or '已供标准尚未核明实际有限闭合与当前精确操作定位','dimensions':['S','E','Ec'],'request_kind':'provided_source_scope_unverified','other_resolved_and_stopped_references_retained':True}
                self.material_requests.append(request)
                self.source_requests.append({**request,'dependency_status':'stopped','resolution_path':'primary_literal_standard_scope_proof_unverified','no_new_material':True})
            self._bounded_primary_support_roles(completion, same_source)
"""
assert s.count(old)==1;s=s.replace(old,new)
r.write_text(s)
d=P/'dimensions.py';s=d.read_text()
insert='''def _verified_source_quote_identity(view, quote):
    """Exact original range identity; a shared leaf ID alone is not a boundary."""
    if not isinstance(quote, dict):
        return None
    matches=[c for c in view.contexts if c.get('context_id')==quote.get('context_id')]
    if len(matches)!=1:
        return None
    c=matches[0];a,b=quote.get('start'),quote.get('end')
    if type(a) is not int or type(b) is not int or not 0<=a<b<=len(c.get('text','')):
        return None
    if quote.get('text')!=c['text'][a:b] or quote.get('source_ref')!=c.get('source_ref'):
        return None
    return (quote['context_id'],a,b,quote['text'],quote['source_ref'])

'''
assert s.count('def _units(view) -> list[Unit]:')==1;s=s.replace('def _units(view) -> list[Unit]:',insert+'def _units(view) -> list[Unit]:')
old="""                        if ctx.get('context_id') in {q['context_id'] for q in details.get('closure_proof', {}).get('boundary_quotes', [])}:
                            continue
"""
new="""                        proof = details.get('closure_proof', {})
                        proof_only = proof.get('boundary_quotes', []) + proof.get('identity_quotes', []) + proof.get('proof_only_quotes', [])
                        same_source_quotes = [q for q in proof_only if q.get('context_id') == ctx.get('context_id')]
                        if same_source_quotes:
                            actual = _verified_source_quote_identity(view, ctx)
                            keys = [_verified_source_quote_identity(view,q) for q in same_source_quotes]
                            if actual is None or any(key is None for key in keys):
                                scope=set(details.get('affected_dimensions',DIMENSIONS))
                                if details.get('only_IF_consumers'):scope &= {'I','F'}
                                if scope:view.material_requests.append({'path':kind,'reference':view.text,'missing':'标准内容/仅作边界的引文缺少一致精确源区间，不能按不同text放行','dimensions':sorted(scope),'request_kind':'quote_scope_conflict'})
                                continue
                            if any(actual == key for key in keys):
                                continue
                            if any(actual[1] < key[2] and key[1] < actual[2] for key in keys):
                                scope=set(details.get('affected_dimensions',DIMENSIONS))
                                if details.get('only_IF_consumers'):scope &= {'I','F'}
                                if scope:view.material_requests.append({'path':kind,'reference':view.text,'missing':'所供实质标准引文与实际仅作边界/身份的原文区间重叠，须核正有限消费范围','dimensions':sorted(scope),'request_kind':'quote_scope_conflict'})
                                continue
"""
assert s.count(old)==1;s=s.replace(old,new);d.write_text(s)
print('edited v5 local bridge and exact quote boundary identity; no shared consumer widening')
