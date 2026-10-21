from pathlib import Path
import json,hashlib,re,unicodedata,collections
from pypdf import PdfReader
O=Path('/PROJECT_ROOT/outputs/coding-v26-20260930/context_repair')
A=json.loads((O/'machine_pending_packets.json').read_text());M={z['inventory']['id']:z for z in A}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum()).lower()
def out(name,d):
 with (O/name).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
# Ranges are zero-based inclusive candidate paragraph indexes, chosen after individual source-structure review.
SEL={
'00006':([(6,16)],'补全“同时满足”的两项条件、第二项五种情形及其术语解释，确认资格对象与条件层级。'),
'00039':([(29,33)],'补全终止程序三种情形；区分本句引导的终止事由与其他程序要求。'),
'00050':([(42,44)],'补全申请说明要求的两项内容；不将下一份异议材料要求混入本引导句。'),
'00064':([(59,62)],'补全“其中”下两项，确认公共卫生急需药品和疫苗的限定；被引技术指导原则尚未取得。'),
'00094':([(87,100),(6,16)],'补全同时适用的一、二两组条件，并回接明确引用的突破性治疗临床优势条件。'),
'00096':([(88,100)],'核清本句属于第二组条件，补全五种适用范围及儿童用药子条件，保留与第一组并列关系。'),
'00260':([(88,96)],'补全随机对照试验所关注的两类问题（对照药选择、样本量比例）及原说明；不带入下一节单臂试验。'),
'00290':([(108,118)],'补全“以下两个问题”所指替代终点与患者报告结局章节，限定在临床终点选择。'),
'00762':([(310,315)],'补全同一问答列出的四项权利义务，不使用附图或下一条扩大对象。'),
'00773':([(88,94)],'补全目录外申报五种情形，另附明确援引的2020用药办法第七、八条。'),
'00779':([(95,100)],'补全目录内申报三种情形及协议有效期解释。'),
'00932':([(19,22)],'补明此小项属于重点考虑调出基本目录范围，并另附明确援引第九、十条；邻项仅定位，不自动转移标签。'),
'01043':([(60,61),(6,15)],'回接本方案第二部分（一）的完整资格条件及申报范围；另附其明确引用第七、八条。'),
'01195':([(2,10)],'补全2020申报指南目录外七种情形，另附明确援引第七、八条。'),
'01204':([(11,14)],'补全本句后两种申报情形；所称“用药范围管理暂行办法”与现有2020“用药管理暂行办法”名称不一致，不擅自替换其第十条。'),
'01289':([(67,68),(6,12)],'回接2021方案第二部分（一）的四种资格及申报要求，另附其明确援引第七、八条。'),
'01434':([(51,51)],'补表题、列头和图像核验；3.2数据保护期为3年，备注原图为空，不能继承3.1备注。'),
'01459':([(15,22)],'补全申请资格三项及创新、早期研发等子条件，保留同时满足层级。'),
'01493':([(48,52)],'补全本节三项总结内容并提供真实小节标题，明确目标适应症、诊疗方法、未满足需求。'),
'01952':([(13,18)],'补全目录内须申报后方可调整的三项情形。'),
'02133':([(152,156),(94,98),(111,120)],'补全重新谈判的两项条件，并回接第二项否定援引的常规目录、简易续约条件；不把两种条件作为本句直接事实。'),
'02237':([(3,6)],'补全30日通道三种条件，保留其择一关系和句内共同前提。'),
'02282':([(15,19)],'补全目录内药品应申报的三种条件，保留所属目录内范围。'),
'02445':([(13,18)],'补全目录内三项申报情形及协议有效期解释。'),
'02760':([(2,9)],'补全2023目录外五项申报情形，另附明确援引第七、八条。'),
'02862':([(43,44)],'原输入同段已给出研发期间风险管理计划名称；核实申请人签字页及该完整段落，不把未附整个计划内容称为缺少名称。'),
'02876':([(76,79)],'原输入已给药物警戒活动计划对象；新增其后监测与报告、评估与处理两项示例，补足示例所指。'),
'03226':([(18,23)],'补全第九条直接调出目录五项情形，保留专家评审及任选条件。'),
'03424':([(7,14)],'补全老年患者六类特征，保留开发老年适用药物这一具体语境。'),
'03703':([(22,30)],'补全政策导向的七项内容及原问答题目，保持官方问答来源性质。'),
'03864':([(93,98)],'补全协议履行四项权利义务，保持2026同版问答。'),
'03974':([(39,41)],'补全第二十一条研究者和机构两项必要条件，不扩到第二十二条。'),
'03977':([(42,45)],'补全第二十二条伦理沟通三项要求。'),
'03990':([(52,56)],'补全第二十六条安全性报告四项要求。'),
'03995':([(57,70)],'补全第二十七条知情同意十一项及第九项续段，不遗漏紧急情况和无预期获益限定。'),
'04022':([(74,79)],'补全第二十九条记录和报告五项要求，不带入下一条报告要求。'),
'04044':([(90,93)],'补全第三十六条服务供应商三项委托要求。'),
'04095':([(123,129)],'补全第四十六条制备、供应、管理六项要求，并确认申办者责任主语。'),
'04233':([(2,9)],'补全2022目录外六项申报情形，另附明确援引第七、八条。'),
'04338':([(8,10)],'补全药师任职资格、经验及培训考核两项条件。'),
'04377':([(49,54)],'补全中药饮片处方五项审核内容。'),
'04386':([(59,64),(8,10)],'补全开展处方审核五项必备条件，并回接明确引用第五条人员条件。'),
'04418':([(12,18)],'补全省级部门五项注册管理职责，保留其后省级技术机构说明但不外推其他条职责。'),
'04566':([(120,126)],'补全中检院/指定机构承检四类药品，并保留其他机构分工说明以确认对象边界。'),
'04594':([(145,149)],'补全第六十三条附条件批准三种情形。'),
'04631':([(184,188)],'补全需补充申请批准后实施的四类变更。'),
'04651':([(203,209)],'补全不予再注册五种情形及其注销后果。'),
'04658':([(211,217)],'补全形式审查五种受理决定及同条缴费要求。'),
'04709':([(251,253)],'补全注册核查的两项时限要求。'),
'04712':([(254,257)],'补全注册检验三项时限要求。'),
'04738':([(276,284),(203,209)],'补全注销证书八种情形；回接其第二项明确引用的不予再注册条款。'),
'04752':([(291,294),(53,55),(73,74)],'补全罚则三种情形及明确援引第二十八、三十三条，区分处罚引导与被罚义务。'),
'04827':([(20,20)],'原输入已包含第十四项全部实质句和责任括注；确认责任对象，不新增其他条款作为证据。')}
cache={};sources={};contexts=[];verif=[]
def getdoc(rid):
 z=M[rid];x=z['rule_input']['input'];f=x['candidate_file']
 if f not in cache:cache[f]=json.loads(Path(f).read_text())
 assert h(f)==x['candidate_sha256']
 return z,x,cache[f]
