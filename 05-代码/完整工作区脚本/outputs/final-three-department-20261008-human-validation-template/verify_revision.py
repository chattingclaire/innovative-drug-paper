from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from fractions import Fraction
import hashlib,json,re

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'final-three-department-20261008-adopted-results'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def plain(x):return ''.join(x.xpath('.//w:t/text()',namespaces=NS)).replace('\u2060','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with ZipFile(p) as z:d={i.filename:z.read(i.filename) for i in z.infolist()}
 return d,E.fromstring(d['word/document.xml'])
def cite_ids(token):
 result=[]
 for segment in token[1:-1].split(','):
  v=re.split('[–—-]',segment);result+=list(range(int(v[0]),int(v[-1])+1))
 return result
checks=[]
def check(name,test,detail=None):
 checks.append({'name':name,'pass':bool(test),'detail':detail})
 if not test:raise AssertionError(name)
src=BASE/'论文修订稿-三部门实测结果版.docx'
dst=OUT/'论文修订稿-人工复核待填版.docx'
memo=OUT/'真人复核实施与待补事项.docx'
sd,sr=read(src);dd,dr=read(dst);md,mr=read(memo)
check('source_main_frozen',sha(src)=='dd23f6e6e426d0a914eb206fb85ee152bdb0400700e769d8c28390efecb7226f')
check('source_memo_frozen',sha(BASE/'校核与待确认事项.docx')=='c73c4c9ef4e9f80421d2650609e1c5fb6d030403ac9a576ac0e2105276578a57')
check('all_non_document_package_parts_preserved',set(sd)==set(dd) and all(sd[k]==dd[k] for k in sd if k!='word/document.xml'))
sb=sr.find('w:body',NS);db=dr.find('w:body',NS)
check('page_and_section_geometry_preserved',[E.tostring(x) for x in sr.findall('.//w:sectPr',NS)]==[E.tostring(x) for x in dr.findall('.//w:sectPr',NS)])
st=sb.findall('w:tbl',NS);dt=db.findall('w:tbl',NS)
check('four_tables_retained',len(st)==len(dt)==4)
for n in [0,3]:check('table_'+str(n+1)+'_unchanged',E.tostring(st[n])==E.tostring(dt[n]))
for ri,(a,b) in enumerate(zip(st[2].findall('w:tr',NS),dt[2].findall('w:tr',NS))):
 av=[plain(c) for c in a.findall('w:tc',NS)];bv=[plain(c) for c in b.findall('w:tc',NS)]
 expected=[{'规则':'自动规则编码','LLM':'LLM编码'}.get(t,t) for t in av]
 check('attention_table_row_'+str(ri)+'_all_numbers_preserved',bv==expected)
rows=dt[1].findall('w:tr',NS)
check('human_table_has_ten_rows',len(rows)==11)
check('all_40_human_result_cells_pending',all(plain(c)=='待填/待填' for row in rows[1:] for c in row.findall('w:tc',NS)[2:]))
check('canonical_method_cells',all(plain(row.findall('w:tc',NS)[1]) in ['自动规则编码','LLM编码'] for row in rows[1:]))
ps=db.findall('w:p',NS);refhead=next(i for i,p in enumerate(ps) if plain(p)=='参考文献')
refps=ps[refhead+1:];refs=[plain(p) for p in refps]
check('66_real_reference_entries',len(refs)==66 and all(t.startswith('['+str(i)+']') for i,t in enumerate(refs,1)))
first=[]
for p in db.iter('{'+NS['w']+'}p'):
 if p in refps:continue
 for match in re.finditer(r'\[\d+(?:[,–—-]\d+)*\]',plain(p)):
  for n in cite_ids(match[0]):
   check('reference_exists_'+str(n),1<=n<=66)
   if n not in first:first.append(n)
 for run in p.findall('w:r',NS):
  if re.fullmatch(r'\[\d+(?:[,–—-]\d+)*\]',plain(run)):
   vert=run.find('w:rPr/w:vertAlign',NS)
   check('citation_superscript_'+plain(run),vert is not None and vert.get('{'+NS['w']+'}val')=='superscript')
check('reference_first_appearance_order',first==list(range(1,67)))
texts=[plain(p) for p in ps[:refhead]];bodytext='\n'.join(texts)
check('no_proxy_as_human_statistics',all(v not in bodytext for v in ['0.944、0.820、0.879、0.520、0.641','三者均为AI评审流','候选参照','180条','60条挑战']))
check('human_results_pending_explicitly','待填、待填、待填、待填、待填' in bodytext and '首次人工提交' in bodytext)
check('planned_240_not_false_completed_human','人工编码拟由两名' in bodytext and '预先冻结240条复核材料' in bodytext)
check('three_proportions_defined_in_framework',all(t in bodytext for t in ['3.3 变量与指标定义','“注意力占比”','“内容覆盖比例”','“经济性单元中的公平性比例”']))
check('two_stage_frame_and_resampling_correct',all(t in bodytext for t in ['1031、841、140','1044、1113、140','80/79','抽取79族','不作有限总体校正']))
check('actual_main_joint_counts_retained',all(t in bodytext for t in ['14/31（45.16%）','125/610（20.49%）','13/30（43.33%）','145/677（21.42%）']))
check('official_updated_policy_sources_present',all(u in '\n'.join(refs) for u in ['art_109_19642','art_53_18971','art_109_17984','art_109_19379','art_14_20707']))
check('corpus_scope_retained','2017年至2026年7月' in bodytext and '共51个' in bodytext and '4481' in bodytext)
check('no_posthoc_hypotheses',not re.search(r'假设\s*[Hh123一二三]',bodytext))
memotext=plain(mr)
check('memo_discloses_origin_and_true_status','既有A、C及第三评审T均为AI代理' in memotext and '工作区尚未收到可核对的真人结果文件' in memotext)
check('memo_original_kappa_table_not_human',len(mr.findall('.//w:tbl',NS))==1 and '既有代理开发诊断' in memotext)
check('memo_pending_steps_and_submission_state',all(t in memotext for t in ['首次标签','裁定记录','基金信息','不能将其作为已通过真人信效度检验的终稿提交']))
cnabstract=plain(ps[1]);main_end=next(i for i,p in enumerate(ps) if plain(p).startswith('附录A'))
maintext=''.join(plain(p) for p in ps[:main_end])
tabletext=''.join(plain(t) for t in dt)
report={'status':'PASS_CONTENT_AND_PACKAGE_CHECKS_NOT_HUMAN_VALIDATION','main_sha256':sha(dst),'memo_sha256':sha(memo),
 'checks_count':len(checks),'checks':checks,'counts':{'paragraphs':len(ps),'references':len(refs),
 'main_han_excluding_tables_appendices_references':len(re.findall('[\u4e00-\u9fff]',maintext)),
 'main_han_with_tables':len(re.findall('[\u4e00-\u9fff]',maintext+tabletext)),
 'cn_abstract_nonwhite_including_label':len(re.sub(r'\s','',cnabstract)),
 'cn_abstract_han_including_label':len(re.findall('[\u4e00-\u9fff]',cnabstract))}}
(OUT/'actual_document_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
