"""Read-only reference/date evidence consolidation. No coding labels or scores."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parent / '创新药论文-完整归档-20260914'
ORIGINAL = ARCHIVE / '02-原始数据-政策文本/政策文件原件'
RESTORED = ARCHIVE / '12-投稿定稿工作区/原文补全'
POLICY = ROOT / 'outputs/final-three-department-20261008-human-validation-template/policy-source-audit'
PRIOR = ROOT / 'outputs/coding-revision-20261007-r3/manuscript-update-20261008/52段修正回验与参考真实性审计-20261008.json'
INTERVIEW_PRIOR = ROOT / 'outputs/coding-revision-20261007-r3/insights-20261008/访谈证据核验.json'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def evidence_file(p, role):
    assert p.is_file(), p
    return {'path': str(p), 'sha256': sha(p), 'role': role}


def norm(t):
    return re.sub(r'[^\w]', '', re.sub(r'^\[\d+\]', '', t)).lower()


def main():
    entries = json.loads((OUT / 'current_reference_entries_51_65.json').read_text())
    prior = json.loads(PRIOR.read_text())
    candidates = prior['old62_audit_crosswalk'] + prior['new6_audit']
    details = {
        51: dict(year=2025, status='CONFIRMED_YEAR_FRESH_PRIMARY_AND_LOCAL_ORIGINAL',
                 dates={'issue_date': '2025-09-09', 'issuer_web_publication_date': '2025-09-12', 'official_reprint_date': '2025-09-16', 'effective_rule': '自发布之日起施行'},
                 urls=['https://www.ccfdie.org/zryyxxw/yaop/cfdatz/webinfo/2025/09/1756485762591435.htm', 'https://www.cde.org.cn/main/att/download/f0e4fbac4fb4af923215467ee0773d1d'],
                 files=[(ORIGINAL / 'CDE-创新药研发期间风险管理计划撰写指导原则-2025.pdf', '正式通告网页存档及附件；物理1页发布日期20250912、落款2025年9月9日；2页封面2025年9月')],
                 note='签署日、原网站发布日、转载日分别记录；2025/10/1打印时间与CMS 2026再生成时间均不是发布年份。'),
        52: dict(year=2021, status='CONFIRMED_YEAR_FRESH_OFFICIAL_REPRINT_AND_LOCAL_ORIGINAL',
                 dates={'issuer_web_publication_date': '2021-11-19', 'official_reprint_date': '2021-11-26', 'effective_rule': '自发布之日起施行'},
                 urls=['https://www.ccfdie.org/zryyxxw/cfdazsjg/ypspzx/webinfo/2021/11/1632899010634031.htm', 'https://www.cde.org.cn/main/att/download/dfe38dda5033466acf410516efe35f2d'],
                 files=[(ORIGINAL / 'NMPA-抗肿瘤药物临床研发指导原则-2021.pdf', '已封存正式附件；日期具体分项来自本轮重开的官方转载')],
                 note='2021年第46号；官方转载明确摘自CDE网站2021-11-19。页尾CMS publishdate 2026不能当原始发表年。'),
        53: dict(year=2020, status='CONFIRMED_YEAR_FRESH_OFFICIAL_REPRINT_AND_PRIOR_PRIMARY_AUDIT',
                 dates={'issue_date_prior_audit': '2020-01-03', 'original_web_publication_date': '2020-01-07', 'official_reprint_date': '2020-01-10'},
                 urls=['https://www.ccfdie.org/zryyxxw/yaop/cfdatz/webinfo/2020/01/1573207428155005.htm', 'https://amr.hainan.gov.cn/himpa/HICDME/ztzl/zssjyj/202107/P020210707553294915372.pdf'],
                 files=[(RESTORED / 'NMPA-真实世界证据2020-海南官方.pdf', '官方保存附件；2021 URL为保存路径，非该指导原则原始年份')],
                 note='本轮官方转载重开确认于2020年1月7日发布；1月3日签署日期沿用已有原文审计，不声称本轮重新取得NMPA原始网页。'),
        54: dict(year=2026, status='CONFIRMED_YEAR_FRESH_GOVERNMENT_REPRINT',
                 dates={'issue_date': '2026-05-21', 'web_publication_date': '2026-06-08', 'effective_date': '2026-09-01'},
                 urls=['https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260608103856150.html', 'https://yjj.sh.gov.cn/qtgzwj/20260608/89cbf084b5cb4eab8fd0fb56d8538a1d.html'],
                 files=[(RESTORED / 'NMPA-药物临床试验质量管理规范GCP-2026-官方转载正文.txt', '已封存2026修订规范正文；本轮上海药监局原公告转载确认签署/发布/施行日期')],
                 note='2026年第50号、附件1；2020版同时废止。2026修订年份真实，不是把访问年份写入标题。'),
        55: dict(year=2026, status='CONFIRMED_YEAR_FRESH_ISSUER_PUBLICATION',
                 dates={'formal_attachment_publication_date': '2026-05-31', 'attachment_number': 3},
                 urls=['https://www.nhsa.gov.cn/art/2026/5/31/art_109_20816.html', 'https://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=acb8bed67d3d475a8e2a4341b7b4f6d5.pdf'],
                 files=[(ORIGINAL / 'NHSA-谈判药品续约规则-2026-正式版.pdf', '正式附件3，与征求意见稿、2023/2024版区分')],
                 note='本轮正式发布公告重开核实；未推定一个原文未列的独立统一生效日。'),
        56: dict(year=2025, status='CONFIRMED_YEAR_LOCAL_ORIGINAL_PRIOR_PRIMARY_DATE_CURRENT_ENDPOINT_TIMEOUT',
                 dates={'official_announcement_date_prior_primary_audit': '2025-07-10', 'cover_month': '2025-07', 'government_reprint_date_prior_audit': '2025-07-11', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhsa.gov.cn/art/2025/7/10/art_109_17198.html'],
                 files=[(RESTORED / '医保2025公告附件/5.pdf', '原公告附件5，封面明确2025年版、2025年7月')],
                 note='本轮直开超时；年份由存档正式原件确认，具体7月10日沿用上一轮原站索引核查。不得声称本轮重新下载成功，亦不能替换为2026 FAQ。'),
        57: dict(year=2019, status='CONFIRMED_YEAR_PRIOR_PRIMARY_INDEX_AND_CURRENT_OFFICIAL_SEARCH_DIRECT_412',
                 dates={'issue_date': '2019-04-03', 'web_publication_date_prior_primary_audit': '2019-04-09', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhc.gov.cn/yaozs/c100097/201904/6bc8f273684845d3ab76fed841eb42d2.shtml'],
                 files=[(RESTORED / 'NHC-药品使用监测和临床综合评价-2019-恢复正文.txt', '已保存正式来源恢复正文'), (ORIGINAL / 'NHC-药品使用监测和临床综合评价-2019.md', '存档元数据及落款4月3日；该MD将成文日标作发布日期，不能据此否定网页4月9日')],
                 note='本轮官方检索结果可核国卫药政函〔2019〕80号及落款4月3日，直开412。参考条目网页4月9日来自既往官方目录/索引，不把两种日期混为一项。'),
        58: dict(year=2020, status='CONFIRMED_YEAR_PRIOR_SEALED_PRIMARY_AUDIT_CURRENT_ENDPOINT_UNAVAILABLE',
                 dates={'issue_date_prior_primary_audit': '2020-06-29', 'original_web_publication_date_prior_audit': '2020-06-30'},
                 urls=['https://www.nmpa.gov.cn/zhuanti/ypzhcglbf/ypzhcglbfzhcwj/20200630180301525.html', 'https://m.cnpharm.com/c/2020-06-30/739326.shtml'],
                 files=[(ARCHIVE / '06-参考文献/稿5新增文献原文/nmpa44_attach.doc', '已有第44号通告附件原件；本轮只核文件绑定、不打开注册条目正文')],
                 note='NMPA原链不可达，中国医药报正式来源转载本轮超时。2020年第44号及签署日期沿用已封存原文审计；不是无证据新PASS。'),
        59: dict(year=2026, status='CONFIRMED_YEAR_FRESH_ISSUER_PUBLICATION',
                 dates={'issue_date': '2026-02-10', 'web_publication_date': '2026-02-10', 'effective_date': '2026-02-10', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhsa.gov.cn/art/2026/2/10/art_109_19642.html'],
                 files=[(POLICY / 'precommunication2026.html', '保存原站网页含PubDate及发布/施行关系'), (POLICY / 'precommunication2026.txt', '原公告正文及落款')],
                 note='发布日期当天施行由“自发布之日起施行”支持；依据2025措施不使本办法成为2025文件。'),
        60: dict(year=2026, status='CONFIRMED_YEAR_FRESH_GOVERNMENT_DATABASE_AND_SAVED_ISSUER_REPRINT',
                 dates={'issue_date': '2026-03-30', 'mofcom_database_publication_and_implementation_fields': '2026-03-30', 'nhsa_reprint_web_date': '2026-04-14'},
                 urls=['https://www.gov.cn/zhengce/zhengceku/202604/content_7065542.htm', 'https://policy.mofcom.gov.cn/claw/clawContent.shtml?id=105596', 'https://www.nhsa.gov.cn/art/2026/4/14/art_53_20215.html'],
                 files=[(POLICY / 'price2026.html', '国家医保局转载网页PubDate2026-04-14、正文落款3月30日'), (ROOT / 'outputs/validation-expansion-20260926/参考文献补核来源/国办发2026_9号-商务部法规库.html', '已保存政府法规库发布/实施字段')],
                 note='国办发〔2026〕9号、2026年正确。中国政府网本轮403；3月30日为成文/法规库日期，4月14日为现保存医保局网页发布日，不能互相替代。'),
        61: dict(year=2025, status='CONFIRMED_YEAR_FRESH_ISSUER_PUBLICATION',
                 dates={'issue_date': '2025-09-23', 'web_publication_date': '2025-09-23', 'startup_phase': '2025年底前', 'practice_phase': '2026年', 'initial_results_deadline': '2026年底前', 'application_phase': '2027年', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhsa.gov.cn/art/2025/9/23/art_109_17984.html'],
                 files=[(POLICY / 'rwepilot2025.html', '原站保存网页'), (POLICY / 'rwepilot2025.txt', '通知正文及2025/2026/2027阶段日期')],
                 note='正文“2025通知部署2026建设数据库、开展评价并形成初步成果”准确，不应改成2026发布。'),
        62: dict(year=2026, status='CONFIRMED_YEAR_FRESH_ISSUER_PUBLICATION',
                 dates={'issue_date': '2026-01-16', 'web_publication_date': '2026-01-16', 'first_network_covenant_signing_date': '2026-01-16', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhsa.gov.cn/art/2026/1/16/art_109_19379.html'],
                 files=[(POLICY / 'trustednetwork2026.html', '原站保存网页'), (POLICY / 'trustednetwork2026.txt', '公约/成员公告原文')],
                 note='公告载首批79家1月16日集中签署；正文“2026年1月首批网络已组建”有日期依据。'),
        63: dict(year=2026, status='CONFIRMED_YEAR_FRESH_ISSUER_PUBLICATION',
                 dates={'event_date': '2026-05-17', 'transcript_web_publication_date': '2026-05-26', 'access_date_in_reference': '2026-10-08'},
                 urls=['https://www.nhsa.gov.cn/art/2026/5/26/art_14_20707.html'],
                 files=[(POLICY / 'interpretation2026.html', '原站保存网页'), (POLICY / 'interpretation2026.txt', '解读实录含活动发生日与非正式调整依据说明')],
                 note='活动发生5月17日，网页实录发布5月26日，参考条目列网页日期正确；解读不是正式调整政策的生效公告。'),
        64: dict(year=None, status='PUBLICATION_YEAR_UNKNOWN_ACCESS_DATE_SEPARATE_NO_YEAR_INFERENCE',
                 dates={'publication_date': None, 'access_date_in_reference': '2026-10-06', 'current_recheck_date': '2026-10-08'},
                 urls=['https://www.aifa.gov.it/registri-farmaci-sottoposti-a-monitoraggio'],
                 files=[],
                 note='本轮重开现行官方页面，未确认该总览页独立发表日期。页面更新列表和全站新闻出现2026日期不等于总览发表年。现参考条目仅列方括号访问日期，不含2026发表年，无需凭访问年补年；10月6日访问依据沿用已封存审计。'),
        65: dict(year=2021, status='CONFIRMED_YEAR_FRESH_PUBLISHER_METADATA_AND_LOCAL_ORIGINAL',
                 dates={'received_date': '2020-06-16', 'online_publication_date': '2021-01-28', 'issue_publication_date': '2021-02-01'},
                 urls=['https://www.yydbzz.com/CN/10.3870/j.issn.1004-0781.2021.02.002', 'https://www.yydbzz.com/CN/article/downloadArticleFile.do?attachType=PDF&id=159610'],
                 files=[(ARCHIVE / '06-参考文献/原文PDF与MD/医保药品目录调整之退出机制的国际经验借鉴_岳晓萌.pdf', '已发表原文PDF')],
                 note='出版社元数据确认2021年40卷2期158–162页；2020为收稿年，不能作出版年。'),
    }
    rows = []
    for entry in entries['entries']:
        number = entry['number']
        detail = details[number]
        matches = [r for r in candidates if norm(r['entry']) == norm(entry['text'])]
        original_year_match = re.search(r'\[Z\]\.\s*(\d{4})', entry['text'])
        if not original_year_match:
            original_year_match = re.search(r'\(?(20\d{2})-\d{2}-\d{2}\)?\[', entry['text'])
        if number == 65:
            original_year = 2021
        elif number == 64:
            original_year = None
        else:
            original_year = int(original_year_match[1])
        row = {
            'current_reference_number': number,
            'current_reference': entry['text'],
            'original_publication_year_in_current_reference': original_year,
            'confirmed_publication_year': detail['year'],
            'status': detail['status'],
            'substantive_dates': detail['dates'],
            'primary_urls': detail['urls'],
            'evidence_files': [evidence_file(p, role) for p, role in detail['files']],
            'date_boundary_and_limits': detail['note'],
            'proposed_publication_year_change': False,
            'prior_audit_match_by_full_citation_not_old_number': [
                {'audit_path': str(PRIOR), 'audit_path_sha256': sha(PRIOR),
                 'old_actual_new_number': r['actual_new_number'], 'audit_group': r['audit_group'],
                 'original_underlying_audit_path': r['audit_path'], 'original_underlying_record': r['audit_record']}
                for r in matches
            ],
        }
        if row['confirmed_publication_year'] is not None:
            assert row['original_publication_year_in_current_reference'] == row['confirmed_publication_year']
        rows.append(row)
    assert len(rows) == 15
    interview = json.loads(INTERVIEW_PRIOR.read_text())
    interview_meta = []
    for s in interview['sources']:
        p = Path(s['path'])
        assert sha(p) == s['sha256']
        interview_meta.append({k: s[k] for k in ('source_id', 'path', 'sha256', 'date_status')})
    source_docx = Path(entries['source_docx'])
    assert sha(source_docx) == entries['source_docx_sha256']
    report = {
        'audit_type': 'read_only_current_references_51_65_publication_and_substantive_dates',
        'checked_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'source_docx': str(source_docx), 'source_docx_sha256': sha(source_docx),
        'source_docx_unchanged': True,
        'reference_scope_n': 15,
        'references': rows,
        'confirmed_years_n': 14,
        'publication_year_unknown_n': 1,
        'year_corrections_supported_n': 0,
        'scope_correction': 'Actual current [51]–[65] include no interview/meeting-minute reference entries. Z denotes cited official policy documents here, not automatically interview material.',
        'interview_date_supplement': {
            'prior_audit': evidence_file(INTERVIEW_PRIOR, '上一轮完整原件只读核验及日期不确定性'),
            'fresh_date_headers': evidence_file(OUT / 'interview_date_header_crosscheck.json', '本轮仅核日期头；不展开访谈实质或编码结果'),
            'sources': interview_meta,
            'body_date_claim': '现稿正文“2025年6月9日史录文教授访谈纪要”与原件P002一致；文件名0605的冲突保留，不能改为2026年或擅定6月5日。',
            'confirmed_explicit_dates': {'SLW': '2025-06-09', 'CONSULT': '2025-03-19', 'BEIGENE': '2025-02-12'},
            'unknown_date_boundary': '0616、0714、0514及其他未明示年份的纪要，未凭文件名月日/归档年/相对日期补2025或2026。',
        },
        'body_substantive_date_checks': [
            {'body_paragraph_index_zero_based': 79, 'claim': '2025年官方问答', 'reference': 56, 'assessment': '2025附件原件封面确认；不可换成2026问答'},
            {'body_paragraph_index_zero_based': 87, 'claim': '2025年6月9日史录文教授访谈', 'assessment': '原件P002确认；文件名0605冲突保留'},
            {'body_paragraph_index_zero_based': 93, 'claim': '2026年药品价格政策', 'reference': 60, 'assessment': '2026年成文/发布真实，3月30日与4月14日网页日期区分'},
            {'body_paragraph_index_zero_based': 96, 'claim': '2025通知部署2026数据库、评价及初步成果；2026年1月首批网络已组建', 'references': [61, 62], 'assessment': '两份原站公告及阶段条款确认，发布时间与工作执行年未混淆'},
            {'body_paragraph_index_zero_based': 97, 'claim': '2026年医保官方解读', 'reference': 63, 'assessment': '活动5月17日，文字实录5月26日；不能当正式政策生效日期'},
            {'body_paragraph_index_zero_based': [9, 99], 'claim': '2025双目录自2026年1月实施；原则上2026年2月底前药事会', 'reference': 3, 'assessment': '超出51–65的旁证：保存正式通知分别明确2026年1月1日起执行、原则上2026年2月底前，供全66核查合并', 'evidence_file': evidence_file(POLICY / 'dual_directory2025.txt', '保存正式双目录通知日期条款')},
        ],
        'method': 'Current DOCX reference paragraphs extracted read-only; retained reference metadata matched by exact normalized citation/title, not stale numbering. Prior sealed primary audits reused transparently; necessary issuer/government/publisher pages reopened. No DOCX authoring or layout claim.',
        'not_claimed': ['All dates freshly downloaded', 'AIFA publication year 2026', 'Undated meeting minutes formed in 2026', 'Policy event date equals webpage publication date', 'CMS rebuild/footer/printing time equals publication date'],
        'labels_or_scores_loaded': False,
        'manuscript_or_reference_entries_edited': False,
    }
    (OUT / 'references_51_65_dates_evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 现稿第51至65条文献日期核查', '',
             '15条中14条已有出版年份与原件/官方或出版商证据一致，未发现支持改年的证据。AIFA总览页发表年未确认，现条目仅列访问日期，继续保留此区分。现稿这15条没有访谈或会议纪要参考条目；额外核对访谈日期，史录文原件P002明确2025年6月9日。未改DOCX、参考条目或规则。', '',
             '|现编号|原年|确认年|实质日期及核验边界|', '|---|---|---|---|']
    for r in rows:
        lines.append(f"|{r['current_reference_number']}|{r['original_publication_year_in_current_reference'] or '未列发表年'}|{r['confirmed_publication_year'] or '未知'}|{r['date_boundary_and_limits']}|")
    lines.extend(['', '逐条原件路径、SHA256、官方URL、原年、确认年、日期类别、检索受限项均见 `references_51_65_dates_evidence.json`。56/57/58的具体网页日期部分依既往封存官方审计，本轮原站存在超时/412/不可达；未冒称全部本轮新取全文。', '',
                  '史录文2025-06-09、咨询会2025-03-19、百济纪要2025-02-12均有明确日期头。0616、0714、0514等缺完整年份的材料继续记未知，不凭归档、文件名月日补年。AIFA列表中的2026更新/新闻日期也不能代表总览页发表年。'])
    (OUT / '现稿51至65条文献年份与实质日期核查.md').write_text('\n'.join(lines) + '\n')
    seal_files = [p for p in OUT.iterdir() if p.is_file() and p.name != 'date_audit_artifact_seal.json']
    (OUT / 'date_audit_artifact_seal.json').write_text(json.dumps({
        'source_docx_unchanged': True, 'source_docx_sha256': sha(source_docx),
        'labels_or_scores_loaded': False,
        'artifacts_sha256': {p.name: sha(p) for p in sorted(seal_files)},
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'references_n': 15, 'confirmed_years_n': 14, 'publication_year_unknown_n': 1,
                      'supported_year_changes_n': 0,
                      'report_sha256': sha(OUT / 'references_51_65_dates_evidence.json'),
                      'seal_sha256': sha(OUT / 'date_audit_artifact_seal.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
