from pathlib import Path
p=Path('outputs/goal-calibration-20261010/06-coding/rule-v20-semantic-audit-repair-sol/versions/v2/relations.py');t=p.read_text()
t=t.replace('        self._bounded_IF_table_qualification()\n','        self._bounded_IF_table_qualification()\n        self._bounded_IF_individual_consultation()\n        self._bounded_IF_first_member()\n        self._bounded_IF_missing_dependency()\n',1)
t=t.replace("(?:可|可以|允许|可申请|应当|应|决定|组织|设立|完成|保持|维持|退出|终止|撤回|不再|协助|商定)","(?:可|可以|允许|可申请|自愿申报|应当|应|决定|组织|设立|完成|保持|维持|退出|终止|撤回|不再|协助|商定|审评时限为)",1)
t=t.replace('(?:沟通交流|会议|临床试验|研究方案|试验方案|研究资料|提交计划|审评|试点项目资格|优先|协调和督导|科学问题)', '(?:沟通交流|会议|咨询会|临床试验|研究方案|试验方案|研究资料|提交计划|审评|试点项目|优先|协调和督导|科学问题|\\d+\\s*日)',1)
t=t.replace("actual = re.search(r'", "actual = re.search(r'自愿申报[^。；;]{0,20}(?:试点|项目)|优先组织[^。；;]{0,12}专家咨询会|审评时限为\\s*\\d+\\s*日|",1)
t=t.replace("                if name in text:\n                    names.add(name)","                # A printed title may prepend a drug/licensing object to the\n                # operative programme name. Match a literal >=6-char suffix,\n                # never the policy title as a positive permission.\n                if name in text or any(name[-size:] in text for size in range(6,len(name)+1)):\n                    names.add(name)",1)
t=t.replace("            objects=[];services=[];stages=[];need=[]\n", "            objects=[];services=[];stages=[];need=[]\n            qualified_list=False\n",1)
old="""                if (re.search(r'创新药|改良型新药|首创新药|源头性创新.{0,12}药物',part) or technical_category) and object_scope:
                    objects.append(self._quote(c,'同一有界安排明确的创新/改良对象和资格',(a,b)))"""
new="""                if closure=='same_source_named_programme':
                    # Actual printed applicability list, ended by the next
                    # top-level section, connects all branches to its parent.
                    if re.search(r'^[一二三四五六七八九十]+、',part):
                        qualified_list=bool(re.search(r'适用范围|适用条件',part))
                    if re.search(r'以下[^。；;]{0,40}药品[^。；;]{0,20}可以申请适用',part):
                        qualified_list=True
                list_member=(qualified_list and re.match(r'[（(][一二三四五六七八九十]+[）)]',part)
                             and not re.search(r'不适用|不得|不再接受',part))
                if (re.search(r'创新药|改良型新药|首创新药|源头性创新.{0,12}药物',part) or technical_category) and (object_scope or list_member):
                    objects.append(self._quote(c,'同一有界安排明确的创新/改良对象和资格',(a,b)))"""
