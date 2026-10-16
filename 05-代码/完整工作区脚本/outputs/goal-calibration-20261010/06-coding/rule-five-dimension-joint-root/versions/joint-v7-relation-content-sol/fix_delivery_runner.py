from pathlib import Path
p=Path('deliver_repair.py');s=p.read_text();s=s.replace(" with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\\n')"," p=Path(p)\n if p.exists():\n  assert read(p)==x, 'Do not replace a different preserved artifact: '+str(p)\n  return\n with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\\n')")
s=s.replace("def labels(r):return {d:r['decisions'][d]['value'] for d in DIMS}","def labels(r):return {d:r['decisions'][d]['value'] for d in DIMS} if 'decisions' in r else {'geometry_only':r.get('actual_programme_span')}")
s=s.replace("snap=P/'after-code-snapshot';snap.mkdir()","snap=P/'after-code-snapshot';snap.mkdir(exist_ok=True)")
s=s.replace("assert manual['sha256']=='5ea7ab74c7863d194107a806bd1b6355bff9e0dc0db1784d615c174a34d3f7f00'","assert manual['sha256']=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'")
p.write_text(s)
