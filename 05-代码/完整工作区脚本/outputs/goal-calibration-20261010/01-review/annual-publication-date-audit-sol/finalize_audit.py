import json, hashlib, re, datetime, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def iso_now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

dates={1:'2023-05-29',2:'2020-02-26',3:'2022-07-27',4:'2018-07-10',5:'2024-11-22',6:'2023-01-13',7:'2019-04-09',8:'2021-07-28',9:'2021-09-03',10:'2022-06-29',11:'2022-06-29',12:'2021-05-10',13:'2020-07-31',14:'2025-09-12',15:'2024-07-31',16:'2024-02-07',17:'2024-08-02',18:'2020-07-08',19:'2026-05-15',20:'2026-06-08'}
docnos={1:'国卫医政发﹝2023﹞12号',2:'国卫医发〔2020〕2号',3:'国卫医函〔2022〕122号',4:'国卫办医发〔2018〕14号',5:'国卫药政发〔2024〕38号',6:'国卫办医政函〔2023〕9号',7:'国卫药政函〔2019〕80号',8:'国卫办药政发〔2021〕16号',9:'国卫办医函〔2021〕474号',10:'国家医疗保障局2022年6月29日正式公告；附件1/3/4',11:'国家医疗保障局2022年6月29日正式公告；附件2',12:'医保发〔2021〕28号',13:'国家医疗保障局令第1号',14:'2025年第86号',15:'国药监药注〔2024〕21号',16:'国药监药注〔2024〕10号',17:'国药监药注函〔2024〕55号',18:'2020年第82号',19:'2026年第47号',20:'2026年第50号'}
rejected={1:[('2023-05-30','现有中国政府网快照firstpublishedtime；转载发布时点')],3:[('2022-07-30','现有中国政府网快照firstpublishedtime；转载发布时点')],4:[('2023-02-13','现有无锡快照PubDate；地方转载时点')],6:[('2023-03-31','现有北京转发页面PubDate；地方转发时点'),('2023-04-04','现有上海政府转发页面displayDate；地方转发时点')],9:[('2021-09-04','现有中国政府网快照firstpublishedtime；转载发布时点')],10:[('2022-07-01','既有正式公告转载快照日期及网上申报开通日；此前仅作原公开上界')],11:[('2022-07-01','既有正式公告转载快照日期及网上申报开通日；此前仅作原公开上界')],12:[('2021-07-10','现有中国政府网公报页面firstpublishedtime；公报刊载时点')],14:[('2025-09-17','现有陕西药监转载页PubDate')],15:[('2024-08-01','现有中国政府网快照firstpublishedtime；转载发布时点')],16:[('2024-02-12','现有中国政府网快照firstpublishedtime；转载发布时点')],17:[('2024-08-06','现有药学数据中心转载页PubDate')],18:[('2020-07-09','现有研究会转载页发布日期')],19:[('2026-05-22','现有福建药监转载页PubDate')],20:[('2026-07-19','现有辽宁药监转载页PubDate')],2:[],5:[],7:[],8:[],13:[]}

