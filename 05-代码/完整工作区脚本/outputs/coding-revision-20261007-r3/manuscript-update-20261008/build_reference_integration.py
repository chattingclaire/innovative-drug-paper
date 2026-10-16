"""Resolve staged citation keys without editing or renumbering the manuscript."""
from pathlib import Path
import hashlib
import json
from docx import Document

OUT = Path(__file__).resolve().parent
prose = json.loads((OUT / "完整论文局部替换稿.json").read_text())
methods = json.loads((OUT / "方法段替换稿与引用映射.json").read_text())
doc = Document(prose["baseline"]["path"])
existing = {int(p.text.split(']')[0][1:]): p.text.split(']', 1)[1].strip()
            for p in doc.paragraphs if p.text.startswith('[') and p.text.split(']')[0][1:].isdigit()}
mapping = {
    "GrimmerStewart2013": {"existing_number": 43, "entry": existing[43], "purpose": "任务及语料内验证原则"},
    "HorvitzThompson1952": {"existing_number": 47, "entry": existing[47], "purpose": "逆纳入概率估计总量，注意力为两个总量估计之比"},
    "WenHongExisting": {"existing_number": 26, "entry": existing[26], "purpose": "政府政策句段注意力测量"},
    "ChenXingpingExisting": {"existing_number": 27, "entry": existing[27], "purpose": "同句同维一次、跨维分别计数的关注结构比较"},
    "HeBaliRamesh2022": {
        "existing_number": None,
        "entry": "HE A J, BALI A S, RAMESH M. Active stewardship in healthcare: Lessons from China's health policy reforms[J]. Social Policy & Administration, 2022, 56(6):925–940. DOI:10.1111/spol.12832.",
        "journal": "Social Policy & Administration",
        "primary_url": "https://onlinelibrary.wiley.com/doi/10.1111/spol.12832",
        "purpose": "已有医保/卫健政策文本及政策工具协调研究，用于明确本文具体增量",
        "verification": "出版商/作者机构元数据与此前核读全文定位；本轮Crossref429保留，未重试，不影响已核出版商证据。",
    },
    "Guo2023Online2024": {
        "existing_number": None,
        "entry": "GUO W, WANG P, ZHANG Y, et al. Health Technology Assessment in China's Health Care Sector: Development and Applications[J]. Health Systems & Reform, 2023, 9(3):2327099. DOI:10.1080/23288604.2024.2327099.",
        "journal": "Health Systems & Reform",
        "primary_url": "https://doi.org/10.1080/23288604.2024.2327099",
        "fulltext_url": "https://researchonline.lshtm.ac.uk/id/eprint/4673940/1/Guo-etal-2024-Health-Technology-Assessment-in-Chinas-Health-Care-Sector.pdf",
        "purpose": "已有五维价值框架、公平可负担与保障缺口；不归本文首创",
        "verification": "agent核读已发表全文Table1；root独立Crossref元数据确认前三作者、卷期2023、在线2024-05-08。按卷期年著录，在线日期另存。",
        "volume_year": 2023,
        "online_date": "2024-05-08",
    },
    "Kroon2022": {
        "existing_number": None,
        "entry": "KROON A C, VAN DER MEER T, VLIEGENTHART R. Beyond Counting Words: Assessing Performance of Dictionaries, Supervised Machine Learning, and Embeddings in Topic and Frame Classification[J]. Computational Communication Research, 2022, 4(2):528–570. DOI:10.5117/CCR2022.2.006.KROO.",
        "journal": "Computational Communication Research",
        "primary_url": "https://www.aup-online.com/content/journals/10.5117/CCR2022.2.006.KROO",
        "fulltext_url": "https://pure.uva.nl/ws/files/118214028/Beyond_counting_words.pdf",
        "purpose": "词典/语境分类需以任务内参考验证，不援引其低分作为本研究合格线",
        "verification": "root新核出版社作者、题名、卷期页码、DOI、2022-10-01；agent已核大学正式全文的样本、人工、词典及Table3。",
    },
    "NHSAFAQ2025": {
        "existing_number": None,
        "entry": "国家医疗保障局. 国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整常用问答（2025年版）[EB/OL]. (2025-07-10)[2026-10-08]. https://www.nhsa.gov.cn/art/2025/7/10/art_109_17198.html.",
        "primary_url": "https://www.nhsa.gov.cn/art/2025/7/10/art_109_17198.html",
        "source_component": "正式公告附件5，官方解释材料",
        "purpose": "支付标准包含基金及个人费用、基金支付监测与可及性共同表达的实际2025原句",
        "verification": "官网搜索索引为2025-07-10并列附件5；直开超时、gov附件直开403。完整原件已存且root本轮重新核封面及物理11/21页文字；访问日期为本轮引用核查日期，未冒称本轮重新下载成功。",
        "local_path": "/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/医保2025公告附件/5.pdf",
        "local_sha256": "7f5b1829d0030b3402f85d288edf764bc3195bb99ca1c419dd8605342eb70d68",
        "n_physical_pages": 23,
        "unit_ids": ["RECODE25-00647", "RECODE25-00752"],
        "gov_reprint_firstpublished_date": "2025-07-11",
        "announcement_official_date": "2025-07-10",
    },
    "RaoWuYue1992": {
        "existing_number": None,
        "entry": "RAO J N K, WU C F J, YUE K. Some recent work on resampling methods for complex surveys[J]. Survey Methodology, 1992, 18(2):209–217.",
        "journal": "Survey Methodology",
        "primary_url": "https://www150.statcan.gc.ca/n1/en/pub/12-001-x/1992002/article/14486-eng.pdf",
        "purpose": "层内重标bootstrap及有限总体抽样设计依据；不宣称稀有二元κ百分位区间精确覆盖",
        "verification": "官方发表记录及CRAN原文档核对n_h−1；实际代码及独立数学QA核公式，未伪称本轮完整取读原PDF。",
        "implementation_crosscheck": "https://search.r-project.org/CRAN/refmans/bootsurv/html/boot.weights.stsrs.html",
    },
    "NHCMonitoring2019": {
        "existing_number": None,
        "entry": "国家卫生健康委. 关于开展药品使用监测和临床综合评价工作的通知：国卫药政函〔2019〕80号[EB/OL]. (2019-04-09)[2026-10-08]. https://www.nhc.gov.cn/yaozs/c100097/201904/6bc8f273684845d3ab76fed841eb42d2.shtml.",
        "primary_url": "https://www.nhc.gov.cn/yaozs/c100097/201904/6bc8f273684845d3ab76fed841eb42d2.shtml",
        "purpose": "使用监测数据共享、采购及上下级医疗机构用药衔接、评价结果应用于供应与使用政策的实际依据",
        "verification": "官网正文搜索索引及官方政策目录均核2019-04-09发布日期；直接打开412。正文依据保存正式来源及00337/00338/00347逐句核对，未冒称本轮官网全文下载成功。基稿[57]为2018处方审核规范，不能代指本政策。",
        "local_path": "/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/NHC-药品使用监测和临床综合评价-2019-恢复正文.txt",
        "local_sha256": "5a8b433e2ee0b4e82c82f64a84a312feff292e009d92ab52767bd9cde1ec072c",
        "unit_ids": ["RECODE25-00337", "RECODE25-00338", "RECODE25-00347"],
    },
}
assert set(mapping) == set(prose["source_keys"])
faq = mapping['NHSAFAQ2025']
assert hashlib.sha256(Path(faq['local_path']).read_bytes()).hexdigest() == faq['local_sha256']
for item in mapping.values():
    if item.get('local_path'):
        assert hashlib.sha256(Path(item['local_path']).read_bytes()).hexdigest() == item['local_sha256']
