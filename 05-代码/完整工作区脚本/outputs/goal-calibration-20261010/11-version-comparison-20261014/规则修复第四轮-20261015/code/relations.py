"""Bounded source relations. No record identity, outcome, or corpus access.

The source graph supplies positions and original text. Relations are computed here;
they are not dimension permissions. Classification remains in dimensions.py.
"""
import re
import json
import hashlib
from evidence import matching_view, raw_span, anchor, context_anchor

OBJECT = r'药品|药物|新药|本药|该药|研究药|试验药|用药|疗效|患者|治疗|制剂|片剂|剂型|研发|生物制品|中药'
INTRO = r'下列|以下(?!简称)|同时满足|条件之一|具体包括'
SUBSTANTIVE = r'申请|纳入|符合|应.{0,12}(?:评价|比较|提供|说明|证据)|支付|享受|可.{0,12}(?:获得|适用|使用)'
ACTION = r'决定开展|组织开展|组织实施|同意.{0,30}开展|设立|开放|实施|撤回|终止|取消|限制|适用'
PROGRAM = r'[\u4e00-\u9fff]{2,24}(?:程序|计划|通道|试点)'
ORDINAL = r'[零〇一二两三四五六七八九十百千0-9]+'
ARTICLE_REFERENCE = rf'第({ORDINAL})条(?:第({ORDINAL})款)?'


def ordinal_number(token):
    if token.isdigit():
        return int(token)
    digits = dict(zip('零〇一二两三四五六七八九', (0, 0, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9)))
    units = {'十': 10, '百': 100, '千': 1000}
    total = number = 0
    for char in token:
        if char in digits:
            number = digits[char]
        elif char in units:
            total += (number or 1) * units[char]
            number = 0
        else:
            return None
    return total + number


def norm(text):
    return matching_view(text)[0]


def sentence_spans(text):
    # Semicolons retain OR branches in the complete decision proposition.
    return [(m.start(), m.end()) for m in re.finditer(r'[^。\n]+(?:。|\n|$)', text)]


def title_key(title):
    # Generic title morphology; not a table of named programs or fixture texts.
    t = re.sub(r'[\W_]', '', norm(title))
    return re.sub(r'关于|改革|工作方案|工作规范|工作|试行|要求|通知|政策解读', '', t)


def same_component(left, right):
    def component(c):
        return c.get('structure', {}).get('component_id') or c.get('source_ref', {}).get('locator', {}).get('component_id')
    a, b = component(left), component(right)
    return not (a and b and a != b)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class SourceDependencyStop(ValueError):
    """Malformed source graph cannot be treated as an absent rule predicate."""


