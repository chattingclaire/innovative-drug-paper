"""Source preparation only: no model calls, predictions, gold answers or rule edits."""
from pathlib import Path
from lxml import html
import json, re, hashlib, unicodedata, difflib, subprocess
from collections import defaultdict, Counter

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
SRC=HERE/'候选来源下载'
OUT=HERE/'追加三份文件来源准备'
OUT.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
def sentences(s): return re.findall(r'.+?(?:[。!?！？]+[”’\"）)]*|$)',s)
def paras(name,selector):
    t=html.fromstring((SRC/name).read_bytes())
    return [''.join(p.itertext()).strip() for p in t.get_element_by_id(selector).xpath('.//p')]

docs=[]
name='NMPA-临床急需境外药品2026-上海药监局正文.html'
p=paras(name,'ivs_content')
docs.append(dict(code='D1',title='国家药监局关于进一步优化临床急需境外已上市药品审评审批有关事项的公告',number='2026年第3号',agency='国家药监局',signed_date='2026-01-05',publication_date='2026-01-07',reprint_date='2026-01-08',url='https://yjj.sh.gov.cn/qtgzwj/20260108/692630d121b44a6db603858f49185b58.html',primary_url='https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260107152912184.html',source_file=name,representation='官方转载HTML正文p元素textContent',paragraphs=p[:11],target_paragraphs=list(range(7)),attachments=['NMPA-临床急需境外药品2026-配套解读.doc']))
name='NHC-儿童用药供应保障2026-医保局转载.html'; p=paras(name,'zoom')
headings=[4,5,7,9,11,13,14,16,18,20,22,24,25,27,29,30,32,34,36,38,40]
docs.append(dict(code='D2',title='关于改革完善儿童用药供应保障机制的实施意见',number='国卫药政发〔2026〕10号',agency='国家卫生健康委等八部门联合发文',signed_date='2026-04-22',publication_date='2026-05-07',reprint_date='2026-05-15',url='https://www.nhsa.gov.cn/art/2026/5/15/art_104_20517.html',primary_url='https://www.nhc.gov.cn/yaozs/c100098/202605/2f111457f6a046869535f9bea5e46bf2.shtml',source_file=name,representation='官方转载HTML正文p元素textContent',paragraphs=p[:49],target_paragraphs=[i for i in range(3,43) if i not in headings],headings=headings,attachments=[]))

name='NHSA-真实世界医保综合价值评价试点2025-网页工具提取.json'
r=json.loads((SRC/name).read_text()); text='\n'.join(c.get('text','') for c in r['content'])
lines={int(i):s for i,s in re.findall(r'^L(\d+): ?(.*)$',text,re.M)}
indices=[15,16,18,20,21,23,25,26,27,28,30,31,33,35,37,39]
assert lines[15].startswith('北京市') and '国家医疗保障局办公室' in lines[37]
p=[lines[i] for i in indices]
docs.append(dict(code='D3',title='国家医疗保障局办公室关于开展真实世界医保综合价值评价试点工作的通知',number='医保办发〔2025〕15号',agency='国家医保局办公室',signed_date='2025-09-23',publication_date='2025-09-23',url='https://www.nhsa.gov.cn/art/2025/9/23/art_109_17984.html',primary_url='https://www.nhsa.gov.cn/art/2025/9/23/art_109_17984.html',source_file=name,representation='网页工具可见文本提取；已与浏览器可见段落核对；不是原始HTML字节保存件',paragraphs=p,target_paragraphs=[1,3,4,6,7,8,9,11],headings=[2,5,10],attachments=['NHSA-真实世界医保综合价值评价试点2025-附件原图.jpg']))