def source(path):
 if path not in sources:
  p=Path(path);v={'path':path,'sha256':h(p),'kind':p.suffix}
  if p.suffix.lower()=='.pdf':v['pages']=[p.extract_text() or '' for p in PdfReader(path).pages]
  else:v['text']=p.read_text()
  sources[path]=v
 return sources[path]
def collect(rid,ranges,relationship):
 z,x,d=getdoc(rid);blocks=[]
 for lo,hi in ranges:
  for idx in range(lo,hi+1):
   p=d['paragraphs'][idx];path=p.get('source_file') or x.get('unit_source') or d['source'];s=source(path)
   pg=p.get('pages',[]);raw='\n'.join(s['pages'][i-1] for i in pg) if 'pages' in s else s['text']
   check=canon(p['text']) in canon(raw)
   blocks.append({'paragraph_id':p['id'],'text':p['text'],'text_representation':'原有候选段落规范化文本（标点/空白以候选版为准）；原文件/页定位可回查','pages':pg,'source_lines':p.get('source_lines',[]),'candidate_line_ids':p.get('line_ids',[]),'candidate_path':x['candidate_file'],'candidate_sha256':x['candidate_sha256'],'source_path':path,'source_sha256':s['sha256'],'relationship':relationship,'source_normalized_substring_verified':check})
   verif.append({'unit':rid,'paragraph':p['id'],'path':path,'pages':pg,'verified':check})
 return blocks
