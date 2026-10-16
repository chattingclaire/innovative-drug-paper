from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,difflib,copy,re
P=Path(__file__).resolve().parent;G=P.parents[3];DIMS=('S','E','Ec','I','F');NAMES=('evidence','source_packet','source_receipts','relations','dimensions')
def read(p):return json.loads(Path(p).read_bytes())
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 p=Path(p)
 if p.exists():
  assert read(p)==x, 'Do not replace a different preserved artifact: '+str(p)
  return
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def labels(r):return {d:r['decisions'][d]['value'] for d in DIMS} if 'decisions' in r else {'geometry_only':r.get('actual_programme_span')}
# Copy final material byte-for-byte; prior attempts remain immutable.
snap=P/'after-code-snapshot';snap.mkdir(exist_ok=True)
for name in NAMES+('regression_tests','parent235_runner','development_runner','relation_controls'):(snap/(name+'.py')).write_bytes((P/(name+'.py')).read_bytes())
code_diff=[]
for name in NAMES:
 a=P/'before-code-snapshot'/(name+'.py');b=P/(name+'.py');change=bind(a)['sha256']!=bind(b)['sha256']
 code_diff.append({'module':name,'before':bind(a),'after':bind(b),'changed':change})
 if change:
  (P/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=str(a),tofile=str(b))),encoding='utf8')
old=read(P/'before-edit-development/records77.json');new=read(P/'final-development/records77.json');assert [r['id'] for r in old]==[r['id'] for r in new]
changes=[{'id':a['id'],'dimension':d,'old':a['labels'][d],'new':b['labels'][d],'current_text':b['text'],'final_decision':b['decisions'][d]} for a,b in zip(old,new) for d in DIMS if a['labels'][d]!=b['labels'][d]]
assert len(changes)==9
save(P/'old-new-label-differences.json',{'total_label_slots':385,'changed_label_slots':len(changes),'unchanged_label_slots':385-len(changes),'changes':changes})
comparisons={}
for kind,oldfile,newfile in [('original75','before-edit-original75/results.json','final-original75/results.json'),('parent235','before-edit-parent235/results.json','final-parent235/results.json'),('counterpairs18','before-edit-development/counterpairs.json','final-development/counterpairs.json')]:
 a=read(P/oldfile);b=read(P/newfile);assert len(a)==len(b)
 fields=[]
 for i,(x,y) in enumerate(zip(a,b)):
  assert x.get('name',x.get('case'))==y.get('name',y.get('case'))
  if labels(x)!=labels(y):fields.append({'index':i,'name':x.get('name',x.get('case')),'old':labels(x),'new':labels(y)})
 newfails=[{'index':i,'name':y.get('name',y.get('case'))} for i,(x,y) in enumerate(zip(a,b)) if x.get('passed') and not y.get('passed')]
 comparisons[kind]={'N':len(a),'old_pass_N':sum(bool(x.get('passed')) for x in a),'new_pass_N':sum(bool(x.get('passed')) for x in b),'new_failures':newfails,'all_five_dimension_changes':fields,'unchanged_all_five_values':not fields}
assert comparisons['parent235']['unchanged_all_five_values'] and not any(v['new_failures'] for v in comparisons.values())
save(P/'regression-before-after-comparison.json',comparisons)
# Reuse the independently hashed earlier frozen-input inventory, taken before
# this repair. It covers A/B, all77 original packets and prior machine outputs.
audit=G/'08-audits/current77-arithmetic-independent-20261011-sol/input-bindings.json';frozen=read(audit)['members'];checked=[]
for x in frozen:
 now=bind(x['path']);checked.append({'path':x['path'],'expected_sha256':x['sha256'],'actual_sha256':now['sha256'],'unchanged':now['sha256']==x['sha256']})
initial=read(P/'initial-snapshot.json');originalcode=[]
for x in initial['copied_original_modules_and_runners']:
 now=bind(x['path']);originalcode.append({'path':x['path'],'expected_sha256':x['sha256'],'actual_sha256':now['sha256'],'unchanged':now['sha256']==x['sha256']})
