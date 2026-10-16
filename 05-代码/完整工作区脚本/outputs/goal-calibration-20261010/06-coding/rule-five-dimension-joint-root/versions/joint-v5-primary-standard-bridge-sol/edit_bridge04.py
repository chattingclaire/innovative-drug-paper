from pathlib import Path
P=Path(__file__).resolve().parent;r=P/'relations.py';s=r.read_text()
old="""        content = []
        for paragraph in re.finditer(r'[^\\n]+(?:\\n|$)', raw[ga:content_end]):
            if paragraph.group().strip():
                content.extend(quotes(ga+paragraph.start(), ga+paragraph.end(), '当前操作性援引的有限标准原文段落，保留成员/定义分支并未跨下一边界'))
"""
new="""        content = []; content_spans = []; pending = None
        for line in re.finditer(r'[^\\n]+(?:\\n|$)', raw[ga:content_end]):
            if not line.group().strip():
                continue
            left,right=ga+line.start(),ga+line.end()
            body=line.group().strip()
            explicit_member = bool(re.match(r'(?:\\d+[.、．]|[（(]\\d+[）)]|[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[）)])',body))
            continuation = bool(re.match(r'但|不过|而|并且|且|其中|即|也|上述|该(?:条件|情形|要求|标准)|这(?:一|种|些)',body))
            finished = pending is not None and bool(re.search(r'[。！？!?][ \\t\\r\\n]*$',raw[pending[0]:pending[1]]))
            if pending is not None and (explicit_member or (finished and not continuation)):
                content_spans.append(pending);pending=None
            pending = [left,right] if pending is None else [pending[0],right]
        if pending is not None:content_spans.append(pending)
        for left,right in content_spans:
            content.extend(quotes(left,right,'当前有限标准明确成员/已终结原文句段；无终结或承接限定的视觉续行不被拆为独立命题'))
"""
assert s.count(old)==1;s=s.replace(old,new)
old="                 'group_snapshot_span':[ga,gb], 'content_snapshot_span':[ga,content_end],\n"
new="                 'group_snapshot_span':[ga,gb], 'content_snapshot_span':[ga,content_end], 'content_quote_snapshot_spans':content_spans,\n                 'paragraph_quote_basis':'explicit numbered members/headings or complete original sentence boundary; visual continuations and qualification links retained',\n"
assert s.count(old)==1;r.write_text(s.replace(old,new));print('explicit members / completed source clauses; visual and qualifier continuations retained')
