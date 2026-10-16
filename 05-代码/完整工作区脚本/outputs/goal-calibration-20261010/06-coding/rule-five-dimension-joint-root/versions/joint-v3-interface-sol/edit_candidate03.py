"""Normalize supplied clause labels; retain source closure and consumer bounds."""
import ast
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'relations.py';text=R.read_text()
marker='class SourceDependencyStop(ValueError):'
helper='''def clause_number(value):
    """A supplied clause label may be 1, 一, 第一款; it is not a closure proof."""
    if type(value) is int:
        return value if value >= 1 else None
    label = re.fullmatch('(?:第)?(' + ORDINAL + ')(?:款)?', norm(str(value)))
    return ordinal_number(label.group(1)) if label else None

'''
assert text.count(marker)==1;text=text.replace(marker,helper+marker)
old="ordinal_number(str(c.get('structure', {}).get('clause', ''))) == clause";assert text.count(old)==1;text=text.replace(old,"clause_number(c.get('structure', {}).get('clause', '')) == clause")
old="ordinal_number(str(st.get('clause', ''))) != clause + 1";assert text.count(old)==1;text=text.replace(old,"clause_number(st.get('clause', '')) != clause + 1")
marker='    def _IF_closed_operational_content(self, operational_requests):'
helper='''    def _IF_operative_standard_consumers(self, reference=None, article=None, clause=None):
        """A direct topic qualifier bounds unknown standard consumers.

        Unqualified whole substantive conditions can contain any construct.
        A current efficacy-only evidence requirement does not make I/F unknown.
        These are consumer scopes, never inferred absent source contents.
        """
        if article is None and reference:
            parsed = re.search(ARTICLE_REFERENCE, norm(reference))
            if parsed:
                article=ordinal_number(parsed.group(1));clause=ordinal_number(parsed.group(2)) if parsed.group(2) else None
        matches=[]
        for match in re.finditer(ARTICLE_REFERENCE,self.norm):
            number=ordinal_number(match.group(1));part=ordinal_number(match.group(2)) if match.group(2) else None
            if article is not None and (number!=article or part!=clause):
                continue
            after=self.norm[match.end():]
            qualifier=re.match('的?(?:本药|药品|药物|用药|治疗)?(?P<topic>安全性|风险|有效性|疗效|效果|经济性|成本|价格|创新性|公平性)(?:实质)?(?:标准|条件|证据(?:要求)?|信息(?:要求)?)',after)
            if qualifier:
                topic=qualifier.group('topic')
                dimension={'安全性':'S','风险':'S','有效性':'E','疗效':'E','效果':'E','经济性':'Ec','成本':'Ec','价格':'Ec','创新性':'I','公平性':'F'}[topic]
                matches.append((dimension,match.end(),match.end()+qualifier.end()))
            else:
                return {'dimensions':['I','F'],'basis':'current exact unqualified substantive article/clause; absent scope unknown, not all unrelated references','current_qualifier_anchor':None}
        if matches:
            dims=[d for d in ('I','F') if d in {x[0] for x in matches}]
            a=min(x[1] for x in matches);b=max(x[2] for x in matches)
            return {'dimensions':dims,'basis':'explicit current topic-qualified standard consumer; other dimensions are not inferred','current_qualifier_anchor':self.current_anchor(a,b)}
        return {'dimensions':['I','F'],'basis':'current exact whole section or unqualified substantive scope; no dimension content inferred from missing material','current_qualifier_anchor':None}

'''
assert text.count(marker)==1;text=text.replace(marker,helper+marker)
old="            shared = {key:value for key,value in details.items() if key not in {'affected_dimensions','only_IF_consumers','relation_subtype'}}"
new="            consumer_scope=self._IF_operative_standard_consumers(article=details.get('reference_article'),clause=details.get('reference_clause'))\n            if not consumer_scope['dimensions']:\n                continue\n"+old
assert text.count(old)==1;text=text.replace(old,new)
old="shared.update(relation_subtype='IF_closed_operational_content', affected_dimensions=['I','F'], only_IF_consumers=True, neutral_closure_reused_from=details['relation_subtype'], scope_is_not_dimension_label=True)"
new="shared.update(relation_subtype='IF_closed_operational_content', affected_dimensions=consumer_scope['dimensions'], only_IF_consumers=True, neutral_closure_reused_from=details['relation_subtype'], scope_is_not_dimension_label=True, current_operative_consumer_scope=consumer_scope)"
assert text.count(old)==1;text=text.replace(old,new)
old="'affected_dimensions':['I','F'],'closure_proof':details.get('closure_proof')";assert text.count(old)==1;text=text.replace(old,"'affected_dimensions':consumer_scope['dimensions'],'current_operative_consumer_scope':consumer_scope,'closure_proof':details.get('closure_proof')")
old="            request = dict(original)\n";new="            consumer_scope=self._IF_operative_standard_consumers(reference=original.get('reference'))\n            if not consumer_scope['dimensions']:\n                continue\n"+old;assert text.count(old)==1;text=text.replace(old,new)
old="request.update(dimensions=['I','F'], original_operational_request_consumers=list(original.get('dimensions', [])), stop_scope='exact current operative reference; no absence-as-zero', dependency_status='stopped')"
new="request.update(dimensions=consumer_scope['dimensions'], current_operative_consumer_scope=consumer_scope, original_operational_request_consumers=list(original.get('dimensions', [])), stop_scope='exact current operative reference; no absence-as-zero', dependency_status='stopped')";assert text.count(old)==1;text=text.replace(old,new)
old="            if not any(norm(c['text'])==self.norm and self._se_same_geometry(c,current) for c in members):\n                continue\n"
new='''            actual_members=[]
            target_span=self.unit.get('source_ref',{}).get('locator',{}).get('unicode_code_point_interval_half_open')
            current_pid,current_pid_ok=self._se_geometry_value(current,'paragraph_id')
            for c in members:
                if norm(c['text'])!=self.norm or not self._se_same_geometry(c,current):
                    continue
                pid,pid_ok=self._se_geometry_value(c,'paragraph_id')
                if not current_pid_ok or not pid_ok or (pid and current_pid and pid!=current_pid):
                    continue
                span=c.get('source_ref',{}).get('locator',{}).get('unicode_code_point_interval_half_open')
                if isinstance(target_span,list) and isinstance(span,list) and len(target_span)==len(span)==2:
                    if any(type(v) is not int for v in target_span+span) or not span[0]<=target_span[0]<=target_span[1]<=span[1]:
                        continue
                actual_members.append(c)
            if len(actual_members)!=1:
                continue
'''
assert text.count(old)==1;text=text.replace(old,new)
ast.parse(text);R.write_text(text)
print('Clause label normalization keeps original geometric proof. I/F missing standards scoped to current exact consumer.')
