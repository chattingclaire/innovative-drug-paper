"""Only metadata address parsing; original source text and geometry stay intact."""
from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'relations.py';text=p.read_text()
def replace(old,new):
    global text
    assert old in text,old
    text=text.replace(old,new)
start=text.index('def clause_number(value):');end=text.index('\nclass SourceDependencyStop',start)
text=text[:start]+'''def structure_ordinal(value, suffix):
    """Parse an address scalar, never original text or a closure proof."""
    if type(value) is int:
        return value if value >= 1 else None
    if type(value) is not str:
        return None
    label = re.fullmatch('(?:第)?(' + ORDINAL + ')(?:' + suffix + ')?', norm(value))
    number = ordinal_number(label.group(1)) if label else None
    return number if number is not None and number >= 1 else None

def article_number(value):
    return structure_ordinal(value, '条')

def clause_number(value):
    return structure_ordinal(value, '款')
''' +text[end:]
replace('        self.material_requests = []\n        self.relations = []','        self.material_requests = []\n        self.structural_address_issues = []\n        self.relations = []')
start=text.index('    def _supplied_clause_number(self, context):');end=text.index('    def _se_clause_proof',start)
text=text[:start]+'''    def _supplied_address(self, context):
        """Raw metadata stays unchanged; invalid/conflicting addresses cannot bind.

        Legal integer/text ordinals are matched against any actual source head.
        Missing heads do not become quotes or prove a complete article/clause.
        """
        st=context.get('structure',{})
        errors=[];values={'article':None,'clause':None}
        for field, parser in (('article',article_number),('clause',clause_number)):
            if field not in st or st[field]=='':
                continue
            value=parser(st[field])
            if value is None:
                errors.append({'field':field,'reason':'illegal_type_or_ordinal_format','metadata_type':type(st[field]).__name__,'metadata_value':st[field]})
            values[field]=value
        if 'clause_index_one_based' in st:
            index=clause_number(st['clause_index_one_based'])
            if index is None:
                errors.append({'field':'clause_index_one_based','reason':'illegal_type_or_ordinal_format','metadata_type':type(st['clause_index_one_based']).__name__,'metadata_value':st['clause_index_one_based']})
            elif values['clause'] is not None and values['clause']!=index:
                errors.append({'field':'clause','reason':'clause_label_index_conflict','metadata_value':st.get('clause'),'index_value':st['clause_index_one_based']})
            else:
                values['clause']=index
        literal=re.match(ARTICLE_REFERENCE,norm(context.get('text','')))
        literal_article=ordinal_number(literal.group(1)) if literal else None
        literal_clause=ordinal_number(literal.group(2)) if literal and literal.group(2) else None
        if literal_article is not None and values['article'] is not None and literal_article!=values['article']:
            errors.append({'field':'article','reason':'metadata_original_heading_conflict','metadata_number':values['article'],'original_number':literal_article})
        if literal_clause is not None:
            if values['clause'] is not None and literal_clause!=values['clause']:
                errors.append({'field':'clause','reason':'metadata_original_heading_conflict','metadata_number':values['clause'],'original_number':literal_clause})
            elif values['clause'] is None:
                values['clause']=literal_clause
        if errors:
            issue={'kind':'context_structure_address','context_id':context.get('context_id'),'source_ref':context.get('source_ref'),
                   'errors':errors,'original_literal_address':literal.group() if literal else None,'original_article_number':literal_article,'metadata_number_used_as_quote':False}
            if issue not in self.structural_address_issues:
                self.structural_address_issues.append(issue)
        return dict(values,valid=not errors,errors=errors,original_article=literal_article,original_clause=literal_clause)

    def _supplied_article_number(self, context):
        value=self._supplied_address(context)
        return value['article'] if value['valid'] else None

    def _supplied_clause_number(self, context):
        value=self._supplied_address(context)
        return value['clause'] if value['valid'] else None

    def _supplied_group_article_number(self, group):
        number=article_number(group.get('article',''))
        if number is None and 'article' in group and group['article']!='':
            issue={'kind':'ordered_article_group_address','field':'article','metadata_value':group['article'],'metadata_type':type(group['article']).__name__,
                   'reason':'illegal_type_or_ordinal_format','ordered_source_resource_ids':group.get('ordered_source_resource_ids',[]),'metadata_number_used_as_quote':False}
            if issue not in self.structural_address_issues:
                self.structural_address_issues.append(issue)
        return number

''' +text[end:]
replace("            label = re.fullmatch(ARTICLE_REFERENCE, norm(st.get('article', '')))\n", "            article = self._supplied_article_number(c)\n")
replace("            if not label or ordinal_number(label.group(1)) != number or self._supplied_clause_number(c) != clause + 1:", "            if article != number or self._supplied_clause_number(c) != clause + 1:")
replace("                match = re.fullmatch(ARTICLE_REFERENCE, norm(c.get('structure', {}).get('article', '')))\n                if match and ordinal_number(match.group(1)) == number:", "                address = self._supplied_address(c)\n                if address['valid'] and address['article'] == number:")
replace("                self.material_requests.append({'path': 'cited_standard', 'reference': f'当前操作性第{number}条' + (f'第{clause}款' if clause else '') + '条件', 'missing': '该确指同版条/款的完整原文及原件末边界未唯一核明；不从已供编号/句号闭合或扩为整条', 'dimensions': ['S', 'E', 'Ec']})", "                issues=[issue for issue in self.structural_address_issues if issue.get('original_article_number') in (None,number)]\n                self.material_requests.append({'path': 'cited_standard', 'reference': f'当前操作性第{number}条' + (f'第{clause}款' if clause else '') + '条件', 'missing': '该确指同版条/款的完整原文及原件末边界未唯一核明；不从已供编号/句号闭合或扩为整条' + ('；已供结构编号非法或与原文矛盾，须核正该引用源定位' if issues else ''), 'dimensions': ['S', 'E', 'Ec'], **({'structural_address_issues':issues} if issues else {})})")
replace("    def _se_article_proof(self, members, number):\n        for container", "    def _se_article_proof(self, members, number):\n        if any(not self._supplied_address(c)['valid'] or (self._supplied_article_number(c) is not None and self._supplied_article_number(c)!=number) for c in members):\n            return None\n        for container")
replace("                if not h or ordinal_number(h.group(1)) != number + 1 or c['source_ref']['sha256'] != last['source_ref']['sha256']:", "                if not h or ordinal_number(h.group(1)) != number + 1 or not self._supplied_address(c)['valid'] or c['source_ref']['sha256'] != last['source_ref']['sha256']:")
replace("            raw = child.get('text', '')\n            for match", "            if not self._supplied_address(child)['valid']:\n                return []\n            raw = child.get('text', '')\n            for match")
replace("            bounded.append(member)\n        return bounded", "            metadata_article=self._supplied_article_number(member[0])\n            if metadata_article is not None and metadata_article!=article:\n                return []\n            bounded.append(member)\n        return bounded")
replace("                heading = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))\n                if not heading or ordinal_number(heading.group(1)) != article:", "                group_article = self._supplied_group_article_number(group)\n                if group_article != article:")
replace("                    if st.get('article') != group['article'] or st.get('clause_index_one_based') != position or (not c.get('text')):", "                    if self._supplied_article_number(c) != group_article or self._supplied_clause_number(c) != position or (not c.get('text')):")
replace("                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))\n                if not h:\n                    continue\n                article = ordinal_number(h.group(1))", "                article = self._supplied_group_article_number(group)\n                if article is None:\n                    continue")
replace("                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))\n                if not h:\n                    continue\n                donors = self._reference_candidates(current, ordinal_number(h.group(1)))", "                group_article = self._supplied_group_article_number(group)\n                if group_article is None:\n                    continue\n                donors = self._reference_candidates(current, group_article)")
replace("                            bridges.append((ordinal_number(h.group(1)), donors[0][0], item))", "                            bridges.append((group_article, donors[0][0], item))")
replace("                h = re.fullmatch(ARTICLE_REFERENCE, group.get('article', ''))\n                if h and ordinal_number(h.group(1)) in articles:", "                group_article = self._supplied_group_article_number(group)\n                if group_article in articles:")
assert "norm(st.get('article'" not in text
assert "norm(c.get('structure', {}).get('article'" not in text
assert "re.fullmatch(ARTICLE_REFERENCE, group.get('article'" not in text
p.write_text(text)
print('Only candidate relations.py structural address parsing edited.')
