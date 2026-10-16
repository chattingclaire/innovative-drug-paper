"""Bounded source relations. No record identity, outcome, or corpus access.

The source graph supplies positions and original text. Relations are computed here;
they are not dimension permissions. Classification remains in dimensions.py.
"""
import re
from evidence import matching_view, raw_span, anchor, context_anchor

OBJECT = r'药品|药物|新药|本药|该药|研究药|试验药|用药|疗效|患者|治疗|制剂|片剂|剂型|研发|生物制品|中药'
INTRO = r'下列|以下|同时满足|条件之一|具体包括'
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


class RelationView:
    def __init__(self, unit):
        if 'id' in unit or 'labels' in unit or 'decisions' in unit:
            raise ValueError('semantic view must not contain administrative identity/results')
        self.unit = unit
        self.text = unit['text']
        self.norm, self.offsets = matching_view(self.text)
        self.contexts = unit.get('contexts', [])
        self.by_id = {c['context_id']: c for c in self.contexts}
        self.material_requests = []
        self.relations = []
        self._parents()
        self._local_operations()
        self._lists()
        self._standards()
        self._operative_references()
        self._mechanisms()
        self._explanations()
        self._anaphors()
        self._applicable_support()
        self._resource_definitions()
        self._tables()

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
        self.relations.append({'kind': kind, 'current_anchor': self.proposition(),
                               'context_evidence': evidence, 'details': d,
                               '_signature': signature})

    def traces(self):
        return [{k: v for k, v in r.items() if k != '_signature'} for r in self.relations]

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

    def _standards(self):
        operative = re.search(r'(?:审核|核验|满足|符合|不符合).{0,20}(?:条件|资格|标准)|(?:条件|资格).{0,25}(?:审核|终止|取消)', self.norm)
        consequence = re.search(r'应当|可以|可申请|予以|终止|取消|限制|维持|授予', self.norm)
        if not operative or not consequence:
            return
        programs = re.findall(PROGRAM, self.norm)
        candidates = []
        # A structural relationship is required for an unnamed standard reference.
        related = set()
        for c in self.contexts:
            if c['kind'] == 'structural_relation':
                related.update(c.get('structure', {}).get('related_context_ids', []))
        for c in self.contexts:
            t = norm(c.get('text', ''))
            if c['kind'] != 'source_paragraph' or not t:
                continue
            shared = [p for p in programs if p in t]
            # Chinese leading particles may attach to the regex title; use suffix
            # intersection for program names, never record ID or normalized hash.
            if not shared:
                for p in programs:
                    for size in range(len(p), 5, -1):
                        if p[-size:] in t:
                            shared.append(p[-size:]); break
            if shared and c['context_id'] in related and re.search(r'用于|符合|条件|申请|适用', t):
                candidates.append(c)
        if candidates:
            self._add('cited_standard', [self._quote(c, '同源操作性标准的完整原文') for c in candidates],
                      '当前以标准核验/资格决定制度适用或终止；并列分支完整保留',
                      standard_text='\n'.join(c['text'] for c in candidates),
                      action_scope='standard_review_or_eligibility_consequence')
        elif re.search(r'(?:上述|该|纳入)(?:实质)?(?:条件|标准)', self.norm):
            self.material_requests.append({'path': 'cited_standard', 'reference': self.text,
                                           'missing': '确指资格/标准与待遇后果的同版标准原文缺失'})

    def _version(self, c, action_text=None):
        meta = c.get('source_ref', {}).get('metadata', {})
        date = meta.get('document_date') or meta.get('source_date') or meta.get('policy_document_date')
        current_years = re.findall(r'(?:19|20)\d{2}年', self.norm if action_text is None else action_text)
        source_year = date[:4] if date else None
        if current_years and (not source_year or any(y[:4] != source_year for y in current_years)):
            return {'established': False, 'current_years': current_years, 'source_date': date}
        return {'established': bool(date), 'current_years': current_years, 'source_date': date,
                'binding': 'explicit_historical_year' if current_years else 'provided_same_version_source'}

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
        return candidates

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
            if clause and re.search(r'该药品|本药品|该药物|本药物', selected[0][2]):
                preceding = members[clause - 2] if clause > 1 else None
                if (preceding is None or not re.search(OBJECT, preceding[2])
                        or re.search(r'(?:另一|其他|另外|另一个).{0,8}(?:药品|药物)', preceding[2])):
                    self.material_requests.append({'path': 'cited_standard', 'reference': reference.group(),
                        'missing': '被援引款的药品指代缺少同条紧邻对象及完整限定条件'})
                    continue
                antecedents.append(preceding)
                evidence.append(self._quote(preceding[0], '被援引款的同条紧邻药品对象及完整限定条件', preceding[1]))
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
                            or not re.search(r'保护范围|相应.{0,6}数据|受保护.{0,6}数据', part)):
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
                    scope = [item for item in donor_members if re.search(
                        r'(?:本条(?:款)?|该条(?:款)?).{0,20}(?:数据保护范围|保护范围)', item[2])
                        and re.search(r'包括|限于|涵盖|仅保护|不包括', item[2])
                        and re.search(r'范围[^。]*(?:数据|证据|试验|研究|安全性|有效性|疗效|临床优势)', item[2])]
                    permissions = [item for item in donor_members if re.search(r'在数据保护期内', item[2])
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
                action_scope='explicit_article_condition_substantive_consequence',
                current_condition_anchor=self.current_anchor(start, reference.end()),
                current_consequence_anchor=self.current_anchor(consequence_start, reference.end() + consequence.end()),
                reference_chain=chain, reference_container_ids=[step['container_context_id'] for step in chain],
                object_definition='\n'.join(item[0].get('text', '')[item[1][0]:item[1][1]] for item in antecedents),
                qualification_text='\n'.join(e['text'] for e in evidence if e not in permission_evidence),
                qualification_context_evidence=[e for e in evidence if e not in permission_evidence],
                treatment_context_evidence=permission_evidence,
                standard_text='\n'.join(e['text'] for e in evidence), unexpanded_references=unexpanded,
                bounded_reference_depth=2)

    def _applicable_support(self):
        current = self._current_source()
        if current is None or not re.search(r'(?:创新|改良)(?:型)?药(?:品|物)?', self.norm):
            return
        arrangement = re.search(r'(?:本|该)(?:工作规范|办法|规程|程序|方案|安排)', self.norm)
        authorization = re.search(r'(?:不再|不得|不能|可以|可|准许|允许)[^。；;]{0,45}(?:适用|使用|按照|依据)', self.norm)
        early_stage = re.search(r'临床试验[^。；;]{0,18}(?:完成前|结束前)|上市前|申报前|申请前|研发阶段|提前', self.norm)
        if not arrangement or not authorization or not early_stage or authorization.end() > arrangement.start():
            return
        arrangement_reference = rf'(?:本|该){re.escape(arrangement.group()[1:])}'
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
                   or not same_component(c, current) for c in members):
                continue
            if not any(norm(c.get('text', '')) == self.norm for c in members):
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
                if re.search(r'适用范围', part) and re.search(r'创新|改良', part):
                    objects.append(self._quote(c, '同一规范有界组件的对象及排除范围', (a, b)))
                if (re.search(arrangement_reference, part) and re.search(r'研发阶段|临床试验.{0,35}完成后|上市前|申报前', part)
                        and norm(raw) != self.norm):
                    stages.append(self._quote(c, '同一规范通常适用的上市前研究阶段', (a, b)))
                if (re.search(r'沟通交流(?:时限|期限).{0,16}\d+(?:个)?(?:工作)?(?:日|天)', part)
                        or re.search(r'(?:品种)?审评(?:时限|期限).{0,45}(?:优先审评|单独序列|\d+(?:个)?(?:工作)?(?:日|天))', part)
                        or re.search(r'(?:提供|可申请|获得).{0,18}(?:研究方案反馈|试验方案反馈|研发技术咨询|技术服务)', part)):
                    if not re.search(r'(?:不提供|不开展|仅提供).{0,20}(?:电话|视频|渠道|一般资料)', part):
                        supports.append(self._quote(c, '当前提前适用直接开放的同规范办理便利/技术支持', (a, b)))
        if not objects or not stages or not supports:
            self.material_requests.append({'path': 'named_mechanism', 'reference': arrangement.group(),
                'missing': '同源规范有界组件缺少创新对象、通常研发阶段或实际可用支持机制原文'})
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
            if c['kind'] != 'external_source' or not c.get('text'):
                continue
            meta = c.get('source_ref', {}).get('metadata', {})
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
        explanations = [c for c in self.contexts if c['kind'] == 'external_source'
                        and '解读' in c.get('source_ref', {}).get('metadata', {}).get('source_document_kind', '')]
        if not explanations or not re.search(r'建设|优化|建立|完善|保障|改进', self.norm):
            return
        # Measures must literally map to current phrases, not merely share topic.
        features = re.findall(r'(?:偏远地区|县域中心药房|上下.{0,5}用药衔接|基层药品配送)', self.norm)
        groups = {}
        for c in explanations:
            meta = c.get('source_ref', {}).get('metadata', {})
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