assert old in t;t=t.replace(old,new,1)
t=t.replace("            direct_current = re.search(r'", "            direct_current = re.search(r'优先组织[^。；;]{0,12}专家咨询会|自愿申报[^。；;]{0,20}(?:试点|项目)|审评时限为\\s*\\d+\\s*日|",1)
t=t.replace("            if objects and services and stages:\n                self._add('named_mechanism',objects+need+services+stages,", "            if objects and services and stages:\n                # A current generic timed review sentence gives I3 service;\n                # it does not apply every programme need branch to its own\n                # separate domestically-unlisted subbranch.\n                timed_review=bool(re.search(r'审评时限为\\s*\\d+\\s*日',text))\n                if timed_review:need=[]\n                self._add('named_mechanism',objects+need+services+stages,",1)
t=t.replace("                          only_IF_consumers=True,negation_and_withdrawal_retained=True)", "                          only_IF_consumers=True,affected_dimensions=['I'] if timed_review else ['I','F'],negation_and_withdrawal_retained=True)",1)
# Right-name parsing is semantic, not a policy title whitelist. Anaphora must
# occur in the current containing paragraph and actual same right operation.
a=t.index('        operation=re.search(',t.index('    def _bounded_IF_right_operation'))
b=t.index('        primary=',a)
t=t[:a]+"""        current=self._current_source()
        current_text=norm(current.get('text','')) if current else self.norm
        right_match=re.search(r'(?:药品试验)?数据保护|市场独占',self.norm)
        operation=re.search(r'申请|给予|享受|实施保护|保护是指|终止|限制|不予许可|不予受理|不受理|不批准',self.norm)
        anaphor=bool(re.search(r'依赖[^。；;]{0,20}(?:该|受|保护)[^。；;]{0,12}数据',self.norm)
                     and re.search(r'(?:药品试验)?数据保护',current_text))
        if (not right_match and not anaphor) or not operation:
            return
        right=right_match.group() if right_match else re.search(r'(?:药品试验)?数据保护',current_text).group()
        # The statutory abbreviation shares the literal terminal noun.
        right=re.search(r'数据保护|市场独占',right).group()
"""+t[b:]
# append general bounded consumers before next table function
pos=t.index('    def _bounded_IF_table_qualification')
new=r'''    def _bounded_IF_individual_consultation(self):
        """An expressly unresolved technical issue gets actual authority access.

        Mere general encouragement/ordinary public-reference sentences cannot
        open this path. A direct supplied parent unit defines the same named
        research document and innovative trial object.
        """
        if not (re.search(r'(?:未能阐明|未涵盖|未解决)[^。；;]{0,20}(?:个性化|具体|技术)问题',self.norm)
                and re.search(r'(?:可|可以)[^。；;]{0,12}(?:与|向)(?:药审中心|审评中心)[^。；;]{0,15}(?:沟通|咨询)',self.norm)):
            return
        current=self._current_source();primary=self.unit.get('source_ref',{}).get('sha256')
        if current is None:return
        containers=[c for c in self.contexts if c['kind']=='parent_paragraph'
                    and c.get('source_ref',{}).get('sha256')==primary and self.norm in norm(c.get('text',''))]
        for container in containers:
            st=container.get('structure',{});uid=st.get('unit_id');index=st.get('sequence_index')
            if not uid or type(index)is not int:continue
            for c in self.contexts:
                cs=c.get('structure',{});part=norm(c.get('text',''))
                definition=re.search(r'(?P<name>[A-Za-z][A-Za-z0-9]{1,16})是[^。；;]{0,30}临床试验',part)
                if (c['kind']!='parent_paragraph' or c.get('source_ref',{}).get('sha256')!=primary
                        or cs.get('unit_id')!=uid or cs.get('sequence_index')!=index-1
                        or not definition or definition.group('name')not in norm(container.get('text',''))
                        or not re.search(r'创新药[^。；;]{0,20}临床试验',part)):
                    continue
                obj=self._quote(c,'同一直接父单元定义的创新药临床试验对象与技术文档')
                service=self._quote(container,'该技术文档未涵盖问题的实际药审机构沟通入口')
                self._add('named_mechanism',[obj,service],
                          '当前为未阐明的具体问题开放审评机构沟通，同一直接父单元限定其创新临床研发对象；非公共指南通常可参考',
                          relation_subtype='bounded_IF_actual_support',object_definition=obj['text'],
                          direct_mechanism=service['text'],research_stage=obj['text'],
                          only_IF_consumers=True,affected_dimensions=['I'],
                          source_closure='direct_ordered_parent_named_research_document')

    def _bounded_IF_first_member(self):
        """A first member may have its actual parent stored as preceding text.

        The first ordinal, immediate preceding-role, colon, complete operative
        applicability predicate and same source bind it. No siblings are read.
        """
        if not re.match(r'^\s*[（(]一[）)]',self.norm):return
        current=self._current_source();primary=self.unit.get('source_ref',{}).get('sha256')
        if current is None or norm(current.get('text',''))!=self.norm:return
        previous=[c for c in self.contexts if c['kind']=='preceding_paragraph'
                  and c.get('source_ref',{}).get('sha256')==primary and same_component(c,current)]
        if len(previous)!=1:return
        c=previous[0];part=norm(c.get('text',''))
        if (not part.endswith(':') or not re.search(r'符合(?:以下|下列)[^。；;]{0,20}(?:情形|条件)[^。；;]{0,15}药品',part)
                or not re.search(r'(?:可以|可|允许)[^。；;]{0,10}申请[^。；;]{0,20}(?:批准|准入|待遇|支持)',part)):
            return
        self._add('parent_predicate',[self._quote(c,'第一项直接承接的同源完整操作性父谓词')],
                  '第一项与立即前置且冒号闭合的完整申请父句直接组合；未展开第二项或其他章节',
                  shared_predicate=c['text'],relation_subtype='bounded_IF_first_operative_member',
                  only_IF_consumers=True,affected_dimensions=['I','F'])

    def _bounded_IF_missing_dependency(self):
        # A current explicit withdrawal for failing programme eligibility needs
        # that same arrangement's scope/support. Absence is not a negative.
        if (re.search(r'(?:不能满足|不符合)[^。；;]{0,25}(?:审评审批|审评|程序)[^。；;]{0,8}条件',self.norm)
                and re.search(r'终止[^。；;]{0,30}(?:审评|程序)',self.norm)
                and not any(r['details'].get('relation_subtype')=='bounded_IF_actual_support' for r in self.relations)):
            self._request('named_mechanism',self.text,
                          '当前资格不符导致实际程序撤回所承接的同版对象条件与支持后果未由共同接口提供',
                          'required_named_qualification_scope_unresolved')
        # A timed named clinical-trial channel may remain usable but its support
        # object must come from a delivered operative scope, never title lines.
        if (re.search(r'\d+日通道',self.norm) and re.search(r'临床试验|审评审批',self.norm)
                and re.search(r'时限[^。；;]{0,20}\d+日|\d+个工作日内完成',self.norm)
                and not re.search(r'创新药|改良型新药',self.norm)
                and not any(r['details'].get('relation_subtype')=='bounded_IF_actual_support' for r in self.relations)):
            request={'path':'named_mechanism','reference':self.text,
                     'current_text':self.text,'missing':'当前实际时限例外所指同版通道的药品对象与准入范围未由共同接口提供',
                     'stop_reason':'required_named_support_object_unresolved','dependency_status':'stopped','affected_dimensions':['I']}
            self.material_requests.append(request);self.source_requests.append(request.copy())

'''
t=t[:pos]+new+t[pos:];p.write_text(t)
p=p.with_name('dimensions.py');t=p.read_text()
t=t.replace(r'沟通交流|技术咨询|研究方案|试验方案|反馈|审评[^。；;]{0,20}(?:时限|期限|工作日)',r'沟通交流|沟通|技术咨询|专家咨询会|研究方案|试验方案|反馈|审评[^。；;]{0,20}(?:时限|期限|工作日)',1)
t=t.replace('可|应|完成|保持|维持|退出|终止|撤回|不再|协助|决定|组织|设立|开展|提供', '可|应|自愿申报|审评时限为|完成|保持|维持|退出|终止|撤回|不再|协助|决定|组织|设立|开展|提供',1)
p.write_text(t)
