"""Integrate preserved audit phases, explicit analytical addendum, and full bindings."""
from pathlib import Path
import json,hashlib,datetime,collections,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent.parent;O=P/'final130';O.mkdir(exist_ok=False)
def bind(q):
 q=Path(q).resolve();r=q.read_bytes();return dict(path=str(q),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def save(n,x):
 with (O/n).open('x',encoding='utf8') as o:json.dump(x,o,ensure_ascii=False,indent=2);o.write('\n')
first=json.loads((P/'phase01-first40/semantic-reviews40.json').read_text());second=json.loads((P/'phase02-remaining90/semantic-reviews90.json').read_text());reviews=first+second
f=json.loads((P/'readable-disagreement-selection-freeze.json').read_text());pos={(r['id'],r['dimension']):i for i,r in enumerate(f['eligible_all_records'])};assert len(reviews)==130 and len(pos)==130;assert {(r['id'],r['dimension']) for r in reviews}==set(pos)
reviews.sort(key=lambda r:pos[(r['id'],r['dimension'])])
manualpath=B/'03-manual/full4481-common-release-20261010-root/manual.txt';manual=manualpath.read_text();mh=bind(manualpath)
q='过去、完成或未来时态及背景位置均不能单独决定标签。若当前记录明确陈述在某时期设立或实施同一具名安排，并直接连接支持对象或内容，可补该时期同版本的必要定义和直接机制；'
a=manual.index(q);anchor=dict(path=mh['path'],sha256=mh['sha256'],quote=q,line_1based=manual.count('\n',0,a)+1,unicode_interval_half_open=[a,a+len(q)])
r=next(r for r in reviews if r['id']=='RECODE25-02209' and r['dimension']=='I');old=r.copy()
r['phase02_preserved_review_class']=r['review_class'];r['review_class']='更支持LLM';r['error_or_boundary_pattern']='有明确实施与对象联系的历史支持议题';r['reason']='当前明确陈述2019年实施60日默示许可、约50工作日平均用时及直接支持创新研发的作用。共同手册第二节明确过去时和背景位置不能单独排除；此处有具体实施—对象联系，符合I3曾实施的支持议题。不能据此声称今天仍可申请，也不能由年份、沿革或名单状态展开全部待遇。';r['frozen_manual_evidence']=r['frozen_manual_evidence']+[anchor];r['audit_addendum']='phase02原边界判断保留，本次依据同一冻结手册明确时态条作分析修正；机器或真人标签均未改。'
save('audit-analysis-addendum-02209.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),old_phase02_review=old,integrated_review=r,new_source_or_definition_added=False,machine_or_human_labels_modified=False,reason='补齐并严格应用已冻结§2时态规则；不能把历史背景位置作为不成立的充分理由。'))
inputs={}
def reg(x):
 assert bind(x['path'])==x;inputs[x['path']]=x
for x in json.loads((P/'metadata-input-seal.json').read_text())['files']:reg(x)
for x in f['eligible_all_records']:reg(x['packet']);reg(x['native_first'])
reg(mh)
checks=json.loads((P/'remaining90-native-evidence-checks.json').read_text())
for x in checks['asset_bindings']:reg(x)
# Actual necessary table images were read as same-source context, not new selected frame members.
for stem in ['fc1c182e94170d6fec92fd653f299a72bdbd2da2bb44d8f3ef54a0cc092b1d3a','66b6fea46e4f2d5dd69f15cfda8ebed6ae85c620825ee0e2a31ef483c44d51d8','f4224d8488a7adb92882dfd62790668ca8a03aa5cfc4e58a6446d29ef676453a']:
 reg(bind(B/'01-review/context-projection-sol/full-frame-preflight/source-assets'/('SOURCEIMAGE-'+stem+'.jpg')))
source_rows=[json.loads(l) for n in ['selected-semantic-inputs.jsonl','remaining90-semantic-inputs.jsonl'] for l in (P/n).open()];byid={r['id']:r for r in source_rows}
# Add corrected recursive material inventory without replacing earlier top-level counters.
def texts(v,prefix=''):
 if isinstance(v,dict):
  for k,x in v.items():
   p=prefix+'/'+k.replace('~','~0').replace('/','~1')
   if k=='text' and isinstance(x,str):yield p,x
   else:yield from texts(x,p)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from texts(x,prefix+'/'+str(i))
inventory=[]
for sid,r in byid.items():
 sb=r['source_bundle'];ts=list(texts(sb));inventory.append(dict(id=sid,packet=r['packet'],actual_nested_context_N=len(sb['source_record'].get('contexts',[])),recursive_texts=[dict(pointer='/source_bundle'+p,characters=len(t),sha256=hashlib.sha256(t.encode()).hexdigest()) for p,t in ts],care_nested_paragraphs_N=sum(len(x.get('paragraphs',[])) for x in sb.get('source_full_text_resources',[])),explicit_primary_source_texts_N=sum(len(x.get('source_texts',[])) for x in sb.get('explicit_or_primary_source_resources',[]))))
save('corrected-full-packet-reading-inventory.json',dict(unique_selected_packet_N=len(byid),inventory=inventory,initial_top_level_context_or_resource_text_counters_not_complete=True,initial_receipts_preserved=True,source_record_contexts_and_nested_paragraphs_are_actual_locations=True,read_scope='current records and full contexts already contained in allowed selected packets; explicitly cited source paragraphs/pages/table images for binding checks; no excluded standalone frame packet opened'))
save('audit-render-limitations-and-recovery.json',dict(issues=[dict(issue='首18项原样输出含重复来源元数据导致工具输出截断',recovery='以当前句、逐条语境文本及理由分0:8/8:18重新完整呈现'),dict(issue='数据保护01403有无text的结构节点，初次呈现触发KeyError',recovery='33:40所有文本节点及表行单列重读；三幅完整表图逐一查看'),dict(issue='数据保护原资源与元数据长输出截断',recovery='九个源原文段落紧凑完整重读，01402/01382/01403实际引文另列复核'),dict(issue='关爱计划完整资源正文在paragraphs嵌套，不在顶层text；原长输出截断',recovery='140个paragraphs以0:70/70:140全部原文完整呈现，含申请资格所有or支、阶段例外、纳入后节点与回复'),dict(issue='试点完整源文本重复元数据长输出及额外原资源列表截断',recovery='试点完整原文单列一次；NHSA9源正文块完整另读；数据保护原九段前已完整读')],presentation_truncation_not_claimed_as_complete_read_before_recovery=True,not_claiming_observation_of_original_native_model_reading=True))
summary=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_selection=bind(P/'readable-disagreement-selection-freeze.json'),dimension_items_N=130,unique_records_N=len(byid),dimensions=dict(collections.Counter(r['dimension'] for r in reviews)),review_classes=dict(collections.Counter(r['review_class'] for r in reviews)),dimension_classes={d:dict(collections.Counter(r['review_class'] for r in reviews if r['dimension']==d)) for d in ('I','F')},machine_direction_counts={'rule0_native1':124,'rule1_native0':6},boundary_items=[dict(id=r['id'],dimension=r['dimension']) for r in reviews if r['review_class']=='边界待定'],rule_supported_items=[dict(id=r['id'],dimension=r['dimension']) for r in reviews if r['review_class']=='更支持规则'],first40_original_counts={'更支持LLM':38,'边界待定':2},remaining90_original_counts={'更支持LLM':80,'更支持规则':1,'边界待定':9},integrated_addendum_02209_I='boundary to more-support-native, same frozen manual temporal rule; old phase preserved',remaining_or_human200_standalone_packet_body_opened_N=0,human200_workbook_or_answer_body_opened_N=0,diagnostic_excluded_rows='JSON bytes were parsed only to extract selection metadata; their reasons/evidence were not presented or used as semantic evidence',existing_human_reference_00131={'A':0,'B':0,'changed':False,'AI_review':'边界待定'},existing_human77_00529='blocked because source_id belongs to human200; no packet body opened',new_human_adjudication=False,production_inputs_or_labels_modified=False,classification_runs=0,external_model_calls=0,formal_metrics_acceptance=False,not_random_accuracy_sample=True,requested_agent_configuration='gpt-6.1-sol ultra; model service identity not independently probed',evidence_checks={'first40_packet_or_packet_embedded_primary_literal':187,'remaining90_packet_pointer_quotes':306,'remaining90_packet_pointer_failures':0,'remaining90_asset_bindings':11,'remaining90_asset_hash_failures':0,'remaining90_asset_quote_checks':36,'external_literal_or_visual_unconfirmed':3,'unconfirmed_cases':[dict(id=x['id'],dimension=x['dimension'],locator=x['locator'],packet_literal_matches=x['packet_literal_matches'],asset_hash_exact=x['asset_hash_exact']) for x in checks['asset_literal_or_visual_unconfirmed']]})
primary=collections.Counter();titles={}
for x in f['eligible_all_records']:
 d=byid[x['id']]['source_bundle']['source_documents'][0];h=d['source_sha256'];primary[h]+=1;titles[h]=d.get('recorded_frame_document_stems',[])
summary['primary_source_groups']=[dict(source_sha256=h,recorded_stems=titles[h],dimension_items_N=n) for h,n in primary.items()];summary['primary_source_groups_N']=len(primary)
save('summary130.json',summary);save('semantic-reviews130.json',reviews)
md=f'''已完成原冻结130项I/F二元单边阳性分歧的语义诊断，覆盖98条原记录。整合结论为更支持LLM119项、更支持规则1项、边界待定10项、都不充分0项。它是AI依据同一冻结手册与原材料的诊断，不是真人核定，不改变生产或真人标签。

|维度|更支持LLM|更支持规则|边界待定|合计|
|---|---:|---:|---:|---:|
|I|79|0|4|83|
|F|40|1|6|47|
|合计|119|1|10|130|

选择与边界

- 身份链先由原prospective allocation绑定到原800 draw、metadata/exposure registry，核明直接暴露2770+同家族267=3037与remaining1444；再由human200 reception绑定到coordinator draw及assigned-design-metadata，200个source_ids一律排除。00529虽在旧开发77，也属于新200，因此未打开其条款正文。
- 原冻结选择仅I/F的(rule,native)=(0,1)/(1,0)：130项中124项前者、6项后者，原frame顺序保持。8项1/null只保留元数据，不并入二元语义审查。未开发/200诊断行只在元数据解析器中被解析，理由与证据没有呈现或用于审查；不能把“没有打开正文”夸称未解析其JSON字节。
- 原首40项38/0/2已封存；剩90项80/1/9已封存，均保留不改。整合时02209 I由边界改为更支持LLM，单独留下分析补充：同一冻结手册§2明确过去、完成、未来时态和背景位置不能单独决定标签，该句已有2019实施60日机制及创新研发支持的直接关系。没有新材料、定义或机器改码。
- 130项涉及15个原资产SHA组，三程序51项与关爱延伸28项合计79项。单侧分歧选择、相同原文重复/同政策聚集均不能用于全量正确率、部门非零要求或验收κ；也不是独立政策工具数量。

当前承载与泛化的可审查界线

1. 先抽取完整当前命题，必要时与合法直接父谓词组成条件—后果。当前实际要求创新/公平内容信息，不能被“程序阶段/形式审查”一律清空：00818/01337明列“主要创新点”“该创新带来的疗效或安全性方面的优势”，00612明确公示药品公平性内容。只有字段非空、已收件、名单公示或栏目名不成立。
2. 当前实际设立、实施、开放、适用、限制或终止有界安排，才补同版同一安排的定义、对象与直接机制。02235的“对符合要求的创新药临床试验申请，在受理后30个工作日内完成审评审批”及02229明确创新研发资源倾斜自足满足I3。00381/00443/01768有具体工具/AI问题或个性技术问题的反馈路径，不能统称交流形式。若只有电话/视频形式、指南普遍设计规范、常规安全义务或题名创新药，不成立I3。
3. 当前成员只用自身条件和共享父谓词；自身定义及明确条款援引可完整读取，不能倒借兄弟项。01424/01427/01432改良资格直接决定4年保护，支持I4；01430/01435/01436是3类非创新对象不给保护，不能继承1/2类创新待遇。01391其他申请人自行取得数据也不是创新，规则在这些记录泛化了保护持有人的资格。01402则实际执行同一改良持有人受保护临床优势数据的排他权利，限制仿制者不等于称仿制药创新。
4. F必须有可指认治疗需要/缺口与当前针对性机会联系。00106“明确为市场短缺且鼓励研发申报的儿童用药实行优先审评审批”和00655保障不足/空白领域“不限制上市时间”是强证据。00654普通不限定治疗领域不能借下一句保障空白的特别安排；更支持native0。急需、未上市、罕见病或创新词单独不足，单品种取得缺口不能推成全部适应症替代疗法无效。
5. 具名支持计划中的资格分支只为该分支建立关系。关爱材料P025②为境内无获批目标适应症药物，P030以完整资格决定纳入；P007开发讨论和P111/P112纳入后节点/回复是实际资源。实际开放、准予进入或实施这些资源可保存缺口—条件—机会链，FIC与临床优势分支不继承缺口。01482 F更支持规则1，依据当前实际跟踪/研发沟通对接这条同阶段链；LLM称缺少优先服务联系有争点，未将“优先”词出现当必要条件，也未称已改善患者结果。普通汇报、备注填写、通知、申报前机制均不能套用。

需要核定的10项

- 00040 F：当前是相对治疗临床优势不再符合导致终止，能否使用另一无有效治疗分支的缺口对象，存在成员范围与已核明支持撤回的冲突。
- 00105 F：全部现有规格不适合儿童、新规格适合，I2关系明确；是否另构成所需药品取得缺口，还是仅给药便利，材料未明确区分，不将I证据机械复制为F。
- 00130 I/F、00131 F：完成检验/反馈的截止日期是否实质承载同阶段明确优先机制，须区别纯手续。00131的15日前与普通25日前不能单凭数字比较成提速。其固定旧A/B=0保留，本报告只记AI证据争点，不替代真人参照。
- 00246/00247 F：高龄者被试验排除及数据缺失限制治疗，是否已表达患者药品获取机会障碍，还是主要安全证据问题；不能把所有老年研究/试验参与赋F。
- 01386/01387 I：建立/实施具名制度可有限补机制，与仅分派行政职责的门槛尚待核定，不能将所有主管职责扩成研发支持。
- 01403 I：新适应症和原研身份单独不足，完整附表2类改良行又明确本款6年例外；该表内关系是否构成本款自身改良分支，需核定，不把第五条创新兄弟款整体倒灌。

阅读和证据核验

98个选中packet字节绑定全部一致，当前及其source_record.contexts逐条读取。需完整资格或机制时读取已包含在同一packet的三程序完整9612字符、关爱140个段落、试点全方案、医保9个源块、数据保护原段及完整表头/行边界；三幅同源完整表图已查看。嵌套段落和语境计数由新增递归清单补强，原不完整顶层计数文件保留。长工具输出截断和一次非文本节点KeyError均另记，之后紧凑分块补读；不把截断输出直接称实读完成。

首40的187条引用在packet或其中同源原文匹配。剩90的306条packet pointer引用均逐字匹配、0失败；11个外部原资产哈希全部匹配。36条外部引用中3条未独立确认字面抽取：关爱01442/01443的扫描PDF5–6页抽取未命中，但引文在同packet同源转录段逐字匹配；02229的doc额外引文未作原doc字面抽取。其余外部引用按原字面或表图核验。此限制不被改写为模型读过所有源页，也不据字面正确自动判断语义正确；逐项当前直接材料和手册引文均保留在JSON。

使用与下一步

可用于既有开发总体的通用规则错误假设、明确反例及需要人工核定的边界清单。建议分别固定I1信息/I2改良/I3具体服务/I4资格四条路径，避免某一路排除否定其他成立路径；F分支保留缺口类型、当前行动、同版同阶段资源及关系。针对表格兄弟资格误扩散和当前自足机会漏判先准备小型通用反例，再经另行授权与冻结影响集合执行必要局部复算。

不能用本AI诊断直接改真人答案、自动把全部规则0改1、追加LLM语义挑选/重编码、修改冻结手册提示词、接触remaining或200正文、追逐κ门槛或声明正式生产合格。仍需对边界作独立核定并保留原机器首答。没有新分类运行，没有外部模型调用，实际模型服务身份本审计未独立探测。
'''
with (O/'report130.md').open('x',encoding='utf8') as o:o.write(md)
lines=['逐项语义诊断，仅作开发材料审查，不是真人核定。\n']
for r in reviews:
 lines.append(f"\n{r['id']} / {r['dimension']} / 规则{r['machine_values']['rules_v7']}—LLM{r['machine_values']['native_original_whole_batch']} / {r['review_class']}\n\n{r['reason']}\n\n当前逐字材料：\n\n> {r['current_direct_material']['quote']}\n\n手册依据："+'；'.join(f"§来源第{a['line_1based']}行：{a['quote']}" for a in r['frozen_manual_evidence'])+'\n')
with (O/'semantic-reviews130.md').open('x',encoding='utf8') as o:o.write('\n'.join(lines))
# Prior audit artifacts and this exact integration script are input bindings.
for q in P.rglob('*'):
 if q.is_file() and O not in q.parents:reg(bind(q))
save('inputs-hashes.json',dict(N=len(inputs),files=list(inputs.values()),original_and_prior_audit_inputs_unchanged=all(bind(x['path'])==x for x in inputs.values())))
outputs=[bind(q) for q in sorted(O.iterdir()) if q.is_file()]
save('outputs-hashes.json',dict(files=outputs,N=len(outputs)))
save('seal.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs=bind(O/'inputs-hashes.json'),outputs=[bind(q) for q in sorted(O.iterdir()) if q.is_file()],all_inputs_rechecked_unchanged=all(bind(x['path'])==x for x in inputs.values()),production_inputs_or_labels_modified=False,no_new_human_adjudication=True,no_formal_metric_acceptance=True))
print(json.dumps({k:summary[k] for k in ['dimension_items_N','unique_records_N','review_classes','dimension_classes']},ensure_ascii=False));print(json.dumps(bind(O/'seal.json'),ensure_ascii=False))
