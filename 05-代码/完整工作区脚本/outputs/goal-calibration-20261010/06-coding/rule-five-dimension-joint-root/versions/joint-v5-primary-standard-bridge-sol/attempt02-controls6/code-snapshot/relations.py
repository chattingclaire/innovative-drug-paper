# ROOT five-dimensional joint developer candidate; no cohort release or formal acceptance.
"""Bounded source relations. No record identity, outcome, or corpus access.

The source graph supplies positions and original text. Relations are computed here;
they are not dimension permissions. Classification remains in dimensions.py.
"""
import re
import json
import hashlib
from evidence import matching_view, raw_span, anchor, context_anchor
OBJECT = '药品|药物|新药|本药|该药|研究药|试验药|用药|疗效|患者|治疗|制剂|片剂|剂型|研发|生物制品|中药'
INTRO = '下列|以下(?!简称)|同时满足|条件之一|具体包括'
SUBSTANTIVE = '申请|纳入|符合|应.{0,12}(?:评价|比较|提供|说明|证据)|支付|享受|可.{0,12}(?:获得|适用|使用)'
ACTION = '决定开展|组织开展|组织实施|同意.{0,30}开展|设立|开放|实施|撤回|终止|取消|限制|适用'
PROGRAM = '[\\u4e00-\\u9fff]{2,24}(?:程序|计划|通道|试点)'
ORDINAL = '[零〇一二两三四五六七八九十百千0-9]+'
ARTICLE_REFERENCE = f'第({ORDINAL})条(?:第({ORDINAL})款)?'
PROGRAMME_HEADING_RE = f'(?m)^[ \\t]*(?:第{ORDINAL}[章节][ \\t]*)?(?P<name>(?:[\\u4e00-\\u9fff][ \\t]*){{2,35}}(?:程序|计划|通道|试点))(?:[（(][^）)\\n]{{1,12}}[）)])?[ \\t]*$'

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
    return [(m.start(), m.end()) for m in re.finditer('[^。\\n]+(?:。|\\n|$)', text)]

def title_key(title):
    t = re.sub('[\\W_]', '', norm(title))
    return re.sub('关于|改革|工作方案|工作规范|工作|试行|要求|通知|政策解读', '', t)

def same_component(left, right):

    def component(c):
        return c.get('structure', {}).get('component_id') or c.get('source_ref', {}).get('locator', {}).get('component_id')
    a, b = (component(left), component(right))
    return not (a and b and (a != b))

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def structure_ordinal(value, suffix):
    """Parse an address scalar, never original text or a closure proof."""
    if type(value) is int:
        return value if value >= 1 else None
    if type(value) is not str:
        return None
    label = re.fullmatch('(?:第)?(' + ORDINAL + ')(?:' + suffix + ')?', norm(value))
    number = ordinal_number(label.group(1)) if label else None
    return number if number is not None and number >= 1 else None

def article_number(value):
    # Preserve the existing full-address string interface, including a clause
    # suffix; that suffix is reconciled separately with actual source text.
    if type(value) is str:
        address=re.fullmatch(ARTICLE_REFERENCE,norm(value))
        if address:
            number=ordinal_number(address.group(1))
            return number if number is not None and number>=1 else None
    return structure_ordinal(value, '条')

