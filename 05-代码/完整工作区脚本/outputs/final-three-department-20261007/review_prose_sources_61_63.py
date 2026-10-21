"""Read-only evidence review of new background/method references and interviews."""
import datetime, hashlib, json, runpy
from pathlib import Path
from docx import Document

B=Path(__file__).resolve().parent
A=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/04-访谈与研讨会原始资料')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def anchors(fn,fragments):
    p=A/fn;d=Document(p);out=[]
    for fragment in fragments:
        matches=[{'paragraph_1based':i+1,'text':x.text} for i,x in enumerate(d.paragraphs) if fragment in x.text]
        assert matches,(fn,fragment)
        out.append({'fragment':fragment,'matches':matches})
    return {'path':str(p),'sha256':sha(p),'anchors':out}

def main():
    prose=B/'final_prose.py';p=runpy.run_path(str(prose));updates=p['UPDATES'];refs=p['NEW_REFERENCES']
    interview=[
      anchors('史录文教授访谈会议纪要-0605.docx',[
        '会议时间：2025年6月9日星期一','各个维度之间的权重比例系数没有明确的绝对标准，但倾向是从健康需求的角度',
        '给了参照药、同意进入下一阶段后','现在商保的问题是拿不到数据，没法测算','商保可以基于公立医院的数据进行测算']),
      anchors('医保局专家调研-0616.docx',[
        '创新、提升、改进和同质','PPT在某些方面描述不够清晰','为什么自己的一类新药在医保谈判中却无法获得理想的价格',
        '不能仅仅因为获得了1.1类新药的认定'])]
    workshop=[
      anchors('创新药政策（百济神州）会议纪要-250212.docx',['会议时间：2025年2月12日','会议主题：创新药医保政策、市场环境及研究方向']),
      anchors('创新药专家咨询会-0319.docx',['2025年3月19日']),
      anchors('0514创新药研讨会议程.docx',['2025年5月14日14:00-17:00','百济、博锐药企医保部门专家讲医保申请实操','聚焦研究方向，修改访谈和调研问题'])]
    result={'checked_at':datetime.datetime.now().astimezone().isoformat(),'reviewed_file':str(prose),'reviewed_sha256':sha(prose),
      'main_prose_modified':False,
      'references':[
       {'id':61,'current_reference':refs[61],'claim':updates[9],
        'status':'supported_by_NDRC_original_PDF_and_official_full_text',
        'official_pdf_url':'https://www.ndrc.gov.cn/fggz/fzzlgh/gjfzgh/202603/U020260317369114704096.pdf',
        'official_full_text_url':'https://www.dswxyjy.org.cn/n1/2026/0314/c423712-40681873.html',
        'source_provenance':'NDRC官方完整PDF140页，独立核对SHA及PDF96—97页/正文91—92页图像；并核中共中央党史和文献研究院转载《人民日报》全文。',
        'local_pdf':str(B/'source-checks/十五五纲要2026.pdf'),
        'local_pdf_sha256':sha(B/'source-checks/十五五纲要2026.pdf'),
        'page_images_visually_inspected':[str(B/f'source-checks/十五五纲要2026-p{i}.png') for i in (96,97)],
        'locators':[{'printed_page':91,'physical_page_1based':96,'content':'第三节标题明确三医协同发展和治理机制。'},
                    {'printed_page':92,'physical_page_1based':97,'content':'第三节续段明确创新药审评审批和医保支持创新药机制。'}],
        'locator':'第三十九章 加快建设健康中国，第三节 健全医疗医保医药协同发展和治理机制',
        'supported_content':['三医协同发展和治理','优化创新药和临床急需药品审评审批','健全医保支持创新药和医疗器械高质量发展机制'],
        'reference_suggestion':'正文概括准确。文献表宜补可追溯官方链接与日期；不要将转载机关自动写成纲要制定机关。'},
       {'id':62,'current_reference':refs[62],'status':'supported; exact_long_title_now_completed',
        'official_url':'https://www.nhsa.gov.cn/art/2025/12/7/art_14_18972.html',
        'exact_page_title':'国家医保局 人力资源社会保障部印发2025年版国家基本医疗保险、生育保险和工伤保险药品目录和商业健康保险创新药品目录',
        'published_date':'2025-12-07','implementation_date':'2026-01-01','first_commercial_catalogue_n':19,
        'reference_suggestion':'国家医疗保障局.国家医保局 人力资源社会保障部印发2025年版国家基本医疗保险、生育保险和工伤保险药品目录和商业健康保险创新药品目录[EB/OL].(2025-12-07)[2026-10-07].https://www.nhsa.gov.cn/art/2025/12/7/art_14_18972.html.',
        'claim_suggestion':'首版商业健康保险创新药品目录自2026年1月1日起实施。'},
       {'id':63,'current_reference':refs[63],'status':'supported',
        'primary_journal_url':'https://www.tandfonline.com/doi/abs/10.1080/01621459.1952.10483446',
        'local_pdf':str(B/'source-checks/HT1952.pdf'),'local_pdf_sha256':sha(B/'source-checks/HT1952.pdf'),
        'bibliography_verified':'D. G. Horvitz; D. J. Thompson; 1952; JASA47(260):663–685; DOI10.1080/01621459.1952.10483446。2012-04-11是数字上线日期，不替换1952出版年。',
        'locators':[{'printed_page':666,'physical_page_1based':5,'content':'一阶与二阶纳入概率定义，式(4)(5)。'},
                    {'printed_page':669,'physical_page_1based':8,'content':'式(6)：T̂=Σ xi/P(ui)，支持总体合计的逆纳入概率估计；同页列等概率抽样N/n权重。'}],
        'claim':updates[56],
        'semantic_review':'当前先估计各维句次再除以五维总计的表述准确。HT支持各维总体合计估计，最终占比是估计总量之比，不附带声称比率本身无偏。'}],
      'interview_source_bindings':interview,'three_workshop_source_bindings':workshop,
      'paragraph_reviews':[
       {'paragraph':61,'status':'supported_after_precision_update','text':updates[61],
        'judgement':'2025年2月至6月范围内三场会议与两份专家纪要有来源对应。现文未虚构药监直接访谈；已读会议材料更偏企业准入和跨环节协调问题。',
        'suggestion_implemented':'药监环节主要依据公开技术文件，研讨会材料补充跨环节问题。'},
       {'paragraph':62,'status':'supported','text':updates[62],
        'judgement':'三个主题是本文对既有材料的整理，未称访谈当时使用与现论文完全相同的统一提纲。可保留。'},
       {'paragraph':84,'status':'supported','text':updates[84],
        'judgement':'医保专家第2、6节明确区分注册分类、实际临床比较价值与价格预期。现在取消伪逐字引号、采用转述，契合纪要。'},
       {'paragraph':86,'status':'supported','text':updates[86],
        'judgement':'高校专家健康需求导向、医保专家临床价值分层后开展成本效果与预算影响评价，均有对应原段。末句是作者结合政策提出的分析要求，不应改成受访者原话。'},
       {'paragraph':101,'status':'supported_after_medical_data_wording_update','text':updates[101],
        'judgement':'医保专家关于PPT不清晰直接影响打分可支持申报材料影响理解。高校纪要谈商保因拿不到公立医院数据而难以测算，当前概括其提到经济测算与医疗数据获取困难有依据。',
        'optional_precision':'如需点明具体主体，可写高校药事管理专家指出商保获得公立医院数据存在困难，影响测算；现文不是伪逐字引语。'}],
      'date_note':'史录文文件名0605，正文会议日期为2025-06-09；叙述与资料台账按正文日期，不按文件名推定。',
      'scope_note':'访谈用于解释具体实践问题，当前文本没有把受访者对正式规则的概述当作政策原文替代，也没有据此另造三部门量化结果。'}
    binding=json.loads((B/'source-checks/十五五纲要2026-matched-pages.json').read_text())
    assert result['references'][0]['local_pdf_sha256']==binding['sha256']=='29b3c70720b1faff458a123cb29672ee2ee8874a53b6d4a91f402a73f6945027'
    assert '国家基本医疗保险、生育保险和工伤保险药品目录和商业健康保险创新药品目录' in refs[62]
    html=B/'source-checks/NHSA-ref62-20251207-policy-review.html'
    if html.exists():result['references'][1]['local_snapshot']={'path':str(html),'sha256':sha(html)}
    out=B/'prose_evidence_QA_refs61-63_interviews.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(str(out))

if __name__=='__main__':main()