class RelationView:
    def __init__(self, unit):
        if 'id' in unit or 'labels' in unit or 'decisions' in unit:
            raise ValueError('semantic view must not contain administrative identity/results')
        self.unit = unit
        self.text = unit['text']
        self.norm, self.offsets = matching_view(self.text)
        self.all_contexts = unit.get('contexts', [])
        self.bundle = unit.get('source_bundle', {})
        self.origins = unit.get('derived_context_origins', {})
        self.source_view_events = []
        self.source_relation_traces = []
        self.source_requests = []
        self._read_keys = set()
        self._scan_source_views()
        self.contexts = [c for c in self.all_contexts if self._policy_role(c)]
        self.by_id = {c['context_id']: c for c in self.contexts}
        self.material_requests = []
        self.relations = []
        self._parents()
        self._local_operations()
        self._lists()
        self._operative_review_list()
        self._named_support_missing_scope()
        self._trial_admission_support()
        self._standards()
        self._programme_condition_consequence()
        self._programme_operative_eligibility()
        self._operative_value_definition()
        self._table_protection_branches()
        self._data_protection_rights_consequence()
        self._operative_references()
        self._mechanisms()
        self._explanations()
        self._anaphors()
        self._applicable_support()
        self._resource_definitions()
        self._postadmission_technical_support()
        self._priority_resource_arrangements()
        self._need_linked_inspection_deferral()
        self._team_service_execution()
        self._price_arrangement_definition()
        self._tables()
        self._complete_source_relations()
        self._nested_explicit_clinical_advantage_standard()
        # The old recognized request paths remain the decision accumulator's
        # stop interface. Receipts make their source dependency explicit.
        for request in self.material_requests:
            if request not in self.source_requests:
                self.source_requests.append(dict(request, dependency_status='stopped'))
        self.source_scope_review = {'status': 'complete', 'source_evidence_note':
            '原CTX文字与结构逐字段读取；完整来源对象的结构、文字及身份已解析。仅当前确指、完整组或同版具名关系使用选定原文；图片未读取，全文不自动适用。'}

    def match(self, pattern, text=None):
        return list(re.finditer(pattern, self.norm if text is None else norm(text)))

    def current_anchor(self, a, b):
        a, b = raw_span(self.offsets, a, b)
        return anchor(self.text, a, b)

    def proposition(self, a=0, b=None):
        # Whole fixed current unit intentionally preserves negation/exception scope.
        return anchor(self.text, 0, len(self.text))

    def context_anchor(self, cid, a, b, usage):
        return context_anchor(self.unit, cid, a, b, usage)

    def linked(self, kind):
        return [r for r in self.relations if r['kind'] == kind]

    def _quote(self, c, usage, span=None):
        a, b = span or (0, len(c.get('text', '')))
        return self.context_anchor(c['context_id'], a, b, usage)

    def _add(self, kind, evidence, reason, **details):
        evidence = [e for e in evidence if e['text']]
        if not evidence:
            return
        signature = (kind, tuple((e['text'], e['source_ref'].get('sha256')) for e in evidence))
        for old in self.relations:
            if old['_signature'] == signature:
                return
        d = {'content': '\n'.join(e['text'] for e in evidence),
             'context_ids': [e['context_id'] for e in evidence],
             'full_scope': True, 'relation_reason': reason, **details}
        used = []
        for e in evidence:
            for view in self._used_views(e['context_id'], e, reason):
                if view not in used:
                    used.append(view)
        pointer = details.get('source_group_pointer')
        if pointer and pointer.startswith('/explicit_or_primary_source_resources/'):
            doc = self.bundle['explicit_or_primary_source_resources'][int(pointer.split('/')[2])]
            used.append({'resource_id': doc['source_resource_id'], 'view': 'document_bundle',
                'use_scope': {'reason': reason, 'geometry_pointer': pointer,
                    'printed_operator': details.get('group_operator'),
                    'scope': 'selected_complete_numbered_geometry; not_whole_source_inheritance'}})
        for pointer in details.get('source_article_group_pointers', []):
            doc = self.bundle['explicit_or_primary_source_resources'][int(pointer.split('/')[2])]
            used.append({'resource_id': doc['source_resource_id'], 'view': 'document_bundle',
                'use_scope': {'reason': reason, 'source_article_group_pointer': pointer,
                    'scope': 'exact_original_article_order_and_clause_identity; selected_branch_only'}})
        raw_ids = {c['context_id'] for c in self.bundle.get('source_record', {}).get('contexts', self.all_contexts)}
        for cid in details.get('reference_container_ids', []):
            if cid in raw_ids:
                used.append({'resource_id': cid, 'view': 'geometry', 'use_scope':
                    {'reason': reason, 'scope': 'bounded_reference_members_and_order', 'reference_chain': details.get('reference_chain')}})
        self.relations.append({'kind': kind, 'current_anchor': self.proposition(),
                               'context_evidence': evidence, 'details': d,
                               'used_source_views': used,
                               '_signature': signature})
        self.source_relation_traces = [dict(r, relation_kind=r['kind']) for r in self.traces()]

    def traces(self):
        return [{k: v for k, v in r.items() if k != '_signature'} for r in self.relations]

    def _pointer(self, pointer):
        value = self.bundle
        for key in pointer.strip('/').split('/'):
            key = key.replace('~1', '/').replace('~0', '~')
            value = value[int(key)] if isinstance(value, list) else value[key]
        return value

    def _event(self, rid, view, sha, view_sha, locator, scope):
        key = (rid, view, view_sha, canonical(locator), scope)
        if key not in self._read_keys:
            self._read_keys.add(key)
            self.source_view_events.append({'resource_id': rid, 'view': view,
                'source_sha256': sha, 'view_sha256': view_sha, 'locator_read': locator,
                'event_kind': 'actual_structured_json_scan', 'consumption_scope': scope})

    def _scan_source_views(self):
        def scan(value):
            # Traverse every field of the delivered structured view; no path is
            # opened and no picture is decoded. Normalized text is only indexed.
            if isinstance(value, dict):
                return {key: scan(item) for key, item in value.items()}
            if isinstance(value, list):
                return [scan(item) for item in value]
            if isinstance(value, str):
                norm(value)
            return value
        raw_ids = {c['context_id'] for c in self.bundle.get('source_record', {}).get('contexts', self.all_contexts)}
        for c in self.all_contexts:
            scan(c)
            origin = self.origins.get(c['context_id'], {})
            if (origin.get('origin_inventory_view') == 'text' and isinstance(c.get('text'), str)
                    and origin.get('origin_inventory_view_sha256') == digest(c['text'])):
                self._event(origin['origin_inventory_resource_id'], 'text', c['source_ref']['sha256'], digest(c['text']),
                    c['source_ref'].get('locator', {}), 'complete_exact_literal_text_resource; original_role_identity_parsed; no_pixels')
            if c['context_id'] not in raw_ids:
                continue
            ref = c['source_ref']
            fields = {k: c[k] for k in ('text', 'title', 'caption', 'headers', 'row_cells') if k in c}
            if fields:
                self._event(c['context_id'], 'text', ref['sha256'], digest(canonical(fields)),
                    ref.get('locator', {}), 'complete_CTX_text_fields_normalized; availability_does_not_establish_applicability')
            self._event(c['context_id'], 'geometry', ref['sha256'], digest(canonical(c.get('structure', {}))),
                ref.get('locator', {}), 'complete_CTX_structure_parsed; links_order_scope_and_roles_only')
        for field, prefix, view in (
                ('explicit_or_primary_source_resources', None, 'document_bundle'),
                ('preserved_historical_neutral_source_supplements', 'HISTORICALSOURCE-', 'text'),
                ('source_full_text_resources', 'FULLSOURCE-', 'text')):
            for obj_index, obj in enumerate(self.bundle.get(field, [])):
                scan(obj)
                # v13 may deliver an individual original paragraph in the
                # full-text list. Its inventory is the exact text view, not a
                # fabricated complete document payload view.
                if (field == 'source_full_text_resources' and isinstance(obj.get('text'), str)
                        and obj.get('text_sha256') == digest(obj['text']) and obj.get('source_resource_id')):
                    self._event(obj['source_resource_id'], 'text', obj['source_sha256'], obj['text_sha256'],
                        obj.get('source_locator', {}), 'complete_exact_original_paragraph_text; structured_locator_identity_parsed; no_whole_document_claim')
                    continue
                h = digest(canonical(obj))
                rid = prefix + h[:20] if prefix else obj['source_resource_id']
                scope = 'complete_structured_payload_text_geometry_identity_scan; no_asset_pixels; no_whole_source_applicability'
                if field == 'preserved_historical_neutral_source_supplements':
                    pointer = '/' + field + '/' + str(obj_index)
                    origin = next((o for o in self.origins.values() if o.get('source_bundle_pointer') == pointer), None)
                    if origin and origin.get('origin_inventory_view_sha256'):
                        # The reader deliberately removes administrative
                        # record_id, retaining the exact raw payload binding.
                        # No administrative identity enters relation matching.
                        h = origin['origin_inventory_view_sha256']
                        rid = origin['origin_inventory_resource_id']
                        scope = 'complete_semantic_text_geometry_source_identity_scan; raw_payload_binding_origin=verified_reader_origin_inventory; administrative_record_id_consumed_only_by_loader_for_finite_source_alignment_then_removed_before_classification; no_pixels_or_whole_source_applicability'
                sha = obj.get('source_sha256', obj.get('source_pdf_sha256', obj.get('snapshot_sha256')))
                self._event(rid, view, sha, h, obj.get('locator', {'document_resource_id': rid}),
                    scope)
                # Separate inventory views are actual text/geometry fields,
                # not a claim that the producer's image review was repeated.
                for item in obj.get('source_visual_text_resources', []):
                    self._event(item['source_resource_id'], 'text', sha, item['text_sha256'],
                        item.get('source_locator', {}), 'complete_literal_visual_text_resource; no_pixels')
                for item in obj.get('source_display_regions', []):
                    self._event(item['region_id'], 'geometry', item['source_sha256'], digest(canonical(item)),
                        {'physical_page': item['physical_page'], 'coordinate_system': item['coordinate_system'],
                         'bbox_points_xyxy': item['bbox_points_xyxy']},
                        'complete_supplied_display_region_geometry_structure; no_pixels; no_invented_operator')

    def _policy_role(self, c):
        role = c.get('structure', {}).get('source_role', c.get('structure', {}).get('role'))
        role = self.origins.get(c['context_id'], {}).get('role') or role
        return role not in {'example_cover_drug_name', 'example_cover_placeholder', 'example_subheading',
            'illustration_scope_notice', 'lower_slide_example', 'printed_page_number',
            'right_side_example', 'section_heading', 'source_attachment_identifier', 'toc_heading', 'toc_item'}

    def _used_views(self, cid, evidence, reason):
        origin = self.origins.get(cid)
        views = []
        raw_ids = {c['context_id'] for c in self.bundle.get('source_record', {}).get('contexts', self.all_contexts)}
        if cid in raw_ids:
            views.append({'resource_id': cid, 'view': 'text', 'use_scope':
                {'reason': reason, 'exact_anchor': evidence}})
        if origin:
            views.append({'resource_id': origin['origin_inventory_resource_id'],
                'view': origin['origin_inventory_view'], 'use_scope':
                {'reason': reason, 'source_bundle_pointer': origin['source_bundle_pointer'],
                 'source_resource_id': origin['source_resource_id'], 'exact_anchor': evidence,
                 'field_scope': 'selected_exact_text; not_whole_document_applicability'}})
        return views

    def _metadata(self, c):
        meta = dict(c.get('source_ref', {}).get('metadata', {}))
        origin = self.origins.get(c['context_id'])
        if not origin:
            return meta
        obj = self._pointer(origin['source_bundle_pointer'])
        meta.update({key: value for key, value in obj.items() if key != 'text'})
        parts = origin['source_bundle_pointer'].strip('/').split('/')
        if parts[0] in ('explicit_or_primary_source_resources', 'source_full_text_resources'):
            doc = self.bundle[parts[0]][int(parts[1])]
            meta.update({key: value for key, value in doc.items() if key not in
                ('source_texts', 'source_visual_text_resources', 'source_visual_frames', 'source_geometry', 'paragraphs')})
        meta.setdefault('source_title', meta.get('document_title', ''))
        meta.setdefault('source_document_kind', meta.get('document_kind', ''))
        meta.setdefault('policy_document_date', meta.get('explained_policy_document_date'))
        meta.setdefault('policy_document_number', meta.get('explained_policy_document_number'))
        return meta

    def _neutral_source(self, c):
        return c['kind'] in ('external_source', 'source_resource_text', 'historical_source_fragment') and self._policy_role(c)

    def _request(self, path, reference, missing, code, unknown_group=False):
        request = {'path': path, 'reference': reference, 'current_text': self.text,
            'missing': missing, 'stop_reason': code, 'dependency_status': 'stopped'}
        if unknown_group:
            request['affected_dimensions'] = ['S', 'E', 'Ec', 'I', 'F']
        if request not in self.material_requests:
            self.material_requests.append(request)
            self.source_requests.append(request.copy())

    def _edition_binding(self, source_sha, doc, reference=None):
        target = doc.get('source_sha256', doc.get('snapshot_sha256'))
        if source_sha == target:
            return {'established': True, 'binding': 'exact_same_snapshot', 'source_sha256': target}
        r = reference or {}
        title = doc.get('document_title', '')
        year = str(doc.get('document_year', ''))
        actual = r.get('target_title_and_year', '')
        established = (r.get('reference_source_sha256', r.get('unit_primary_source_sha256')) == source_sha
            and r.get('target_source_sha256') == target and 'same_edition' in
            str(r.get('binding_scope', r.get('literal_relation_type', '')))
            and bool(title and year and title in actual and year in actual))
        return {'established': bool(established), 'binding': 'evidenced_same_edition_title_year_reference' if established else 'edition_ambiguous',
            'source_sha256': target, 'source_title': title, 'source_year': year}

    def _complete_source_relations(self):
        if not self.bundle:
            return
        resource_contexts = {}
        for c in self.contexts:
            origin = self.origins.get(c['context_id'], {})
            rid = origin.get('source_resource_id') or c.get('structure', {}).get('source_paragraph_id')
            if rid:
                resource_contexts.setdefault(rid, c)
            resource_contexts.setdefault(c['context_id'], c)
        groups = []
        def walk(value, doc, pointer):
            if isinstance(value, dict):
                if 'parent_resource_id' in value and 'numbered_members' in value:
                    groups.append((value, doc, pointer))
                for key, item in value.items():
                    walk(item, doc, pointer + '/' + key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    walk(item, doc, pointer + '/' + str(i))
        for i, doc in enumerate(self.bundle.get('explicit_or_primary_source_resources', [])):
            walk(doc.get('source_geometry', {}), doc, f'/explicit_or_primary_source_resources/{i}/source_geometry')
        self._source_groups = groups
        self._resource_contexts = resource_contexts
        # A current numbered member obtains only its own shared predicate.
        # Reading the complete group does not transfer sibling assertions.
        for group, doc, pointer in groups:
            members = group.get('numbered_members', [])
            cs = [resource_contexts.get(rid) for rid in members]
            if any(c and norm(c.get('text', '')) == self.norm for c in cs):
                full = self._group_evidence(group, doc, pointer, required=True)
                if full:
                    parent = resource_contexts[group['parent_resource_id']]
                    self._add('parent_predicate', [self._quote(parent, '当前编号成员的同源共享谓词')],
                        '当前成员仅承接完整组的共享谓词，不承接其他成员', relation_subtype='complete_numbered_member_parent',
                        source_group_pointer=pointer, group_operator=group['operator'], group_member_ids=members)
                    self._add('source_group_scope', full, '完整编号与原始限定/例外只作组范围证明，不自动传递兄弟条件',
                        source_group_pointer=pointer, group_operator=group['operator'], dimension_inheritance=False)
        candidates = [(self.text, self.unit.get('source_ref', {}).get('sha256'), None)]
        for relation in list(self.relations):
            if relation['kind'] in ('substantive_list', 'cited_standard'):
                candidates.extend((e['text'], e['source_ref']['sha256'], e['context_id']) for e in relation['context_evidence'])
        visited = set()
        # Only reference clauses reached from current evidence may add a group;
        # newly selected group clauses can explicitly reference another group.
        while candidates:
            text, sha, cid = candidates.pop(0)
            references = list(self.bundle.get('source_reference_index', []))
            # A selected condition may itself expressly cite another named
            # condition in this exact snapshot. The actual heading names, not
            # administrative group keys, supply the possible literal targets.
            for group, doc, pointer in groups:
                parent = resource_contexts.get(group['parent_resource_id'])
                if not parent or doc.get('source_sha256', doc.get('snapshot_sha256')) != sha:
                    continue
                for heading in parent.get('structure', {}).get('heading_path', []):
                    name = re.sub(r'^规则[一二三四五六七八九十0-9]+[：:、.．\s]*', '', str(heading))
                    if name != heading and name and name in text:
                        references.append({'source_field': 'text', 'source_field_text_sha256': digest(text),
                            'literal_reference': name, 'resource_id': doc['source_resource_id'],
                            'reference_source_sha256': sha, 'target_source_sha256': sha,
                            'literal_relation_type': 'actual_selected_clause_same_snapshot_named_conditions'})
            for reference in references:
                literal = reference.get('literal_reference', '')
                if not literal or literal not in text or reference.get('source_field_text_sha256') != digest(text):
                    continue
                if reference.get('source_field') != 'text':
                    continue
                # Bare mention/application or a numeric calculation rule does
                # not assert an entire eligibility dependency.
                n = norm(text)
                if not re.search(r'(?:符合|满足)[^。；;]{0,24}' + re.escape(norm(literal)) + r'[^。；;]{0,8}条件', n):
                    continue
                key = (sha, literal)
                if key in visited:
                    continue
                visited.add(key)
                options = []
                for group, doc, pointer in groups:
                    parent = resource_contexts.get(group['parent_resource_id'])
                    if not parent:
                        continue
                    headings = parent.get('structure', {}).get('heading_path', [])
                    if literal not in parent.get('text', '') and not any(literal in str(h) for h in headings):
                        continue
                    # A named rule's conditions identify its direct condition
                    # section, not an embedded later adjustment group.
                    if not headings or not any(re.search(r'^[一1][、.．]?条件$', norm(str(h))) for h in headings):
                        continue
                    if doc.get('source_resource_id') != reference.get('resource_id'):
                        continue
                    options.append((group, doc, pointer))
                if len(options) != 1:
                    self._request('cited_standard', literal, '确指条件组缺失或无法唯一闭合', 'required_reference_unresolved', True)
                    continue
                group, doc, pointer = options[0]
                binding = self._edition_binding(sha, doc, reference)
                if not binding['established']:
                    self._request('cited_standard', literal, '确指条件与来源同版关系未建立', 'reference_edition_ambiguous', True)
                    continue
                full = self._group_evidence(group, doc, pointer, required=True)
                if full:
                    self._add('cited_standard', full, '当前资格谓词确指同版完整条件组，保留原编号、共享限定与例外，未继承全文',
                        relation_subtype='explicit_complete_numbered_condition_reference', reference_literal=literal,
                        source_group_pointer=pointer, group_operator=group['operator'], version_binding=binding,
                        reference_clause={'text': text, 'context_id': cid}, qualifier_exception_scope='exact_complete_selected_group')
                    candidates.extend((e['text'], e['source_ref']['sha256'], e['context_id']) for e in full)

    def _group_evidence(self, group, doc, pointer, required):
        parent = self._resource_contexts.get(group.get('parent_resource_id'))
        ids = group.get('numbered_members', [])
        expanded = []
        for index, rid in enumerate(ids, 1):
            expanded.append(rid)
            expanded.extend(group.get(f'member{index}_submembers', []))
        sha = doc.get('source_sha256', doc.get('snapshot_sha256'))
        cs = [self._resource_contexts.get(rid) for rid in expanded]
        if (not parent or not ids or len(expanded) != len(set(expanded)) or
                any(not c or not c.get('text') or c['source_ref']['sha256'] != sha for c in [parent] + cs)):
            self._request('cited_standard', pointer, '完整条件组的父谓词/编号成员/子项原文或同源绑定缺失', 'missing_required_source', True)
            return []
        printed = group.get('operator_printed', '')
        operator = group.get('operator')
        actual = 'any' if '之一' in printed else 'all' if '同时' in printed else None
        if not printed or printed not in parent['text'] or actual != operator:
            self._request('cited_standard', pointer, '条件组没有可见且一致的原印逻辑操作文字', 'source_operator_not_visible', True)
            return []
        return [self._quote(c, '当前确指完整编号条件及原限定/排除范围') for c in [parent] + cs]

    def _parents(self):
        # Only direct supplied parent clauses; no sibling or preceding paragraph.
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts
                           if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            t = c.get('text', '')
            same_source = not current_sources or c.get('source_ref', {}).get('sha256') in current_sources
            if c['kind'] == 'parent_paragraph' and same_source and re.search(INTRO, norm(t)):
                self._add('parent_predicate', [self._quote(c, '直接父谓词补全本成员')],
                          '当前成员与来源包直接父句的共同谓词组合；不继承兄弟内容',
                          shared_predicate=t, member_text=self.text)

    def _lists(self):
        if not re.search(INTRO, self.norm) or not re.search(SUBSTANTIVE, self.norm):
            return
        groups = []
        for c in self.contexts:
            st = c.get('structure', {})
            if c['kind'] in ('ordered_list', 'supplemental_group', 'source_paragraph'):
                ids = []
                for g in st.get('child_groups', []):
                    if g.get('position') in ('contexts', 'members', 'ordered_members'):
                        ids.extend(g.get('ordered_context_ids', []))
                if ids:
                    groups.append([self.by_id[i] for i in ids])
        # Some source graph versions record only a common parent pointer.
        by_parent = {}
        for c in self.contexts:
            if c['kind'] == 'ordered_members':
                p = c.get('structure', {}).get('parent_context_id')
                if p:
                    by_parent.setdefault(p, []).append(c)
        groups.extend(sorted(g, key=lambda c: c.get('structure', {}).get('sequence_index', 0))
                      for g in by_parent.values())
        found = False
        for group in groups:
            matches = [i for i, c in enumerate(group) if norm(c.get('text', '')) == self.norm]
            if not matches:
                continue
            start = matches[0]
            members = []
            for c in group[start + 1:]:
                if c['kind'] in ('boundary', 'following_heading'):
                    break
                if c.get('text'):
                    members.append(c)
            if not members:
                continue
            found = True
            self._add('substantive_list', [self._quote(c, '当前实质总领确指的完整成员范围')
                                          for c in members],
                      '当前有实质条件/内容要求，按来源有序容器读取全部成员',
                      member_texts=[c['text'] for c in members], shared_predicate=self.text)
        if not found:
            # No request for a merely potentially relevant background list.
            self.material_requests.append({'path': 'substantive_list',
                                           'reference': self.text,
                                           'missing': '当前确指的完整成员范围未在结构图闭合提供'})

    def _validated_current_list(self):
        """One complete local list, deduplicating aliases of identical sources."""
        current = self._current_source()
        if (not current or not same_component(self.unit,current)
                or current['source_ref'].get('sha256') != self.unit.get('source_ref',{}).get('sha256')):
            return None
        sha = current['source_ref']['sha256']
        candidates = {}
        for root in self.contexts:
            if root['kind']!='ordered_list' or root['source_ref'].get('sha256')!=sha or not same_component(current,root):
                continue
            groups = root.get('structure',{}).get('child_groups',[])
            ids = [cid for g in groups if g.get('position')=='contexts' for cid in g.get('ordered_context_ids',[])]
            bounds = [cid for g in groups if g.get('position')=='structure_boundary' for cid in g.get('ordered_context_ids',[])]
            if len(ids)<2 or len(ids)!=len(set(ids)) or len(bounds)!=1:
                continue
            members = [self.by_id.get(cid) for cid in ids]
            boundary = self.by_id.get(bounds[0])
            if not boundary or any(not c for c in members):
                continue
            if (any(c['kind']!='ordered_members' or c['source_ref'].get('sha256')!=sha
                    or not same_component(current,c) or c.get('structure',{}).get('parent_context_id')!=root['context_id']
                    or c.get('structure',{}).get('sequence_index')!=i for i,c in enumerate(members))
                    or norm(members[0].get('text',''))!=self.norm):
                continue
            st=boundary.get('structure',{})
            paragraph_ids=[c.get('structure',{}).get('paragraph_id') for c in members]
            next_ids=st.get('text_child_context_ids',[])
            if (not all(paragraph_ids) or len(set(paragraph_ids))!=len(paragraph_ids)
                    or boundary['kind']!='boundary_container' or boundary['source_ref'].get('sha256')!=sha
                    or not same_component(current,boundary) or st.get('parent_context_id')!=root['context_id']
                    or st.get('first_paragraph')!=paragraph_ids[0] or st.get('last_paragraph')!=paragraph_ids[-1]
                    or len(next_ids)!=1):
                continue
            nxt=self.by_id.get(next_ids[0])
            if (not nxt or nxt['kind']!='boundary' or nxt['source_ref'].get('sha256')!=sha
                    or not same_component(current,nxt) or nxt.get('structure',{}).get('parent_context_id')!=boundary['context_id']
                    or nxt.get('structure',{}).get('paragraph_id')!=st.get('next_paragraph_id')):
                continue
            numbers=[]
            for c in members[1:]:
                m=re.match(r'(?:[（(]('+ORDINAL+r')[）)]|('+ORDINAL+r')[.．、])',norm(c['text']))
                numbers.append(ordinal_number(next(x for x in m.groups() if x is not None)) if m else None)
            if numbers!=list(range(1,len(members))):
                continue
            key=(sha,tuple(paragraph_ids),tuple(norm(c['text']) for c in members))
            candidates.setdefault(key,{'members':members[1:],'root':root,'boundary':boundary,'next':nxt,
                                      'source_sha256':sha,'paragraph_ids':paragraph_ids})
        return next(iter(candidates.values())) if len(candidates)==1 else None

    def _operative_review_list(self):
        """An actual drug/prescription audit consumes its complete checklist."""
        action=re.search(r'(?:应当|应|必须)(?:审核|核验|审查)(?:以下|下列)(?:项目|内容|事项)',self.norm)
        body=re.sub(r'^(?:[（(]'+ORDINAL+r'[）)]|第'+ORDINAL+r'条)','',self.norm)
        if not action or not re.match(r'(?:中药饮片处方|药品处方|药物处方|处方|药品|用药)[^。；;]{0,25}(?:应当|应|必须)(?:审核|核验|审查)',body):
            return
        group=self._validated_current_list()
        if not group:
            self._request('substantive_list',self.text,'当前实际审核要求的完整同源清单及边界未核明','required_complete_review_list_unresolved')
            return
        self._add('substantive_list',[self._quote(c,'当前处方/用药审核实际要求的完整有界项目') for c in group['members']],
            '当前实质审核谓词指向完整项目；同一物理清单的重复图别名只消费一次，纯目录引导不触发',
            relation_subtype='bounded_operative_review_checklist',
            shared_predicate=self.text,member_texts=[c['text'] for c in group['members']],
            current_review_anchor=self.current_anchor(action.start(),action.end()),
            scope_binding={'source_sha256':group['source_sha256'],'context_ids':[c['context_id'] for c in group['members']],
                           'ordered_paragraph_ids':group['paragraph_ids'],'boundary_context_id':group['boundary']['context_id']},
            duplicate_source_aliases_deduplicated=True)

    def _named_support_missing_scope(self):
        """Expose missing programme scope without importing programme topics."""
        current=self._current_source()
        if not current or not same_component(self.unit,current):return
        sha=current['source_ref']['sha256']
        governing=None
        head=re.search(r'对纳入([^。；;，,]{3,28}(?:程序|计划|试点))的[^。；;]{0,25}给予以下政策支持[:：]$',self.norm)
        if head:
            group=self._validated_current_list()
            if not group:return
            governing=self.proposition();name=head.group(1)
        elif re.fullmatch(r'[（(]一[）)]药品上市许可申请的审评时限为'+ORDINAL+r'日[；;。]?',self.norm):
            parents=[c for c in self.contexts if c['kind']=='preceding_paragraph' and c['source_ref'].get('sha256')==sha
                     and same_component(current,c) and re.search(r'对纳入([^。；;，,]{3,28}(?:程序|计划|试点))的[^。；;]{0,25}给予以下政策支持[:：]$',norm(c.get('text','')))]
            if len(parents)!=1:return
            parent=parents[0]
            m=re.search(r'对纳入([^。；;，,]{3,28}(?:程序|计划|试点))的',norm(parent['text']))
            name=m.group(1);governing=self._quote(parent,'紧邻实质支持总领与明确第一项时限组成直接父谓词关系')
            self._add('parent_predicate',[governing],
                '当前明确编号第一项实际时限，直接承接紧邻同源支持总领；仅补对象及支持谓词，不继承其他时限或支持内容',
                relation_subtype='bounded_first_support_deadline_member',shared_predicate=parent['text'],member_text=self.text)
        if not governing:return
        # These inputs declare an original file but do not deliver its programme
        # scope as a text resource. A filename or a programme title is not it.
        if any(c['kind'] in {'source_textleaf','source_resource_text','source_paragraph'} and c['source_ref'].get('sha256')==sha for c in self.contexts):
            return
        self.material_requests.append({'path':'named_mechanism','reference':name,
            'missing':'当前实际支持所指程序的同版完整适用对象/条件未作为共同文字材料提供，不能由程序名称推创新或需要缺口',
            'affected_dimensions':['I','F'],'dependency_status':'stopped',
            'current_support_anchor':governing,
            'declared_original_source_pointers':[{'snapshot':d.get('snapshot'),'source_sha256':d.get('source_sha256')} for d in self.bundle.get('source_documents',[]) if d.get('source_sha256')==sha]})

    def _trial_admission_support(self):
        """Actual admission to a named trial, with finite source-defined rights."""
        # A proposed admission/publication and an already-included status do
        # not grant the support. The final normative branch must do so itself.
        action=re.search(r'(?:公示无异议的品种|符合条件的品种)\s*(?:最终将|即|予以)纳入[“「]([^”」]{2,35})[”」]试点(?:工作|计划|项目)',self.norm)
        current=self._current_source()
        if not action or not current or not same_component(self.unit,current):return
        if re.search(r'栏目|标点|这一表述|仅(?:记录|公布)|不予纳入|未予纳入',self.norm):return
        if action.start()!=0 and not re.match(r'经评价拟同意纳入[“「][^”」]{2,35}[”」]试点(?:工作|计划|项目)后',self.norm):return
        if len([c for c in self.contexts if c['kind']=='paragraph' and self.norm in norm(c.get('text',''))])!=1:return
        name=action.group(1);sha=current['source_ref']['sha256']
        if sha!=self.unit.get('source_ref',{}).get('sha256'):return
        options=[]
        for di,doc in enumerate(self.bundle.get('source_full_text_resources',[])):
            if doc.get('source_sha256',doc.get('source_pdf_sha256'))!=sha or not same_component(current,doc):continue
            paras=doc.get('paragraphs',[])
            if not paras:continue
            cs=[]
            # Resolve each paragraph by its exact pointer and source identity,
            # not by a remembered programme name or a resource ID prefix.
            for pi,para in enumerate(paras):
                pointer=f'/source_full_text_resources/{di}/paragraphs/{pi}'
                matches=[c for c in self.contexts if self.origins.get(c['context_id'],{}).get('source_bundle_pointer')==pointer
                         and c['source_ref'].get('sha256')==sha and same_component(current,c)
                         and same_component(current,para) and same_component(doc,para) and same_component(c,para)
                         and para.get('source_ref',{}).get('sha256',sha)==sha
                         and c.get('text')==para.get('text')]
                cs.append(matches[0] if len(matches)==1 else None)
            current_matches=[i for i,c in enumerate(cs) if c and norm(c['text'])==self.norm]
            services=[c for c in cs if c and name in norm(c['text']) and re.search(r'核心内容',norm(c['text']))
                      and re.search(r'研发早期',norm(c['text'])) and re.search(r'开发计划进行讨论',norm(c['text']))
                      and re.search(r'当品种被纳入试点项目后',norm(c['text']))
                      and re.search(r'当品种被纳入试点项目后[^。]{0,100}实施框架(?:中|内)的相关内容[^。]{0,30}[；;]实施框架将成为该品种[^。]{0,50}档案[，,]便于在整个开发过程中[^。]{0,30}沟通交流',norm(c['text']))
                      and not re.search(r'不提供|不得[^。]{0,30}沟通交流|不能[^。]{0,30}讨论|仅作为示例',norm(c['text']))]
            starts=[i for i,c in enumerate(cs) if c and re.fullmatch(r'1[.．]1\s*申请资格',norm(c['text']))]
            stops=[i for i,c in enumerate(cs) if c and re.fullmatch(r'1[.．]2\s*纳入标准',norm(c['text']))]
            if len(current_matches)!=1 or len(services)!=1 or len(starts)!=1 or len(stops)!=1 or starts[0]>=stops[0]:continue
            group=cs[starts[0]+1:stops[0]]
            if any(c is None for c in group):continue
            texts=[norm(c['text']) for c in group]
            if (not group or name not in texts[0] or not re.search(r'需同时满足以下条件',texts[0])
                    or re.search(r'不适用(?:于)?创新药|不包括创新药|非创新药|不属于创新|仅适用于仿制药',''.join(texts))):continue
            numbered=[re.match(r'[（(]('+ORDINAL+r')[）)]',t) for t in texts]
            numbers=[ordinal_number(m.group(1)) for m in numbered if m]
            if numbers!=[1,2,3]:continue
            innovation=[c for c in group if all(x in c['text'] for x in ['①','②','③']) and re.search(r'首创新药[^。]{0,60}新作用机制/新靶点药物',norm(c['text']))
                        and re.search(r'或2在境内尚无药物获批',norm(c['text'])) and re.search(r'或3与境内外现有治疗手段相比',norm(c['text']))]
            stage=[c for c in group if re.search(r'早期临床研发阶段',norm(c['text'])) and re.search(r'尚未推进至关键研究阶段',norm(c['text']))
                   and re.search(r'且2境内外',norm(c['text'])) and re.search(r'除外',norm(c['text']))]
            if len(innovation)!=1 or len(stage)!=1:continue
            options.append((doc,cs,current_matches[0],services[0],group,innovation[0],stage[0]))
        if len(options)!=1:
            self.material_requests.append({'path':'named_mechanism','reference':name,
                'missing':'当前实际试点纳入缺少唯一同源服务定义或完整资格共同条件、OR分支及例外',
                'affected_dimensions':['I','F'],'dependency_status':'stopped'})
            return
        doc,cs,index,service,group,innovation,stage=options[0]
        sq=[self._quote(service,'同一具名试点明确的早期研发讨论及纳入后持续技术沟通权利')]
        eq=[self._quote(c,'实际授予同一试点机会所用的完整资格共同条件、OR及例外') for c in group]
        # Keep the full OR and its qualifiers in eligibility_quotes. Roles only
        # receive operative branches; an expressly excluded branch grants no
        # opportunity even though its needs/innovation words remain in scope.
        raw=innovation['text']
        markers=[raw.index(symbol) for symbol in ['①','②','③']]+[len(raw)]
        active=[];excluded=[]
        for a,b in zip(markers,markers[1:]):
            branch=raw[a:b]
            excluded_branch=re.search(r'(?:此|本|该)分支[^。；;]{0,16}(?:不在[^。；;]{0,20}(?:纳入|适用)范围|不适用|不予纳入|不属于[^。；;]{0,15}范围)|(?:不包括|不纳入|不适用于|排除)[^。；;]{0,12}(?:此|本|该)分支',norm(branch))
            quote=self._quote(innovation,'完整资格中的明确排除分支' if excluded_branch else '完整资格中仍生效的OR分支',(a,b))
            (excluded if excluded_branch else active).append(quote)
        iq=[q for q in active if re.search(r'(?<!非)(?:首创新药|创新药)|新作用机制/新靶点',norm(q['text']))]
        nq=[q for q in active if re.search(r'境内尚无药物获批[^。；;]{0,20}适应症',norm(q['text']))]
        rq=[self._quote(stage,'共同早期临床研发限定及其并列条件和例外')]
        self._add('named_mechanism',sq+eq,
            '当前公示无异议后实际授予同一试点资格，使用其早期创新研发技术讨论及持续沟通；资格完整OR中的无获批治疗分支只支撑该分支的需要—机会关系',
            relation_subtype='bounded_trial_admission_support',programme_name=name,
            content='\n'.join(q['text'] for q in sq+eq),current_admission_anchor=self.current_anchor(action.start(),action.end()),
            support_quotes=sq,eligibility_quotes=eq,innovation_eligible_branches=iq,need_eligible_branches=nq,research_stage_quotes=rq,
            excluded_eligibility_branches=excluded,
            scope_binding={'source_sha256':sha,'context_ids':[q['context_id'] for q in sq+eq],
                           'current_source_context_id':cs[index]['context_id'],'first_eligibility_context_id':group[0]['context_id'],
                           'last_eligibility_context_id':group[-1]['context_id'],'source_resource_id':doc['source_resource_id']},
            version_binding={'established':True,'binding':'same_source_exact_ordered_paragraphs_and_named_mechanism','source_sha256':sha},
            eligibility_or_and_exceptions_preserved=True,all_participants_have_unmet_need=False,
            admission_is_current_action_not_status=True)

    def _local_operations(self):
        # Current data/design reference may use the same operation's definition
        # in the prefix of its own original paragraph. No neighboring paragraph
        # or guideline scope can supply product limitations.
        operations = re.findall(r'([\u4e00-\u9fff]{2})操作', self.norm)
        if not operations or not re.search(r'参考.{0,8}数据|操作.{0,12}数据|数据.{0,12}(?:改善|设计|开发)', self.norm):
            return
        for c in self.contexts:
            raw = c.get('text', '')
            if c['kind'] != 'paragraph' or self.text not in raw:
                continue
            prefix_end = raw.find(self.text)
            for a, b in sentence_spans(raw[:prefix_end]):
                part = norm(raw[a:b])
                shifts = re.findall(r'另一(?:种|个)?药|其他药|对照药|其他品种|另一品种|另一个项目', part)
                if shifts and not all(shift in self.norm for shift in shifts):
                    continue
                if (any(op in part for op in operations)
                        and re.search(r'困难|障碍|不便|限制|灵活性.{0,40}操作.{0,10}影响|影响.{0,30}操作', part)):
                    self._add('parent_predicate', [self._quote(c, '当前明确操作数据所指的同段操作限制', (a, b))],
                              '当前操作数据—改动关系明确承接同段同一操作限制，不使用指南整体宗旨',
                              shared_predicate=raw[a:b], member_text=self.text,
                              relation_subtype='same_paragraph_operation_reference',
                              operation_terms=operations)

    def _primary_standard_group(self, candidates, family):
        """Complete one expressly used standard from exact primary literal leaves.

        This is not a full-file applicability rule. A named programme, structural
        seed, current operative norm, same-snapshot current occurrence, contiguous
        literal leaf coordinates and one complete bounded group must all agree.
        """
        primary = self.unit.get('source_ref', {}).get('sha256')
        leaves = [c for c in self.contexts if c['kind'] == 'source_textleaf'
                  and c.get('source_ref', {}).get('sha256') == primary]
        if not leaves:
            return None
        intervals = []
        for c in leaves:
            bounds = c['source_ref'].get('locator', {}).get('unicode_code_point_interval_half_open')
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(type(v) is not int for v in bounds)
                    or bounds[1] - bounds[0] != len(c.get('text', ''))):
                return None
            intervals.append((bounds[0], bounds[1], c))
        intervals.sort(key=lambda z: z[0])
        if intervals[0][0] != 0 or any(a[1] != b[0] for a,b in zip(intervals, intervals[1:])):
            return None
        raw = ''.join(c['text'] for _,_,c in intervals)
        # A line-shaped named programme heading, not a title mentioned in prose.
        titles = []
        title_re = r'(?m)^[ \t]*(?P<name>[\u4e00-\u9fff]{2,30}(?:程序|计划|通道|试点))(?:[（(][^）)\n]{1,12}[）)])?[ \t]*$'
        for m in re.finditer(title_re, raw):
            name = re.sub(r'审评工作|审评|工作', '', norm(m.group('name')))
            if len(name) >= 6 and name in self.norm and any(name in norm(c['text']) for c in candidates):
                titles.append((m, name))
        if len(titles) != 1:
            return None
        title, name = titles[0]
        next_titles = [m.start() for m in re.finditer(title_re, raw) if m.start() > title.start()]
        end = min(next_titles) if next_titles else len(raw)
        block = raw[title.end():end]
        if self.norm not in norm(block) or not any(norm(c['text']) in norm(block) for c in candidates):
            return None
        if family == 'termination':
            header_re = r'(?m)^[ \t]*[（(][一二三四五六七八九十]+[）)][ \t]*(?:终止|取消)(?:程序|资格|条件|情形)(?=[ \t]*(?:$|[。．.:：]))'
            boundary_re = r'(?m)^[ \t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])'
        else:
            header_re = r'(?m)^[ \t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])[ \t]*(?:适用范围和适用条件|适用条件|纳入条件|适用标准|纳入标准|资格条件)(?=[ \t]*(?:$|[。．.:：]))'
            boundary_re = r'(?m)^[ \t]*[一二三四五六七八九十]+、'
        heads = list(re.finditer(header_re, block))
        if family != 'termination':
            outer = [h for h in heads if re.match(r'^[ \t]*[一二三四五六七八九十]+、', h.group())]
            if outer:
                heads = outer
        if len(heads) != 1:
            return None
        head = heads[0]
        stops = [m.start() for m in re.finditer(boundary_re, block) if m.start() > head.start()]
        ga = title.end() + head.start()
        gb = title.end() + (min(stops) if stops else len(block))
        # A visibly introduced full enumerated substantive group is required.
        group = norm(raw[ga:gb])
        intro = (r'(?:以下|下列).{0,12}(?:情形|条件).{0,24}(?:终止|取消)|(?:终止|取消).{0,24}(?:以下|下列).{0,12}(?:情形|条件)'
                 if family == 'termination' else r'(?:同时满足|符合|满足).{0,16}(?:以下|下列).{0,12}(?:条件|标准)|(?:以下|下列).{0,12}(?:条件|标准)')
        if not re.search(intro, group) or not re.search(r'(?m)^[ \t]*1[.、．]', raw[ga:gb]):
            return None
        evidence = []
        selected = []
        for a,b,c in intervals:
            for lo,hi,role in [(title.start(),title.end(),'named_programme_heading'), (ga,gb,'complete_' + family + '_standard_group')]:
                x,y = max(a,lo),min(b,hi)
                if x < y:
                    evidence.append(self._quote(c, '同源确指操作性标准的有限完整组及名称', (x-a,y-a)))
                    selected.append({'context_id': c['context_id'], 'role': role,
                                     'leaf_span': [x-a,y-a], 'snapshot_span': [x,y]})
        return {'evidence': evidence, 'standard_text': raw[ga:gb],
                'programme_name': name, 'standard_family': family,
                'source_sha256': primary, 'selected_group_snapshot_span': [ga,gb],
                'programme_block_snapshot_span': [title.end(),end],
                'selected_leaf_spans': selected,
                'not_whole_file_inheritance': True}

    def _bounded_primary_support_roles(self, completion, candidates):
        """Keep object/support/withdrawal roles beside, not inside, standards.

        Activation is a real current qualification review with a normative
        consequence. The already closed same-source programme is the boundary;
        no purpose, status, paperwork or unrelated mechanism is inherited.
        """
        if (not re.search(r'(?:资格|条件).{0,12}(?:审核|核验)|(?:审核|核验).{0,12}(?:资格|条件)', self.norm)
                or not re.search(r'终止|取消|撤回|限制|维持', self.norm)):
            return
        primary = completion['source_sha256']
        name = completion['programme_name']
        intervals = []
        for c in self.contexts:
            if c['kind'] == 'source_textleaf' and c['source_ref'].get('sha256') == primary:
                a,b = c['source_ref']['locator']['unicode_code_point_interval_half_open']
                intervals.append((a,b,c))
        intervals.sort(key=lambda item:item[0])
        raw = ''.join(c['text'] for _,_,c in intervals)
        lo,hi = completion['programme_block_snapshot_span']
        block = raw[lo:hi]
        view,offsets = matching_view(block)
        objects = []
        for c in candidates:
            seed = norm(c.get('text',''))
            if (not seed or name not in seed or not re.search(r'药物|药品',seed)
                    or not re.search(r'申请适用|可以申请|可申请',seed)):
                continue
            occurrences = [m for m in re.finditer(re.escape(seed),view)]
            if len(occurrences) == 1:
                a,b = raw_span(offsets,occurrences[0].start(),occurrences[0].end())
                objects.append((lo+a,lo+b))
        objects = list(dict.fromkeys(objects))
        if len(objects) != 1:
            return
        supports,withdrawals = [],[]
        for a,b in sentence_spans(block):
            part = norm(block[a:b])
            if name not in part:
                continue
            if (re.search(r'(?:对|对于|针对).{0,80}'+re.escape(name),part)
                    and re.search(r'药物|药品|研发',part)
                    and re.search(r'优先配置.{0,15}资源.{0,20}(?:沟通交流|技术服务|研究方案反馈|研发)',part)
                    and re.search(r'研发|研制|临床试验',part)
                    and not re.search(r'为了|制定|印发|仅.*(?:形式|渠道)',part)):
                supports.append((lo+a,lo+b))
            if (re.search(r'自(?:终止|取消|撤回)之日起',part)
                    and re.search(r'不再优先(?:安排|提供).{0,20}(?:沟通交流|技术服务|研究方案反馈)',part)):
                withdrawals.append((lo+a,lo+b))
        if len(supports) != 1 or len(withdrawals) != 1:
            return
        services = r'沟通交流|技术服务|研究方案反馈'
        shared = set(re.findall(services,norm(raw[supports[0][0]:supports[0][1]]))) & set(re.findall(services,norm(raw[withdrawals[0][0]:withdrawals[0][1]])))
        if not shared:
            return
        evidence,roles = [],[]
        def add_role(role, bounds, inherited=True):
            for start,end in bounds:
                for a,b,c in intervals:
                    x,y = max(a,start),min(b,end)
                    if x < y:
                        quote = self._quote(c,'当前资格审核/撤回承接的同版有限'+role,(x-a,y-a))
                        evidence.append(quote)
                        roles.append({'role':role,'source_snapshot_span':[x,y],
                                      'source_leaf_span':[x-a,y-a],'evidence':quote,
                                      'inherited_as_support_definition':inherited})
        add_role('object_and_eligibility_definition',objects)
        add_role('priority_research_support',supports)
        add_role('withdrawal_direct_mechanism',withdrawals)
        qualification = completion if completion['standard_family']=='admission' else self._primary_standard_group(candidates,'admission')
        if qualification:
            add_role('qualification_standard',[qualification['selected_group_snapshot_span']],False)
        content = '\n'.join(r['evidence']['text'] for r in roles if r['inherited_as_support_definition'])
        self._add('named_mechanism',evidence,
                  '当前资格审核及规范性限制/撤回直接控制同一程序优先研发机会；对象、可用支持、撤回后果与完整标准分别保留，不复制宗旨或其他机制',
                  content=content, relation_subtype='bounded_primary_qualification_support_roles',
                  mechanism_name=name, object_definition=raw[objects[0][0]:objects[0][1]],
                  direct_mechanism=raw[supports[0][0]:supports[0][1]],
                  withdrawal_mechanism=raw[withdrawals[0][0]:withdrawals[0][1]],
                  current_qualification_bridge=self.proposition(), source_roles=roles,
                  qualification_standard_snapshot_span=qualification['selected_group_snapshot_span'] if qualification else None,
                  termination_standard_snapshot_span=completion['selected_group_snapshot_span'] if completion['standard_family']=='termination' else None,
                  version_binding={'established':True,'binding':'same_primary_snapshot_closed_programme','source_sha256':primary},
                  direct_mapping=True, not_whole_programme_inheritance=True,
                  standards_not_inherited_as_support_definition=True)

    def _standards(self):
        operative = re.search(r'(?:审核|核验|满足|符合|不符合).{0,20}(?:条件|资格|标准)|(?:条件|资格).{0,25}(?:审核|终止|取消)', self.norm)
        consequence = re.search(r'应当|可以|可申请|予以|终止|取消|限制|维持|授予', self.norm)
        if not operative or not consequence:
            return
        programs = re.findall(PROGRAM, self.norm)
        candidates = []
        related = set()
        for c in self.contexts:
            if c['kind'] == 'structural_relation':
                related.update(c.get('structure', {}).get('related_context_ids', []))
        for c in self.contexts:
            t = norm(c.get('text', ''))
            if c['kind'] != 'source_paragraph' or not t:
                continue
            shared = [p for p in programs if p in t]
            if not shared:
                for p in programs:
                    for size in range(len(p), 5, -1):
                        if p[-size:] in t:
                            shared.append(p[-size:]); break
            if shared and c['context_id'] in related and re.search(r'用于|符合|条件|申请|适用', t):
                candidates.append(c)
        completion = None
        # Neither a status report nor a material-format step activates this path.
        normative = re.search(r'应当|应予|必须|可以|可申请|予以', self.norm)
        action = re.search(r'终止|取消|限制|维持|授予|申请适用|审核.{0,12}资格|资格.{0,12}审核', self.norm)
        family = None
        if re.search(r'(?:符合|满足).{0,16}(?:终止|取消).{0,35}(?:情形|条件)', self.norm):
            family = 'termination'
        elif re.search(r'(?:纳入|适用)(?:实质)?(?:条件|标准)|资格.{0,12}审核|审核.{0,12}资格', self.norm):
            family = 'admission'
        if candidates and normative and action and family:
            same_source = [c for c in candidates if c['source_ref'].get('sha256') == self.unit.get('source_ref', {}).get('sha256')]
            completion = self._primary_standard_group(same_source, family)
        if completion:
            details = {k:v for k,v in completion.items() if k != 'evidence'}
            self._add('cited_standard', completion['evidence'],
                      '当前确指标准核验或标准—资格后果；同一原件具名程序内的完整适用/终止组，保留并列条件，不复制其他节或其他程序',
                      action_scope='standard_review_or_eligibility_consequence',
                      resolution_path='primary_literal_complete_operative_standard', **details)
            self._bounded_primary_support_roles(completion, same_source)
        elif candidates:
            self._add('cited_standard', [self._quote(c, '同源操作性标准的原有短语境') for c in candidates],
                      '当前以标准核验/资格决定制度适用或终止；原有确指语境范围保留',
                      standard_text='\n'.join(c['text'] for c in candidates),
                      action_scope='standard_review_or_eligibility_consequence')
        elif re.search(r'(?:上述|该|纳入)(?:实质)?(?:条件|标准)', self.norm):
            self.material_requests.append({'path': 'cited_standard', 'reference': self.text,
                                           'missing': '确指资格/标准与待遇后果的同版标准原文缺失'})

    def _operative_value_definition(self):
        """An operative clinical-value criterion consumes its complete definition.

        A programme name alone does not activate this path. The current clause
        must use a comparative value as an application/admission condition, its
        structural seed must be the same primary source, and the bounded full
        condition group must explicitly define that very expression.
        """
        criterion = re.search(r'明显临床优势|显著临床优势|明显治疗优势|显著治疗优势', self.norm)
        application = re.search(r'(?:可以|可|允许).{0,100}申请适用([^。；;，,]{4,28}(?:程序|计划|通道|试点))', self.norm)
        if not criterion or not application or not re.search(r'药品|药物|新药', self.norm):
            return
        clause_bound = any(m.start() <= criterion.start() and application.end() <= m.end()
                           for m in re.finditer(r'[^。；;]+', self.norm))
        between = self.norm[criterion.end():application.end()]
        if (not clause_bound or re.search(r'其他(?:药品|药物|产品)|另(?:一|外)[^，,]{0,10}(?:药品|药物|产品)', between)):
            return
        primary = self.unit.get('source_ref', {}).get('sha256')
        related = {cid for c in self.contexts if c['kind'] == 'structural_relation'
                   for cid in c.get('structure', {}).get('related_context_ids', [])}
        candidates = [c for c in self.contexts if c['kind'] == 'source_paragraph'
                      and c['context_id'] in related and c['source_ref'].get('sha256') == primary
                      and norm(c.get('text', '')) == self.norm]
        if not candidates:
            # No source identity/structural seed means no permission to search
            # arbitrary background; the required definition remains unknown.
            self._request('cited_standard', criterion.group(),
                '当前操作性临床优势申请条件缺少同源确指种子及完整定义', 'required_reference_unresolved')
            return
        closed = self._closed_primary_programme(application.group(1))
        if not closed:
            self._request('cited_standard', criterion.group(),
                '当前临床优势条件缺少同源完整程序及唯一操作命题位置', 'required_reference_unresolved')
            return
        completion = self._primary_standard_group(candidates, 'admission')
        if not completion:
            self._request('cited_standard', criterion.group(),
                '当前操作性临床优势申请条件的同版完整条件组不能闭合', 'required_reference_unresolved')
            return
        definition = norm(completion['standard_text'])
        literal = re.escape(criterion.group())
        if not re.search(literal + r'[^。；;]{0,8}(?:即|是指)', definition):
            # Complete available conditions without such a definition are a
            # semantic negative, not grounds to invent an absent S branch.
            return
        details = {k: v for k, v in completion.items() if k != 'evidence'}
        self._add('cited_standard', completion['evidence'],
            '当前以明确临床优势作为申请程序的操作性条件，承接同源同版完整定义及并列分支；疾病严重程度、宗旨和其他工作章节不被补入',
            relation_subtype='operative_value_complete_definition',
            resolution_path='primary_literal_complete_operative_value_definition',
            current_criterion_anchor=self.current_anchor(criterion.start(), criterion.end()),
            current_application_anchor=self.current_anchor(application.start(), application.end()),
            defined_value_expression=criterion.group(),
            action_scope='current_application_criterion_consumes_definition', **details)

    def _closed_primary_programme(self, name):
        """Return one same-source, contiguous literal programme and exact spans."""
        primary = self.unit.get('source_ref', {}).get('sha256')
        intervals = []
        for c in self.contexts:
            if c['kind'] != 'source_textleaf' or c['source_ref'].get('sha256') != primary:
                continue
            bounds = c['source_ref'].get('locator', {}).get('unicode_code_point_interval_half_open')
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(type(v) is not int for v in bounds)
                    or bounds[1] - bounds[0] != len(c.get('text', ''))):
                raise SourceDependencyStop('malformed same-source primary literal leaf coordinates')
            intervals.append((bounds[0], bounds[1], c))
        intervals.sort(key=lambda item: item[0])
        if any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
            raise SourceDependencyStop('overlapping same-source primary literal leaf coordinates')
        if not intervals or intervals[0][0] != 0 or any(a[1] != b[0] for a, b in zip(intervals, intervals[1:])):
            return None
        raw = ''.join(c['text'] for _, _, c in intervals)
        title_re = r'(?m)^[ \t]*(?P<name>[\u4e00-\u9fff]{2,35}(?:程序|计划|通道|试点))(?:[（(][^）)\n]{1,12}[）)])?[ \t]*$'
        titles = list(re.finditer(title_re, raw))
        # Morphology only: preserve 审评 in 优先审评审批, while the optional
        # 审评工作 wording may sit between a programme name and 程序.
        def key(value):
            return norm(value).replace('审评工作', '').replace('工作', '')
        selected = [m for m in titles if key(m.group('name')).endswith(key(name))]
        if len(selected) != 1:
            return None
        title = selected[0]
        end = min((m.start() for m in titles if m.start() > title.start()), default=len(raw))
        lo = title.end()
        block = raw[lo:end]
        view, offsets = matching_view(block)
        occurrences = list(re.finditer(re.escape(self.norm), view))
        if len(occurrences) != 1:
            return None
        a, b = raw_span(offsets, occurrences[0].start(), occurrences[0].end())
        return {'raw': raw, 'intervals': intervals, 'programme_name': name,
                'programme_span': [lo, end], 'heading_span': [title.start(), title.end()],
                'current_snapshot_span': [lo + a, lo + b], 'source_sha256': primary}

    def _primary_role_quotes(self, closed, bounds, role):
        evidence, roles = [], []
        for start, end in bounds:
            for a, b, c in closed['intervals']:
                x, y = max(a, start), min(b, end)
                if x < y:
                    quote = self._quote(c, '当前有界安排直接使用的同版' + role, (x-a, y-a))
                    evidence.append(quote)
                    roles.append({'role': role, 'source_snapshot_span': [x, y],
                                  'source_leaf_span': [x-a, y-a], 'evidence': quote})
        return evidence, roles

    def _programme_eligibility_quotes(self, closed):
        """Only the bounded eligibility section before working procedures."""
        lo, hi = closed['programme_span']
        block = closed['raw'][lo:hi]
        scope = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、适用范围(?:和适用条件)?[ \t]*$', block)
        work = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、工作程序[ \t]*$', block)
        if not scope or not work or scope.end() >= work.start():
            return [], []
        # Keep all applicability branches and conjunctions. The working
        # chapter's parallel services/obligations never enter this quotation.
        return self._primary_role_quotes(closed,
            [(lo + scope.start(), lo + work.start())], 'operative_eligibility_scope')

    def _closed_programme_for_current_action(self):
        """Locate a literal boundary only; callers must prove an actual action."""
        primary = self.unit.get('source_ref', {}).get('sha256')
        names = set()
        pattern = r'(?m)^[ \t]*([\u4e00-\u9fff]{2,35}(?:程序|计划|通道|试点))(?:[（(][^）)\n]{1,12}[）)])?[ \t]*$'
        for c in self.contexts:
            if c['kind'] == 'source_textleaf' and c.get('source_ref', {}).get('sha256') == primary:
                names.update(re.findall(pattern, c.get('text', '')))
        closed = [value for name in sorted(names)
                  if (value := self._closed_primary_programme(name))]
        return closed[0] if len(closed) == 1 else None

    def _current_programme_component(self, closed):
        """The one working subsection containing the exact current sentence."""
        lo, hi = closed['programme_span']
        raw = closed['raw']
        heads = list(re.finditer(r'(?m)^[ \t]*(?:[（(][一二三四五六七八九十]+[）)]|[一二三四五六七八九十]+、)', raw[lo:hi]))
        a, b = closed['current_snapshot_span']
        previous = [h for h in heads if lo+h.start() <= a]
        if not previous:
            return None
        head = previous[-1]
        start = lo+head.start()
        stop = min((lo+h.start() for h in heads if lo+h.start() > start), default=hi)
        if b > stop or not re.match(r'[ \t]*[（(]', raw[start:stop]):
            return None
        return {'span': [start, stop], 'text': raw[start:stop],
                'current_span': [a, b]}

    def _programme_operative_eligibility(self):
        """Current actual eligibility assessment or condition-based withdrawal.

        A bare programme title, a publication notice, and missed paperwork alone
        cannot use substantive conditions. All eligibility branches are retained.
        """
        criterion = re.search(r'(?:是否符合|是否满足|不符合|不再符合|不能满足)[^。；;，,]{0,30}(?:纳入条件|适用条件|资格标准)', self.norm)
        review = re.search(r'(?:组织|召开)[^。；;]{0,24}(?:专家|论证|审核)|(?:进行|开展|作出)[^。；;]{0,12}(?:论证|审核|核验|决定)', self.norm)
        withdrawal = re.search(r'(?:应当|应|须|必须)[^。；;]{0,15}(?:及时)?(?:终止|取消|撤回)[^。；;]{0,35}(?:程序|计划|通道|试点)', self.norm)
        if not criterion or not (review or withdrawal):
            return
        if re.search(r'仅(?:记录|转发|通知)|不(?:进行|开展)(?:审核|核验|论证)', self.norm):
            return
        closed = self._closed_programme_for_current_action()
        if not closed:
            return
        component = self._current_programme_component(closed)
        if not component:
            return
        # The current local subsection must explicitly identify the same
        # programme's qualification. Boundary location alone supplies no scope.
        short = closed['programme_name'].replace('药品上市许可', '').replace('工作', '')
        if short not in norm(component['text']) or not re.search(r'纳入条件|适用条件', norm(component['text'])):
            return
        quotes, roles = self._programme_eligibility_quotes(closed)
        if not quotes:
            return
        self._add('cited_standard', quotes,
            '当前实际论证具名程序纳入资格或依条件决定终止；引用该程序完整同版适用条件，不从单纯文书逾期推定所有条件失败',
            relation_subtype='bounded_current_eligibility_assessment',
            action_scope='standard_review_or_eligibility_consequence',
            standard_text='\n'.join(q['text'] for q in quotes),
            programme_name=short, source_roles=roles,
            current_condition_anchor=self.current_anchor(criterion.start(), criterion.end()),
            current_application_anchor=self.current_anchor((withdrawal or review).start(), (withdrawal or review).end()),
            scope_binding={'source_sha256': closed['source_sha256'], 'component_snapshot_span': component['span'],
                           'current_snapshot_span': closed['current_snapshot_span'],
                           'context_ids': [q['context_id'] for q in quotes]},
            version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme',
                             'source_sha256': closed['source_sha256']})
        # Resolve only this resolver's exact earlier missing-eligibility request.
        # Other material requests, dimensions, and source dependencies stay open.
        self.material_requests[:] = [r for r in self.material_requests
            if not (r.get('path') == 'cited_standard' and r.get('reference') == self.text
                    and r.get('missing') == '确指资格/标准与待遇后果的同版标准原文缺失')]

    def _nested_explicit_clinical_advantage_standard(self):
        """One explicit same-edition definition inside an operative standard.

        The current record must already consume a complete qualification
        standard. A precise title + defined criterion may then resolve the
        finite clinical-advantage group. This is not traversal of generic
        related regulations, and no programme identity can trigger it.
        """
        actual_condition = re.search(r'(?:条件|资格|标准)', self.norm)
        actual_operation = re.search(r'(?:进行|开展|组织|作出)[^。；;]{0,25}(?:论证|审核|核验|决定)|(?:应当|应|将|必须|须)[^。；;]{0,30}(?:终止|取消|撤回|限制|满足|符合)|(?:条件|资格)[^。；;]{0,12}(?:审核|核验)', self.norm)
        if not actual_condition or not actual_operation:
            return
        references = []
        for relation in list(self.relations):
            if (relation['kind'] != 'cited_standard'
                    or relation['details'].get('action_scope') != 'standard_review_or_eligibility_consequence'):
                continue
            for quote in relation['context_evidence']:
                for ref in re.finditer(r'参照《([^》]+)》关于临床优势的适用条件', quote['text']):
                    if (quote['source_ref'].get('sha256') == self.unit.get('source_ref', {}).get('sha256')
                            and (quote['context_id'], ref.start(), ref.end()) not in [x[0] for x in references]):
                        references.append(((quote['context_id'], ref.start(), ref.end()), quote, ref))
        if not references:
            return
        closed = self._closed_programme_for_current_action()
        for _, bridge, reference in references:
            title = reference.group(1)
            failure = '当前操作性资格条件确指临床优势定义，但同版完整五分支定义及边界尚未核明'
            selected = None
            if closed and closed['source_sha256'] == bridge['source_ref'].get('sha256'):
                raw = closed['raw']
                titles = [m for m in re.finditer(r'(?m)^[^\n]+$', raw)
                          if norm(m.group()).strip() == norm(title).strip()]
                if len(titles) == 1:
                    start = titles[0].end()
                    work = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、工作程序[ \t]*$', raw[start:])
                    if work:
                        stop = start + work.start()
                        section = raw[start:stop]
                        condition_heading = re.search(r'(?m)^[ \t]*[（(][一二三四五六七八九十]+[）)]适用条件[ \t]*$', section)
                        if condition_heading:
                            clauses = list(re.finditer(r'(?m)^[ \t]*[0-9]+[.．、]', section))
                            groups = []
                            for index, clause in enumerate(clauses):
                                end = clauses[index+1].start() if index+1 < len(clauses) else len(section)
                                part = section[clause.start():end]
                                pt = norm(part)
                                if (clause.start() > condition_heading.end()
                                        and re.search(r'明显临床优势[^。]{0,100}即', pt)
                                        and re.search(r'具体包括以下任一情形', pt)):
                                    numbers = re.findall(r'(?m)^[ \t]*[（(]([0-9]+)[）)]', part)
                                    # This exact named criterion has five
                                    # enumerated alternatives, followed by its
                                    # own defined terms before 工作程序.
                                    complete = (numbers == ['1','2','3','4','5']
                                                and re.search(r'现有治疗手段是指', pt)
                                                and re.search(r'具有临床意义的终点', pt))
                                    if complete:
                                        groups.append((start+clause.start(), start+end))
                            if len(groups) == 1:
                                selected = groups[0]
            if selected:
                definition, roles = self._primary_role_quotes(closed, [selected], 'explicit_nested_clinical_advantage_definition')
                # Keep the literal referring clause separate from its target.
                # Only the target criterion becomes substantive standard text.
                c = self.by_id[bridge['context_id']]
                a = bridge['start'] + reference.start()
                b = bridge['start'] + reference.end()
                bridge_quote = self._quote(c, '完整资格条件明确参照的具名临床优势适用条件', (a,b))
                self._add('cited_standard', definition + [bridge_quote],
                    '当前资格核验/终止条件经完整同版条件明确参照临床优势定义；只展开被确指五分支及直接术语，含疗效比较和安全性优势，不把不符合整体条件解释为每项均失败',
                    relation_subtype='bounded_nested_clinical_advantage_standard',
                    action_scope='standard_review_or_eligibility_consequence',
                    standard_text='\n'.join(q['text'] for q in definition),
                    source_roles=roles, reference_bridge=bridge_quote,
                    target_document_title=title, selected_group_snapshot_span=list(selected),
                    group_operator='任一', complete_member_numbers=['1','2','3','4','5'],
                    version_binding={'established': True, 'binding': 'exact_same_snapshot_explicit_standard_reference',
                                     'source_sha256': closed['source_sha256']},
                    finite_reference_depth=1, generic_reference_recursion=False)
            else:
                request = {'path': 'cited_standard', 'reference': reference.group(),
                           'current_text': self.text, 'missing': failure,
                           'affected_dimensions': ['S','E'],
                           'dependency_status': 'stopped',
                           'stop_reason': 'explicit_nested_clinical_advantage_definition_incomplete_or_wrong_edition'}
                if request not in self.material_requests:
                    self.material_requests.append(request)

    def _programme_condition_consequence(self):
        """Resolve a named programme's conditions when they control withdrawal.

        The prior resolver recognizes literal 纳入条件. This path also accepts
        the programme's own name followed by 条件, with an explicit current
        standards-to-withdrawal consequence and a closed same-source programme.
        """
        programme = re.search(r'纳入([^。；;，,]{3,30}(?:程序|计划|通道|试点))的', self.norm)
        if not programme:
            return
        name = programme.group(1)
        short = re.sub(r'(?:程序|计划|通道|试点)$', '', name)
        criterion = re.search(r'(?:不能满足|不再符合|不符合|未满足|不满足)[^。；;]{0,12}'
                              + re.escape(short) + r'(?:程序)?(?:条件|标准)', self.norm)
        consequence = re.search(r'(?:应当|应|将|须|必须)[^。；;]{0,20}(?:终止|取消|撤回)[^。；;]{0,25}'
                                + re.escape(short[:4]), self.norm)
        if not criterion or not consequence or criterion.end() > consequence.start():
            return
        closed = self._closed_primary_programme(name)
        if not closed:
            return
        evidence, roles = self._programme_eligibility_quotes(closed)
        if not evidence:
            return
        self._add('cited_standard', evidence,
            '当前明确以具名程序条件不满足决定撤回其待遇，完整核验同源同版适用条件；不把不满足整体条件说成每一分支都失败',
            relation_subtype='bounded_named_conditions_withdrawal',
            action_scope='standard_review_or_eligibility_consequence',
            standard_text='\n'.join(e['text'] for e in evidence),
            programme_name=name, source_roles=roles,
            current_condition_anchor=self.current_anchor(criterion.start(), criterion.end()),
            current_consequence_anchor=self.current_anchor(consequence.start(), consequence.end()),
            version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme',
                             'source_sha256': closed['source_sha256']})

    def _priority_resource_arrangements(self):
        """Connect current priority resources to their own programme scope."""
        programme = re.search(r'(?:对|针对)纳入([^。；;，,]{3,30}(?:程序|计划|通道|试点))的(?:品种|药品|药物|项目)', self.norm)
        allocation = re.search(r'优先配置[^。；;]{0,12}资源[^。；;]{0,18}审评|(?:应当|应)[^。；;]{0,12}优先(?:进行|安排)[^。；;]{0,20}(?:核查|检验|审评)', self.norm)
        if not programme or not allocation or programme.end() > allocation.start():
            return
        if re.search(r'仅(?:记录|通知|告知)|未(?:实施|安排)|不再|不得', self.norm):
            return
        closed = self._closed_primary_programme(programme.group(1))
        if not closed:
            return
        evidence, roles = self._programme_eligibility_quotes(closed)
        if not evidence:
            return
        self._add('named_mechanism', evidence,
            '当前已明确对纳入品种实际优先配置审评/核查资源，仅补同版同程序的完整对象范围，不复制其他阶段待遇',
            relation_subtype='bounded_current_priority_resource',
            object_definition='\n'.join(e['text'] for e in evidence),
            direct_mechanism=self.text, source_roles=roles,
            current_allocation_anchor=self.current_anchor(allocation.start(), allocation.end()),
            version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme',
                             'source_sha256': closed['source_sha256']})

    def _team_service_execution(self):
        """Execution of a demonstrated specialist review service, not staffing."""
        execution = re.search(r'审评团队[^。；;]{0,35}(?:解决|处理)[^。；;]{0,12}技术问题[^。；;]{0,25}(?:按时限|按期)[^。；;]{0,12}完成审评', self.norm)
        if not execution or re.search(r'仅[^。；;]{0,20}(?:转发|收发|归档)|行政(?:文件|材料)', self.norm):
            return
        current = self._current_source()
        if not current:
            return
        sha = current.get('source_ref', {}).get('sha256')
        groups = []
        for boundary in self.contexts:
            st = boundary.get('structure', {})
            ids = st.get('scope_context_ids', [])
            if (boundary['kind'] != 'following_heading' or not ids or len(ids) != len(set(ids))
                    or st.get('follows_context_id') != ids[-1]
                    or boundary.get('source_ref', {}).get('sha256') != sha
                    or not same_component(current, boundary)):
                continue
            members = [self.by_id.get(cid) for cid in ids]
            if any(not c or c['kind'] != 'source_paragraph' or not c.get('text')
                   or c.get('source_ref', {}).get('sha256') != sha
                   or not same_component(current, c) for c in members):
                continue
            objects = [c for c in members if re.search(r'适用范围', norm(c['text']))
                       and re.search(r'创新药|改良型新药', norm(c['text']))]
            stages = [c for c in members if re.search(r'研发阶段', norm(c['text']))
                      and re.search(r'上市前', norm(c['text']))]
            timings = [c for c in members if re.search(r'审评时限', norm(c['text']))
                       and re.search(r'单独序列|优先审评', norm(c['text']))]
            if objects and stages and timings:
                groups.append((boundary, members, objects, stages, timings))
        if len(groups) != 1:
            return
        boundary, members, objects, stages, timings = groups[0]
        oq = [self._quote(c, '同源有界规范明确的创新研发服务对象') for c in objects]
        sq = [self._quote(c, '同源有界规范明确的上市前研发阶段') for c in stages]
        tq = [self._quote(c, '当前团队解决技术问题落实的专门审评序列与时限') for c in timings]
        st = boundary['structure']
        self._add('named_mechanism', oq + sq + tq,
            '当前专门审评团队实际解决技术问题以落实同版审评时限；只补已闭合的创新对象、上市前阶段和专门序列，普通行政事务不适用',
            relation_subtype='bounded_specialized_team_execution',
            object_definition='\n'.join(e['text'] for e in oq),
            research_stage='\n'.join(e['text'] for e in sq),
            direct_mechanism=self.text + '\n' + '\n'.join(e['text'] for e in tq),
            current_execution_anchor=self.current_anchor(execution.start(), execution.end()),
            scope_binding={'source_sha256': sha, 'boundary_context_id': boundary['context_id'],
                           'context_ids': st['scope_context_ids'],
                           'component_first_paragraph': st.get('component_first_paragraph'),
                           'component_last_paragraph': st.get('component_last_paragraph')},
            version_binding={'established': True, 'binding': 'same_source_closed_component', 'source_sha256': sha})

    def _need_linked_inspection_deferral(self):
        """A current postapproval exception plus its explicit prior baseline.

        A general postmarketing inspection is not a priority measure. Require
        both the governing unmet-need object and an adjacent, same-source
        preapproval inspection baseline. Neither a rare-disease name nor a
        bare number of days can establish this relation.
        """
        action = re.search(r'完成上市审批后[^。；;]{0,8}(?:可以|可)[^。；;]{0,30}开展药品注册核查', self.norm)
        if not action or re.search(r'其他(?:药品|药物|品种)|另(?:一|外)', self.norm):
            return
        source_sha = self.unit.get('source_ref', {}).get('sha256')
        paragraphs = [c for c in self.contexts if c['kind'] == 'paragraph'
                      and c.get('source_ref', {}).get('sha256') == source_sha
                      and self.norm in norm(c.get('text', ''))]
        if len(paragraphs) != 1:
            return
        parent = paragraphs[0]
        parent_norm = norm(parent['text'])
        before = parent_norm.split(self.norm, 1)[0]
        target = re.search(r'^对于[^。；;]{0,160}临床急需[^。；;]{0,25}境外已上市境内未上市[^。；;，,]{0,20}药品', before)
        if not target or re.search(r'另(?:一|外)|其他(?:药品|药物|品种)', before[target.end():]):
            return
        baselines = [c for c in self.contexts if c['kind'] == 'preceding_paragraph'
                     and c.get('source_ref', {}).get('sha256') == source_sha
                     and same_component(parent, c)
                     and re.search(r'药品注册核查', norm(c.get('text', '')))
                     and re.search(r'审评时限届满[^。；;]{0,12}日前完成核查', norm(c.get('text', '')))]
        if len(baselines) != 1:
            return
        # Quote the actual raw object span, not a synthetic '后置' label.
        _, offsets = matching_view(parent['text'])
        a, b = raw_span(offsets, target.start(), target.end())
        oq = self._quote(parent, '当前核查例外直接承接的临床急需且境内未上市治疗对象', (a, b))
        bq = self._quote(baselines[0], '同源相邻一般程序要求审评期限前完成核查的对照')
        self._add('named_mechanism', [oq, bq],
            '同一段所限定急需境内未上市药品的核查可在上市审批后开展，与相邻同源审评期限前核查基准形成明确办理便利；不以普通上市后检查本身推优先',
            relation_subtype='bounded_need_linked_inspection_deferral',
            content=oq['text'], object_definition=oq['text'],
            direct_mechanism=self.text, baseline_before_review_quote=bq,
            current_deferral_anchor=self.current_anchor(action.start(), action.end()),
            object_scope_quote=oq,
            scope_binding={'source_sha256': source_sha,
                           'context_ids': [parent['context_id'], baselines[0]['context_id']],
                           'inspection_kind': '药品注册核查',
                           'current_is_governed_same_paragraph_exception': True},
            version_binding={'established': True, 'binding': 'same_source_adjacent_paragraph_exception',
                             'source_sha256': source_sha})

    def _postadmission_technical_support(self):
        """Resolve actual technical communication after programme admission.

        The current service, same programme's eligibility scope, technical-review
        priority communication and concrete technical-material feedback are
        separate roles. Preapplication communication and general purpose never
        supply the missing service or priority opportunity.
        """
        target = re.search(r'(?:对|针对)纳入([^。；;，,]{4,28}(?:程序|计划|通道|试点))的(?:品种|药品|药物|项目)', self.norm)
        service = re.search(r'(?:进行|开展|提供|安排)[^。；;]{0,20}(?:沟通交流|技术咨询|研究反馈)', self.norm)
        # An actual opportunity to request technical-content feedback is a
        # service, unlike a list of phone/video/submission channels. Keep the
        # content requirement explicit in the current proposition.
        if service is None:
            service = re.search(r'(?:可以|可|允许)[^。；;]{0,45}(?:提出|提交)[^。；;]{0,25}(?:补充提交技术资料|研究方案反馈|试验方案反馈|研发技术咨询)[^。；;]{0,12}(?:沟通交流|技术咨询)申请', self.norm)
        form_only = (re.search(r'(?:电话|视频|面对面|书面)[^。；;]{0,15}(?:形式|渠道|方式)|沟通交流(?:形式|渠道|方式)', self.norm)
                     and not re.search(r'(?:提供|开展|进行)[^。；;]{0,20}(?:研究反馈|技术咨询|技术资料|技术服务|研究方案反馈)', self.norm))
        service_mode = 'explicit_postadmission_technical_service'
        scope_binding = {}
        closed = None
        if form_only or re.search(r'申请前|申报前|仅[^。；;]{0,12}(?:电话|视频|形式|渠道)|其他(?:药品|药物|产品)', self.norm):
            return
        if target and service:
            clause_bound = any(m.start() <= target.start() and service.end() <= m.end()
                               for m in re.finditer(r'[^。；;]+', self.norm))
            if not clause_bound:
                return
            name = target.group(1)
            closed = self._closed_primary_programme(name)
        else:
            priority_service = re.search(r'(?:在审评中|审评过程中)[^。；;]{0,50}(?:沟通交流|技术咨询|研究反馈)[^。；;]{0,25}优先(?:安排|提供|处理)', self.norm)
            confirmed = re.search(r'经(?:沟通交流|技术咨询)确认[^。；;]{0,25}(?:可以|可|允许)[^。；;]{0,15}提交[^。；;]{0,15}技术资料', self.norm)
            admission = re.search(r'(?:即|直接|予以)纳入([^。；;，,]{4,28}(?:程序|计划|通道|试点))', self.norm)
            if admission and re.search(r'(?:拟|建议|仅通知|未决定)[^。；;]{0,12}$', self.norm[:admission.start()]):
                admission = None
            if not priority_service and not confirmed and not admission:
                return
            closed = self._closed_programme_for_current_action()
            if not closed:
                return
            component = self._current_programme_component(closed)
            if not component:
                return
            ct = norm(component['text'])
            governor = re.search(r'(?:对|针对)纳入([^。；;，,]{4,28}(?:程序|计划|通道|试点))的(?:品种|药品|药物|项目)', ct)
            if not governor and not admission:
                return
            name = admission.group(1) if admission else governor.group(1)
            # Recheck the governor resolves the same literal programme.
            governed = self._closed_primary_programme(name)
            if not governed or governed['programme_span'] != closed['programme_span']:
                return
            closed = governed
            if admission:
                service = admission
                service_mode = 'programme_admission'
            elif priority_service:
                if not re.search(r'^[（(][一二三四五六七八九十]+[）)]技术审评', ct):
                    return
                service = priority_service
                service_mode = 'priority_technical_communication'
            else:
                # Confirmation must be the next step of the SAME paragraph's
                # explicit postadmission technical-feedback application.
                parents = [c for c in self.contexts if c['kind'] == 'paragraph'
                           and c.get('source_ref', {}).get('sha256') == closed['source_sha256']
                           and self.norm in norm(c.get('text', ''))]
                if len(parents) != 1:
                    return
                before = norm(parents[0]['text']).split(self.norm, 1)[0]
                if (not re.search(r'纳入'+re.escape(name), before)
                        or not re.search(r'在审评过程中[^。；;]{0,100}(?:提出|提交)[^。；;]{0,20}补充提交技术资料[^。；;]{0,15}沟通交流申请', before)
                        or not re.search(r'审评时限不延长', self.norm)):
                    return
                service = confirmed
                service_mode = 'confirmed_technical_submission'
            sq, _ = self._primary_role_quotes(closed, [component['span']], 'current_service_component_binding')
            scope_binding = {'source_sha256': closed['source_sha256'],
                             'component_snapshot_span': component['span'],
                             'current_snapshot_span': closed['current_snapshot_span'],
                             'context_ids': [q['context_id'] for q in sq],
                             'governing_component_quotes': sq}
        if not closed:
            self._request('named_mechanism', name,
                '当前纳入后技术沟通缺少同版完整程序、唯一当前位置和对象/技术审评组件边界',
                'required_reference_unresolved')
            return
        raw = closed['raw']
        lo, hi = closed['programme_span']
        block = raw[lo:hi]
        scope = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、(?:适用范围|适用范围和适用条件)[ \t]*$', block)
        work = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、工作程序[ \t]*$', block)
        review = re.search(r'(?m)^[ \t]*[（(][一二三四五六七八九十]+[）)]技术审评[。．.:：]', block)
        if not scope or not work or not scope.start() < work.start():
            # The programme is already closed. Missing substantive scope or
            # support content is a semantic negative, not hypothetical material.
            return
        priority, review_component = [], []
        if review and work.start() < review.start():
            next_head = re.search(r'(?m)^[ \t]*(?:[（(][一二三四五六七八九十]+[）)]|[一二三四五六七八九十]+、)', block[review.end():])
            review_end = review.end() + next_head.start() if next_head else len(block)
            review_text = block[review.start():review_end]
            if re.search(r'纳入' + re.escape(name), norm(review_text)):
                for a, b in sentence_spans(review_text):
                    part = norm(review_text[a:b])
                    if name in part and re.search(r'纳入', part):
                        review_component.append((lo+review.start()+a, lo+review.start()+b))
                    if (re.search(r'在审评中|审评过程中', part) and re.search(r'沟通交流|技术咨询|研究反馈', part)
                            and re.search(r'优先(?:安排|处理|提供)', part)):
                        priority.append((lo+review.start()+a, lo+review.start()+b))
        technical = []
        for a, b in sentence_spans(block[work.end():]):
            part = norm(block[work.end()+a:work.end()+b])
            if (name in part and re.search(r'在审评过程中|在审评中', part)
                    and re.search(r'沟通交流申请|技术咨询申请', part)
                    and re.search(r'补充提交技术资料|研究方案反馈|试验方案反馈|研发技术咨询', part)
                    and not re.search(r'申请前|申报前|仅[^。；;]{0,10}(?:形式|渠道)', part)):
                technical.append((lo+work.end()+a, lo+work.end()+b))
        if not priority and not technical:
            # The two resource paths are independent. I3 does not require a
            # priority measure; F does not require a technical-material branch.
            return
        object_bounds = [(lo+scope.start(), lo+work.start())]
        evidence, roles = [], []
        for role, bounds in [('programme_heading', [closed['heading_span']]),
                             ('object_and_need_eligibility', object_bounds),
                             ('postadmission_technical_review_component_scope', review_component if priority else []),
                             ('postadmission_priority_technical_communication', priority),
                             ('postadmission_technical_material_feedback', technical)]:
            es, rs = self._primary_role_quotes(closed, bounds, role)
            evidence.extend(es); roles.extend(rs)
        objects = '\n'.join(r['evidence']['text'] for r in roles if r['role'] == 'object_and_need_eligibility')
        supports = '\n'.join(r['evidence']['text'] for r in roles if r['role'].startswith('postadmission_'))
        scope_end = re.search(r'(?m)^[ \t]*[一二三四五六七八九十]+、', block[scope.end():work.start()])
        scope_stop = scope.end()+scope_end.start() if scope_end else work.start()
        applicable_scope = block[scope.start():scope_stop]
        innovation_branches = []
        if (re.search(r'(?:可以|可|允许).{0,40}申请适用'+re.escape(name), norm(applicable_scope))
                or re.search(r'适用于|面向', norm(applicable_scope))):
            for a, b in sentence_spans(applicable_scope):
                part = norm(applicable_scope[a:b])
                object_part = part.replace(name, '')
                if (re.search(r'创新药|创新型药物|改良型新药|首创新药', object_part)
                        and not re.search(r'不适用|不包括|不包含|排除|除外|不得申请', part)):
                    quotes, _ = self._primary_role_quotes(closed,
                        [(lo+scope.start()+a, lo+scope.start()+b)], 'positive_innovation_eligible_branch')
                    innovation_branches.extend(quotes)
        evidence.extend(scope_binding.get('governing_component_quotes', []))
        self._add('named_mechanism', evidence,
            '当前实际授予或使用同一程序的技术审评待遇；同版明确技术审评优先沟通或技术资料反馈机会，分别保留实际动作、对象与待遇证据，I3与F独立判断，不借申报前机制或总宗旨',
            relation_subtype='bounded_primary_postadmission_technical_support',
            content=objects+'\n'+supports, object_definition=objects, direct_mechanism=supports,
            current_service_bridge=self.proposition(), source_roles=roles,
            current_service_anchor=self.current_anchor(service.start(), service.end()),
            current_service_mode=service_mode, scope_binding=scope_binding,
            innovation_eligible_branches=innovation_branches,
            postadmission_priority_communication_present=bool(priority),
            postadmission_technical_material_feedback_present=bool(technical),
            programme_name=name, current_snapshot_span=closed['current_snapshot_span'],
            programme_block_snapshot_span=closed['programme_span'],
            version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme',
                             'source_sha256': closed['source_sha256']},
            direct_mapping=True, research_stage='纳入后、药品上市许可技术审评过程中',
            preapplication_mechanism_inherited=False, general_purpose_inherited=False,
            not_whole_programme_inheritance=True)

    def _price_arrangement_definition(self):
        """Map a current operative price node to its same-edition price content."""
        price = re.search(r'价格(?:谈判|协商|磋商)', self.norm)
        if not price or not re.search(OBJECT, self.norm):
            return
        # Stage labels, document preparation and success words alone are not a
        # price proposition. A workflow needs a drug inclusion/indication branch.
        branch = re.search(r'价格(?:谈判|协商|磋商)→(?:协商|谈判|磋商)成功[:：][^。；;]{0,70}(?:纳入|新增适应症|新增功能主治)', self.norm)
        substantive = re.search(r'(?:根据|依据)[^。；;]{0,35}(?:评估|测算|确定)[^。；;]{0,20}(?:协商价格|药品价格)[^。；;]{0,25}(?:开展|进行)[^。；;]{0,15}价格(?:谈判|协商|磋商)', self.norm)
        if not branch or substantive:
            return
        primary = self.unit.get('source_ref', {}).get('sha256')
        evidence, chains = [], []
        current_directories = re.findall(r'《([^》]{2,20}目录)》', self.norm)
        for c in self.contexts:
            if (c['kind'] not in {'source_textleaf', 'source_resource_text', 'historical_source_fragment', 'source_paragraph'}
                    or c['source_ref'].get('sha256') != primary):
                continue
            view, offsets = matching_view(c.get('text', ''))
            sentences = list(re.finditer(r'[^。]+(?:。|$)', view))
            for index, sentence in enumerate(sentences):
                part = sentence.group()
                if (re.search(r'(?:根据|依据)[^。；;]{0,30}(?:评估|测算|确定)[^。；;]{0,20}(?:协商价格|药品价格)', part)
                        and re.search(r'(?:开展|进行)[^。；;]{0,15}(?:现场)?价格(?:谈判|协商|磋商)', part)):
                    previous = sentences[index-1] if index else None
                    object_part = part if re.search(r'药品|药物|该药|本药', part) else (previous.group() if previous else '')
                    if (not re.search(r'药品|药物|该药|本药', object_part)
                            or not re.search(r'价格(?:协商|谈判|磋商)', object_part)
                            or (current_directories and not any(d in part + object_part for d in current_directories))):
                        continue
                    selected = []
                    if previous is not None and object_part != part:
                        a, b = raw_span(offsets, previous.start(), previous.end())
                        selected.append(self._quote(c, '同版价格磋商定义的紧邻药品/目录对象及节点指代', (a, b)))
                    a, b = raw_span(offsets, sentence.start(), sentence.end())
                    selected.append(self._quote(c, '当前价格协商节点的同版评估价格与实际磋商定义', (a, b)))
                    evidence.extend(selected)
                    chains.append({'source_context_id': c['context_id'], 'object_and_node': object_part,
                                   'price_content': part, 'exact_quotes': selected,
                                   'same_snapshot': True, 'nearest_preceding_object_only': object_part != part})
        if not evidence:
            self._request('price_arrangement', price.group(),
                '当前实际价格协商分支缺少同版评估/确定价格及磋商内容定义', 'required_reference_unresolved')
            return
        self._add('price_arrangement', evidence,
            '当前实际价格协商分支与同版评估确定协商价格的现场磋商定义直接相接；只补价格配置内容，不从商保推荐目录推出实际医保或商业承保支付',
            relation_subtype='same_edition_price_node_content_definition',
            current_price_anchor=self.current_anchor(price.start(), price.end()),
            current_branch_anchor=self.current_anchor(branch.start(), branch.end()),
            version_binding={'established': True, 'binding': 'exact_same_snapshot', 'source_sha256': primary},
            price_definition='\n'.join(e['text'] for e in evidence),
            price_object_content_chains=chains,
            directory_recommendation_is_payment_coverage=False,
            direct_mapping=True, not_whole_document_inheritance=True)

    def _version(self, c, action_text=None):
        meta = self._metadata(c)
        date = meta.get('document_date') or meta.get('source_date') or meta.get('policy_document_date')
        current_years = re.findall(r'(?:19|20)\d{2}年', self.norm if action_text is None else action_text)
        source_year = date[:4] if date else None
        if current_years and (not source_year or any(y[:4] != source_year for y in current_years)):
            return {'established': False, 'current_years': current_years, 'source_date': date}
        sha = c.get('source_ref', {}).get('sha256')
        primary = self.unit.get('source_ref', {}).get('sha256')
        same_snapshot = bool(sha and primary == sha)
        title = meta.get('document_title') or meta.get('source_title', '')
        # Neutral v12 supplements carry original source identities. A date in
        # a filename is never consumed as an edition statement.
        identity = bool(date and title and (meta.get('document_number') or meta.get('policy_document_number')
            or meta.get('source_url') or meta.get('original_url')))
        return {'established': bool(same_snapshot or identity), 'current_years': current_years, 'source_date': date,
                'source_title': title, 'source_sha256': sha,
                'binding': 'exact_same_snapshot' if same_snapshot else
                    'explicit_historical_year_source_identity' if current_years else 'preserved_same_policy_source_identity'}

    def _current_source(self):
        paragraphs = [c for c in self.contexts if c['kind'] == 'paragraph'
                      and self.norm and self.norm in norm(c.get('text', ''))]
        sources = {c.get('source_ref', {}).get('sha256') for c in paragraphs}
        return paragraphs[0] if len(sources) == 1 and paragraphs else None

    def _reference_members(self, container, current):
        source_sha = current.get('source_ref', {}).get('sha256')
        if (container.get('source_ref', {}).get('sha256') != source_sha
                or not same_component(container, current)):
            return []
        ids = []
        for group in container.get('structure', {}).get('child_groups', []):
            if group.get('position') in ('contexts', 'members', 'ordered_members'):
                ids.extend(group.get('ordered_context_ids', []))
        if not ids or len(ids) != len(set(ids)):
            return []
        members = []
        for cid in ids:
            child = self.by_id.get(cid)
            if child is None:
                return []
            if child['kind'] in ('boundary', 'boundary_container', 'following_heading'):
                break
            if (child.get('source_ref', {}).get('sha256') != source_sha
                    or not same_component(child, current)
                    or child.get('structure', {}).get('parent_context_id') != container['context_id']):
                return []
            if child['kind'] not in ('ordered_members', 'cited_article', 'cited_section', 'source_paragraph'):
                return []
            raw = child.get('text', '')
            for match in re.finditer(r'[^\n]+(?:\n|$)', raw):
                if match.group().strip():
                    members.append((child, (match.start(), match.end()), norm(match.group())))
        if not members:
            return []
        first = re.match(ARTICLE_REFERENCE, members[0][2])
        if not first:
            return []
        article = ordinal_number(first.group(1))
        bounded = []
        for member in members:
            heading = re.match(ARTICLE_REFERENCE, member[2])
            if heading and ordinal_number(heading.group(1)) != article:
                break
            bounded.append(member)
        return bounded

    def _reference_candidates(self, current, article):
        candidates = []
        source_sha = current.get('source_ref', {}).get('sha256')
        for root in self.contexts:
            if (root['kind'] != 'cited_reference_group'
                    or root.get('source_ref', {}).get('sha256') != source_sha
                    or not same_component(root, current)):
                continue
            ids = []
            for group in root.get('structure', {}).get('child_groups', []):
                if group.get('position') == 'references':
                    ids.extend(group.get('ordered_context_ids', []))
            for cid in ids:
                container = self.by_id.get(cid)
                if (not container or container['kind'] != 'cited_reference'
                        or container.get('structure', {}).get('parent_context_id') != root['context_id']):
                    continue
                members = self._reference_members(container, current)
                if not members:
                    continue
                heading = re.match(ARTICLE_REFERENCE, members[0][2])
                if ordinal_number(heading.group(1)) == article:
                    candidates.append((container, members))
        # Original article groups supplied as neutral resources have their own
        # source identity and order; they are not converted to old graph kinds.
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != source_sha:
                continue
            for group in doc.get('ordered_article_groups', []):
                heading = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))
                if not heading or ordinal_number(heading.group(1)) != article:
                    continue
                ids = group.get('ordered_source_resource_ids', [])
                if not ids or len(ids) != len(set(ids)):
                    continue
                members = []
                for position, rid in enumerate(ids, 1):
                    matches = [c for c in self.contexts if self.origins.get(c['context_id'], {}).get('source_resource_id') == rid
                        and c['source_ref']['sha256'] == source_sha]
                    if len(matches) != 1:
                        members = []
                        break
                    c = matches[0]
                    st = c.get('structure', {})
                    if st.get('article') != group['article'] or st.get('clause_index_one_based') != position or not c.get('text'):
                        members = []
                        break
                    members.append((c, (0, len(c['text'])), norm(c['text'])))
                if members:
                    candidates.append((members[0][0], members))
        return candidates

    def _data_protection_rights_consequence(self):
        """Actual use of a defined innovation-related protection entitlement.

        Current filing, expiry-conditioned permission, or release of the
        exclusion must be operative. Announcements, lists, consultation forms,
        and unrelated confidentiality cannot inherit an innovation branch.
        """
        current = self._current_source()
        if (current is None or current['source_ref'].get('sha256') != self.unit.get('source_ref', {}).get('sha256')
                or not same_component(self.unit,current)
                or not re.search(r'药品|药物', self.norm)):
            return
        current_matches = [c for c in self.contexts if c['kind']=='paragraph' and self.norm in norm(c.get('text',''))]
        if len(current_matches) != 1:
            return
        expiry = re.search(r'数据保护期届满前[^。；;]{0,16}(?<!不)(?:可以|可|允许)(?:提交|提出)[^。；;]{0,12}依赖(?:该|其)?受保护数据[^。；;]{0,30}(?:药品上市申请|药品注册申请|补充申请)', self.norm)
        expiry_end = re.search(r'数据保护期届满后(?:方可|才可|可以|可)?批准[^。；;]{0,15}药品上市', self.norm)
        termination = re.search(r'终止(?:药品试验)?数据保护公告之日起[^。；;]{0,8}(?<!不)(?:可以|可|允许)(?:受理|批准)', self.norm)
        reliance = re.search(r'依赖(?:该|其)?受保护数据[^。；;]{0,20}药品注册申请', self.norm)
        application = re.search(r'(?:拟申请|申请)(?:药品试验)?数据保护的[^。；;]{0,8}(?:应当|应|必须)[^。；;]{0,10}提交药品上市许可申请时(?:同时)?(?:提出|提交)(?:药品试验)?数据保护申请(?!表|材料|格式)', self.norm)
        if expiry and expiry_end and expiry.end() <= expiry_end.start():
            mode = 'expiry_conditioned_market_permission'
            action_bounds = (expiry.start(), expiry_end.end())
        elif termination and reliance and termination.end() <= reliance.start():
            mode = 'termination_releases_market_permission'
            action_bounds = (termination.start(), reliance.end())
        elif application:
            mode = 'protection_application'
            action_bounds = application.span()
        else:
            return
        # The operative text must be the current proposition, not a quoted
        # form label, wording consultation, or system-field description.
        body = re.sub(r'^第(?:'+ORDINAL+r'|[0-9]+)条[\s:：]*','',self.norm)
        if mode == 'protection_application' and not re.match(r'(?:申请人|持有人|药品上市许可申请人)(?:拟申请|申请)',body):
            return
        if mode == 'expiry_conditioned_market_permission' and not re.match(r'(?:药品|药物)(?:获得|取得)数据保护后[，,](?:其他)?申请人在',body):
            return
        if mode == 'termination_releases_market_permission' and not re.match(r'自[^。；;]{0,25}发布终止(?:药品试验)?数据保护公告',body):
            return
        if re.search(r'仅(?:公布|公示|记录|更新|咨询)|不(?:可以|可|得)(?:受理|批准)|不得申请数据保护|网络数据|个人信息|账号', self.norm):
            return
        # Same snapshot may contain both an announcement and its annex. A
        # bare 《实施办法》 in the announcement is not an annex binding.
        article_bound = bool(re.match(r'第(?:'+ORDINAL+r'|[0-9]+)条', norm(current['text'])))
        governance = []
        if not article_bound and mode == 'termination_releases_market_permission':
            parents = [c for c in self.contexts if c['kind'] == 'preceding_paragraph'
                       and c['source_ref'].get('sha256') == current['source_ref']['sha256']
                       and same_component(current,c)
                       and re.match(r'第(?:'+ORDINAL+r'|[0-9]+)条', norm(c.get('text','')))
                       and re.search(r'数据保护终止', norm(c.get('text','')))]
            before = norm(current['text']).split(self.norm,1)[0]
            if len(parents) == 1 and re.search(r'数据保护终止的[^。]{0,30}发布终止数据保护公告',before):
                article_bound = True
                governance = [self._quote(parents[0], '同一规范紧邻的保护终止条款，仅界定当前解除后果所指安排')]
        if not article_bound:
            return
        # Competing applicants need not be innovative. The limiting object
        # here is the protected DATA, not the competitor's drug category.
        if re.search(r'(?:仅|只)(?:适用于|涉及|保护|针对)[^。；;]{0,20}(?:非创新药|仿制药|生物类似药)[^。；;]{0,12}(?:试验数据|受保护数据|的数据)|(?:仅|只)(?:适用于|涉及|针对)[^。；;]{0,25}(?:自行取得且未依赖|不依赖受保护数据)', self.norm):
            return
        source_sha = current['source_ref']['sha256']
        articles = set()
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256',doc.get('snapshot_sha256')) == source_sha:
                if not same_component(current,doc):
                    return
                for group in doc.get('ordered_article_groups', []):
                    heading = re.fullmatch(ARTICLE_REFERENCE,group.get('article',''))
                    if heading:
                        member_ids = set(group.get('ordered_source_resource_ids',[]))
                        available = [c for c in self.contexts if self.origins.get(c['context_id'],{}).get('source_resource_id') in member_ids]
                        raw_members = [t for t in doc.get('source_texts',[]) if t.get('source_resource_id') in member_ids]
                        relevant = any(re.search(r'数据保护是指|上市许可之日起[^。；;]{0,12}给予[^。；;]{0,12}数据保护期|本条款中药品的数据保护范围',norm(m.get('text',''))) for m in available+raw_members)
                        if not relevant:
                            continue
                        if not same_component(current,group) or any(not same_component(current,m) for m in available+raw_members):
                            return
                        articles.add(ordinal_number(heading.group(1)))
        groups = []
        incomplete = False
        for article in sorted(articles):
            candidates = self._reference_candidates(current,article)
            if len(candidates) != 1:
                incomplete = True
                continue
            groups.append((article,candidates[0][1]))
        foundations, entitlement_groups, complete_other_entitlements = [], [], []
        for article,members in groups:
            definitions = [m for m in members if re.search(r'数据保护是指',m[2])
                           and re.search(r'试验数据',m[2]) and re.search(r'药品|生物制品',m[2])]
            permissions = [m for m in members if re.search(r'数据保护期内',m[2])
                           and re.search(r'未经[^。；;]{0,35}同意',m[2])
                           and re.search(r'依赖[^。；;]{0,25}数据[^。；;]{0,35}(?:药品上市许可|补充申请)',m[2])
                           and re.search(r'不予许可',m[2])
                           and re.search(r'自行取得[^。；;]{0,30}未依赖[^。；;]{0,20}除外',m[2])]
            if len(definitions)==len(permissions)==1:
                foundations.append((article,members,definitions[0],permissions[0]))
            entitlements = [m for m in members if re.search(r'(?<!非)(?:创新药|改良型新药)[^。；;]{0,25}上市许可之日起[^。；;]{0,8}给予[^。；;]{0,12}数据保护期',m[2])
                            and not re.search(r'不适用|不得|不予|不包括|不属于[^。；;]{0,8}(?:创新药|改良型新药)|非(?:创新药|改良型新药)|仅作为示例',m[2])]
            if entitlements:
                entitlement_groups.append((article,members,entitlements))
            elif any(re.search(r'(?:药品|药|制品)[^。；;]{0,25}上市许可之日起[^。；;]{0,8}给予[^。；;]{0,12}数据保护期',m[2]) for m in members):
                complete_other_entitlements.append((article,members))
        if incomplete or len(foundations)!=1 or not groups:
            self.material_requests.append({'path':'named_mechanism','reference':'药品试验数据保护的实际申请/准入后果',
                'missing':'同版有序条款未完整提供保护定义、依赖数据的准入排他后果及例外',
                'affected_dimensions':['I'],'dependency_status':'stopped'})
            return
        if not entitlement_groups:
            # Complete supplied scope without an innovation entitlement is a
            # semantic negative, not permission to infer from 原研 or 保密.
            if not complete_other_entitlements:
                self.material_requests.append({'path':'named_mechanism','reference':'数据保护实际权益适用分支',
                    'missing':'现有材料未提供完整权益适用条文，不能判定创新资格是否与当前保护后果相连',
                    'affected_dimensions':['I'],'dependency_status':'stopped'})
            return
        if len(entitlement_groups)!=1:
            self.material_requests.append({'path':'named_mechanism','reference':'创新资格的数据保护权益分支',
                'missing':'同版创新资格与具体数据保护权益分支不唯一','affected_dimensions':['I'],'dependency_status':'stopped'})
            return
        da,dm,definition,permission = foundations[0]
        ea,em,entitlements = entitlement_groups[0]
        # Read the complete bounded articles but inherit only the directly
        # relevant definition/permission and innovation entitlement roles.
        dq = [self._quote(m[0], '同一数据保护机制定义、排他准入与保留的同条例外',m[1]) for m in dm]
        iq = [self._quote(m[0], '创新资格直接取得保护期的实际权益分支；其他保护对象不因此均为创新',m[1]) for m in entitlements]
        complete = [self._quote(m[0], '完整同版权益条文仅作范围审查，不把数据内容要求复制给当前准入动作',m[1]) for m in em]
        selected = dq+iq
        self._add('named_mechanism',selected+governance,
            '当前实际申请、按保护期限授予准入或终止后解除准入限制，实施同版数据保护权益；创新资格对应明确保护期分支，保留非创新对象和自行取得数据除外，不改称研发技术服务',
            relation_subtype='bounded_data_protection_rights_consequence',
            content='\n'.join(q['text'] for q in selected),
            current_rights_anchor=self.current_anchor(*action_bounds),action_mode=mode,
            definition_quotes=dq,innovation_entitlement_quotes=iq,
            complete_entitlement_article_quotes=complete,
            innovation_scope='only_the_explicit_innovation_entitlement_branch',
            source_article_group_pointers=self._article_group_pointers(source_sha,[da,ea]),
            scope_binding={'source_sha256':source_sha,'context_ids':[q['context_id'] for q in selected+governance],
                           'article_level_current_action':True,'explicit_component_id':current.get('structure',{}).get('component_id') or current.get('source_ref',{}).get('locator',{}).get('component_id'),
                           'component_claim':'reject_conflicting_explicit_components; otherwise_exact_source_ordered_normative_article_binding','definition_article':da,'entitlement_article':ea},
            version_binding={'established':True,'binding':'exact_same_snapshot_complete_ordered_articles','source_sha256':source_sha},
            innovation_entitlement_not_entire_protected_population=True,
            research_technical_service_inferred=False)

    def _table_protection_branches(self):
        """Bind a table's basic duration to the same arrangement's definition.

        Exact table columns remain separate from a conditional remark. Only
        original ordered articles of the exact snapshot are eligible; reading
        an article group does not propagate its independent other branches.
        """
        current = self._current_source()
        if current is None or '|' not in self.norm or not re.search(r'数据保护期|保护期限', self.norm):
            return
        # Separator-adjacent whitespace is original layout, not cell content;
        # matches retain their actual offsets into the complete current row.
        cells = list(re.finditer(r'[^|\s](?:[^|]*[^|\s])?', self.norm))
        durations = [(i, c) for i, c in enumerate(cells) if re.fullmatch(r'\d+(?:\.\d+)?年', c.group())]
        if len(durations) != 1:
            return
        index, duration = durations[0]
        if index < 1:
            return
        subject = cells[index - 1]
        object_types = set(re.findall(r'原研|创新|改良', subject.group()))
        if not object_types or not re.search(r'药品|药物', subject.group()):
            return
        candidates = []
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != current['source_ref']['sha256']:
                continue
            for group in doc.get('ordered_article_groups', []):
                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))
                if not h:
                    continue
                article = ordinal_number(h.group(1))
                donors = self._reference_candidates(current, article)
                if len(donors) != 1:
                    continue
                container, members = donors[0]
                for pos, item in enumerate(members):
                    if not (object_types <= set(re.findall(r'原研|创新|改良', item[2]))
                            and re.search(r'给予' + re.escape(duration.group()) + r'数据保护期', item[2])):
                        continue
                    # A foreign/domestic listing qualifier is part of the
                    # subject binding and cannot be omitted as a mere name.
                    if ('境外' in item[2] and '境外' not in subject.group()
                            or '境内' in item[2] and '境内' not in subject.group()):
                        continue
                    scopes = [m for m in members[pos + 1:] if re.search(r'本条款中药品|本条中药品|前款药品', m[2])
                        and re.search(r'数据保护范围.{0,8}(?:包括|限于|涵盖)', m[2])]
                    if len(scopes) == 1:
                        candidates.append((article, container, item, scopes[0]))
        if len(candidates) != 1:
            self._request('cited_standard', subject.group() + '|' + duration.group(),
                '整表行基础保护待遇缺少同源唯一对象、期限及条内数据范围定义', 'required_reference_unresolved')
            return
        bridges = []
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != current['source_ref']['sha256']:
                continue
            for group in doc.get('ordered_article_groups', []):
                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))
                if not h:
                    continue
                donors = self._reference_candidates(current, ordinal_number(h.group(1)))
                if len(donors) == 1:
                    for item in donors[0][1]:
                        if re.search(r'详见附表|见附表|见附录', item[2]) and re.search(r'数据保护', item[2]):
                            bridges.append((ordinal_number(h.group(1)), donors[0][0], item))
        if len(bridges) != 1:
            self._request('cited_standard', duration.group(), '当前附表与保护安排正文的同源确切连接缺失或不唯一', 'required_reference_unresolved')
            return
        article, container, treatment, scope = candidates[0]
        bridge_article, bridge_container, bridge = bridges[0]
        evidence = [self._quote(bridge[0], '同源定义明确连接附表保护安排', bridge[1]),
                    self._quote(treatment[0], '当前表行基础对象及期限的同条款定义', treatment[1]),
                    self._quote(scope[0], '基础保护待遇的条内试验数据范围定义', scope[1])]
        self._table_current_object = self.current_anchor(subject.start(), subject.end())
        self._add('cited_standard', evidence,
            '完整表行的基础期限与条件例外分别读取；仅补基础同一对象、同一期限及条内数据范围，未将例外先行条件移入基础',
            relation_subtype='complete_table_basic_protection_definition', protection_branch='base_table_arrangement',
            current_object_anchor=self.current_anchor(subject.start(), subject.end()),
            current_consequence_anchor=self.current_anchor(duration.start(), duration.end()),
            basic_duration=duration.group(), exception_not_inherited=True,
            source_article_group_pointers=self._article_group_pointers(current['source_ref']['sha256'], [bridge_article, article]),
            reference_chain=[{'article': bridge_article, 'context_id': bridge_container['context_id'], 'relation': 'explicit_appendix_connection'},
                             {'article': article, 'context_id': container['context_id'], 'relation': 'same_object_duration_and_article_scope',
                              'treatment_context_id': treatment[0]['context_id'], 'scope_context_id': scope[0]['context_id']}],
            version_binding={'established': True, 'binding': 'exact_same_snapshot', 'source_sha256': current['source_ref']['sha256']})

    def _article_group_pointers(self, source_sha, articles):
        pointers = []
        for di, doc in enumerate(self.bundle.get('explicit_or_primary_source_resources', [])):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != source_sha:
                continue
            for gi, group in enumerate(doc.get('ordered_article_groups', [])):
                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))
                if h and ordinal_number(h.group(1)) in articles:
                    pointers.append(f'/explicit_or_primary_source_resources/{di}/ordered_article_groups/{gi}')
        return pointers

    def _operative_references(self):
        current = self._current_source()
        if current is None:
            return
        for reference in re.finditer(ARTICLE_REFERENCE, self.norm):
            before = self.norm[max(0, reference.start() - 16):reference.start()]
            operative = re.search(r'(?:不符合|符合|未满足|满足|核验|审核)[^。；;|]{0,12}$', before)
            branch_tail = re.split(r'[。；;|]', self.norm[reference.end():], maxsplit=1)[0]
            consequence = re.search(
                rf'(?:数据保护期|保护期)(?:暂定|确定|应当|应|可以|可|仅|将|则)?为(?:\d+(?:\.\d+)?|{ORDINAL})(?:个)?(?:年|月|日|天)'
                r'|(?:数据保护期|保护期)[^。；;|]{0,8}(?:给予|享受|不予|限制|缩短|延长)'
                r'|(?:予以|给予|授予|取消|终止|不得|不予)[^。；;]{0,20}(?:许可|准入|待遇|权利|保护|支持)'
                r'|(?:可以|可|准许)[^。；;]{0,12}(?:申请|获得)[^。；;]{0,18}(?:许可|保护|待遇|支持)',
                branch_tail)
            if not operative or not consequence:
                continue
            if re.search(r'(?:另一|其他|另外|另一个).{0,8}(?:药品|药物|品种|项目)',
                         branch_tail[:consequence.end()]):
                continue
            article = ordinal_number(reference.group(1))
            clause = ordinal_number(reference.group(2)) if reference.group(2) else None
            candidates = self._reference_candidates(current, article)
            if len(candidates) != 1:
                self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(),
                    'missing': '当前条件—实质待遇确指的同源条款缺失或不能唯一绑定'})
                continue
            container, members = candidates[0]
            if clause is not None and not 1 <= clause <= len(members):
                self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(),
                    'missing': '当前确指款次未在同源有界条文中完整提供'})
                continue
            selected = members if clause is None else [members[clause - 1]]
            evidence, antecedents = [], []
            current_object_binding = None
            if clause and re.search(r'该药品|本药品|该药物|本药物', selected[0][2]):
                if '|' in self.norm and getattr(self, '_table_current_object', None):
                    # The complete current row and its independently bound
                    # basic same-object definition already name the subject.
                    # Do not quote or use the previous first-indication clause.
                    current_object_binding = self._table_current_object
                else:
                    current_object_binding = None
                preceding = members[clause - 2] if clause > 1 else None
                if (current_object_binding is None and (preceding is None or not re.search(OBJECT, preceding[2])
                        or re.search(r'(?:另一|其他|另外|另一个).{0,8}(?:药品|药物)', preceding[2]))):
                    self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(),
                        'missing': '被援引款的药品指代缺少同条紧邻对象及完整限定条件'})
                    continue
                # A nominal anaphor identifies the drug subject; it does not
                # import the preceding clause's independent application or
                # first-indication eligibility. The cited clause retains its
                # own conditions and consequential reference separately.
                if current_object_binding is None:
                    raw = preceding[0]['text'][preceding[1][0]:preceding[1][1]]
                    normalized, offsets = matching_view(raw)
                    subject = re.match(r'(?:' + ARTICLE_REFERENCE + r')?[^，,。；;]{0,70}(?:药品|药物)(?=[，,。；;]|$)', normalized)
                    if subject is None:
                        self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(),
                            'missing': '被援引款药品指代不能与上一款独立条件分开定位'})
                        continue
                    left, right = raw_span(offsets, subject.start(), subject.end())
                    subject_span = (preceding[1][0] + left, preceding[1][0] + right)
                    antecedents.append((preceding[0], subject_span, subject.group()))
                    evidence.append(self._quote(preceding[0], '仅定位被援引款同条药品先行对象；不继承上一款独立条件', subject_span))
            for child, span, part in selected:
                evidence.append(self._quote(child, '当前条件—待遇明确援引的精确条款', span))
            chain = [{'article': article, 'clause': clause, 'container_context_id': container['context_id'],
                      'context_ids': [item[0]['context_id'] for item in selected]}]
            unexpanded = [{'reference': m.group(), 'reason': '对象先行词内部引用不继续展开'}
                          for item in antecedents for m in re.finditer(ARTICLE_REFERENCE, item[2])]
            data_scope_evidence = []
            permission_evidence = []
            further_missing = False
            for child, span, part in selected:
                for further in re.finditer(ARTICLE_REFERENCE, part):
                    if further.start() == 0 and re.match(ARTICLE_REFERENCE, part):
                        continue
                    further_article = ordinal_number(further.group(1))
                    if further_article == article:
                        continue
                    prefix = part[max(0, further.start() - 12):further.start()]
                    if (not re.search(r'按照|依照|适用|执行', prefix)
                            or not re.search(r'(?:数据)?保护(?:的)?(?:数据)?范围|相应.{0,6}数据|受保护(?:的)?数据', part)):
                        unexpanded.append({'reference': further.group(), 'reason': '非本款明确数据范围/权利后果引用'})
                        continue
                    if len(chain) >= 2:
                        unexpanded.append({'reference': further.group(), 'reason': '有限关系最多展开一个进一步确指条款'})
                        continue
                    donors = self._reference_candidates(current, further_article)
                    if len(donors) != 1:
                        further_missing = True
                        self.material_requests.append({'path': 'cited_standard', 'reference': further.group(),
                            'missing': '精确款再援引的数据保护范围/许可后果同源原文缺失或不唯一'})
                        continue
                    donor, donor_members = donors[0]
                    further_clause = ordinal_number(further.group(2)) if further.group(2) else None
                    if further_clause is not None:
                        if not 1 <= further_clause <= len(donor_members):
                            further_missing = True
                            self.material_requests.append({'path': 'cited_standard', 'reference': further.group(),
                                'missing': '再援引的精确款次未在同源有界条文中提供'})
                            continue
                        donor_members = [donor_members[further_clause - 1]]
                    scope = []
                    for item in donor_members:
                        subject = re.search(r'(?:数据)?保护(?:的)?(?:数据)?范围|受保护(?:的)?数据', item[2])
                        content = item[2][subject.end():] if subject else ''
                        if (subject and re.search(r'包括|限于|涵盖|仅保护|不包括', content)
                                and re.search(r'数据|证据|试验|研究|安全性|有效性|疗效|临床优势', content)):
                            scope.append(item)
                    permissions = [item for item in donor_members if re.search(r'(?:数据)?保护期(?:间|内)', item[2])
                                   and re.search(r'(?:不予|准予|予以|不得|不再|可以).{0,12}(?:许可|批准|依赖|使用)'
                                                 r'|(?:未经|经).{0,16}同意|(?:有权|享有).{0,12}(?:许可|同意|保护)'
                                                 r'|禁止.{0,12}(?:依赖|使用)', item[2])]
                    if not scope or not permissions:
                        further_missing = True
                        self.material_requests.append({'path': 'cited_standard', 'reference': further.group(),
                            'missing': '再援引条文未完整提供当前确指的数据范围及保护期间许可后果'})
                        continue
                    for item in scope:
                        data_scope_evidence.append(self._quote(item[0], '本款明确再援引的数据保护范围及排除内容', item[1]))
                    for item in permissions:
                        permission_evidence.append(self._quote(item[0], '本款保护待遇对应的期间许可后果及例外', item[1]))
                    evidence.extend(data_scope_evidence + permission_evidence)
                    chain.append({'article': further_article, 'clause': further_clause,
                                  'container_context_id': donor['context_id'],
                                  'context_ids': [item[0]['context_id'] for item in scope + permissions]})
                    unexpanded.extend({'reference': m.group(), 'reason': '进一步范围/许可条文不作第三层展开'}
                                      for item in scope + permissions for m in re.finditer(ARTICLE_REFERENCE, item[2]))
            if further_missing:
                continue
            start = max(0, reference.start() - 16) + operative.start()
            consequence_start = reference.end() + consequence.start()
            self._add('cited_standard', evidence,
                '当前以精确条款条件决定实质保护待遇，仅补该款同条对象及其明确数据范围/许可后果；不继承独立兄弟待遇',
                relation_subtype='finite_operational_article_reference',
                protection_branch='conditional_table_exception' if '|' in self.norm else 'current_operative_reference',
                antecedent_scope='nominal_drug_subject_only; no_independent_preceding_eligibility',
                action_scope='explicit_article_condition_substantive_consequence',
                current_condition_anchor=self.current_anchor(start, reference.end()),
                current_consequence_anchor=self.current_anchor(consequence_start, reference.end() + consequence.end()),
                reference_chain=chain, reference_container_ids=[step['container_context_id'] for step in chain],
                object_definition=current_object_binding['text'] if current_object_binding else '\n'.join(item[0].get('text', '')[item[1][0]:item[1][1]] for item in antecedents),
                current_object_binding=current_object_binding,
                qualification_text='\n'.join(e['text'] for e in evidence if e not in permission_evidence),
                qualification_context_evidence=[e for e in evidence if e not in permission_evidence],
                treatment_context_evidence=permission_evidence,
                standard_text='\n'.join(e['text'] for e in evidence), unexpanded_references=unexpanded,
                bounded_reference_depth=2)

    def _applicable_support(self):
        current = self._current_source()
        if current is None or not re.search(r'(?:创新|改良)(?:型)?药(?:品|物)?', self.norm):
            return
        arrangement = re.search(r'(?:本|该)(?:(?:工作)?规范|办法|规程|程序|方案|安排)', self.norm)
        authorization = re.search(r'(?:不再|不得|不能|可以|可|准许|允许)[^。；;]{0,45}(?:适用|使用|按照|依据)', self.norm)
        early_stage = re.search(r'临床试验[^。；;]{0,18}(?:完成前|结束前)|上市前|申报前|申请前|研发阶段|提前', self.norm)
        if not arrangement or not authorization or not early_stage or authorization.end() > arrangement.start():
            return
        noun = arrangement.group()[1:]
        arrangement_reference = (r'(?:本|该)(?:工作)?规范' if noun.endswith('规范')
                                 else rf'(?:本|该){re.escape(noun)}')
        source_sha = current.get('source_ref', {}).get('sha256')
        groups = []
        for boundary in self.contexts:
            st = boundary.get('structure', {})
            ids = st.get('scope_context_ids', [])
            if (boundary['kind'] != 'following_heading' or not ids or len(ids) != len(set(ids))
                    or boundary.get('source_ref', {}).get('sha256') != source_sha
                    or not same_component(boundary, current)):
                continue
            members = [self.by_id.get(cid) for cid in ids]
            if any(not c or c['kind'] != 'source_paragraph'
                   or c.get('source_ref', {}).get('sha256') != source_sha
                   or not same_component(c, current) or not c.get('text') for c in members):
                continue
            current_copies = [c for c in members if norm(c.get('text', '')) == self.norm]
            if len(current_copies) != 1 or any(not same_component(c, current_copies[0]) for c in members):
                continue
            first, last = st.get('component_first_paragraph'), st.get('component_last_paragraph')
            containers = [c for c in self.contexts if c['kind'] == 'source_paragraph'
                and c.get('source_ref', {}).get('sha256') == source_sha and same_component(c, current)
                and c.get('structure', {}).get('first_paragraph') == first
                and c.get('structure', {}).get('last_paragraph') == last]
            if not first or not last or len(containers) != 1:
                continue
            if st.get('follows_context_id') != ids[-1]:
                continue
            groups.append((boundary, containers[0], members))
        if len(groups) != 1:
            self.material_requests.append({'path': 'named_mechanism', 'reference': arrangement.group(),
                'missing': '当前申请前适用/限制确指的同源规范组件范围不能闭合绑定'})
            return
        boundary, container, members = groups[0]
        objects, stages, supports = [], [], []
        for c in members:
            raw = c.get('text', '')
            for a, b in sentence_spans(raw):
                part = norm(raw[a:b])
                if (re.search(r'适用范围', part) or re.search(arrangement_reference + r'适用于', part)) and re.search(r'创新|改良', part):
                    objects.append(self._quote(c, '同一规范有界组件的对象及排除范围', (a, b)))
                if (re.search(arrangement_reference, part) and re.search(r'研发阶段|临床试验.{0,35}完成后|上市前|申报前', part)
                        and norm(raw) != self.norm):
                    stages.append(self._quote(c, '同一规范通常适用的上市前研究阶段', (a, b)))
                if (re.search(r'沟通交流(?:时限|期限).{0,16}\d+(?:个)?(?:工作)?(?:日|天)', part)
                        or re.search(r'(?:品种)?审评(?:时限|期限).{0,45}(?:优先审评|单独序列|\d+(?:个)?(?:工作)?(?:日|天))', part)
                        or re.search(r'(?:实行|设置|开放|采用).{0,12}(?:单独序列|优先审评).{0,20}(?:缩短|加快|时限)', part)
                        or re.search(r'(?:提供|可申请|获得).{0,18}(?:研究方案反馈|试验方案反馈|研发技术咨询|技术服务)', part)):
                    if not re.search(r'(?:不提供|不开展|仅提供).{0,20}(?:电话|视频|渠道|一般资料)', part):
                        supports.append(self._quote(c, '当前提前适用直接开放的同规范办理便利/技术支持', (a, b)))
        if not objects or not stages or not supports:
            # The supplied component is structurally closed and every listed
            # paragraph's source text is present. Absent qualifying content is
            # a criterion failure, not an invitation to request imagined support.
            return
        self._add('named_mechanism', objects + stages + supports,
            '当前明确创新药申请前适用/限制同一规范，仅补同组件对象、通常研究阶段及直接可用便利；不复制平行义务',
            relation_subtype='bounded_rule_preapplication_authorization',
            object_definition='\n'.join(e['text'] for e in objects),
            direct_mechanism='\n'.join(e['text'] for e in supports),
            research_stage='\n'.join(e['text'] for e in stages),
            current_authorization_anchor=self.current_anchor(authorization.start(), arrangement.end()),
            mechanism_name=arrangement.group(),
            version_binding={'established': True, 'binding': 'same_source_closed_component', 'source_sha256': source_sha},
            scope_binding={'container_context_id': container['context_id'], 'boundary_context_id': boundary['context_id'],
                           'context_ids': boundary['structure']['scope_context_ids'],
                           'component_first_paragraph': boundary['structure']['component_first_paragraph'],
                           'component_last_paragraph': boundary['structure']['component_last_paragraph']})

    def _mechanisms(self):
        action = re.search(ACTION, self.norm)
        if not action:
            return
        matched_source = False
        for c in self.contexts:
            if not self._neutral_source(c) or not c.get('text'):
                continue
            meta = self._metadata(c)
            title = meta.get('document_title') or meta.get('source_title', '')
            key = title_key(title)
            if len(key) < 6:
                continue
            action_clause = None
            for clause in re.findall(r'[^。；;，,]+', self.norm):
                clean = title_key(clause)
                pos = clean.find(key)
                if pos < 0:
                    continue
                before, after = clean[:pos], clean[pos + len(key):]
                actions = list(re.finditer(ACTION, before))
                if (not actions or len(before) - actions[-1].end() > 35
                        or re.search(r'详见|附件|名称|资料|归档|格式|印发', before[actions[-1].end():])
                        or re.match(r'(?:资料|文件|的?归档|名称|格式)', after)):
                    continue
                action_clause = clause
                break
            if action_clause is None:
                continue
            matched_source = True
            ver = self._version(c, action_clause)
            if not ver['established']:
                self.material_requests.append({'path': 'named_mechanism', 'reference': title,
                                               'missing': '具名机制的行动时期与来源版本未能绑定', 'version_binding': ver})
                continue
            text = c['text']
            objects, mechanisms = [], []
            for a, b in sentence_spans(text):
                s = norm(text[a:b])
                if re.search(r'(?:范围|适用对象|适用于|面向).{0,65}(?:创新|改良)|(?:创新|改良).{0,20}(?:范围|适用对象)', s):
                    objects.append(self._quote(c, '同版安排的对象与排除范围', (a, b)))
                if re.search(r'(?:审评|审批).{0,20}(?:\d+个?工作日|缩短|加快)|(?:\d+个?工作日).{0,20}(?:完成|审评|审批)|(?:提供|开展|申请|获得).{0,20}(?:技术服务|方案反馈|沟通交流)', s):
                    # Only convenience/resources. Do not copy safety obligations,
                    # outcomes, fees, or program governance from full plan text.
                    if not re.search(r'廉政|纪律|风险.{0,8}义务', s):
                        mechanisms.append(self._quote(c, '当前实施行为直接对应的研发安排', (a, b)))
            if objects and mechanisms:
                self._add('named_mechanism', objects + mechanisms,
                          '当前实质实施同一具名安排，按来源日期绑定，仅补对象及直接可用机制',
                          object_definition='\n'.join(e['text'] for e in objects),
                          direct_mechanism='\n'.join(e['text'] for e in mechanisms),
                          version_binding=ver, mechanism_name=title)
            else:
                self.material_requests.append({'path': 'named_mechanism', 'reference': title,
                                               'missing': '同版安排缺少可定位对象定义或直接机制原文'})
        if (not matched_source and re.search(r'(?:实施|设立|开放|组织开展).{0,40}(?:创新|改良).{0,35}(?:试点|计划|通道)', self.norm)
                and not re.search(r'(?:试点|计划|通道)(?:资料|文件|的?归档|名称|格式)', self.norm)
                and not re.search(r'提供.{0,20}(?:反馈|技术服务)|加快.{0,15}审评|缩短.{0,15}(?:研发|试验)', self.norm)):
            self.material_requests.append({'path': 'named_mechanism', 'reference': self.text,
                                           'missing': '当前实质实施具名支持安排，缺少同版对象与直接可用机制原文'})
        # A bare generic reference is not an invitation to recurse into policy.

    def _explanations(self):
        explanations = [c for c in self.contexts if self._neutral_source(c)
                        and ('解读' in self._metadata(c).get('source_document_kind', '')
                             or self._metadata(c).get('source_document_kind') == 'official_policy_explainer')]
        if not explanations or not re.search(r'建设|优化|建立|完善|保障|改进', self.norm):
            return
        # Measures must literally map to current phrases, not merely share topic.
        features = re.findall(r'(?:偏远地区|县域中心药房|上下.{0,5}用药衔接|基层药品配送)', self.norm)
        groups = {}
        for c in explanations:
            meta = self._metadata(c)
            binding = (c.get('source_ref', {}).get('sha256'), meta.get('policy_document_number'),
                       meta.get('policy_document_date'), meta.get('source_title'))
            if not all(binding) or not self._version(c)['established']:
                continue
            groups.setdefault(binding, []).append(c)
        for binding, group in groups.items():
            measure_quotes, problem_quotes = [], []
            for c in group:
                for a, b in sentence_spans(c['text']):
                    s = norm(c['text'][a:b])
                    if not any(f in s for f in features):
                        continue
                    if re.search(r'鼓励|建设|优化|建立|完善', s):
                        measure_quotes.append(self._quote(c, '官方解释与当前同一措施的文字映射', (a, b)))
                    if re.search(r'不稳定|断供|可及性差|不畅|差异|不平衡|能力弱|障碍', s):
                        problem_quotes.append(self._quote(c, '该措施明确对应的药品获取问题', (a, b)))
            if measure_quotes and problem_quotes:
                self._add('policy_explanation', problem_quotes + measure_quotes,
                          '共同包同政策解释按当前措施的原文字面关系补足对象及问题，不扩散其他措施',
                          problem_text='\n'.join(e['text'] for e in problem_quotes),
                          measure_text='\n'.join(e['text'] for e in measure_quotes),
                          version_binding=[self._version(c) for c in group], policy_binding=binding)

    def _anaphors(self):
        # A supplied self-declared scope may establish object only, never labels.
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts
                           if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            st = c.get('structure', {})
            t = c.get('text', '')
            if current_sources and c.get('source_ref', {}).get('sha256') not in current_sources:
                continue
            if (st.get('source_role') == 'self_declared_scope' or
                (c['kind'] == 'source_paragraph' and re.search(r'^\(?[一二三四五六七八九十]+\)?.{0,3}适用范围', norm(t)))) and re.search(OBJECT, norm(t)):
                self._add('anaphor', [self._quote(c, '同组件/适用范围仅用于确认当前对象')],
                          '原文同组件范围说明对象；不复制其他维度内容', object_text=t)

    def _tables(self):
        # Supplied cell coordinates bind content to its column. A number cannot
        # inherit an unrelated column or all dimensions in the table heading.
        current_cells = [c for c in self.contexts if c['kind'] in ('table_row_cell', 'table_row')
                         and norm(c.get('text', '')) == self.norm]
        for cell in current_cells:
            st = cell.get('structure', {})
            columns = st.get('column_indices', [st.get('column_index')])
            headers = [c for c in self.contexts if c['kind'] in ('table_header_cell', 'table_header')
                       and c.get('text') and c.get('structure', {}).get('column_index') in columns
                       and c.get('source_ref', {}).get('sha256') == cell.get('source_ref', {}).get('sha256')]
            for header in headers:
                self._add('parent_predicate', [self._quote(header, '同表同列标题补全当前单元格内容')],
                          '来源表格坐标建立当前值与同列内容对象的关系',
                          shared_predicate=header['text'], member_text=self.text,
                          table_cell_binding={'row': st.get('row_index_zero_based'), 'columns': columns})

    def _resource_definitions(self):
        # A team name alone supplies no service. The current set-up action may
        # refer to a resource whose concrete function is defined in the same
        # source paragraph, with an explicit scope and research-stage clause.
        entity = re.search(r'(?:组建|建立|设立|安排)([^。；;，,]{1,15}团队)', self.norm)
        if not entity:
            return
        scope = [r for r in self.linked('anaphor')]
        for paragraph in self.contexts:
            raw = paragraph.get('text', '')
            if paragraph['kind'] != 'paragraph' or self.text not in raw:
                continue
            source_sha = paragraph.get('source_ref', {}).get('sha256')
            services = []
            for a, b in sentence_spans(raw):
                part = norm(raw[a:b])
                bound_entity = re.search(rf'(?:{re.escape(entity.group(1))}|该团队|本团队|此团队).{{0,15}}(?:负责|提供|服务)', part)
                if (bound_entity and not re.search(r'另一(?:支|个)?团队|其他团队|另一支[^。]{0,15}团队|其他[^。]{0,15}团队', part)
                        and re.search(r'技术审评|方案反馈|技术咨询|研究反馈', part)):
                    services.append(self._quote(paragraph, '当前所设资源在同段的实际技术服务定义', (a, b)))
            stages = [c for c in self.contexts if c['kind'] == 'source_paragraph'
                      and c.get('source_ref', {}).get('sha256') == source_sha
                      and same_component(c, paragraph)
                      and re.search(r'研发阶段|临床试验.{0,60}(?:上市前|研发阶段)', norm(c.get('text', '')))
                      and re.search(r'上市前', norm(c.get('text', '')))]
            objects = [e for r in scope for e in r['context_evidence']
                       if e['source_ref'].get('sha256') == source_sha
                       and same_component(self.by_id[e['context_id']], paragraph)]
            stages = [c for c in stages if all(same_component(c, self.by_id[e['context_id']]) for e in objects)]
            if services and stages and objects:
                stage_quotes = [self._quote(c, '同组件明确适用的上市前研发阶段') for c in stages]
                self._add('named_mechanism', objects + services + stage_quotes,
                          '当前设立资源与同段功能定义直接承接，同源适用范围及上市前阶段补对象；团队名称本身不充分',
                          object_definition='\n'.join(e['text'] for e in objects),
                          direct_mechanism='\n'.join(e['text'] for e in services),
                          research_stage='\n'.join(e['text'] for e in stage_quotes),
                          version_binding={'established': True, 'binding': 'same_source_component', 'source_sha256': source_sha},
                          mechanism_name=entity.group(1), resource_definition_required=True)

    def object_evidence(self, a=0, b=None):
        b = len(self.norm) if b is None else b
        candidates = list(re.finditer(OBJECT, self.norm))
        if candidates:
            m = min(candidates, key=lambda m: abs(m.start() - a))
            return {'established': True, 'current_anchors': [self.current_anchor(m.start(), m.end())],
                    'context_evidence': [], 'object_text': m.group(), 'role': 'current_drug_or_treatment_object',
                    'reason': '当前完整命题直接表达药品、研发或患者治疗对象'}
        # Object clarification from direct parent / explicit scope only.
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts
                           if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            if c['kind'] not in ('parent_paragraph', 'heading'):
                continue
            if current_sources and c.get('source_ref', {}).get('sha256') not in current_sources:
                continue
            m = re.search(OBJECT, norm(c.get('text', '')))
            if m:
                return {'established': True, 'current_anchors': [],
                        'context_evidence': [self._quote(c, '承接对象解释，不作维度内容')],
                        'object_text': c['text'], 'role': 'explicit_parent_or_heading_object',
                        'reason': '直接父句或标题仅补当前对象'}
        for rel in self.linked('parent_predicate'):
            if rel['details'].get('table_cell_binding') and re.search(OBJECT, rel['details']['content']):
                return {'established': True, 'current_anchors': [], 'context_evidence': rel['context_evidence'],
                        'object_text': rel['details']['content'], 'role': 'same_table_same_column_object',
                        'reason': '当前单元格按来源同列标题建立对象'}
        if re.search(r'具体品种|该品种|相关品种|本品种|该项目|本项目', self.norm):
            for rel in self.linked('anaphor'):
                return {'established': True, 'current_anchors': [],
                        'context_evidence': rel['context_evidence'],
                        'object_text': rel['details']['object_text'],
                        'role': 'same_source_explicit_scope_anaphor',
                        'reason': '当前品种/项目指代由同来源明确适用范围补全对象；内容仍由当前行动判断'}
        return {'established': False, 'current_anchors': [], 'context_evidence': [],
                'object_text': '', 'role': None, 'reason': '当前及明确承接范围未建立药品/患者治疗对象'}