for suffix,(ranges,why) in SEL.items():
 rid='RECODE25-'+suffix;z,x,d=getdoc(rid)
 sp=x.get('unit_source') or x['source'];assert h(sp)==(x.get('unit_source_sha256') or x['source_sha256'])
 blocks=collect(rid,ranges,'本句及其明确指向的结构范围')
 if suffix in ['00773','01043','01195','01289','02760','04233']:blocks+=collect('RECODE25-03226',[(8,17)],'被引《基本医疗保险用药管理暂行办法》第七、八条')
 if suffix=='00932':blocks+=collect('RECODE25-03226',[(18,27)],'被引《基本医疗保险用药管理暂行办法》第九、十条')
 # Presence checks use actual supplied context strings, not just file availability.
 def allstrings(a):
  if isinstance(a,str):yield a
  elif isinstance(a,dict):
   for v in a.values():yield from allstrings(v)
  elif isinstance(a,list):
   for v in a:yield from allstrings(v)
 old_rule=list(allstrings({k:v for k,v in x.items() if k not in ['source','candidate_file','unit_source']}));old_llm=list(allstrings(z['llm_input']['contexts']))
 for b in blocks:
  b['present_in_original_rule_input']=any(canon(b['text']) in canon(v) for v in old_rule)
  b['present_in_original_llm_contexts']=any(canon(b['text']) in canon(v) for v in old_llm)
 gaps=[]
 if suffix=='00064':gaps=['本地给定归档及outputs按文件名检索未取得被明确援引的《药品附条件批准上市技术指导原则》全文；只补同文“其中”两项，不能声称关键资格条件已全部核清。']
 if suffix=='01204':gaps=['原PDF称《基本医疗保险用药范围管理暂行办法》第十条，与现有2020年《基本医疗保险用药管理暂行办法》名称不同；本轮不猜测更名或误引，未附一个未经确认的替代第十条。']
 status='partially_supplemented_with_gap' if gaps else ('existing_context_confirmed' if suffix in ['02862','04827'] else 'supplemented')
 rec={'id':rid,'original_id':z['inventory']['original_id'],'unit_text':z['inventory']['text'],'unit_text_sha256':z['inventory']['unit_text_sha256'],'source_title':z['inventory']['source_title'],'repair_status':status,'material_explanation':why,'context_blocks':blocks,'unresolved_material_gaps':gaps,'original_pending_reason_record':str(O/'all_pending_reason_records.json')+'#'+rid,'usage_boundary':'仅用于恢复原分析单元的对象、指代、限定与明确引用。原单元正文及边界保持不变；不得把后项、同节或被引条文的所有标签复制给本单元。本文件不裁定任何维度标签。'}
 if suffix=='01434':
  table=json.loads(Path(sp).read_text())['tables'][2];ip=table['source_image'];assert h(ip)==table['source_sha256']
  rec['verified_table_context']={'table_title':table['title'],'columns':table['columns'],'target_row':table['rows'][3],'source_image':ip,'source_sha256':h(ip),'source_url':table['source_url'],'visual_observation':'本次实际查看附表3原图：第一列3类跨3.1—3.4合并；3.2位于内容列；数据保护期为3年；备注单元为空，横线与上一3.1备注分开，不能向下继承。','present_in_original_rule_input':False,'present_in_original_llm_contexts':False,'added_information':'表头、所属表类、合并关系与空白备注的核实'}
 contexts.append(rec)
out('source_repair_working.json',{'status':'source_context_only_no_labels','records':contexts,'verification_checks':verif})
out('source_text_extractions.json',[v for v in sources.values()])
print('units',len(contexts),'paragraph_checks',len(verif),'failed',sum(not x['verified'] for x in verif))
for x in verif:
 if not x['verified']:print(x)
