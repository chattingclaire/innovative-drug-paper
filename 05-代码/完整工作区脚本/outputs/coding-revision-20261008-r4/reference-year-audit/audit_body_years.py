from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re

OUT=Path(__file__).parent
BASE=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
inv=json.loads((OUT/'current_docx_reference_year_inventory.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={
 'annual_guidelines':str(OUT/'annual_guideline_metadata_check.json'),
 'policy_dates':str(BASE/'outputs/coding-revision-20261008-r4/references-51-65-date-audit/references_51_65_dates_evidence.json'),
 'policy_official':str(BASE/'outputs/final-three-department-20261008-human-validation-template/policy-source-audit/政策建议官方证据包-20261008.json'),
 'all66':str(OUT/'all66_reference_year_audit.json'),
 'interview':str(BASE/'outputs/final-three-department-20261007/prose_evidence_QA_refs61-63_interviews.json'),
 'casilli_pdf':str(BASE/'outputs/validation-expansion-20260926/参考文献补核来源/Casilli2023-Cambridge-primary.pdf'),
 'NHC2022_header':str(BASE/'政策文件/NHC-加强用药安全管理提升合理用药水平-2022.md'),
 'old51_scope':str(BASE/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl'),
}
review={
 1:('研究摘要2017—2026语料时间概括',[],'SCOPE_CONSISTENT_WITH_METHOD_WINDOW_NOT_CUTOFF_INDEPENDENTLY_VERIFIED',['old51_scope'],'机械source_title元数据最小2017、最大2026；摘要概括不等于每个政策发布日核验。'),
 6:('英文摘要2017—2026时间概括',[],'SCOPE_CONSISTENT_WITH_METHOD_WINDOW_NOT_CUTOFF_INDEPENDENTLY_VERIFIED',['old51_scope'],'与中文范围一致；不由DOI年或访问日推语料截止。'),
 9:('2025措施、2025版双目录自2026-01-01实施',[1,2,3],'DATE_VERIFIED',['policy_official','all66'],'措施成文2025-06-30/公布07-01；双目录成文2025-12-05/公布12-07，实施2026-01-01。'),
 12:('引言2017—2026语料时间概括',[],'SCOPE_CONSISTENT_WITH_METHOD_WINDOW_NOT_CUTOFF_INDEPENDENTLY_VERIFIED',['old51_scope'],'与方法2017至2026年7月一致；完整51来源日期清单尚待根代理定位。'),
 15:('段晓托等研究作为2017当时状况',[6],'YEAR_VERIFIED',['all66'],'现用文献2017,28(4):455–457，一手刊期原审计明确；未写成2026现况。'),
 17:('Casilli样本观察2017年7月至2022年12月',[15],'DATE_RANGE_VERIFIED_ORIGINAL_PDF',['casilli_pdf'],'原发表PDF物理1页摘要、2页Methods均列July2017 to December2022；这不是该文发表年，发表年2023另记。'),
 29:('临床综合评价指南2021版',[37],'YEAR_VERIFIED',['all66'],'2021通知及其附件版年一致。'),
 42:('方法预设公开材料窗口2017年至2026年7月；2017年36药目录事件',[38],'CUTOFF_REQUIRES_COMPLETE_CURRENT_SOURCE_DATE_TABLE',['old51_scope','all66'],'[38]2017年人社部发54号真实；不表述全国药品谈判始于2017。标题年份元数据支持2017—2026，但55原source_title到51实际条目的发布日期映射及2026年7月截止未由本审计独立重建，不能将该部分标成PASS。'),
 44:('2023—2026年申报五维名称延续；2026问答版年',[39,40],'YEARS_AND_HEADING_NAMES_VERIFIED_SCOPE_LIMITED',['annual_guidelines','all66'],'2023/24/25/26四原PDF各存在安全性、有效性、经济性、创新性、公平性名称；年度封面/版年与SHA已核。不推论细项要求、适用范围或定义四年不变；现引[39][40]只直接覆盖2026，年际依据宜通过来源清单保留。'),
 72:('2025FAQ示例及2022用药安全示例的来源年',[],'SOURCE_YEARS_VERIFIED_MECHANICALLY',['all66','NHC2022_header'],'两处已引短句由脚本分别与2025FAQ附件5及2022NHC源文去标点空白匹配，均真；不显示原句、预测或标签。NHC原文件头成文2022-07-27，官网来源链接2022-07-30。'),
 78:('2026年发布新版GCP',[51,52,53,54,35],'DATE_VERIFIED',['policy_dates'],'GCP2026-05-21成文、2026-06-08公布、2026-09-01施行；正文用发布年2026成立，非成效发生年。'),
 79:('2025问答版本',[39,55,56,37,57],'YEAR_VERIFIED',['policy_dates'],'2025-07-10原公告附件5，封面2025年7月；2026正式问答另列[40]，不得混年。'),
 87:('史录文访谈实际会议日期2025-06-09',[39,37],'INTERVIEW_ORIGINAL_HEADER_DATE_VERIFIED',['policy_dates','interview'],'原DOCX正文P002会议时间2025-06-09；文件名0605与正文不一致，已保留差异。访谈没有被塞入现66条Z文献，也没有虚构发表年。'),
 93:('参照药办法2026年2月实施；2026价格政策',[59,39,60],'DATE_VERIFIED',['policy_dates','policy_official'],'参照药2026-02-10发布且自发布之日起施行；价格意见2026-03-30成文/NHSA2026-04-14转载，均2026。'),
 96:('2025RWE试点通知部署2026工作；2026年1月网络公告',[35,61,62],'DATES_VERIFIED_PLANNED_VS_COMPLETED_LIMIT',['policy_dates','policy_official'],'2025-09-23通知部署2026数据库/评价工作；可信评价点网络公告2026-01-16。年度任务部署不能改写为全部目标已完成。'),
 97:('2026医保官方解读',[63,64,65],'DATE_VERIFIED',['policy_dates'],'活动实际日期2026-05-17，实录官网公布2026-05-26；[64]AIFA访问2026-10-06不是发表年；[65]期刊2021年。'),
 99:('2025版双目录规定2026年2月底前药事会期限',[3],'DATE_VERIFIED',['policy_official'],'通知版年2025、实施2026-01-01、原则上药事会期限2026年2月底，三者分别保留；非2026年新发双目录。'),
}
records=[]
for x in inv['body_year_paragraphs']:
    p=x['paragraph_index'];claim,refs,status,keys,note=review[p]
    records.append({'paragraph_index':p,'year_tokens':re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',x['text']),'claim_summary':claim,'citation_numbers':refs,'status':status,'evidence_paths':[sources[k] for k in keys],'evidence_note':note})
metadata=[]
for ln in Path(sources['old51_scope']).read_text().splitlines():
    r=json.loads(ln);metadata.append(r['source_title'])
titles=sorted(set(metadata))
result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_docx':inv['source'],'source_docx_sha256':inv['sha256'],'paragraphs_with_substantive_years_n':len(records),'scope':'All body paragraphs containing19xx/20xx in the current docx; author publication year vs substantive year/date separated. Does not inspect labels/scores.','records':records,'corpus_metadata_only':{'raw_source_title_unique_n':len(titles),'raw_source_titles_year_min':min(int(y) for t in titles for y in re.findall(r'20\d{2}',t)),'raw_source_titles_year_max':max(int(y) for t in titles for y in re.findall(r'20\d{2}',t)),'do_not_claim_equals51_sources':True,'july_cutoff_independent_status':'PENDING_COMPLETE_CURRENT_51_SOURCE_DATE_MAPPING'},'source_bindings':[{'path':p,'sha256':sha(p)} for p in sources.values()],'source_text_visibility_exception':str(OUT/'source_visibility_exception_metadata.json'),'remaining':['Current51source mapping and substantive2026-07 cutoff need precise source-date evidence; absence of contrary dates is not an independent cutoff confirmation.']}
(OUT/'body_substantive_year_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
lines=['# 正文实质年份独立核查','',f'共{len(records)}个含年份段落；逐段按现DOCX零基段落索引定位。未把文献作者出版年、政策成文日、网页发布日期、施行日、访问日、观察区间混为一类。','', '|段落索引|年份用途|核查结果|状态|','|---|---|---|---|']
for r in records:lines.append(f"|{r['paragraph_index']}|{r['claim_summary']}|{r['evidence_note']}|{r['status']}|")
lines += ['', '仍待独立补证的是实际51来源的完整发布日期映射与2026年7月截止；原55source_title只是元数据年界，不能冒充51条目日期检查。其余文献及政策年份未发现需改年的证据。','', '另有源PDF全文被web返回造成的源文本可见例外，仅保存ID/覆盖元数据，不用于开发，见source_visibility_exception_metadata.json。']
(OUT/'正文实质年份逐段核查.md').write_text('\n'.join(lines))
print(json.dumps({'body_year_paragraphs':len(records),'remaining':result['remaining']},ensure_ascii=False))
