from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re
from pypdf import PdfReader

BASE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
OUT = Path(__file__).parent
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s): return re.sub(r'[\W_]+', '', re.sub(r'^\[\d+\]\s*', '', s)).lower()
inv = read(OUT/'current_docx_reference_year_inventory.json')
old_path = BASE/'outputs/manuscript-completion-20261006/参考文献核验.json'
old = read(old_path)
cross_path = BASE/'outputs/coding-revision-20261007-r3/manuscript-update-20261008/52段修正回验与参考真实性审计-20261008.json'
cross = read(cross_path)
policy_path = BASE/'outputs/final-three-department-20261008-human-validation-template/policy-source-audit/政策建议官方证据包-20261008.json'
policy = read(policy_path)
policy_by_id = {r['id']: r for r in policy['sources']}
policy_map = {2:'innovation2025',3:'dual_directory2025',59:'precommunication2026',60:'price2026',61:'rwepilot2025',62:'trustednetwork2026',63:'interpretation2026'}
rows=[]
source_checks={}
for cur in inv['references']:
    n=cur['number']; citation=cur['citation']
    match=[r for r in cross['old62_audit_crosswalk']+cross['new6_audit'] if norm(r['entry'])==norm(citation)]
    row={'number':n,'citation':citation,'paragraph_index':cur['paragraph_index'],'citation_year':None,'verified_issue_or_publication_year':None,'online_date':None,'issuer_date':None,'web_publication_date':None,'effective_date':None,'access_date':None,'primary_sources':[],'evidence_paths':[],'evidence_locator':'','year_evidence':'','status':'UNVERIFIED','scope':'publication year/date metadata only; not a new full-text or claim-validity certification'}
    if '[EB/OL]' in citation:
        issued=re.search(r'\((\d{4}-\d{2}-\d{2})\)',citation)
        access=re.search(r'\[(\d{4}-\d{2}-\d{2})\]',citation)
        if issued: row['citation_year']=int(issued[1][:4]);row['citation_web_date']=issued[1]
        if access: row['access_date']=access[1]
    else:
        m=re.search(r'\[(?:J|M|C|Z)(?:/OL)?\].*?((?:19|20)\d{2})',citation)
        if m:row['citation_year']=int(m[1])
    if match:
        m=match[0];row['evidence_paths']=[m['audit_path'],str(cross_path)];row['evidence_locator']=m['audit_record']
        if m['audit_group']=='oct6_inherited':
            loc=m['audit_record'].split('/'); key=loc[0]; ident=int(loc[1])
            pool=old[key]; field='original_number' if key=='references' else 'proposed_number'
            src=next(r for r in pool if r[field]==ident)
            row['primary_sources']=src.get('sources',[])
            row['year_evidence']=src.get('note','') or ('既有一手元数据核验为真；当前与原已核完整著录逐字段归一匹配。')
            row['prior_core_metadata_verified']=src.get('core_metadata_verified',src.get('verified',False))
            row['original_fulltext_scope']=src.get('claim_review','method article metadata and previous reading')
            local=src.get('local_originals',[])
            for x in local:
                p=x['path'];check={'path':p,'expected_sha256':x.get('sha256'),'exists':Path(p).exists()}
                if check['exists']:check.update(actual_sha256=sha(p),sha_matches=sha(p)==x.get('sha256'))
                source_checks[p]=check
                row.setdefault('local_original_checks',[]).append(check)
            if row['prior_core_metadata_verified']: row['status']='YEAR_VERIFIED_REUSED_PRIMARY_AUDIT';row['verified_issue_or_publication_year']=row['citation_year']
        else:
            src=m.get('evidence_record',m)
            row['primary_sources']=[{'url':v,'type':'official/publisher/author primary source'} for k,v in src.items() if ('url' in k and isinstance(v,str) and v.startswith('http'))]
            row['year_evidence']=src.get('content_verification_scope',src.get('status',''))
            row['evidence_locator'] += '; '+str(src.get('locator',src.get('locators','')))
            for field in ['online_date','issue_date','publication_date','official_publication_date','official_announcement_date','gov_reprint_date','crossref_published_print']:
                if field in src:row[field]=src[field]
            yr=src.get('issue_year',src.get('final_issue_year',src.get('year',None)))
            if yr is not None:row['verified_issue_or_publication_year']=int(yr)
            else:row['verified_issue_or_publication_year']=row['citation_year']
            row['status']='YEAR_VERIFIED_REUSED_PRIMARY_AUDIT'
            row['prior_metadata_status']=m.get('metadata_status',src.get('status'))
            for f,h in [('local_pdf','local_pdf_sha256'),('local_path','local_sha256')]:
                if f in src:
                    p=src[f];check={'path':p,'expected_sha256':src.get(h),'exists':Path(p).exists()}
                    if check['exists']:check.update(actual_sha256=sha(p),sha_matches=(sha(p)==src.get(h)) if src.get(h) else None)
                    source_checks[p]=check;row.setdefault('local_original_checks',[]).append(check)
    if n in policy_map:
        src=policy_by_id[policy_map[n]]; p=Path(src['path']); t=p.read_text();metadata=dict(re.findall(r'<meta\s+name=[\"\x27]([^\"\x27]+)[\"\x27]\s+content=[\"\x27]([^\"\x27]*)[\"\x27]',t,re.I))
        row.update(issuer_date=src.get('issuer_date'),web_publication_date=src.get('web_publish_date'),verified_issue_or_publication_year=int(src['web_publish_date'][:4]),status='YEAR_VERIFIED_SAVED_OFFICIAL_ORIGINAL',year_evidence='官方HTML PubDate与可见日期一致；成文、网站公布、实施分别记录。')
        row['primary_sources']=[{'url':src['url'],'type':'issuing authority official original'}];row['evidence_paths'] += [str(policy_path),str(p)];row['evidence_locator']='HTML meta PubDate / 可见日期；已封存官方原件核验'
        check={'path':str(p),'expected_sha256':src['sha256'],'actual_sha256':sha(p),'sha_matches':sha(p)==src['sha256']};source_checks[str(p)]=check;row.setdefault('local_original_checks',[]).append(check);row['saved_official_PubDate']=metadata.get('PubDate')
    if n==3:row['effective_date']='2026-01-01';row['implementation_deadline']='2026-02月底（原则上召开药事会）'
    if n==16:row['online_year']=2017;row['online_date_note']='既存Springer/PubMed原始著录核2017 online、2018卷期；未新增未经证实的月日'
    if n==22:row['online_year']=2022;row['online_date_note']='既存Wiley/作者高校原文核2022 online、2023卷期；未新增未经证实的月日'
    if n==26:
        p=OUT/'Guo2023-online2024-LSHTM.pdf';d=PdfReader(p);t='\n'.join(d.pages[i].extract_text() for i in [0,1]); ok=('(2023)' in t and '2023, VOL. 9, NO. 3' in t and 'Published online: 08 May 2024' in t)
        row.update(verified_issue_or_publication_year=2023,online_date='2024-05-08',status='YEAR_VERIFIED_CURRENT_PUBLISHED_PDF' if ok else 'UNVERIFIED',year_evidence='本轮重新取得11页发表PDF，物理1页To cite this article列2023、9:3；物理2页刊头2023,VOL.9,NO.3；物理1页online08May2024。©2024及DOI2024均不替代正式卷年。')
        row['evidence_paths'] += [str(p),str(OUT/'Guo-front-matter-year-evidence.txt')];row['primary_sources'].append({'url':'https://researchonline.lshtm.ac.uk/id/eprint/4673940/1/Guo-etal-2024-Health-Technology-Assessment-in-Chinas-Health-Care-Sector.pdf','type':'author institution published version PDF'});source_checks[str(p)]={'path':str(p),'actual_sha256':sha(p),'parsed_pages':len(d.pages)}
    if n==33:row['online_year']=1998;row['online_date_note']='既存Wiley著录核电子上线1998；正式卷年1997，不改为1998'
    if n==43:row.update(verified_issue_or_publication_year=2026,online_date='2025-09-19',issue_date='2026-04',status='YEAR_VERIFIED_CURRENT_PUBLISHER_PAGE',year_evidence='本轮Cambridge官网Published online19September2025；Information为Volume34,Issue2,April2026,pp188–204。DOIpan.2025.10017不替代正式卷期年。')
    if n==44:row.update(verified_issue_or_publication_year=2015,status='YEAR_VERIFIED_CURRENT_PUBLISHER_PAGE',year_evidence='本轮ACL Anthology Details Year2015、MonthJuly；Pages438–444；BibTeX与MODS dateIssued2015-07一致。',primary_sources=[{'url':'https://aclanthology.org/P15-2072/','type':'ACL original proceedings bibliography'}],evidence_locator='ACL Details Year/Month/Pages; BibTeX year; MODS dateIssued')
    if n==64:row.update(status='NO_PUBLICATION_YEAR_ACCESS_DATE_VERIFIED',verified_issue_or_publication_year=None,year_evidence='官网为动态监测登记页面，现条目只写[2026-10-06]访问日期，没有冒称2026发表。既存2026-10-06实际读取记录支持此访问日。')
    if any(x.get('sha_matches') is False for x in row.get('local_original_checks',[])):row['status']='SOURCE_HASH_MISMATCH_REQUIRES_RECHECK'
    if row['citation_year'] is not None and row['verified_issue_or_publication_year']!=row['citation_year']:row['status']='YEAR_MISMATCH_REQUIRES_CORRECTION'
    peer_path=BASE/'outputs/coding-revision-20261008-r4/references-51-65-date-audit/references_51_65_dates_evidence.json'
    if 51<=n<=65 and peer_path.exists():
        peer=read(peer_path); pr=next(x for x in peer['references'] if x['current_reference_number']==n)
        assert norm(pr['current_reference'])==norm(citation)
        assert pr['confirmed_publication_year']==row['verified_issue_or_publication_year']
        row['independent_date_audit_status']=pr['status'];row['date_types_independent_audit']=pr['substantive_dates'];row['date_boundary_and_limits']=pr['date_boundary_and_limits'];row['evidence_paths'].append(str(peer_path))
        row['primary_sources'] += [{'url':u,'type':'independent official date audit source'} for u in pr['primary_urls'] if u not in [s['url'] for s in row['primary_sources']]]
        for f in pr['evidence_files']:
            check={'path':f['path'],'expected_sha256':f['sha256'],'actual_sha256':sha(f['path']),'sha_matches':sha(f['path'])==f['sha256']};source_checks[f['path']]=check;row.setdefault('local_original_checks',[]).append(check)
            if not check['sha_matches']:row['status']='SOURCE_HASH_MISMATCH_REQUIRES_RECHECK'
    rows.append(row)