manual=bind(G/'03-manual/full4481-common-release-20261010-root/manual.txt');assert manual['sha256']=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
assert all(x['unchanged'] for x in checked+originalcode)
protected={'earlier_inventory':bind(audit),'unchanged_prior_inventory_N':len(checked),'changed_prior_inventory_N':sum(not x['unchanged'] for x in checked),'prior_inventory_readback':checked,'original_v6_code_readback':originalcode,'manual':manual,'manual_identity_check':'matches previously frozen full SHA256','writes_confined_to_owned_v7_directory':True,'parent_statistics_and_progress_not_modified_by_this_task':True}
save(P/'protected-input-readback.json',protected)
source_findings={'necessary_source_missing_in_original_target_packets':[], '01423':{'status':'necessary original source material exists; structural consumption repaired', 'packet':bind(G/'06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-01423.json'), 'base_current_row':'/source_bundle/source_record/text', 'base_definition':'/source_bundle/explicit_or_primary_source_resources/0/ordered_article_groups; article3 appendix bridge, article5 exact foreign original-drug6-year treatment and in-article scope definition', 'exception_article7_container':'/source_bundle/source_record/contexts/12', 'exception_article7_members':'/source_bundle/source_record/contexts/13 and /14', 'exception_article7_actual_next_boundary':'/source_bundle/source_record/contexts/15; boundary container16 p0022–p0023→p0024', 'exception_article6_container':'/source_bundle/source_record/contexts/17', 'exception_article6_members':'/source_bundle/source_record/contexts/18–21', 'exception_article6_actual_next_boundary':'/source_bundle/source_record/contexts/22; boundary container23 p0018–p0021→p0022', 'next_candidate_field_is_not_alone_proof':True, 'finite_reference_depth':2, 'next_boundary_not_consumed_as_content':True,'independent_base_SE_survives_exception_missing':True},'definition_boundaries_retained':[{'id':r['id'],'dimension':'F','value':r['labels']['F'],'needed_material':r['decisions']['F'].get('needed_material'),'reason':r['decisions']['F']['reason']} for r in new if r['id'] in ('RECODE25-00110','RECODE25-00118')]}
save(P/'source-material-findings.json',source_findings)
controls=read(P/'final-controls/summary.json');before=read(P/'before-edit-controls/summary.json');old235=read(P/'before-edit-parent235/summary.json');new235=read(P/'final-parent235/summary.json');summary=read(P/'final-development/summary.json')
report={'at_utc':datetime.now(timezone.utc).isoformat(),'identity':'disclosed finite development relation repair; not formal validation or population evidence','model_requested':'gpt-6.1-sol ultra (inherited requested setting)','source_directory':str(P.parent/'joint-v6-direct-content-root'),'delivery_directory':str(P),'scope':'five specified relation errors plus four nulls at original table row; no full4481 or800 reclassification','manual_and_source_unchanged':True,'classifier_features_exclude_current_record_id_human_LLM_reference_metric_target':True,'expected_values_outside_semantic_classifier_input':True,'code':code_diff,'changed_label_slots':9,'unchanged_label_slots':376,'differences_artifact':bind(P/'old-new-label-differences.json'),'final_controls':controls,'regression_comparison':comparisons,'parent235_existing_failures_retained':new235['failed'],'current77_remaining_mismatches_including_null':summary['mismatches_including_null'],'current77_coverage':{'rows':77,'total_label_slots':385,'numeric_slots':383,'unresolved_slots':2,'numeric_slot_fraction':383/385,'complete_rows':75,'complete_row_fraction':75/77,'denominators_by_dimension':{d:summary['metrics'][d]['N'] for d in DIMS}},'current77_development_metrics_only':summary['metrics'],'formal_validation_complete':False,'population_confidence_intervals_calculated':False,'target_kappa_used_for_classification':False,'native_recovery35_process_compliance_guaranteed_by_arithmetic':False,'process_limit':'Current77 arithmetic and development relation checks condition on the delivered sources and numeric labels; they cannot establish recovery35 process compliance, blinding, or a formal validation sample.','missing_original_source_check':source_findings,'preserved_failures_and_fixture_correction':{'before_edit_controls':before,'attempt01':read(P/'attempt01-controls/summary.json'),'attempt02_original_fixture':read(P/'attempt02-controls/summary.json'),'attempt02_corrected_fixture':read(P/'attempt02-corrected-controls/summary.json'),'fixture_correction':{k:v for k,v in read(P/'relation-controls-corrected-fixed-before-third-edit.json').items() if k!='cases'},'original_expected_table_values_changed':False,'original_fixture_and_results_preserved':True},'protected_inputs':{'unchanged_prior_inventory_N':len(checked),'v6_original_code_unchanged_N':len(originalcode),'manual_sha256':manual['sha256'],'protected_input_artifact':bind(P/'protected-input-readback.json')},'classifier_filesystem_access_attempts':{'new22':controls['filesystem_access_attempts_during_classification'],'parent235':new235['filesystem_access_attempts_during_classification']},'execution':{'controls':'python3 relation_controls.py <new-output-name> relation-controls-corrected-fixed-before-third-edit.json','original75':'python3 regression_tests.py <new-output-name>','parent235':'python3 parent235_runner.py --suite 235 --out <new-output-name>','development77and18':'python3 development_runner.py joint-v7-relation-content-sol <new-output-name>'}}
save(P/'delivery-report.json',report)
rows='\n'.join(f"| {c['id'].removeprefix('RECODE25-')} | {c['dimension']} | {'null' if c['old'] is None else c['old']} | {c['new']} |" for c in changes)
md=f'''本次已完成指定五类通用关系修复，交付在独占 v7 目录。相对 v6，77 条的385个维度位置只变化9个，其余376个保持；00110、00118 的 F 继续为 null。Ec 指经济性，I 指创新性。\n\n| 记录 | 维度 | v6 | v7 |\n|---|---|---:|---:|\n{rows}\n\n通用修复机制如下：\n\n- 操作性“明显临床优势”的申请条件消费同版完整定义。安全性优势只能来自该完整定义中的实际分支；标题、下一界、重复当前命题只作证明。初轮重复当前引用与身份引用重叠曾引出 Ec null，保留该真实失败，最终排除重叠重复捐献后恢复 Ec=0。\n- 当前明确为仿制药分支时，同程序的混合创新对象不能供给 I；供药缺口及其实际服务仍可供给 F。明确创新研发服务控制仍保留 I。\n- 完整列表入口接受“满足条件纳入范围”和“申请品种需同时满足以下条件”。成员、原次序、同源首末及真实下一界仍须闭合；纯宗旨不能打开列表。\n- 支付范围成员直接补足同源父句“须申报后方可调整”的省略宾语，形成申报—方可调整支付范围的后果；普通申报身份或异版父句仍排除。\n- 数据保护表行的基础6年与条件例外4年分别读取。基础仅消费第三条附表桥及第五条同对象/同期限/明确条内数据范围；例外仅按7.2→6的有限链消费数据范围及许可后果。核验完整款次、原次序、真实下一条边界后才开放 SE，不使用下一界文字供给标签。\n\n01423 在原 v15 包中不缺必要原文。第七条两款、后续第八条首界、第六条四款及后续第七条首界均已供给；修复的是结构入口和兼容的下一界字段，不能把 `next_candidate_paragraph_id` 声明单独当成完整证明。删除第六条、删除第六/七条真实下一界、改为异版第六条或重排第七条后，独立基础 S/E 保留1，例外未解的 Ec/F 保留 null。具体 JSON 指针见 source-material-findings.json。\n\n最终新关系控制22/22、原18正反例18/18、原75回归75/75通过。235条保持227/235，8个既有失败原样保留；235条全部五维值也与改前相同，没有新增失败。既有失败及每次代码快照、输入、实际结果均保存。\n\n首轮有三项反例输入构造错误：第六条容器的地址也写有“第七条”，旧构造器优先按“七”识别，三项预定删除/改源操作因此为空变异。原22项文件和失败结果不改；修正文件按实际第一原文成员的条标题选组，表行预期完全不变，并在第三轮代码编辑前固定。修正后控制另外增加00005/Ec=0以捕捉引用重叠产生的误null。见 relation-controls-corrected-fixed-before-third-edit.json 和各 attempt 目录。\n\n这组77条已用于定位与修复，只能作公开的开发诊断。S/E/Ec/I 的数值分母各77，F为75；覆盖383/385，完整行75/77。数值位置的κ/P/R/F1/Po在本次均为1，这不证明总体性能、独立验证或定义边界已解决，也不是修复的目标。00110/00118的名单内所需产品境内取得缺口涉及 F 的定义边界，按任务继续保持 null，留给统一裁决。\n\n938份此前已封印输入及7份原v6源码/runner逐字节哈希未变；冻结手册哈希亦保持。原packet、A/B、既有预测、统计及progress未由本任务修改。分类模块不读取真人/LLM值、样本ID或κ目标；新22例及235回放的分类期禁止文件访问，访问尝试均为0。\n\n算术只在给定材料、数字标签和分母下成立，不能保证补跑35的流程合规、盲法或正式验证身份。\n\n可运行源码为目录顶部五模块，改前/后快照分别在 before-code-snapshot 和 after-code-snapshot；relations.diff、dimensions.diff提供完整逐行差异。每次复跑须使用新的输出目录名，命令见 delivery-report.json。最终 seal.json 列出本目录所有交付文件的 SHA256，自身不纳入自身封印。\n'''
(P/'delivery-report.md').write_text(md,encoding='utf8')
# A seal is produced only after every report has been written.
files=[bind(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='seal.json']
# Nested run seals are themselves part of this delivery, even though root self
# seal alone is excluded.
files=[bind(p) for p in sorted(P.rglob('*')) if p.is_file() and p!=P/'seal.json']
save(P/'seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'identity':'owned v7 complete delivery and preserved actual attempts','self_excluded':True,'files':files})
sealed=read(P/'seal.json');assert all(bind(x['path'])['sha256']==x['sha256'] for x in sealed['files']);print(json.dumps({'files_N':len(files),'seal':bind(P/'seal.json'),'report':bind(P/'delivery-report.json'),'changes':[(x['id'],x['dimension'],x['old'],x['new']) for x in changes],'frozen_prior_inputs_unchanged_N':len(checked),'original_v6_code_unchanged_N':len(originalcode)},ensure_ascii=False,indent=2))
