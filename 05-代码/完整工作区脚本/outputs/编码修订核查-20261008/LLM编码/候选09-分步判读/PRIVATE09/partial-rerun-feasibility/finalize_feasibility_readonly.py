"""Summarize a completed metadata scan; no model, labels, source edits or sampling."""
import collections
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,obj):
 with(OUT/name).open('x')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main():
 report_path=OUT/'partial_scope_feasibility_METADATA_ONLY.json'
 r=json.loads(report_path.read_text())
 pp=Path(r['all4924_row_provenance']['path'])
 assert sha(pp)==r['all4924_row_provenance']['sha256']
 rows=[json.loads(s)for s in pp.read_text().splitlines()if s.strip()]
 checks={}
 checks['rows4924_unique_exact_order']=len(rows)==4924==len({x['id']for x in rows})and[x['original_input_line_1based']for x in rows]==list(range(1,4925))
 checks['union_count_exact']=sum(x['selected_for_proposed_review']for x in rows)==r['union_selected_n']==3262
 checks['trigger_counts_exact']=dict(collections.Counter(t for x in rows for t in x['trigger_ids']))==r['trigger_counts']
 checks['selected_equals_nonempty_trigger_set']=all(x['selected_for_proposed_review']==bool(x['trigger_ids'])for x in rows)
 checks['original_two_source_sha_every_row']=all(x['original_input_source_sha256']=='6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'and x['original_LLM03_source_sha256']=='29c36d745357872b05311f0456bd823842f312e00de892634a3e654bc318750e'for x in rows)
 checks['no_original_text_or_individual_label_fields']=all(not({'text','contexts','labels','dimension_reasons','evidence'}&set(x))for x in rows)
 checks['current9_coverage_only_not_expectations']=len(r['current9_real_control_coverage'])==r['current9_covered_n']==9 and all(not x['private_expectations_or_B_result_used']for x in r['current9_real_control_coverage'])
 checks['protected267_metadata_counts_match']=sum(x['reserved_family_member']for x in rows)==267 and sum(x['reserved_family_member']and x['selected_for_proposed_review']for x in rows)==192
 checks['all4924_group_frames_exact']=sum(g['all_n']for g in r['groups'].values())==4924 and r['three_department4481']=={'all_n':4481,'selected_n':2987}
 checks['sources_current_hashes_unchanged']=all(sha(x['path'])==x['sha256']and Path(x['path']).stat().st_size==x['bytes']for x in r['sources'])
 assert all(checks.values()),checks
 # Compute only future sample quotas from metadata; do not draw IDs or read
 # original/old-prediction prose. Four groups are distinct from main4481.
 strata=collections.defaultdict(int)
 for key,s in r['outside_strata_for_future_independent_audit'].items():
  g,k=key.split('|');k='I0F0'if k.startswith('I0F0')else k
  strata[g+'|'+k]+=s['nonprotected_outside_n']
 quotas=[{'stratum':g+'|'+p,'current_nonreserved_outside_N':strata[g+'|'+p],
          'future_proposed_n':min(5,strata[g+'|'+p]),
          'inclusion_probability_if_this_frame_unchanged':min(5,strata[g+'|'+p])/strata[g+'|'+p]if strata[g+'|'+p]else None}
         for g in ['GOV','NHSA','NHC','NMPA']for p in ['I0F0','I0F1','I1F0','I1F1']]
 future_n=sum(x['future_proposed_n']for x in quotas)
 method=OUT/'method-review/scope_spec_independent_method_review.json'
 erratum=OUT/'method-review/sampling_frame_erratum.json'
 assessment={'status':'FINAL_FEASIBILITY_ONLY_C09_B_FAIL_NO_EXECUTION_OR_ADOPTION',
  'mechanical_scan':bind(report_path),'scope_spec':bind(OUT/'scope_spec_PREDECLARED.json'),
  'scope_spec_lock':bind(OUT/'scope_spec_lock.json'),'per_row_real_source_provenance':bind(pp),
  'method_scope_review':bind(method),'method_sampling_frame_erratum':bind(erratum),
  'candidate_impact_range':{'all4924':3262,'fraction':3262/4924,'outside':1662,'main4481':2987,'main4481_outside':1494,
    'meaning':'Uniform candidate review scope, not3262 confirmed errors or3262 rows proven to need model rerunning.'},
  'current9_real_development_controls':{'covered':9,'total':9,'not_error_recall_or_B_success':True},
  'root_later_B_status':{'source':'Parent root message received after scope lock and mechanical scan; private expectation/review files not read.',
    'status':'FAIL','old_six_errors_corrected':3,'old_three_attribute_I_omissions_remain':True,'previously_correct_F_access_regression':True,
    'operational_implication':'Current09 is not ready for selective rerun/adoption. Scope estimation does not repair StageB adding thresholds absent from the manual.'},
  'outside_audit_PROPOSED_NOT_DRAWN':{'frame':'Current nonreserved current-unit IDs in1662 complement:1587. All human display input/output projections require the registered context redactor; critical masking means UNREVIEWABLE, not pass.',
    'reserved_outside_n_mechanical_only':75,'selection':'SRSWOR within department x retained03 I/F four combinations; stable ascending ID order and ascending department/I/F stratum order; random.Random(2026100809).',
    'quota':'min(5,N_h) in each nonempty stratum; weights N_h/n_h if describing the audit frame. Old labels stratify only, never expected answers.',
    'upper_bound_main4481':60,'upper_bound_GOV443':20,'upper_bound_all4924':80,
    'current_quota_metadata_total_if_authorized_and_frame_unchanged':future_n,
    'current_quota_main4481':sum(x['future_proposed_n']for x in quotas if not x['stratum'].startswith('GOV|')),
    'current_quota_GOV443':sum(x['future_proposed_n']for x in quotas if x['stratum'].startswith('GOV|')),
    'quota_metadata':quotas,'sample_IDs_drawn':False,'semantic_audit_completed':False,
    'limits':'Small development audit detects additional failures; absence of observed errors does not establish exhaustive recall, full-corpus correctness, power or external validity.',
    'file_and_structure_checks':'Record source-file and structure representation. If a file/structure is absent, transparently add a separately declared purposive supplement, never pool it unweighted as the probability sample.',
    'optional_near_miss':'At most1 predeclared single-predicate/near-structure item per trigger x group; main3 groups<=15, GOV<=5; separate purposive controls, not a population estimate. No items selected now.'},
  'regression_and_stop_conditions':[
    'Before any expanded execution, a fixed new implementation must pass actual original known-error correction and protection cases; current09B FAIL blocks expansion/adoption.',
    'Freeze prompt/runtime/input/subset/order and scope selector before any model call; all selected units retain full original raw input and receive complete five-dimensional judgment.',
    'Review every selected output, all five dimensions/reasons/quotes/I-F subtypes/S quality/issues and every technical attempt material flag; A original records may not be hand-edited.',
    'Preserve explicit positive parent/list/condition controls and independent-neighbor invariance controls; correct I/F must not degrade S/E/Ec or known-correct access/continuity.',
    'No known-target IDs, A/B disagreements, kappa or expected distribution select subset or actual response. First technical valid only; no semantic retry or majority voting.',
    'A confirmed outside-scope same-mechanism omission or a new regression stops a claim of sufficient scope. Record it and consider a separately versioned general scope only, not an ID exception.',
    'Reserved267 and shared contexts remain mechanically registered. Do not read protected originals/labels for development; redacted critical cases remain explicitly unaudited, with no blanket semantic-pass claim.'
  ],
  'true_selective_review_lineage':{
    'baseline':'Complete originalLLM03 remains immutable and visible as the initial judgment for all4924.',
    'eligible_review':'Fixed general scope union, whole five-dimensional row including unchanged values; not only the six known-error IDs or favorable changed dimensions.',
    'unreviewed':'Explicitly retains original03; do not imply it received09.',
    'row_append_fields':['original_input_file_SHA/line/ID/row_SHA','original03_output_file_SHA/line/row_SHA','scope_version_SHA/trigger_IDs/selected','actual_A_raw_file_SHA/same_ID_record_SHA','actual_B_raw_file_SHA/same_ID_full_row_SHA','all_attempt/request/event_SHA','technical_and_semantic_review_status','root_adoption_decision_SHA','effective_method_origin'],
    'version_name':'If later authorized and all fixed gates pass:03 initial judgment plus uniformly scoped09 review (selective-review combination version). Never call it a single complete09 corpus run.',
    'no_row_cherry_picking':'Adopt/reject the prespecified review version under declared gates; do not choose03 versus09 for each row/dimension from scores or expected labels.',
    'downstream':'If actually adopted later, recompute affected classifications and attention using the complete explicit effective version and existing fixed references/weights; preserve complete03 comparator and all prior statistics. Nothing is recomputed/adopted now.'},
  'cost_limit':'3262 is66.25% of rows; it saves33.75% of row rereads versus4924, before additional audits. Two-stage full-material requests can still cost more than an old one-stage full run; no token/fee saving is established.',
  'outside_old03_descriptive_counts':{'I1':93,'F1':88,'allfive0':1303,'meaning':'These are original predicted strata, not validated truth; complement cannot be presumed error-free.'},
  'frame_limit':'4924 includes GOV443; main analysis4481 excludes it. Neither equals the probability canonical frame1767 (947/760/60). Scope counts are not prevalence or weighted attention estimates.',
  'metadata_QA':checks,'metadata_QA_passed_n':len(checks),
  'initial_author_scan_failure_preserved':bind(OUT/'implementation-history/initial_scan_failure.json'),
  'original_C09_prompt_runtime_freeze_adoption_or_manuscript_modified':False,'private_expectations_or_B_outputs_read':False,
  'individual_policy_or_protected_prediction_semantically_read_or_displayed':False,'new_CLI_invocations':0,'new_model_calls':0,
  'finalizer_script':bind(Path(__file__))}
 save('partial_rerun_feasibility_FINAL.json',assessment)
 desc={'T1_CURRENT_ATTRIBUTE_CHANGE':'当前属性改变','T2_CURRENT_SAFETY_DUTY_OR_ACTION':'当前安全职责/动作','T3_CURRENT_SUPPORT_OR_ADMIN_IN_RESEARCH_CONTEXT':'研发语境中的支持/行政','T4_COVERAGE_ACCESS_OR_LINKED_CONDITION':'保障可及/关联条件','T5_NONEMPTY_STRUCTURED_FOLLOWING':'非空后项结构'}
 table='\n'.join('|'+desc[k]+'|'+str(r['trigger_counts'][k])+'|'for k in desc)
 dept='\n'.join('|'+g+'|'+str(v['all_n'])+'|'+str(v['selected_n'])+'|'+str(v['outside_n'])+'|'for g,v in r['groups'].items())
 text=f'''# 部分定向复核可行性：尚未执行或采用

可以保留完整LLM03初判，对统一、事先冻结的机制风险范围进行定向复核。此次固定触发的候选影响范围为3262/4924条（66.25%），范围外1662条；不是3262条确认错误，也不证明它们全部需要模型重跑。当前09B已由root报告FAIL，因此这个范围估计不能作为扩跑或采用门禁。

触发条件在计数前锁定（SHA `{sha(OUT/'scope_spec_PREDECLARED.json')}`），没有ID例外，不用原03标签、A/B分歧、κ或预期分布入围。旧03预测仅作汇总分层。词表只是召回风险，不作语义判定；原材料未删，所有4924行有真实来源路径、行号和双重原始row SHA。

|固定触发|命中条数（可重叠）|
|---|---:|
{table}

|来源组|原框|候选并集|范围外|
|---|---:|---:|---:|
{dept}

三部门4481条中的候选范围为2987、范围外1494；GOV443另算。4924、4481与原180概率样本对应的1767规范框（947/760/60）不同，不能混作比例或注意力分布。

当前9条真实开发控制9/9均在候选范围内，原字段与全输入逐对象一致；这只是范围覆盖，不是错误召回率或09B修复成功。root在计数后报告：六处旧错仅修3，三处I属性漏判仍在，原正确F可及项新增漏判。我们没有打开私有期待或B实际输出，以上状态来自root；触发词未随结果改动。下一步首先解决StageB额外阈值导致的真实失败，不能直接把当前09用于3262条。

范围外原03仍有I1=93、F1=88和五维全0=1303条；这些是旧机器预测而非真值。建议未来先在可开发审读的未命中框按部门×旧I/F四格抽检，每非空层SRSWOR抽min(5,N_h)，固定seed2026100809、ID与层序升序。主4481最多60条，GOV最多20条；按当前排除267成员后的元数据，拟配额为主48+GOV15=63条，尚未抽取ID或审读。抽样权重N_h/n_h单列，文件/结构缺口与最多20条近似机制对照另列为定向补充，不能与概率抽检混成未经加权的总体正确率。小样本未见错误也不能证明范围外全正确。

保护池中192条命中、75条在范围外，仅机械计数。未来人工投影须排除保护当前ID并用既有redactor遮蔽共享上下文；关键命题被遮蔽则记不可审定，不能强行PASS。当前ID无交集不等于上下文无保护材料。真实机器输入仍保留原字段/语境，不能静默改输入。

扩展前固定门禁应包括六处真实错全部修复、已正确项保留、08传播错与必要父条件/清单的对称控制、所有选中输出的完整五维/理由/引文/子类/质量/issue审查，以及范围外同机制漏召回检查。任何确定新回归或范围外机制遗漏均如实停止充分性结论；不按分数挑行、挑维、重试或给A手改后继续。

若以后获准并通过门禁，保留完整03基线，逐行追加触发版本、原A/B及同ID row SHA、请求/事件/attempt、审查与采用来源；未复核行明确沿用03。有效新版本只能称“03初判+统一预定范围的09定向复核组合”，不能伪装为一次完整09全量运行，也不能逐条选最有利的03/09值。只有真实采用后才沿既定参照/权重复算全版本统计，完整03平行结果仍保留。

3262条相对4924少33.75%的行数，尚未加抽检；两阶段保留完整材料，费用未必低于旧单阶段全量。本分析不保证全部潜在错误被召回，也不承诺κ达标。完整报告含{len(checks)}项元数据QA、重叠、行级来源及方法复核绑定。所有真实CLI/模型新增调用为0，提示、运行、标签、采用和正文均未改。

原4924输入SHA：`6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763`。完整03预测SHA：`29c36d745357872b05311f0456bd823842f312e00de892634a3e654bc318750e`。
'''
 with(OUT/'partial_rerun_feasibility_FINAL.md').open('x')as f:f.write(text)
 seal={'status':'FEASIBILITY_DELIVERED_NOT_EXECUTION_OR_ADOPTION','final_JSON':bind(OUT/'partial_rerun_feasibility_FINAL.json'),'final_MD':bind(OUT/'partial_rerun_feasibility_FINAL.md'),'mechanical_report':bind(report_path),'all4924_provenance':bind(pp),'scope_spec':bind(OUT/'scope_spec_PREDECLARED.json'),'method_review':bind(method),'method_erratum':bind(erratum),'new_model_calls':0,'new_CLI_invocations':0}
 save('feasibility_delivery_seal.json',seal)
 print(json.dumps({'status':assessment['status'],'final_JSON':seal['final_JSON'],'final_MD':seal['final_MD'],'delivery_seal':bind(OUT/'feasibility_delivery_seal.json'),'metadata_QA_n':len(checks),'future_outside_sample_quota_only':future_n,'new_CLI_invocations':0,'new_model_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
