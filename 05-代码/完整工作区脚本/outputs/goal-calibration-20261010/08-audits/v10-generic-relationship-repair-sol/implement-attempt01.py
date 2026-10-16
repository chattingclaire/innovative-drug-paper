from pathlib import Path
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol'
p=V/'relations.py';s=p.read_text();new='''
V10_REPAIR_ENTRY = (
    r'其他[^。；;]{0,30}优先审评审批[^。；;]{0,12}情形'
    r'|(?:工具|表征|评估)[^。；;]{0,100}(?:沟通|接受)'
    r'|(?:建立|完善|实施)[^。；;]{0,80}支持创新[^。；;]{0,30}机制'
    r'|(?:审核|符合)[^。；;]{0,35}药品试验数据保护条件[^。；;]{0,50}(?:执行|实施)'
    r'|(?:开展|实施)[^。；;]{0,18}试点'
    r'|(?:项目申请前|临床试验申请前)[^。；;]{0,120}沟通交流'
    r'|临床试验机构[^。；;]{0,65}(?:培训|技术能力)'
)

def _v10_repair_gate(text):
    """Pure nomination gate; accepts only the normalized current text.

    No IDs, labels, path, source inventory or decision is inspected. Every new
    builder/consumer starts with this gate; it never establishes a positive.
    """
    return bool(re.search(V10_REPAIR_ENTRY, text))

'''
s=s.replace('class SourceDependencyStop(ValueError):',new+'class SourceDependencyStop(ValueError):',1)
s=s.replace('            self._v9_bounded_relationships()','            self._v9_bounded_relationships()\n        if _v10_repair_gate(self.norm):\n            self._v10_bounded_relationships()',1)
methods=r'''
    def _v10_bounded_relationships(self):
        # Gate precedes every new lookup/mutation. This is the full extension
        # entry, exported verbatim for static record selection.
        if not _v10_repair_gate(self.norm):return
        self._v10_exact_priority_member()
        self._v10_bound_tool_communication()
        self._v10_current_innovation_appraisal()
        self._v10_qualified_right_execution()
        self._v10_pilot_operation()

    def _v10_emit(self, evidence, path, dimensions, reason, **roles):
        self._add('v10_IF_relationship',evidence,reason,
                  relation_subtype=path,v10_semantic_path=path,
                  affected_dimensions=dimensions,only_IF_consumers=True,
                  v10_role_receipt=roles)

    def _v10_exact_priority_member(self):
        member=self.norm.rstrip('。；;')
        if not re.fullmatch(r'[（(][一二三四五六七八九十]+[）)][^。；;]*其他[^。；;]*优先审评审批[^。；;]*情形',member):return
        closed=self._v9_programme()
        if not closed:return
        chain=self._v9_direct_chain(closed)
        if not chain:return
        parents,roles=chain
        if not any(re.search(r'药品上市许可申请[^。；;]*可以申请适用优先审评审批程序',norm(q['text'])) for q in parents):return
        raw=closed['raw'];lo,hi=closed['programme_span'];block=raw[lo:hi]
        for m in re.finditer(r'[^\n。]+按照适用范围[“「"](?P<member>[^”」"]+)[”」"][^\n。]*提出优先审评审批申请[。]?',block):
            if norm(m.group('member')).rstrip('。；;')!=member:continue
            need=norm(m.group())
            # Concrete unmet local availability + clinical need is a single
            # selected beneficiary, not the programme's ordinary advantage branch.
            if not re.search(r'临床急需境外已上市境内未上市的[^，,。；;]{0,35}(?:药品|药物)',need):continue
            if re.search(r'并非|不是|未列入|不适用|不包括|仅作说明|示例',need):continue
            quoted,receipt=self._primary_role_quotes(closed,[(lo+m.start(),lo+m.end())],'exact_member_need_selected_application')
            if quoted:self._v10_emit(parents+quoted,'exact_member_need_selected_application',['F'],'同版完整当前成员的明确交叉引用将实际需要药品的优先申请落实到本成员；不借其他优先情形',current_member=self.norm,object_and_need_scope=m.group(),direct_parent_roles=roles,cross_reference_roles=receipt)

    def _v10_bound_tool_communication(self):
        if not re.search(r'(?:工具|表征)[^。；;]{0,80}(?:选择|接受)[^。；;]{0,70}(?:建议|可)[^。；;]{0,30}(?:药监机构|药审中心)[^。；;]{0,15}沟通',self.norm):return
        if re.search(r'仿制药|非创新药|仅[^。；;]{0,12}(?:填写|提交|备案|签章)|不提供|仅通知',self.norm):return
        current=self._v9_current_context()
        if not current:return
        sha=self.unit.get('source_ref',{}).get('sha256');groups={}
        for c in self.contexts:
            if c.get('source_ref',{}).get('sha256')!=sha:continue
            comp,ok=self._se_geometry_value(c,'component_id');role=c.get('structure',{}).get('source_role') or c.get('source_ref',{}).get('locator',{}).get('source_role')
            if ok and comp and role:groups.setdefault(comp,{}).setdefault(role,[]).append(c)
        valid=[]
        required=('published_title_and_notice','same_title_attachment_link','self_declared_scope','body_opening','body_last_paragraph','actual_reference_component_boundary')
        for comp,g in groups.items():
            if any(len(g.get(k,[]))!=1 for k in required):continue
            rows=[g[k][0] for k in required]
            order=[self._se_geometry_value(c,'sequence_index')[0] for c in rows]
            if any(type(i)is not int for i in order) or order!=sorted(set(order)):continue
            notice,attachment,scope,opening,last,boundary=rows
            title=re.search(r'附件[:：](.+)',norm(attachment['text']))
            if not title or norm(title.group(1)) not in norm(notice['text']):continue
            if not re.search(r'本指导原则[^。；;]{0,90}创新药临床试验',norm(scope['text'])):continue
            if re.search(r'不适用[^。；;]{0,20}创新药|不包括[^。；;]{0,20}创新药',norm(scope['text'])):continue
            cc,ok=self._se_geometry_value(current,'component_id')
            if not ok or (cc and cc!=comp):continue
            def pages(c):
                loc=c.get('source_ref',{}).get('locator',{});st=c.get('structure',{})
                return loc.get('physical_pages') or loc.get('pages') or st.get('physical_pages') or st.get('pages') or []
            a,b,z,u=pages(opening),pages(last),pages(boundary),pages(current)
            if not all(x and all(type(i)is int for i in x) for x in [a,b,z,u]):continue
            if not(max(a)<=min(u)<=max(u)<=max(b)<min(z)):continue
            # The actual current paragraph is uniquely bound by SHA, original
            # paragraph number and physical pages inside the same body interval.
            def pid_number(c):
                loc=c.get('source_ref',{}).get('locator',{});st=c.get('structure',{})
                pid=st.get('paragraph_id') or loc.get('paragraph_id') or st.get('candidate_paragraph_id') or loc.get('candidate_paragraph_id')
                m=re.fullmatch(r'p(\d+)',pid or '')
                return int(m.group(1)) if m else None
            pn=[pid_number(c) for c in [opening,current,last]]
            if any(i is None for i in pn) or not pn[0]<=pn[1]<=pn[2]:continue
            valid.append((rows,comp,{'paragraph_interval':pn,'current_pages':u,'body_pages':[a,b],'reference_boundary_pages':z,'sequence':order}))
        if len(valid)!=1:return
        rows,comp,geometry=valid[0]
        evidence=[self._quote(rows[1],'同版同名附件明确绑定有限指导原则正文'),self._quote(rows[2],'当前所在有限正文明确面向创新药临床试验'),self._quote(rows[3],'该附件实际正文起始边界'),self._quote(rows[4],'该附件实际正文终止边界'),self._quote(rows[5],'该附件参考文献边界'),self._quote(current,'当前具体工具选择/自行工具接受问题的实际监管沟通')]
        self._v10_emit(evidence,'bounded_innovative_trial_tool_communication',['I'],'当前具体研究工具选择/接受问题可与监管沟通，实际提供创新临床研发技术便利；普通指导原则条款和手续不继承支持',innovation_scope=rows[2]['text'],actual_beneficiary='this bounded innovative clinical trial',component_binding={'component_id':comp,**geometry},current_service=self.norm)

    def _v10_current_innovation_appraisal(self):
        if not re.search(r'(?:建立|完善|实施)[^。；;]*支持创新[^。；;]*机制',self.norm):return
        current=self._v9_current_context()
        if not current:return
        body=norm(current['text']);tail=body.split(self.norm,1)[1]
        if re.search(r'另一[^。；;]{0,25}机制|其他[^。；;]{0,25}机制|表格字段|仅为宗旨|尚未建立|不建立',tail+self.norm):return
        m=re.search(r'[^。；;]*研判药品价值[^。；;]*对创新价值进行量化和分级[^。；;]*',tail)
        if not m:return
        # Only the immediately supplied operational definition of this actual
        # mechanism supplies substantive innovation appraisal, not its name.
        evidence=[self._quote(current,'当前已建立机制及同原段实际药品创新价值量化分级内容')]
        self._v10_emit(evidence,'current_drug_innovation_value_appraisal',['I'],'当前机制实质评价药品创新价值，同段定义其量化分级内容；不由泛支持宗旨给创新依据',innovation_scope=m.group(),current_operation=self.norm,complete_same_paragraph=current['text'])

    def _v10_complete_articles(self):
        # Pure supplied-geometry lookup. Completeness is at article level;
        # absent articles/table are never reconstructed or read from assets.
        sha=self.unit.get('source_ref',{}).get('sha256');out=[]
        for di,doc in enumerate(self.bundle.get('explicit_or_primary_source_resources',[])):
            if doc.get('source_sha256',doc.get('snapshot_sha256'))!=sha:continue
            items=doc.get('source_texts',[])
            for gi,g in enumerate(doc.get('ordered_article_groups',[])):
                ids=g.get('ordered_source_resource_ids',[])
                if not ids or len(ids)!=len(set(ids)):continue
                rows=[]
                for order,rid in enumerate(ids,1):
                    found=[(ti,x) for ti,x in enumerate(items) if x.get('source_resource_id')==rid]
                    if len(found)!=1:break
                    ti,x=found[0]
                    if x.get('clause_index_one_based')!=order or x.get('article')!=g.get('article') or x.get('source_sha256')!=sha:break
                    pointer=f'/explicit_or_primary_source_resources/{di}/source_texts/{ti}'
                    contexts=[c for c in self.contexts if self.origins.get(c['context_id'],{}).get('source_bundle_pointer')==pointer and c.get('source_ref',{}).get('sha256')==sha and c.get('text')==x.get('text')]
                    if len(contexts)!=1:break
                    rows.append(contexts[0])
                if len(rows)==len(ids):out.append((rows,f'/explicit_or_primary_source_resources/{di}/ordered_article_groups/{gi}'))
        return out

    def _v10_qualified_right_execution(self):
        if not re.fullmatch(r'经审核符合药品试验数据保护条件的药品[,]按照《[^》]+》有关规定执行[。]?',self.norm):return
        current=self._v9_current_context()
        if not current:return
        # Qualification + actual execution, not mere application documents.
        if not re.search(r'符合《[^》]+》中给予药品试验数据保护条件',norm(current['text'])):return
        articles=self._v10_complete_articles();definition=[];entitlements=[]
        for rows,pointer in articles:
            first=norm(rows[0]['text']);whole='\n'.join(norm(c['text']) for c in rows)
            if re.search(r'数据保护是指[^。]*实施保护[^。]*给予[^。]*数据保护期',first) and re.search(r'其他申请人自行取得并未依赖他人受保护数据的除外',whole):definition.append((rows,pointer))
            if re.search(r'^第[一二三四五六七八九十]+条\s*自创新药首次境内上市许可之日起[,]给予\d+年数据保护期',first) and re.search(r'受保护的数据[^。；;]*不予许可',whole) and re.search(r'其他申请人提交自行取得并未依赖他人受保护数据的除外',whole):entitlements.append((rows,pointer))
        if len(definition)!=1 or len(entitlements)!=1:return
        dr,dp=definition[0];er,ep=entitlements[0]
        evidence=[self._quote(current,'当前经实质资格审核后执行数据保护安排')]+[self._quote(c,'同版完整数据保护定义与自行取数例外') for c in dr]+[self._quote(c,'同版完整创新持有人资格与保护待遇及例外') for c in er]
        self._v10_emit(evidence,'qualified_innovative_right_actual_execution',['I'],'当前对审核合格药品实质执行同版保护安排，包内完整创新权利条款给出资格及实际保护；不把其他自行取数者视为创新持有人',innovation_scope=er[0]['text'],current_operation=self.norm,qualification_branch='qualified protected innovative holder only',exception_preserved='other applicant independent data does not receive this entitlement',source_article_group_pointers=[dp,ep],no_missing_article_inference=True)

    def _v10_closed_plan(self):
        sha=self.unit.get('source_ref',{}).get('sha256');current=self._v9_current_context()
        if not current:return None
        valid=[]
        for c in self.contexts:
            if c['kind']!='source_resource_text' or c.get('source_ref',{}).get('sha256')!=sha:continue
            raw=c.get('text','');loc=c.get('source_ref',{}).get('locator',{})
            interval=loc.get('character_range_0based_halfopen')
            if not isinstance(interval,list) or len(interval)!=2 or any(type(x)is not int for x in interval) or interval[1]-interval[0]!=len(raw):continue
            if not re.search(r'全部正文|完整正文',str(loc.get('sections',''))):continue
            title=raw.splitlines()[0] if raw.splitlines() else ''
            if not re.fullmatch(r'[^\n]{2,60}临床试验[^\n]*试点工作方案',title):continue
            heads=list(re.finditer(r'(?m)^[一二三四五六七八九十]+、[^\n]+$',raw))
            if len(heads)<3 or len({m.group().split('、',1)[0] for m in heads})!=len(heads):continue
            text,offsets=matching_view(raw)
            if text.count(self.norm)!=1 or text.count(norm(current['text']))!=1:continue
            pos=text.index(self.norm);span=raw_span(offsets,pos,pos+len(self.norm))
            whole=norm(current['text']);within=whole.index(self.norm)
            # Complete actual paragraph binding, not reused ID + substring.
            fullpos=text.index(whole)
            if fullpos+within!=pos:continue
            scope=re.search(r'试点项目范围为1类创新药(?:[（(][^。\n]{0,100}除外[）)])?临床试验申请[。]',raw)
            if not scope:continue
            excluded=re.search(r'[（(]([^）)]+)除外[）)]',scope.group())
            exclusions=excluded.group(1) if excluded else ''
            if any(token and token in self.norm for token in re.split(r'[、，,]|产品|等',exclusions)):continue
            if re.search(r'仿制药|生物类似药|非创新药|另一[^。；;]{0,20}(?:项目|药品)|其他[^。；;]{0,20}(?:项目|药品)',self.norm):continue
            valid.append((c,current,span,scope.span(),title,exclusions,heads))
        return valid[0] if len(valid)==1 else None

    def _v10_pilot_operation(self):
        if not re.search(r'(?:开展|实施)[^。；;]{0,18}试点|(?:项目申请前|临床试验申请前)[^。；;]{0,120}沟通交流|临床试验机构[^。；;]{0,65}(?:培训|技术能力)',self.norm):return
        plan=self._v10_closed_plan()
        if not plan:return
        c,current,span,scope_span,title,exclusions,heads=plan;raw=c['text']
        before=raw[:span[0]]
        top=[m for m in heads if m.start()<span[0]]
        if not top:return
        section=top[-1].group()
        subsection=list(re.finditer(r'(?m)^[（(][一二三四五六七八九十]+[）)][^\n]+$',before[top[-1].end():]))
        sub=subsection[-1].group() if subsection else ''
        evidence=[self._quote(c,'同版完整工作方案有限项目对象及排除条件',scope_span),self._quote(current,'当前操作性试点实施或实际技术服务')]
        path=None;roles={'plan_name':title,'innovation_scope':raw[slice(*scope_span)],'actual_current_object':self.norm,'current_section':section,'current_subsection':sub,'exclusions_preserved':exclusions,'current_original_span':span}
        if re.fullmatch(r'在具备条件的省[^。；;]{0,15}(?:开展|实施)试点[。]?',self.norm) and '纳入试点工作' in section and '试点区域' in sub:
            actual=re.search(r'经确认的试点项目[，,][^。\n]*受理临床试验申请后\d+个工作日内完成审评审批[。]',raw)
            if not actual:return
            evidence.append(self._quote(c,'实际确认纳入后可用审评便利，不用工作目标代替落实机制',actual.span()))
            path='actual_innovative_trial_pilot_rollout';roles['actual_mechanism']=actual.group()
        elif re.search(r'^申请人在项目申请前可[^。；;]*提出新药临床试验申请前沟通交流[。]?$',self.norm) and '实施步骤' in section and '试点项目申请' in sub:
            # This same-phase service stands on its own. Post-admission review
            # time is deliberately neither quoted nor used for this path.
            start=before.rfind('1.提出申请。');prefix=raw[start:span[0]] if start>=0 else ''
            if not re.search(r'符合要求的申请人自愿申报试点项目',prefix) or re.search(r'其他项目|非试点项目',prefix):return
            evidence.append(self._quote(c,'项目申请当前组成部分明确同一合格申请人', (start,span[0])))
            path='same_stage_innovative_trial_preapplication_communication';roles['actual_service']=self.norm;roles['post_admission_time_not_used']=True
        elif re.search(r'^药审中心为试点区域临床试验机构(?:[（(]含试点机构和非试点机构[）)])?提供人员培训[,]以提高临床试验机构[^。；;]*(?:项目立项|方案审核|风险评估)[^。；;]*技术能力[。]?$',self.norm) and '保障措施' in section and '技术培训' in sub:
            institution=re.search(r'试点机构原则上[^。\n]*申请人提交新药临床试验申请前提供临床试验项目立项[^。\n]*工作制度[。]',raw)
            if not institution:return
            evidence.append(self._quote(c,'实际试点机构为本创新临床项目提供申请前技术工作，非试点分支不借创新对象',institution.span()))
            path='innovative_trial_institution_technical_training';roles['actual_beneficiary']='included pilot institution branch only';roles['nonpilot_not_inferred_innovative']=True
        if path:self._v10_emit(evidence,path,['I'],'当前操作性动作与有限同方案创新对象及实际同阶段便利/技术服务直接承接；宗旨、常规流程和兄弟角色不继承',**roles)
'''
s += methods;p.write_text(s)
p=V/'dimensions.py';s=p.read_text();s=s.replace('from evidence import make_decision','from evidence import make_decision\nfrom relations import _v10_repair_gate',1)
s=s.replace('        _v9_IF_consume(acc, view)\n    decisions = acc.finish()','        _v9_IF_consume(acc, view)\n    if _v10_repair_gate(view.norm):\n        _v10_IF_consume(acc, view)\n    decisions = acc.finish()',1)
s += '''

def _v10_IF_consume(acc, view):
    # No shared old helper or global is changed; only explicit new I/F
    # relations are consumed after the exact frozen v9 path.
    if not _v10_repair_gate(view.norm):return
    for rel in view.linked('v10_IF_relationship'):
        details=rel['details'];dims=details.get('affected_dimensions',[])
        if not isinstance(dims,list) or not dims or len(dims)!=len(set(dims)) or any(d not in ('I','F') for d in dims):raise ValueError('invalid v10 IF subset')
        path=details['v10_semantic_path'];roles=details.get('v10_role_receipt',{})
        unit=Unit(view.norm,0,len(view.norm),rel['context_evidence'],'v10_IF_relationship',details)
        obj={'established':True,'object_text':roles.get('innovation_scope',roles.get('object_and_need_scope',view.text)),'context_evidence':unit.contexts,'current_anchors':[view.current_anchor(0,len(view.norm))],'role':'v10_bounded_current_operation_object_service','reason':'current actual predicate, legally bounded object and same-stage opportunity are individually proved'}
        for d in dims:
            acc.add(d,unit,'v10_'+path,details['relation_reason'],obj,{'v10_role_receipt':roles,'scope':'only proved current operation and beneficiary; no sibling propagation'})
''';p.write_text(s)
print('wrote isolated IF attempt01')
