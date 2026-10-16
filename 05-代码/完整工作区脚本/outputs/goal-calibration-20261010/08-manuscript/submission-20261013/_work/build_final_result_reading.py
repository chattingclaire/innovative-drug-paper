from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
import hashlib,json,re
WOR=Path(__file__).resolve().parent
SRC=WOR.parent/'创新药评价的注意力配置差异与协调路径-署名信息补全版.docx'
DST=WOR.parent/'创新药评价的注意力配置差异与协调路径-署名阅读版-最终结果.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(n):return '{'+NS['w']+'}'+n
def tx(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def settext(p,s):
    template=next(r for r in p.findall('w:r',NS) if r.find('w:rPr/w:vertAlign',NS) is None)
    rp=template.find('w:rPr',NS)
    for c in list(p):
        if c.tag!=W('pPr'):p.remove(c)
    r=E.SubElement(p,W('r'))
    if rp is not None:r.append(deepcopy(rp))
    t=E.SubElement(r,W('t'));t.text=s;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
with ZipFile(SRC) as z:infos=z.infolist();pkg={i.filename:z.read(i.filename) for i in infos}
doc=E.fromstring(pkg['word/document.xml']);body=doc.find('w:body',NS)
orig=list(body);tables=body.findall('w:tbl',NS);table_keep=[E.tostring(t) for t in tables[:7]]
refs=[tx(p) for p in body.findall('w:p',NS) if re.match(r'^\[\d+\]',tx(p))]
records=[]
def replace(prefix,new):
    matches=[p for p in body.findall('w:p',NS) if tx(p).startswith(prefix)]
    assert len(matches)==1,(prefix,len(matches));p=matches[0]
    records.append({'before':tx(p),'after':new});settext(p,new)
def trim_sentence(prefix,tail):
    p=next(p for p in body.findall('w:p',NS) if tx(p).startswith(prefix));s=tx(p)
    assert s.endswith(tail);replace(prefix,s[:-len(tail)])
replace('κ用于衡量扣除机会一致后的判定一致性。','κ用于衡量扣除机会一致后的判定一致性。κ=1表示两套判定完全一致，κ=0表示与按边际比例计算的机会一致相当，负值则表示低于机会一致。P、R、F1取值为0—1，数值越大，表明机器判断与所用参照越吻合。本文结合各维度的四格、分类指标及区间，分析编码结果与人工核验结果的差异。')
replace('表2 自动规则编码与LLM编码相对于人工核验参照的分类表现','表2 两种编码方法相对于人工核验参照的设计加权分类指标')
en=next(p for p in body.findall('w:p',NS) if tx(p).startswith('Table 2 '));records.append({'before':tx(en),'after':'Table 2 Design-Weighted Classification Metrics against the Human-Reviewed Reference'});settext(en,records[-1]['after'])
replace('与人工核验结果相比，LLM在安全性、有效性、经济性和创新性上的加权κ为',
'在200条核验样本的原始对照中，LLM五维κ为0.914—1.000，P、R和F1为0.909—1.000（见附录C）。按抽样设计加权后，LLM在安全性、有效性、经济性和创新性上的κ为0.895—1.000，F1为0.908—1.000；公平性的κ和F1分别为0.788和0.791。两种编码方法的完整加权结果见表2，公平性分歧的权重解释见附录C。部门注意力分布依据全量编码比较，并进一步考察来源构成、汇总方式及待定信息对结果的影响。')
trim_sentence('为考察统计方式对结果的影响，设置九种口径：','固定800条材料的重复稳定性和请求敏感性检验，另列计划数量、技术失败、待定数量及共同可比较记录的结果。')
trim_sentence('配套材料包括统一编码手册、','重复稳定性和请求敏感性资料另列原抽样权重、各条件的有效记录数、共同可比较记录的四格及注意力占比变化。')
p=next(p for p in body.findall('w:p',NS) if tx(p).startswith('官方问答与正文分别标记，重复附件只计一次。'))
s=tx(p);tail='三部门4481条全量分布、200条人工核验资料、固定800条材料的重复及请求敏感性结果，以及开发复核资料分别保存。';assert s.endswith(tail)
replace('官方问答与正文分别标记，重复附件只计一次。',s[:-len(tail)]+'三部门4481条全量分布、200条人工核验资料及相应统计结果分别保存。')
replace('附录C\u3000编码检验与重复稳定性','附录C\u3000编码质量检验')
removed=[]
p=next(p for p in body.findall('w:p',NS) if tx(p).startswith('为考察重复编码的稳定性，在固定800条材料上'))
removed.append(tx(p));body.remove(p)
start=next(i for i,p in enumerate(list(body)) if tx(p).startswith('表C4 固定800条材料的重复及请求敏感性覆盖'))
end=next(i for i,p in enumerate(list(body)) if tx(p)=='参考文献')
for p in list(body)[start:end]:removed.append(tx(p));body.remove(p)
assert len(removed)==7
assert [E.tostring(t) for t in body.findall('w:tbl',NS)]==table_keep
assert [tx(p) for p in body.findall('w:p',NS) if re.match(r'^\[\d+\]',tx(p))]==refs
assert len(refs)==66
full=tx(body)
for forbidden in ['0.80作为开发阶段','固定800条','表C4','R1/R2','重复稳定性','请求敏感性']:
    assert forbidden not in full,forbidden
# All non-targeted body elements remain byte-identical.
changed_elements=[]
for i,p in enumerate(orig):
    if p.getparent() is None:continue
    if tx(p) in [r['after'] for r in records]:changed_elements.append(i)
assert len(changed_elements)==len(records)
pkg['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(DST,'w') as z:
    for info in infos:z.writestr(info,pkg[info.filename])
with ZipFile(SRC) as a,ZipFile(DST) as b:assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['word/document.xml']
record={'source':str(SRC),'output':str(DST),'output_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'edits':records,'removed_old_v16_content':removed,'removal_reason':'重复检验绑定v16的800条材料，不是最终v17的同版验证；整组移出而非按指标高低选择','final_result_tables':7,'final_numeric_tables_preserved_byte_identical':True,'references_preserved':len(refs),'no_encoding_or_analysis_rerun':True,'visual_review':'pending'}
(WOR/'final-result-reading-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in record.items() if k not in ['edits','removed_old_v16_content']},ensure_ascii=False,indent=2))
