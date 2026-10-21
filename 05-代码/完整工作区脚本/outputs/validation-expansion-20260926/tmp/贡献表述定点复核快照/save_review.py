from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,os
out=Path('/PROJECT_ROOT/outputs/validation-expansion-20260926')
tmp=out/'tmp/贡献表述定点复核快照'
m=json.loads((tmp/'manifest.json').read_text())
a={x['paragraph_index_zero_based']:x['text'] for x in json.loads((tmp/'word-paragraphs.json').read_text())}
for x in m:
 assert hashlib.sha256(Path(x['snapshot_path']).read_bytes()).hexdigest()==x['sha256']
 x['live_source_sha256_at_report_write']=hashlib.sha256(Path(x['source_path']).read_bytes()).hexdigest()
 x['live_source_same_as_reviewed_snapshot']=x['live_source_sha256_at_report_write']==x['sha256']
issue={
 'id':'C01','severity':'需要修订执行范围表述','document':'manuscript','paragraph_index_zero_based':39,'paragraph_locator':'word/document.xml中w:body的直接w:p，自0计数；不是Word页码',
 'section':'3.2 三种制度逻辑的操作化，分析框架收束句',
 'exact_original_sentence':a[39],
 'problematic_span':'并通过不同统计口径检查文件类型、时期和样本构成对结果的影响',
 'judgment':'该句把文件类型、时期和样本构成的影响检查写为本文已实施的组成部分；现交付D668说明能支持的是五项操作定义边界的描述性敏感性，并明确未检验年份效应。它也不能证明这些替代解释已经被排除。问题是研究设计承诺与实际执行证据范围不一致，不是对已冻结数值提出异议。',
 'existing_evidence':[
  {'path':m[2]['source_path'],'sha256':m[2]['sha256'],'line_start':76,'line_end':101,'locator':'五项描述性敏感性的影响','supports':'五情景均为操作定义边界变化；无新置信区间、P值或比较方向，不能写成稳健性全部通过。'},
  {'path':m[2]['source_path'],'sha256':m[2]['sha256'],'line_start':113,'line_end':113,'locator':'不改变分母与分析对象','supports':'明确说明本阶段没有检验年份效应。'},
  {'path':m[0]['source_path'],'sha256':m[0]['sha256'],'paragraph_index_zero_based':74,'supports':'主稿自己仅报告五项操作定义情景的描述性变化。'},
  {'path':m[0]['source_path'],'sha256':m[0]['sha256'],'paragraph_index_zero_based':82,'supports':'主稿将文件类型、时间分布和测量框架列为需要考虑的替代解释，而非已经排除的解释。'}
 ],
 'recommended_replacement':'据此，本文以文本编码比较五维关注分布，结合条文与访谈解释评价标准及决策用途，并以判读前另行登记的五项操作定义边界情景描述编码口径对点估计的影响。文件类型、时期和样本构成可能带来的影响仍作为解释限制，不据上述情景认定这些影响已被排除。',
 'new_analysis_required':False,
 'caveat':'若作者另有与当前冻结版本一致、已交付的文件类型或时期分析，应另行准确引用其结果；本次未发现于指定证据说明中，也不追加分析寻找。'
}
assert issue['problematic_span'] in a[39]
checks=[
 {'risk':'把点估计写成稳健排序或把未支持写成部门等价','paragraphs':[3,65,68,73,98,100,172],'judgment':'所查段落未发现该越界。正文明确30项共同方向未支持、点估计不是共同稳健排名，也不等于部门相同；P73说明未检验组内维度排序。','evidence_paths':[m[2]['source_path']],'evidence_locator':'D668边界说明L3、L60—72、L109—112'},
 {'risk':'把文本频次或阳性比例直接写成实际赋权、偏好或制度逻辑因果效应','paragraphs':[11,22,28,29,47,73,75,80,82,99,100],'judgment':'所查段落未发现该越界。文本比例和实际评审权重已明确分开，制度逻辑仅为解释视角，未声称识别因果影响。','evidence_paths':[m[2]['source_path'],m[3]['source_path']],'evidence_locator':'D668边界说明L13、L52、L113；矩阵L3—5、L97、L107'},
 {'risk':'把框架比较写成首次发现、完整领域缺口或已经证明原创性','paragraphs':[12,20,22,77,78,80,84,88,93,96,98,99],'judgment':'所查段落未使用首次或领域空白结论。贡献表述限于区分关注分布和维度内内容、在中国情境中对照评价用途与衔接条件；实践内容写为建议，不是已验证有效的干预。','evidence_paths':[m[1]['source_path'],m[3]['source_path']],'evidence_locator':'创新点备忘录首段、可检验的贡献候选、与原论文结构的衔接；矩阵共同点及解释边界','boundary':'可追溯比较可以作为贡献候选的实际工作内容，仍不能据本次定向复核认定可发表原创性或穷尽领域研究。'},
 {'risk':'把AI一致性说成人工金标准或内容效度已经通过','paragraphs':[3,49,53,54,55,100,111,172],'judgment':'所查段落未发现该越界。正文明确AI按人工流程执行但不是真人编码基准，高一致性不能证明词典准确，操作定义敏感性不是专家内容效度评分；当前创新点备忘录要求的人工验证仍不能由这两份AI编码替代。','evidence_paths':[m[2]['source_path'],m[1]['source_path']],'evidence_locator':'D668边界说明L101、L107、L111、L114；创新点备忘录贡献候选第1项'},
 {'risk':'把条文用途比较扩大为完整部门偏好或各部门互斥属性','paragraphs':[31,55,77,78,80,83,84,88,98,99,100],'judgment':'所查段落保留共同关注、比较内容与用途的区别，以及五维覆盖限制。证据矩阵本身是探索性条文锚点，未覆盖格保留不足；当前结论没有用其直接报告稳定的子类型比例或部门完整偏好。','evidence_paths':[m[3]['source_path'],m[1]['source_path']],'evidence_locator':'矩阵L3—5、L87—91、L103—115、L141—159、L175—190；创新点备忘录贡献候选2及末段'}
]
report={
 'status':'targeted_contribution_language_review_completed','created_at':datetime.now(timezone.utc).isoformat(),
 'identity':{'kind':'AI','name':'V600独立评审A（贡献与创新表述定点复核）'},
 'overall_judgment':'所查核心表述已避免四类重点越界；确认1处执行范围表述需收窄（P39）。没有据此宣称全文通过、效度通过或创新性成立。',
 'sources':m,
 'scope':{'manuscript_paragraph_locator':'zero-based direct w:body/w:p index; not page number','research_questions_and_positioning':[10,11,12,20,22],'theory_and_operational_claims':[25,26,27,28,29,31,39],'interpretation_discussion_and_recommendations':list(range(73,101)),'abstracts':[3,172],'supporting_boundary_paragraphs':[43,47,49,50,53,54,55,56,59,61,62,65,68,72,108,109,110,111,112,113,114,115],'memo':'完整阅读指定创新点备忘录与D668结果边界说明；读取已有证据矩阵作用途比较定位。'},
 'issues':[issue],
 'checks_without_confirmed_overclaim':checks,
 'uncovered_items':['未重新核验理论或政策原始文献，也未开展查新或外部检索。','未重新编码、审读编码标签或运行统计；统计事实仅对照指定的既有结果边界说明。','未复核访谈原始转录、参与者授权及访谈样本记录，因此不能验收访谈事实或充分性。','未检查Word表格、嵌入图、排版、修订历史、批注、页眉页脚或文献格式；这不是全文验收。','本报告绑定读取时的字节快照。主稿负责人可能并行改稿，未读取后续不同哈希正文进行再验收。','未认定创新性已证明、框架内容效度已通过或论文已达投稿条件。'],
 'actions':{'word_modified':False,'prior_reference_review_files_modified':False,'labels_or_statistics_modified':False,'new_coding':False,'new_statistical_analysis':False,'external_search':False},
 'checks':{'issue_quote_matches_snapshot':True,'snapshots_rehashed':True,'confirmed_issue_count':1}
}
md=['# D668：贡献与创新表述定点复核','',report['overall_judgment'],'',
 '本次为AI执行的表述—既有证据对照；未改Word，未重新编码、统计或检索文献。段落P编号是`word/document.xml`内直接`w:body/w:p`从0计数的位置，不是页码。','',
 '## 读取快照','',
 '| 文件 | SHA256 | 读取时间（UTC） |','|---|---|---|']
