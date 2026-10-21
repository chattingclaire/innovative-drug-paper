from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
OUT=Path('/PROJECT_ROOT/outputs/validation-expansion-20260926')
T=OUT/'tmp/附录A压缩独立核对快照'
m=json.loads((T/'manifest.json').read_text()); standards=json.loads((T/'protocol-manifest.json').read_text())
A=[{r['p']:r['text'] for r in json.loads(Path(x['paragraphs_path']).read_text())} for x in m]
for x in m+standards:
 assert hashlib.sha256(Path(x['snapshot_path']).read_bytes()).hexdigest()==x['sha256']
 live=hashlib.sha256(Path(x['source_path']).read_bytes()).hexdigest()
 x['live_source_sha256_at_report_write']=live;x['live_source_same_as_snapshot']=live==x['sha256']
paragraph_matches=[{'original_paragraph':p,'supplement_paragraph':p-100,'equal_text':A[1][p]==A[2][p-100]} for p in range(102,116)]
assert all(x['equal_text'] for x in paragraph_matches)
assert A[2][0] in A[0][102]
issue={
 'id':'A-F01','candidate_paragraph':107,'original_paragraph':107,'supplement_paragraph':7,
 'candidate_sentence':'支付保障范围扩展、配备用药限制解除、明确治疗需求及送药安排按实质内容判读，供应状况资料要求亦可计入。',
 'original_clause':'明确未满足的治疗需求、药品保障机制、医保覆盖和常规送药获取安排按实质内容判读',
 'judgment':'“未满足的”是保障获取构念的实质限定，不是可无损删除的举例。压缩后“明确治疗需求”可能包括一般适应症、疾病治疗目标或常规治疗需求，而这些内容本身不能自动构成F。完整配套细则仍保留原口径，但候选概述不宜给出较宽的规则。',
 'standard_basis':[{'path':standards[0]['source_path'],'sha256':standards[0]['sha256'],'section':'公平性F','relevant_rule':'保障获取包括弥补用药保障空白、改善可及、短缺供应及防止不合理获取限制；人群名称需有治疗需求未获满足、获取或保障含义。'},{'path':m[1]['source_path'],'sha256':m[1]['sha256'],'paragraph':107,'relevant_rule':'原附录明确保留“未满足的治疗需求”限定。'}],
 'minimal_edit':{'old':'明确治疗需求','new':'明确未满足的治疗需求'},
 'suggested_sentence':'支付保障范围扩展、配备用药限制解除、明确未满足的治疗需求及送药安排按实质内容判读，供应状况资料要求亦可计入。',
 'requires_new_coding_or_statistics':False
}
assert issue['candidate_sentence'] in A[0][107]
assert issue['original_clause'] in A[1][107]
checks=[
 {'item':'A1规则版本','candidate_p':102,'original_p':102,'supplement_p':2,'result':'未发现压缩改变判据','reason':'两个实现版本与共同协议版本完整保留；规则组不等于关键词数、封存不表示检验通过亦保留。删去规则组数量等细节由逐字保存的配套P2和冻结代码承接，不是标准变化。'},
 {'item':'I定义','candidate_p':106,'original_p':106,'supplement_p':6,'result':'未发现压缩改变创新性边界','reason':'一般创新属性、注册分类、知识产权与规则限定研发支持仍是不同依据，I04单列且需核实资格/终止条件及本单元临床优势；没有把所有I限定为突破性治疗或定量优越。仅名称、阶段、程序、新品种、人群不自动命中；三类来源、重大专项身份与实际支持措施的区别、排除纯资格优势时保留其他独立依据均保留。详细属性实例、非自动继承规则见配套P6及共同手册。知识产权仍须按共同澄清§3实质判读，摘要列举不构成任何专利事实一律I=1。'},
 {'item':'F定义','candidate_p':107,'original_p':107,'supplement_p':7,'result':'1处需最小修订','reason':'四子类、公平与可及不是同义、具体供应状态资料可涉及保障、人口名称不自动命中等边界保留；但删除“未满足的”扩大治疗需求表述，见A-F01。'},
 {'item':'语境与计数','candidate_p':108,'original_p':108,'supplement_p':8,'result':'结合明确引用条款未发现改变','reason':'上下文只解释对象和明确引用，不复制其他条目标签；本单元证据、I04另核资格、多标签每维至多一次、部门和文件名不作判据、不补写缺字均保留。材料缺陷/关键语境不足五维待定、未审查与充分区分、待定不填0保留。原段“证据或明确引用”的具体路径仍由本段“明确引用”、未压缩Ec段P105及配套P8共同承接，不据删短语判为取消同源引用。'},
 {'item':'语料与版本','candidate_p':110,'original_p':110,'supplement_p':10,'result':'未发现压缩改变语料或验证身份','reason':'4924/621、119/860、同输入比较及旧版不读取新增字段、各项校验值、首轮600与200仅作开发均保留。621语境不计数在候选P47明确重复，来源条目数和单元边界的完整说明在配套P10；不把重复删除认定为分母变化。'}
]
focused=[
 {'topic':'1/0/待定','paragraphs':[47,53,59,108,111],'result':'三态与不得填0保留。1测量实质关注、0为具备判读条件且未涉及的含义仍受v1.3约束；完整材料的单维概念疑问按共同澄清§1单维待定。原附录本就未全文重述澄清，此次没有将单维概念争议扩大为整条五维待定。'},
 {'topic':'I质性创新与突破资格','paragraphs':[106],'result':'创新属性与I04分列；不要求所有创新内容必须突破或具有量化效果。完整属性示例被移到配套P6，不等于删除。'},
 {'topic':'F公平与可及','paragraphs':[107],'result':'研究映射和非同义边界保留；需恢复治疗需求的“未满足”限定，除此未确认新的含义变化。'},
 {'topic':'上下文不添加别条证据','paragraphs':[46,47,105,108],'result':'对象、条件和明确引用的解释与独立单元标签分开；没有许可从父条款批量继承标签。'},
 {'topic':'AI角色、首次提交、历史LLM未重跑','paragraphs':[111],'result':'候选A2与原A2及配套P11文字完全相同。AI不是真人金标准、D668保留既往上下文、首次提交不按他方改写、来源机关未盲、模型信息不完整、历史外部LLM未按本轮同输入重跑且不进入验证结论全部保留。'}
]
report={
 'status':'bounded_appendix_compression_review_completed','created_at':datetime.now(timezone.utc).isoformat(),
 'identity':{'kind':'AI','name':'V600独立评审A（附录A压缩语义独立核对）'},
 'summary':'五处压缩中确认1处需恢复限定词：候选P107“明确治疗需求”应为“明确未满足的治疗需求”。其余已核关键语义未发现因压缩改变；配套细则逐段完整保留原附录A的14段正文，候选指引标题可定位。',
 'word_snapshots':m,'semantic_standards':standards,
 'locator_definition':'P编号是word/document.xml中w:body直接w:p从0计数，不是Word页码。',
 'scope':{'candidate_appendix_paragraphs':[101,115],'original_appendix_paragraphs':[101,115],'supplement_paragraphs':[0,15],'five_compressed_paragraphs':[102,106,107,108,110],'limited_context_paragraphs':[46,47,49,53,55,56,59],'scope_note':'正文只回看附录涉及的三态、计数、同源引用与AI身份重复说明，未展开全稿审查。手册与共同澄清为同一AI既往使用的冻结版本，仅重读其语义，不读取任何样本或标签。'},
 'checks':checks,'focused_boundaries':focused,'issues':[issue],
 'supplement_preservation':{'original_content_paragraph_count':14,'paragraph_text_correspondence':paragraph_matches,'all_14_paragraph_texts_identical':True,'original_section_heading':'附录A 编码方案技术细节','heading_handling':'原附录标题未作为配套正文段复制；配套使用独立文档标题和导语，此差别不删改14段规则/执行/访谈说明内容。','candidate_guidance_paragraph':102,'guidance_title':'创新药评价研究编码执行细则','supplement_title_paragraph':0,'supplement_title':A[2][0],'title_found_exactly':True,'file_name':'投稿配套-编码执行细则.docx','uncompressed_candidate_appendix_paragraphs_equal_original':all(A[0][p]==A[1][p] for p in range(101,116) if p not in [102,106,107,108,110])},
 'reproducibility_dependency':'配套文件完整保存的是原附录A，不等于已全文收入共同协议及共同澄清。复现仍需具备v1.3、共同执行澄清、同版输入及冻结实现。单维概念待定及知识产权未决边界保留在共同澄清；这属于原已有依赖，不作为本次压缩新增缺陷。',
 'limitations':['未做Word或PDF渲染、分页、版式和超链接点击检查；标题定位仅核对文档实际段落文字。','未重跑代码、重算统计、审读样本标签或核验算法实现符合度；协议一致不等于效度通过。','未扩展全稿、政策来源、参考文献、访谈真实性或投稿条件审查。','只对所存字节快照负责；并行编辑后的不同字节版本不自动继承本次判断。'],
 'actions':{'word_modified':False,'originals_modified':False,'new_coding':False,'statistical_recalculation':False,'rendering_performed':False,'full_manuscript_acceptance':False}
}
md=['# 候选稿附录A压缩：独立核对','',report['summary'],'',
 '本次为AI的有界只读核对。P编号是`word/document.xml`中直接`w:body/w:p`从0计数的位置，不是页码。未做渲染，未作全稿验收。','',
 '## 本次快照','', '| 文件 | SHA256 |','|---|---|']
