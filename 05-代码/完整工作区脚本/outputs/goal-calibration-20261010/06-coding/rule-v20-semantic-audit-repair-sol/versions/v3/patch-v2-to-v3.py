from pathlib import Path
p=Path(__file__).resolve().parent
r=(p/'relations.py').read_text();d=(p/'dimensions.py').read_text()
def change(s,a,b):
 if a not in s:raise ValueError('old fragment absent: '+a[:100])
 return s.replace(a,b,1)
# Complete actually delivered qualification seeds can be recognized from the
# literal original, without synthesizing structural metadata or new materials.
r=change(r,"if shared and c['context_id'] in related and re.search(r'用于|符合|条件|申请|适用', t):\n                candidates.append(c)","""if shared and re.search(r'用于|符合|条件|申请|适用', t):
                supplied_seed = c['context_id'] in related
                literal_seed = False
                if (not supplied_seed and c.get('source_ref', {}).get('sha256') == self.unit.get('source_ref', {}).get('sha256')
                        and re.search(r'(?:申请适用|申请纳入).{0,35}(?:程序|计划|通道|试点).{0,20}(?:药品|药物).{0,25}(?:以下|下列).{0,12}条件', t)):
                    for name in shared:
                        closed = self._closed_primary_programme(name)
                        if closed:
                            lo,hi = closed['programme_span']
                            block = norm(closed['raw'][lo:hi])
                            if len(re.findall(re.escape(t),block)) == 1:
                                literal_seed = True
                if supplied_seed or literal_seed:
                    candidates.append(c)""")
r=change(r,"normative = re.search(r'应当|应予|必须|可以|可申请|予以', self.norm)","normative = re.search(r'应当|应予|应(?=核验|审核|终止|取消|撤回)|必须|可以|可申请|予以', self.norm)")
r=change(r,"action = re.search(r'终止|取消|限制|维持|授予|申请适用|审核.{0,12}资格|资格.{0,12}审核', self.norm)","action = re.search(r'终止|取消|撤回|限制|维持|授予|申请适用|(?:核验|审核).{0,35}(?:资格|纳入条件|适用条件)|资格.{0,12}(?:核验|审核)', self.norm)")
# Current direct service recognizer and finite role matching are independent of
# arrangement names. Exact primary programme closure requires the current norm.
r=change(r,"        text = self.norm\n        ordinary_duty", """        text = self.norm
        # Current postmarketing routine duties cannot consume premarketing
        # research services merely because the programme name is shared.
        if (re.search(r'上市后[^。；;]{0,18}(?:常规|日常|例行)[^。；;]{0,25}(?:监测|会议|填表|资料)',text)
                and not re.search(r'(?:进一步|继续|后续|服务于)[^。；;]{0,25}(?:创新|改良)?(?:研发|研制)',text)):
            return
        current_service = re.search(r'(?:药审中心|审评中心|审评团队|技术团队)[^。；;]{0,65}(?:提供|反馈|安排|不再提供)[^。；;]{0,45}(?:研究方案(?:反馈|意见|建议)?|试验方案(?:反馈|意见|建议)?|技术沟通|技术咨询|研究反馈)|(?:优先)?安排[^。；;]{0,20}技术沟通[^。；;]{0,30}(?:反馈|研究方案)',text)
        current_classes = set(re.findall(r'([\\u4e00-\\u9fff]{1,8}类)项目',text))
        def same_service_branch(part):
            classes = set(re.findall(r'([\\u4e00-\\u9fff]{1,8}类)项目',part))
            if current_classes and classes and not current_classes.intersection(classes):
                return False
            if re.search(r'上市后',text) and re.search(r'上市前|申报前',part):
                return False
            return True
        ordinary_duty""")
r=change(r,"if not operation or re.search(r'鼓励", "if not (operation or current_service) or re.search(r'鼓励")
r=change(r,"        if not actual:\n            return\n        current =", "        if not (actual or current_service):\n            return\n        if operation is None:operation = current_service\n        current =")
r=change(r,"closed = self._closed_primary_programme(name, require_current=False)","closed = self._closed_primary_programme(name, require_current=True)")
# Split explicitly distinct semicolon object branches, preserving original raw
# coordinates. The whole programme is never one undifferentiated role bucket.
r=change(r,"        for closure,items in sources:\n            objects=[]", """        for closure,items in sources:
            branch_items=[]
            for c,span in items:
                raw=c.get('text','');a,b=span or (0,len(raw))
                for m in re.finditer(r'[^；;]+(?:[；;]|$)',raw[a:b]):
                    branch_items.append((c,(a+m.start(),a+m.end())))
            items=branch_items
            objects=[]""")
r=change(r,"                list_member=(qualified_list and re.match(r'[（(][一二三四五六七八九十]+[）)]',part)\n                             and not re.search(r'不适用|不得|不再接受',part))", """                list_member=(qualified_list and (re.match(r'[（(][一二三四五六七八九十]+[）)]',part)
                             or re.search(r'[\\u4e00-\\u9fff]{1,8}类项目为',part))
                             and not re.search(r'不适用|不得|不再接受',part))
                if not same_service_branch(part):
                    continue""")
