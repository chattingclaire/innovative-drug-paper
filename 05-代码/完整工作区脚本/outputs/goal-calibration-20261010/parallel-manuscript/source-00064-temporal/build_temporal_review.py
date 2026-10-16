#!/usr/bin/env python3
"""Reconcile source chronology only, preserving an unresolved reference."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import hashlib
import zipfile
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parent
def read(name): return json.loads((BASE/name).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,obj): (BASE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def link(label,url): return '['+label.replace('|',r'\|')+'](<'+str(url)+'>)'
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
a=read('pre2017-review.json'); b=read('pre2019-review.json'); c=read('bridge-review.json'); r=read('root-source-review.json')
unit=read('snapshots/RECODE25-00064-only.json')
original_read=read('root-july-original-read.json')
bs={x['id']:x for x in c['sources']}
s2017={x['id']:x for x in a['sources']}
bc={x['candidate_id']:x for x in b['candidates']}

def carrier(path,expected=None,role='source'):
    return {'path':str(path),'sha256':expected or sha(path),'role':role}

records=[]
def add(rid,title,issuer,composition,publication,effective,draft,role,urls,carriers,locator,reading,meaning,**extra):
    records.append({'id':rid,'full_title':title,'issuer':issuer,'composition_date':composition,
                    'publication_date':publication,'effective_date':effective,'draft_status':draft,
                    'source_role':role,'urls':urls,'carriers':carriers,'locator':locator,
                    'actual_reading_level':reading,'interpretive_limit':meaning,**extra})

s=s2017['S1']; annex=s2017['S2']
add('T2017','临床急需药品有条件批准上市的技术指南（征求意见稿）',
    '食品药品监管总局办公厅（通知）；药品审评中心组织起草',
    '2017-12-13（通知落款；附件无独立成文日）','2017-12-20',None,'征求意见稿','official_original_notice_and_attachment',
    [s['url'],annex['url']],
    [carrier(s['local_path'],s['sha256'],'original_notice'),carrier(annex['local_path'],annex['sha256'],'original_draft_doc')],
    '通知发布日期/落款/征求截止；附件封面及末条第20条',
    '代理读取官方通知、原始DOC；PDF镜像首页及第6页视觉核对，镜像正文与原DOC比对',
    '属于草案；末条拟定“自发布之日起施行”不产生已施行日期，不能绑定7月引用。',
    consultation_deadline='2018-01-14（当时通知）',later_history_deadline='2018-01-15（2019起草说明回顾）')
s=bc['2019-original-drafting-explanation']
add('H2018','《临床急需药品附条件批准上市技术指导原则》起草说明所记2018年定向征求意见',
    '国家药品监督管理局药品审评中心',None,'2019-11-08（说明附载日期）',None,'定向征求意见过程的后来回顾','official_original_drafting_history',
    [s['primary_url'],s['parent_notice_url']], [carrier(s['local_source']['local_file'],s['local_source']['sha256'],'original_explanation_docx')],
    '2019原始起草说明第12段','代理读全部22段起草说明；本次不以内部过程推定发布/施行',
    '没有取得独立的2018正式发布指南；定向征求意见不是正式版发布证明。',
    event_year='2018（仅历史过程年份；不作成文日期）')
s=bc['2019-original-guideline-draft']; notice=bc['2019-original-notice']; history=bc['2019-original-drafting-explanation']
add('T2019',s['full_title'],'国家药品监督管理局药品审评中心',
    '2019-11-08（通知署日；附件未独立署日）','2019-11-08',None,'再次公开征求意见稿','official_original_notice_and_docx',
    [notice['primary_url'],s['primary_url'],history['primary_url']],
    [carrier(s['local_source']['local_file'],s['local_source']['sha256'],'original_draft_docx'),carrier(history['local_source']['local_file'],history['local_source']['sha256'],'original_drafting_explanation_docx'),
     carrier(notice['local_browser_read_evidence']['local_file'],notice['local_browser_read_evidence']['sha256'],'original_notice_browser_read_record')],
    '通知发布日期/署日/截止；原DOCX第1–3段；起草说明第6/9/12/14/17段',
    '代理直接读CDE渲染通知及官方链接下载DOCX；指南核标题/稿别/日期词，起草说明全部22段',
    '确认2017→2019改题名和征求意见沿革；不确认2019稿已施行，也不把它唯一绑定为7月被援稿。',
    consultation_deadline='2019-11-13 17:00',file_metadata_not_legal_date=True)
s=bs['B07']
add('LAW2020',s['title'],s['issuer'],'2020-01-22','2020-03-30（当前官方法规页显示日期）','2020-07-01','正式部门规章','official_regulation_registry',
    [s['url']],[carrier(s['artifact']['local_path'],s['artifact']['sha256'],'official_registry_html')],
    '第8条、第61条、第63–67条；网页日期与附则','代理读SAMR官方法规原文相关条款',
    '第61条是突破性治疗政策支持；第63–67条是附条件批准法规范依据。可并列，不是被援技术指南稿本。')
s=bs['B06']
add('TRANS46',s['title'],s['issuer'],'2020-03-30',None,None,'正式公告','official_government_republication_and_original_scan',
    [s['url'],s['original_pdf_url']],
    [carrier(s['artifact']['local_path'],s['artifact']['sha256'],'official_reprint_html'),carrier(s['original_pdf_artifact']['local_path'],s['original_pdf_artifact']['sha256'],'government_hosted_original_pdf')],
    '原PDF第1项跨物理1–2页；第4页落款、印发；官网第一项',
    '代理读官网正文；根代理视觉核PDF第1、2、4页，核一般过渡、落款及印发',
    '新配套文件陆续发布、已有新规定从其规定、未调整按现行要求的一般过渡；未指名任一附条件指南稿，不能由此授权草案。',
    printing_date='2020-03-31',official_republication_date='2020-04-10 08:52',
    publication_date_limit='未直接核定NMPA原公开日；PDF扫描创建2020-04-07不是文件发布/施行日',
    effective_date_limit='公告提及新注册办法2020-07-01施行，未单列本公告统一施行日')
s=bs['B04']; exp=bs['B03']; notice=bs['B02']
add('PROC_DRAFT2020',s['title'],s['issuer'],None,'2020-04-30',None,'征求意见稿及起草说明','official_original_docx',
    [notice['url'],s['url'],exp['url']],
    [carrier(s['artifact']['local_path'],s['artifact']['sha256'],'original_procedure_draft_docx'),carrier(exp['artifact']['local_path'],exp['artifact']['sha256'],'original_drafting_explanation_docx')],
    '程序第28–29段；起草说明第9/14–15段（XML含空段计数）',
    '代理读CDE原通知、官方DOCX相关段；起草说明具体历史与衔接表述已核',
    '官方可证2019技术指南征求意见与2020程序起草的联系；未点名7月终稿所援具体稿本。',
    proposed_effective_date_in_draft='2020-07-01（仅拟定条文）',consultation_deadline='2020-05-30',
    composition_date_limit='附件无独立落款日期；正文记2020年4月起草')
s=next(x for x in r['sources'] if x['id']=='JULY82_ATTACHMENT2'); notice=next(x for x in r['sources'] if x['id']=='JULY82_NOTICE')
add('PROC_FINAL2020',s['title'],s['issuer'],'2020-07-07（公告落款）','2020-07-08','2020-07-08（自发布之日起）','正式试行工作程序','official_original_html_and_binary_doc',
    [notice['url'],s['url']],notice['carriers']+s['carriers'],
    '原始附件2 TXT L3–8、24–25；公告日期及施行句',
    '根代理实际下载NMPA原网页及DOC、读相关段；00064规范化原句与官方附件一致',
    '原句出处已核定；入口句和具体技术要求句均未注明指南年份、稿别或文号，具体版本仍未知。',
    reference_title_as_printed='药品附条件批准上市技术指导原则',unit_match_verified=True)
s=bs['B08']
add('COMMENT2020',s['title'],'佟路、王海辉（辉瑞投资有限公司）；中国食品药品网载文',None,'2020-07-27',None,'署名政策分析文章','contemporaneous_nongovernmental_commentary',
    [s['url']],[carrier(s['artifact']['local_path'],s['artifact']['sha256'],'commentary_html')],
    '附条件批准段；作者、末段单位及免责声明','根代理及代理直接读全文相关段与作者身份',
    '同期作者称技术指南尚未发布；企业作者观点且非本站立场，不能升为发布机关确认、正式过渡规则或版本绑定。')
s=bs['B05']
add('GUIDE_FINAL2020','药品附条件批准上市技术指导原则（试行）',s['issuer'],'2020-11-19（通告落款）','2020-11-19','2020-11-19（通告自发布之日起）','正式发布、试行技术指南','official_current_download_and_original_notice',
    [s['url'],s['attachment_url'],s['reprint_url']],
    [carrier(s['attachment_artifact']['local_path'],s['attachment_artifact']['sha256'],'current_official_pdf_carrier'),carrier(s['reprint_artifact']['local_path'],s['reprint_artifact']['sha256'],'official_notice_reprint_html')],
    'CDE通知日期/落款/施行；PDF物理第1页封面2020年11月',
    '代理读CDE原通知及官方转载；根代理视觉核官方PDF封面，不声称通读11页',
    '能核后续正式版本；晚于7月。不能以它填补当时未注明的指南条件或宣布回溯适用。',
    notice_number='2020年第41号',official_republication_date='2020-11-25 10:10',
    digital_carrier_creation_date='2022-10-09（pdfinfo）',
    byte_history_limit='现代官方PDF封面2020年11月；文件数字生成于2022，不改变通告年，也不证明2020发布时与现载体字节相同。')

unresolved=[
    '2020年7月工作程序所援技术指导原则的具体年份、稿别及版本仍未唯一核明。',
    '未取得2020-07-08以前同名或沿革可唯一对应的正式/试行指南发布证据；有界检索未命中不能证明不存在未索引或内部稿。',
    '未取得发布机关明确指定2019征求稿于7月适用，或明确将该援引解释为某一未来正式稿的版本专门说明。',
    '第46号公告为一般过渡，不确定何种具体既有指南/内部标准在7月适用，也不自动把征求稿转为现行要求。',
    '2017当时通知与2019起草说明回顾的首次征求截止日分别为2018-01-14和2018-01-15；并列记录差异，不用搜索摘要或后稿静默统一。',
]
reporting={
    'recommended_status':'unresolved_contemporaneous_reference_version',
    'verified_part':'00064字面出处和2020年7月正式程序载体已核定；2017/2019征求意见稿原件及官方起草沿革已取得。',
    'source_note':'2020年7月正式工作程序援引的技术指导原则未标注年份或稿本。官方2017与2019征求稿及2020程序起草说明可证开发沿革，第46号公告可证一般过渡；所取得原文均未唯一指定7月应适用的技术指南稿本。2020年第41号指南于11月19日正式发布施行，作为后续版本单列。',
    'handling':['保留RECODE25-00064及既有材料问题记录，不在本分支赋任何维度标签、改手册或替换来源接口。',
                '来源包可并列7月程序本身、当时法规范及候选沿革，明确区分直接原文与未决援引；法规范不改名成被援技术指南。',
                '后续判读若仍需未决外部条文，材料状态保持未决并同步所有接口；不将缺口补0、删除单位或伪称已补全。',
                '若日后取得发布机关版本专门证据，另存并核日期/稿别后再评估是否可补；当前不强行解决。'],
    'avoid_claims':c['reporting_recommendation']['avoid_claims'],
    'research_claim_limit':'本包不完成human首判、裁定、整体freeze或指标验收，不以来源恢复宣布这些工作已完成。',
}
doc={
    'schema':'source-00064-temporal-v1','created_at':now,'record_id':'RECODE25-00064','material_id':'MATERIAL00064',
    'status':'unresolved_contemporaneous_reference_version','requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra',
    'scope':{'writes_restricted_to':str(BASE),'new_coding_results_read':False,'labels_assigned':False,'manuscript_modified':False,'prior_reference_plan_modified':False,'source_only_record_read':'RECODE25-00064 only'},
    'source_only_unit':unit['unit_text'],'unit_text_sha256':unit['unit_text_sha256'],
    'original_source_file_sha256':unit['source_position']['source_sha256_recorded'],
    'verified_literal_provenance':original_read,
    'timeline':records,'remaining_unresolved':unresolved,'reporting_recommendation':reporting,
    'date_conflicts':[{'topic':'first_consultation_deadline','contemporaneous_2017_notice':'2018-01-14','2019_drafting_history':'2018-01-15','resolution':'retain_both_with_attribution_not_silent_rewrite'}],
    'bounded_search':b['bounded_original_site_search'],
    'source_reviews':[str(BASE/x) for x in ['pre2017-review.json','pre2019-review.json','bridge-review.json','root-source-review.json']],
    'direct_pdf_visual_reads':[{'path':bs['B05']['attachment_artifact']['local_path'],'pages':[1],'reading':'cover only; official title and 2020年11月'},
                               {'path':bs['B06']['original_pdf_artifact']['local_path'],'pages':[1,2,4],'reading':'general transition and signed/printing dates; not OCR or whole4pages claim'}],
}
save('source-timeline.json',doc)

root_log=read('root-search-log.json')
logs={'created_at':now,'limit':'成功读取、响应失败、站内未命中和候选稿身份分开。未命中不证明不存在；200/202响应不自动等于原DOCX/PDF。',
      'root':{'search_and_open':root_log,'retrieval':read('root-retrieval-log.json'),'original_attachment':read('root-july-attachment-retrieval.json')},
      '2017':{'search':a['search_log'],'retrieval':a['retrieval_log']},
      '2019':{'bounded_site_search':b['bounded_original_site_search'],'logs':[]},
      'bridge':{'search_batches':c['search_batches'],'retrieval':c['retrieval_attempts']}}
for path in b['search_and_failure_logs']:
    q=Path(path);logs['2019']['logs'].append({'path':str(q),'sha256':sha(q),'entries':json.loads(q.read_text())})
save('search-log.json',logs)

lines=['# MATERIAL00064：所援技术指南版本与时间轴','',
       '**00064字面出处已核定；2020年7月所援技术指南的具体版本仍未唯一核明。状态保持 `unresolved_contemporaneous_reference_version`。**','',
       '本轮只读指定来源单位、来源调查/manifest及相关原始政策指南；未读新编码结果、未赋维度标签、未改正文或此前23核心引用预案。','',
       '## 可核时间轴','',
       '| 文件／过程 | 成文、公开、施行／稿别 | 证据与结论边界 |','|---|---|---|']
for x in records:
    dates='成文：'+str(x['composition_date'] or '未独立核定')+'；公开：'+str(x['publication_date'] or '未独立核定')+'；施行：'+str(x['effective_date'] or '不作已施行认定')+'；'+x['draft_status']
    if x.get('event_year'):dates+='；过程年份：'+x['event_year']
    if x.get('consultation_deadline'):dates+='；征求截止：'+x['consultation_deadline']
    if x.get('official_republication_date'):dates+='；官方转载：'+x['official_republication_date']
    lines.append('| '+x['id']+' '+link(x['full_title'],x['urls'][0])+' | '+dates+' | '+x['interpretive_limit']+' |')
lines += ['', '## 已核定与仍未核定的关系','',
          '7月NMPA原公告和原始附件2已直接下载。00064原句在官方DOC中存在，正文第一部分入口句、第三部分（三）均使用未注明版本的技术指南名。公告落款2020-07-07，页面公开2020-07-08，正式程序自发布之日起施行。4月征求稿拟定2020-07-01不作终稿施行日。','',
          '2017官方原DOC封面明确“征求意见稿”。2019 CDE原通知及两份原DOCX也已恢复；其起草说明记录2017公开征求、2018定向征求、2019内部征求及改题名过程。2017“有条件批准上市的技术指南”改为2019“附条件批准上市技术指导原则”的沿革有原文依据，但名称沿革不能自动建立7月引用的具体稿本身份。','',
          '2020年4月官方程序起草说明明确记载2019-11-08技术指南征求意见、2020年4月结合技术指南起草程序，并设置衔接条款。它证明起草联系，未宣布2019草案施行或指名7月终稿所援版本。','',
          '2020年第46号公告第一项规定配套文件陆续发布的一般过渡安排。官网正文及政府保存扫描PDF均可核；根代理视觉读第1、2、4页，确认3月30日落款、3月31日印发。一般过渡没有指定某个附条件指南稿本，不能据此将征求稿认作现行指南。原NMPA公开日未本轮核定，吉林转载为4月10日。','',
          '当时《药品注册管理办法》第63–67条可作为并列法规范依据；第61条属于突破性治疗政策支持。它们不替代被援指南，也不能以法规范较相似的条件反推所援稿本。','',
          '2020-07-27中国食品药品网文章提到技术指南尚未发布。作者为辉瑞投资有限公司人员，页尾限定作者观点。它只提供同期观察，不作为发布机关的版本或过渡确认。','',
          '## 日期与数字载体差异','',
          '- 2017当时通知写征求截止2018-01-14；2019起草说明第6/9段回顾为2018-01-15。两值及来源并列，不静默统一。',
          '- 草案末条“自发布之日起施行”或拟定7月1日属于草案内容，不产生正式施行日期。',
          '- 当前CDE官方下载正式指南PDF封面为2020年11月，文件CreationDate为2022-10-09。数字载体生成日期不改通告2020-11-19发布年；也不声称已核2020上传时同一字节。',
          '- 46号扫描PDF的创建日期2020-04-07不替代3月30日成文、3月31日印发或未知原公开日。','',
          '## 检索边界与读取层级','',
          'CDE当前站内以技术指南标题、2000-01-01至2020-07-08日期筛选仅返回2019征求意见通知。结合官方网页、原附件和官方转载，本轮未核得此前正式/试行指南或明确指名稿本的实施说明。这个结果只反映本轮可达来源和索引范围，不证明未索引/内部稿不存在。','',
          'CDE旧链接曾返回404、202防护HTML或空正文；现代原页经内置浏览器可读，官方链接下载取得真实DOCX/PDF。失败响应与成功载体分别保留，不把HTTP响应、搜索摘要或相似标题记作绑定通过。','',
          '读取为定点原文核查：2017原通知/DOC及PDF镜像相关页；2019原通知、DOCX标题/稿别与完整22段起草说明；2020程序和起草说明相关段、法规范相关条款；11月通告和官方PDF封面。未声称读完正式指南11页。','',
          '## 可以怎样真实报告','',reporting['source_note'],'']
for x in reporting['handling']:lines.append('- '+x)
lines += ['','本包不完成真人首判、裁定、整体冻结或任何新指标验收。','',
          '## 直接原件与哈希','',
          '| ID | 直接可核载体 | SHA256 | 实际定位 |','|---|---|---|---|']
for x in records:
    for e in x['carriers']:
        lines.append('| '+x['id']+' | '+link(Path(e['path']).name,e['path'])+' | `'+e['sha256']+'` | '+x['locator']+' |')
lines += ['', '- '+link('完整时间轴与未决项JSON',BASE/'source-timeline.json'),
          '- '+link('成功／失败检索总记录',BASE/'search-log.json'),
          '- '+link('本轮来源载体manifest',BASE/'source-manifest.json'),
          '- '+link('冻结输入',BASE/'input-manifest.json'), '']
(BASE/'source-timeline.md').write_text('\n'.join(lines))

# Manifest covers source carriers and snapshots; no file outside this directory
# is created, relabeled, or replaced.
manifest=[]
for folder in ['sources','snapshots']:
    for path in sorted((BASE/folder).rglob('*')):
        if path.is_file():
            role='captured_source_or_response_see_retrieval_log'
            if path.suffix=='.png':role='derived_visual_check_not_original_policy'
            if folder=='snapshots':role='read_only_input_snapshot'
            manifest.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'role':role})
save('source-manifest.json',{'created_at':now,'scope':'hash identifies bytes, not formal version binding; responses and authentic sources distinguished in logs','files':manifest})

checks=[]
def check(name,ok,detail=None): checks.append({'check':name,'passed':bool(ok),'detail':detail})
check('status_stays_unresolved',doc['status']=='unresolved_contemporaneous_reference_version')
check('one_source_record_only',unit['id']=='RECODE25-00064' and doc['scope']['source_only_record_read']=='RECODE25-00064 only')
check('unit_text_hash_matches',hashlib.sha256(unit['unit_text'].encode()).hexdigest()==unit['unit_text_sha256'])
check('original_july_sentence_found',original_read['normalized_unit_sentence_found_in_original_attachment'])
check('no_labels_or_manuscript_edit',not doc['scope']['labels_assigned'] and not doc['scope']['manuscript_modified'])
check('agents_no_new_coding',not a['new_coding_results_read'] and not b['new_coding_results_read'] and not c['scope_controls']['new_coding_results_read'])
check('agents_no_label_assignment',not a['label_assigned'] and not b['label_assigned'] and not c['scope_controls']['labels_assigned'])
check('past_drafts_not_marked_effective',all(x['effective_date'] is None for x in records if x['id'] in ['T2017','T2019','PROC_DRAFT2020']))
check('later_formal_guide_after_july',next(x for x in records if x['id']=='GUIDE_FINAL2020')['publication_date']>next(x for x in records if x['id']=='PROC_FINAL2020')['publication_date'])
check('consultation_deadline_conflict_retained',doc['date_conflicts'][0]['contemporaneous_2017_notice']!=doc['date_conflicts'][0]['2019_drafting_history'])
check('current_official_docx_zip',all(zipfile.is_zipfile(x) for x in [bs['B03']['artifact']['local_path'],bs['B04']['artifact']['local_path'],bc['2019-original-guideline-draft']['local_source']['local_file'],bc['2019-original-drafting-explanation']['local_source']['local_file']]))
check('july_original_doc_binary',Path(original_read['source_doc']).read_bytes().startswith(bytes.fromhex('d0cf11e0a1b11ae1')))
for x in records:
    check('candidate_full_title_status_and_layer_'+x['id'],bool(x['full_title'] and x['draft_status'] and x['actual_reading_level'] and x['locator']))
    for e in x['carriers']:check('candidate_hash_'+x['id']+'_'+Path(e['path']).name,sha(e['path'])==e['sha256'])
for e in read('input-manifest.json')['files']:check('frozen_input_'+Path(e['snapshot_path']).name,sha(e['snapshot_path'])==e['sha256'])
for e in manifest:check('carrier_in_directory_'+Path(e['path']).name,Path(e['path']).is_relative_to(BASE) and sha(e['path'])==e['sha256'])
for name in ['source-timeline.json','search-log.json','source-manifest.json']:check('json_parse_'+name,isinstance(read(name),dict))
validation={'created_at':now,'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL','checks_total':len(checks),'failures':[x for x in checks if not x['passed']],'checks':checks,'limit':'文件及来源链完整性核查通过不等于解决指南稿本，不等于human或指标验收。'}
save('verification.json',validation)
if validation['status']!='PASS':raise RuntimeError(validation['failures'])
outputs=[]
for path in sorted(BASE.rglob('*')):
    if path.is_file() and path.name!='交付封存.json' and '__pycache__' not in path.parts:outputs.append(carrier(path))
save('交付封存.json',{'created_at':now,'status':'source_review_complete_reference_version_unresolved','validation_status':validation['status'],'checks_total':len(checks),'outputs':outputs,'labels_assigned':False,'manuscript_modified':False,'prior_reference_plan_modified':False})
print(json.dumps({'status':doc['status'],'timeline_records':len(records),'source_carriers':len(manifest),'verification':validation['status'],'checks':len(checks),'sealed_files':len(outputs)},ensure_ascii=False))