for x in m:md.append(f"| [{Path(x['source_path']).name}](<{x['source_path']}>) | `{x['sha256']}` |")
md+=['','三份Word于2026-09-26 13:25:57 UTC读取；精确时间、字节快照路径与输出时源文件是否变化见JSON。语义依据为本人既往使用的冻结v1.3及共同澄清，本次完整重读，未读取正式样本或标签。']
for x in standards:md+=['',f"- [{Path(x['source_path']).name}](<{x['source_path']}>)：`{x['sha256']}`。"]
md+=['','## 唯一确认的问题及最小修订','','**候选P107，F定义**：','','> '+issue['candidate_sentence'],'',
 '原稿P107及配套P7写的是“明确未满足的治疗需求”。共同手册F要求保障空白、获取/保障含义或患者负担等依据；一般治疗需求本身并不自动触发F。删去“未满足的”会放宽这项判据，属于实质限定的丢失。','',
 '**最小修订**：将“明确治疗需求”恢复为“明确未满足的治疗需求”。其余句子无须因此重写，也无需新增编码或统计。','','## 五处压缩结论','']
for x in checks:md+=['- **'+x['item']+'（候选P'+str(x['candidate_p'])+'）**：'+x['result']+'。'+x['reason']]
md+=['','## 配套细则与重点边界','','原稿P102—P115的14段正文，与配套P2—P15逐段文字完全一致，顺序未变。候选P102的《创新药评价研究编码执行细则》与配套P0文档标题完全一致；其实际文件名为《投稿配套-编码执行细则.docx》。原附录的区段标题由配套独立标题及导语替代，不影响正文保留。','']
for x in focused:md+=['- **'+x['topic']+'**：'+x['result']]
md+=['',report['reproducibility_dependency'],'','## 未覆盖','']
for x in report['limitations']:md+=['- '+x]
md+=['']
for ext,body in [('json',json.dumps(report,ensure_ascii=False,indent=2)+'\n'),('md','\n'.join(md))]:
 dest=OUT/('候选稿附录A压缩-独立核对.'+ext);assert not dest.exists()
 q=T/(dest.name+'.pending')
 with q.open('x',encoding='utf-8') as f:f.write(body);f.flush();os.fsync(f.fileno())
 os.link(q,dest);q.unlink()
 print(json.dumps({'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},ensure_ascii=False))
print(json.dumps({'changed_sources':[x['source_path'] for x in m if not x['live_source_same_as_snapshot']]},ensure_ascii=False))
