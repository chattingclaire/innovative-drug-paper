from pathlib import Path
p=Path(__file__).resolve().parent;r=(p/'relations.py').read_text()
a=r.index('    def _bounded_IF_right_operation(self):');b=r.index('    def _bounded_IF_individual_consultation(self):',a)
r=r[:a]+'''    def _bounded_IF_right_operation(self):
        """Qualified scope of this right, never another article's drug/right."""
        if re.search(r'原研药品|仿制药',self.norm) and not re.search(r'创新药|改良型新药',self.norm):
            return
        current=self._current_source()
        current_text=norm(current.get('text','')) if current else self.norm
        right_match=re.search(r'(?:药品试验)?数据保护|市场独占',self.norm)
        operation=re.search(r'申请|给予|享受|实施保护|保护是指|终止|限制|不予许可|不予受理|不受理|不批准',self.norm)
        anaphor=bool(re.search(r'依赖[^。；;]{0,20}(?:该|受|保护)[^。；;]{0,12}数据',self.norm)
                     and re.search(r'(?:药品试验)?数据保护',current_text))
        if (not right_match and not anaphor) or not operation:
            return
        right=right_match.group() if right_match else re.search(r'(?:药品试验)?数据保护',current_text).group()
        right=re.search(r'数据保护|市场独占',right).group()
        primary=self.unit.get('source_ref',{}).get('sha256')
        def article(c):
            if not c:return None
            for container in (c.get('structure',{}),c.get('source_ref',{}).get('locator',{})):
                if container.get('article_id') is not None:return container['article_id']
            literal=re.match(r'^第'+ORDINAL+r'条',norm(c.get('text','')))
            return literal.group() if literal else None
        current_article=article(current)
        # A general definition/express general qualification applies the same
        # right's finite definitions; a particular drug's bare anaphor does not.
        general_bridge=bool(re.search(re.escape(right)+r'是指|符合[^。；;]{0,30}给予[^。；;]{0,20}'+re.escape(right)+r'条件',current_text))
        own_ordinary=bool(re.search(r'(?:本条|该|本)(?:普通)?药品[^。；;]{0,35}(?:一般资料保密|一般数据保密|普通药品)|本条普通药品',current_text))
        definitions=[];blocked=[]
        for c in self.contexts:
            if c.get('source_ref',{}).get('sha256')!=primary or c['kind'] not in {'source_resource_text','source_paragraph'}:
                continue
            if current and not same_component(c,current):continue
            raw=c.get('text','')
            for a,b in sentence_spans(raw):
                part=norm(raw[a:b])
                # The category, specific right and grant/scope must be in this
                # very definition proposition, not scattered across one resource.
                if not (right in part and re.search(r'创新药|改良型新药|改良型药品',part)
                        and re.search(r'给予|享受|实施保护|数据保护期|保护范围',part)):
                    continue
                if re.search(r'另一(?:条|种|个)?|其他(?:药品|药物|创新药|保护)',part) and not re.search(r'创新药|改良型新药',self.norm):
                    blocked.append({'reason':'definition expressly belongs to another drug/right','context_id':c['context_id']});continue
                source_article=article(c)
                conflict=current_article is not None and source_article is not None and current_article!=source_article
                if conflict and not general_bridge:
                    blocked.append({'reason':'different original article without a direct general qualification bridge','context_id':c['context_id'],'current_article':current_article,'definition_article':source_article});continue
                if own_ordinary and not re.search(r'创新药|改良型新药',self.norm):
                    continue
                definitions.append(self._quote(c,'当前同一权利及同一资格对象的有限创新/改良—权利后果定义',(a,b)))
        if definitions:
            self._add('named_mechanism',definitions,'当前实际操作同一权利，同版有限定义直接给出对应创新/改良资格与后果；不同药品、条款或保护类型不混接',
                      relation_subtype='bounded_IF_qualified_right_operation',object_definition='\\n'.join(e['text']for e in definitions),
                      current_right_name=right,source_sha256=primary,only_IF_consumers=True,
                      affected_dimensions=['I'],right_scope_binding={'current_article':current_article,'general_qualification_bridge':general_bridge,'one_definition_proposition_required':True,'blocked_alternative_definitions':blocked})
        elif blocked and not own_ordinary and re.search(r'本条药品|该药品|该药物|受保护数据',self.norm):
            request={'path':'named_mechanism','reference':self.text,'current_text':self.text,
                     'missing':'当前药品同一权利的资格/数据指代未核明；已供创新定义定位属于不同条款或对象，不能借用',
                     'stop_reason':'qualified_right_object_origin_unresolved','dependency_status':'stopped',
                     'affected_dimensions':['I'],'blocked_alternative_definitions':blocked}
            self.material_requests.append(request);self.source_requests.append(request.copy())

''' +r[b:]
# A resolved qualification receipt is evidence of exact closure, not permission
# to discard any old unresolved request concerning another dependency.
s="""            self._bounded_primary_support_roles(completion, same_source)"""
t="""            self.source_requests.append({'path':'cited_standard','reference':self.text,
                'current_text':self.text,'dependency_status':'resolved',
                'resolution_path':'primary_literal_complete_operative_standard',
                'same_primary_source_sha256':completion['source_sha256'],
                'programme_name':completion['programme_name'],'standard_family':completion['standard_family'],
                'selected_group_snapshot_span':completion['selected_group_snapshot_span'],
                'selected_leaf_spans':completion['selected_leaf_spans'],
                'seed_context_ids':[c['context_id'] for c in same_source],
                'original_structural_seed_ids':[c['context_id'] for c in same_source if c['context_id'] in related],
                'seed_interface':'supplied structural relation or exact literal operative condition introduction in the same closed programme',
                'evidence':completion['evidence'],'no_new_material':True,
                'other_unresolved_requests_retained':True})
            self._bounded_primary_support_roles(completion, same_source)"""
assert s in r;r=r.replace(s,t,1)
(p/'relations.py').write_text(r)
