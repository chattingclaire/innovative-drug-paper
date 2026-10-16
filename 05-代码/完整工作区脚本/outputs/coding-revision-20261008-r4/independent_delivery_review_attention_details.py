"""Read-only delivery review. No classifier/statistical author function imported."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile
from fractions import Fraction
from itertools import combinations
import hashlib, json, re
from lxml import etree as E
from pypdf import PdfReader
from PIL import Image

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
R4=ROOT/'outputs/coding-revision-20261008-r4'
OUT=R4/'final-attention-details-independent-review'
OUT.mkdir(exist_ok=True)
DOC=ROOT/'outputs/final-three-department-20261008-human-validation-template/创新药评价的注意力配置差异与协调路径.docx'
OLD=R4/'manuscript-before-attention-details.docx'
RENDER=R4/'render-attention-details'
PDF=RENDER/(DOC.stem+'.pdf')
NUM=R4/'rules38-findings-independent-numeric-review/independent_numeric_review.json'
FULL=R4/'rules38-LLM03-synchronized-findings/完整定义构成核查.json'
DETAIL=R4/'all-pair-attention-detail-analysis-rule38/all60_conditional_department_contrasts.json'
METHODS=('rules-v38-development','LLM-candidate03-single-unit-reconciled')
GROUPS=('NMPA','NHSA','NHC')
DIMS=('S','E','Ec','I','F')
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def xml(p):
    with ZipFile(p) as z:return E.fromstring(z.read('word/document.xml'))
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
fail=[];checks=[]
def check(name,condition,details=None):
    checks.append({'check':name,'pass':bool(condition),'details':details})
    if not condition:fail.append(name)

start_sha=sha(DOC)
check('document exact requested SHA',start_sha=='4d61c921a8ea9837f9d31eb4cd09ace0af1839b51e2793232ee0f402ede905e0')
check('preserved pre-update document SHA',sha(OLD)=='36b5839a4eb6545bc62bcea90875956438a6dbc0062b94440b1fbaa6c947199e')
check('independent numeric review bound',sha(NUM)=='c07d632e8bfe7727958c080595b8e1f8217a9c7cf860fc2109c98157a8f4accd')
check('full findings bound',sha(FULL)=='6d66e26bcc4a0bfd395fcf5ed2641d61738ac4dae759f53177f4defe00886dc1')
x=xml(DOC);old=xml(OLD);body=x.find('w:body',NS)
ps=body.findall('w:p',NS);texts=[plain(p) for p in ps]
tables=body.findall('w:tbl',NS);oldtables=old.find('w:body',NS).findall('w:tbl',NS)
check('four tables retained',len(tables)==len(oldtables)==4)
table2=[]
for row in tables[1].findall('w:tr',NS)[1:]:
    cells=row.findall('w:tc',NS)
    for cell in cells[2:]: table2.extend(re.findall(r'\d+\.\d+',plain(cell)))
check('all80 table2 numeric entries and complete OOXML unchanged',len(table2)==80 and E.tostring(tables[1])==E.tostring(oldtables[1]),{'numeric_entry_n':len(table2),'old_table_xml_sha256':hashlib.sha256(E.tostring(oldtables[1])).hexdigest(),'new_table_xml_sha256':hashlib.sha256(E.tostring(tables[1])).hexdigest()})
for i in (0,3):check('table%d complete OOXML unchanged'%(i+1),E.tostring(tables[i])==E.tostring(oldtables[i]))

num=json.loads(NUM.read_text());full=json.loads(FULL.read_text());detail=json.loads(DETAIL.read_text())
check('prior independent full numeric audit PASS with no failures',num['status']=='PASS' and not num['failures'])
profiles=num['primary_exact_profiles_and_pairs']
table3=[]
for i,(g,m) in enumerate((g,m) for g in GROUPS for m in METHODS):
    p=profiles[m]['departments'][g]['profile'];total=sum(p['coding_count'].values())
    cells=tables[2].findall('w:tr',NS)[i+1].findall('w:tc',NS)
    for j,d in enumerate(DIMS):
        actual=plain(cells[j+2]);expected=f'{100*Fraction(p["coding_count"][d],total):.2f}' if False else f'{100*p["coding_count"][d]/total:.2f}'
        table3.append({'department':g,'method':m,'dimension':d,'count':p['coding_count'][d],'denominator':total,'exact':str(Fraction(p['coding_count'][d],total)),'expected_display':expected,'actual_display':actual,'pass':actual==expected})
check('all30 table3 percentages independently match counts',len(table3)==30 and all(t['pass'] for t in table3))
nhc=profiles[METHODS[0]]['departments']['NHC']['profile']
check('NHC F60 and five-dimension total165',nhc['coding_count']['F']==60 and nhc['five_dimension_coding_count']==165 and nhc['unit_n']==533,nhc)

def pair(dept,a,b):
    for p in dept['all10_pairs']:
        if {p['dimension_a'],p['dimension_b']}=={a,b}:return p
    raise KeyError((a,b))
def conditional(dept,a,b):
    p=pair(dept,a,b);a_first=p['dimension_a']==a
    if 'cluster_counts' in p:
        # Equal-cluster estimand: average only nonzero condition denominators.
        vals=[]
        for c in p['cluster_counts'].values():
            n=int(c['both_n']);den=n+int(c['a_only_n'] if a_first else c['b_only_n'])
            if den:vals.append(Fraction(n,den))
        return sum(vals,Fraction())/len(vals) if vals else None
    n=int(p['both_n']);den=n+int(p['a_only_n'] if a_first else p['b_only_n'])
    return Fraction(n,den) if den else None
def scenario_depts(s,m,kind):return s['methods'][m]['full4481']['departments'] if kind=='definition6' else s['methods'][m]['departments']
conditionals=[]
for m in METHODS:
    for a,b,groups in [('Ec','F',('NHSA','NHC')),('F','Ec',('NHSA','NHC')),('S','E',GROUPS),('E','S',GROUPS)]:
        for g in groups:
            dept=profiles[m]['departments'][g];p=pair(dept,a,b);n=p['both_n'];den=dept['profile']['coding_count'][a]
            ratio=Fraction(n,den)
            conditionals.append({'method':m,'department':g,'condition_dimension':a,'cooccurring_dimension':b,'numerator':n,'denominator':den,'exact':str(ratio),'display_fraction':f'{n}/{den}','display_percent':f'{100*float(ratio):.2f}%'})
            if (a,b)!=('E','S'):
                check(f'5.2 numeric fraction {m} {g} {a}->{b}',f'{n}/{den}' in ''.join(texts),conditionals[-1])

directions=[]
for kind in ('definition6','composition56'):
    check(kind+' scenario count',len(full[kind])==(6 if kind=='definition6' else 56))
    for m in METHODS:
        for a,b,one,two in [('Ec','F','NHC','NHSA'),('F','Ec','NHSA','NHC'),('S','E','NHSA','NMPA'),('S','E','NHSA','NHC')]:
            vals=[]
            for s in full[kind]:
                ds=scenario_depts(s,m,kind);v1=conditional(ds[one],a,b);v2=conditional(ds[two],a,b)
                vals.append((s['scenario'],None if v1 is None or v2 is None else 100*(v1-v2)))
            v=[z for _,z in vals if z is not None]
            record={'scope':kind,'method':m,'condition':a,'cooccurring':b,'higher_department':one,'lower_department':two,'scenario_n':len(vals),'higher_n':sum(z>0 for z in v),'equal_n':sum(z==0 for z in v),'undefined_n':len(vals)-len(v),'min_pp':float(min(v)),'max_pp':float(max(v))}
            directions.append(record);check(f'{kind} all-direction {m} {a}->{b} {one}>{two}',record['higher_n']==len(vals),record)
            if kind=='composition56' and (a,b)==('Ec','F'):
                check('5.2 '+m+' stated range',f'{float(min(v)):.2f}—{float(max(v)):.2f}' in ''.join(texts),record)

# Independently rederive every all60 aggregate contrast, both methods.
all60=[]
for r in detail['rows']:
    a,b=r['condition_dimension'],r['cooccurring_dimension'];one,two=r['department_one'],r['department_two']
    for m,entry in r['methods'].items():
        ds=profiles[m]['departments'];v1=conditional(ds[one],a,b);v2=conditional(ds[two],a,b)
        ok=abs(float(v1)-entry['one']['conditional_share'])<1e-12 and abs(float(v2)-entry['two']['conditional_share'])<1e-12
        for kind in ('definition6','composition56'):
            vals=[]
            for s in full[kind]:
                d=scenario_depts(s,m,kind);u,v=conditional(d[one],a,b),conditional(d[two],a,b)
                vals.append(None if u is None or v is None else 100*(u-v))
            defined=[v for v in vals if v is not None];e=entry[kind]
            ok=ok and len(vals)==e['scenario_n'] and sum(v>0 for v in defined)==e['one_higher_n'] and sum(v<0 for v in defined)==e['two_higher_n'] and sum(v==0 for v in defined)==e['equal_n'] and len(vals)-len(defined)==e['undefined_n']
            ok=ok and all(abs(float(v)-expected)<1e-10 for v,expected in zip((min(defined),max(defined)),e['difference_percentage_point_range']))
        all60.append({'method':m,'condition':a,'cooccurring':b,'department_one':one,'department_two':two,'pass':ok})
check('all60 contrasts times two methods rederived from aggregate cells',len(all60)==120 and all(r['pass'] for r in all60))

# Textual construction checks, without treating coexpression as causal evidence.
p33=next(t for t in texts if t.startswith('比较采用三类比例'))
check('3.3 all three denominators and reverse defined',all(s in p33 for s in ('除以五维编码句次合计','除以本部门全部分析单元数','除以作为条件的该维单元数','反向比例另以另一维单元数为分母','共同表达可包括并列内容要求')))
ci=texts.index('7 结语');ai=next(i for i,t in enumerate(texts) if t.startswith('附录A '))
conclusion=[p for p in ps[ci+1:ai] if plain(p).strip()]
check('conclusion one nonempty paragraph and no manual linebreak',len(conclusion)==1 and not conclusion[0].xpath('.//w:br',namespaces=NS))
check('conclusion has bounded execution limitation',len(conclusion)==1 and '尚未直接检验上述配置与实际执行效果之间的关系' in plain(conclusion[0]))
ri=texts.index('参考文献');refs=texts[ri+1:];refs=[t for t in refs if t.strip()]
oldps=old.find('w:body',NS).findall('w:p',NS);oldrefs=[plain(p) for p in oldps if re.match(r'^\[\d+\]',plain(p))]
check('all66 references retained without text changes',len(refs)==66 and refs==oldrefs)
check('reference list continuous1..66',[int(re.match(r'^\[(\d+)\]',t).group(1)) for t in refs]==list(range(1,67)))
citation_records=[];seen=[]
for child in body:
    if child is ps[ri]:break
    pseq=[child] if child.tag.endswith('}p') else child.findall('.//w:p',NS)
    for p in pseq:
        chars=[];flags=[]
        for r in p.findall('.//w:r',NS):
            t=plain(r);vert=r.find('w:rPr/w:vertAlign',NS);sup=vert is not None and vert.get('{'+NS['w']+'}val')=='superscript'
            chars.extend(t);flags.extend([sup]*len(t))
        t=''.join(chars)
        for match in re.finditer(r'\[(\d+(?:,\d+)*)\]',t):
            ids=[int(v) for v in match.group(1).split(',')]
            citation_records.append({'citation':match.group(),'all_characters_superscript':all(flags[match.start():match.end()]),'reference_ids':ids})
            for v in ids:
                if v not in seen:seen.append(v)
check('all first citations follow1..66',seen==list(range(1,67)),{'first_appearance_order':seen})
check('all numeric inline citation characters superscript',all(r['all_characters_superscript'] for r in citation_records),{'citation_group_n':len(citation_records),'not_superscript':[r for r in citation_records if not r['all_characters_superscript']]})
check('appendicesA B before references',ci<ai<next(i for i,t in enumerate(texts) if t.startswith('附录B '))<ri)

# Bind figure image and rendered numerical visibility, independently of author QA.
with ZipFile(DOC) as z:figure_sha=hashlib.sha256(z.read('word/media/image4.png')).hexdigest()
check('figure2 embedded bytes equal root current figure',figure_sha==sha(R4/'figure2_attention_current.png'))
reader=PdfReader(PDF);pdftexts=[p.extract_text() or '' for p in reader.pages]
check('rendered PDF21 pages and all21 original PNGs present',len(reader.pages)==21 and all((RENDER/f'page-{i}.png').is_file() for i in range(1,22)))
check('PDF page9 table3 all30 percentages visible',all(r['actual_display'] in pdftexts[8] for r in table3))
check('PDF page8 table2 all80 values visible',all(v in pdftexts[7] for v in table2))

projection=R4/'all-pair-attention-detail-analysis/非预留政策细节_事后解释核查投影.json'
extra=R4/'all-pair-attention-detail-analysis/非预留卫健经济公平_追加四例.json'
exclusion=R4/'validation-state-audit/future_human_v5_development_exclusion_metadata.json'
ex=json.loads(exclusion.read_text());reserved=set(ex['all_registered_members_of_reserved_families_unit_ids'])
pp=json.loads(projection.read_text());ee=json.loads(extra.read_text())
check('read policy projections exclude all267 reserved members',len(reserved)==267 and all(r['id'] not in reserved for r in pp['rows']+ee['rows']))
policy_evidence=[{'claim':'第七条以临床必需、安全有效、价格合理列目录准入条件','projection_id':'RECODE25-03215','source_pages':[3,4],'assessment':'Supported; coexpression includes conjunction, does not itself establish decision weighting or causality.'},{'claim':'申报创新带来疗效或安全性优势','projection_id':'RECODE25-02490','source_pages':[8],'assessment':'Supported; current statement says 疗效或安全性, not mandatory both.'},{'claim':'可及性纳入价格、可获得及可负担；必要时医保报销判断实际支付；家庭收入比重','projection_ids':['RECODE25-01154','RECODE25-01155','RECODE25-01157'],'assessment':'Supported by redacted nonreserved projection; manuscript is a summary of the policy, not a new coding adjustment.'}]
for row in pp['rows']+ee['rows']:check('policy source current bytes '+row['id'],sha(row['source'])==row['source_sha256'])

interview=[]
for filename,paragraphs,needle in [('医保局专家调研-0616.docx',[4],'安全性、有效性和经济性三个核心维度'),('史录文教授访谈会议纪要-0605.docx',[2,15],'医保进了，医院不一定用')]:
    path=ROOT/filename;ix=xml(path);ips=ix.find('w:body',NS).findall('w:p',NS)
    check('interview exact statement '+filename,any(needle in plain(ips[i-1]) for i in paragraphs))
    interview.append({'path':str(path),'sha256':sha(path),'paragraphs':['P%03d'%i for i in paragraphs],'statement_confirmed':needle,'scope':'Saved meeting-minute statement; not audio-verified quotation or a quantified population claim.'})
check('SLW manuscript date reflects originalP002', '2025年6月9日' in ''.join(texts) and '2025年6月9日' in plain(xml(ROOT/'史录文教授访谈会议纪要-0605.docx').find('w:body',NS).findall('w:p',NS)[1]))

notes={
1:'中英文题目、摘要、关键词清楚；首段[1]—[3]上标正常。',
2:'引言至2.1连续，段落及标题无遮挡；作者后序号上标可读。',
3:'2.1—2.2英文作者、重音字符及中英混排正常，未见缺字。',
4:'2.3、3.1和3.2开头层级清楚；引文上标及五维比例说明正常。',
5:'表1完整单页，表头与内容可读；图1框线、箭头、五维标签完整；3.3起段正常。',
6:'3.3三种分母及反向分母完整可读；4.1标题与文本正常。',
7:'4.1—4.2文本连续；AI代理初读与人工复核后保留身份披露可读，未写成独立盲评真人首次标签。',
8:'表2十行全部落在单页，80个三位小数可读，表注未截断；κ字形与上标正常。',
9:'表3六行30值完整，三部门/方法标签对应清楚，表注说明分母及舍入。',
10:'图2两分面、五维图例、六条堆积条、部门名和0—100轴均清楚；小于3%的窄段未放内部数值，但色块仍在且表3给全值。',
11:'5.1分母句次、5.2 Ec→F和F→Ec分数及百分数清楚；段落跨至12页自然。',
12:'表4完整单页，五行四列内容及来源表注可读；随后政策证据段无裁切。',
13:'S→E六个分数/百分数和5.3均可读。引文[39]因换行位于行首，仍为上标接前句，属可选排版优化。',
14:'5.4和6节引入清楚；纪要内2025年6月9日与短引句可读，上标引用未错位。',
15:'6.1、6.2层级清楚，2026年政策日期及引文上标正常，无重叠。',
16:'6.3完整；7结语标题及同一段前部清楚，段落自然跨17页。',
17:'结语同一段续文清楚；附录A在参考文献前，边界、模型参数和补充统计说明可读。',
18:'附录B完整后进入参考文献；[1]—[16]顺序连续，中英文条目无遮挡。',
19:'[17]—[38]顺序连续，外文重音及DOI可读；[26]2023卷年与2024 DOI按既核出版口径保留。',
20:'[39]—[59]顺序连续；[43]2026正式卷年与DOI2025并存可读，长URL换行无裁切。',
21:'[60]—[66]顺序连续，AIFA仅列访问日，末条DOI完整；下部空白为文末余量，无空白页。'}
pages=[]
for i in range(1,22):
    path=RENDER/f'page-{i}.png'
    with Image.open(path) as im:size=list(im.size)
    pages.append({'page':i,'path':str(path),'sha256':sha(path),'pixel_size':size,'actual_view_image_called':True,'requested_detail':'original','inspection':'PASS_WITH_OPTIONAL_NOTE' if i==13 else 'PASS','observation':notes[i],'blocking_issue':False})
page_review={'status':'PASS_WITH_OPTIONAL_TYPESSETTING_NOTE','review_utc':datetime.now(timezone.utc).isoformat(),'document_sha256':start_sha,'method':'All21 PNG files were actually emitted using view_image(detail="original") and visually inspected individually at original size; no montage/thumbnail substitute. This JSON records observations after visual inspection, not an automated visual pass.','pages':pages,'blocking_visual_issue_n':0,'optional_notes':[{'page':13,'note':'[39]上标落到行首，可选避免引文起行。'}]}
save('21_page_visual_review.json',page_review)
check('document bytes unchanged by review',sha(DOC)==start_sha)
report={'status':'PASS' if not fail else 'FAIL','review_utc':datetime.now(timezone.utc).isoformat(),'document':{'path':str(DOC),'sha256':start_sha},'sources':{name:{'path':str(path),'sha256':sha(path)} for name,path in [('old_document',OLD),('numeric_independent_review',NUM),('full_aggregate_findings',FULL),('all60_detail',DETAIL),('rendered_pdf',PDF),('policy_projection',projection),('policy_extra_projection',extra),('reserved_exclusion_metadata',exclusion)]},'checks':checks,'failures':fail,'table2_numeric_entry_n':len(table2),'table2_all80_unchanged':len(table2)==80 and E.tostring(tables[1])==E.tostring(oldtables[1]),'table3_all30':table3,'section5_2_conditional_ratios_including_supplementary_reverse_SE':conditionals,'scenario_direction_checks':directions,'all60_times2_check_records':all60,'citation_groups':citation_records,'policy_short_evidence_scope':policy_evidence,'interview_short_evidence':interview,'visual_review':'21_page_visual_review.json','limits':['This is delivery and arithmetic checking; it cannot guarantee journal acceptance.','This review does not establish new independent human or machine validity. Existing A/B were initially AI代理读后由真人事后复核保留；T为AI裁定，未改写身份。','No new reserved267 original text/prediction/individual reference labels were opened. Policy interpretation uses mechanically redacted nonreserved projections only.','The reviewer previously designed candidate38; independence here is from the current manuscript authoring operations and statistical function implementation, not independent blind efficacy validation.','Six definitions and56 file composition scenarios are sensitivity scenarios, not62 independent validation experiments. Reproducing a bootstrap does not prove nominal interval coverage.','Minutes are saved edited records; no audio verification or representative respondent inference is asserted.'],'script_sha256':sha(__file__)}
save('content_delivery_review.json',report)
md=['# 最新完整稿独立交付审查','',f'结论：{report["status"]}。已逐张实际查看全部21张原尺寸页图，未发现阻断交付的字形、裁切、重叠或表格跨页问题。仅第13页[39]上标落行首，可作排版微调。未修改文档。','',f'文档：`{DOC}`',f'SHA-256：`{start_sha}`','','数值和内容核对：','','- 表2的完整OOXML与修订前保存稿相同，80个数值未变。','- 表3全部30个值按已独立重聚的原始整数句次重新计算，逐格一致；卫健规则F=60、五维总句次165。','- 第3.3节三类比例和反向条件分母明示；第5.2节Ec/F双向与S→E的分子分母、百分比一致，6定义和56构成方向/范围一致。补充反向E→S在JSON另列，正文未将其当作S→E。','- 全部60个部门条件比较×两方法再次由聚合四格重算，含定义/构成的方向与范围。没有导入作者统计函数。','- 结语为一个非空OOXML段落，视觉上跨第16—17页；附录A/B在参考文献前。','- 文内序号首次出现为1—66连续，全部数字引文为上标；66条参考文献内容与修订前相同。','- 已核政策短证据支持目录准入、安全/疗效优势及费用可负担解释；医保纪要P004和史录文纪要P002/P015原件支持相关转述与日期。','','逐页实际检查：','']
for p in pages:md.append(f'- 第{p["page"]}页：{p["observation"]}')
md+=['','此审查不能保证录用，也不构成新的独立效度证明。原预留家族的已暴露标记保持；未读取其他预留原句、个体判断或标签。现有A/B为代理初读经真人事后复核后保留，不能据交付检查重写为首次独立盲评。','',f'机械检查数：{len(checks)}；失败数：{len(fail)}。详见 `content_delivery_review.json` 与 `21_page_visual_review.json`。']
(OUT/'独立交付审查.md').write_text('\n'.join(md)+'\n')
save('review_seal.json',{'review_utc':datetime.now(timezone.utc).isoformat(),'document_unchanged_sha256':sha(DOC),'files':{f.name:sha(f) for f in OUT.iterdir() if f.is_file() and f.name!='review_seal.json'},'failures':fail})
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':fail,'out':str(OUT),'content_sha256':sha(OUT/'content_delivery_review.json'),'visual_sha256':sha(OUT/'21_page_visual_review.json'),'markdown_sha256':sha(OUT/'独立交付审查.md')},ensure_ascii=False))