r=change(r,"                if re.search(r'境内[^。；;]{0,15}尚无药物获批|(?:尚无|没有)有效(?:防治|治疗)(?:手段|药物)|临床急需.{0,12}短缺药品',part):", "                if (object_scope or list_member) and re.search(r'境内[^。；;]{0,15}尚无药物获批|(?:尚无|没有)有效(?:防治|治疗)(?:手段|药物)|临床急需.{0,12}短缺药品',part):")
r=change(r,"            if direct_current:\n                services.append", "            if current_service:\n                direct_current=current_service\n                # This service is the current operation itself; a different\n                # object or phase's convenience is not copied into it.\n                services=[]\n                if re.search(r'研发|研制|临床试验|上市前|申报前|研究方案|试验方案',text):\n                    stages=[self._quote(current,'当前实际技术服务的研发内容/阶段')]\n            if direct_current:\n                services.append")
r=change(r,"                          source_closure=closure,version_binding", "                          selected_current_object_branches=sorted(current_classes),\n                          role_scope='current service and matching applicability branches; no other stage or object',\n                          source_closure=closure,version_binding")
# The exact current research-document referent, rather than an incidental alias
# anywhere in a parent, must be the unresolved technical question's subject.
r=change(r,"or not definition or definition.group('name')not in norm(container.get('text',''))", "or not definition or not re.search(re.escape(definition.group('name'))+r'[^。；;，,]{0,15}(?:未能阐明|未涵盖|未解决)',self.norm)")
# Origin conflicts override local role metadata. Missing origin coordinates do
# not raise the frozen input threshold; their relation is explicitly role-only.
a=r.index('    def _bounded_IF_first_member(self):');b=r.index('    def _bounded_IF_missing_dependency(self):',a)
r=r[:a]+'''    def _IF_local_parent_geometry(self, parent, current):
        def field(c,key):
            return c.get('structure',{}).get(key,c.get('source_ref',{}).get('locator',{}).get(key))
        for key in ('component_id','chapter_id','section_id','list_id','parent_context_id'):
            left,right=field(parent,key),field(current,key)
            if left is not None and right is not None and left!=right:
                return {'status':'conflict','reason':'different '+key}
        bounds=[]
        for c in (parent,current):
            interval=field(c,'unicode_code_point_interval_half_open')
            bounds.append(interval if isinstance(interval,list) and len(interval)==2 and all(type(v)is int for v in interval) else None)
        if all(bounds):
            gap=bounds[1][0]-bounds[0][1]
            if not 0<=gap<=4:
                return {'status':'conflict','reason':'original character intervals not local preceding','origin_gap':gap,'intervals':bounds}
            return {'status':'verified_origin_coordinates','origin_gap':gap,'intervals':bounds}
        left,right=field(parent,'sequence_index'),field(current,'sequence_index')
        if type(left)is int and type(right)is int:
            if right!=left+1:return {'status':'conflict','reason':'nonadjacent ordered source sequence'}
            return {'status':'verified_supplied_order','sequence_indices':[left,right]}
        return {'status':'role_only','reason':'unique supplied local preceding role; original adjacency not independently proved'}

    def _bounded_IF_first_member(self):
        """Actual first member plus unique local operative parent, never siblings."""
        if not re.match(r'^\\s*[（(]一[）)]',self.norm):return
        current=self._current_source();primary=self.unit.get('source_ref',{}).get('sha256')
        if current is None or norm(current.get('text',''))!=self.norm:return
        previous=[c for c in self.contexts if c['kind']=='preceding_paragraph'
                  and c.get('source_ref',{}).get('sha256')==primary]
        if len(previous)!=1:return
        c=previous[0];part=norm(c.get('text',''))
        if (not part.endswith(':') or not re.search(r'符合(?:以下|下列)[^。；;]{0,20}(?:情形|条件)[^。；;]{0,15}药品',part)
                or not re.search(r'(?:可以|可|允许)[^。；;]{0,10}申请[^。；;]{0,20}(?:批准|准入|待遇|支持)',part)):
            return
        geometry=self._IF_local_parent_geometry(c,current)
        if geometry['status']=='conflict':
            request={'path':'parent_predicate','reference':self.text,'current_text':self.text,
                     'missing':'接口preceding角色与原定位冲突；第一项实际操作性父谓词须核明',
                     'stop_reason':'local_parent_origin_conflict','dependency_status':'stopped',
                     'origin_conflict':geometry,'affected_dimensions':['F'] if re.search(r'尚无|没有|短缺',self.norm) and not re.search(r'创新|改良|新作用机制',self.norm) else ['I','F']}
            self.material_requests.append(request);self.source_requests.append(request.copy())
            return
        self._add('parent_predicate',[self._quote(c,'第一项直接承接的同源完整操作性父谓词')],
                  '实际第一项与唯一局部preceding且冒号闭合的完整申请父句组合；原定位冲突阻断，不展开兄弟或其他章节',
                  shared_predicate=c['text'],relation_subtype='bounded_IF_first_operative_member',
                  parent_binding_evidence_grade=geometry['status'],parent_geometry=geometry,
                  only_IF_consumers=True,affected_dimensions=['I','F'])

''' +r[b:]
r=change(r,"if (re.search(r'(?:不能满足|不符合)[^。；;]{0,25}(?:审评审批|审评|程序)[^。；;]{0,8}条件',self.norm)\n                and re.search(r'终止[^。；;]{0,30}(?:审评|程序)',self.norm)\n                and not any(r['details'].get('relation_subtype')=='bounded_IF_actual_support' for r in self.relations)):","""if (re.search(r'(?:不能满足|不符合|不满足)[^。；;]{0,35}(?:程序|计划|通道|试点)[^。；;]{0,12}(?:条件|资格)|(?:纳入|适用)(?:条件|资格)[^。；;]{0,20}不满足',self.norm)
                and re.search(r'(?:终止|取消|撤回|限制)[^。；;]{0,35}(?:审评|程序|研究方案|试验方案|反馈|支持|服务)',self.norm)
                and not any(r['kind']=='cited_standard' and r['details'].get('resolution_path')=='primary_literal_complete_operative_standard' for r in self.relations)
                and not any(r['details'].get('relation_subtype')=='bounded_IF_actual_support' for r in self.relations)):
""".rstrip())
# Restrict actual-right definitions to the current linked right branch; no
# another-product or another-right provision can supply innovative eligibility.
r=change(r,"            if (right in part and re.search(r'创新药|改良型新药|改良型药品',part) and re.search(r'给予|享受|实施保护|数据保护期|保护范围',part)):","""            if not same_component(c,current) if current else False:
                continue
            if re.search(r'另一(?:条|种|个)?|其他(?:药品|药物|创新药|保护)',part) and not re.search(r'创新药|改良型新药',self.norm):
                continue
            if (right in part and re.search(r'创新药|改良型新药|改良型药品',part) and re.search(r'给予|享受|实施保护|数据保护期|保护范围',part)):
""".rstrip())
# Only I/F-specific patterns and modifier ownership change in dimensions.
d=change(d,'OPPORTUNITY = r"','OPPORTUNITY = r"优先[^。；;，,]{0,15}(?:研究方案反馈|试验方案反馈|技术反馈|技术沟通|技术咨询)|')
d=change(d,'ACTUAL_ALLOCATION = r"','ACTUAL_ALLOCATION = r"(?:提供|不再提供|撤回|终止)[^。；;，,]{0,20}优先[^。；;，,]{0,20}(?:反馈|沟通|咨询)|')
d=change(d,'"no_domestic_approved_option": r"','"no_domestic_approved_option": r"境内[^。；;]{0,12}(?:尚无|没有)药物获批(?:用于|治疗)[^。；;]{0,15}(?:疾病|适应症)|')
insert='''def _administrative_innovation_owner(text):
    """Novelty of administrative organization is not drug technical content."""
    technical = re.search(r'新作用机制|新靶点|新化合物|新分子实体|实质改良|实质改进|(?:药品|药物|新药|制剂)(?:的)?(?:技术)?(?:新颖性|原创性|创新性)',text)
    if technical:return False
    return bool(re.search(r'(?:办公室|监管会议|排班|值班|会议流程|管理工作|组织方式)[^。；;]{0,45}(?:创新|新颖|原创)|(?:创新|新颖|原创)[^。；;]{0,25}(?:排班|会议|值班|管理工作|组织方式)',text))


'''
d=change(d,'def _innovation(acc: Accumulator, unit: Unit, obj: dict):',insert+'def _innovation(acc: Accumulator, unit: Unit, obj: dict):')
d=change(d,'if re.search(r"新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新", text) and _substantive(text, "I"):', 'if re.search(r"新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新", text) and _substantive(text, "I") and not _administrative_innovation_owner(text):')
d=change(d,'and not re.search(r"创新性[^。；;]{0,20}(?:系统性|工作)",text)):', 'and not re.search(r"创新性[^。；;]{0,20}(?:系统性|工作)",text) and not _administrative_innovation_owner(text)):')
d=change(d,'        if dim == "I" and re.search(r"创新性', '        if dim == "I" and _administrative_innovation_owner(text):\n            acc.exclude("I",unit,"创新性/新颖性修饰办公室组织、值班或管理工作；药品技术属性不是其内容对象。")\n            continue\n        if dim == "I" and re.search(r"创新性')
(p/'relations.py').write_text(r);(p/'dimensions.py').write_text(d)
print('v3 generic I/F repair written')
