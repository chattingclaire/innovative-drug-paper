from pathlib import Path
from pypdf import PdfReader
import hashlib,json,re,datetime
D=Path(__file__).parent
paths=list(Path('outputs/validation-expansion-20260926').glob('科学决策*原刊.pdf'))+list(Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/期刊论述修订-20260927/样文研读').glob('科学决策*.pdf'))
rows=[]
for i,p in enumerate(sorted(paths),1):
 b=p.read_bytes();r=PdfReader(p);texts=[x.extract_text() for x in r.pages];(D/f'local-sample-{i}-extracted.txt').write_text(''.join(f'\n=== PDF_PAGE_{n+1} ===\n'+s for n,s in enumerate(texts)))
 examples=[]
 for n,s in enumerate(texts[:min(len(texts),4)]):
  for line in s.splitlines():
   if re.search(r'[（(](?:19|20)\d{2}[）)]',line):examples.append({'pdf_page_1based':n+1,'line':line})
 out={'sample_key':f'local-sample-{i}','path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'page_count':len(r.pages),'first_page_opening':texts[0][:550],'year_parentheses_examples_first_four_pages':examples[:18]}
 rows.append(out);print(json.dumps(out,ensure_ascii=False,indent=2))
(D/'local_journal_sample_inventory.json').write_text(json.dumps({'read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'filename_search_roots':['/Users/rainbow/Desktop/战略院/药企项目-创新药','/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914'],'samples':rows},ensure_ascii=False,indent=2)+'\n')
