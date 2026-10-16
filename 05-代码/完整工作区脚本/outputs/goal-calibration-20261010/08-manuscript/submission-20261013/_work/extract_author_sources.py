"""Read-only extraction of actual historical author statements."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from datetime import datetime,timezone
import hashlib,json

BASE=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
ARCHIVE=BASE.parent/'创新药论文-完整归档-20260914'
OUT=BASE/'outputs/goal-calibration-20261010/08-manuscript/submission-20261013/_work'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def bind(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def text(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
paths=[BASE/n for n in [
 '0815论文修订稿v2-创新药评价的认知分歧-科学决策版式.docx',
 '0815论文修订稿-制度视角下创新药多主体评价的认知分歧与协调路径-科学决策版式.docx',
 '0813论文终稿-制度视角下创新药多主体评价的认知分歧与协调路径-科学决策版式-已核查带批注.docx',
 '0807论文正文-制度视角下创新药多主体评价的认知分歧与协调路径-王孝炯意见.docx',
 '论文正文-制度视角下创新药多主体评价的认知分歧与协调路径.docx',
 '智库论文/制度视角下创新药多主体评价的认知分歧与协调路径-0630.docx',
 'outputs/autocode-v25-20260927/manuscript_root_review/视觉收尾前快照/论文修订稿-署名版.docx']]
paths += [ARCHIVE/'12-投稿定稿工作区'/part/'论文修订稿-署名版.docx' for part in ['重跑修订稿-20260927','期刊论述修订-20260927']]
records=[]
for p in paths:
    with ZipFile(p) as z:
        ps=E.fromstring(z.read('word/document.xml')).xpath('.//w:body/w:p',namespaces=NS)
        paragraphs=[{'paragraph_1_based':i+1,'text':text(x)} for i,x in enumerate(ps)
                    if (i<7 and ('作者' in text(x) or '单位' in text(x) or '王孝炯' in text(x)))
                    or text(x).startswith('WANG Xiaojiong') or ('英文署名待补充' in text(x))]
        notes=[]
        for part in ('word/footnotes.xml','word/endnotes.xml'):
            if part in z.namelist():
                x=E.fromstring(z.read(part))
                for note in x:
                    t=text(note)
                    if t.strip():notes.append({'part':part,'id':note.get('{'+NS['w']+'}id'),'text':t})
        records.append({'binding':bind(p),'author_related_paragraphs':paragraphs,'notes':notes,
                        'has_actual_named_author_list':any(x['text']=='［王孝炯　陈海婷　刘中全］' for x in paragraphs)})
actual=[r for r in records if r['has_actual_named_author_list']]
assert len(actual)==3
zh={p['text'] for r in actual for p in r['author_related_paragraphs'] if p['text'].startswith('［王孝炯')}
en={p['text'] for r in actual for p in r['author_related_paragraphs'] if p['text'].startswith('WANG Xiaojiong')}
bio={p['text'] for r in actual for p in r['author_related_paragraphs'] if p['text'].startswith('作者简介：')}
fund={n['text'].strip() for r in actual for n in r['notes'] if '基金项目：' in n['text']}
assert len(zh)==len(en)==len(bio)==len(fund)==1
qa_path=ARCHIVE/'12-投稿定稿工作区/陈海婷作者简介补充QA.json'
qa=json.loads(qa_path.read_text())
result={'schema':'historical-author-source-restoration-v1','created_at_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Author recovery only. No manuscript body/statistics edited. No new factual author information inferred.',
 'primary_source':actual[1]['binding'],'corroborating_sources':[actual[0]['binding'],actual[2]['binding']],
 'recovered':{'author_order_zh':['王孝炯','陈海婷','刘中全'],
   'author_order_en':['WANG Xiaojiong','CHEN Haiting','LIU Zhongquan'],
   'author_line_zh_raw':next(iter(zh)),'author_line_en_raw':next(iter(en)),
   'author_biographies_raw':next(iter(bio)),
   'funding_raw':next(iter(fund)),
   'funding_program':'国家自然科学基金项目','funding_project_name':'中国新兴产业创新政策组合的绩效影响机制研究','funding_project_number':'72074204',
   'funding_template_form':'基金项目：国家自然科学基金项目（72074204）。',
   'authors':[
      {'order':1,'zh':'王孝炯','en':'WANG Xiaojiong','birth_raw':'1982.2-','sex':'男','origin_raw':'安徽合肥',
       'affiliation_raw':'中国科学院科技战略咨询研究院','position_raw':'研究员','research_field':'创新发展政策'},
      {'order':2,'zh':'陈海婷','en':'CHEN Haiting','birth_raw':'2002—','sex':'女','origin_raw':'福建建瓯人',
       'affiliations_raw':['中国科学院科技战略咨询研究院','中国科学院大学公共管理学院'],
       'position_raw':'硕士研究生','research_field':'科技创新管理与政策'},
      {'order':3,'zh':'刘中全','en':'LIU Zhongquan','birth_raw':'1988-','sex':'男','origin_raw':'河南周口',
       'affiliation_raw':'国家发改委创新驱动发展中心','position_raw':'处长、副研究员','research_field':'科技政策、生物经济'}]},
 'supporting_user_supplied_biography_record':{'binding':bind(qa_path),'record':qa},
 'conflicts':[],
 'comparison':'All three named-author manuscripts have exactly the same Chinese author order, English spelling, author biographies, and grant. Earlier Aug manuscripts contain placeholders, not alternative author lists.',
 'not_found_or_not_inferred':['Independent affiliation line with author superscript mapping','Affiliation cities and postal codes','English institution names','Corresponding author designation','Corresponding author email/phone','Any additional fourth author'],
 'missing_details_action':'Restore the confirmed three-author list and known bios/funding; do not invent postal codes, English institutional names, corresponding author, or a fourth author. Biography administrative job title may be omitted to follow the journal, with the scholarly rank retained.',
 'checked_sources':records}
(OUT/'author-source.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'primary_source':result['primary_source'],'recovered':result['recovered'],'not_found':result['not_found_or_not_inferred']},ensure_ascii=False,indent=2))