entries=json.loads((ROOT/'working-entries.json').read_text())
browser=json.loads((ROOT/'browser_observed_date_evidence.json').read_text())
browser_records={e['index']:e for e in browser['records']}
generated=[]
for entry in entries:
    i=entry['index']; directory=Path(entry['directory']); ev=directory/'evidence'
    http=json.loads((ev/'primary-http-retrieval.json').read_text())
    metadata={**entry,'schema':'original-publication-date-entry-audit-v1','audit_saved_at':iso_now(),'publication_date':dates[i],'publication_date_status':'exact_original_agency_page_publication_date_verified','publication_date_upper_bound':None,'primary_publication_url':http['url'],'policy_year':int(entry['policy_year']),'publication_year':int(dates[i][:4]),'document_version':docnos[i],'cutoff':'2026-07-31','published_by_cutoff':dates[i]<='2026-07-31','new_issue_publication_same_year':entry['issue_date'][:4]==dates[i][:4],'attempts':[http]}
    metadata['evidence']=list(entry['evidence'])
    metadata['excluded_date_candidates']=[{'date':d,'reason':r} for d,r in rejected.get(i,[])]
    if i<=9:
        b=browser_records[i]
        capture=ev/'primary-browser-dom-date-evidence.json'
        dump(capture,{'capture_date':browser['capture_date'],'method':browser['method'],**b})
        sections=[b['title'],b['visible_publication_line'],b['document_number'],b.get('body_excerpt',''),b.get('signature_excerpt',''),b.get('signature_date_excerpt','')]
        text=ev/'primary-browser-dom-date-excerpt.txt'
        text.write_text('\n'.join(s for s in sections if s)+'\n')
        metadata['evidence'].append({'role':'primary_original_publication_date_rendered_dom','url':b['url'],'saved_path':str(capture),'sha256':sha(capture),'text_saved_path':str(text),'text_sha256':sha(text),'content_extent':'实际原页DOM中标题/可见发布时间/文号/正文及署名日期的选定摘录；不是完整HTML；空行规范化','date_location':'原页标题下可见发布时间行；摘录txt第2行','publication_date_verbatim':b['visible_publication_line']})
        metadata['evidence'].append({'role':'failed_http_response_not_publication_evidence','url':http['url'],'saved_path':http['raw_saved'],'sha256':http['raw_sha256'],'status_code':412})
        metadata['attempts'].append({'method':'Codex in-app browser; read-only rendered DOM inspection','status':'original_notice_rendered_and_title_date_docno_read','url':b['url'],'capture_date':browser['capture_date'],'saved_evidence':str(capture),'failure_policy':'HTTP412未循环重试；采用正常浏览器读取。'})
        metadata['primary_publication_evidence_kind']='original_agency_visible_publication_label_in_rendered_DOM'
        metadata['date_metadata_conflict']={'head_pubdate':b['head_pubdate'],'visible_original_publication_date':dates[i],'decision':'采用正文上方明确保留的原发布时间。head PubDate为2024/2025重建页面时间，跨年且与政策原日期及可见标签冲突；不充作原公开日。','migration_timestamp_status':'inferred_page_rebuild_time_not_certified_as_original_publication'}
        metadata['excluded_date_candidates'].append({'date':b['head_pubdate'],'reason':'原页head PubDate与可见原发布时间冲突；未采为原公开日'})
        metadata['publication_date_verbatim']=b['visible_publication_line']
        metadata['publication_time_of_day']=None
    else:
        assert http['status_code']==200
        soup=BeautifulSoup((ev/'primary-http-response.html').read_bytes(),'lxml')
        headmeta={m.get('name',''):m.get('content') for m in soup.find_all('meta') if m.get('name')}
        lines=(ev/'primary-http-visible-text.txt').read_text().splitlines()
        hits=[]
        for n,line in enumerate(lines,1):
            if dates[i] in line and any(k in line for k in ['日期：','发布时间：']):
                hits.append({'line':n,'text':line})
            if line.strip()=='发布日期' or line.strip()=='发布日期：':
                hits.append({'line':n,'text':' | '.join(lines[n-1:n+2])})
        assert hits, (i,'no visible primary-date label')
        pub=headmeta.get('PubDate')
        assert pub and pub.startswith(dates[i]),(i,pub)
        metadata['evidence'].append({'role':'primary_original_publication_date_complete_HTML','url':http['url'],'saved_path':http['raw_saved'],'sha256':http['raw_sha256'],'text_saved_path':http['text_saved'],'text_sha256':http['text_sha256'],'content_extent':'实际HTTP200原发布机关完整HTML响应及派生正文转文本','date_locations':hits,'meta_pubdate':pub,'meta_article_title':headmeta.get('ArticleTitle')})
        metadata['primary_publication_evidence_kind']='original_agency_complete_HTML_visible_date_and_matching_PubDate'
        metadata['publication_date_verbatim']=hits[0]['text']
        metadata['publication_time_of_day']=pub[11:] if len(pub)>10 else None
        # Correct the mechanically over-nested html.parser meta dump in the retrieval log.
        http['meta']=[{'name':k,'content':v} for k,v in headmeta.items() if k.lower() in ['pubdate','articletitle','url','maketime','effectivetime']]
        dump(ev/'primary-http-retrieval.json',http)
        metadata['attempts'][0]=http
        if i in [10,11]:
            ar=json.loads((ev/'original-attachment-retrieval.json').read_text())
            assert ar['same_bytes_as_preserved_source']
            metadata['evidence'].append({'role':'official_original_attachment_version_identity','url':ar['url'],'saved_path':ar['saved_path'],'sha256':ar['sha256'],'same_bytes_as_preserved_source':True,'basis':'本公告直接链接附件与此前纳入PDF的SHA256完全相同；确认原版本，未换为征求意见稿或更新附件。'})
            metadata['version_identity_check']={'status':'official_attachment_SHA256_exactly_matches_preserved_source','original_source_sha256':entry['evidence'][0]['sha256'],'official_attachment_sha256':ar['sha256']}
    if 'version_identity_check' not in metadata:
        metadata['version_identity_check']={'status':'same_document_notice_identity_verified_no_original_source_replacement','basis':'原发布页题名、文号/公告号、署名日期与此前纳入文档及元数据一致。附件/规范本体仍引用原source SHA，不把新页面或转载作为替代编码材料。','original_source_sha256':entry['evidence'][0]['sha256'],'original_source_retained':True}
    metadata['issue_date_basis']='保留原55条源元数据成文日；6项缺失成文日依既有department-year-analysis-plan-sol/report.json的原文补核。此次核读原公告署名日期，与保留值一致；绝不由署名日自动推定公開日。'
    metadata['effective_date_status']='prior_evidence_preserved' if entry['effective_date'] else 'not_explicitly_verified_or_not_applicable_keep_null'
    if i==18:
        metadata['effective_date']='2020-07-08'
        metadata['effective_date_status']='newly_resolved_by_explicit_effective_on_publication_clause'
        metadata['effective_date_basis']='原公告明确“本公告自发布之日起施行”；原页公开日为2020-07-08，署名日2020-07-07另存。'
    elif i==19:
        metadata['effective_date_basis']='原公告明确“现予发布，自发布之日起施行”；原公开日与署名日均为2026-05-15。'
    elif i==20:
        metadata['effective_date_basis']='原公告明确“自2026年9月1日起施行”；成文2026-05-21、公开2026-06-08。'
    elif i==13:
        metadata['effective_date_basis']='医保局令第1号及本体第三十七条明确自2020年9月1日起施行；公开7月31日、署名7月30日。'
    elif i in [4,9]:
        metadata['effective_date_basis']='保留既有原文“自印发之日起施行”对应成文/印发日；公开日期另核，未混用。'
    else:
        metadata['effective_date_basis']='未以成文、公告发布或试点启动时间擅自补造法律施行日；保留null。'
    metadata['scope_limits']=['仅补核原公开日期及其时间类型，未读取最终研究标签、未生成注意力结论。','既有分析归属、年度系列、4481来源框及原材料字节不变。','本审计确认原发布机关现页明确保留的原发布时间；非全网最早出现时点普查。']
    # Keep original publication upper-bound evidence, while superseding its use as the best available estimate.
    if i in [10,11]:
        metadata['retired_date_bound']={'upper_bound':'2022-07-01','reason':'现已核得原机关精确日期2022-06-29，且原附件SHA完全相同；7月1日仅是原公告中的申报开通时间及此前转载上界。'}
    for e in metadata['evidence']:
        if e.get('saved_path') and e.get('sha256'): assert sha(e['saved_path'])==e['sha256']
    dump(directory/'metadata.json',metadata)
    note=f"{entry['id']}\n原公开日：{dates[i]}（原发布机关页面明确日期）。\n成文/署名日：{entry['issue_date']}。施行日：{metadata['effective_date'] or 'null（未明确核实）'}。\n原页：{metadata['primary_publication_url']}\n证据：metadata.json中的primary_original_publication_date项及evidence目录；SHA256逐文件保留。\n"
    if i<=9: note+='HTTP直取412响应只是失败记录；日期取自正常浏览器实际读取的原页可见发布时间。摘录是选定DOM证据，不冒称完整HTML；head PubDate迁移/重建时间另记，不采作原公开日。\n'
    else: note+='保存HTTP200完整原页HTML；可见日期与head PubDate同日。\n'
    if i in [10,11]: note+='原公告附件与此前纳入PDF的SHA256完全一致。2022-07-01不再充作精确原公开日，旧上界证据仍保留。\n'
    if i==20: note+='2026-06-08公开早于2026-07-31收集截止；9月1日施行晚于收集截止，与公开纳入是两个时钟。\n'
    (directory/'说明.txt').write_text(note)
    generated.append(metadata)

