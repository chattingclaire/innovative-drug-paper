from pathlib import Path
C=Path(__file__).parent;p=C/'relations.py';s=p.read_text();s=s.replace("elif technical or substantive_application or termination:","elif technical or substantive_application or termination or re.search('即纳入|同意纳入',text):")
s=s.replace("or re.search('评估[^。；;]{0,25}适用范围和适用条件',text):", "or re.search('评估[^。；;]{0,25}适用范围和适用条件|情形和适用条件[^。；;]{0,15}详细阐述',text):")
s=s.replace("        self._v9_right_object_filter()", "        self._v9_right_object_filter()\n        self._v9_qualified_exact_table_row()")
s+='''
    def _v9_qualified_exact_table_row(self):
        if '|' not in self.norm:return
        cells=[norm(x).strip() for x in self.text.split('|')];primary=self.unit.get('source_ref',{}).get('sha256')
        if len(cells)!=4:return
        for row in self.contexts:
            if row['kind']!='table_row' or row['source_ref']['sha256']!=primary:continue
            rc=[norm(x).strip() for x in row.get('row_cells',[])];headers=row.get('headers',[]);pairs=row.get('structure',{}).get('row_cell_column_pairs',[])
            if rc!=cells or len(headers)!=4 or len(pairs)!=4:continue
            if any(p.get('cell_index')!=i or p.get('header_index')!=i or p.get('column_index')!=i for i,p in enumerate(pairs)):continue
            if not re.search('创新(?:型)?(?:药|疫苗|生物制品)|改良型(?:新药|药品|疫苗|生物制品)',rc[1]):continue
            if not re.search('数据保护期|保护期限',norm(headers[2])) or not re.search(r'\\d+年|给予数据保护',rc[2]+' '+rc[3]):continue
            selected=[c for c in self.contexts if c['source_ref']['sha256']==primary and c.get('structure',{}).get('parent_context_id')==row['context_id'] and c['kind'] in {'table_row_cell','table_header_cell'}]
            if len(selected)!=8:continue
            self._v9_emit([self._quote(c,'当前明文创新/改良内容与精确保护待遇列的同一行几何') for c in selected],'current_exact_qualified_table_right',['I'],'当前确切表行明文创新/改良资格决定实质保护待遇；不从裸分类号或裸年数推定',current_row=rc,current_headers=headers,current_row_geometry=row['structure'])
'''
p.write_text(s)
p=C/'dimensions.py';s=p.read_text();start=s.index("    if '|' in text:",s.index('def _v9_current_candidates'));end=s.index('\ndef _v9_IF_consume',start);s=s[:start]+s[end:]
start=s.index('    technical_content=',s.index('def _v9_current_candidates'))
s=s[:start]+'''    if re.search('药品',text) and re.search('(?:创新性|公平性)[^。；;]{0,15}(?:方面的)?信息',text) and re.search('公示|公开|披露',text):
        for dim,topic in [('I','创新性'),('F','公平性')]:
            if topic in text:
                acc.add(dim,unit,'v9_current_explicit_dimension_information','当前公示药品对应维度的实质信息内容；不是字段非空、普通名单或一般程序公平。',obj,{'current_explicit_content_dimension':topic,'operation':'公示/公开实际维度信息'})
''' +s[start:]
s+='''
'''
# Complete current causal treatment opportunity may cross semicolons; both the
# no-treatment target and same enrolled subjects are explicit in this record.
s=s.replace("    for match in re.finditer('[^。；;]+',view.norm):", "    if re.search('无药可治',view.norm) and re.search('入组的受试者均能接受试验治疗',view.norm) and re.search('因此',view.norm) and not re.search('其他(?:药品|药物|试验)|另一(?:药品|药物|试验)',view.norm):\n        _v9_current_candidates(acc,view,Unit(view.norm,0,len(view.norm)))\n    for match in re.finditer('[^。；;]+',view.norm):")
p.write_text(s)