warning_2025 = {"Wireless Personal Communications", "Natural Resources Forum", "Computers & Electrical Engineering", "Numerical Heat Transfer Part A-Applications", "Scalable Computing-Practice and Experience"}
for item in mapping.values():
    if item.get('journal'):
        item['verified_2025_CAS_warning_list_match'] = item['journal'].casefold() in {j.casefold() for j in warning_2025}
report = {
    "status": "all_staged_citation_keys_resolved_no_DOCX_renumbering",
    "date": "2026-10-08",
    "source_keys": mapping,
    "CAS_scope": "新加期刊均未命中已取得2025官方五刊名单。2026是否新发布名单未确认，不能称全年度审查通过；最终采用后的全文实际参考集合仍需再核。",
    "CAS_primary_2025": "https://www.iae.cas.cn/jw/kycx/202504/t20250401_7585150.html",
    "numbering_policy": "Final builder resolves baseline numbers and new keys, removes unused bibliography entries, and numbers references by first appearance. No final numbers assigned here.",
    "old_method_references_scope": "Sevenans会议稿/Loughran金融词典及旧超几何/Bonferroni引用若在最终正文无调用，依引用完整性剔除；不把旧方法作为新统计依据。",
    "DOCX_modified": False,
}
(OUT/'新引用接入清单.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# 新引用接入清单', '', f'2026年10月8日。全部{len(mapping)}个草稿来源key已解析，正式序号待最终引用首次出现顺序统一编排，原DOCX未改。', '']
for key,item in mapping.items():
    md.extend(['## '+key,'',item['entry'],'',item['purpose'],'',item.get('verification','沿用已核基稿条目；现有序号'+str(item['existing_number'])),''])
md.extend(['## 核验范围','',report['CAS_scope'],'',report['numbering_policy'],'',report['old_method_references_scope']])
(OUT/'新引用接入清单.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'citation_keys_n':len(mapping),'new_entries_n':sum(x['existing_number'] is None for x in mapping.values()),'all_keys_resolved':True,'DOCX_modified':False},ensure_ascii=False))