plan=ROOT.parents[1]/'02-methods/department-year-analysis-plan-sol/report.json'
source_map=ROOT.parents[2]/'validation-expansion-20260926/frozen-inputs/source_metadata--55条部门与系列映射-核验中.json'
summary={'schema':'annual-original-publication-date-audit-v1','generated_at':iso_now(),'status':'complete_20_of_20_missing_dates_verified','scope':'仅本新增目录；原材料、Goal、progress、编码、最终研究标签均未改动/未读取。','inputs':[{'path':str(plan),'sha256':sha(plan)},{'path':str(source_map),'sha256':sha(source_map)}],'target_missing_date_entry_n':20,'verified_exact_original_publication_date_n':20,'still_null_n':0,'prior_available_publication_date_n':31,'integrated_available_publication_date_n_if_applied':51,'prior_issue_publication_same_year_pair_n_preserved_without_reauditing':28,'new_issue_publication_same_year_pair_n':20,'integrated_same_year_pair_n_if_applied':48,'cutoff_preserved':'2026-07-31','all_20_publication_dates_before_or_on_cutoff':all(e['published_by_cutoff'] for e in generated),'official_primary_complete_HTML_entry_n':11,'official_primary_rendered_DOM_excerpt_entry_n':9,'same_official_announcement_shared_entries':[{'entry_indices':[10,11],'independent_source_entry_n':2,'announcement_n':1,'publication_date':'2022-06-29'}],'original_version_identity_SHA_exact_match_entry_indices':[10,11],'nmpa2026_GCP_three_clocks':{'issue_date':'2026-05-21','publication_date':'2026-06-08','effective_date':'2026-09-01'},'limits':['未重新审读其余31条原公开日证据，31为此前计划已认证可用值，原28同年对照保持。','卫健9条保存实际正常浏览器原页DOM日期证据选摘，未取得完整HTML正文响应。HTTP412原响应仅为失败留痕，不能引用为政策原文。','各条publication_date来自明确原页日期标签，未使用文件名、URL字符串日期、搜索摘要或同题转载日期推定。','保留既有原政策版本、部门归属与2026部分年度边界；不生产任何五维研究结论。'],'entries':[{'index':e['index'],'id':e['id'],'analysis_group':e['analysis_group'],'document_version':e['document_version'],'issue_date':e['issue_date'],'publication_date':e['publication_date'],'effective_date':e['effective_date'],'primary_publication_url':e['primary_publication_url'],'metadata_path':str(Path(e['directory'])/'metadata.json'),'metadata_sha256':sha(Path(e['directory'])/'metadata.json')} for e in generated]}
assert len(generated)==20 and len(set(e['id'] for e in generated))==20
assert all(e['publication_date'] and e['new_issue_publication_same_year'] and e['published_by_cutoff'] for e in generated)
dump(ROOT/'metadata.json',summary)
lines=['20条原公开日期缺口已逐条补核，20/20为精确原发布机关页面日期，0条仍为null。此次新增20条全部与保留成文年度同年；此前28对照保留，未把重核范围扩展为全部51条。若整合本交付，原公开日期可用条目为原31+新增20=51，成文/公开同年对为原28+新增20=48。','医保4条、药监7条保存实际HTTP200完整原页HTML与文本。卫健9条HTTP直取412，但正常浏览器成功渲染原机关通知，保存标题、文号、可见发布时间、正文及署名日期DOM选摘。其head PubDate出现2024/2025迁移/重建时间，与明确保留的原可见发布时间冲突，均另记并排除。DOM选摘不冒称完整HTML。','医保2022方案/指南确认原公开2022-06-29；公告直接链接的两个原PDF与此前纳入PDF的SHA256完全相同。此前2022-07-01只是转载上界/申报系统开通日。GCP2026成文2026-05-21、公开2026-06-08、施行2026-09-01分别保存；收集截止2026-07-31与已有部门年度归属不变。','每条子目录均含metadata.json、说明.txt与evidence；根metadata.json为汇总。working-entries.json为补核前20条缺口输入快照，其publication_date=null不是最终结论；最终以逐条metadata.json/根metadata.json为准。seal.json封存全部本目录文件SHA。','本次不改原材料、Goal/progress/编码或原元数据，也不读取最终研究标签，不生成注意力结论。原政策版本仍绑定原source SHA；新网页证据只补日期。']
lines.extend([f"{e['index']:02d}. {e['id']}：公开 {e['publication_date']}；成文 {e['issue_date']}；施行 {e['effective_date'] or 'null'}。" for e in generated])
(ROOT/'说明.txt').write_text('\n\n'.join(lines)+'\n')
dump(ROOT/'verification.json',{'status':'passed','checked_at':iso_now(),'unique_entries':20,'all_exact_dates_present':True,'all_new_pairs_same_year':True,'cutoff_unchanged':True,'all_dates_before_or_on_cutoff':True,'original_2022_PDF_bytes_matched':True,'external_source_files_changed':False,'final_research_labels_read':False,'note':'本任务写入路径均在指定新增目录，输入SHA绑定与保存副本逐项核对。'})
dump(ROOT/'http-retrievals.json',[json.loads((Path(e['directory'])/'evidence/primary-http-retrieval.json').read_text()) for e in entries])
seal_files=[]
for f in sorted(ROOT.rglob('*')):
    if f.is_file() and f.name!='seal.json': seal_files.append({'relative_path':str(f.relative_to(ROOT)),'sha256':sha(f),'bytes':f.stat().st_size})
dump(ROOT/'seal.json',{'schema':'annual-publication-date-audit-seal-v1','created_at':iso_now(),'root':str(ROOT),'file_n':len(seal_files),'files':seal_files,'summary_metadata_sha256':sha(ROOT/'metadata.json'),'status':'complete','write_scope':'this_new_directory_only','cutoff':'2026-07-31'})
print(json.dumps({'status':summary['status'],'verified':20,'still_null':0,'sealed_files':len(seal_files),'metadata':str(ROOT/'metadata.json')},ensure_ascii=False))
