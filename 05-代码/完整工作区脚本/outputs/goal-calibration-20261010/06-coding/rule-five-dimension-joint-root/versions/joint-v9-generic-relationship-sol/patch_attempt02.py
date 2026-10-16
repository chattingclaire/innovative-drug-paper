from pathlib import Path
import json
C=Path(__file__).parent;entry=json.loads((C/'impact-contract-amendment-before-attempt02.json').read_text())['entry_regex']
for n in ['relations','dimensions','select_static_impact']:
 p=C/(n+'.py');s=p.read_text();start=s.index('V9_REPAIR_ENTRY =');end=s.index('\n',start);s=s[:start]+'V9_REPAIR_ENTRY = '+repr(entry)+s[end:];p.write_text(s)
p=C/'relations.py';s=p.read_text()
s=s.replace("else 2\n            for line in raw[b:ca].splitlines():", "else None\n            if literal_level is None:\n                prior=list(re.finditer(r'(?m)^[ \\t]*(?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)]|\\d+[.．]|[（(]\\d+[）)])',raw[lo:a]))\n                token=norm(prior[-1].group()).strip() if prior else ''\n                literal_level=1 if re.match(r'^[一二三四五六七八九十]+、',token) else 2 if re.match(r'^[（(][一二三四五六七八九十]+[）)]',token) else 3 if re.match(r'^\\d+[.．]',token) else 4 if re.match(r'^[（(]\\d+[）)]',token) else 1\n            for line in raw[b:ca].splitlines():")
s=s.replace("            if len(names)!=1:continue\n", "            if not names:continue\n")
s=s.replace("            group=paragraphs[start:stop];body=norm('\\n'.join(p['text'] for p in group));name=next(iter(names))", "            group=paragraphs[start:stop];body=norm('\\n'.join(p['text'] for p in group))\n            qualified_names=set(re.findall('“([^”]{2,30})”试点工作',body))\n            if len(qualified_names)!=1:continue\n            name=next(iter(qualified_names))\n            current_named=set(re.findall('“([^”]{2,30})”(?:试点工作|试点项目|项目)',self.norm))\n            if current_named and current_named!={name}:continue")
s=s.replace("            if len(current)!=1:continue\n            contexts={}", "            if len(current)!=1 and cp:\n                pages=cp.get('structure',{}).get('pages',cp.get('source_ref',{}).get('locator',{}).get('physical_pages',[]))\n                located=[i for i in current if set(pages).intersection(paragraphs[i].get('physical_pages',[]))]\n                if len(located)==1:current=located\n            if len(current)!=1:continue\n            contexts={}")
# More exact substantive technical service forms already tied to same component.
s=s.replace("(?:对|针对)纳入[^。；;]{0,45}(?:优先|沟通|咨询|反馈|核查|检验)',text)","(?:对|针对)纳入[^。；;]{0,45}(?:优先|沟通|咨询|反馈|核查|检验)|(?:应|应当)优先进行(?:核查|检验)|核查、检验[^。；;]{0,12}优先',text)")
# Actual admission is substantive even when the same sentence also gives notice.
s=s.replace("not re.search('签章|收件|通知|网站|附件|不再接受|一并',text)","not re.search('签章|收件|网站|不再接受|一并',text)")
s=s.replace("(named_general and (technical or substantive_application))", "(named_general and (technical or substantive_application or bool(re.search('即纳入|同意纳入',text))))")
s=s.replace("            elif substantive_application:\n", "            elif substantive_application or re.search('即纳入|同意纳入',text):\n")
# _v9_bounded_relationships retains only additive calls, no old paths changed.
s=s.replace("        self._v9_structured_plan()\n", "        self._v9_structured_plan()\n        self._v9_supplied_qualification_parent()\n")
s+='''
    def _v9_supplied_qualification_parent(self):
        primary=self.unit.get('source_ref',{}).get('sha256')
        parents={norm(c.get('text','')):c for c in self.contexts if c['kind']=='parent_paragraph' and c['source_ref']['sha256']==primary and same_component(c,self._current_source() or c)}
        # A mandatory innovative trial object is inherited only as the direct
        # predicate of a substantive qualification member, never a disease label.
        eligible=[c for t,c in parents.items() if re.search('纳入[^。；;]{0,30}(?:通道|试点)',t) and re.search('1类创新药临床试验',t) and re.search('满足以下条件之一',t)]
        member=bool(re.search('重点创新药|儿童创新药|罕见病创新药|中药创新药|全球同步研发|国际多中心临床试验',self.norm))
        if len(eligible)==1 and member:
            self._v9_emit([self._quote(eligible[0],'当前成员直接父句明文限定1类创新临床对象及通道准入后果')],'direct_innovative_trial_qualification_member',['I'],'当前实质创新临床准入成员承接直接父句的对象及后果；非兄弟条件',current_member=self.norm,direct_parent=eligible[0]['text'])
'''
p.write_text(s)
p=C/'dimensions.py';s=p.read_text()
a=s.index('    innovation=re.search(INNOVATION_OBJECT,text)',s.index('def _v9_current_candidates'));b=s.index('    technical_content=',a)
s=s[:a]+'''    innovation=re.search(INNOVATION_OBJECT,text)
    distinct=bool(re.search('其他(?:药品|药物|项目)|另一(?:药品|药物|项目)',text))
    # Bind service recipient, action and innovation in their actual grammatical
    # role. Innovation mentioned elsewhere cannot donate its beneficiary.
    allocation=re.search(r'(?:审评审批资源|审评资源)[^，,。；;]{0,12}(?:向|对)(?P<object>[^，,。；;]{0,20}(?:'+INNOVATION_OBJECT+r')[^，,。；;]{0,18})(?:倾斜|配置)',text)
    direct=re.search(r'(?:对|向|为|针对)(?P<object>[^，,。；;]{0,15}(?:'+INNOVATION_OBJECT+r')[^，,。；;]{0,18}(?:研发|临床试验申请))(?P<bridge>[^。；;]{0,35})(?P<service>(?:提供|给予|安排|开放|撤回|不再提供)[^。；;]{0,25}(?:研究方案反馈|技术指导|研究反馈)|(?:在)?受理后\\d+个工作日内完成审评审批)',text)
    service=allocation or direct
    if direct and re.search('常规药|仿制药|药品[甲乙丙]|药物[甲乙丙]|创新药[甲乙丙]',direct.group('bridge')):service=None
    if innovation and service and not distinct:
        acc.add('I',unit,'v9_I3_current_explicit_RND_arrangement','当前明确创新研发对象与具体反馈、资源倾斜或临床申请办理便利直接相连；当前并非普通通知/签章。',obj,{'current_object':service.group('object'),'actual_arrangement':service.group(),'relationship_proof':'actual service beneficiary syntax; innovation elsewhere cannot donate beneficiary'})
    qualification=bool(innovation and re.search('(?:依申请纳入|将依申请纳入|范围为|给予|撤回)[^。；;]{0,30}(?:\\d+日通道|数据保护)|(?:试点项目|试点|计划)范围为[^。；;]{0,20}创新药[^。；;]{0,30}临床试验申请',text))
    comparison=bool(innovation and re.search('(?:相对|相比|与)[^。；;]{0,20}现有治疗[^。；;]{0,20}(?:临床优势|显著改善)',text) and re.search('可申请|可以申请|纳入',text))
    rights=bool(innovation and re.search('(?:给予|撤回|限制|终止)[^。；;]{0,30}数据保护',text))
    if qualification or comparison or rights:
        acc.add('I',unit,'v9_I4_current_explicit_qualification_consequence','当前明文创新对象的技术比较资格、准入或权利后果直接成立；真实限制仍为该对象议题。',obj,{'current_qualification_and_consequence':text})
''' +s[b:]
s=s.replace("克服耐药|新(?:剂型|规格)","克服[^。；;]{0,12}耐药|新(?:剂型|规格)")
s=s.replace("(?:耐药|现有[^。；;]{0,20}(?:均不适用|不适用|局限))", "(?:耐药|吞咽能力|现有[^。；;]{0,20}(?:均不适用|不适用|局限))")
s=s.replace("开发[^。；;]{0,15}(?:剂型|给药)","开发[^。；;]{0,20}(?:剂型|给药)")
a=s.index('    if gap and arrangement and not form and not distinct:',s.index('def _v9_current_candidates'))
s=s[:a]+'''    denied_identity=bool(gap and re.search('并非|不是|并不存在|不存在|不属于',text[max(0,gap.start()-12):gap.start()]))
    alternate_cause=bool(gap and arrangement and re.search('(?:凭|因|基于)[^。；;]{0,15}(?:临床|治疗)优势|不因该(?:资格|需要)',text[gap.end():arrangement.start()]))
    real_negative_qualification=bool(gap and re.search('不符合|不满足',text[max(0,gap.start()-15):gap.start()]) and re.search('条件|资格',text[gap.end():]) and re.search('不得|不予|不能',text))
''' +s[a:]
s=s.replace('    if gap and arrangement and not form and not distinct:', '    if gap and arrangement and not form and not distinct and not alternate_cause and (not denied_identity or real_negative_qualification):')
# Withdrawal filters must inspect each candidate anchor/object, not basis path alone.
s=s.replace("                if positive['basis_path'] in targets:\n                    removed.append(positive)\n", "                anchor_text=_norm(positive.get('current_anchor',{}).get('text',''))\n                explicit_other_valid_right=bool(re.search('(?:创新药|改良型新药)[^。；;]{0,30}(?:持有人|数据)|(?:未经|依赖)[^。；;]{0,35}(?:创新药|改良型新药)',anchor_text) and re.search('受保护|给予[^。；;]{0,15}保护|不予许可',anchor_text))\n                same_current_object=(anchor_text==view.norm or anchor_text.rstrip('。;；')==view.norm.rstrip('。;；'))\n                if positive['basis_path'] in targets and same_current_object and not explicit_other_valid_right:\n                    removed.append(positive)\n")
a=s.index('    for match in re.finditer',s.index('def _v9_IF_consume'))
s=s[:a]+'''    # Current unrestricted all-fields application is not a need-selected
    # beneficiary. Only this old generic allocation candidate is withdrawn.
    if re.search('不限定申报药品的治疗领域[^。；;]{0,20}满足各治疗领域用药需求',view.norm) and not re.search('短缺|保障空白|保障还不充分|无有效|未满足',view.norm):
        acc.positive['F']=[p for p in acc.positive['F'] if not (p['basis_path']=='F_different_treatment_needs_open_opportunity' and _norm(p.get('current_anchor',{}).get('text','')).rstrip('。')==view.norm.rstrip('。'))]
        acc.excluded['F'].append('v9当前机会面向全部治疗领域，未因真实差异需要选择对象；不借下一独立句的保障缺口豁免。')
''' +s[a:]
p.write_text(s)
p=C/'run_finite_controls.py';s=p.read_text();s=s.replace("raw=json.loads(fixed.read_bytes());synthetics=json.loads(syn.read_bytes())", "raw=json.loads(fixed.read_bytes());synthetics=json.loads(syn.read_bytes())\nextra=[O/'supplemental-controls-before-attempt02.json',O/'supplemental-controls-b-before-attempt02.json']\nfor path in extra:synthetics['cases'].extend(json.loads(path.read_bytes())['cases'])")
s=s.replace("'controls':[bind(fixed),bind(syn)]", "'controls':[bind(fixed),bind(syn)]+[bind(p) for p in extra]");p.write_text(s)
