"""Candidate-only generic interface repair after fixed controls and audit receipt."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
assert (P/'control-pre-edit-seal.json').exists() and (P/'independent20-reception-bindings.json').exists()
def replace_function(path,name,new):
 text=path.read_text();tree=ast.parse(text);nodes=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name];assert len(nodes)==1
 n=nodes[0];lines=text.splitlines(keepends=True);path.write_text(''.join(lines[:n.lineno-1])+new.rstrip()+'\n\n'+''.join(lines[n.end_lineno:]))
def add_before(path,marker,new):
 text=path.read_text();assert text.count(marker)==1;path.write_text(text.replace(marker,new.rstrip()+'\n\n'+marker))
D=P/'dimensions.py';R=P/'relations.py'
add_before(D,'def _form_only(','''def _document_name_only(text: str, dimension: str) -> bool:
    """Identify the named-file role, not negation of a drug property.

    An independent substantive clause survives. Denial of inference from a
    filename is not an evaluation request and cannot donate its action verb.
    """
    if not re.search('文件名|附件名|文件名称|附件名称|栏目[^。；;]{0,20}(?:名称|文件名)|标题', text):
        return False
    content = text
    for match in reversed(list(re.finditer('《[^》]+》|“[^”]+”|"[^"]+"', text))):
        before = text[max(0, match.start()-24):match.start()]
        if re.search('(?:文件|附件|材料)?(?:名称|文件名|附件名|标题)(?:为|是|[:：])?$', before):
            content = content[:match.start()] + ' ' + content[match.end():]
    candidates = []
    for part in re.findall('[^，,。；;]+', content):
        if not re.search(TOPICS[dimension], part):
            continue
        nominal = re.search('(?:仅|只)(?:用作|作为|用于)[^。；;]{0,20}(?:文件名|附件名|标题)|(?:文件|附件|材料)?(?:名称|文件名|附件名|标题)(?:为|是|[:：])', part)
        denied_inference = re.search('(?:不据|不从|不得[^。；;]{0,6}从|不能[^。；;]{0,6}从)[^。；;]{0,20}(?:名称|文件名|附件名|标题)[^。；;]{0,12}(?:推定|推断|认定|判断)', part)
        if not (nominal or denied_inference):
            candidates.append(part)
    return bool(re.search(TOPICS[dimension], text)) and not candidates
''')
t=D.read_text();needle="def _form_only(text: str, dimension: str) -> bool:\n";assert needle in t;t=t.replace(needle,needle+"    if _document_name_only(text, dimension):\n        return True\n",1);D.write_text(t)
add_before(D,'def _innovation(acc:', '''def _current_RND_support(unit: Unit):
    """Current beneficiary/action/service or explicit comparative convenience.

    No object is taken from programme roles here. Numbers do not establish
    acceleration, and a later different beneficiary blocks the connection.
    """
    if unit.kind != 'current' or _administrative_innovation_owner(unit.text):
        return None
    text = unit.text
    object_match = re.search(INNOVATION_OBJECT + '[^。；;，,]{0,15}(?:研发|研制)(?:项目|工作|活动)?', text)
    if not object_match:
        return None
    before = text[:object_match.start()]
    subject = re.search('项目|工作|活动$', object_match.group())
    beneficiary = re.search('(?:为|向|对|针对)[^。；;]{0,25}$', before)
    if not (subject or beneficiary):
        return None
    service = re.search('(?:研究|试验|研发)(?:方案|设计|技术|项目)?[^。；;，,]{0,12}(?:反馈|意见|建议|咨询|指导|服务)', text[object_match.end():])
    operation = None
    if service:
        service_start = object_match.end()+service.start()
        operation = re.search('开放|提供|给予|安排|实施|设置|建立|允许[^。；;，,]{0,8}(?:使用|获得)|可(?:以)?获得|撤回|取消|终止|不再提供', text[object_match.end():service_start+1])
        if not operation:
            service = None
    convenience = re.search('(?:审评|审批)(?:时限|期限)[^。；;]{0,45}(?:缩短|减少)|(?:缩短|减少)[^。；;]{0,15}(?:审评|审批)(?:时限|期限)', text[object_match.end():])
    baseline = re.search('(?:相较|相比|比较|较|由)[^。；;]{0,20}(?:普通|常规|一般|现行)(?:程序|审评|审批)|(?:普通|常规|一般)程序[^。；;]{0,20}(?:相比|比较)', text[object_match.end():])
    if not service and not (convenience and baseline):
        return None
    selected = service or convenience
    end = object_match.end()+selected.end()
    if re.search('其他(?:药品|药物|项目)|另一(?:药品|药物|项目)|另一个(?:药品|药物|项目)', text[object_match.end():end]):
        return None
    return {'object':object_match.group(),'arrangement':selected.group(),'operation':operation.group() if operation else '当前相对普通程序明确缩短审评时限','connection':'current explicit same beneficiary and service/convenience; no parallel programme role inheritance','numeric_deadline_alone_not_sufficient':True}
''')
t=D.read_text();needle="    if unit.kind != 'named_mechanism':\n";start=t.index('def _innovation(acc:');position=t.index(needle,start)
t=t[:position]+"    direct_support = _current_RND_support(unit)\n    if direct_support:\n        acc.add('I', unit, 'I3_current_explicit_RND_support', '当前明确创新研发对象直接获得技术反馈服务，或相较普通程序缩短审评时限；对象—实际可用安排—直接联系均在当前，不借程序名称、数字或其他对象分支。', obj, {'I3_object': direct_support['object'], 'I3_arrangement': direct_support['arrangement'], 'I3_connection': direct_support['connection'], 'support_action': direct_support['operation'], 'numeric_deadline_alone_not_sufficient': True})\n"+t[position:]
needle="        if consumers == set(DIMENSIONS):\n            _generic(acc, unit, obj)\n";assert needle in t;t=t.replace(needle,"        _generic(acc, unit, obj)  # Each generic consumer independently intersects its typed permissions.\n",1);D.write_text(t)
t=R.read_text();needle='        self._se_operational_references()\n';assert t.count(needle)==1;t=t.replace(needle,'        operational_request_start = len(self.material_requests)\n'+needle+'        self._IF_closed_operational_content(self.material_requests[operational_request_start:])\n        self._IF_named_feedback_access()\n',1);R.write_text(t)
add_before(R,'    def _se_parent_binding(','''    def _IF_closed_operational_content(self, operational_requests):
        """Reuse neutral closure only for exact current substantive standards.

        SE producer permissions stay intact. A separate I/F relation consumes
        the same proven selected article/clause; boundary siblings do not enter.
        Missing references route to I/F separately without clearing any stops.
        """
        for relation in list(self.linked('cited_standard')):
            details = relation.get('details') or {}
            if details.get('relation_subtype') not in {'SE_closed_explicit_article_condition', 'SE_closed_explicit_section'} or not details.get('SE_scope_verified'):
                continue
            shared = {key:value for key,value in details.items() if key not in {'affected_dimensions','only_IF_consumers','relation_subtype'}}
            shared.update(relation_subtype='IF_closed_operational_content', affected_dimensions=['I','F'], only_IF_consumers=True, neutral_closure_reused_from=details['relation_subtype'], scope_is_not_dimension_label=True)
            evidence = relation.get('context_evidence') or []
            self._add('cited_standard', evidence, '当前明确要求同版确指实质标准；复用已经核明的同源有界条/款证明，仅把实际内容交I/F消费者逐维检查，闭合不赋标签', **shared)
            reference = ('第'+str(details['reference_article'])+'条'+('第'+str(details['reference_clause'])+'款' if details.get('reference_clause') is not None else '')) if 'reference_article' in details else '当前同版确指章节实质标准'
            self.source_requests.append({'path':'cited_standard','reference':reference,'current_text':self.text,'dependency_status':'resolved','resolution_path':'neutral_closed_operational_content_IF_consumer','affected_dimensions':['I','F'],'closure_proof':details.get('closure_proof'),'reference_article':details.get('reference_article'),'reference_clause':details.get('reference_clause'),'evidence':evidence,'no_new_material':True,'other_unresolved_requests_retained':True})
        for original in operational_requests:
            if original.get('path') != 'cited_standard':
                continue
            request = dict(original)
            request.pop('affected_dimensions', None)
            request.update(dimensions=['I','F'], original_operational_request_consumers=list(original.get('dimensions', [])), stop_scope='exact current operative reference; no absence-as-zero', dependency_status='stopped')
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
        access = re.search('开放|提供|实施|可(?:以)?获得|允许[^。；;]{0,10}使用|不再提供|撤回|终止', self.norm)
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
            if not any(norm(c['text'])==self.norm and self._se_same_geometry(c,current) for c in members):
                continue
            if st.get('follows_context_id') != ids[-1] or not self._se_next_geometry(members[-1],boundary):
                continue
            if any(not self._se_next_geometry(a,b) for a,b in zip(members,members[1:])):
                continue
            containers = [c for c in self.contexts if c['kind']=='source_paragraph' and not c.get('text') and c.get('structure',{}).get('first_paragraph')==st.get('component_first_paragraph') and c.get('structure',{}).get('last_paragraph')==st.get('component_last_paragraph') and c.get('source_ref',{}).get('sha256')==primary and same_component(c,current)]
            if len(containers)!=1:
                continue
            names=[norm(c['text']) for c in members if re.fullmatch(PROGRAM,norm(c['text']))]
            names=[name for name in names if name in self.norm]
            if len(set(names))!=1:
                continue
            definitions=[]
            family=re.search('研究方案|试验方案|研发技术|研究设计|试验设计',service.group())
            for c in members:
                for a,b in sentence_spans(c['text']):
                    part=norm(c['text'][a:b])
                    if not re.search('(?:本|该)(?:计划|程序|通道)(?:仅)?(?:面向|适用于)|适用(?:对象|范围)[^。；;]{0,20}(?:为|是|包括)',part):
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
''')
for path in [D,R]:ast.parse(path.read_text())
print('Candidate modules edited; baseline and controls retained.')
