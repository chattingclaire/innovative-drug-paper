from pathlib import Path
p=Path(__file__).resolve().parent;r=(p/'relations.py').read_text()
def ch(a,b):
 global r
 if a not in r:raise ValueError(a[:80])
 r=r.replace(a,b,1)
ch("([^\\W_]{1,8}类)(?=项目|和|及|、)","([^的和及、，,；;：:\\s]{1,8}类)(?=项目|和|及|、)")
ch("re.match(r'[（(][一二三四五六七八九十]+[）)]',part)","re.match(r'[（(](?:[一二三四五六七八九十]+|[0-9]+)[）)]',part)")
ch("(?:撰写|编制|涉及)'+re.escape(alias)+r'", "(?:撰写|编制|涉及)\\s*'+re.escape(alias)+r'")
(p/'relations.py').write_text(r)