bindings=[{'path':str(p),'sha256':sha(p)} for p in [old_path,cross_path,policy_path,OUT/'current_docx_reference_year_inventory.json',OUT/'annual_guideline_metadata_check.json']]
bindings.append({'path':str(peer_path),'sha256':sha(peer_path)})
result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_docx':inv['source'],'source_docx_sha256':inv['sha256'],'scope':'All 66 currently used bibliography entries, year/date only; reuse explicitly bound first-hand audits. No model calls, labels or scores read. No manuscript/coding/prompt edit. A source-text visibility exception is explicitly logged, never used for tuning.','status_counts':{s:sum(r['status']==s for r in rows) for s in sorted(set(r['status'] for r in rows))},'confirmed_publication_year_entries_n':sum(r['verified_issue_or_publication_year'] is not None for r in rows),'no_publication_year_access_only_entries_n':sum(r['status']=='NO_PUBLICATION_YEAR_ACCESS_DATE_VERIFIED' for r in rows),'unverified_numbers':[r['number'] for r in rows if r['status'] in ['UNVERIFIED','YEAR_MISMATCH_REQUIRES_CORRECTION','SOURCE_HASH_MISMATCH_REQUIRES_RECHECK']],'records':rows,'evidence_bindings':bindings,'local_source_hash_checks':list(source_checks.values()),'source_text_visibility_exception_path':str(OUT/'source_visibility_exception_metadata.json'),'limitations':['YEAR_VERIFIED_REUSED_PRIMARY_AUDIT means current citation matched explicitly verified sealed primary metadata; it does not claim newly downloading or fully rereading all 66 sources.','Online dates not independently present in a source record remain null; no fabricated month/day.','Reference64 has no publication year; its access date must never be counted as publication year.','Body substantive years are reviewed separately; a bibliography year match cannot establish a policy effect or corpus cutoff.']}
(OUT/'all66_reference_year_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
fields=['number','citation','citation_year','verified_issue_or_publication_year','online_date','issuer_date','web_publication_date','effective_date','access_date','status','year_evidence','source_urls','evidence_paths','evidence_locator']
with (OUT/'all66_reference_year_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for r in rows:
        o={k:r.get(k,'') for k in fields};o['source_urls']=' | '.join(x['url'] for x in r['primary_sources']);o['evidence_paths']=' | '.join(r['evidence_paths']);w.writerow(o)
lines=['# 现用66条参考文献年份逐条核验','',f"源DOCX SHA256：`{inv['sha256']}`。核验范围为出版/公布年份及日期性质，不把访问日期当出版年。本轮复用逐条绑定的一手元数据审计，另核Guo发表PDF、Cambridge正式卷期、ACL原始会议记录及已封存官方HTML的PubDate。没有重写参考文献或主稿。",'',f"状态计数：{result['status_counts']}。未核实或不匹配编号：{result['unverified_numbers']}。",'', '|编号|现用年|核实年/日期性质|证据与范围|状态|','|---|---|---|---|---|']
for r in rows:
    date_note=f"{r['verified_issue_or_publication_year'] or '无发表年'}"+(f"；online {r['online_date']}" if r.get('online_date') else '')+(f"；成文 {r['issuer_date']}，官网 {r['web_publication_date']}" if r.get('issuer_date') else '')+(f"；访问 {r['access_date']}" if r.get('access_date') else '')
    urls='、'.join(f"[一手来源{i+1}]({x['url']})" for i,x in enumerate(r['primary_sources']))
    lines.append(f"|{r['number']}|{r['citation_year'] or '仅访问日期'}|{date_note}|{r['year_evidence'].replace('|','/')} {urls}|{r['status']}|")
lines+=['','完整著录、各条一手URL、原审计路径/记录号和原件SHA核对见同目录CSV/JSON。未记录的online月日为空，不能从DOI数字或访问日期补造。','', '特别核对：[16]2018卷期/2017online；[22]2023卷期/2022online；[26]2023卷期/2024-05-08online；[33]1997卷期/1998电子上线；[43]2026卷期/2025-09-19online；[64]2026-10-06仅访问日期。']
(OUT/'全66条参考文献年份核验.md').write_text('\n'.join(lines))
print(json.dumps({'counts':result['status_counts'],'unverified':result['unverified_numbers'],'local_hash_mismatches':[x for x in source_checks.values() if x.get('sha_matches') is False]},ensure_ascii=False))
