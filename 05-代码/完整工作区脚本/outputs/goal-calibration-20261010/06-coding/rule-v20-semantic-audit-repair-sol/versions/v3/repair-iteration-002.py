from pathlib import Path
p=Path(__file__).resolve().parent;r=(p/'relations.py').read_text();d=(p/'dimensions.py').read_text()
def ch(s,a,b):
 if a not in s:raise ValueError(a[:80])
 return s.replace(a,b,1)
r=ch(r,"current_classes = set(re.findall(r'([\\u4e00-\\u9fff]{1,8}类)项目',text))", "def object_classes(part):\n            return set(re.findall(r'(?:^|[的和及、，,；;：:])([^\\W_]{1,8}类)(?=项目|和|及|、)',part))\n        current_classes = object_classes(text)")
r=ch(r,"classes = set(re.findall(r'([\\u4e00-\\u9fff]{1,8}类)项目',part))", "classes = object_classes(part)")
r=ch(r,'            qualified_list=False','            qualified_list=closure in {\'closed_applicability_component\',\'quoted_name_qualification_and_current_service\'}')
r=ch(r,"or re.search(r'[\\u4e00-\\u9fff]{1,8}类项目为',part))", "or re.search(r'[\\u4e00-\\u9fff]{1,8}类项目为',part)\n                             or re.search(r'(?:药品|药物|项目)[^。；;]{0,15}(?:可|可以)申请[^。；;]{0,15}(?:本|该)程序',part))")
r=ch(r,"(?:不能满足|不符合|不满足)[^。；;]{0,35}(?:程序|计划|通道|试点)","(?:不能满足|不符合|不满足)[^。；;]{0,35}(?:审评审批|审评|程序|计划|通道|试点)")
d=ch(d,'    "named_mechanism": ("I", "F"),','    "named_mechanism": ("I", "F"),\n    "parent_predicate": ("I", "F"),')
d=ch(d,'REQUEST_ROUTING_VERSION = "relation-consumer-routing-2-with-price-content"','REQUEST_ROUTING_VERSION = "relation-consumer-routing-3-local-parent-origin-conflict"')
d=ch(d,'action = re.search(r"可|应|自愿申报|审评时限为|完成|保持|维持|退出|终止|撤回|不再|协助|决定|组织|设立|开展|提供", text)','action = re.search(r"可|应|自愿申报|审评时限为|完成|保持|维持|退出|终止|撤回|不再|协助|决定|组织|设立|开展|提供|安排|反馈", text)')
# Current-question anaphor can be supplied by its immediate containing sentence,
# with an actual document-purpose predicate. Incidental archive aliases cannot.
a=r.index('                definition=re.search',r.index('    def _bounded_IF_individual_consultation'));b=r.index('                obj=self._quote',a)
r=r[:a]+'''                definition=re.search(r'(?P<name>[A-Za-z][A-Za-z0-9]{1,16})是[^。；;]{0,30}临床试验',part)
                reference_span=None
                referent=False
                if definition:
                    alias=definition.group('name')
                    referent=bool(re.search(re.escape(alias)+r'[^。；;，,]{0,15}(?:未能阐明|未涵盖|未解决)',self.norm))
                    raw=container.get('text','')
                    starts=[m.start() for m in re.finditer(re.escape(self.text),raw)]
                    if not referent and len(starts)==1 and re.match(r'如有|对于未|对于该|对于本',self.norm):
                        preceding=sentence_spans(raw[:starts[0]])
                        if preceding:
                            lo,hi=preceding[-1];previous=norm(raw[lo:hi])
                            referent=bool(re.search(r'(?:本|该)(?:指导原则|技术文档)[^。；;]{0,15}(?:撰写|编制|涉及)'+re.escape(alias)+r'[^。；;]{0,35}(?:未|不能|尚不能)[^。；;]{0,12}(?:涵盖|阐明|解决)',previous))
                            if referent:reference_span=(lo,starts[0]+len(self.text))
                if (c['kind']!='parent_paragraph' or c.get('source_ref',{}).get('sha256')!=primary
                        or cs.get('unit_id')!=uid or cs.get('sequence_index')!=index-1
                        or not definition or not referent
                        or not same_component(c,current)
                        or not re.search(r'创新药[^。；;]{0,20}临床试验',part)):
                    continue
''' +r[b:]
r=ch(r,"service=self._quote(container,'该技术文档未涵盖问题的实际药审机构沟通入口')","service=self._quote(container,'当前问题直接承接的同一技术文档及实际药审机构沟通入口',reference_span)")
(p/'relations.py').write_text(r);(p/'dimensions.py').write_text(d)