def clause_number(value):
    return structure_ordinal(value, '款')

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
        self.structural_address_issues = []
        self.relations = []
        self._parents()
        self._local_operations()
        self._lists()
        self._standards()
        self._operative_value_definition()
        self._table_protection_branches()
        self._operative_references()
        self._mechanisms()
        self._explanations()
        self._anaphors()
        self._applicable_support()
        self._resource_definitions()
        self._postadmission_technical_support()
        self._price_arrangement_definition()
        self._tables()
        self._complete_source_relations()
        self._bounded_IF_semantic_support()
        self._bounded_IF_right_operation()
        self._bounded_IF_modification_bridge()
        self._bounded_IF_table_qualification()
        self._bounded_IF_individual_consultation()
        self._bounded_IF_first_member()
        self._bounded_IF_missing_dependency()
        self._se_bounded_content()
        self._se_direct_content_parents()
        self._se_complete_lists()
        operational_request_start = len(self.material_requests)
        self._se_operational_references()
        self._IF_closed_operational_content(self.material_requests[operational_request_start:])
        self._IF_named_feedback_access()
        for request in self.material_requests:
            if request not in self.source_requests:
                self.source_requests.append(dict(request, dependency_status='stopped'))
        self.source_scope_review = {'status': 'complete', 'source_evidence_note': '原CTX文字与结构逐字段读取；完整来源对象的结构、文字及身份已解析。仅当前确指、完整组或同版具名关系使用选定原文；图片未读取，全文不自动适用。'}

    def match(self, pattern, text=None):
        return list(re.finditer(pattern, self.norm if text is None else norm(text)))

    def current_anchor(self, a, b):
        a, b = raw_span(self.offsets, a, b)
        return anchor(self.text, a, b)

    def proposition(self, a=0, b=None):
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
        signature = (kind, tuple(((e['context_id'], e['start'], e['end'], e['text'], e['source_ref'].get('sha256')) for e in evidence)), details.get('relation_subtype'), tuple(sorted(details.get('affected_dimensions', ['S', 'E', 'Ec', 'I', 'F']))), bool(details.get('only_IF_consumers')), details.get('norm_start'), details.get('norm_end'), details.get('shared_predicate'))
        for old in self.relations:
            if old['_signature'] == signature:
                return
        d = {'content': '\n'.join((e['text'] for e in evidence)), 'context_ids': [e['context_id'] for e in evidence], 'full_scope': True, 'relation_reason': reason, **details}
        used = []
        for e in evidence:
            for view in self._used_views(e['context_id'], e, reason):
                if view not in used:
                    used.append(view)
        pointer = details.get('source_group_pointer')
        if pointer and pointer.startswith('/explicit_or_primary_source_resources/'):
            doc = self.bundle['explicit_or_primary_source_resources'][int(pointer.split('/')[2])]
            used.append({'resource_id': doc['source_resource_id'], 'view': 'document_bundle', 'use_scope': {'reason': reason, 'geometry_pointer': pointer, 'printed_operator': details.get('group_operator'), 'scope': 'selected_complete_numbered_geometry; not_whole_source_inheritance'}})
        for pointer in details.get('source_article_group_pointers', []):
            doc = self.bundle['explicit_or_primary_source_resources'][int(pointer.split('/')[2])]
            used.append({'resource_id': doc['source_resource_id'], 'view': 'document_bundle', 'use_scope': {'reason': reason, 'source_article_group_pointer': pointer, 'scope': 'exact_original_article_order_and_clause_identity; selected_branch_only'}})
        raw_ids = {c['context_id'] for c in self.bundle.get('source_record', {}).get('contexts', self.all_contexts)}
        for cid in details.get('reference_container_ids', []):
            if cid in raw_ids:
                used.append({'resource_id': cid, 'view': 'geometry', 'use_scope': {'reason': reason, 'scope': 'bounded_reference_members_and_order', 'reference_chain': details.get('reference_chain')}})
        self.relations.append({'kind': kind, 'current_anchor': self.proposition(), 'context_evidence': evidence, 'details': d, 'used_source_views': used, '_signature': signature})
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
            self.source_view_events.append({'resource_id': rid, 'view': view, 'source_sha256': sha, 'view_sha256': view_sha, 'locator_read': locator, 'event_kind': 'actual_structured_json_scan', 'consumption_scope': scope})

    def _scan_source_views(self):

        def scan(value):
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
            if origin.get('origin_inventory_view') == 'text' and isinstance(c.get('text'), str) and (origin.get('origin_inventory_view_sha256') == digest(c['text'])):
                self._event(origin['origin_inventory_resource_id'], 'text', c['source_ref']['sha256'], digest(c['text']), c['source_ref'].get('locator', {}), 'complete_exact_literal_text_resource; original_role_identity_parsed; no_pixels')
            if c['context_id'] not in raw_ids:
                continue
            ref = c['source_ref']
            fields = {k: c[k] for k in ('text', 'title', 'caption', 'headers', 'row_cells') if k in c}
            if fields:
                self._event(c['context_id'], 'text', ref['sha256'], digest(canonical(fields)), ref.get('locator', {}), 'complete_CTX_text_fields_normalized; availability_does_not_establish_applicability')
            self._event(c['context_id'], 'geometry', ref['sha256'], digest(canonical(c.get('structure', {}))), ref.get('locator', {}), 'complete_CTX_structure_parsed; links_order_scope_and_roles_only')
        for field, prefix, view in (('explicit_or_primary_source_resources', None, 'document_bundle'), ('preserved_historical_neutral_source_supplements', 'HISTORICALSOURCE-', 'text'), ('source_full_text_resources', 'FULLSOURCE-', 'text')):
            for obj_index, obj in enumerate(self.bundle.get(field, [])):
                scan(obj)
                if field == 'source_full_text_resources' and isinstance(obj.get('text'), str) and (obj.get('text_sha256') == digest(obj['text'])) and obj.get('source_resource_id'):
                    self._event(obj['source_resource_id'], 'text', obj['source_sha256'], obj['text_sha256'], obj.get('source_locator', {}), 'complete_exact_original_paragraph_text; structured_locator_identity_parsed; no_whole_document_claim')
                    continue
                h = digest(canonical(obj))
                rid = prefix + h[:20] if prefix else obj['source_resource_id']
                scope = 'complete_structured_payload_text_geometry_identity_scan; no_asset_pixels; no_whole_source_applicability'
                if field == 'preserved_historical_neutral_source_supplements':
                    pointer = '/' + field + '/' + str(obj_index)
                    origin = next((o for o in self.origins.values() if o.get('source_bundle_pointer') == pointer), None)
                    if origin and origin.get('origin_inventory_view_sha256'):
                        h = origin['origin_inventory_view_sha256']
                        rid = origin['origin_inventory_resource_id']
                        scope = 'complete_semantic_text_geometry_source_identity_scan; raw_payload_binding_origin=verified_reader_origin_inventory; administrative_record_id_consumed_only_by_loader_for_finite_source_alignment_then_removed_before_classification; no_pixels_or_whole_source_applicability'
                sha = obj.get('source_sha256', obj.get('source_pdf_sha256', obj.get('snapshot_sha256')))
                self._event(rid, view, sha, h, obj.get('locator', {'document_resource_id': rid}), scope)
                for item in obj.get('source_visual_text_resources', []):
                    self._event(item['source_resource_id'], 'text', sha, item['text_sha256'], item.get('source_locator', {}), 'complete_literal_visual_text_resource; no_pixels')
                for item in obj.get('source_display_regions', []):
                    self._event(item['region_id'], 'geometry', item['source_sha256'], digest(canonical(item)), {'physical_page': item['physical_page'], 'coordinate_system': item['coordinate_system'], 'bbox_points_xyxy': item['bbox_points_xyxy']}, 'complete_supplied_display_region_geometry_structure; no_pixels; no_invented_operator')

    def _policy_role(self, c):
        role = c.get('structure', {}).get('source_role', c.get('structure', {}).get('role'))
        role = self.origins.get(c['context_id'], {}).get('role') or role
        return role not in {'example_cover_drug_name', 'example_cover_placeholder', 'example_subheading', 'illustration_scope_notice', 'lower_slide_example', 'printed_page_number', 'right_side_example', 'section_heading', 'source_attachment_identifier', 'toc_heading', 'toc_item'}

    def _used_views(self, cid, evidence, reason):
        origin = self.origins.get(cid)
        views = []
        raw_ids = {c['context_id'] for c in self.bundle.get('source_record', {}).get('contexts', self.all_contexts)}
        if cid in raw_ids:
            views.append({'resource_id': cid, 'view': 'text', 'use_scope': {'reason': reason, 'exact_anchor': evidence}})
        if origin:
            views.append({'resource_id': origin['origin_inventory_resource_id'], 'view': origin['origin_inventory_view'], 'use_scope': {'reason': reason, 'source_bundle_pointer': origin['source_bundle_pointer'], 'source_resource_id': origin['source_resource_id'], 'exact_anchor': evidence, 'field_scope': 'selected_exact_text; not_whole_document_applicability'}})
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
            meta.update({key: value for key, value in doc.items() if key not in ('source_texts', 'source_visual_text_resources', 'source_visual_frames', 'source_geometry', 'paragraphs')})
        meta.setdefault('source_title', meta.get('document_title', ''))
        meta.setdefault('source_document_kind', meta.get('document_kind', ''))
        meta.setdefault('policy_document_date', meta.get('explained_policy_document_date'))
        meta.setdefault('policy_document_number', meta.get('explained_policy_document_number'))
        return meta

    def _neutral_source(self, c):
        return c['kind'] in ('external_source', 'source_resource_text', 'historical_source_fragment') and self._policy_role(c)

    def _request(self, path, reference, missing, code, unknown_group=False):
        request = {'path': path, 'reference': reference, 'current_text': self.text, 'missing': missing, 'stop_reason': code, 'dependency_status': 'stopped'}
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
        established = r.get('reference_source_sha256', r.get('unit_primary_source_sha256')) == source_sha and r.get('target_source_sha256') == target and ('same_edition' in str(r.get('binding_scope', r.get('literal_relation_type', '')))) and bool(title and year and (title in actual) and (year in actual))
        return {'established': bool(established), 'binding': 'evidenced_same_edition_title_year_reference' if established else 'edition_ambiguous', 'source_sha256': target, 'source_title': title, 'source_year': year}

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
        for group, doc, pointer in groups:
            members = group.get('numbered_members', [])
            cs = [resource_contexts.get(rid) for rid in members]
            if any((c and norm(c.get('text', '')) == self.norm for c in cs)):
                full = self._group_evidence(group, doc, pointer, required=True)
                if full:
                    parent = resource_contexts[group['parent_resource_id']]
                    self._add('parent_predicate', [self._quote(parent, '当前编号成员的同源共享谓词')], '当前成员仅承接完整组的共享谓词，不承接其他成员', relation_subtype='complete_numbered_member_parent', source_group_pointer=pointer, group_operator=group['operator'], group_member_ids=members)
                    self._add('source_group_scope', full, '完整编号与原始限定/例外只作组范围证明，不自动传递兄弟条件', source_group_pointer=pointer, group_operator=group['operator'], dimension_inheritance=False)
        candidates = [(self.text, self.unit.get('source_ref', {}).get('sha256'), None)]
        for relation in list(self.relations):
            if relation['kind'] in ('substantive_list', 'cited_standard'):
                candidates.extend(((e['text'], e['source_ref']['sha256'], e['context_id']) for e in relation['context_evidence']))
        visited = set()
        while candidates:
            text, sha, cid = candidates.pop(0)
            references = list(self.bundle.get('source_reference_index', []))
            for group, doc, pointer in groups:
                parent = resource_contexts.get(group['parent_resource_id'])
                if not parent or doc.get('source_sha256', doc.get('snapshot_sha256')) != sha:
                    continue
                for heading in parent.get('structure', {}).get('heading_path', []):
                    name = re.sub('^规则[一二三四五六七八九十0-9]+[：:、.．\\s]*', '', str(heading))
                    if name != heading and name and (name in text):
                        references.append({'source_field': 'text', 'source_field_text_sha256': digest(text), 'literal_reference': name, 'resource_id': doc['source_resource_id'], 'reference_source_sha256': sha, 'target_source_sha256': sha, 'literal_relation_type': 'actual_selected_clause_same_snapshot_named_conditions'})
            for reference in references:
                literal = reference.get('literal_reference', '')
                if not literal or literal not in text or reference.get('source_field_text_sha256') != digest(text):
                    continue
                if reference.get('source_field') != 'text':
                    continue
                n = norm(text)
                if not re.search('(?:符合|满足)[^。；;]{0,24}' + re.escape(norm(literal)) + '[^。；;]{0,8}条件', n):
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
                    if literal not in parent.get('text', '') and (not any((literal in str(h) for h in headings))):
                        continue
                    if not headings or not any((re.search('^[一1][、.．]?条件$', norm(str(h))) for h in headings)):
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
                    self._add('cited_standard', full, '当前资格谓词确指同版完整条件组，保留原编号、共享限定与例外，未继承全文', relation_subtype='explicit_complete_numbered_condition_reference', reference_literal=literal, source_group_pointer=pointer, group_operator=group['operator'], version_binding=binding, reference_clause={'text': text, 'context_id': cid}, qualifier_exception_scope='exact_complete_selected_group')
                    candidates.extend(((e['text'], e['source_ref']['sha256'], e['context_id']) for e in full))

    def _group_evidence(self, group, doc, pointer, required):
        parent = self._resource_contexts.get(group.get('parent_resource_id'))
        ids = group.get('numbered_members', [])
        expanded = []
        for index, rid in enumerate(ids, 1):
            expanded.append(rid)
            expanded.extend(group.get(f'member{index}_submembers', []))
        sha = doc.get('source_sha256', doc.get('snapshot_sha256'))
        cs = [self._resource_contexts.get(rid) for rid in expanded]
        if not parent or not ids or len(expanded) != len(set(expanded)) or any((not c or not c.get('text') or c['source_ref']['sha256'] != sha for c in [parent] + cs)):
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
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            t = c.get('text', '')
            same_source = not current_sources or c.get('source_ref', {}).get('sha256') in current_sources
            if c['kind'] == 'parent_paragraph' and same_source and re.search(INTRO, norm(t)):
                self._add('parent_predicate', [self._quote(c, '直接父谓词补全本成员')], '当前成员与来源包直接父句的共同谓词组合；不继承兄弟内容', shared_predicate=t, member_text=self.text)

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
        by_parent = {}
        for c in self.contexts:
            if c['kind'] == 'ordered_members':
                p = c.get('structure', {}).get('parent_context_id')
                if p:
                    by_parent.setdefault(p, []).append(c)
        groups.extend((sorted(g, key=lambda c: c.get('structure', {}).get('sequence_index', 0)) for g in by_parent.values()))
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
            self._add('substantive_list', [self._quote(c, '当前实质总领确指的完整成员范围') for c in members], '当前有实质条件/内容要求，按来源有序容器读取全部成员', member_texts=[c['text'] for c in members], shared_predicate=self.text)
        if not found:
            self.material_requests.append({'path': 'substantive_list', 'reference': self.text, 'missing': '当前确指的完整成员范围未在结构图闭合提供'})

    def _local_operations(self):
        operations = re.findall('([\\u4e00-\\u9fff]{2})操作', self.norm)
        if not operations or not re.search('参考.{0,8}数据|操作.{0,12}数据|数据.{0,12}(?:改善|设计|开发)', self.norm):
            return
        for c in self.contexts:
            raw = c.get('text', '')
            if c['kind'] != 'paragraph' or self.text not in raw:
                continue
            prefix_end = raw.find(self.text)
            for a, b in sentence_spans(raw[:prefix_end]):
                part = norm(raw[a:b])
                shifts = re.findall('另一(?:种|个)?药|其他药|对照药|其他品种|另一品种|另一个项目', part)
                if shifts and (not all((shift in self.norm for shift in shifts))):
                    continue
                if any((op in part for op in operations)) and re.search('困难|障碍|不便|限制|灵活性.{0,40}操作.{0,10}影响|影响.{0,30}操作', part):
                    self._add('parent_predicate', [self._quote(c, '当前明确操作数据所指的同段操作限制', (a, b))], '当前操作数据—改动关系明确承接同段同一操作限制，不使用指南整体宗旨', shared_predicate=raw[a:b], member_text=self.text, relation_subtype='same_paragraph_operation_reference', operation_terms=operations)

    def _primary_standard_group(self, candidates, family):
        """Complete one expressly used standard from exact primary literal leaves.

        This is not a full-file applicability rule. A named programme, structural
        seed, current operative norm, same-snapshot current occurrence, contiguous
        literal leaf coordinates and one complete bounded group must all agree.
        """
        primary = self.unit.get('source_ref', {}).get('sha256')
        leaves = [c for c in self.contexts if c['kind'] == 'source_textleaf' and c.get('source_ref', {}).get('sha256') == primary]
        if not leaves:
            return None
        intervals = []
        for c in leaves:
            bounds = c['source_ref'].get('locator', {}).get('unicode_code_point_interval_half_open')
            if not isinstance(bounds, list) or len(bounds) != 2 or any((type(v) is not int for v in bounds)) or (bounds[1] - bounds[0] != len(c.get('text', ''))):
                return None
            intervals.append((bounds[0], bounds[1], c))
        intervals.sort(key=lambda z: z[0])
        if intervals[0][0] != 0 or any((a[1] != b[0] for a, b in zip(intervals, intervals[1:]))):
            return None
        raw = ''.join((c['text'] for _, _, c in intervals))
        titles = []
        title_re = PROGRAMME_HEADING_RE
        for m in re.finditer(title_re, raw):
            name = norm(m.group('name')).replace('审评工作', '').replace('工作', '')
            if len(name) >= 6 and name in self.norm and any((name in norm(c['text']) for c in candidates)):
                titles.append((m, name))
        if len(titles) != 1:
            return None
        title, name = titles[0]
        next_titles = [m.start() for m in re.finditer(title_re, raw) if m.start() > title.start()]
        end = min(next_titles) if next_titles else len(raw)
        block = raw[title.end():end]
        if self.norm not in norm(block) or not any((norm(c['text']) in norm(block) for c in candidates)):
            return None
        if family == 'termination':
            header_re = '(?m)^[ \\t]*[（(][一二三四五六七八九十]+[）)][ \\t]*(?:终止|取消)(?:程序|资格|条件|情形)(?=[ \\t]*(?:$|[。．.:：]))'
            boundary_re = '(?m)^[ \\t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])'
        else:
            header_re = '(?m)^[ \\t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])[ \\t]*(?:适用范围和适用条件|适用条件|纳入条件|适用标准|纳入标准|资格条件)(?=[ \\t]*(?:$|[。．.:：]))'
            boundary_re = '(?m)^[ \\t]*[一二三四五六七八九十]+、'
        heads = list(re.finditer(header_re, block))
        if family != 'termination':
            outer = [h for h in heads if re.match('^[ \\t]*[一二三四五六七八九十]+、', h.group())]
            if outer:
                heads = outer
        if len(heads) != 1:
            return None
        head = heads[0]
        stops = [m.start() for m in re.finditer(boundary_re, block) if m.start() > head.start()]
        ga = title.end() + head.start()
        gb = title.end() + (min(stops) if stops else len(block))
        group = norm(raw[ga:gb])
        intro = '(?:以下|下列).{0,12}(?:情形|条件).{0,24}(?:终止|取消)|(?:终止|取消).{0,24}(?:以下|下列).{0,12}(?:情形|条件)' if family == 'termination' else '(?:同时满足|符合|满足).{0,16}(?:以下|下列).{0,12}(?:条件|标准)|(?:以下|下列).{0,12}(?:条件|标准)'
        if not re.search(intro, group) or not re.search('(?m)^[ \\t]*1[.、．]', raw[ga:gb]):
            return None
        evidence = []
        selected = []
        for a, b, c in intervals:
            for lo, hi, role in [(title.start(), title.end(), 'named_programme_heading'), (ga, gb, 'complete_' + family + '_standard_group')]:
                x, y = (max(a, lo), min(b, hi))
                if x < y:
                    evidence.append(self._quote(c, '同源确指操作性标准的有限完整组及名称', (x - a, y - a)))
                    selected.append({'context_id': c['context_id'], 'role': role, 'leaf_span': [x - a, y - a], 'snapshot_span': [x, y]})
        completion = {'evidence': evidence, 'standard_text': raw[ga:gb], 'programme_name': name, 'standard_family': family, 'source_sha256': primary, 'selected_group_snapshot_span': [ga, gb], 'programme_block_snapshot_span': [title.end(), end], 'selected_leaf_spans': selected, 'not_whole_file_inheritance': True}
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
        line_end = raw.find('\n', gb)
        line_end = len(raw) if line_end < 0 else line_end
        boundary_text = raw[gb:line_end]
        normative_heading = re.fullmatch(r'[ \t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])[ \t]*[^\n]{2,}', boundary_text)
        next_programme = re.fullmatch(PROGRAMME_HEADING_RE, boundary_text)
        if gb >= len(raw) or not (normative_heading or next_programme):
            return None, '同版有限标准组后未见实际下一规范边界；EOF/有限叶截止不能证明闭合'
        numbered = list(re.finditer(r'(?m)^[ \t]*(\d+)[.、．][^\n]*', raw[ga:gb]))
        if not numbered or [int(m.group(1)) for m in numbered] != list(range(1, len(numbered)+1)):
            return None, '明确条件成员的原文编号未从首项连续闭合提供'
        content_end = gb
        if family == 'termination':
            last = numbered[-1]
            content_end = ga + last.end()
            # A physical continuation is included only until the enumerated
            # member's actual final punctuation. An independent next paragraph
            # is not an additional unnumbered termination condition.
            while not re.search(r'[。；;][ \t]*$', raw[ga+last.start():content_end]):
                next_end = raw.find('\n', content_end+1, gb)
                next_end = gb if next_end < 0 else next_end
                if next_end <= content_end:
                    return None, '末项终止条件的实际原文段落未闭合'
                content_end = next_end
            if not re.search(r'[。；;][ \t]*$', raw[ga+last.start():content_end]):
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

    def _bounded_primary_support_roles(self, completion, candidates):
        """Keep object/support/withdrawal roles beside, not inside, standards.

        Activation is a real current qualification review with a normative
        consequence. The already closed same-source programme is the boundary;
        no purpose, status, paperwork or unrelated mechanism is inherited.
        """
        if not re.search('(?:资格|条件).{0,12}(?:审核|核验)|(?:审核|核验).{0,12}(?:资格|条件)', self.norm) or not re.search('终止|取消|撤回|限制|维持', self.norm):
            return
        primary = completion['source_sha256']
        name = completion['programme_name']
        intervals = []
        for c in self.contexts:
            if c['kind'] == 'source_textleaf' and c['source_ref'].get('sha256') == primary:
                a, b = c['source_ref']['locator']['unicode_code_point_interval_half_open']
                intervals.append((a, b, c))
        intervals.sort(key=lambda item: item[0])
        raw = ''.join((c['text'] for _, _, c in intervals))
        lo, hi = completion['programme_block_snapshot_span']
        block = raw[lo:hi]
        view, offsets = matching_view(block)
        objects = []
        for c in candidates:
            seed = norm(c.get('text', ''))
            if not seed or name not in seed or (not re.search('药物|药品', seed)) or (not re.search('申请适用|可以申请|可申请', seed)):
                continue
            occurrences = [m for m in re.finditer(re.escape(seed), view)]
            if len(occurrences) == 1:
                a, b = raw_span(offsets, occurrences[0].start(), occurrences[0].end())
                objects.append((lo + a, lo + b))
        objects = list(dict.fromkeys(objects))
        if len(objects) != 1:
            return
        supports, withdrawals = ([], [])
        for a, b in sentence_spans(block):
            part = norm(block[a:b])
            if name not in part:
                continue
            if re.search('(?:对|对于|针对).{0,80}' + re.escape(name), part) and re.search('药物|药品|研发', part) and re.search('优先配置.{0,15}资源.{0,20}(?:沟通交流|技术服务|研究方案反馈|研发)', part) and re.search('研发|研制|临床试验', part) and (not re.search('为了|制定|印发|仅.*(?:形式|渠道)', part)):
                supports.append((lo + a, lo + b))
            if re.search('自(?:终止|取消|撤回)之日起', part) and re.search('不再优先(?:安排|提供).{0,20}(?:沟通交流|技术服务|研究方案反馈)', part):
                withdrawals.append((lo + a, lo + b))
        if len(supports) != 1 or len(withdrawals) != 1:
            return
        services = '沟通交流|技术服务|研究方案反馈'
        shared = set(re.findall(services, norm(raw[supports[0][0]:supports[0][1]]))) & set(re.findall(services, norm(raw[withdrawals[0][0]:withdrawals[0][1]])))
        if not shared:
            return
        evidence, roles = ([], [])

        def add_role(role, bounds, inherited=True):
            for start, end in bounds:
                for a, b, c in intervals:
                    x, y = (max(a, start), min(b, end))
                    if x < y:
                        quote = self._quote(c, '当前资格审核/撤回承接的同版有限' + role, (x - a, y - a))
                        evidence.append(quote)
                        roles.append({'role': role, 'source_snapshot_span': [x, y], 'source_leaf_span': [x - a, y - a], 'evidence': quote, 'inherited_as_support_definition': inherited})
        add_role('object_and_eligibility_definition', objects)
        add_role('priority_research_support', supports)
        add_role('withdrawal_direct_mechanism', withdrawals)
        qualification = completion if completion['standard_family'] == 'admission' else self._primary_standard_group(candidates, 'admission')
        if qualification:
            add_role('qualification_standard', [qualification['selected_group_snapshot_span']], False)
        content = '\n'.join((r['evidence']['text'] for r in roles if r['inherited_as_support_definition']))
        self._add('named_mechanism', evidence, '当前资格审核及规范性限制/撤回直接控制同一程序优先研发机会；对象、可用支持、撤回后果与完整标准分别保留，不复制宗旨或其他机制', content=content, relation_subtype='bounded_primary_qualification_support_roles', mechanism_name=name, object_definition=raw[objects[0][0]:objects[0][1]], direct_mechanism=raw[supports[0][0]:supports[0][1]], withdrawal_mechanism=raw[withdrawals[0][0]:withdrawals[0][1]], current_qualification_bridge=self.proposition(), source_roles=roles, qualification_standard_snapshot_span=qualification['selected_group_snapshot_span'] if qualification else None, termination_standard_snapshot_span=completion['selected_group_snapshot_span'] if completion['standard_family'] == 'termination' else None, version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme', 'source_sha256': primary}, direct_mapping=True, not_whole_programme_inheritance=True, standards_not_inherited_as_support_definition=True)

    def _standards(self):
        operative = re.search('(?:审核|核验|满足|符合|不符合).{0,20}(?:条件|资格|标准)|(?:条件|资格).{0,25}(?:审核|终止|取消)', self.norm)
        consequence = re.search('应当|可以|可申请|予以|终止|取消|限制|维持|授予', self.norm)
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
                            shared.append(p[-size:])
                            break
            if shared and re.search('用于|符合|条件|申请|适用', t):
                supplied_seed = c['context_id'] in related
                literal_seed = False
                if not supplied_seed and c.get('source_ref', {}).get('sha256') == self.unit.get('source_ref', {}).get('sha256') and re.search('(?:申请适用|申请纳入).{0,35}(?:程序|计划|通道|试点).{0,20}(?:药品|药物).{0,25}(?:以下|下列).{0,12}条件', t):
                    for name in shared:
                        closed = self._closed_primary_programme(name)
                        if closed:
                            lo, hi = closed['programme_span']
                            block = norm(closed['raw'][lo:hi])
                            if len(re.findall(re.escape(t), block)) == 1:
                                literal_seed = True
                if supplied_seed or literal_seed:
                    candidates.append(c)
        completion = None
        normative = re.search('应当|应予|应(?=核验|审核|终止|取消|撤回)|必须|可以|可申请|予以', self.norm)
        action = re.search('终止|取消|撤回|限制|维持|授予|申请适用|(?:核验|审核).{0,35}(?:资格|纳入条件|适用条件)|资格.{0,12}(?:核验|审核)', self.norm)
        family = None
        if re.search('(?:符合|满足).{0,16}(?:终止|取消).{0,35}(?:情形|条件)', self.norm):
            family = 'termination'
        elif re.search('(?:纳入|适用)(?:实质)?(?:条件|标准)|资格.{0,12}审核|审核.{0,12}资格', self.norm):
            family = 'admission'
        if candidates and normative and action and family:
            same_source = [c for c in candidates if c['source_ref'].get('sha256') == self.unit.get('source_ref', {}).get('sha256')]
            completion = self._primary_standard_group(same_source, family)
        if completion:
            details = {k: v for k, v in completion.items() if k != 'evidence'}
            self._add('cited_standard', completion['evidence'], '当前确指标准核验或标准—资格后果；同一原件具名程序内的完整适用/终止组，保留并列条件，不复制其他节或其他程序', action_scope='standard_review_or_eligibility_consequence', resolution_path='primary_literal_complete_operative_standard', **details)
            self.source_requests.append({'path': 'cited_standard', 'reference': self.text, 'current_text': self.text, 'dependency_status': 'resolved', 'resolution_path': 'primary_literal_complete_operative_standard', 'same_primary_source_sha256': completion['source_sha256'], 'programme_name': completion['programme_name'], 'standard_family': completion['standard_family'], 'selected_group_snapshot_span': completion['selected_group_snapshot_span'], 'selected_leaf_spans': completion['selected_leaf_spans'], 'seed_context_ids': [c['context_id'] for c in same_source], 'original_structural_seed_ids': [c['context_id'] for c in same_source if c['context_id'] in related], 'seed_interface': 'supplied structural relation or exact literal operative condition introduction in the same closed programme', 'evidence': completion['evidence'], 'no_new_material': True, 'other_unresolved_requests_retained': True})
            receipt = completion.get('neutral_scope_receipt')
            if receipt:
                proof = receipt['closure_proof']
                proof_only = proof['boundary_quotes'] + proof['identity_quotes'] + proof['proof_only_quotes']
                self._add('cited_standard', receipt['content_evidence'] + proof_only, '当前操作性标准核验/资格后果精确承接同一原件有限完整标准；真实下一规范边界与标题/独立尾段仅作闭合证明', relation_subtype='SE_primary_literal_operational_standard', affected_dimensions=['S','E','Ec'], SE_scope_verified=True, closure_proof=proof, standard_text=receipt['standard_text'], current_operative_anchor=receipt['current_operative_anchor'], current_source_snapshot_span=receipt['current_source_snapshot_span'], standard_family=family, version_binding={'established':True,'binding':'exact_same_primary_literal_snapshot','source_sha256':completion['source_sha256']}, action_scope='standard_review_or_eligibility_consequence', norm_start=0, norm_end=len(self.norm), not_whole_file_inheritance=True)
            else:
                request = {'path':'cited_standard','reference':self.text,'current_text':self.text,'missing':completion.get('neutral_scope_problem') or '已供标准尚未核明实际有限闭合与当前精确操作定位','dimensions':['S','E','Ec'],'request_kind':'provided_source_scope_unverified','other_resolved_and_stopped_references_retained':True}
                self.material_requests.append(request)
                self.source_requests.append({**request,'dependency_status':'stopped','resolution_path':'primary_literal_standard_scope_proof_unverified','no_new_material':True})
            self._bounded_primary_support_roles(completion, same_source)
        elif candidates:
            self._add('cited_standard', [self._quote(c, '同源操作性标准的原有短语境') for c in candidates], '当前以标准核验/资格决定制度适用或终止；原有确指语境范围保留', standard_text='\n'.join((c['text'] for c in candidates)), action_scope='standard_review_or_eligibility_consequence')
        elif re.search('(?:上述|该|纳入)(?:实质)?(?:条件|标准)', self.norm):
            self.material_requests.append({'path': 'cited_standard', 'reference': self.text, 'missing': '确指资格/标准与待遇后果的同版标准原文缺失'})

    def _operative_value_definition(self):
        """An operative clinical-value criterion consumes its complete definition.

        A programme name alone does not activate this path. The current clause
        must use a comparative value as an application/admission condition, its
        structural seed must be the same primary source, and the bounded full
        condition group must explicitly define that very expression.
        """
        criterion = re.search('明显临床优势|显著临床优势|明显治疗优势|显著治疗优势', self.norm)
        application = re.search('(?:可以|可|允许).{0,100}申请适用([^。；;，,]{4,28}(?:程序|计划|通道|试点))', self.norm)
        if not criterion or not application or (not re.search('药品|药物|新药', self.norm)):
            return
        clause_bound = any((m.start() <= criterion.start() and application.end() <= m.end() for m in re.finditer('[^。；;]+', self.norm)))
        between = self.norm[criterion.end():application.end()]
        if not clause_bound or re.search('其他(?:药品|药物|产品)|另(?:一|外)[^，,]{0,10}(?:药品|药物|产品)', between):
            return
        primary = self.unit.get('source_ref', {}).get('sha256')
        related = {cid for c in self.contexts if c['kind'] == 'structural_relation' for cid in c.get('structure', {}).get('related_context_ids', [])}
        candidates = [c for c in self.contexts if c['kind'] == 'source_paragraph' and c['context_id'] in related and (c['source_ref'].get('sha256') == primary) and (norm(c.get('text', '')) == self.norm)]
        if not candidates:
            self._request('cited_standard', criterion.group(), '当前操作性临床优势申请条件缺少同源确指种子及完整定义', 'required_reference_unresolved')
            return
        closed = self._closed_primary_programme(application.group(1))
        if not closed:
            self._request('cited_standard', criterion.group(), '当前临床优势条件缺少同源完整程序及唯一操作命题位置', 'required_reference_unresolved')
            return
        completion = self._primary_standard_group(candidates, 'admission')
        if not completion:
            self._request('cited_standard', criterion.group(), '当前操作性临床优势申请条件的同版完整条件组不能闭合', 'required_reference_unresolved')
            return
        definition = norm(completion['standard_text'])
        literal = re.escape(criterion.group())
        if not re.search(literal + '[^。；;]{0,8}(?:即|是指)', definition):
            return
        details = {k: v for k, v in completion.items() if k != 'evidence'}
        self._add('cited_standard', completion['evidence'], '当前以明确临床优势作为申请程序的操作性条件，承接同源同版完整定义及并列分支；疾病严重程度、宗旨和其他工作章节不被补入', relation_subtype='operative_value_complete_definition', resolution_path='primary_literal_complete_operative_value_definition', current_criterion_anchor=self.current_anchor(criterion.start(), criterion.end()), current_application_anchor=self.current_anchor(application.start(), application.end()), defined_value_expression=criterion.group(), action_scope='current_application_criterion_consumes_definition', **details)

    def _closed_primary_programme(self, name, require_current=True):
        """Return one same-source, contiguous literal programme and exact spans."""
        primary = self.unit.get('source_ref', {}).get('sha256')
        intervals = []
        for c in self.contexts:
            if c['kind'] != 'source_textleaf' or c['source_ref'].get('sha256') != primary:
                continue
            bounds = c['source_ref'].get('locator', {}).get('unicode_code_point_interval_half_open')
            if not isinstance(bounds, list) or len(bounds) != 2 or any((type(v) is not int for v in bounds)) or (bounds[1] - bounds[0] != len(c.get('text', ''))):
                raise SourceDependencyStop('malformed same-source primary literal leaf coordinates')
            intervals.append((bounds[0], bounds[1], c))
        intervals.sort(key=lambda item: item[0])
        if any((a[1] > b[0] for a, b in zip(intervals, intervals[1:]))):
            raise SourceDependencyStop('overlapping same-source primary literal leaf coordinates')
        if not intervals or intervals[0][0] != 0 or any((a[1] != b[0] for a, b in zip(intervals, intervals[1:]))):
            return None
        raw = ''.join((c['text'] for _, _, c in intervals))
        title_re = PROGRAMME_HEADING_RE
        titles = list(re.finditer(title_re, raw))

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
        if require_current and len(occurrences) != 1:
            return None
        a, b = raw_span(offsets, occurrences[0].start(), occurrences[0].end()) if len(occurrences) == 1 else (0, 0)
        return {'raw': raw, 'intervals': intervals, 'programme_name': name, 'programme_span': [lo, end], 'heading_span': [title.start(), title.end()], 'current_snapshot_span': [lo + a, lo + b], 'source_sha256': primary}

    def _bounded_IF_modification_bridge(self):
        """An explicit example/causal bridge can complete its own limitation.

        Only the immediately preceding sentence in the containing paragraph is
        used. General feedback-based optimisation is deliberately left separate.
        """
        if not re.search('比如|例如|因此|针对|为解决', self.norm):
            return
        if not re.search('剂型|制剂|片剂|胶囊|给药途径|给药频次|掰断|压碎|咀嚼', self.norm):
            return
        for c in self.contexts:
            raw = c.get('text', '')
            if c['kind'] != 'paragraph' or self.text not in raw:
                continue
            start = raw.index(self.text)
            parts = sentence_spans(raw[:start])
            if not parts:
                continue
            a, b = parts[-1]
            preceding = norm(raw[a:b])
            if re.search('吞咽困难|吞咽障碍|难以吞咽|现有.{0,20}(?:不适用|局限|不足)|实质改良|实质改进|改良给药途径|给药.{0,15}(?:不便|困难)|负担|频次', preceding):
                self._add('parent_predicate', [self._quote(c, '当前例示/因果改变直接承接的同段紧邻局限定义', (a, b))], '显式例示或因果词连接当前具体改变与紧邻局限；不借用其他句的独立设计', shared_predicate=raw[a:b], relation_subtype='bounded_IF_modification_bridge', affected_dimensions=['I'])

    def _bounded_IF_semantic_support(self):
        """Separate current operation, applicability and usable-service roles.

        Three source-neutral closures are accepted: a delivered closed scope
        component; a literal same-source named programme; a paragraph resource
        with an actual quoted-name qualification group and current service.
        Neither a title alone nor a nearby ordinary duty opens this relation.
        """
        text = self.norm
        if re.search('上市后[^。；;]{0,18}(?:常规|日常|例行)[^。；;]{0,25}(?:监测|会议|填表|资料)', text) and (not re.search('(?:进一步|继续|后续|服务于)[^。；;]{0,25}(?:创新|改良)?(?:研发|研制)', text)):
            return
        current_service = re.search('(?:药审中心|审评中心|审评团队|技术团队)[^。；;]{0,65}(?:提供|反馈|安排|不再提供)[^。；;]{0,45}(?:研究方案(?:反馈|意见|建议)?|试验方案(?:反馈|意见|建议)?|技术沟通|技术咨询|研究反馈)|(?:优先)?安排[^。；;]{0,20}技术沟通[^。；;]{0,30}(?:反馈|研究方案)', text)

        def object_classes(part):
            return set(re.findall('(?:^|[的和及、，,；;：:])([^的和及、，,；;：:\\s]{1,8}类)(?=项目|和|及|、)', part))
        current_classes = object_classes(text)

        def same_service_branch(part):
            classes = object_classes(part)
            if current_classes and classes and (not current_classes.intersection(classes)):
                return False
            if re.search('上市后', text) and re.search('上市前|申报前', part):
                return False
            return True
        ordinary_duty = re.search('申请人[^。；;]{0,12}(?:应当|应|需|需要)[^。；;]{0,25}(?:提交|收集|更新|报送)[^。；;]{0,30}(?:资料|材料|文件)', text)
        actual_application = re.search('(?:可|可以|允许)[^。；;]{0,45}(?:提出|申请|商定)|提出[^。；;]{0,20}沟通交流申请|(?:药审中心|审评团队)[^。；;]{0,35}(?:提供|反馈|商定)', text)
        if ordinary_duty and (not actual_application):
            return
        operation = re.search('(?:可|可以|允许|可申请|自愿申报|应当|应|决定|组织|设立|完成|保持|维持|退出|终止|撤回|不再|协助|商定|审评时限为)[^。；;]{0,70}(?:沟通交流|会议|咨询会|临床试验|研究方案|试验方案|研究资料|提交计划|审评|试点项目|优先|协调和督导|科学问题|\\d+\\s*日)', text)
        if not (operation or current_service) or re.search('鼓励[^。；;]{0,30}(?:密切沟通|沟通交流)', text):
            return
        actual = re.search('自愿申报[^。；;]{0,20}(?:试点|项目)|优先组织[^。；;]{0,12}专家咨询会|审评时限为\\s*\\d+\\s*日|(?:可|可以|允许)[^。；;]{0,65}(?:申请[^。；;]{0,20}(?:会议|沟通|试点|程序)|提出[^。；;]{0,20}沟通交流申请|商定[^。；;]{0,30}(?:资料|计划))|(?:研发|研究|临床试验|申报前|批准上市前)[^。；;]{0,60}(?:保持沟通|沟通交流|方案|资料)|(?:审评|沟通交流)[^。；;]{0,25}(?:时限|期限|工作日)|(?:\\d+|[一二三四五六七八九十百]+)(?:个)?(?:工作)?日[^。；;]{0,15}(?:完成审评|召开专家)|(?:维持|退出|终止|撤回|不再)[^。；;]{0,35}(?:资格|优先|程序)|协助审评团队[^。；;]{0,30}协调和督导', text)
        if not (actual or current_service):
            return
        if operation is None:
            operation = current_service
        current = self._current_source()
        primary = self.unit.get('source_ref', {}).get('sha256')
        if current is None or current.get('source_ref', {}).get('sha256') != primary:
            return
        sources = []
        for boundary in self.contexts:
            st = boundary.get('structure', {})
            ids = st.get('scope_context_ids', [])
            if boundary['kind'] != 'following_heading' or not ids or len(ids) != len(set(ids)):
                continue
            members = [self.by_id.get(cid) for cid in ids]
            if any((not c or c['kind'] != 'source_paragraph' or c.get('source_ref', {}).get('sha256') != primary or (not same_component(c, current)) or (not c.get('text')) for c in members)):
                continue
            containers = [c for c in self.contexts if c['kind'] == 'source_paragraph' and c.get('source_ref', {}).get('sha256') == primary and (c.get('structure', {}).get('first_paragraph') == st.get('component_first_paragraph')) and (c.get('structure', {}).get('last_paragraph') == st.get('component_last_paragraph'))]
            if len(containers) == 1 and st.get('follows_context_id') == ids[-1]:
                sources.append(('closed_applicability_component', [(c, None) for c in members]))
        names = set()
        for c in self.contexts:
            if c['kind'] != 'source_textleaf' or c.get('source_ref', {}).get('sha256') != primary:
                continue
            for m in re.finditer(PROGRAMME_HEADING_RE, c['text']):
                name = norm(m.group('name')).replace('审评工作', '').replace('工作', '')
                if name in text or any((name[-size:] in text for size in range(6, len(name) + 1))):
                    names.add(name)
        for name in names:
            closed = self._closed_primary_programme(name, require_current=True)
            if not closed:
                continue
            lo, hi = closed['programme_span']
            snippets = []
            for m in re.finditer('[^\\n]+(?:\\n|$)', closed['raw'][lo:hi]):
                x, y = (lo + m.start(), lo + m.end())
                for a, b, c in closed['intervals']:
                    if max(a, x) < min(b, y):
                        snippets.append((c, (max(a, x) - a, min(b, y) - a)))
            sources.append(('same_source_named_programme', snippets))
        for c in self.contexts:
            if c['kind'] != 'source_resource_text' or c.get('source_ref', {}).get('sha256') != primary:
                continue
            raw = c.get('text', '')
            view = norm(raw)
            if text not in view or not re.search('适用范围|(?:项目|药品|药物)范围为|申请资格|纳入[^。；;]{0,20}通道[^。；;]{0,35}应当为', raw):
                continue
            snippets = []
            for a, b in sentence_spans(raw):
                snippets.append((c, (a, b)))
            sources.append(('literal_structured_original_current_and_printed_scope', snippets))
        quoted = re.findall('[“「"]([^”」"]{2,45})[”」"](?:试点工作|项目|计划|程序)', current.get('text', ''))
        for name in quoted:
            ordered = [c for c in self.contexts if c['kind'] == 'source_resource_text' and c.get('source_ref', {}).get('sha256') == primary and self.origins.get(c['context_id'], {}).get('source_bundle_pointer', '').startswith('/source_full_text_resources/')]

            def pindex(c):
                pointer = self.origins[c['context_id']]['source_bundle_pointer']
                return tuple((int(v) for v in pointer.split('/') if v.isdigit()))
            ordered.sort(key=pindex)
            starts = [i for i, c in enumerate(ordered) if re.search('申请[^。；;]{0,5}' + re.escape(name) + '[^。；;]{0,25}(?:需|应)[^。；;]{0,15}同时满足[^。；;]{0,15}条件', norm(c.get('text', '')))]
            if len(starts) != 1:
                continue
            i = starts[0]
            group = [ordered[i]]
            for c in ordered[i + 1:]:
                part = norm(c.get('text', ''))
                if re.match('\\d+(?:\\.\\d+)?(?:\\s|申请流程)|[一二三四五六七八九十]+、|附件', part):
                    break
                group.append(c)
                if re.search('(?:后|再|将)[^。；;]{0,20}纳入|最终将纳入', part):
                    break
            if len(group) > 1 and any((re.search('境内[^。；;]{0,15}尚无药物获批|新作用机制|新靶点', norm(c.get('text', ''))) for c in group)):
                sources.append(('quoted_name_qualification_and_current_service', [(c, None) for c in group] + [(current, None)]))
        for closure, items in sources:
            branch_items = []
            for c, span in items:
                raw = c.get('text', '')
                a, b = span or (0, len(raw))
                for m in re.finditer('[^；;]+(?:[；;]|$)', raw[a:b]):
                    branch_items.append((c, (a + m.start(), a + m.end())))
            items = branch_items
            objects = []
            services = []
            stages = []
            need = []
            qualified_list = closure in {'closed_applicability_component', 'quoted_name_qualification_and_current_service'}
            for c, span in items:
                raw = c.get('text', '')
                a, b = span or (0, len(raw))
                part = norm(raw[a:b])
                technical_category = re.search('(?:化学药|生物制品|中药)', part) and re.search('(?:注册)?[1一]类', part) and re.search('仅适用|适用范围|适用', part) and (int(self._metadata(c).get('document_year', 0) or 0) >= 2020)
                object_scope = re.search('适用范围|(?:项目|品种|药品|药物)范围为|申请适用[^。；;]{0,35}(?:程序|规范|试点)|申请[^。；;]{0,40}品种[^。；;]{0,15}(?:需|应)[^。；;]{0,12}同时满足|(?:本|该)(?:程序|规范|计划|试点)[^。；;]{0,25}适用|纳入[^。；;]{0,20}通道[^。；;]{0,35}应当为', part)
                if closure == 'same_source_named_programme':
                    if re.search('^[一二三四五六七八九十]+、', part):
                        qualified_list = bool(re.search('适用范围|适用条件', part))
                    if re.search('以下[^。；;]{0,40}药品[^。；;]{0,20}可以申请适用', part):
                        qualified_list = True
                list_member = qualified_list and (re.match('(?:或|以及|及)?(?:[（(](?:[一二三四五六七八九十]+|[0-9]+)[）)]|[0-9]+(?=[\\u4e00-\\u9fff])|[①-⑳])', part) or re.search('[\\u4e00-\\u9fff]{1,8}类项目为', part) or re.search('(?:药品|药物|项目)[^。；;]{0,15}(?:可|可以)申请[^。；;]{0,15}(?:本|该)程序', part)) and (not re.search('不适用|不得|不再接受', part))
                if not same_service_branch(part):
                    continue
                if (re.search('创新药|改良型新药|首创新药|源头性创新.{0,12}药物', part) or technical_category) and (object_scope or list_member):
                    objects.append(self._quote(c, '同一有界安排明确的创新/改良对象和资格', (a, b)))
                if (object_scope or list_member) and re.search('境内[^。；;]{0,15}尚无药物获批|(?:尚无|没有)有效(?:防治|治疗)(?:手段|药物)|临床急需.{0,12}短缺药品', part):
                    need.append(self._quote(c, '同一安排实际资格中的治疗选项/供药缺口分支', (a, b)))
                if re.search('研发|研制|临床试验|上市前|申报前', part):
                    stages.append(self._quote(c, '当前服务对应的研发/上市前阶段', (a, b)))
                if re.search('优先(?:配置|安排|处理)|研究方案.{0,20}(?:意见|建议)|反馈给申请人|沟通交流.{0,20}(?:时限|期限)|审评.{0,20}(?:时限|期限)|单独序列|研发.{0,20}保持.{0,10}沟通交流', part):
                    services.append(self._quote(c, '同一有界安排已设的可用技术服务或办理便利', (a, b)))
            direct_current = re.search('优先组织[^。；;]{0,12}专家咨询会|自愿申报[^。；;]{0,20}(?:试点|项目)|审评时限为\\s*\\d+\\s*日|提出[^。；;]{0,20}沟通交流申请|可申请.{0,8}类会议|围绕.{0,30}临床试验方案.{0,15}沟通|(?:商定|达成一致).{0,35}(?:资料|计划)|研发过程中保持沟通|协助审评团队.{0,30}协调和督导|(?:\\d+|[一二三四五六七八九十]+)(?:个)?(?:工作)?日内完成审评', text)
            if current_service:
                direct_current = current_service
                services = []
                if re.search('研发|研制|临床试验|上市前|申报前|研究方案|试验方案', text):
                    stages = [self._quote(current, '当前实际技术服务的研发内容/阶段')]
            if direct_current:
                services.append(self._quote(current, '当前已经明确开放或提供的技术服务/办理便利'))
            if objects and services and stages:
                timed_review = bool(re.search('审评时限为\\s*\\d+\\s*日', text))
                if timed_review:
                    need = []
                self._add('named_mechanism', objects + need + services + stages, '当前实质行动与同版闭合对象、可用服务及阶段直接相连；资料可用性和项目名称本身不充分', relation_subtype='bounded_IF_actual_support', object_definition='\n'.join((e['text'] for e in objects + need)), direct_mechanism='\n'.join((e['text'] for e in services)), research_stage='\n'.join((e['text'] for e in stages)), current_action_anchor=self.current_anchor(operation.start(), operation.end()), selected_current_object_branches=sorted(current_classes), role_scope='current service and matching applicability branches; no other stage or object', source_closure=closure, version_binding={'established': True, 'binding': 'exact_same_primary_source', 'source_sha256': primary}, only_IF_consumers=True, affected_dimensions=['I'] if timed_review else ['I', 'F'], negation_and_withdrawal_retained=True)

    def _bounded_IF_right_operation(self):
        """Qualified scope of this right, never another article's drug/right."""
        if re.search('原研药品|仿制药', self.norm) and (not re.search('创新药|改良型新药', self.norm)):
            return
        current = self._current_source()
        current_text = norm(current.get('text', '')) if current else self.norm
        right_match = re.search('(?:药品试验)?数据保护|市场独占', self.norm)
        operation = re.search('申请|给予|享受|实施保护|保护是指|终止|限制|不予许可|不予受理|不受理|不批准', self.norm)
        anaphor = bool(re.search('依赖[^。；;]{0,20}(?:该|受|保护)[^。；;]{0,12}数据', self.norm) and re.search('(?:药品试验)?数据保护', current_text))
        if not right_match and (not anaphor) or not operation:
            return
        right = right_match.group() if right_match else re.search('(?:药品试验)?数据保护', current_text).group()
        right = re.search('数据保护|市场独占', right).group()
        primary = self.unit.get('source_ref', {}).get('sha256')

        def article(c):
            if not c:
                return None
            for container in (c.get('structure', {}), c.get('source_ref', {}).get('locator', {})):
                if container.get('article_id') is not None:
                    return container['article_id']
            literal = re.match('^第' + ORDINAL + '条', norm(c.get('text', '')))
            return literal.group() if literal else None
        current_article = article(current)
        general_bridge = bool(re.search(re.escape(right) + '是指|符合[^。；;]{0,30}给予[^。；;]{0,20}' + re.escape(right) + '条件', current_text))
        own_ordinary = bool(re.search('(?:本条|该|本)(?:普通)?药品[^。；;]{0,35}(?:一般资料保密|一般数据保密|普通药品)|本条普通药品', current_text))
        definitions = []
        blocked = []
        for c in self.contexts:
            if c.get('source_ref', {}).get('sha256') != primary or c['kind'] not in {'source_resource_text', 'source_paragraph'}:
                continue
            if current and (not same_component(c, current)):
                continue
            raw = c.get('text', '')
            for a, b in sentence_spans(raw):
                part = norm(raw[a:b])
                if not (right in part and re.search('创新药|改良型新药|改良型药品', part) and re.search('给予|享受|实施保护|数据保护期|保护范围', part)):
                    continue
                if re.search('另一(?:条|种|个)?|其他(?:药品|药物|创新药|保护)', part) and (not re.search('创新药|改良型新药', self.norm)):
                    blocked.append({'reason': 'definition expressly belongs to another drug/right', 'context_id': c['context_id']})
                    continue
                source_article = article(c)
                conflict = current_article is not None and source_article is not None and (current_article != source_article)
                if conflict and (not general_bridge):
                    blocked.append({'reason': 'different original article without a direct general qualification bridge', 'context_id': c['context_id'], 'current_article': current_article, 'definition_article': source_article})
                    continue
                if own_ordinary and (not re.search('创新药|改良型新药', self.norm)):
                    continue
                definitions.append(self._quote(c, '当前同一权利及同一资格对象的有限创新/改良—权利后果定义', (a, b)))
        if definitions:
            self._add('named_mechanism', definitions, '当前实际操作同一权利，同版有限定义直接给出对应创新/改良资格与后果；不同药品、条款或保护类型不混接', relation_subtype='bounded_IF_qualified_right_operation', object_definition='\n'.join((e['text'] for e in definitions)), current_right_name=right, source_sha256=primary, only_IF_consumers=True, affected_dimensions=['I'], right_scope_binding={'current_article': current_article, 'general_qualification_bridge': general_bridge, 'one_definition_proposition_required': True, 'blocked_alternative_definitions': blocked})
        elif blocked and (not own_ordinary) and re.search('本条药品|该药品|该药物|受保护数据', self.norm):
            request = {'path': 'named_mechanism', 'reference': self.text, 'current_text': self.text, 'missing': '当前药品同一权利的资格/数据指代未核明；已供创新定义定位属于不同条款或对象，不能借用', 'stop_reason': 'qualified_right_object_origin_unresolved', 'dependency_status': 'stopped', 'affected_dimensions': ['I'], 'blocked_alternative_definitions': blocked}
            self.material_requests.append(request)
            self.source_requests.append(request.copy())

    def _bounded_IF_individual_consultation(self):
        """An expressly unresolved technical issue gets actual authority access.

        Mere general encouragement/ordinary public-reference sentences cannot
        open this path. A direct supplied parent unit defines the same named
        research document and innovative trial object.
        """
        if not (re.search('(?:未能阐明|未涵盖|未解决)[^。；;]{0,20}(?:个性化|具体|技术)问题', self.norm) and re.search('(?:可|可以)[^。；;]{0,12}(?:与|向)(?:药审中心|审评中心)[^。；;]{0,15}(?:沟通|咨询)', self.norm)):
            return
        current = self._current_source()
        primary = self.unit.get('source_ref', {}).get('sha256')
        if current is None:
            return
        containers = [c for c in self.contexts if c['kind'] == 'parent_paragraph' and c.get('source_ref', {}).get('sha256') == primary and (self.norm in norm(c.get('text', '')))]
        for container in containers:
            st = container.get('structure', {})
            uid = st.get('unit_id')
            index = st.get('sequence_index')
            if not uid or type(index) is not int:
                continue
            for c in self.contexts:
                cs = c.get('structure', {})
                part = norm(c.get('text', ''))
                definition = re.search('(?P<name>[A-Za-z][A-Za-z0-9]{1,16})是[^。；;]{0,30}临床试验', part)
                reference_span = None
                referent = False
                if definition:
                    alias = definition.group('name')
                    referent = bool(re.search(re.escape(alias) + '[^。；;，,]{0,15}(?:未能阐明|未涵盖|未解决)', self.norm))
                    raw = container.get('text', '')
                    starts = [m.start() for m in re.finditer(re.escape(self.text), raw)]
                    if not referent and len(starts) == 1 and re.match('如有|对于未|对于该|对于本', self.norm):
                        preceding = sentence_spans(raw[:starts[0]])
                        if preceding:
                            lo, hi = preceding[-1]
                            previous = norm(raw[lo:hi])
                            referent = bool(re.search('(?:本|该)(?:指导原则|技术文档)[^。；;]{0,15}(?:撰写|编制|涉及)\\s*' + re.escape(alias) + '[^。；;]{0,35}(?:未|不能|尚不能)[^。；;]{0,12}(?:涵盖|阐明|解决)', previous))
                            if referent:
                                reference_span = (lo, starts[0] + len(self.text))
                if c['kind'] != 'parent_paragraph' or c.get('source_ref', {}).get('sha256') != primary or cs.get('unit_id') != uid or (cs.get('sequence_index') != index - 1) or (not definition) or (not referent) or (not same_component(c, current)) or (not re.search('创新药[^。；;]{0,20}临床试验', part)):
                    continue
                obj = self._quote(c, '同一直接父单元定义的创新药临床试验对象与技术文档')
                service = self._quote(container, '当前问题直接承接的同一技术文档及实际药审机构沟通入口', reference_span)
                self._add('named_mechanism', [obj, service], '当前为未阐明的具体问题开放审评机构沟通，同一直接父单元限定其创新临床研发对象；非公共指南通常可参考', relation_subtype='bounded_IF_actual_support', object_definition=obj['text'], direct_mechanism=service['text'], research_stage=obj['text'], only_IF_consumers=True, affected_dimensions=['I'], source_closure='direct_ordered_parent_named_research_document')

    def _IF_local_parent_geometry(self, parent, current):

        def field(c, key):
            return c.get('structure', {}).get(key, c.get('source_ref', {}).get('locator', {}).get(key))
        for key in ('component_id', 'chapter_id', 'section_id', 'list_id', 'parent_context_id'):
            left, right = (field(parent, key), field(current, key))
            if left is not None and right is not None and (left != right):
                return {'status': 'conflict', 'reason': 'different ' + key}
        bounds = []
        for c in (parent, current):
            interval = field(c, 'unicode_code_point_interval_half_open')
            bounds.append(interval if isinstance(interval, list) and len(interval) == 2 and all((type(v) is int for v in interval)) else None)
        if all(bounds):
            gap = bounds[1][0] - bounds[0][1]
            if not 0 <= gap <= 4:
                return {'status': 'conflict', 'reason': 'original character intervals not local preceding', 'origin_gap': gap, 'intervals': bounds}
            return {'status': 'verified_origin_coordinates', 'origin_gap': gap, 'intervals': bounds}
        left, right = (field(parent, 'sequence_index'), field(current, 'sequence_index'))
        if type(left) is int and type(right) is int:
            if right != left + 1:
                return {'status': 'conflict', 'reason': 'nonadjacent ordered source sequence'}
            return {'status': 'verified_supplied_order', 'sequence_indices': [left, right]}
        return {'status': 'role_only', 'reason': 'unique supplied local preceding role; original adjacency not independently proved'}

    def _bounded_IF_first_member(self):
        """Actual first member plus unique local operative parent, never siblings."""
        if not re.match('^\\s*[（(]一[）)]', self.norm):
            return
        current = self._current_source()
        primary = self.unit.get('source_ref', {}).get('sha256')
        if current is None or norm(current.get('text', '')) != self.norm:
            return
        previous = [c for c in self.contexts if c['kind'] == 'preceding_paragraph' and c.get('source_ref', {}).get('sha256') == primary]
        if len(previous) != 1:
            return
        c = previous[0]
        part = norm(c.get('text', ''))
        if not part.endswith(':') or not re.search('符合(?:以下|下列)[^。；;]{0,20}(?:情形|条件)[^。；;]{0,15}药品', part) or (not re.search('(?:可以|可|允许)[^。；;]{0,10}申请[^。；;]{0,20}(?:批准|准入|待遇|支持)', part)):
            return
        geometry = self._IF_local_parent_geometry(c, current)
        if geometry['status'] == 'conflict':
            request = {'path': 'parent_predicate', 'reference': self.text, 'current_text': self.text, 'missing': '接口preceding角色与原定位冲突；第一项实际操作性父谓词须核明', 'stop_reason': 'local_parent_origin_conflict', 'dependency_status': 'stopped', 'origin_conflict': geometry, 'affected_dimensions': ['F'] if re.search('尚无|没有|短缺', self.norm) and (not re.search('创新|改良|新作用机制', self.norm)) else ['I', 'F']}
            self.material_requests.append(request)
            self.source_requests.append(request.copy())
            return
        self._add('parent_predicate', [self._quote(c, '第一项直接承接的同源完整操作性父谓词')], '实际第一项与唯一局部preceding且冒号闭合的完整申请父句组合；原定位冲突阻断，不展开兄弟或其他章节', shared_predicate=c['text'], relation_subtype='bounded_IF_first_operative_member', parent_binding_evidence_grade=geometry['status'], parent_geometry=geometry, only_IF_consumers=True, affected_dimensions=['I', 'F'])

    def _bounded_IF_missing_dependency(self):
        if re.search('(?:不能满足|不符合|不满足)[^。；;]{0,35}(?:审评审批|审评|程序|计划|通道|试点)[^。；;]{0,12}(?:条件|资格)|(?:纳入|适用)(?:条件|资格)[^。；;]{0,20}不满足', self.norm) and re.search('(?:终止|取消|撤回|限制)[^。；;]{0,35}(?:审评|程序|研究方案|试验方案|反馈|支持|服务)', self.norm) and (not any((r['kind'] == 'cited_standard' and r['details'].get('resolution_path') == 'primary_literal_complete_operative_standard' for r in self.relations))) and (not any((r['details'].get('relation_subtype') == 'bounded_IF_actual_support' for r in self.relations))):
            self._request('named_mechanism', self.text, '当前资格不符导致实际程序撤回所承接的同版对象条件与支持后果未由共同接口提供', 'required_named_qualification_scope_unresolved')
        if re.search('\\d+日通道', self.norm) and re.search('临床试验|审评审批', self.norm) and re.search('时限[^。；;]{0,20}\\d+日|\\d+个工作日内完成', self.norm) and (not re.search('创新药|改良型新药', self.norm)) and (not any((r['details'].get('relation_subtype') == 'bounded_IF_actual_support' for r in self.relations))):
            request = {'path': 'named_mechanism', 'reference': self.text, 'current_text': self.text, 'missing': '当前实际时限例外所指同版通道的药品对象与准入范围未由共同接口提供', 'stop_reason': 'required_named_support_object_unresolved', 'dependency_status': 'stopped', 'affected_dimensions': ['I']}
            self.material_requests.append(request)
            self.source_requests.append(request.copy())

    def _bounded_IF_table_qualification(self):
        """Current whole row, explicit innovation content and matched right column.

        Bare cell/category numbers and other rows cannot use this closure. The
        printed row-cell/column mapping remains part of the evidence trace.
        """
        if '|' not in self.norm:
            return
        current_cells = [norm(x).strip() for x in self.text.split('|')]
        primary = self.unit.get('source_ref', {}).get('sha256')
        for row in self.contexts:
            if row['kind'] != 'table_row' or row.get('source_ref', {}).get('sha256') != primary:
                continue
            cells = row.get('row_cells', [])
            headers = row.get('headers', [])
            st = row.get('structure', {})
            if [norm(x).strip() for x in cells] != current_cells or len(headers) != len(cells):
                continue
            pairs = st.get('row_cell_column_pairs', [])
            if len(pairs) != len(cells) or any((p.get('cell_index') != i or p.get('header_index') != i or p.get('column_index') != i for i, p in enumerate(pairs))):
                continue
            subject = [i for i, x in enumerate(cells) if re.search('创新(?:型)?(?:药|疫苗|生物制品)|改良型新药', norm(x))]
            rights = [i for i, x in enumerate(headers) if re.search('保护(?:期|期限)|待遇|权利|准入', norm(x)) and re.search('\\d+(?:\\.\\d+)?年|给予|享受|允许', norm(cells[i]))]
            if len(subject) != 1 or len(rights) != 1:
                continue
            selected = []
            for c in self.contexts:
                s = c.get('structure', {})
                if c.get('source_ref', {}).get('sha256') == primary and s.get('parent_context_id') == row['context_id'] and (c['kind'] == 'table_row_cell' and s.get('column_index') in subject + rights or (c['kind'] == 'table_header_cell' and s.get('column_index') in rights)):
                    selected.append(self._quote(c, '当前同表同一行创新资格与实质权利列的原文及坐标'))
            if len(selected) == 3:
                self._add('parent_predicate', selected, '当前完整表行按实际列坐标连接明文创新/改良资格与保护/待遇；不能借其他行或纯类别号', relation_subtype='bounded_IF_table_qualification_consequence', shared_predicate='\n'.join((e['text'] for e in selected)), current_table_subject=cells[subject[0]], current_table_right=cells[rights[0]], table_header=headers[rights[0]], table_row_structure=st, only_IF_consumers=True)

    def _primary_role_quotes(self, closed, bounds, role):
        evidence, roles = ([], [])
        for start, end in bounds:
            for a, b, c in closed['intervals']:
                x, y = (max(a, start), min(b, end))
                if x < y:
                    quote = self._quote(c, '当前有界安排直接使用的同版' + role, (x - a, y - a))
                    evidence.append(quote)
                    roles.append({'role': role, 'source_snapshot_span': [x, y], 'source_leaf_span': [x - a, y - a], 'evidence': quote})
        return (evidence, roles)

    def _postadmission_technical_support(self):
        """Resolve actual technical communication after programme admission.

        The current service, same programme's eligibility scope, technical-review
        priority communication and concrete technical-material feedback are
        separate roles. Preapplication communication and general purpose never
        supply the missing service or priority opportunity.
        """
        target = re.search('(?:对|针对)纳入([^。；;，,]{4,28}(?:程序|计划|通道|试点))的(?:品种|药品|药物|项目)', self.norm)
        service = re.search('(?:进行|开展|提供|安排)[^。；;]{0,20}(?:沟通交流|技术咨询|研究反馈)', self.norm)
        form_only = re.search('(?:电话|视频|面对面|书面)[^。；;]{0,15}(?:形式|渠道|方式)|沟通交流(?:形式|渠道|方式)', self.norm) and (not re.search('(?:提供|开展|进行)[^。；;]{0,20}(?:研究反馈|技术咨询|技术资料|技术服务|研究方案反馈)', self.norm))
        if not target or not service or form_only or re.search('申请前|申报前|仅[^。；;]{0,12}(?:电话|视频|形式|渠道)', self.norm):
            return
        clause_bound = any((m.start() <= target.start() and service.end() <= m.end() for m in re.finditer('[^。；;]+', self.norm)))
        if not clause_bound or re.search('其他(?:药品|药物|产品)|另(?:一|外)[^，,]{0,10}(?:药品|药物|产品)', self.norm[target.end():service.end()]):
            return
        name = target.group(1)
        closed = self._closed_primary_programme(name)
        if not closed:
            self._request('named_mechanism', name, '当前纳入后技术沟通缺少同版完整程序、唯一当前位置和对象/技术审评组件边界', 'required_reference_unresolved')
            return
        raw = closed['raw']
        lo, hi = closed['programme_span']
        block = raw[lo:hi]
        scope = re.search('(?m)^[ \\t]*[一二三四五六七八九十]+、(?:适用范围|适用范围和适用条件)[ \\t]*$', block)
        work = re.search('(?m)^[ \\t]*[一二三四五六七八九十]+、工作程序[ \\t]*$', block)
        review = re.search('(?m)^[ \\t]*[（(][一二三四五六七八九十]+[）)]技术审评[。．.:：]', block)
        if not scope or not work or (not scope.start() < work.start()):
            return
        priority, review_component = ([], [])
        if review and work.start() < review.start():
            next_head = re.search('(?m)^[ \\t]*(?:[（(][一二三四五六七八九十]+[）)]|[一二三四五六七八九十]+、)', block[review.end():])
            review_end = review.end() + next_head.start() if next_head else len(block)
            review_text = block[review.start():review_end]
            if re.search('纳入' + re.escape(name), norm(review_text)):
                for a, b in sentence_spans(review_text):
                    part = norm(review_text[a:b])
                    if name in part and re.search('纳入', part):
                        review_component.append((lo + review.start() + a, lo + review.start() + b))
                    if re.search('在审评中|审评过程中', part) and re.search('沟通交流|技术咨询|研究反馈', part) and re.search('优先(?:安排|处理|提供)', part):
                        priority.append((lo + review.start() + a, lo + review.start() + b))
        technical = []
        for a, b in sentence_spans(block[work.end():]):
            part = norm(block[work.end() + a:work.end() + b])
            if name in part and re.search('在审评过程中|在审评中', part) and re.search('沟通交流申请|技术咨询申请', part) and re.search('补充提交技术资料|研究方案反馈|试验方案反馈|研发技术咨询', part) and (not re.search('申请前|申报前|仅[^。；;]{0,10}(?:形式|渠道)', part)):
                technical.append((lo + work.end() + a, lo + work.end() + b))
        if not priority and (not technical):
            return
        object_bounds = [(lo + scope.start(), lo + work.start())]
        evidence, roles = ([], [])
        for role, bounds in [('programme_heading', [closed['heading_span']]), ('object_and_need_eligibility', object_bounds), ('postadmission_technical_review_component_scope', review_component if priority else []), ('postadmission_priority_technical_communication', priority), ('postadmission_technical_material_feedback', technical)]:
            es, rs = self._primary_role_quotes(closed, bounds, role)
            evidence.extend(es)
            roles.extend(rs)
        objects = '\n'.join((r['evidence']['text'] for r in roles if r['role'] == 'object_and_need_eligibility'))
        supports = '\n'.join((r['evidence']['text'] for r in roles if r['role'].startswith('postadmission_')))
        scope_end = re.search('(?m)^[ \\t]*[一二三四五六七八九十]+、', block[scope.end():work.start()])
        scope_stop = scope.end() + scope_end.start() if scope_end else work.start()
        applicable_scope = block[scope.start():scope_stop]
        innovation_branches = []
        if re.search('(?:可以|可|允许).{0,40}申请适用' + re.escape(name), norm(applicable_scope)) or re.search('适用于|面向', norm(applicable_scope)):
            for a, b in sentence_spans(applicable_scope):
                part = norm(applicable_scope[a:b])
                object_part = part.replace(name, '')
                if re.search('创新药|创新型药物|改良型新药|首创新药', object_part) and (not re.search('不适用|不包括|不包含|排除|除外|不得申请', part)):
                    quotes, _ = self._primary_role_quotes(closed, [(lo + scope.start() + a, lo + scope.start() + b)], 'positive_innovation_eligible_branch')
                    innovation_branches.extend(quotes)
        self._add('named_mechanism', evidence, '当前对已纳入同一程序的品种实际进行沟通，同版明确实际技术审评优先沟通或技术资料反馈机会；对象、技术支持和按需优先机会分别留痕，I3与F独立判断，不借申报前机制或总宗旨', relation_subtype='bounded_primary_postadmission_technical_support', content=objects + '\n' + supports, object_definition=objects, direct_mechanism=supports, current_service_bridge=self.proposition(), source_roles=roles, current_service_anchor=self.current_anchor(service.start(), service.end()), innovation_eligible_branches=innovation_branches, postadmission_priority_communication_present=bool(priority), postadmission_technical_material_feedback_present=bool(technical), programme_name=name, current_snapshot_span=closed['current_snapshot_span'], programme_block_snapshot_span=closed['programme_span'], version_binding={'established': True, 'binding': 'same_primary_snapshot_closed_programme', 'source_sha256': closed['source_sha256']}, direct_mapping=True, research_stage='纳入后、药品上市许可技术审评过程中', preapplication_mechanism_inherited=False, general_purpose_inherited=False, not_whole_programme_inheritance=True)

    def _price_arrangement_definition(self):
        """Map a current operative price node to its same-edition price content."""
        price = re.search('价格(?:谈判|协商|磋商)', self.norm)
        if not price or not re.search(OBJECT, self.norm):
            return
        branch = re.search('价格(?:谈判|协商|磋商)→(?:协商|谈判|磋商)成功[:：][^。；;]{0,70}(?:纳入|新增适应症|新增功能主治)', self.norm)
        substantive = re.search('(?:根据|依据)[^。；;]{0,35}(?:评估|测算|确定)[^。；;]{0,20}(?:协商价格|药品价格)[^。；;]{0,25}(?:开展|进行)[^。；;]{0,15}价格(?:谈判|协商|磋商)', self.norm)
        if not branch or substantive:
            return
        primary = self.unit.get('source_ref', {}).get('sha256')
        evidence, chains = ([], [])
        current_directories = re.findall('《([^》]{2,20}目录)》', self.norm)
        for c in self.contexts:
            if c['kind'] not in {'source_textleaf', 'source_resource_text', 'historical_source_fragment', 'source_paragraph'} or c['source_ref'].get('sha256') != primary:
                continue
            view, offsets = matching_view(c.get('text', ''))
            sentences = list(re.finditer('[^。]+(?:。|$)', view))
            for index, sentence in enumerate(sentences):
                part = sentence.group()
                if re.search('(?:根据|依据)[^。；;]{0,30}(?:评估|测算|确定)[^。；;]{0,20}(?:协商价格|药品价格)', part) and re.search('(?:开展|进行)[^。；;]{0,15}(?:现场)?价格(?:谈判|协商|磋商)', part):
                    previous = sentences[index - 1] if index else None
                    object_part = part if re.search('药品|药物|该药|本药', part) else previous.group() if previous else ''
                    if not re.search('药品|药物|该药|本药', object_part) or not re.search('价格(?:协商|谈判|磋商)', object_part) or (current_directories and (not any((d in part + object_part for d in current_directories)))):
                        continue
                    selected = []
                    if previous is not None and object_part != part:
                        a, b = raw_span(offsets, previous.start(), previous.end())
                        selected.append(self._quote(c, '同版价格磋商定义的紧邻药品/目录对象及节点指代', (a, b)))
                    a, b = raw_span(offsets, sentence.start(), sentence.end())
                    selected.append(self._quote(c, '当前价格协商节点的同版评估价格与实际磋商定义', (a, b)))
                    evidence.extend(selected)
                    chains.append({'source_context_id': c['context_id'], 'object_and_node': object_part, 'price_content': part, 'exact_quotes': selected, 'same_snapshot': True, 'nearest_preceding_object_only': object_part != part})
        if not evidence:
            self._request('price_arrangement', price.group(), '当前实际价格协商分支缺少同版评估/确定价格及磋商内容定义', 'required_reference_unresolved')
            return
        self._add('price_arrangement', evidence, '当前实际价格协商分支与同版评估确定协商价格的现场磋商定义直接相接；只补价格配置内容，不从商保推荐目录推出实际医保或商业承保支付', relation_subtype='same_edition_price_node_content_definition', current_price_anchor=self.current_anchor(price.start(), price.end()), current_branch_anchor=self.current_anchor(branch.start(), branch.end()), version_binding={'established': True, 'binding': 'exact_same_snapshot', 'source_sha256': primary}, price_definition='\n'.join((e['text'] for e in evidence)), price_object_content_chains=chains, directory_recommendation_is_payment_coverage=False, direct_mapping=True, not_whole_document_inheritance=True)

    def _version(self, c, action_text=None):
        meta = self._metadata(c)
        date = meta.get('document_date') or meta.get('source_date') or meta.get('policy_document_date')
        current_years = re.findall('(?:19|20)\\d{2}年', self.norm if action_text is None else action_text)
        source_year = date[:4] if date else None
        if current_years and (not source_year or any((y[:4] != source_year for y in current_years))):
            return {'established': False, 'current_years': current_years, 'source_date': date}
        sha = c.get('source_ref', {}).get('sha256')
        primary = self.unit.get('source_ref', {}).get('sha256')
        same_snapshot = bool(sha and primary == sha)
        title = meta.get('document_title') or meta.get('source_title', '')
        identity = bool(date and title and (meta.get('document_number') or meta.get('policy_document_number') or meta.get('source_url') or meta.get('original_url')))
        return {'established': bool(same_snapshot or identity), 'current_years': current_years, 'source_date': date, 'source_title': title, 'source_sha256': sha, 'binding': 'exact_same_snapshot' if same_snapshot else 'explicit_historical_year_source_identity' if current_years else 'preserved_same_policy_source_identity'}

    def _current_source(self):
        paragraphs = [c for c in self.contexts if c['kind'] == 'paragraph' and self.norm and (self.norm in norm(c.get('text', '')))]
        sources = {c.get('source_ref', {}).get('sha256') for c in paragraphs}
        return paragraphs[0] if len(sources) == 1 and paragraphs else None

    def _reference_members(self, container, current):
        source_sha = current.get('source_ref', {}).get('sha256')
        if container.get('source_ref', {}).get('sha256') != source_sha or not same_component(container, current):
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
            if child.get('source_ref', {}).get('sha256') != source_sha or not same_component(child, current) or child.get('structure', {}).get('parent_context_id') != container['context_id']:
                return []
            if child['kind'] not in ('ordered_members', 'cited_article', 'cited_section', 'source_paragraph'):
                return []
            if not self._supplied_address(child)['valid']:
                return []
            raw = child.get('text', '')
            for match in re.finditer('[^\\n]+(?:\\n|$)', raw):
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
            metadata_article=self._supplied_article_number(member[0])
            if metadata_article is not None and metadata_article!=article:
                return []
            bounded.append(member)
        return bounded

    def _reference_candidates(self, current, article):
        candidates = []
        source_sha = current.get('source_ref', {}).get('sha256')
        for root in self.contexts:
            if root['kind'] != 'cited_reference_group' or root.get('source_ref', {}).get('sha256') != source_sha or (not same_component(root, current)):
                continue
            ids = []
            for group in root.get('structure', {}).get('child_groups', []):
                if group.get('position') == 'references':
                    ids.extend(group.get('ordered_context_ids', []))
            for cid in ids:
                container = self.by_id.get(cid)
                if not container or container['kind'] != 'cited_reference' or container.get('structure', {}).get('parent_context_id') != root['context_id']:
                    continue
                members = self._reference_members(container, current)
                if not members:
                    continue
                heading = re.match(ARTICLE_REFERENCE, members[0][2])
                if ordinal_number(heading.group(1)) == article:
                    candidates.append((container, members))
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != source_sha:
                continue
            for group in doc.get('ordered_article_groups', []):
                group_article = self._supplied_group_article_number(group)
                if group_article != article:
                    continue
                ids = group.get('ordered_source_resource_ids', [])
                if not ids or len(ids) != len(set(ids)):
                    continue
                members = []
                for position, rid in enumerate(ids, 1):
                    matches = [c for c in self.contexts if self.origins.get(c['context_id'], {}).get('source_resource_id') == rid and c['source_ref']['sha256'] == source_sha]
                    if len(matches) != 1:
                        members = []
                        break
                    c = matches[0]
                    st = c.get('structure', {})
                    if self._supplied_article_number(c) != group_article or self._supplied_clause_number(c) != position or (not c.get('text')):
                        members = []
                        break
                    members.append((c, (0, len(c['text'])), norm(c['text'])))
                if members:
                    candidates.append((members[0][0], members))
        return candidates

    def _table_protection_branches(self):
        """Bind a table's basic duration to the same arrangement's definition.

        Exact table columns remain separate from a conditional remark. Only
        original ordered articles of the exact snapshot are eligible; reading
        an article group does not propagate its independent other branches.
        """
        current = self._current_source()
        if current is None or '|' not in self.norm or (not re.search('数据保护期|保护期限', self.norm)):
            return
        cells = list(re.finditer('[^|\\s](?:[^|]*[^|\\s])?', self.norm))
        durations = [(i, c) for i, c in enumerate(cells) if re.fullmatch('\\d+(?:\\.\\d+)?年', c.group())]
        if len(durations) != 1:
            return
        index, duration = durations[0]
        if index < 1:
            return
        subject = cells[index - 1]
        object_types = set(re.findall('原研|创新|改良', subject.group()))
        if not object_types or not re.search('药品|药物', subject.group()):
            return
        candidates = []
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != current['source_ref']['sha256']:
                continue
            for group in doc.get('ordered_article_groups', []):
                article = self._supplied_group_article_number(group)
                if article is None:
                    continue
                donors = self._reference_candidates(current, article)
                if len(donors) != 1:
                    continue
                container, members = donors[0]
                for pos, item in enumerate(members):
                    if not (object_types <= set(re.findall('原研|创新|改良', item[2])) and re.search('给予' + re.escape(duration.group()) + '数据保护期', item[2])):
                        continue
                    if '境外' in item[2] and '境外' not in subject.group() or ('境内' in item[2] and '境内' not in subject.group()):
                        continue
                    scopes = [m for m in members[pos + 1:] if re.search('本条款中药品|本条中药品|前款药品', m[2]) and re.search('数据保护范围.{0,8}(?:包括|限于|涵盖)', m[2])]
                    if len(scopes) == 1:
                        candidates.append((article, container, item, scopes[0]))
        if len(candidates) != 1:
            self._request('cited_standard', subject.group() + '|' + duration.group(), '整表行基础保护待遇缺少同源唯一对象、期限及条内数据范围定义', 'required_reference_unresolved')
            return
        bridges = []
        for doc in self.bundle.get('explicit_or_primary_source_resources', []):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != current['source_ref']['sha256']:
                continue
            for group in doc.get('ordered_article_groups', []):
                group_article = self._supplied_group_article_number(group)
                if group_article is None:
                    continue
                donors = self._reference_candidates(current, group_article)
                if len(donors) == 1:
                    for item in donors[0][1]:
                        if re.search('详见附表|见附表|见附录', item[2]) and re.search('数据保护', item[2]):
                            bridges.append((group_article, donors[0][0], item))
        if len(bridges) != 1:
            self._request('cited_standard', duration.group(), '当前附表与保护安排正文的同源确切连接缺失或不唯一', 'required_reference_unresolved')
            return
        article, container, treatment, scope = candidates[0]
        bridge_article, bridge_container, bridge = bridges[0]
        evidence = [self._quote(bridge[0], '同源定义明确连接附表保护安排', bridge[1]), self._quote(treatment[0], '当前表行基础对象及期限的同条款定义', treatment[1]), self._quote(scope[0], '基础保护待遇的条内试验数据范围定义', scope[1])]
        self._table_current_object = self.current_anchor(subject.start(), subject.end())
        self._add('cited_standard', evidence, '完整表行的基础期限与条件例外分别读取；仅补基础同一对象、同一期限及条内数据范围，未将例外先行条件移入基础', relation_subtype='complete_table_basic_protection_definition', protection_branch='base_table_arrangement', current_object_anchor=self.current_anchor(subject.start(), subject.end()), current_consequence_anchor=self.current_anchor(duration.start(), duration.end()), basic_duration=duration.group(), exception_not_inherited=True, source_article_group_pointers=self._article_group_pointers(current['source_ref']['sha256'], [bridge_article, article]), reference_chain=[{'article': bridge_article, 'context_id': bridge_container['context_id'], 'relation': 'explicit_appendix_connection'}, {'article': article, 'context_id': container['context_id'], 'relation': 'same_object_duration_and_article_scope', 'treatment_context_id': treatment[0]['context_id'], 'scope_context_id': scope[0]['context_id']}], version_binding={'established': True, 'binding': 'exact_same_snapshot', 'source_sha256': current['source_ref']['sha256']})

    def _article_group_pointers(self, source_sha, articles):
        pointers = []
        for di, doc in enumerate(self.bundle.get('explicit_or_primary_source_resources', [])):
            if doc.get('source_sha256', doc.get('snapshot_sha256')) != source_sha:
                continue
            for gi, group in enumerate(doc.get('ordered_article_groups', [])):
                group_article = self._supplied_group_article_number(group)
                if group_article in articles:
                    pointers.append(f'/explicit_or_primary_source_resources/{di}/ordered_article_groups/{gi}')
        return pointers

    def _operative_references(self):
        current = self._current_source()
        if current is None:
            return
        for reference in re.finditer(ARTICLE_REFERENCE, self.norm):
            before = self.norm[max(0, reference.start() - 16):reference.start()]
            operative = re.search('(?:不符合|符合|未满足|满足|核验|审核)[^。；;|]{0,12}$', before)
            branch_tail = re.split('[。；;|]', self.norm[reference.end():], maxsplit=1)[0]
            consequence = re.search(f'(?:数据保护期|保护期)(?:暂定|确定|应当|应|可以|可|仅|将|则)?为(?:\\d+(?:\\.\\d+)?|{ORDINAL})(?:个)?(?:年|月|日|天)|(?:数据保护期|保护期)[^。；;|]{{0,8}}(?:给予|享受|不予|限制|缩短|延长)|(?:予以|给予|授予|取消|终止|不得|不予)[^。；;]{{0,20}}(?:许可|准入|待遇|权利|保护|支持)|(?:可以|可|准许)[^。；;]{{0,12}}(?:申请|获得)[^。；;]{{0,18}}(?:许可|保护|待遇|支持)', branch_tail)
            if not operative or not consequence:
                continue
            if re.search('(?:另一|其他|另外|另一个).{0,8}(?:药品|药物|品种|项目)', branch_tail[:consequence.end()]):
                continue
            article = ordinal_number(reference.group(1))
            clause = ordinal_number(reference.group(2)) if reference.group(2) else None
            candidates = self._reference_candidates(current, article)
            if len(candidates) != 1:
                self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(), 'missing': '当前条件—实质待遇确指的同源条款缺失或不能唯一绑定'})
                continue
            container, members = candidates[0]
            if clause is not None and (not 1 <= clause <= len(members)):
                self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(), 'missing': '当前确指款次未在同源有界条文中完整提供'})
                continue
            selected = members if clause is None else [members[clause - 1]]
            evidence, antecedents = ([], [])
            current_object_binding = None
            if clause and re.search('该药品|本药品|该药物|本药物', selected[0][2]):
                if '|' in self.norm and getattr(self, '_table_current_object', None):
                    current_object_binding = self._table_current_object
                else:
                    current_object_binding = None
                preceding = members[clause - 2] if clause > 1 else None
                if current_object_binding is None and (preceding is None or not re.search(OBJECT, preceding[2]) or re.search('(?:另一|其他|另外|另一个).{0,8}(?:药品|药物)', preceding[2])):
                    self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(), 'missing': '被援引款的药品指代缺少同条紧邻对象及完整限定条件'})
                    continue
                if current_object_binding is None:
                    raw = preceding[0]['text'][preceding[1][0]:preceding[1][1]]
                    normalized, offsets = matching_view(raw)
                    subject = re.match('(?:' + ARTICLE_REFERENCE + ')?[^，,。；;]{0,70}(?:药品|药物)(?=[，,。；;]|$)', normalized)
                    if subject is None:
                        self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(), 'missing': '被援引款药品指代不能与上一款独立条件分开定位'})
                        continue
                    left, right = raw_span(offsets, subject.start(), subject.end())
                    subject_span = (preceding[1][0] + left, preceding[1][0] + right)
                    antecedents.append((preceding[0], subject_span, subject.group()))
                    evidence.append(self._quote(preceding[0], '仅定位被援引款同条药品先行对象；不继承上一款独立条件', subject_span))
            for child, span, part in selected:
                evidence.append(self._quote(child, '当前条件—待遇明确援引的精确条款', span))
            chain = [{'article': article, 'clause': clause, 'container_context_id': container['context_id'], 'context_ids': [item[0]['context_id'] for item in selected]}]
            unexpanded = [{'reference': m.group(), 'reason': '对象先行词内部引用不继续展开'} for item in antecedents for m in re.finditer(ARTICLE_REFERENCE, item[2])]
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
                    if not re.search('按照|依照|适用|执行', prefix) or not re.search('(?:数据)?保护(?:的)?(?:数据)?范围|相应.{0,6}数据|受保护(?:的)?数据', part):
                        unexpanded.append({'reference': further.group(), 'reason': '非本款明确数据范围/权利后果引用'})
                        continue
                    if len(chain) >= 2:
                        unexpanded.append({'reference': further.group(), 'reason': '有限关系最多展开一个进一步确指条款'})
                        continue
                    donors = self._reference_candidates(current, further_article)
                    if len(donors) != 1:
                        further_missing = True
                        self.material_requests.append({'path': 'cited_standard', 'reference': further.group(), 'missing': '精确款再援引的数据保护范围/许可后果同源原文缺失或不唯一'})
                        continue
                    donor, donor_members = donors[0]
                    further_clause = ordinal_number(further.group(2)) if further.group(2) else None
                    if further_clause is not None:
                        if not 1 <= further_clause <= len(donor_members):
                            further_missing = True
                            self.material_requests.append({'path': 'cited_standard', 'reference': further.group(), 'missing': '再援引的精确款次未在同源有界条文中提供'})
                            continue
                        donor_members = [donor_members[further_clause - 1]]
                    scope = []
                    for item in donor_members:
                        subject = re.search('(?:数据)?保护(?:的)?(?:数据)?范围|受保护(?:的)?数据', item[2])
                        content = item[2][subject.end():] if subject else ''
                        if subject and re.search('包括|限于|涵盖|仅保护|不包括', content) and re.search('数据|证据|试验|研究|安全性|有效性|疗效|临床优势', content):
                            scope.append(item)
                    permissions = [item for item in donor_members if re.search('(?:数据)?保护期(?:间|内)', item[2]) and re.search('(?:不予|准予|予以|不得|不再|可以).{0,12}(?:许可|批准|依赖|使用)|(?:未经|经).{0,16}同意|(?:有权|享有).{0,12}(?:许可|同意|保护)|禁止.{0,12}(?:依赖|使用)', item[2])]
                    if not scope or not permissions:
                        further_missing = True
                        self.material_requests.append({'path': 'cited_standard', 'reference': further.group(), 'missing': '再援引条文未完整提供当前确指的数据范围及保护期间许可后果'})
                        continue
                    for item in scope:
                        data_scope_evidence.append(self._quote(item[0], '本款明确再援引的数据保护范围及排除内容', item[1]))
                    for item in permissions:
                        permission_evidence.append(self._quote(item[0], '本款保护待遇对应的期间许可后果及例外', item[1]))
                    evidence.extend(data_scope_evidence + permission_evidence)
                    chain.append({'article': further_article, 'clause': further_clause, 'container_context_id': donor['context_id'], 'context_ids': [item[0]['context_id'] for item in scope + permissions]})
                    unexpanded.extend(({'reference': m.group(), 'reason': '进一步范围/许可条文不作第三层展开'} for item in scope + permissions for m in re.finditer(ARTICLE_REFERENCE, item[2])))
            if further_missing:
                continue
            start = max(0, reference.start() - 16) + operative.start()
            consequence_start = reference.end() + consequence.start()
            self._add('cited_standard', evidence, '当前以精确条款条件决定实质保护待遇，仅补该款同条对象及其明确数据范围/许可后果；不继承独立兄弟待遇', relation_subtype='finite_operational_article_reference', protection_branch='conditional_table_exception' if '|' in self.norm else 'current_operative_reference', antecedent_scope='nominal_drug_subject_only; no_independent_preceding_eligibility', action_scope='explicit_article_condition_substantive_consequence', current_condition_anchor=self.current_anchor(start, reference.end()), current_consequence_anchor=self.current_anchor(consequence_start, reference.end() + consequence.end()), reference_chain=chain, reference_container_ids=[step['container_context_id'] for step in chain], object_definition=current_object_binding['text'] if current_object_binding else '\n'.join((item[0].get('text', '')[item[1][0]:item[1][1]] for item in antecedents)), current_object_binding=current_object_binding, qualification_text='\n'.join((e['text'] for e in evidence if e not in permission_evidence)), qualification_context_evidence=[e for e in evidence if e not in permission_evidence], treatment_context_evidence=permission_evidence, standard_text='\n'.join((e['text'] for e in evidence)), unexpanded_references=unexpanded, bounded_reference_depth=2)

    def _applicable_support(self):
        current = self._current_source()
        if current is None or not re.search('(?:创新|改良)(?:型)?药(?:品|物)?', self.norm):
            return
        arrangement = re.search('(?:本|该)(?:(?:工作)?规范|办法|规程|程序|方案|安排)', self.norm)
        authorization = re.search('(?:不再|不得|不能|可以|可|准许|允许)[^。；;]{0,45}(?:适用|使用|按照|依据)', self.norm)
        early_stage = re.search('临床试验[^。；;]{0,18}(?:完成前|结束前)|上市前|申报前|申请前|研发阶段|提前', self.norm)
        if not arrangement or not authorization or (not early_stage) or (authorization.end() > arrangement.start()):
            return
        noun = arrangement.group()[1:]
        arrangement_reference = '(?:本|该)(?:工作)?规范' if noun.endswith('规范') else f'(?:本|该){re.escape(noun)}'
        source_sha = current.get('source_ref', {}).get('sha256')
        groups = []
        for boundary in self.contexts:
            st = boundary.get('structure', {})
            ids = st.get('scope_context_ids', [])
            if boundary['kind'] != 'following_heading' or not ids or len(ids) != len(set(ids)) or (boundary.get('source_ref', {}).get('sha256') != source_sha) or (not same_component(boundary, current)):
                continue
            members = [self.by_id.get(cid) for cid in ids]
            if any((not c or c['kind'] != 'source_paragraph' or c.get('source_ref', {}).get('sha256') != source_sha or (not same_component(c, current)) or (not c.get('text')) for c in members)):
                continue
            current_copies = [c for c in members if norm(c.get('text', '')) == self.norm]
            if len(current_copies) != 1 or any((not same_component(c, current_copies[0]) for c in members)):
                continue
            first, last = (st.get('component_first_paragraph'), st.get('component_last_paragraph'))
            containers = [c for c in self.contexts if c['kind'] == 'source_paragraph' and c.get('source_ref', {}).get('sha256') == source_sha and same_component(c, current) and (c.get('structure', {}).get('first_paragraph') == first) and (c.get('structure', {}).get('last_paragraph') == last)]
            if not first or not last or len(containers) != 1:
                continue
            if st.get('follows_context_id') != ids[-1]:
                continue
            groups.append((boundary, containers[0], members))
        if len(groups) != 1:
            self.material_requests.append({'path': 'named_mechanism', 'reference': arrangement.group(), 'missing': '当前申请前适用/限制确指的同源规范组件范围不能闭合绑定'})
            return
        boundary, container, members = groups[0]
        objects, stages, supports = ([], [], [])
        for c in members:
            raw = c.get('text', '')
            for a, b in sentence_spans(raw):
                part = norm(raw[a:b])
                if (re.search('适用范围', part) or re.search(arrangement_reference + '适用于', part)) and re.search('创新|改良', part):
                    objects.append(self._quote(c, '同一规范有界组件的对象及排除范围', (a, b)))
                if re.search(arrangement_reference, part) and re.search('研发阶段|临床试验.{0,35}完成后|上市前|申报前', part) and (norm(raw) != self.norm):
                    stages.append(self._quote(c, '同一规范通常适用的上市前研究阶段', (a, b)))
                if re.search('沟通交流(?:时限|期限).{0,16}\\d+(?:个)?(?:工作)?(?:日|天)', part) or re.search('(?:品种)?审评(?:时限|期限).{0,45}(?:优先审评|单独序列|\\d+(?:个)?(?:工作)?(?:日|天))', part) or re.search('(?:实行|设置|开放|采用).{0,12}(?:单独序列|优先审评).{0,20}(?:缩短|加快|时限)', part) or re.search('(?:提供|可申请|获得).{0,18}(?:研究方案反馈|试验方案反馈|研发技术咨询|技术服务)', part):
                    if not re.search('(?:不提供|不开展|仅提供).{0,20}(?:电话|视频|渠道|一般资料)', part):
                        supports.append(self._quote(c, '当前提前适用直接开放的同规范办理便利/技术支持', (a, b)))
        if not objects or not stages or (not supports):
            return
        self._add('named_mechanism', objects + stages + supports, '当前明确创新药申请前适用/限制同一规范，仅补同组件对象、通常研究阶段及直接可用便利；不复制平行义务', relation_subtype='bounded_rule_preapplication_authorization', object_definition='\n'.join((e['text'] for e in objects)), direct_mechanism='\n'.join((e['text'] for e in supports)), research_stage='\n'.join((e['text'] for e in stages)), current_authorization_anchor=self.current_anchor(authorization.start(), arrangement.end()), mechanism_name=arrangement.group(), version_binding={'established': True, 'binding': 'same_source_closed_component', 'source_sha256': source_sha}, scope_binding={'container_context_id': container['context_id'], 'boundary_context_id': boundary['context_id'], 'context_ids': boundary['structure']['scope_context_ids'], 'component_first_paragraph': boundary['structure']['component_first_paragraph'], 'component_last_paragraph': boundary['structure']['component_last_paragraph']})

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
            for clause in re.findall('[^。；;，,]+', self.norm):
                clean = title_key(clause)
                pos = clean.find(key)
                if pos < 0:
                    continue
                before, after = (clean[:pos], clean[pos + len(key):])
                actions = list(re.finditer(ACTION, before))
                if not actions or len(before) - actions[-1].end() > 35 or re.search('详见|附件|名称|资料|归档|格式|印发', before[actions[-1].end():]) or re.match('(?:资料|文件|的?归档|名称|格式)', after):
                    continue
                action_clause = clause
                break
            if action_clause is None:
                continue
            matched_source = True
            ver = self._version(c, action_clause)
            if not ver['established']:
                self.material_requests.append({'path': 'named_mechanism', 'reference': title, 'missing': '具名机制的行动时期与来源版本未能绑定', 'version_binding': ver})
                continue
            text = c['text']
            objects, mechanisms = ([], [])
            for a, b in sentence_spans(text):
                s = norm(text[a:b])
                if re.search('(?:范围|适用对象|适用于|面向).{0,65}(?:创新|改良)|(?:创新|改良).{0,20}(?:范围|适用对象)', s):
                    objects.append(self._quote(c, '同版安排的对象与排除范围', (a, b)))
                if re.search('(?:审评|审批).{0,20}(?:\\d+个?工作日|缩短|加快)|(?:\\d+个?工作日).{0,20}(?:完成|审评|审批)|(?:提供|开展|申请|获得).{0,20}(?:技术服务|方案反馈|沟通交流)', s):
                    if not re.search('廉政|纪律|风险.{0,8}义务', s):
                        mechanisms.append(self._quote(c, '当前实施行为直接对应的研发安排', (a, b)))
            if objects and mechanisms:
                self._add('named_mechanism', objects + mechanisms, '当前实质实施同一具名安排，按来源日期绑定，仅补对象及直接可用机制', object_definition='\n'.join((e['text'] for e in objects)), direct_mechanism='\n'.join((e['text'] for e in mechanisms)), version_binding=ver, mechanism_name=title)
            else:
                self.material_requests.append({'path': 'named_mechanism', 'reference': title, 'missing': '同版安排缺少可定位对象定义或直接机制原文'})
        if not matched_source and re.search('(?:实施|设立|开放|组织开展).{0,40}(?:创新|改良).{0,35}(?:试点|计划|通道)', self.norm) and (not re.search('(?:试点|计划|通道)(?:资料|文件|的?归档|名称|格式)', self.norm)) and (not re.search('提供.{0,20}(?:反馈|技术服务)|加快.{0,15}审评|缩短.{0,15}(?:研发|试验)', self.norm)):
            self.material_requests.append({'path': 'named_mechanism', 'reference': self.text, 'missing': '当前实质实施具名支持安排，缺少同版对象与直接可用机制原文'})

    def _explanations(self):
        explanations = [c for c in self.contexts if self._neutral_source(c) and ('解读' in self._metadata(c).get('source_document_kind', '') or self._metadata(c).get('source_document_kind') == 'official_policy_explainer')]
        if not explanations or not re.search('建设|优化|建立|完善|保障|改进', self.norm):
            return
        features = re.findall('(?:偏远地区|县域中心药房|上下.{0,5}用药衔接|基层药品配送)', self.norm)
        groups = {}
        for c in explanations:
            meta = self._metadata(c)
            binding = (c.get('source_ref', {}).get('sha256'), meta.get('policy_document_number'), meta.get('policy_document_date'), meta.get('source_title'))
            if not all(binding) or not self._version(c)['established']:
                continue
            groups.setdefault(binding, []).append(c)
        for binding, group in groups.items():
            measure_quotes, problem_quotes = ([], [])
            for c in group:
                for a, b in sentence_spans(c['text']):
                    s = norm(c['text'][a:b])
                    if not any((f in s for f in features)):
                        continue
                    if re.search('鼓励|建设|优化|建立|完善', s):
                        measure_quotes.append(self._quote(c, '官方解释与当前同一措施的文字映射', (a, b)))
                    if re.search('不稳定|断供|可及性差|不畅|差异|不平衡|能力弱|障碍', s):
                        problem_quotes.append(self._quote(c, '该措施明确对应的药品获取问题', (a, b)))
            if measure_quotes and problem_quotes:
                self._add('policy_explanation', problem_quotes + measure_quotes, '共同包同政策解释按当前措施的原文字面关系补足对象及问题，不扩散其他措施', problem_text='\n'.join((e['text'] for e in problem_quotes)), measure_text='\n'.join((e['text'] for e in measure_quotes)), version_binding=[self._version(c) for c in group], policy_binding=binding)

    def _anaphors(self):
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            st = c.get('structure', {})
            t = c.get('text', '')
            if current_sources and c.get('source_ref', {}).get('sha256') not in current_sources:
                continue
            if (st.get('source_role') == 'self_declared_scope' or (c['kind'] == 'source_paragraph' and re.search('^\\(?[一二三四五六七八九十]+\\)?.{0,3}适用范围', norm(t)))) and re.search(OBJECT, norm(t)):
                self._add('anaphor', [self._quote(c, '同组件/适用范围仅用于确认当前对象')], '原文同组件范围说明对象；不复制其他维度内容', object_text=t)

    def _tables(self):
        current_cells = [c for c in self.contexts if c['kind'] in ('table_row_cell', 'table_row') and norm(c.get('text', '')) == self.norm]
        for cell in current_cells:
            st = cell.get('structure', {})
            columns = st.get('column_indices', [st.get('column_index')])
            headers = [c for c in self.contexts if c['kind'] in ('table_header_cell', 'table_header') and c.get('text') and (c.get('structure', {}).get('column_index') in columns) and (c.get('source_ref', {}).get('sha256') == cell.get('source_ref', {}).get('sha256'))]
            for header in headers:
                self._add('parent_predicate', [self._quote(header, '同表同列标题补全当前单元格内容')], '来源表格坐标建立当前值与同列内容对象的关系', shared_predicate=header['text'], member_text=self.text, table_cell_binding={'row': st.get('row_index_zero_based'), 'columns': columns})

    def _resource_definitions(self):
        entity = re.search('(?:组建|建立|设立|安排)([^。；;，,]{1,15}团队)', self.norm)
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
                bound_entity = re.search(f'(?:{re.escape(entity.group(1))}|该团队|本团队|此团队).{{0,15}}(?:负责|提供|服务)', part)
                if bound_entity and (not re.search('另一(?:支|个)?团队|其他团队|另一支[^。]{0,15}团队|其他[^。]{0,15}团队', part)) and re.search('技术审评|方案反馈|技术咨询|研究反馈', part):
                    services.append(self._quote(paragraph, '当前所设资源在同段的实际技术服务定义', (a, b)))
            stages = [c for c in self.contexts if c['kind'] == 'source_paragraph' and c.get('source_ref', {}).get('sha256') == source_sha and same_component(c, paragraph) and re.search('研发阶段|临床试验.{0,60}(?:上市前|研发阶段)', norm(c.get('text', ''))) and re.search('上市前', norm(c.get('text', '')))]
            objects = [e for r in scope for e in r['context_evidence'] if e['source_ref'].get('sha256') == source_sha and same_component(self.by_id[e['context_id']], paragraph)]
            stages = [c for c in stages if all((same_component(c, self.by_id[e['context_id']]) for e in objects))]
            if services and stages and objects:
                stage_quotes = [self._quote(c, '同组件明确适用的上市前研发阶段') for c in stages]
                self._add('named_mechanism', objects + services + stage_quotes, '当前设立资源与同段功能定义直接承接，同源适用范围及上市前阶段补对象；团队名称本身不充分', object_definition='\n'.join((e['text'] for e in objects)), direct_mechanism='\n'.join((e['text'] for e in services)), research_stage='\n'.join((e['text'] for e in stage_quotes)), version_binding={'established': True, 'binding': 'same_source_component', 'source_sha256': source_sha}, mechanism_name=entity.group(1), resource_definition_required=True)

    def object_evidence(self, a=0, b=None):
        b = len(self.norm) if b is None else b
        candidates = list(re.finditer(OBJECT, self.norm))
        if candidates:
            m = min(candidates, key=lambda m: abs(m.start() - a))
            return {'established': True, 'current_anchors': [self.current_anchor(m.start(), m.end())], 'context_evidence': [], 'object_text': m.group(), 'role': 'current_drug_or_treatment_object', 'reason': '当前完整命题直接表达药品、研发或患者治疗对象'}
        current_sources = {c.get('source_ref', {}).get('sha256') for c in self.contexts if c['kind'] == 'paragraph' and self.norm in norm(c.get('text', ''))}
        for c in self.contexts:
            if c['kind'] not in ('parent_paragraph', 'heading'):
                continue
            if current_sources and c.get('source_ref', {}).get('sha256') not in current_sources:
                continue
            m = re.search(OBJECT, norm(c.get('text', '')))
            if m:
                return {'established': True, 'current_anchors': [], 'context_evidence': [self._quote(c, '承接对象解释，不作维度内容')], 'object_text': c['text'], 'role': 'explicit_parent_or_heading_object', 'reason': '直接父句或标题仅补当前对象'}
        for rel in self.linked('parent_predicate'):
            if rel['details'].get('table_cell_binding') and re.search(OBJECT, rel['details']['content']):
                return {'established': True, 'current_anchors': [], 'context_evidence': rel['context_evidence'], 'object_text': rel['details']['content'], 'role': 'same_table_same_column_object', 'reason': '当前单元格按来源同列标题建立对象'}
        if re.search('具体品种|该品种|相关品种|本品种|该项目|本项目', self.norm):
            for rel in self.linked('anaphor'):
                return {'established': True, 'current_anchors': [], 'context_evidence': rel['context_evidence'], 'object_text': rel['details']['object_text'], 'role': 'same_source_explicit_scope_anaphor', 'reason': '当前品种/项目指代由同来源明确适用范围补全对象；内容仍由当前行动判断'}
        return {'established': False, 'current_anchors': [], 'context_evidence': [], 'object_text': '', 'role': None, 'reason': '当前及明确承接范围未建立药品/患者治疗对象'}

    def _se_next_geometry(self, left, right, check_spans=True):
        """A boundary must be next, not merely named as next by a container."""
        if not self._se_same_geometry(left, right):
            return None
        proof = []
        a, ok = self._se_geometry_value(left, 'sequence_index')
        b, ok2 = self._se_geometry_value(right, 'sequence_index')
        if not ok or not ok2:
            return None
        if type(a) is int and type(b) is int:
            if b != a + 1:
                return None
            proof.append('adjacent_supplied_sequence')
        a, ok = self._se_geometry_value(left, 'paragraph_id')
        b, ok2 = self._se_geometry_value(right, 'paragraph_id')
        if not ok or not ok2:
            return None
        a = re.sub('_item\\d+$', '', a or '')
        b = re.sub('_item\\d+$', '', b or '')
        m = re.fullmatch('(.+?)(\\d+)', a)
        n = re.fullmatch('(.+?)(\\d+)', b)
        if m and n:
            if m.group(1) != n.group(1) or int(n.group(2)) != int(m.group(2)) + 1:
                return None
            proof.append('adjacent_supplied_original_paragraph')
        if not proof:
            return None
        aa = left.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
        bb = right.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
        if check_spans and isinstance(aa, list) and isinstance(bb, list) and (len(aa) == len(bb) == 2) and (bb[0] < aa[1]):
            return None
        return {'evidence_grade': proof, 'component_identity_supplied': bool(self._se_geometry_value(left, 'component_id')[0])}

    def _se_article_proof(self, members, number):
        if any(not self._supplied_address(c)['valid'] or (self._supplied_article_number(c) is not None and self._supplied_article_number(c)!=number) for c in members):
            return None
        for container in self.contexts:
            if container['kind'] not in ('cited_reference', 'ordered_list'):
                continue
            ids = [i for g in container.get('structure', {}).get('child_groups', []) if g.get('position') in ('contexts', 'members', 'ordered_members') for i in g.get('ordered_context_ids', [])]
            if ids == [c['context_id'] for c in members]:
                proof = self._se_group_proof(container, members)
                if proof:
                    return proof
        if len(members) == 1 and norm(members[0]['text']).endswith('。'):
            last = members[-1]
            pid = last.get('structure', {}).get('paragraph_id')
            m = re.fullmatch('(.+?)(\\d+)', pid or '')
            for c in self.contexts:
                h = re.match(ARTICLE_REFERENCE, norm(c.get('text', '')))
                if not h or ordinal_number(h.group(1)) != number + 1 or not self._supplied_address(c)['valid'] or c['source_ref']['sha256'] != last['source_ref']['sha256']:
                    continue
                adjacency = self._se_next_geometry(last, c)
                if not adjacency:
                    continue
                n = re.fullmatch('(.+?)(\\d+)', c.get('structure', {}).get('paragraph_id', ''))
                if not m or not n or m.group(1) != n.group(1) or (int(n.group(2)) != int(m.group(2)) + 1):
                    continue
                q = self._quote(c, '条文下一条同源相邻原件首界，仅验证本条闭合')
                return {'boundary_quotes': [q], 'source_sha256': last['source_ref']['sha256'], 'adjacent_original_paragraph_boundary': True, 'adjacency_geometry': adjacency}
        return None

    def _se_preceding_binding(self, preceding):
        """Use the frozen local role only absent contradictory supplied geometry."""
        if preceding.get('source_ref', {}).get('sha256') != self.unit.get('source_ref', {}).get('sha256'):
            return None
        current = re.sub('\\s+', '', self.norm)
        for c in self._se_current_geometry_contexts():
            if not self._se_same_geometry(preceding, c):
                continue
            a = preceding.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
            b = c.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
            if isinstance(a, list) and isinstance(b, list) and (len(a) == len(b) == 2) and (any((type(x) is not int for x in a + b)) or a[0] > a[1] or b[0] > b[1] or (a[1] > b[0])):
                continue
            pp, ok = self._se_geometry_value(preceding, 'paragraph_id')
            cp, ok2 = self._se_geometry_value(c, 'paragraph_id')
            if not ok or not ok2:
                continue
            if pp and cp:
                if pp == cp:
                    return {'evidence_grade': 'same_original_paragraph_and_supplied_local_role'}
                adjacency = self._se_next_geometry(preceding, c)
                if not adjacency:
                    continue
                return adjacency
            a, ok = self._se_geometry_value(preceding, 'sequence_index')
            b, ok2 = self._se_geometry_value(c, 'sequence_index')
            if not ok or not ok2 or (type(a) is int and type(b) is int and (b != a + 1)):
                continue
            return {'evidence_grade': 'supplied_local_preceding_role_only', 'not_independent_source_adjacency_verification': True}
        return None

    def _se_parent_span_geometry(self, parent, current):
        """Known original spans must precede or contain the direct target."""
        a = parent.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
        b = current.get('source_ref', {}).get('locator', {}).get('unicode_code_point_interval_half_open')
        if not (isinstance(a, list) and isinstance(b, list) and (len(a) == len(b) == 2)):
            return {'evidence_grade': 'supplied_structural_relation_without_complete_spans', 'original_span_order_independently_verified': False}
        if any((type(x) is not int for x in a + b)) or a[0] > a[1] or b[0] > b[1]:
            return None
        if a[1] <= b[0]:
            return {'evidence_grade': 'supplied_source_parent_precedes_target', 'not_alone_a_parent_relation': True}
        if a[0] <= b[0] and a[1] >= b[1]:
            return {'evidence_grade': 'supplied_source_parent_contains_target', 'not_alone_a_parent_relation': True}
        return None

    def _se_edition(self, c):
        binding = self._version(c)
        if binding['established']:
            return binding
        sha = c['source_ref']['sha256']
        quoted_names = re.findall('《([^》]+)》', self.norm)
        for doc in self.bundle.get('source_documents', []):
            if doc.get('source_sha256') != sha or doc.get('byte_SHA_verified') is not True:
                continue
            lines = '\n'.join(doc.get('source_title_lines_verbatim_extraction_candidates', []))
            names = [name for name in quoted_names if name in norm(lines)]
            dates = re.findall('(?:19|20)\\d{2}\\s*年\\s*\\d{1,2}\\s*月\\s*\\d{1,2}\\s*日', lines)
            if names and dates:
                return {'established': True, 'binding': 'quoted_title_and_date_in_bound_original_source_text', 'source_sha256': sha, 'matched_literal_titles': names, 'date_literals': dates, 'filename_not_used': True}
        return binding

    def _supplied_address(self, context):
        """Raw metadata stays unchanged; invalid/conflicting addresses cannot bind.

        Legal integer/text ordinals are matched against any actual source head.
        Missing heads do not become quotes or prove a complete article/clause.
        """
        st=context.get('structure',{})
        errors=[];values={'article':None,'clause':None}
        for field, parser in (('article',article_number),('clause',clause_number)):
            if field not in st or st[field]=='':
                continue
            value=parser(st[field])
            if value is None:
                errors.append({'field':field,'reason':'illegal_type_or_ordinal_format','metadata_type':type(st[field]).__name__,'metadata_value':st[field]})
            values[field]=value
        if 'clause_index_one_based' in st:
            index=clause_number(st['clause_index_one_based'])
            if index is None:
                errors.append({'field':'clause_index_one_based','reason':'illegal_type_or_ordinal_format','metadata_type':type(st['clause_index_one_based']).__name__,'metadata_value':st['clause_index_one_based']})
            elif values['clause'] is not None and values['clause']!=index:
                errors.append({'field':'clause','reason':'clause_label_index_conflict','metadata_value':st.get('clause'),'index_value':st['clause_index_one_based']})
            else:
                values['clause']=index
        metadata_address=re.fullmatch(ARTICLE_REFERENCE,norm(st['article'])) if type(st.get('article')) is str else None
        if metadata_address and metadata_address.group(2):
            metadata_clause=ordinal_number(metadata_address.group(2))
            if values['clause'] is not None and values['clause']!=metadata_clause:
                errors.append({'field':'clause','reason':'article_address_clause_label_conflict','metadata_number':values['clause'],'article_address_clause':metadata_clause})
            elif metadata_clause is None or metadata_clause<1:
                errors.append({'field':'article','reason':'illegal_compound_clause_ordinal','metadata_value':st['article']})
            else:
                values['clause']=metadata_clause
        literal=re.match(ARTICLE_REFERENCE,norm(context.get('text','')))
        literal_article=ordinal_number(literal.group(1)) if literal else None
        literal_clause=ordinal_number(literal.group(2)) if literal and literal.group(2) else None
        if literal_article is not None and values['article'] is not None and literal_article!=values['article']:
            errors.append({'field':'article','reason':'metadata_original_heading_conflict','metadata_number':values['article'],'original_number':literal_article})
        if literal_clause is not None:
            if values['clause'] is not None and literal_clause!=values['clause']:
                errors.append({'field':'clause','reason':'metadata_original_heading_conflict','metadata_number':values['clause'],'original_number':literal_clause})
            elif values['clause'] is None:
                values['clause']=literal_clause
        if errors:
            issue={'kind':'context_structure_address','context_id':context.get('context_id'),'source_ref':context.get('source_ref'),
                   'errors':errors,'original_literal_address':literal.group() if literal else None,'original_article_number':literal_article,'metadata_number_used_as_quote':False}
            if issue not in self.structural_address_issues:
                self.structural_address_issues.append(issue)
        return dict(values,valid=not errors,errors=errors,original_article=literal_article,original_clause=literal_clause)

    def _supplied_article_number(self, context):
        value=self._supplied_address(context)
        return value['article'] if value['valid'] else None

    def _supplied_clause_number(self, context):
        value=self._supplied_address(context)
        return value['clause'] if value['valid'] else None

    def _supplied_group_article_number(self, group):
        number=article_number(group.get('article',''))
        if number is None and 'article' in group and group['article']!='':
            issue={'kind':'ordered_article_group_address','field':'article','metadata_value':group['article'],'metadata_type':type(group['article']).__name__,
                   'reason':'illegal_type_or_ordinal_format','ordered_source_resource_ids':group.get('ordered_source_resource_ids',[]),'metadata_number_used_as_quote':False}
            if issue not in self.structural_address_issues:
                self.structural_address_issues.append(issue)
        return number

    def _se_clause_proof(self, members, number, clause):
        proof = self._se_article_proof(members, number)
        if proof:
            return proof
        if len(members) != 1 or not norm(members[0]['text']).endswith('。'):
            return None
        last = members[0]
        m = re.fullmatch('(.+?)(\\d+)', last.get('structure', {}).get('paragraph_id', ''))
        for c in self.contexts:
            st = c.get('structure', {})
            article = self._supplied_article_number(c)
            n = re.fullmatch('(.+?)(\\d+)', st.get('paragraph_id', ''))
            if article != number or self._supplied_clause_number(c) != clause + 1:
                continue
            if c['source_ref']['sha256'] != last['source_ref']['sha256'] or not same_component(last, c):
                continue
            adjacency = self._se_next_geometry(last, c)
            if not adjacency:
                continue
            if not m or not n or m.group(1) != n.group(1) or (int(n.group(2)) != int(m.group(2)) + 1):
                continue
            q = self._quote(c, '明确款次的下一款同源相邻原件首界，仅验证本款闭合')
            return {'boundary_quotes': [q], 'source_sha256': last['source_ref']['sha256'], 'adjacent_original_clause_boundary': True, 'adjacency_geometry': adjacency}
        return None

    def _se_operational_references(self):
        current = self.norm
        operative = re.search('符合|不符合|满足|不满足|核验|确认.{0,20}条件|就.{0,20}条件', current)
        if not operative:
            return
        if re.search('(?:本方案|本文件).{0,45}(?:部分|节).{0,65}(?:所列条件|条件)', current):
            options = []
            for container in self.contexts:
                if container['kind'] != 'cited_reference':
                    continue
                addr = container.get('structure', {}).get('reference_address')
                addresses = [addr] if isinstance(addr, str) else list(addr.values()) if isinstance(addr, dict) else []
                if not any((isinstance(a, str) and norm(a) in current for a in addresses)):
                    continue
                ids = [i for g in container.get('structure', {}).get('child_groups', []) if g.get('position') == 'contexts' for i in g.get('ordered_context_ids', [])]
                contexts = [self.by_id.get(i) for i in ids]
                proof = self._se_group_proof(container, contexts)
                if proof:
                    options.append((contexts, proof))
            if len(options) == 1:
                contexts, proof = options[0]
                self._add('cited_standard', [self._quote(c, '当前地址对应的完整同源章节条件') for c in contexts] + proof['boundary_quotes'], '核地址、成员、首末、同源下一段；不递归展开隐含或其他章节', relation_subtype='SE_closed_explicit_section', affected_dimensions=['S', 'E', 'Ec'], SE_scope_verified=True, closure_proof=proof, full_scope=True, finite_reference_depth=1)
            else:
                self.material_requests.append({'path': 'cited_standard', 'reference': '当前本方案/本文件确指章节条件', 'missing': '地址及实际同源边界未唯一核明，不能以仅有boundary字段声明完整', 'dimensions': ['S', 'E', 'Ec']})
        requested = []
        for number, clause in re.findall(ARTICLE_REFERENCE, current[operative.start():]):
            key = (ordinal_number(number), ordinal_number(clause) if clause else None)
            if key not in requested:
                requested.append(key)
        for number, clause in requested:
            grouped = {}
            for c in self.contexts:
                if c['kind'] != 'cited_article' or not c.get('text'):
                    continue
                address = self._supplied_address(c)
                if address['valid'] and address['article'] == number:
                    grouped.setdefault(c['source_ref']['sha256'], []).append(c)
            options = []
            for sha, members in grouped.items():
                unique = []
                for c in sorted(members, key=lambda c: c.get('structure', {}).get('sequence_index', 0)):
                    if c['text'] not in [m['text'] for m in unique]:
                        unique.append(c)
                if not unique or not self._se_edition(unique[0])['established']:
                    continue
                if clause is None:
                    if not re.match(ARTICLE_REFERENCE, norm(unique[0]['text'])):
                        continue
                    consumed = unique
                    proof = self._se_article_proof(unique, number)
                else:
                    consumed = [c for c in unique if self._supplied_clause_number(c) == clause]
                    if not consumed:
                        continue
                    proof = self._se_clause_proof(consumed, number, clause)
                    if not proof and re.match(ARTICLE_REFERENCE, norm(unique[0]['text'])):
                        proof = self._se_article_proof(unique, number)
                if not proof:
                    continue
                options.append((consumed, proof))
            if len(options) == 1:
                members, proof = options[0]
                self._add('cited_standard', [self._quote(c, '当前操作性标准确指的条/款内容及限定') for c in members] + proof['boundary_quotes'], '原包核同版且完整闭合；明确款次只消费该款，兄弟款作为边界不能捐献内容', relation_subtype='SE_closed_explicit_article_condition', affected_dimensions=['S', 'E', 'Ec'], SE_scope_verified=True, reference_article=number, reference_clause=clause, version_binding=self._se_edition(members[0]), closure_proof=proof, full_scope=clause is None)
            else:
                issues=[issue for issue in self.structural_address_issues if issue.get('original_article_number') in (None,number,number+1)]
                self.material_requests.append({'path': 'cited_standard', 'reference': f'当前操作性第{number}条' + (f'第{clause}款' if clause else '') + '条件', 'missing': '该确指同版条/款的完整原文及原件末边界未唯一核明；不从已供编号/句号闭合或扩为整条' + ('；已供结构编号非法或与原文矛盾，须核正该引用源定位' if issues else ''), 'dimensions': ['S', 'E', 'Ec'], **({'structural_address_issues':issues} if issues else {})})

    def _IF_operative_standard_consumers(self, reference=None, article=None, clause=None):
        """A direct topic qualifier bounds unknown standard consumers.

        Unqualified whole substantive conditions can contain any construct.
        A current efficacy-only evidence requirement does not make I/F unknown.
        These are consumer scopes, never inferred absent source contents.
        """
        if article is None and reference:
            parsed = re.search(ARTICLE_REFERENCE, norm(reference))
            if parsed:
                article=ordinal_number(parsed.group(1));clause=ordinal_number(parsed.group(2)) if parsed.group(2) else None
        topics='安全性|风险|有效性|疗效|效果|经济性|成本|价格|创新性|公平性'
        construct={'安全性':'S','风险':'S','有效性':'E','疗效':'E','效果':'E','经济性':'Ec','成本':'Ec','价格':'Ec','创新性':'I','公平性':'F'}
        sequence='(?:'+topics+')(?:[和及、与](?:'+topics+'))*'
        plain_article='第'+ORDINAL+'条(?:第'+ORDINAL+'款)?'
        matches=[]
        for match in re.finditer(ARTICLE_REFERENCE,self.norm):
            number=ordinal_number(match.group(1));part=ordinal_number(match.group(2)) if match.group(2) else None
            if article is not None and (number!=article or part!=clause):
                continue
            after=self.norm[match.end():]
            connected=re.match('(?:(?:和|及|与|、|,|，)'+plain_article+')+',after)
            offset=connected.end() if connected else 0
            after=after[offset:]
            qualifier=re.match('的?(?:本药|药品|药物|用药|治疗)?(?P<topics>'+sequence+')(?:实质)?(?:标准|条件|证据(?:要求)?|信息(?:要求)?)',after)
            if qualifier:
                values=[construct[x] for x in re.findall(topics,qualifier.group('topics'))]
                matches.append((values,match.end()+offset,match.end()+offset+qualifier.end()))
                continue
            before=self.norm[:match.start()]
            subject=re.search('(?P<topics>'+sequence+')(?:证据|信息)?(?:应当|必须|应|须)(?:满足|符合|达到|遵守|核验)[^。；;，,]{0,35}$',before)
            if subject:
                values=[construct[x] for x in re.findall(topics,subject.group('topics'))]
                matches.append((values,subject.start(),subject.end()))
                continue
            return {'dimensions':['I','F'],'basis':'current exact unqualified substantive article/clause; absent scope unknown, not all unrelated references','current_qualifier_anchor':None}
        if matches:
            dims=[d for d in ('I','F') if d in {v for values,_,_ in matches for v in values}]
            a=min(x[1] for x in matches);b=max(x[2] for x in matches)
            return {'dimensions':dims,'basis':'explicit current topic-qualified standard consumer; other dimensions are not inferred','current_qualifier_anchor':self.current_anchor(a,b)}
        return {'dimensions':['I','F'],'basis':'current exact whole section or unqualified substantive scope; no dimension content inferred from missing material','current_qualifier_anchor':None}

    def _IF_closed_operational_content(self, operational_requests):
        """Reuse neutral closure only for exact current substantive standards.

        SE producer permissions stay intact. A separate I/F relation consumes
        the same proven selected article/clause; boundary siblings do not enter.
        Missing references route to I/F separately without clearing any stops.
        """
        for relation in list(self.linked('cited_standard')):
            details = relation.get('details') or {}
            if details.get('relation_subtype') not in {'SE_closed_explicit_article_condition', 'SE_closed_explicit_section'} or not details.get('SE_scope_verified'):
                continue
            consumer_scope=self._IF_operative_standard_consumers(article=details.get('reference_article'),clause=details.get('reference_clause'))
            if not consumer_scope['dimensions']:
                continue
            shared = {key:value for key,value in details.items() if key not in {'affected_dimensions','only_IF_consumers','relation_subtype'}}
            shared.update(relation_subtype='IF_closed_operational_content', affected_dimensions=consumer_scope['dimensions'], only_IF_consumers=True, neutral_closure_reused_from=details['relation_subtype'], scope_is_not_dimension_label=True, current_operative_consumer_scope=consumer_scope)
            evidence = relation.get('context_evidence') or []
            self._add('cited_standard', evidence, '当前明确要求同版确指实质标准；复用已经核明的同源有界条/款证明，仅把实际内容交I/F消费者逐维检查，闭合不赋标签', **shared)
            reference = ('第'+str(details['reference_article'])+'条'+('第'+str(details['reference_clause'])+'款' if details.get('reference_clause') is not None else '')) if 'reference_article' in details else '当前同版确指章节实质标准'
            self.source_requests.append({'path':'cited_standard','reference':reference,'current_text':self.text,'dependency_status':'resolved','resolution_path':'neutral_closed_operational_content_IF_consumer','affected_dimensions':consumer_scope['dimensions'],'current_operative_consumer_scope':consumer_scope,'closure_proof':details.get('closure_proof'),'reference_article':details.get('reference_article'),'reference_clause':details.get('reference_clause'),'evidence':evidence,'no_new_material':True,'other_unresolved_requests_retained':True})
        for original in operational_requests:
            if original.get('path') != 'cited_standard':
                continue
            consumer_scope=self._IF_operative_standard_consumers(reference=original.get('reference'))
            if not consumer_scope['dimensions']:
                continue
            request = dict(original)
            request.pop('affected_dimensions', None)
            request.update(dimensions=consumer_scope['dimensions'], current_operative_consumer_scope=consumer_scope, original_operational_request_consumers=list(original.get('dimensions', [])), stop_scope='exact current operative reference; no absence-as-zero', dependency_status='stopped')
            if request not in self.material_requests:
                self.material_requests.append(request)

    def _IF_named_feedback_access(self):
        """Current service to admitted projects plus exact same-stage scope.

        The component only proves source bounds. Actual content comes from the
        single direct applicability/service sentence, never parallel standards.
        """
        current = self._current_source()
        if current is None:
            return
        access = re.search('开放|提供|实施|可(?:以)?(?:获得|预约)|允许[^。；;]{0,10}使用|不再提供|撤回|终止', self.norm)
        service = re.search('(?:研究|试验|研发)(?:方案|设计|技术)[^。；;，,]{0,12}(?:反馈|意见|建议|咨询|服务)', self.norm)
        if not access or not service or not re.search('纳入[^。；;]{0,40}(?:项目|药品)|(?:本|该)(?:计划|程序|通道)[^。；;]{0,12}(?:项目|药品)', self.norm):
            return
        if re.search('上市后[^。；;]{0,20}(?:日常|常规|监测|临床服务)|仅[^。；;]{0,12}(?:电话|视频|形式|签章|归档)', self.norm):
            return
        primary = self.unit.get('source_ref', {}).get('sha256')
        options = []
        for boundary in self.contexts:
            st = boundary.get('structure', {});ids = st.get('scope_context_ids', [])
            if boundary['kind'] != 'following_heading' or not ids or len(ids) != len(set(ids)):
                continue
            members = [self.by_id.get(cid) for cid in ids]
            if any(not c or c['kind'] != 'source_paragraph' or not c.get('text') or c.get('source_ref',{}).get('sha256') != primary or not self._se_same_geometry(c,current) for c in members):
                continue
            actual_members=[]
            target_span=self.unit.get('source_ref',{}).get('locator',{}).get('unicode_code_point_interval_half_open')
            current_pid,current_pid_ok=self._se_geometry_value(current,'paragraph_id')
            for c in members:
                if norm(c['text'])!=self.norm or not self._se_same_geometry(c,current):
                    continue
                pid,pid_ok=self._se_geometry_value(c,'paragraph_id')
                if not current_pid_ok or not pid_ok or (pid and current_pid and pid!=current_pid):
                    continue
                span=c.get('source_ref',{}).get('locator',{}).get('unicode_code_point_interval_half_open')
                if isinstance(target_span,list) and isinstance(span,list) and len(target_span)==len(span)==2:
                    if any(type(v) is not int for v in target_span+span) or not span[0]<=target_span[0]<=target_span[1]<=span[1]:
                        continue
                actual_members.append(c)
            if len(actual_members)!=1:
                continue
            if st.get('follows_context_id') != ids[-1] or not self._se_next_geometry(members[-1],boundary):
                continue
            if any(not self._se_next_geometry(a,b) for a,b in zip(members,members[1:])):
                continue
            containers = [c for c in self.contexts if c['kind']=='source_paragraph' and not c.get('text') and c.get('structure',{}).get('first_paragraph')==st.get('component_first_paragraph') and c.get('structure',{}).get('last_paragraph')==st.get('component_last_paragraph') and c.get('source_ref',{}).get('sha256')==primary and same_component(c,current)]
            if len(containers)!=1:
                continue
            names=[norm(c['text']) for c in members if re.fullmatch(PROGRAM,norm(c['text']))]
            explicit_names=[name for name in names if name in self.norm]
            if explicit_names:
                names=explicit_names
            elif not re.search('(?:本|该)(?:计划|程序|通道)',self.norm):
                names=[]
            # A local anaphor can bind only the one fully closed programme in
            # this actual current component, never a title elsewhere.
            if len(set(names))!=1:
                continue
            definitions=[]
            family=re.search('研究方案|试验方案|研发技术|研究设计|试验设计',service.group())
            for c in members:
                for a,b in sentence_spans(c['text']):
                    part=norm(c['text'][a:b])
                    if not re.search('(?:本|该)(?:计划|程序|通道)(?:仅)?(?:面向|适用于)|(?:本|该)(?:计划|程序|通道)(?:的)?(?:支持)?(?:对象|适用对象|支持目标|适用范围)(?:为|是|包括)|适用(?:对象|范围)[^。；;]{0,20}(?:为|是|包括)',part):
                        continue
                    if not re.search('创新药|改良型新药|首创新药',part) or not re.search('上市前|研发|研制',part):
                        continue
                    if not family or family.group() not in part or not re.search('反馈|意见|建议|咨询',part):
                        continue
                    if '纳入' in self.norm and not re.search('纳入(?:后|者)|纳入[^。；;]{0,12}(?:可|获得)',part):
                        continue
                    if re.search('另一(?:种|个)?(?:药|项目)|其他(?:药|项目)|上市后[^。；;]{0,15}(?:常规|日常)',part):
                        continue
                    definitions.append(self._quote(c,'当前具名反馈服务直接适用的创新研发对象及纳入后同一机会',(a,b)))
            if len(definitions)==1:
                options.append((definitions[0],boundary,names[0]))
        if len(options)!=1:
            return
        definition,boundary,name=options[0]
        self._add('named_mechanism',[definition,self._quote(current,'当前实际开放或限制同一研发反馈服务')],'当前实质服务行动连接同版同组件定义的纳入后创新研发对象，只补同一反馈机会，不读并行资格内容',relation_subtype='bounded_IF_explicit_feedback_access',affected_dimensions=['I'],only_IF_consumers=True,object_definition=definition['text'],direct_mechanism=self.text,research_stage=definition['text'],current_action_anchor=self.current_anchor(access.start(),service.end()),mechanism_name=name,version_binding={'established':True,'binding':'exact_same_source_component'},scope_boundary_context_id=boundary['context_id'],parallel_qualification_content_not_inherited=True)

    def _se_parent_binding(self, parent):
        """Finite current-parent scope; reused IDs in other components cannot bind."""
        primary = self.unit.get('source_ref', {})
        if parent.get('source_ref', {}).get('sha256') != primary.get('sha256'):
            return None
        pc, ok = self._se_geometry_value(parent, 'component_id')
        uc = primary.get('locator', {}).get('component_id')
        if not ok or (uc and pc and (uc != pc)):
            return None
        current = re.sub('\\s+', '', self.norm)
        candidates = self._se_current_geometry_contexts()
        target, ok = self._se_geometry_value(parent, 'target_paragraph_id')
        if not ok:
            return None
        valid = []
        for c in candidates:
            if not self._se_same_geometry(parent, c):
                continue
            cp, ok = self._se_geometry_value(c, 'paragraph_id')
            pp, ok2 = self._se_geometry_value(parent, 'paragraph_id')
            if not ok or not ok2 or (target and cp != target):
                continue
            span_geometry = self._se_parent_span_geometry(parent, c)
            if not span_geometry:
                continue
            for key in ('chapter_id', 'list_id'):
                a, ok = self._se_geometry_value(parent, key)
                b, ok2 = self._se_geometry_value(c, key)
                if not ok or not ok2 or (a is not None and b is not None and (a != b)):
                    break
            else:
                first = bool(re.match('^[（(]?一[）)、]|^1[.．、]', current))
                derived = bool(pp and cp and re.fullmatch(re.escape(pp) + '_item0*1', cp))
                if first and (not derived) and pp and cp and re.fullmatch('.+?\\d+', pp) and re.fullmatch('.+?\\d+', cp):
                    if not self._se_next_geometry(parent, c, check_spans=False):
                        continue
                valid.append((c, span_geometry))
        if not valid:
            return None
        return {'evidence_grade': 'supplied_local_parent_target' if target else 'supplied_local_parent_role', 'role_only_not_independent_source_verification': not bool(target), 'target_context_ids': [c['context_id'] for c, _ in valid], 'source_span_geometry': [g for _, g in valid]}

    def _se_bounded_content(self):
        """Exact current anaphor selects finite same-object sentence(s), not paragraph."""
        current = re.sub('\\s+', '', self.norm)
        tests = [('例如.{0,120}用药指导.{0,80}风险发现', '药物临床试验中的风险监测|风险管理计划.{0,35}提出相应控制策略', ['S'], 'same_drug_risk_control_example'), ('SOC.{0,70}(?:发生率|排序)', '(?:AE|ADR).{0,45}SOC|SOC.{0,45}(?:AE|ADR)', ['S'], 'same_classified_safety_event'), ('药品追溯.{0,50}(?:质量评估|继续使用|更换)', '严重不良反应.{0,60}(?:暂停使用|救治)', ['S'], 'same_drug_ADR_response'), ('根据实际情况.{0,40}(?:维持|退出).{0,20}(?:资格|试点)', '安全性事件.{0,20}(?:暂停|终止)', ['S'], 'current_eligibility_refers_to_reported_risk_event'), ('这些特殊指标|上述.{0,10}(?:安全性信息|风险|疗效指标|观察指标)|相同的观察指标', '(?:客观|主观)?疗效指标|(?:疗效|安全性)观察指标|评估药物.{0,20}(?:有效性|安全性)', ['S', 'E'], 'explicit_indicator_definition'), ('(?:协商|数据).{0,30}(?:一致|为准)|相关数据.{0,30}(?:科学性|及时性|准确性)', '基金实际支出.{0,20}分歧|(?:药品费用|医保基金支出).{0,40}相关数据', ['Ec'], 'same_cost_data_reference'), ('减轻受试者负担', '误工|收入损失|社会经济负担', ['Ec'], 'same_burden_explanation'), ('试验终点.{0,25}(?:呼应|需求)|说明试验药物.{0,25}需求', '(?:反映患者获益|预期带来的获益)指标|患者获益的临床终点', ['E'], 'same_endpoint_effect_content'), ('非最优.{0,20}对照', '有效性不确定|(?:安全性和/或有效性|疗效).{0,20}(?:不确定|替代)', ['E'], 'same_comparator_effect_limitation'), ('风险控制措施.{0,35}(?:预防|监测|治疗)', '如.{0,50}(?:给药方案|暂停用药|永久停药)', ['S'], 'same_drug_risk_control_example')]
        for c in self.contexts:
            raw = c.get('text', '')
            p = re.sub('\\s+', '', norm(raw))
            if c['kind'] != 'paragraph' or not raw or current not in p or (p == current) or (not self._se_same_geometry(self.unit, c)):
                continue
            current_component = self.unit.get('source_ref', {}).get('locator', {}).get('component_id')
            component = c.get('structure', {}).get('component_id') or c.get('source_ref', {}).get('locator', {}).get('component_id')
            if current_component and component and (current_component != component):
                continue
            for trigger, antecedent, dims, name in tests:
                if not re.search(trigger, current):
                    continue
                selected_dims = list(dims)
                indicator_qualifier = None
                if name == 'explicit_indicator_definition':
                    effect = bool(re.search('(?:上述|这些|相同).{0,10}疗效(?:观察)?指标', current))
                    safety = bool(re.search('(?:上述|这些|相同).{0,10}(?:安全性(?:观察)?指标|安全性信息|风险)', current))
                    if effect and (not safety):
                        indicator_qualifier = '疗效(?:观察)?指标|评估药物.{0,20}有效性'
                        selected_dims = ['E']
                    elif safety and (not effect):
                        indicator_qualifier = '安全性(?:观察)?指标|安全性信息|风险|评估药物.{0,20}安全性'
                        selected_dims = ['S']
                selected = []
                for a, b in sentence_spans(raw):
                    part = raw[a:b]
                    n = re.sub('\\s+', '', norm(part))
                    if not re.search(antecedent, n) or n == current:
                        continue
                    if indicator_qualifier and (not re.search(indicator_qualifier, n)):
                        continue
                    if re.search('另一(?:种|个)?(?:药|品种|项目)|其他(?:药|品种|项目)|另行|另一个', n) and (not re.search('另一|其他|另行|另一个', current)):
                        continue
                    pos = p.find(current)
                    ante = p.find(n)
                    if name == 'explicit_indicator_definition' and '上述' in current and (ante >= pos):
                        continue
                    between = p[min(pos, ante):max(pos, ante)]
                    if re.search('另一(?:种|个)?(?:药|品种|项目)|其他(?:药|品种|项目)|另一个', between) and (not re.search('另一|其他|另一个', current)):
                        continue
                    selected.append((a, b))
                if selected:
                    qs = [self._quote(c, '当前明确指代的同对象有限定义/原因/例证', span) for span in selected]
                    self._add('parent_predicate', qs, '只消费当前确指的有限句段；不把整个同段内容并入当前', relation_subtype='SE_' + name, affected_dimensions=selected_dims, shared_predicate='。'.join((raw[a:b] for a, b in selected)), member_text=self.text, not_whole_source_inheritance=True, selected_raw_spans=selected)
        if re.match('例如', current) and re.search('药物模型|模型引导', current) and re.search('确定合理的用法用量|制定合理剂量', current):
            for c in self.contexts:
                raw = c.get('text', '')
                binding = self._se_preceding_binding(c) if c['kind'] == 'preceding_paragraph' else None
                if binding and re.search('给药剂量.{0,120}剂量[-—]暴露量[-—]效应\\(安全性/疗效\\).{0,20}确定', norm(raw)):
                    self._add('parent_predicate', [self._quote(c, '当前例如确指的剂量—暴露—安全性/疗效定义')], '当前合理剂量模型明确承接给药—效应定义', relation_subtype='SE_explicit_dose_model_example', affected_dimensions=['S', 'E'], shared_predicate=raw, member_text=self.text, preceding_scope_binding=binding)

    def _se_group_proof(self, container, contexts):
        """Validate supplied ordered scope and its actual next boundary."""
        if not contexts or any((not c or not c.get('text') for c in contexts)):
            return None
        ids = [c['context_id'] for c in contexts]
        if len(ids) != len(set(ids)):
            return None
        sequence_values = [self._se_geometry_value(c, 'sequence_index') for c in contexts]
        if any((not ok for _, ok in sequence_values)):
            return None
        sequences = [value for value, _ in sequence_values]
        if any((type(i) is not int for i in sequences)) or sequences != list(range(sequences[0], sequences[0] + len(sequences))):
            return None
        sha = contexts[0]['source_ref']['sha256']
        if any((not self._se_same_geometry(contexts[0], c) for c in contexts)):
            return None
        if not self._se_same_geometry(contexts[0], container):
            return None
        st = container.get('structure', {})
        boundary_ids = [i for g in st.get('child_groups', []) if g.get('position') == 'structure_boundary' for i in g.get('ordered_context_ids', [])]
        for bid in boundary_ids:
            boundary = self.by_id.get(bid)
            if not boundary or boundary['kind'] != 'boundary_container' or (not self._se_same_geometry(contexts[0], boundary)):
                continue
            bst = boundary.get('structure', {})
            if bst.get('parent_context_id') != container['context_id']:
                continue
            first = bst.get('first_paragraph', bst.get('first_paragraph_id'))
            last = bst.get('last_paragraph', bst.get('last_paragraph_id'))
            if not first or not last:
                continue

            def pid(c):
                value, ok = self._se_geometry_value(c, 'paragraph_id')
                return value if ok else None
            if pid(contexts[0]) != first or pid(contexts[-1]) != last:
                continue
            nextid = bst.get('next_paragraph_id')
            text_ids = bst.get('text_child_context_ids', []) + [i for g in bst.get('child_groups', []) if g.get('position') in ('next_boundary', 'contexts') for i in g.get('ordered_context_ids', [])]
            qs = []
            for cid in text_ids:
                c = self.by_id.get(cid)
                if not c or not c.get('text') or c['source_ref']['sha256'] != sha or (not same_component(contexts[0], c)):
                    continue
                if not nextid or pid(c) != nextid or cid in ids:
                    continue
                adjacency = self._se_next_geometry(contexts[-1], c)
                if not adjacency:
                    continue
                q = self._quote(c, '确指范围的原件下一段边界，仅验证闭合而不消费内容')
                qs.append(q)
            if qs:
                return {'boundary_quotes': qs, 'container_id': container['context_id'], 'first_paragraph': first, 'last_paragraph': last, 'next_paragraph': nextid, 'source_sha256': sha, 'adjacency_geometry': adjacency}
        return None

    def _se_geometry_value(self, c, key):
        """Use supplied geometry without silently preferring conflicting fields."""
        st = c.get('structure', {})
        loc = c.get('source_ref', {}).get('locator', {})
        a = st.get(key)
        b = loc.get(key)
        if a is not None and b is not None and (a != b):
            return (None, False)
        return (a if a is not None else b, True)

    def _se_same_geometry(self, left, right):
        if left.get('source_ref', {}).get('sha256') != right.get('source_ref', {}).get('sha256'):
            return False
        for key in ('component_id',):
            a, ok = self._se_geometry_value(left, key)
            b, ok2 = self._se_geometry_value(right, key)
            if not ok or not ok2 or (a is not None and b is not None and (a != b)):
                return False
        return True

    def _se_current_geometry_contexts(self):
        current = re.sub('\\s+', '', self.norm)
        loc = self.unit.get('source_ref', {}).get('locator', {})
        ids = loc.get('paragraph_ids') or ([loc['paragraph_id']] if loc.get('paragraph_id') else [])
        out = []
        for c in self.contexts:
            if c['kind'] != 'paragraph' or current not in re.sub('\\s+', '', norm(c.get('text', ''))):
                continue
            if not self._se_same_geometry(self.unit, c):
                continue
            pid, ok = self._se_geometry_value(c, 'paragraph_id')
            if not ok or (ids and pid and (pid not in ids)):
                continue
            out.append(c)
        return out

    def _se_complete_lists(self):
        current = re.sub('\\s+', '', self.norm)
        if not re.search('下列|以下|同时满足|情况之一', current):
            return
        substantial = re.search('(?:符合|满足|具备).{0,45}(?:可以|可|方可|不得|不予).{0,20}(?:申请|申报|续约|支付|纳入)|(?:有|具有)(?:下列|以下).{0,35}(?:调出|注销|终止)|(?:应|须|要求).{0,20}(?:评价|核验|提供|说明|撰写).{0,20}(?:内容|信息|证据|数据)', current)
        if not substantial:
            return
        options = []
        for container in self.contexts:
            if container['kind'] not in ('ordered_list', 'supplemental_group'):
                continue
            ids = [i for g in container.get('structure', {}).get('child_groups', []) if g.get('position') in ('contexts', 'members', 'ordered_members') for i in g.get('ordered_context_ids', [])]
            group = [self.by_id.get(i) for i in ids]
            if not group or not group[0] or group[0]['source_ref']['sha256'] != self.unit.get('source_ref', {}).get('sha256') or (re.sub('\\s+', '', norm(group[0].get('text', ''))) != current):
                continue
            proof = self._se_group_proof(container, group)
            if proof:
                options.append((group, proof))
        unique = {tuple((c['text'] for c in group)): (group, proof) for group, proof in options}
        if len(unique) == 1:
            group, proof = next(iter(unique.values()))
            self._add('substantive_list', [self._quote(c, '当前实质总领确指的完整成员') for c in group[1:]] + proof['boundary_quotes'], '当前条件/实质要求按结构核见首末成员和同源下一段，闭合边界不捐献标签', relation_subtype='SE_closed_substantive_members', affected_dimensions=['S', 'E', 'Ec'], SE_scope_verified=True, closure_proof=proof, shared_predicate=self.text, full_scope=True)
        else:
            self.material_requests.append({'path': 'substantive_list', 'reference': self.text, 'missing': '原包确指组的成员/首末范围/同源下一段未唯一闭合；不能用连续编号或句号替代完整证明', 'dimensions': ['S', 'E', 'Ec']})

    def _se_direct_content_parents(self):
        current_paragraphs = {c.get('structure', {}).get('paragraph_id') for c in self.contexts if c['kind'] == 'paragraph' and re.sub('\\s+', '', self.norm) in re.sub('\\s+', '', norm(c.get('text', '')))}
        primary = self.unit.get('source_ref', {}).get('sha256')
        for c in self.contexts:
            raw = c.get('text', '')
            st = c.get('structure', {})
            if c['kind'] != 'parent_paragraph' or c.get('source_ref', {}).get('sha256') != primary:
                continue
            binding = self._se_parent_binding(c)
            if not binding:
                continue
            target = st.get('target_paragraph_id')
            if target and target not in current_paragraphs:
                continue
            if re.search('(?:撰写|整理|汇总|分析|核验|提供).{0,30}安全性(?:内容|信息|数据|证据)', norm(raw)) and target:
                self._add('parent_predicate', [self._quote(c, '结构直接指向当前成员的实质安全性数据整理谓词')], '直接内容父谓词限定当前人群/数据成员，不继承一般宗旨', relation_subtype='SE_direct_safety_content_member', affected_dimensions=['S'], shared_predicate=raw, member_text=self.text, parent_scope_binding=binding)
            if re.search('(?:费用|药费).{0,50}(?:符合|满足).{0,20}(?:下列|以下).{0,40}(?:基金支付|报销)', norm(raw)):
                self._add('parent_predicate', [self._quote(c, '直接费用—支付条件父谓词')], '当前成员限定被直接支付父句指向的费用/支付资格，不取兄弟内容', relation_subtype='SE_direct_payment_condition_member', affected_dimensions=['Ec'], shared_predicate=raw, member_text=self.text, parent_scope_binding=binding)
        if re.search('就药品测算评估的(?:思路|重点)', self.norm):
            for c in self.contexts:
                raw = c.get('text', '')
                binding = self._se_preceding_binding(c) if c['kind'] == 'preceding_paragraph' else None
                if binding and re.search('开展测算评估', norm(raw)) and re.search('基金测算|药物经济学', norm(raw)) and re.search('(?:提出|确定).{0,30}医保支付标准.{0,15}评估意见', norm(raw)) and (not re.search('其他药品|另一药品', norm(raw))):
                    self._add('parent_predicate', [self._quote(c, '当前同一测算评估思路的紧邻实质费用/支付定义')], '当前就同一测算评估内容交流承接已给经济方法及支付标准意见，不从阶段标题继承', relation_subtype='SE_price_evaluation_method_reference', affected_dimensions=['Ec'], shared_predicate=raw, member_text=self.text, preceding_scope_binding=binding)
