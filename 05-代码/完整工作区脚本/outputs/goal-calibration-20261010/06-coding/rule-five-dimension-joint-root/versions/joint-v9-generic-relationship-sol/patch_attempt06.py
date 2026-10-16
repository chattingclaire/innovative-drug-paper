from pathlib import Path
P=Path(__file__).resolve().parent
q=P/'dimensions.py';s=q.read_text()
s=s.replace("        details=rel['details'];path=details['v9_semantic_path'];roles=details.get('v9_role_receipt',{})", "        details=rel['details'];path=details['v9_semantic_path'];roles=details.get('v9_role_receipt',{})\n        dims=details.get('affected_dimensions',[])\n        if not isinstance(dims,list) or not dims or len(dims)!=len(set(dims)) or any(d not in ('I','F') for d in dims):raise ValueError('invalid v9 affected IF subset')")
s=s.replace("for d in details['affected_dimensions']:","for d in dims:")
s=s.replace("    gap=re.search('(?:目前)?无有效治疗", "    named_objects=set(re.findall(r'(?:创新药|药品|药物|新药)([甲乙丙丁A-Za-z][A-Za-z0-9_-]*)',text))\n    beneficiary_bound=len(named_objects)<2\n    gap=re.search('(?:目前)?无有效治疗")
s=s.replace("and not alternate_cause and (not denied_identity", "and not alternate_cause and beneficiary_bound and (not denied_identity")
needle="    if re.search('其他申请人',text) and re.search('未经"
insert="""    actual_innovation_support=bool(innovation and not distinct and beneficiary_bound and re.search('(?:审评审批|临床试验审评)[^。；;]{0,35}(?:缩减|缩短|增设|优化)|形成优化创新药临床试验审评审批的工作措施|(?:创新药|抗肿瘤创新药)[^。；;]{0,70}(?:密切沟通|支持国家重点研发|鼓励全球早期同步研发)|(?:密切沟通)[^。；;]{0,45}提高[^。；;]{0,15}创新药[^。；;]{0,20}评价质量',text))
    if actual_innovation_support:
        acc.add('I',unit,'v9_I3_current_innovation_support_operation','当前实际审评便利、研发通道措施或针对明确创新药的研发技术沟通支持；不借政策宗旨或普通流程身份。',obj,{'current_support_operation':text})
    if re.search('药物研发[^。；;]{0,25}(?:使用|采用)AI技术',text) and re.search('与药监机构[^。；;]{0,90}(?:模型|技术)[^。；;]{0,60}(?:沟通|咨询)',text) and not distinct:
        acc.add('I',unit,'v9_I3_current_development_technology_consultation','当前为具体研发技术工具的设计、模型使用问题开放技术沟通支持；普通AI材料录入不符合。',obj)
    if re.search('急危重患者优先救治',text) and re.search('抢救资源配置与紧急调配',text) and re.search('药品可用',text):
        acc.add('F',unit,'v9_F_current_urgent_medication_resource','当前急危重需要决定优先救治和药品可用的抢救资源配置；泛疾病或普通药品配置不符合。',obj)
    if re.search('暂时无法纳入基本目录',text) and re.search('商保[^。；;]{0,15}(?:目录|药品目录)',text) and re.search('(?:主要聚焦|主要纳入)[^。；;]{0,100}(?:药品|创新药)|推荐商业健康保险',text):
        acc.add('F',unit,'v9_F_current_basic_coverage_gap_target','当前基本保障未能纳入的对象被确定为补充保障目录的实质纳入/聚焦对象；临床优势不代替保障缺口。',obj)
    if re.search('遴选儿童用药',text) and re.search('明确儿童适应证和儿童用法用量',text) and re.search('可不受[^。；;]{0,25}(?:两规|品种数)限制',text) and re.search('增加用药范围',text):
        acc.add('F',unit,'v9_F_current_specific_population_access','当前针对有明确儿童使用需要的药品放宽实际遴选数量限制、增加药品使用范围；不是裸儿童身份。',obj)
"""
s=s.replace(needle,insert+needle)
q.write_text(s)
q=P/'relations.py';s=q.read_text()
s=s.replace("        self._v9_supplied_qualification_parent()", "        self._v9_supplied_qualification_parent()\n        self._v9_same_paragraph_support()")
s=s.replace("eligible=[c for t,c in parents.items() if self._se_parent_binding(c) and self._se_parent_binding(c).get('role_only_not_independent_source_verification') is False and re.search", "eligible=[c for t,c in parents.items() if ((self._se_parent_binding(c) and self._se_parent_binding(c).get('role_only_not_independent_source_verification') is False) or self._v9_ordered_parent_binding(c,current)) and re.search")
s=s.replace("            if len(selected)!=8:continue", "            required=[('table_header_cell',i,norm(h)) for i,h in enumerate(headers)]+[('table_row_cell',i,norm(t)) for i,t in enumerate(rc) if t]\n            actual=[(c['kind'],c.get('structure',{}).get('column_index'),norm(c.get('text',''))) for c in selected]\n            if len(actual)!=len(required) or set(actual)!=set(required):continue")
s=s.replace("if self._v9_eligible_scope_topic(objects,'尚无有效|无有效治疗|短缺药品'):self._v9_emit", "if self._v9_eligible_scope_topic(objects,'尚无有效|无有效治疗|短缺药品'):self._v9_emit")
# An explicit general qualification refers to its complete named range; the
# clinical-value criterion alone never supplies F.
needle="        if not chain or not re.search('申请适用|申请资格',parent):return"
insert="""        complete_range=bool(name in text and re.search('符合[^。；;]{0,30}范围的药品上市许可申请',text) and re.search('应具有明显临床价值',text))
        if complete_range and self._v9_eligible_scope_topic(objects,'尚无有效|无有效治疗|短缺药品') and not re.search('附条件批准|仅限|仅适用',text+'。'+parent):
            self._v9_emit(scope+chain,'explicit_complete_range_qualification',['F'],'当前明文完整范围的申请资格承接该有限范围的真实需要对象；当前临床价值不自行生成F',current_complete_range_reference=text,finite_qualified_need_scope=objects)
"""
s=s.replace(needle,insert+needle)
s+='''
    def _v9_ordered_parent_binding(self, parent, current):
        # A supplied parent role alone is insufficient. The ordered scope must
        # bind this exact current member, with its original line order and an
        # explicit next top-level boundary. Other members provide closure only.
        primary=self.unit.get('source_ref',{}).get('sha256')
        pid,pok=self._se_geometry_value(parent,'paragraph_id');cid,cok=self._se_geometry_value(current,'paragraph_id')
        if not pok or not cok or not pid or not cid or current['source_ref']['sha256']!=primary:return None
        options=[]
        for group in self.contexts:
            if group['kind']!='source_list' or group['source_ref']['sha256']!=primary:continue
            groups,ok=self._se_geometry_value(group,'child_groups')
            if not ok or not isinstance(groups,list):continue
            ids=[i for g in groups if g.get('position')=='contexts' for i in g.get('ordered_context_ids',[])]
            members=[self.by_id.get(i) for i in ids]
            if len(members)<2 or len(ids)!=len(set(ids)) or any(not c or c['kind']!='ordered_members' or not self._se_same_geometry(parent,c) for c in members):continue
            seq=[self._se_geometry_value(c,'sequence_index') for c in members]
            if any(not ok for _,ok in seq) or [v for v,_ in seq]!=list(range(len(members))):continue
            mp=[self._se_geometry_value(c,'paragraph_id') for c in members]
            if any(not ok for _,ok in mp) or mp[0][0]!=pid or norm(members[0]['text'])!=norm(parent['text']):continue
            matches=[c for c,(p,_) in zip(members[1:],mp[1:]) if p==cid and self.norm in norm(c['text'])]
            if len(matches)!=1:continue
            lines=[self._se_geometry_value(c,'source_lines') for c in members]
            if any(not ok or not isinstance(ls,list) or not ls or any(type(v)is not int for v in ls) for ls,ok in lines):continue
            if any(max(a[0])>=min(b[0]) for a,b in zip(lines,lines[1:])):continue
            if any(self._se_geometry_value(c,'parent_context_id')!=(group['context_id'],True) for c in members):continue
            top=re.match(r'^([一二三四五六七八九十]+)、',norm(parent['text']))
            if not top or not re.search('(?:满足|符合)以下条件之一[:：]$',norm(parent['text'])):continue
            for bid in [i for g in groups if g.get('position')=='structure_boundary' for i in g.get('ordered_context_ids',[])]:
                boundary=self.by_id.get(bid)
                if not boundary or boundary['kind']!='boundary_container' or not self._se_same_geometry(parent,boundary):continue
                st=boundary.get('structure',{})
                if st.get('parent_context_id')!=group['context_id'] or st.get('first_paragraph')!=pid or st.get('last_paragraph')!=mp[-1][0]:continue
                next_ids=[i for g in st.get('child_groups',[]) if g.get('position')=='next_structure' for i in g.get('ordered_context_ids',[])]
                if len(next_ids)!=1:continue
                edge=self.by_id.get(next_ids[0])
                if not edge or edge['kind']!='boundary' or not self._se_same_geometry(parent,edge):continue
                ls,ok=self._se_geometry_value(edge,'source_lines');nexttop=re.match(r'^([一二三四五六七八九十]+)、',norm(edge.get('text','')))
                if not ok or not isinstance(ls,list) or not ls or any(type(v)is not int for v in ls) or min(ls)<=max(lines[-1][0]):continue
                if self._se_geometry_value(edge,'parent_context_id')!=(boundary['context_id'],True) or not nexttop or ordinal_number(nexttop.group(1))!=ordinal_number(top.group(1))+1:continue
                options.append({'ordered_scope_id':group['context_id'],'current_member_id':matches[0]['context_id'],'parent_id':members[0]['context_id'],'next_boundary_id':edge['context_id'],'scope_quote':self._quote(edge,'原位置下一顶层边界仅用于父治理闭合，不消费其内容')})
        unique={x['ordered_scope_id']:x for x in options}
        return next(iter(unique.values())) if len(unique)==1 else None

    def _v9_same_paragraph_support(self):
        current=self._current_source()
        if current is None or current['source_ref']['sha256']!=self.unit.get('source_ref',{}).get('sha256'):return
        raw=current.get('text','');body=norm(raw);text=self.norm
        if body.count(text)!=1 or body==text or not re.search('创新药|抗肿瘤创新药|药物研发',body):return
        if re.search('其他(?:药品|药物|项目)|另一(?:药品|药物|项目)',body):return
        technical=bool(re.search('如有[^。；;]{0,25}个性化问题[^。；;]{0,30}沟通交流',text) and re.search('针对[^。；;]{0,25}抗肿瘤创新药[^。；;]{0,35}(?:准备|整理|分析)',body))
        tool=bool(re.search('是否接受自行开发[^。；;]{0,20}(?:表征|评估)工具',text) and re.search('与药监机构进行沟通',text) and re.search('药物研发|药物临床',body))
        causal=bool(re.match('为此',text) and re.search('临床试验申请[^。；;]{0,8}再提速',text) and re.search('(?:在研产品|临床研发)[^。；;]{0,40}(?:研发创新|加快研发)|创新[^。；;]{0,50}在研产品需要进一步加快研发',body))
        global_target=bool(re.search('支持符合条件的全球同步研发品种[^。；;]{0,30}纳入\\d+日通道',text) and re.search('创新药全球同步研发',body))
        support=bool(re.search('全流程支持创新的机制',text) and re.search('创新药',body))
        if technical or tool or causal or global_target or support:
            self._v9_emit([self._quote(current,'当前确切同段的对象、个性化/技术工具内容或显式因果研发对象')],'same_paragraph_explicit_support',['I'],'当前技术支持或研发便利实际承接本段确指对象/问题/因果；不借相邻程序、普通通知或孤立创新身份',current_operation=text,same_paragraph_object_and_bridge=body,bridge_type='individual_problem' if technical else 'development_tool' if tool else 'explicit_cause' if causal else 'named_global_development_object' if global_target else 'current_support_innovation_operation')
'''
q.write_text(s)
q=P/'run_finite_controls.py';s=q.read_text().replace("O/'supplemental-controls-before-attempt04.json']","O/'supplemental-controls-before-attempt04.json',O/'supplemental-controls-before-attempt06.json']");q.write_text(s)
