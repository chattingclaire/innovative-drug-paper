from pathlib import Path
C=Path(__file__).parent;p=C/'relations.py';s=p.read_text()
s=s.replace("innovation=bool(re.search('创新药|改良型新药|创新型药物|创新疫苗',scope))", "innovation=self._v9_eligible_scope_topic(scope,'创新药|改良型新药|创新型药物|创新疫苗')")
s=s.replace("gap=bool(re.search('尚无有效|无有效治疗|短缺药品|市场短缺',scope))", "gap=self._v9_eligible_scope_topic(scope,'尚无有效|无有效治疗|短缺药品|市场短缺')")
s=s.replace("if re.search('创新药|改良型新药',objects):", "if self._v9_eligible_scope_topic(objects,'创新药|改良型新药'):")
s=s.replace("if re.search('尚无有效|无有效治疗|短缺药品',objects):", "if self._v9_eligible_scope_topic(objects,'尚无有效|无有效治疗|短缺药品'):")
s=s.replace("name=norm(closed['programme_name']).replace('审评工作','').replace('工作','')\n        objects=", "name=norm(closed['programme_name']).replace('审评工作','').replace('工作','')\n        name=name.removeprefix('药品上市许可').removesuffix('程序')\n        objects=")
s=s.replace("            current=[i for i,p in enumerate(paragraphs) if self.norm in norm(p.get('text',''))]", "            compact=re.sub(r'\\s+','',self.norm)\n            current=[i for i,p in enumerate(paragraphs) if compact in re.sub(r'\\s+','',norm(p.get('text','')))]")
s=s.replace("complete=norm(cp.get('text',''));exact=[i for i,p in enumerate(paragraphs) if complete==norm(p.get('text',''))]", "complete=re.sub(r'\\s+','',norm(cp.get('text','')));exact=[i for i,p in enumerate(paragraphs) if complete==re.sub(r'\\s+','',norm(p.get('text','')))]")
s=s.replace("own_stage=bool(start<=position<stop and re.search('早期临床研发阶段',text) and ('临床优势' in norm(ps[definition]['text'])))", "own_stage=bool(re.search('早期临床研发阶段',text) and ('临床优势' in norm(ps[definition]['text'])) and (start<=position<stop or any(norm(p['text']).startswith(text.rstrip('。')) for p in ps[start:stop])))")
s=s.replace("        self._v9_supplied_qualification_parent()", "        self._v9_supplied_qualification_parent()\n        self._v9_restricted_mother_boundary()")
s=s.replace("eligible=[c for t,c in parents.items() if re.search", "current=self._current_source()\n        if current is None:return\n        eligible=[c for t,c in parents.items() if self._se_parent_binding(c) and self._se_parent_binding(c).get('role_only_not_independent_source_verification') is False and re.search")
s=s.replace("heads=list(re.finditer(r'(?m)^[ \\t]*(\\d+)[.．][^\\n]+',block));matches=[h for h in heads if int(h.group(1))==number]", "heads=list(re.finditer(r'(?m)^[ \\t]*(\\d+)[.．][^\\n]+',block))\n        current_key=re.sub(r'^[（(][一二三四五六七八九十]+[）)]','',text).rstrip(';；。')\n        matches=[h for h in heads if re.sub(r'^\\d+[.．]','',norm(h.group()).strip()).rstrip(';；。')==current_key]")
s+='''
    def _v9_eligible_scope_topic(self, text, pattern):
        for part in re.split('[。；;\\n]',text):
            for match in re.finditer(pattern,part):
                before=part[:match.start()].split(',')[-1].split('，')[-1]
                after=part[match.end():].split(',')[0].split('，')[0]
                if re.search('不适用于?|不包括|不包含|排除|不要求',before) or re.match(r'[^。；;]{0,8}(?:不适用|不得申请|被排除)',after):continue
                return True
        return False

    def _v9_restricted_mother_boundary(self):
        if not (re.search('一并',self.norm) and re.search('优先审评',self.norm)):return
        current=self._current_source()
        if current is None or current['source_ref']['sha256']!=self.unit.get('source_ref',{}).get('sha256'):return
        body=norm(current.get('text',''))
        if not ('附条件批准' in body and self.norm in body):return
        if re.search('创新药|改良型新药|短缺药品|无有效治疗',self.norm):return
        dims=['I'] if '沟通' in self.norm else ['I','F']
        self._v9_emit([self._quote(current,'当前完整母段限定附条件批准品种及一并优先操作')],'restricted_mother_unclosed',dims,'当前确切母段已收窄附条件批准对象，尚无相应创新/需要分支交叉证明',current_mother_scope=body,current_operation=self.norm)
'''
p.write_text(s)
p=C/'dimensions.py';s=p.read_text();s=s.replace("            for d in ('I','F'):\n                acc.boundary", "            for d in details['affected_dimensions']:\n                acc.boundary");p.write_text(s)
p=C/'run_finite_controls.py';s=p.read_text();s=s.replace("extra=[O/'supplemental-controls-before-attempt02.json',O/'supplemental-controls-b-before-attempt02.json']", "extra=[O/'supplemental-controls-before-attempt02.json',O/'supplemental-controls-b-before-attempt02.json',O/'supplemental-controls-before-attempt04.json']");p.write_text(s)
