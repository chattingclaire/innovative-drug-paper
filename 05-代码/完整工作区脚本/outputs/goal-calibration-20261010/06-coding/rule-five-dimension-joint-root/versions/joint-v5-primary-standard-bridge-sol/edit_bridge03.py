from pathlib import Path
P=Path(__file__).resolve().parent;r=P/'relations.py';s=r.read_text()
old="        content = quotes(ga, content_end, '当前操作性援引的完整有限标准成员及直接定义，未跨到下一边界')\n"
new="""        content = []
        for paragraph in re.finditer(r'[^\\n]+(?:\\n|$)', raw[ga:content_end]):
            if paragraph.group().strip():
                content.extend(quotes(ga+paragraph.start(), ga+paragraph.end(), '当前操作性援引的有限标准原文段落，保留成员/定义分支并未跨下一边界'))
"""
assert s.count(old)==1;r.write_text(s.replace(old,new));print('precise neutral paragraph quotes; no label predicate changes')
