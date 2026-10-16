"""Independent document/data binding and citation checks; no authoring."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from fractions import Fraction
from collections import Counter
import json,re,hashlib,argparse
OUT=Path(__file__).resolve().parent
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def text(x):return ''.join(x.xpath('.//w:t/text()',namespaces=N)).replace('\u2060','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ids(t):
 out=[]
 for part in t[1:-1].split(','):
  v=re.split('[–—-]',part);out.extend(range(int(v[0]),int(v[-1])+1))
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');args=ap.parse_args()
 folder=OUT/'preview' if args.preview else OUT
 f=folder/'论文修订稿-三部门版.docx';memo=folder/'校核与待确认事项.docx'
 manifest=json.loads((folder/'文稿生成与证据绑定.json').read_text())
 stats=json.loads((OUT/'三部门编码指标.json').read_text());attention=json.loads((OUT/'三部门注意力分布与敏感性.json').read_text())
 root=E.fromstring(ZipFile(f).read('word/document.xml'));body=root.find('w:body',N);ps=body.findall('w:p',N);tables=body.findall('w:tbl',N)
 assert len(tables)==4
 assert manifest['output_sha256'][str(f)]==sha(f) and manifest['output_sha256'][str(memo)]==sha(memo)
 full=text(body);assert not re.search(r'\{[A-Z_]+\}',full)
 check_full='\n'.join(text(p) for p in body.xpath('.//w:p',namespaces=N) if not args.preview or not text(p).startswith('内部排版预览'))
 for old in ['旧LLM','v28.2','中央综合','综合政策','阳性维度','κ≥0.80','60项单参照','30项比较','H427的A/C']:
  assert old not in check_full,f'Old process or inconsistent term left in manuscript: {old}'
 if not args.preview:
  for unclosed in ['内部排版预览','待闭合','尚未闭合','尚无新全量']:
   assert unclosed not in full
 assert 'AI agent' in full,'Reference provenance must remain true'
 # Rebuild all table 2 point estimates from the statistical records.
 cn=['安全性','有效性','经济性','创新性','公平性'];dims=['S','E','Ec','I','F'];records=stats['records'];rule=attention['method_bindings']['rule']['method']
 table_values=[[[text(c) for c in r.findall('w:tc',N)] for r in t.findall('w:tr',N)] for t in tables]
 t2=table_values[1];assert len(t2)==11
 checked=0
 for row in t2[1:]:
  dim=dims[cn.index(row[0])];method=rule if row[1]=='自动规则' else 'llm_gpt56_sol_v29'
  if args.preview and row[2]=='待闭合':continue
  for ci,key in enumerate(['kappa','precision','recall','f1'],2):
   expected=[]
   for ref in ['A','C']:
    r=next(r for r in records if (r['frame'],r['group'],r['method'],r['reference'],r['dimension'])==('main1057','ALL',method,ref,dim));v=r['metrics'][key]['estimate']
    expected.append('—' if v is None else f'{v*100:.1f}' if key in ['precision','recall'] else f'{v:.3f}')
   assert row[ci]=='/'.join(expected),(dim,method,key,row[ci],expected);checked+=2
 # Independently verify denominators and all displayed percentages in table 3.
 t3=table_values[2];mapping={'药监':'NMPA','医保':'NHSA','卫健':'NHC'};methods={'规则':rule,'LLM':'llm_gpt56_sol_v29','A':'A_AI_reference','C':'C_AI_reference'}
 for row in t3[1:]:
  g=mapping[row[0]];m=methods[row[1]];x=attention['primary'][m][g]
  counts=[Fraction(x['dimensions'][d]['weighted_known_hit_count']['exact_fraction']) for d in dims];den=sum(counts)
  assert Fraction(x['weighted_five_dimension_known_hit_sum']['exact_fraction'])==den
  assert row[2]==(f'{float(den):.2f}' if m.endswith('_reference') else f'{float(den):.0f}')
  shares=[c/den for c in counts];assert sum(shares)==1
  for val,share in zip(row[3:],shares):assert val==f'{float(share)*100:.2f}';checked+=1
  assert abs(sum(float(v) for v in row[3:])-100)<=.020001
 # Confirm actual first-appearance citation order, accounting for ranges/tables.
 ref_start=next(i for i,p in enumerate(ps) if text(p)=='参考文献');refs=ps[ref_start+1:];nums=[]
 for p in refs:
  match=re.match(r'^\[(\d+)\]',text(p));assert match;nums.append(int(match[1]))
 assert nums==list(range(1,len(nums)+1))
 observed=[];after_refs=False
 for block in body:
  if block.tag=='{'+N['w']+'}p' and text(block)=='参考文献':break
  for pp in ([block] if block.tag=='{'+N['w']+'}p' else block.xpath('.//w:p',namespaces=N)):
   for token in re.findall(r'\[\d+(?:[,–—-]\d+)*\]',text(pp)):
    for rid in ids(token):
     assert rid in nums
     if rid not in observed:observed.append(rid)
 assert observed==nums
 # Journal type rules verified directly on the final generated table runs.
 for t in tables[1:]:
  for r in t.xpath('.//w:r',namespaces=N):
   v=r.find('w:rPr/w:sz',N);assert v is not None and v.get('{'+N['w']+'}val')=='21'
 report={'status':'passed','main_sha256':sha(f),'memo_sha256':sha(memo),'statistics_sha256':sha(OUT/'三部门编码指标.json'),'attention_sha256':sha(OUT/'三部门注意力分布与敏感性.json'),'checked_table_values':checked,'table_count':len(tables),'reference_count':len(nums),'citations_first_appearance_valid':True,'five_shares_sum_exactly_one':True,'rounded_share_max_sum_error_pp':.02,'AI_provenance_retained':True,'old_process_values_removed':True,'table_font_pt':10.5,'scope':'Machine checks do not substitute for actual page-image review, policy/literature source checks or human validation.'}
 (folder/'最终文稿数据与引用核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