for x in m:
 md.append(f"| [{Path(x['source_path']).name}](<{x['source_path']}>) | `{x['sha256']}` | {x['captured_at']} |")
md+=['','原始字节快照另存在JSON所列路径。输出时是否仍与源文件相同亦逐件记录；后续改稿不在本次判断内。','','## 一处需要修订','',
 '**P39，3.2节分析框架收束句**：','', '> '+issue['exact_original_sentence'],'',issue['judgment'],'',
 f"依据：[D668结果边界说明](<{m[2]['source_path']}>)第76—101行仅列五项定义边界描述性情景，第113行明确没有年份效应检验；主稿P74也只报告操作定义情景，P82仍将文件类型、时间分布列为替代解释。",'',
 '**建议替换**：','', '> '+issue['recommended_replacement'],'',
 '这项修改无需新增分析。若另有当前版本的文件类型或时期分析，应准确补引；不能用五项定义情景代替这类证据。','','## 已检查但未发现上述越界的范围','']
for x in checks:
 md+=['- **'+x['risk']+'**（P'+ '、P'.join(map(str,x['paragraphs']))+'）：'+x['judgment']]
md+=['','创新点备忘录本身明确“定向初筛、不是系统综述、不能写首次或尚无研究”。其贡献候选仍是候选；目前的条文矩阵能支持具体用途比较，不能证明完整部门偏好、已通过人工效度验证或可发表原创性。','','## 未覆盖','']
for u in report['uncovered_items']:md+=['- '+u]
md+=['']
for suffix,content in [('json',json.dumps(report,ensure_ascii=False,indent=2)+'\n'),('md','\n'.join(md))]:
 dest=out/('D668-贡献与创新表述定点复核.'+suffix)
 assert not dest.exists(),f'拒绝覆盖已有文件 {dest}'
 p=tmp/(dest.name+'.pending')
 with p.open('x',encoding='utf-8') as f:f.write(content);f.flush();os.fsync(f.fileno())
 os.link(p,dest);p.unlink()
 print(json.dumps({'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},ensure_ascii=False))
print(json.dumps({'source_changed_since_snapshot':[x['source_path'] for x in m if not x['live_source_same_as_reviewed_snapshot']]},ensure_ascii=False))