# Appendix transcription preserves row/column meaning; it is context, not a new
# prediction target. The source image is always supplied alongside it.
table1=[
['北京市','海淀区','药品综合价值评价真实世界研究规范。','创新药、医用耗材'],
['辽宁','大连市','基于真实世界数据的目录内药品综合价值评价研究。','创新药、仿制药'],
['江苏','南京市','服务药品综合价值评价的真实世界数据库研究。','创新药、中医'],
['江苏','苏州市','医保数据如何服务保障真实世界研究。','仿制药、医用耗材'],
['浙江','杭州市','基于真实世界数据的拟新纳入目录的药品综合价值评价研究。','创新药、医疗服务'],
['浙江','温州市','基于特定区域的药品综合价值评价组织研究。','仿制药、医用耗材'],
['福建','厦门市','未被满足的临床需求研究。','创新药、医疗服务'],
['福建','三明市','基于真实世界数据的医药价格价值符合性研究。','仿制药、医疗服务'],
['广东','深圳市','药品综合价值评价真实世界研究规范。','创新药、医用耗材'],
['海南','海南省','1. 基于真实世界数据的特定区域内境内未上市药品综合价值评价研究；2. 医保数据如何服务保障真实世界研究。','创新药、医用耗材、中医'],
['重庆','重庆市','基于特定区域的药品综合价值评价组织研究。','仿制药、中药、医用耗材'],
['四川','成都市','未被满足的临床需求研究。','创新药、医疗服务'],
['陕西','西安市','基于真实世界数据的目录内药品退出机制研究。','仿制药、中医'],
['甘肃','兰州市','医保数据如何服务保障真实世界研究。','中药、中医']]
table2={
'药品':['上市前研发立项参考','药品首发挂网','医保及商保创新药目录调整','集采药品疗效及价格分析','挂网药品价格治理','药品使用分析，用法用量、联合用药、超适应症用药等','上市后药品价值再评价'],
'医用耗材':['（异地就医）医用耗材医保目录调整','可单独收费目录调整','医用耗材挂网及价格治理','创新医用耗材医保分类','集采医用耗材分组及比价系数调整'],
'医疗服务':['医疗服务价格项目管理，附条件新增、转归、调整、废止','医疗服务定价及价格治理','（异地就医）医疗服务医保目录调整','医疗服务价格动态调整','医疗服务价格改革政策制定'],
'其他':['药品 VS 医疗服务综合价值评估','中医优势病种 VS 西医治疗综合价值评估','按病种付费特例单议及除外支付政策','按疗效付费政策研究']}
docs[2]['attachment_transcription']={'source_image':'NHSA-真实世界医保综合价值评价试点2025-附件原图.jpg','table1_title':'医保综合价值评价试点先行地区名单及任务分工','table1_headers':['省份','试点名单','研究方向','评价类别'],'table1_rows':table1,'table2_title':'医保综合价值评价参考应用场景','table2_headers':['类别','参考应用场景'],'table2_rows':[[k,v] for k,vals in table2.items() for v in vals],'method':'原图人工转写；合并单元格的类别逐行展开，不添加原图没有的评价结论。'}

old=[]; idx=defaultdict(set)
for line in (BASE/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').read_text().splitlines():
    r=json.loads(line); t=r['semantic_unit']['text']; n=norm(t); k=len(old);old.append((r['id'],t,n))
    for g in {n[i:i+12] for i in range(max(0,len(n)-11))}:idx[g].add(k)
targets=[]; overlap=[]
for d in docs:
    d['source_sha256']=sha(SRC/d['source_file'])
    d['attachment_checks']=[{'file':a,'bytes':(SRC/a).stat().st_size,'sha256':sha(SRC/a)} for a in d['attachments']]
    if d['code']=='D1':
        z=subprocess.run(['textutil','-convert','txt','-stdout',str(SRC/d['attachments'][0])],capture_output=True,text=True,check=True)
        d['attachment_transcription']={'text':z.stdout,'method':'textutil只读提取官方DOC原件；保留原件供核对'}
    for pi in d['target_paragraphs']:
        for si,s in enumerate(sentences(d['paragraphs'][pi])):
            ident=f"SUP-{d['code']}-{pi:03}-{si:02}"
            # Short inline subheadings retained as context, not standalone targets.
            heading=bool(re.match(r'^（[一二三四五六七八九十]+）.*。$',s) and len(s)<24) or bool(re.match(r'^[一二三四五六七八九十]是.{1,12}。$',s))
            if heading:continue
            r={'id':ident,'document_code':d['code'],'paragraph_index':pi,'sentence_index':si,'text':s,'source_sha256':d['source_sha256'],'status':'source_scope_preparation_not_issued'}
            targets.append(r);n=norm(s);counts=Counter(k for g in {n[i:i+12] for i in range(max(0,len(n)-11))} for k in idx.get(g,[]));hits=[]
            for k,c in counts.most_common(30):
                oi,ot,on=old[k];ratio=difflib.SequenceMatcher(None,n,on,autojunk=False).ratio()
                if ratio>=.7 or(min(len(n),len(on))>=20 and (n in on or on in n)):
                    hits.append({'old_id':oi,'old_text':ot,'ratio':round(ratio,6),'exact':n==on})
            if hits:overlap.append({'id':ident,'text':s,'hits':hits})
dump(OUT/'sources.json',docs)
(OUT/'targets.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in targets))
dump(OUT/'overlap-screen.json',{'method':'与旧4481正文的12字符召回加相似度/包含初筛；不等于语义独立认证','flagged_count':len(overlap),'rows':overlap})
summary={'status':'source_scope_preparation_not_issued','target_count':len(targets),'targets_per_source':dict(Counter(r['document_code'] for r in targets)),'flagged_count':len(overlap),'exact_duplicate_count':sum(any(h['exact'] for h in r['hits']) for r in overlap),'no_rule_or_llm_predictions':True,'no_new_human_answers':True,'old4481_changed':False}
dump(OUT/'source-preparation-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
for r in overlap:print(r['id'],r['text'][:70],[(h['old_id'],h['ratio']) for h in r['hits'][:3]])
