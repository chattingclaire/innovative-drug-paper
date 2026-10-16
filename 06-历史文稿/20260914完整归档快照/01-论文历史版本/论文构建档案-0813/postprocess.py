#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-process final.docx: widen tables to 100%, add review comments at highlighted spots.
Usage: python3 postprocess.py  (run in paper dir; needs finalw/ = unpacked final.docx with comment infra from comment.py first call)
"""
import re, random, sys

random.seed(20260812)

TITLE_COMMENT = ("制度视角下创新药多主体评价的认知分歧与协调路径",
  "《科学决策》模板要求标题不超过20字，现标题23字。可考虑改为《创新药多主体评价的认知分歧与协调路径》（18字），请与王老师商定。")

COMMENTS = [
 ("作者姓名　作者姓名", "待补充：作者中文署名（多作者以空格隔开）。"),
 ("姓名（出生年-），性别，籍贯", "待补充：所有署名作者的简介，格式见模板范例：李子木（1957-），女，河南郑州人，西南交通大学公共管理学院教授，研究方向：公共管理。"),
 ("《中华人民共和国国民经济和社会发展第十五个五年规划纲要》", "不确定：全称系按十四五规划命名惯例推断，请核对正式发布的规范名称后确认。"),
 ("2026年7月", "不确定：文本收集截止时间系按语料中最新文件（2026年医保目录调整方案正式版等）推断，请按实际收集时间核改。"),
 ("剔除空白及无实质内容的片段后", "不确定：句子过滤规则系根据数据文件反推（切分符含句号、分号、问号，剔除空白片段），请对照当时的编码脚本核实表述。"),
 ("2025年2月至6月", "不确定：访谈时间范围系按项目内纪要文件日期（2月百济座谈、3月研讨会、6月两次访谈）推断，请核实。"),
 ("2场", "不确定：一对一深度访谈场次系按现有纪要（史录文教授0609、医保评审专家0616）推断为2场，如有其他未存档访谈请补充。"),
 ("3场", "不确定：专家研讨场次按0319专家研讨会、0514课题研讨会、0212百济神州座谈计为3场，请核实口径。"),
 ("医疗机构药事管理与医保目录评审领域资深专家1人、医疗保障评审领域专家1人", "不确定：访谈对象描述基于两份纪要推断，请核实身份表述是否准确、是否同意此种匿名化描述。"),
 ("1.5-2.5小时", "不确定：访谈时长为估算值，请按实际核改。"),
 ("13名", "不确定：研讨会专家数按0319研讨会9名发言专家+0514研讨会4名药企准入专家合计13名，请核实。"),
 ("药品监管部门专家未能安排一对一访谈", "请确认：项目文件中未见药监（CDE）领域一对一访谈纪要（0421调研清单中为计划事项）。若实际访谈过请补充并修改此句；若确未访谈请保留此说明。"),
 ("2025年5月课题研讨会", "依据：0514研讨会议程第3项（聚焦研究方向、修改访谈和调研问题）。请确认提纲确经该次会议修订。"),
 ("6万字", "不确定：转录文字量为估算（两份纪要约2.5万字+研讨会转录约2.9小时），请按实际转录规模核改。"),
 ("资料由两名研究人员分别整理并交叉核对", "请确认：是否确有两名研究人员分别整理并交叉核对；如无此流程请删除该句，不可虚构。"),
 ("请从编码脚本导出96个关键词全表", "待补充：96词全表当时的中间文件已无法找回，需从编码脚本重新导出。词典编码的逐句结果建议一并存档，否则κ系数无法复算。"),
 ("版本号待补充", "待补充：LLM具体版本号、温度等参数设置、编码提示词全文，均需从当时的调用脚本或记录中导出，不可凭记忆填写。"),
 ("三个主题模块的具体访谈问题", "待补充：访谈提纲原文（三个主题模块的具体问题）。"),
 ("最高150点的企业自评量表", "建议补充政策出处：国家医保局《关于建立新上市化学药品首发价格形成机制 鼓励高质量创新的通知》（2024）；请核实该文件生效状态（征求意见稿/试行）后决定是否列入参考文献。"),
 ("英文署名待补充", "待补充：英文署名。格式：姓全大写，双字名首字母大写、以短横线连接，如 LI Zi-mu。"),
]

def esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def pid():
    return ''.join(random.choice('0123456789ABCDEF') for _ in range(8))

# ---- 1) widen tables ----
p='finalw/word/document.xml'
s=open(p,encoding='utf-8').read()
s=re.sub(r'<w:tblW [^/]*/>','<w:tblW w:w="5000" w:type="pct"/>',s)
def ins(m):
    seg=m.group(0)
    if 'w:tblW' in seg: return seg
    return seg.replace('<w:tblPr>','<w:tblPr><w:tblW w:w="5000" w:type="pct"/>',1)
s=re.sub(r'<w:tblPr>.*?</w:tblPr>', ins, s, flags=re.S)
open(p,'w',encoding='utf-8').write(s)

# ---- 2) comments (assumes comment.py already created infra with the title comment id=0) ----
p='finalw/word/comments.xml'
s=open(p,encoding='utf-8').read()
if 'xmlns:w14=' not in s.split('>',2)[1]:
    s=s.replace('<w:comments xmlns:w=','<w:comments xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w=',1)
entries=[]; ext=[]; ids=[]
for i,(target,text) in enumerate(COMMENTS, start=1):
    para=pid()
    entries.append(f'<w:comment w:id="{i}" w:author="Claude" w:date="2026-08-12T15:40:00Z" w:initials="C"><w:p w14:paraId="{para}" w14:textId="77777777"><w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r><w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p></w:comment>')
    ext.append(f'<w15:commentEx w15:paraId="{para}" w15:done="0"/>')
    ids.append(f'<w16cid:commentId w16cid:paraId="{para}" w16cid:durableId="{random.randint(100000000,999999999)}"/>')
s=s.replace('</w:comments>', ''.join(entries)+'</w:comments>')
open(p,'w',encoding='utf-8').write(s)

p='finalw/word/commentsExtended.xml'
s=open(p,encoding='utf-8').read()
s=s.replace('</w15:commentsEx>', ''.join(ext)+'</w15:commentsEx>')
open(p,'w',encoding='utf-8').write(s)

p='finalw/word/commentsIds.xml'
s=open(p,encoding='utf-8').read()
s=s.replace('</w16cid:commentsIds>', ''.join(ids)+'</w16cid:commentsIds>')
open(p,'w',encoding='utf-8').write(s)

# ---- 3) anchor all comments ----
p='finalw/word/document.xml'
s=open(p,encoding='utf-8').read()
placed=0
all_c=[(0,)+TITLE_COMMENT]+[(i,)+c for i,c in enumerate(COMMENTS, start=1)]
for cid, target, _ in all_c:
    idx=s.find(target)
    if idx==-1:
        print('NOT FOUND:', target[:30]); continue
    rs=max(s.rfind('<w:r>',0,idx), s.rfind('<w:r ',0,idx))
    re_end=s.find('</w:r>',idx)+len('</w:r>')
    a=f'<w:commentRangeStart w:id="{cid}"/>'
    b=f'<w:commentRangeEnd w:id="{cid}"/><w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="{cid}"/></w:r>'
    s=s[:rs]+a+s[rs:re_end]+b+s[re_end:]
    placed+=1
open(p,'w',encoding='utf-8').write(s)
print('anchored:',placed,'/',len(all_c))
