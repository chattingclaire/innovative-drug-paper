from pathlib import Path
import json,hashlib,ast,datetime,copy
O=Path(__file__).resolve().parent;R=O.parents[1];A=R/'08-audits/01402-same-version-missing-material-sol';PRE=R/'06-coding/full4481-common-v15-production-preparation-sol';TARGET='RECODE25-01402'
def H(b):return hashlib.sha256(b).hexdigest()
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':H(b)}
def save(p,x):
 with Path(p).open('x')as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
manifest=json.loads((O/'source-extension-manifest-v16.json').read_bytes());proof=json.loads((O/'byte-and-source-interface-proof.json').read_bytes());closure=json.loads((O/'native-original-whole-batch-closure.json').read_bytes());samples=json.loads((O/'human200-stability800-ID-hash-check.json').read_bytes());oldp=json.loads(Path(manifest['base_packet']['path']).read_bytes());newp=json.loads((O/'packets/RECODE25-01402.json').read_bytes());newr=newp['source_bundle']['explicit_or_primary_source_resources'][-1]
# Static parser contract; no module import, RelationView, judge or model invoked.
source_packet=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol/source_packet.py';tr=ast.parse(source_packet.read_text());required=next(ast.literal_eval(x.value)for x in tr.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='BUNDLE_KEYS'for t in x.targets));assert required<=set(newp['source_bundle']) and set(newp)==set(oldp)
assert newp['packet_version']==oldp['packet_version'] and newp['source_id']==oldp['source_id'] and newp['output_id']==oldp['output_id']
assert len(newr['source_texts'])==5 and newr['ordered_article_groups'][0]['ordered_source_resource_ids']==[x['source_resource_id']for x in newr['source_texts'][:4]]
assert all(H(x['text'].encode())==x['text_sha256']for x in newr['source_texts'])
oldlines=Path(manifest['base_common']['path']).read_bytes().splitlines(keepends=True);newlines=(O/'common-frame-bundles-v16.jsonl').read_bytes().splitlines(keepends=True);assert len(oldlines)==len(newlines)==4481 and [i for i,(a,b)in enumerate(zip(oldlines,newlines),1)if a!=b]==[1402]
for k in ['human200','stability800']:
 assert not samples[k]['material_changed_record_ids'] and not samples[k]['native_batch_closure_intersection_record_ids']
 assert all(x['common_line_byte_same']and x['packet_binding_same']for x in samples[k]['records'])
# Verify sealed input metadata & immutable former candidates by exact byte hash.
source_seal=json.loads((A/'output-seal.json').read_bytes())
for x in source_seal['files']:assert bind(x['path'])==x
v9seal=R/'08-audits/v9-generic-relationship-repair-design-sol/final-candidate-delivery-20261012-sol/output-seal.json';v10seal=R/'08-audits/v10-generic-relationship-repair-sol/output-seal.json'
for p in [v9seal,v10seal]:
 j=json.loads(p.read_bytes())
 for x in j['files']:
  if Path(x['path']).name in ['evidence.py','source_packet.py','source_receipts.py','relations.py','dimensions.py'] and '/code-snapshot/' not in x['path']:assert bind(x['path'])==x
