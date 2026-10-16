from pathlib import Path
import shutil, ast
R=Path(__file__).resolve().parents[2]
V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v11-protected-data-role-sol'
B=V.parent/'joint-v10-if-e-combined-v2-root'
V.mkdir(exist_ok=False)
for n in ['evidence','source_packet','source_receipts','relations','dimensions']:
 (V/(n+'.py')).write_bytes((B/(n+'.py')).read_bytes())
gate='数据保护|受保护[^。；;]{0,6}数据'
rel=(V/'relations.py').read_text()
constant="\nV11_REPAIR_ENTRY = "+repr(gate)+"\n\ndef _v11_repair_gate(text):\n    return bool(re.search(V11_REPAIR_ENTRY, text))\n\n"
rel=rel.replace('class SourceDependencyStop(ValueError):',constant+'class SourceDependencyStop(ValueError):',1)
old='        if _e_outcome_gate(self.text):\n            self._e_current_outcome_relationships()\n'
assert rel.count(old)==1
rel=rel.replace(old,old+'        if _v11_repair_gate(self.norm):\n            self._v11_protected_data_roles()\n',1)
rel+=r'''

    def _v11_article_geometry(self, rows, pointer):
        # Read supplied original addresses only; no asset read or source cache
        # mutation. Article labels alone are not a completeness proof.
        sha = self.unit.get('source_ref', {}).get('sha256')
        group = self._pointer(pointer)
        di = int(pointer.split('/')[2])
        doc = self.bundle['explicit_or_primary_source_resources'][di]
        number = article_number(group.get('article'))
        if not number or group.get('scope_stop_before_next_article') is not True:
            return None
        header = re.match(r'^第(' + ORDINAL + r')条', norm(rows[0]['text']))
        if not header or ordinal_number(header.group(1)) != number:
            return None
        items = []
        for c in rows:
            origin = self.origins.get(c['context_id'], {})
            item = self._pointer(origin['source_bundle_pointer'])
            if item.get('source_sha256') != sha or item.get('text_sha256') != digest(item['text']):
                return None
            if not doc.get('source_version_id') or item.get('source_version_id') != doc['source_version_id']:
                return None
            if item.get('role') != 'original_normative_paragraph':
                return None
            items.append(item)
        positions, html_positions, html_spans = [], [], []
        json_sha, html_sha = None, None
        for item in items:
            loc = item.get('source_locator', {})
            structured, html = loc.get('structured_snapshot', {}), loc.get('raw_html', {})
            index = structured.get('normative_paragraphs_index_zero_based')
            hp = html.get('p_element_index_zero_based_document_wide')
            span = html.get('raw_utf8_byte_interval_half_open')
            if type(index) is not int or type(hp) is not int or not isinstance(span, list) or len(span) != 2 or any(type(i) is not int for i in span) or span[0] >= span[1]:
                return None
            if structured.get('json_pointer') != '/normative_paragraphs/' + str(index) or structured.get('sha256') != sha:
                return None
            if not isinstance(html.get('sha256'), str) or len(html['sha256']) != 64:
                return None
            pair = (structured.get('sha256'), html.get('sha256'))
            if json_sha is None:
                json_sha, html_sha = pair
            elif pair != (json_sha, html_sha):
                return None
            positions.append(index); html_positions.append(hp); html_spans.append(span)
        if positions != list(range(positions[0], positions[0] + len(rows))) or html_positions != list(range(html_positions[0], html_positions[0] + len(rows))):
            return None
        if any(a[1] != b[0] for a, b in zip(html_spans, html_spans[1:])):
            return None
        if group.get('structured_index_range_half_open') != [positions[0], positions[-1] + 1] or group.get('raw_HTML_p_indices_zero_based') != html_positions:
            return None
        boundary = [x for x in doc.get('source_texts', []) if x.get('source_resource_id') == group.get('next_article_boundary_resource_id')]
        if len(boundary) != 1:
            return None
        b = boundary[0]; sl = b.get('source_locator', {}); bs = sl.get('structured_snapshot', {}); bh = sl.get('raw_html', {})
        if b.get('role') != 'next_article_boundary_header_only' or b.get('source_sha256') != sha or b.get('source_version_id') != doc['source_version_id'] or b.get('text_sha256') != digest(b.get('text', '')):
            return None
        if not re.fullmatch(r'第' + ORDINAL + r'条', norm(b.get('text', ''))) or article_number(b['text']) != number + 1 or group.get('next_article_boundary_header_only') != b['text']:
            return None
        if bs.get('sha256') != sha or bs.get('normative_paragraphs_index_zero_based') != positions[-1] + 1 or bs.get('json_pointer') != '/normative_paragraphs/' + str(positions[-1] + 1) or bh.get('sha256') != html_sha or bh.get('p_element_index_zero_based_document_wide') != html_positions[-1] + 1 or bh.get('header_only') is not True:
            return None
        return {'article': group['article'], 'source_sha256': sha, 'source_version_id': doc['source_version_id'], 'structured_positions': positions, 'raw_HTML_paragraph_positions': html_positions, 'raw_HTML_byte_intervals': html_spans, 'next_article_header': b['text'], 'source_article_group_pointer': pointer}

    def _v11_missing_protected_holder(self, issue):
        # A typed private request is consumed only by the new I consumer. Old
        # material/source request lists and source scan events are untouched.
        request = {'path': 'named_mechanism', 'reference': '当前该持有人受保护数据所在的同版本完整原条款', 'missing': issue, 'dimensions': ['I'], 'affected_dimensions': ['I'], 'status': 'unresolved', 'dependency_status': 'stopped', 'necessary_dependency': True, 'current_text': self.text, 'producer': 'v11_protected_data_I_relationship'}
        self._add('v11_protected_data_I_relationship', [self.proposition()], '当前已实质实施受保护数据许可限制，但原持有人及本条保护范围的必要来源关系未闭合；未知不记0。', relation_subtype='protected_holder_definition_missing', affected_dimensions=['I'], only_IF_consumers=True, v11_status='necessary_material_unresolved', v11_dependency_request=request)

    def _v11_protected_data_roles(self):
        # The pure current gate dominates every new lookup or mutation.
        if not _v11_repair_gate(self.norm):
            return
        operation = re.fullmatch(r'在数据保护期内,其他申请人未经持有人(?:同意|许可),依赖该持有人受保护的数据提交的(?P<counterparty>(?:改良型新药、)?化学仿制药和生物类似药)的上市申请或者补充申请,[^,。；;]{1,30}不予许可;(?P<exception>其他申请人提交自行取得并未依赖他人受保护数据的除外)[。]?', self.norm)
        if not operation:
            return
        current = self._v9_current_context()
        if not current or norm(current.get('text', '')) != self.norm:
            self._v11_missing_protected_holder('当前完整原段唯一身份及其同条治理关系未核明。')
            return
        matches = [(rows, pointer) for rows, pointer in self._v10_complete_articles() if sum(norm(c['text']) == self.norm for c in rows) == 1]
        if len(matches) != 1:
            self._v11_missing_protected_holder('同版资料未唯一提供当前完整原段所在条款的全部连续段落及边界，不能借其他条的持有人定义。')
            return
        rows, pointer = matches[0]
        geometry = self._v11_article_geometry(rows, pointer)
        if not geometry or norm(rows[-1]['text']) != self.norm:
            self._v11_missing_protected_holder('当前条款的原条首、连续原位置、当前末段及下一条边界尚未完整绑定。')
            return
        first = norm(rows[0]['text'])
        holder = re.fullmatch(r'第' + ORDINAL + r'条\s*自(?P<class>创新药|改良型药品|改良型新药)首次境内上市许可之日起,给予\d+年数据保护期[。]?', first)
        # Complete ordinary/non-qualifying holder data is a substantiated
        # exclusion, not missing material, and is never borrowed from siblings.
        if not holder:
            return
        drug_class = holder.group('class')
        data_scope = None
        if drug_class.startswith('改良'):
            if len(rows) < 3:
                self._v11_missing_protected_holder('改良药本条受保护数据的实质资格范围未提供。')
                return
            data_scope = norm(rows[-2]['text'])
            if not re.fullmatch(r'本条款中药品的数据保护范围包括证明其与[^。；;]{1,100}(?:相比|比较)具有明显临床优势的新的临床试验数据,但不包括[^。；;]{1,100}[。]?', data_scope) or not re.search('已知|已上市', data_scope):
                return
            # Any other branch before the data scope must remain the same
            # improved class and same first-domestic-license entitlement.
            for c in rows[1:-2]:
                if not re.fullmatch(r'境外已上市境内未上市的' + re.escape(drug_class) + r',自首次境内上市许可之日起,给予\d+年数据保护期[。]?', norm(c['text'])):
                    return
        elif len(rows) != 2:
            # A minimal general route cannot silently inherit unparsed extra
            # branches. Larger innovative articles stay on their old paths.
            return
        evidence = [self._quote(c, '同版完整本条原持有人、保护范围、许可限制及自取例外逐项角色依据') for c in rows]
        self._add('v11_protected_data_I_relationship', evidence, '当前依赖受保护数据的不予许可安排执行同条创新/改良原持有人的差异化权利；仿制/类似药申请人是受限相对方，自取且未依赖数据的例外完整保留。', relation_subtype='qualified_original_holder_data_right', affected_dimensions=['I'], only_IF_consumers=True, v11_status='qualified_original_holder_right', source_article_group_pointers=[pointer], v11_role_receipt={'protected_holder_drug_class': drug_class, 'protected_holder_entitlement': rows[0]['text'], 'improved_qualified_data_scope': rows[-2]['text'] if data_scope else None, 'restricted_counterparty': operation.group('counterparty'), 'current_operation': self.text, 'independent_nonreliant_data_exception': operation.group('exception'), 'complete_article_quotes': [c['text'] for c in rows], 'original_article_binding': geometry, 'no_counterparty_innovation_inference': True})
'''
(V/'relations.py').write_text(rel)
dims=(V/'dimensions.py').read_text();needle='from relations import _v10_repair_gate\n';assert dims.count(needle)==1;dims=dims.replace(needle,needle+'from relations import _v11_repair_gate\n',1)
needle='    decisions = acc.finish()\n';assert dims.count(needle)==1;dims=dims.replace(needle,'    if _v11_repair_gate(view.norm):\n        _v11_protected_data_I_consume(acc, view)\n'+needle,1)
dims+=r'''

def _v11_protected_data_I_consume(acc, view):
    if not _v11_repair_gate(view.norm):
        return
    for relation in view.linked('v11_protected_data_I_relationship'):
        details = relation['details']
        if details.get('affected_dimensions') != ['I'] or details.get('only_IF_consumers') is not True:
            raise ValueError('v11 protected-data consumer must be exactly I-only')
        if details.get('v11_status') == 'necessary_material_unresolved':
            request = details['v11_dependency_request']
            route = _material_request_route(request)
            if route['dimensions'] != ['I']:
                raise ValueError('v11 dependency request must be exactly I-only')
            acc.request('I', request)
            if route not in acc.material_routes['I']:
                acc.material_routes['I'].append(route)
            continue
        if details.get('v11_status') != 'qualified_original_holder_right':
            raise ValueError('unrecognized v11 protected-holder status')
        roles = details['v11_role_receipt']
        unit = Unit(view.norm, 0, len(view.norm), relation['context_evidence'], 'v11_protected_data_I_relationship', details)
        obj = {'established': True, 'object_text': roles['protected_holder_entitlement'], 'context_evidence': unit.contexts, 'current_anchors': [view.current_anchor(0, len(view.norm))], 'role': 'same_article_original_qualified_protected_holder', 'reason': '原创新/改良药品持有人的保护权利由当前依赖数据许可限制执行；受限仿制/类似药申请人不成为创新对象'}
        acc.add('I', unit, 'v11_I4_qualified_original_holder_data_right', details['relation_reason'], obj, {'v11_role_receipt': roles, 'scope': 'same original article holder, protected data and actual current restriction/exception; no sibling rights or counterparty novelty'})
'''
(V/'dimensions.py').write_text(dims)
(V/'static_gate.py').write_text('"""Pure current-only V11 gate. No classifier import or source access."""\nimport re\nimport unicodedata\nV11_REPAIR_ENTRY = '+repr(gate)+'\n\ndef matching_current(raw):\n    joined = "".join(unicodedata.normalize("NFKC", char) for char in raw)\n    return re.sub(r"(?<=[\\u3400-\\u9fff])\\s+(?=[\\u3400-\\u9fff])", "", joined)\n\ndef normalized_gate(text):\n    return bool(re.search(V11_REPAIR_ENTRY, text))\n\ndef gate(raw):\n    return normalized_gate(matching_current(raw))\n')
for p in V.glob('*.py'):ast.parse(p.read_text())
print('candidate written and AST syntax checked; classifier executions=0')
