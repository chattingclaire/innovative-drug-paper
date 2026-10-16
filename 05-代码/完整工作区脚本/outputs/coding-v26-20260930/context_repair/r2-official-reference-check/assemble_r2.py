from pathlib import Path
import json, hashlib, datetime
O=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-v26-20260930/context_repair')
D=O/'r2-official-reference-check'
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=json.loads((O/'machine_pending_context_supplements_v26.json').read_text())
rr={r['id']:r for r in prior['records'] if r['id'] in ['RECODE25-00064','RECODE25-01204']}
manifest=json.loads((O/'delivery_manifest_v26.json').read_text())
checks=[dict(x,unchanged=h(x['path'])==x['sha256']) for x in manifest['files']]
assert all(x['unchanged'] for x in checks)
def source(name,url,role,loc):
 p=D/name
 return {'path':str(p),'url':url,'sha256':h(p),'bytes':p.stat().st_size,'role':role,'locator':loc}
sources={
 'nhsa_announcement':source('nhsa_2020_announcement.html','http://www.nhsa.gov.cn/art/2020/8/17/art_53_3408.html','官方公告原始HTML','可见文本L9–L19；发布日期2020-08-17；附件2'),
 'nhsa_original_pdf':source('nhsa_2020_originalattachment.pdf','http://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=2edbafaf09654373a58f7e33fbeaac7d.pdf','官方公告附件PDF','PDF第2页，一（二）目录内西药和中成药'),
 'nhsa_wx_pdf':source('nhsa_2020_guide.pdf','https://wx.nhsa.gov.cn/Sites/Uploaded/File/2020/08/186373334449723857494133741.pdf','国家医保局微信站点同字节附件','PDF第2页'),
 'shrs_1999_method':source('shrs_1999_method.html','https://rsj.sh.gov.cn/trlzyhshbzbgz_17256/20200617/t0035_1388342.html','上海人社官方转载1999年办法，用于比较身份；不认定其就是目标外引','标题/文号/日期L8–L16；第十条L37–L42'),
 'nhsa_2020_method':source('nhsa_2020_method_http.html','http://www.nhsa.gov.cn/art/2020/7/31/art_173_10977.html','国家医保局官方2020年办法，用于比较身份；不自动替代目标外引','标题/文号/签发/施行L6–L12；第十条L39–L42'),
 'cde_notice_response':source('cde_2020_41_old_response.html','http://www.cde.org.cn/news.do?method=viewInfoCommon&id=e8e70cb03a94e5f2','HTTP202 HTML挑战响应；不是通告正文','正文未取得'),
 'cde_attachment_response':source('cde_guideline_http_response.bin','http://www.cde.org.cn/zdyz/downloadAtt?idCODE=eae16177a1eb066690d66f21fc711b1a','HTTP202 HTML挑战响应；不是PDF，不是技术指导原则文件hash','正文未取得'),
 'locator_only':source('locator_only_allfordrug.html','https://www.allfordrug.com/cde','非官方链接目录，只用于发现CDE附件URL，不作为政策内容证据','编号305的技术指导原则链接'),
}
oldlines=(D/'shrs_1999_method.html.visible.txt').read_text().splitlines()
newlines=(D/'nhsa_2020_method_http.html.visible.txt').read_text().splitlines()
old10='\n'.join(s.split(': ',1)[1] for s in oldlines[36:42])
new10='\n'.join(s.split(': ',1)[1] for s in newlines[38:42])
records=[]
for id in ['RECODE25-00064','RECODE25-01204']:
 r=rr[id]
 out={k:r[k] for k in ['id','original_id','unit_text','unit_text_sha256','source_title']}
 assert hashlib.sha256(out['unit_text'].encode()).hexdigest()==out['unit_text_sha256']
 out.update({'r1_record_path':str(O/'machine_pending_context_supplements_v26.json')+'#'+id,'r1_status_preserved':r['repair_status'],'no_label_judgment':True,'eligible_for_automatic_context_merge':False,'new_admissible_context_blocks':[],'empty_context_meaning':'本轮未形成可无歧义并入原单元的新增外引条件；不代表材料缺口已解决。'})
 if id.endswith('00064'):
  out.update({
   'r2_status':'official_candidate_located_fulltext_and_historical_referent_unresolved',
   'source_refs':['cde_notice_response','cde_attachment_response','locator_only'],
   'candidate':{'title':'药品附条件批准上市技术指导原则（试行）','issuer':'国家药品监督管理局药品审评中心','notice_number':'2020年第41号','publication_date_locator':'2020-11-19','date_evidence_level':'检索结果及捕获的CDE通告转载线索定位；本轮未成功取得官方通告正文或附件，不能称官方全文核验完毕。','official_reprint_urls':['https://www.ccfdie.org/zryyxxw/zxdt/webinfo/2020/11/1602453958504309.htm','https://www.ccfdie.org/cn/yjxx/yphzp/webinfo/2020/11/1602453958453674.htm'],'official_notice_url':'http://www.cde.org.cn/news.do?method=viewInfoCommon&id=e8e70cb03a94e5f2','official_attachment_url':'https://www.cde.org.cn/zdyz/downloadAtt?idCODE=eae16177a1eb066690d66f21fc711b1a','official_guideline_file_sha256':None,'fulltext_obtained':False},
   'chronology':{'citing_document_year':2020,'citing_document_publication_date_locator':'2020-07-08','citing_document_url':'https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20200708151701834.html','candidate_is_later_than_citing_publication':True,'interpretation':'同年11月正式指导原则晚于7月三程序文件；本轮没有证据证明其正式版条件与7月引文当时所指版本逐字相同，不因同年同题自动嫁接。'},
   'access_limits':['CDE旧通告URL返回HTTP202 HTML挑战页，未取得通告正文。','CDE附件HTTPS下载出现IncompleteRead；HTTP跳转后返回HTTP202 text/html，不是PDF。','交流中心官方转载页面直接请求超时或502；搜索索引可定位题名和2020年第41号。','浏览器访问附件报net::ERR_BLOCKED_BY_CLIENT；未绕过访问限制。','NMPA三程序官方页面本轮请求返回412；原研究已存同文来源未改。'],
   'verified_increment':'新增官方入口、候选年份/通告身份和时间边界记录；没有新增已核清的附条件批准实质情形条文。',
   'remaining_gap':'被引技术指导原则官方全文未取得；7月引文对应的当时版本及条件尚未核清。保留r1缺口；不以2017征求意见稿、2026工作程序或注册管理办法条文替代。'
  })
 else:
  local=Path(r['context_blocks'][0]['source_path'])
  assert h(local)==sources['nhsa_original_pdf']['sha256']==sources['nhsa_wx_pdf']['sha256']
  out.update({
   'r2_status':'official_original_wording_confirmed_reference_identity_unresolved',
   'source_refs':['nhsa_announcement','nhsa_original_pdf','nhsa_wx_pdf','shrs_1999_method','nhsa_2020_method'],
   'citing_document':{'title':'2020年国家医保药品目录调整申报指南','publication_date':'2020-08-17','official_pdf_sha256':sources['nhsa_original_pdf']['sha256'],'local_study_pdf_path':str(local),'local_study_pdf_same_bytes':True,'official_two_endpoints_same_bytes':True,'locator':'PDF第2页，一（二）目录内西药和中成药，首段','observed_exact_reference_title':'基本医疗保险用药范围管理暂行办法','verification_methods':['pypdf文字提取','pypdfium2渲染第2页后实际看图'],'render_path':str(D/'nhsa_2020_guide_page2.png'),'render_sha256':h(D/'nhsa_2020_guide_page2.png'),'finding':'官方PDF确实含“范围”二字；不是本地抄录、OCR或候选文件改写造成。'},
   'comparison_documents_only':[
    {'source_ref':'shrs_1999_method','title':'城镇职工基本医疗保险用药范围管理暂行办法','document_number':'劳社部发〔1999〕15号','publication_date':'1999-05-12','date_source_locator':'官方转载可见文本L9–L15；URL的20200617不是原规章发布日期','article':'第十条','article_text':old10,'article_locator':'可见文本L37–L42','identity_difference':'题名包含“城镇职工”，与申报指南书名不完全相同。','eligible_for_automatic_context_merge':False},
    {'source_ref':'nhsa_2020_method','title':'基本医疗保险用药管理暂行办法','document_number':'国家医疗保障局令第1号','signed_date':'2020-07-30','web_publication_date':'2020-07-31','effective_date':'2020-09-01','article':'第十条','article_text':new10,'article_locator':'可见文本L39–L42','identity_difference':'题名没有“范围”；第十条内容与1999年办法不同。施行日在指南2020-08-17公告之后，不能仅靠时序替代引用身份核验。','eligible_for_automatic_context_merge':False}
   ],
   'verified_increment':'新增官方指南同字节回证，以及两份正式办法第十条的可追溯比较材料；不是修复原PDF文字，也没有确定哪一个第十条就是原引文。',
   'remaining_gap':'本轮有界官方检索未找到该申报指南的相关勘误或将其所称办法明确对应到1999/2020文件的说明。两份不同第十条不能择一自动补入；不能由题名相似认定同文件。'
  })
 records.append(out)