inputs=[A/'necessary-material-addendum.json',A/'output-seal.json',PRE/'input-bindings.json',PRE/'packet-bindings.json',PRE/'frame-order.json',PRE/'batch-plan.json',Path(manifest['base_common']['path']),Path(manifest['base_source_seal']['path']),PRE/'packets/RECODE25-01402.json',R/'01-review/source-interface-v15-price-context-sol/frame-bundle-bindings-v15.jsonl',Path(manifest['source_snapshot_binding']['path']),Path(manifest['source_original_binding']['path']),Path(manifest['source_original_HTML_binding']['path']),Path(closure['selected_original_whole_manifest_binding']['path']),R/'09-delivery/human200-independent-preparation-root/workbook-manifest.json',Path(samples['human200']['draw_binding']['path']),R/'06-coding/current-freeze-stability800-v1-root/run-manifest.json',Path(samples['stability800']['ordered_source_ids_binding']['path']),v9seal,v10seal,R/'03-manual/full4481-common-release-20261010-root/manual.txt',R/'03-manual/full4481-common-release-20261010-root/execution-prompt.txt',R/'03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt',source_packet]
save(O/'input-seal.json',{'files':[bind(p)for p in inputs],'scope':'01402 material and mechanical identity/hash transport only; other source bodies and predictions not semantically reviewed','source_only_no_classification_or_model':True,'original_v9_v10_five_modules_match_seals':True,'former_manual_prompt_protocol_unchanged':True,'actual_calls':{'classifier':0,'model':0}})
save(O/'material-change-list.json',{'changed_source_ids':[TARGET],'changed_common_line_ordinals_1based':[1402],'allowed_target_bundle_changes':[{'pointer':'/explicit_or_primary_source_resources/1','change':'append one same-source complete original article6 resource document with original four paragraphs plus next-header-only resource'},{'pointer':'/source_bundle_extension/v16_finite_article6_same_version','change':'add neutral material version and byte/source bindings'}],'current_source_record_and_all_contexts_changed':False,'other_bundle_fields_changed':False,'old_explicit_resources_prefix_changed':False,'original_source_SHA_or_version_changed':False,'old_common_line_and_packet_immutable':True,'physically_produced_packet_ids':[TARGET],'old_packet_bindings_reused_N':4480,'rule_followup_material_scope':[TARGET],'native_followup_context_unit':'original complete batch-0216','native_followup_members':['RECODE25-01402','RECODE25-01403','RECODE25-01404'],'new_core_prompt_constructed':False,'adoption_or_execution_authorized_by_this_preparation':False,'no_dimension_value_or_expected_conclusion':True})
save(O/'source-interface-static-check.json',{'original_source_packet_module_binding':bind(source_packet),'verification_method':'AST BUNDLE_KEYS literal + JSON schema-key/identity/source/group/byte invariants only, module not imported or run','native_packet_keys_exact_same':True,'native_packet_version_exact_same':'native-full-source-3','common_source_bundle_base_identity_exact_same':True,'bundle_required_source_fields_present':True,'source_texts_exact_N':5,'complete_article6_original_paragraph_N':4,'next_header_only_N':1,'ordered_group_members_are_exact_unique_continuous_original_paragraphs':True,'all_original_text_sha256_verified':True,'source_original_and_snapshot_source_version_identity_proved':True,'new_packet_canonical_bundle_SHA_verified':True,'models_executed':0,'classifiers_executed':0,'source_parser_executed':False,'all_consumption_read_use_status':'not_recorded'})
report='''已准备独立 source-interface v16 材料版本，状态为等待 ROOT 审查及另行采用；没有新生产 GO，分类器和模型执行均为0。

原冻结 01402 可读包的第六条完整投影缺首二段。本版本把同一原始 JSON/HTML 源中的第六条四段逐字、连续加入独立 explicit_or_primary_source_resources 文档，使用 source_texts 和 ordered_article_groups 接口；第七条只保存原印刷标题“第七条”作为闭合边界，没有提供下一条实质正文。每段保留原源 SHA、source_version_id、JSON pointer、JSON 字符/字节位置、HTML p序号、HTML字符/字节位置及逐字文本hash。未添加 expected、编码结论或维度特征。

原源 JSON SHA：09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06；原 HTML SHA：e0e9f205f2ba8bdd245da3ebeee78fe68f86b3c7d791b23585ff59acab9ba88b。原 JSON asset 与冻结 snapshot 字节相同；第六条 /normative_paragraphs/13—16，HTML p27—30。四段的原始 visible text 无规范化；下一条仅 /normative_paragraphs/17 的三字头和 HTML p31 的同三字头，有精确范围定位。

新 common-frame-bundles-v16.jsonl 保留4481原顺序，仅第1402行改变；其他4480行包含行末换行逐字节相同。frame-bundle-bindings-v16.jsonl 也只替换01402一行。仅物理生成新01402 packet；packet-bindings-v16.json 的其他4480项精确保留原路径、bytes、SHA及bundle SHA，不伪称重新生产全部packets。full4481-material-correspondence.json 列出全部4481旧→新行hash与包绑定，均可机械核验。

当前01402原文、contexts、既有资源、原source documents/locator/index/provenance及原 common_source_bundle_version 均不变。新增变化只限 /explicit_or_primary_source_resources/1 和 /source_bundle_extension/v16_finite_article6_same_version。新packet仍沿原 native-full-source-3键集合与格式，bundle SHA按原 UTF8 canonical JSON（ensure_ascii=False、sort_keys=True、紧凑分隔、allow_nan=False、无尾换行）计算。source-interface-static-check.json 只核源码AST和数据不变量，没有调用source parser、classifier或模型。

规则后续材料重算单位为01402单记录。native原whole-manifest机械闭包仍是batch-0216：01402、01403、01404三成员及原顺序；后两条只核原包路径/hash，未语义阅读。native-original-whole-batch-closure.json 给出原批次及选定whole快照元数据、新旧三包binding；新sum packet bytes=223991，小于原packet limit=260000。未构造完整新prompt/core，不能据packet sum宣称其token或full core预算已通过。没有建立或修改原run、selection、receiver、结果及stability文件。

human200和stability800抽样均无01402，也无batch-0216三成员。ID/hash检查逐项确认原human200的200行/包与原stability800的800行/包保持byte/hash相同；未改变抽样ID、权重或人工材料。完整核对表在human200-stability800-ID-hash-check.json；人工正文、答案和机器判断未被读取。

本轮发现阶段有一次元数据输出错误：将stability800 sample-metadata的list当keys打印，附带了抽样stratum元数据。未打开正文、模型结果或human答案，也未把这些字段用于材料构造或选择，已向ROOT说明；后续只使用ordered-source-ids白名单。read-scope-log.json如实记录该事件，不复制stratum值。材料包保持源文中立，此准备不授予任何维度判断。

所有旧冻结文件、手册、prompt、v9/v10候选均未修改。材料差异与代码修订分开保存；ROOT审核后才能单独采用本版本，并另行安排规则单记录及native完整原批次执行。
'''
(O/'report.md').write_text(report)
required=['source-extension-manifest-v16.json','common-frame-bundles-v16.jsonl','frame-bundle-bindings-v16.jsonl','packet-bindings-v16.json','packets/RECODE25-01402.json','source-library/article6-original-complete-with-next-boundary.json','input-seal.json','byte-and-source-interface-proof.json','source-interface-static-check.json','material-change-list.json','full4481-material-correspondence.json','native-original-whole-batch-closure.json','human200-stability800-ID-hash-check.json','read-scope-log.json','report.md']
files=[bind(p)for p in sorted(O.rglob('*'))if p.is_file()]
seal={'schema':'source-interface-v16-article6-neutral-material-preparation-total-seal-v1','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mandatory_members':[str((O/p).resolve())for p in required],'files':files,'self_excluded':True,'state':'prepared_not_adopted_not_executed','new_production_GO':False,'model_calls':0,'classifier_calls':0,'source_only_material_delta_no_I_conclusion':True,'old_freeze_unchanged':True};save(O/'output-seal.json',seal)
for x in files:assert bind(x['path'])==x
assert set(seal['mandatory_members'])<=set(x['path']for x in files)
print(json.dumps({'total_seal':bind(O/'output-seal.json'),'files_N':len(files),'mandatory_N':len(required),'new_common':bind(O/'common-frame-bundles-v16.jsonl'),'new_packet':bind(O/'packets/RECODE25-01402.json'),'new_bundle_sha256':newp['source_bundle_sha256'],'other_common_byte_same_N':4480,'reused_packet_bindings_N':4480,'human200_changed_N':0,'stability800_changed_N':0,'classifier_calls':0,'model_calls':0},ensure_ascii=False,indent=2))
