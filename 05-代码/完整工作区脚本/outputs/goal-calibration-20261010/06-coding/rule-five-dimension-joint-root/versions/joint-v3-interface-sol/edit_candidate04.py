"""Reconcile supplied/literal clause labels and finite topic-qualified consumers."""
import ast
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'relations.py';t=R.read_text()
marker='    def _se_clause_proof(self, members, number, clause):'
helper='''    def _supplied_clause_number(self, context):
        """Normalize supplied labels and reject contradictory literal headings."""
        st=context.get('structure',{})
        value=clause_number(st.get('clause',''))
        index=st.get('clause_index_one_based')
        if type(index) is int and index>=1:
            if value is not None and value!=index:
                return None
            value=index
        literal=re.match(ARTICLE_REFERENCE,norm(context.get('text','')))
        article=re.fullmatch(ARTICLE_REFERENCE,norm(st.get('article','')))
        if literal and article and ordinal_number(literal.group(1))!=ordinal_number(article.group(1)):
            return None
        if literal and literal.group(2):
            literal_clause=ordinal_number(literal.group(2))
            if value is not None and value!=literal_clause:
                return None
            value=literal_clause
        return value

'''
assert t.count(marker)==1;t=t.replace(marker,helper+marker)
a="clause_number(st.get('clause', '')) != clause + 1";assert t.count(a)==1;t=t.replace(a,"self._supplied_clause_number(c) != clause + 1")
a="clause_number(c.get('structure', {}).get('clause', '')) == clause";assert t.count(a)==1;t=t.replace(a,"self._supplied_clause_number(c) == clause")
start=t.index('    def _IF_operative_standard_consumers(');end=t.index('    def _IF_closed_operational_content(',start)
replacement='''    def _IF_operative_standard_consumers(self, reference=None, article=None, clause=None):
        """A direct topic qualifier bounds unknown standard consumers.

        Unqualified whole substantive conditions can contain any construct.
        A current efficacy-only evidence requirement does not make I/F unknown.
        These are consumer scopes, never inferred absent source contents.
        """
        if article is None and reference:
            parsed = re.search(ARTICLE_REFERENCE, norm(reference))
            if parsed:
                article=ordinal_number(parsed.group(1));clause=ordinal_number(parsed.group(2)) if parsed.group(2) else None
        topics='安全性|风险|有效性|疗效|效果|经济性|成本|价格|创新性|公平性'
        construct={'安全性':'S','风险':'S','有效性':'E','疗效':'E','效果':'E','经济性':'Ec','成本':'Ec','价格':'Ec','创新性':'I','公平性':'F'}
        sequence='(?:'+topics+')(?:[和及、与](?:'+topics+'))*'
        plain_article='第'+ORDINAL+'条(?:第'+ORDINAL+'款)?'
        matches=[]
        for match in re.finditer(ARTICLE_REFERENCE,self.norm):
            number=ordinal_number(match.group(1));part=ordinal_number(match.group(2)) if match.group(2) else None
            if article is not None and (number!=article or part!=clause):
                continue
            after=self.norm[match.end():]
            connected=re.match('(?:(?:和|及|与|、|,|，)'+plain_article+')+',after)
            offset=connected.end() if connected else 0
            after=after[offset:]
            qualifier=re.match('的?(?:本药|药品|药物|用药|治疗)?(?P<topics>'+sequence+')(?:实质)?(?:标准|条件|证据(?:要求)?|信息(?:要求)?)',after)
            if qualifier:
                values=[construct[x] for x in re.findall(topics,qualifier.group('topics'))]
                matches.append((values,match.end()+offset,match.end()+offset+qualifier.end()))
                continue
            before=self.norm[:match.start()]
            subject=re.search('(?P<topics>'+sequence+')(?:证据|信息)?(?:应当|必须|应|须)(?:满足|符合|达到|遵守|核验)[^。；;，,]{0,35}$',before)
            if subject:
                values=[construct[x] for x in re.findall(topics,subject.group('topics'))]
                matches.append((values,subject.start(),subject.end()))
                continue
            return {'dimensions':['I','F'],'basis':'current exact unqualified substantive article/clause; absent scope unknown, not all unrelated references','current_qualifier_anchor':None}
        if matches:
            dims=[d for d in ('I','F') if d in {v for values,_,_ in matches for v in values}]
            a=min(x[1] for x in matches);b=max(x[2] for x in matches)
            return {'dimensions':dims,'basis':'explicit current topic-qualified standard consumer; other dimensions are not inferred','current_qualifier_anchor':self.current_anchor(a,b)}
        return {'dimensions':['I','F'],'basis':'current exact whole section or unqualified substantive scope; no dimension content inferred from missing material','current_qualifier_anchor':None}

'''
t=t[:start]+replacement+t[end:];ast.parse(t);R.write_text(t)
print('Literal and supplied clause numbers reconciled; no source geometry bypass. Direct topic qualifiers retain finite consumer subsets.')