report={'version':'v26-context-repair-r2-official-reference-check','date':'2026-09-30','identity':{'kind':'AI','name':'V600独立评审A（本轮仅材料来源核对）'},'scope':{'ids':list(rr),'record_count':2,'task':'官方外引身份、年份和条文定位核对；不编码','outside_machine_53_examined':False,'r1_modified':False,'new_labels_added':False},'r1_hash_checks':checks,'sources':sources,'records':records,'summary':{'records_checked':2,'official_guide_same_byte_confirmations':1,'external_reference_gaps_resolved':0,'gaps_retained':2,'automatically_mergeable_new_external_context_blocks':0},'limitations':['两条的原分析单元及其边界不变；不复制外引或后项全部标签。','下载响应文件的hash仅识别实际收到的字节；CDE的HTML挑战页hash不能作为未取得的技术指导原则hash。','01204两份办法只为身份比较保存，不下达其适用性或编码判断。','00064的2020-11-19是候选版本检索定位日期，官方全文核验仍未完成。','本轮未重算、未修改论文、原参照、预测或r1。root另有下发包审计，本报告不冒称自己完成该审计。'],'context_recovery_note':'本轮有上下文压缩；依据本轮已落盘原始下载、请求日志、此前执行摘要恢复。恢复后重新核对两条r1记录、官方HTML相关行及PDF第2页提取文字。'}
fn=D/'external_reference_supplements_00064_01204_r2.json'
with fn.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
md=f'''# 两条外部引文官方原文补核（r2）

仅核对 RECODE25-00064、RECODE25-01204 的来源身份、年份和明确外引。AI 身份；不编码、不改 r1、不扩至机器待定并集外条目。核对日：2026-09-30。

## 结果

两条均新增可回查证据，但外引缺口均未完全解决：**已核对 2 条，解决 0 条，保留缺口 2 条**。没有可无歧义自动合并的新外引条件；空补丁不代表问题解决。r1 的 8 份交付文件哈希复验均未变。

### 00064

原单元引用《药品附条件批准上市技术指导原则》。官方检索入口可定位 2020 年第 41 号《药品附条件批准上市技术指导原则（试行）》；2020-11-19 为检索/转载线索定位日期，**未成功取得官方通告正文或技术指导原则附件，不能称已完成官方全文核验**。[官方转载入口](https://www.ccfdie.org/cn/yjxx/yphzp/webinfo/2020/11/1602453958453674.htm)、[CDE 通告入口](http://www.cde.org.cn/news.do?method=viewInfoCommon&id=e8e70cb03a94e5f2)、[CDE 附件入口](https://www.cde.org.cn/zdyz/downloadAtt?idCODE=eae16177a1eb066690d66f21fc711b1a)。

候选正式版的 11 月日期晚于引用它的三程序文件 2020-07-08 发布日期。本轮未取得能确认当时所指版本及情形条件的证据，因此不把 11 月版本自动追溯至 7 月。CDE 旧通告及附件返回 HTTP 202 HTML 挑战页，附件 HTTPS 下载中断；官方转载超时/502，浏览器附件访问受阻。响应已留存，但其 hash **不是指导原则 hash**。不使用不同年份文件或注册管理办法替代。原 r1 已补同文“其中”两项仍保留，技术指导原则实质条件缺口仍在。

### 01204

[国家医保局公告](http://www.nhsa.gov.cn/art/2020/8/17/art_53_3408.html)日期为 2020-08-17。公告附件、医保局微信站点附件及研究本地原 PDF 的 SHA256 完全一致：`{sources['nhsa_original_pdf']['sha256']}`。实际提取并看图核对 PDF 第 2 页，“基本医疗保险用药**范围**管理暂行办法”确实存在于官方文件，不能改写为另一个标题。[官方附件](http://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=2edbafaf09654373a58f7e33fbeaac7d.pdf)。

两个可取得的官方比较文本存在实质差别：

| 比较文件 | 身份及日期 | 第十条性质 | 定位 |
|---|---|---|---|
| 《城镇职工基本医疗保险用药范围管理暂行办法》 | 劳社部发〔1999〕15号；1999-05-12 | 撤号、吊销进口证、禁产销使用、生产销售违法及评审弄虚作假等删除情形 | 上海人社官方转载可见文本 L37–L42 |
| 《基本医疗保险用药管理暂行办法》 | 国家医保局令第1号；2020-07-30签发，2020-09-01施行 | 价格费用明显偏高、临床价值不确切及不符合安全性/有效性/经济性等可以调出情形 | 国家医保局官方页面可见文本 L39–L42 |

[1999 年办法官方转载](https://rsj.sh.gov.cn/trlzyhshbzbgz_17256/20200617/t0035_1388342.html)的 URL 含 2020 不等于该规章原发布日期；页面明示 1999-05-12。[2020 年办法官方页面](http://www.nhsa.gov.cn/art/2020/7/31/art_173_10977.html)题名则不含“范围”。本轮未找到官方勘误或明确对应说明。两份第十条仅作为身份比较记录，**均不自动合并为目标单元的确定外引**；原文含义不能因目录标题接近而替换。

## 回查与保留

详见同目录 JSON：逐条记录原单元 SHA、来源 URL、下载文件 SHA、定位、请求失败、比较原句和剩余缺口。官方指南 PDF 第 2 页看图留存 `nhsa_2020_guide_page2.png`。官方 HTML 保留原字节，并另存带行号可见文本；行号仅属于该本地提取，不是网站自带段落编号。原始请求日志一并保留。

本轮没有最终 0/1 标签，不更改待定原因，不作完整法规适用性判断。未改论文、原参照、预测、r1 或统计；未扩展其他条目。root 另行提供的组包审计没有被表述为本代理自行完成，也不能据此推断模型实际读完或正确使用了语境。
'''
with (D/'外引两条官方原文补核-r2.md').open('x') as f:f.write(md)
artifacts=[]
for p in sorted(D.iterdir()):
 if p.is_file():artifacts.append({'path':str(p),'sha256':h(p),'bytes':p.stat().st_size})
with (D/'r2_manifest.json').open('x') as f:json.dump({'files':artifacts,'r1_all_checked_unchanged':True,'r1_checked_count':len(checks),'ids':[r['id'] for r in records],'no_final_labels_added':True},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'json':str(fn),'json_sha256':h(fn),'report_sha256':h(D/'外引两条官方原文补核-r2.md'),'manifest_sha256':h(D/'r2_manifest.json'),'records':len(records),'gaps_retained':2,'r1_unchanged':len(checks)},ensure_ascii=False,indent=2))
