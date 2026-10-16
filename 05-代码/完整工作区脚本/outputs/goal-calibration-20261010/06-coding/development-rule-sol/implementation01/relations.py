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


def norm(text):
    return matching_view(text)[0]


def sentence_spans(text):
    # Semicolons retain OR branches in the complete decision proposition.
    return [(m.start(), m.end()) for m in re.finditer(r'[^。\n]+(?:。|\n|$)', text)]


def title_key(title):
    # Generic title morphology; not a table of named programs or fixture texts.
    t = re.sub(r'[\W_]', '', norm(title))
    return re.sub(r'关于|改革|工作方案|工作规范|工作|试行|要求|通知|政策解读', '', t)


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
        self._lists()
        self._standards()
        self._mechanisms()
        self._explanations()
        self._anaphors()
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
        for c in self.contexts:
            st = c.get('structure', {})
            t = c.get('text', '')
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

    def object_evidence(self, a=0, b=None):
        b = len(self.norm) if b is None else b
        candidates = list(re.finditer(OBJECT, self.norm))
        if candidates:
            m = min(candidates, key=lambda m: abs(m.start() - a))
            return {'established': True, 'current_anchors': [self.current_anchor(m.start(), m.end())],
                    'context_evidence': [], 'object_text': m.group(), 'role': 'current_drug_or_treatment_object',
                    'reason': '当前完整命题直接表达药品、研发或患者治疗对象'}
        # Object clarification from direct parent / explicit scope only.
        for c in self.contexts:
            if c['kind'] not in ('parent_paragraph', 'heading'):
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
        return {'established': False, 'current_anchors': [], 'context_evidence': [],
                'object_text': '', 'role': None, 'reason': '当前及明确承接范围未建立药品/患者治疗对象'}
