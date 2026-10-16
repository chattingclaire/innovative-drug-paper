from pathlib import Path
C=Path(__file__).parent
p=C/'relations.py';s=p.read_text();s=s.replace("具有[^。；;]{0,8}创新性[^。；;]{0,8}具体包括", "具有[^。；;]{0,8}创新性[。.]?[^。；;]{0,8}具体包括")
s=s.replace("对纳入|申请适用|终止|开放|可申请", "对纳入|申请适用|终止|开放|可申请|即纳入|同意纳入")
s=s.replace("研制指导|技术审评|申报前沟通", "研制指导|技术审评|申报前沟通|核查|检验")
# Extend only the isolated builder; old definitions remain identical.
s=s.replace("        if closed:self._v9_programme_relations(closed)","        if closed:\n            self._v9_programme_relations(closed)\n            self._v9_operational_programme_content(closed)")
s+='''
    def _v9_operational_programme_content(self, closed):
        scope=self._v9_scope_roles(closed)
        if not scope:return
        raw=closed['raw'];lo,hi=closed['programme_span'];text=self.norm
        name=norm(closed['programme_name']).replace('审评工作','').replace('工作','')
        objects=norm('\\n'.join(q['text'] for q in scope));chain=self._v9_direct_chain(closed)
        parent=norm('\\n'.join(q['text'] for q in chain))
        # Actual assessment/explanation of this exact programme's qualifications
        # is content; mere website/form delivery is not a content action.
        actual=bool(name in text and re.search('评估[^。；;]{0,25}适用范围和适用条件|根据[^。；;]{0,35}适用情形[^。；;]{0,15}(?:阐述|说明)|(?:就|对)[^。；;]{0,25}情形和适用条件[^。；;]{0,15}(?:阐述|说明)',text))
        finite=[]
        if not actual and name in text and re.search('提交相关支持性资料[^。；;]{0,10}附件1',text):
            headers=list(re.finditer(r'(?m)^[ \\t]*附1[ \\t]*$',raw[lo:hi]))
            if len(headers)==1:
                start=lo+headers[0].end();next_head=re.search(r'(?m)^[ \\t]*附[2-9][ \\t]*$',raw[start:hi]);stop=start+next_head.start() if next_head else hi
                content=raw[start:stop]
                requirements=[]
                for a,b in sentence_spans(content):
                    part=norm(content[a:b])
                    if re.search('说明符合[^。；;]{0,15}情形的具体条款',part) and re.search('情形和适用条件[^。；;]{0,15}详细阐述',part):requirements.append((start+a,start+b))
                if len(requirements)==1:
                    finite=self._primary_role_quotes(closed,requirements,'exact_named_attachment_substantive_qualification_content')[0];actual=True
        if actual:
            evidence=scope+chain+finite
            if re.search('创新药|改良型新药',objects):self._v9_emit(evidence,'exact_programme_qualification_content',['I'],'当前实质评估/阐述或准确附表内容要求读取本程序资格；普通表单手续不能进入',current_content_action=text,finite_scope=objects,attachment_content=[q['text'] for q in finite])
            if re.search('尚无有效|无有效治疗|短缺药品',text) or finite or re.search('评估[^。；;]{0,25}适用范围和适用条件',text):
                if re.search('尚无有效|无有效治疗|短缺药品',objects):self._v9_emit(evidence,'exact_programme_need_content',['F'],'当前实际评估完整需要资格或确指附表实质内容，真实缺口分支单独消费',current_content_action=text,finite_need_scope=objects,attachment_content=[q['text'] for q in finite])
        if not chain or not re.search('申请适用|申请资格',parent):return
        # A currently named admitted-programme member is a specific class of
        # beneficiary; only that referenced programme supplies its scope.
        target=re.search('纳入([^。；;，,]{2,30}(?:程序|计划|通道))的药品',text)
        if target:
            referenced=self._closed_primary_programme(target.group(1),require_current=False)
            if referenced:
                linked_scope=self._v9_scope_roles(referenced);body=norm('\\n'.join(q['text'] for q in linked_scope))
                if re.search('创新药|改良型新药',body):self._v9_emit(chain+linked_scope,'named_admitted_object_qualification',['I'],'当前实质准入成员确指已纳入的同源有限程序对象；不借其他范围兄弟',current_member=text,direct_current_parent=parent,referenced_scope=body)
                if re.search('尚无有效|无有效治疗',body):self._v9_emit(chain+linked_scope,'named_admitted_need_qualification',['F'],'当前准入成员确指同源已纳入对象，真实缺口分支经此对象进入当前机会',current_member=text,direct_current_parent=parent,referenced_need_scope=body)
        # Printed scope ordinal is consumed only with the same programme's
        # conditions section explicitly mapping each scope item to conditions.
        member=re.match(r'^[（(]([一二三四五六七八九十]+)[）)]',text)
        if not member:return
        number=ordinal_number(member.group(1))
        conditions=re.search(r'(?m)^[ \\t]*[一二三四五六七八九十]+、适用条件[ \\t]*$',raw[lo:hi])
        if not conditions:return
        section_start=lo+conditions.end();next_top=re.search(r'(?m)^[ \\t]*[一二三四五六七八九十]+、',raw[section_start:hi]);section_end=section_start+next_top.start() if next_top else hi
        block=raw[section_start:section_end]
        if not re.search('以下列出的适用范围应满足相关条件',norm(block)):return
        heads=list(re.finditer(r'(?m)^[ \\t]*(\\d+)[.．][^\\n]+',block));matches=[h for h in heads if int(h.group(1))==number]
        if len(matches)!=1:return
        head=matches[0];end=next((h.start() for h in heads if h.start()>head.start()),len(block));definition=block[head.start():end]
        # The '此外' market-shortage mechanism is a distinct parallel subset.
        extra=definition.find('此外');definition=definition[:extra] if extra>=0 else definition
        body=norm(definition);quotes=self._primary_role_quotes(closed,[(section_start+head.start(),section_start+head.start()+len(definition))],'exact_current_scope_member_conditions')[0]
        if re.search('现有上市(?:剂型|规格)均不适用于儿童人群',body) and re.search('新(?:剂型|规格)[^。；;]{0,12}适(?:于|宜)',body) and re.search('新品种|剂型|规格',text):
            self._v9_emit(chain+quotes,'specific_form_modification_qualification',['I'],'当前剂型/规格资格成员的同号有限定义明确既有局限—新形式—适宜性，非新品种字面推定',current_member=text,direct_current_parent=parent,exact_definition=body)
        gap=re.search('(?:目前)?无有效治疗(?:药物|手段)|临床急需[^。；;]{0,30}境内未上市',body)
        if gap:
            self._v9_emit(chain+quotes,'specific_scope_need_qualification',['F'],'当前同号资格成员的准确有限定义包含真实治疗选项或所需药品取得缺口；不复制相邻市场短缺或优势分支',current_member=text,direct_current_parent=parent,qualified_gap=gap.group(),exact_definition=body)
'''
p.write_text(s)
p=C/'dimensions.py';s=p.read_text();s=s.replace("anchor_text==view.norm or anchor_text.rstrip('。;；')==view.norm.rstrip('。;；')","anchor_text==_norm(view.norm) or anchor_text.rstrip('。;；')==_norm(view.norm).rstrip('。;；')")
s=s.replace('创新药持有人同意','创新药持有人(?:同意|许可)')
s=s.replace("re.search('(?:依申请纳入|将依申请纳入|范围为|给予|撤回)","re.search(r'(?:依申请纳入|将依申请纳入|范围为|给予|撤回)")
p.write_text(s)
p=C/'run_finite_controls.py';s=p.read_text();s=s.replace("'pending_N':sum(not c['hard_assertion'] for c in results)","'hard_passed_N':sum(c['hard_assertion'] and c['passed'] for c in results),'hard_failed_N':sum(c['hard_assertion'] and not c['passed'] for c in results),'pending_N':sum(not c['hard_assertion'] for c in results)");p.write_text(s)
