from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
A=R/'08-audits/current-machine-rare-disagreement-semantic-20261011-sol'
V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
def bind(p):
 p=p.resolve();r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def save(n,x):
 with (O/n).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
inputs=['phase01-first40/semantic-reviews40.json','phase01-first40/seal.json','phase02-remaining90/semantic-reviews90.json','phase02-remaining90/seal.json','readable-disagreement-selection-freeze.json','semantic-second-check/report.json','semantic-second-check/report.md','semantic-second-check/output-seal.json','final130/report130.md','final130/seal.json','final130/audit-analysis-addendum-02209.json','supplement-restricted-mother-object-20261012-sol/report.json','supplement-restricted-mother-object-20261012-sol/seal.json']
reviews=json.loads((A/inputs[0]).read_text())+json.loads((A/inputs[2]).read_text())
pending={('00040','F'),('00105','F'),('00130','I'),('00130','F'),('00131','F'),('00246','F'),('00247','F'),('01386','I'),('01387','I'),('01403','I'),('00068','I'),('00071','I'),('00071','F')}
zeros={('01391','I'),('01430','I'),('01435','I'),('01436','I'),('00654','F')}
cases=[];packets={}
for x in reviews:
 key=(x['id'][-5:],x['dimension']);pb=x['current_direct_material']['packet'];actual=bind(Path(pb['path']))
 assert actual==pb,(actual,pb)
 packets[x['id']]=pb
 cases.append({'name':x['id']+'/'+x['dimension'],'packet_binding':pb,'expected':{} if key in pending else {x['dimension']:0 if key in zeros else 1},'hard_assertion':key not in pending,'pending_dimensions':[x['dimension']] if key in pending else [],'semantic_reason':x['reason'],'review_status':'development diagnosis; not gold or human adjudication','must_not_add_unproved_whole_programme_positive':key in {('00068','I'),('00071','I'),('00071','F')},'restricted_mother_object_review_supersedes_first_review':key in {('00068','I'),('00071','I'),('00071','F')}})
save('real-controls-fixed-before-edit.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'control_N':len(cases),'hard_dimension_N':sum(x['hard_assertion'] for x in cases),'pending_dimension_N':len(pending),'expected_outside_semantic_input':True,'no_native_or_human_labels_in_classifier_input':True,'all_cases_including_failures_must_be_retained':True,'cases':cases})
# Fully materialized neutral source-only examples; source positions and predicates are input, expectations are external.
S='a'*64
ref={'sha256':S,'source_resource_id':'SOURCE-'+S,'locator':{}}
def unit(text,contexts=None):return {'text':text,'source_ref':ref,'contexts':contexts or []}
synthetics=[]
def lit(n,t,e,reason):synthetics.append({'name':n,'semantic_input':unit(t),'expected':e,'hard_assertion':True,'semantic_reason':reason,'synthetic':True})
for n,t,e,reason in [
 ('explicit_resource_tilt','30日通道将审评审批资源向符合条件的创新药临床试验申请倾斜。',{'I':1},'当前对象、资源与倾斜动作自足'),
 ('explicit_innovation_time_convenience','对符合要求的创新药临床试验申请，在受理后30个工作日内完成审评审批。',{'I':1},'明确创新研发申请办理便利'),
 ('general_deadline','所有药品注册申请应在受理后30个工作日内完成通知送达。',{'I':0,'F':0},'普通通知期限'),
 ('innovation_signature','创新药申请书必须签章，并在30日内递交。',{'I':0,'F':0},'签章递交事务不为研发服务'),
 ('innovation_drug_safety_obligation','创新药申请人应收集不良反应并更新风险管理计划。',{'S':1,'I':0},'一般风险义务'),
 ('clinical_comparison_without_innovation','应比较药物与现有治疗的完全应答率。',{'E':1,'I':0},'普通效果比较无创新联系'),
 ('innovation_content_list','药品创新性说明包括主要创新点，以及该创新带来的疗效或安全性优势。',{'I':1},'实质创新内容栏目'),
 ('innovation_field_presence','药品创新性字段不能为空，只检查字符数。',{'I':0},'字段存在性'),
 ('substantive_action_mechanism','基础研究和药物作用机制创新是推进药物研发的根本动力。',{'I':1},'当前药物技术创新关系'),
 ('admin_innovation','监管办公室通过排班创新提高收件效率。',{'I':0},'管理创新'),
 ('give_route_modification','改良给药途径是重要改良方式之一。',{'I':1},'当前实质改良内容'),
 ('resistance_modification','现有药物发生耐药后无药可治，因此应寻找可克服耐药的新一代抗肿瘤药物。',{'I':1},'局限与具体治疗属性改变'),
 ('direct_market_gap_priority','对明确为市场短缺的儿童药品实行优先审评审批。',{'F':1},'现实供药缺口直接配置机会'),
 ('market_gap_definition','市场短缺是本词典中的一种术语。',{'F':0},'纯术语定义'),
 ('no_options_evidence','申请优先支持时，应说明目标疾病目前无有效治疗药物或治疗手段，并提交相应证据。',{'F':1},'当前实质缺口证据要求与机会'),
 ('advantage_is_not_gap','该创新药相对现有治疗具有临床优势，可申请优先审评。',{'F':0,'I':1},'临床优势不能补治疗选项缺口'),
 ('unmet_need_generic','研发单位应关注患者治疗需求。',{'F':0},'泛需要'),
 ('other_drug_priority','儿童药品甲目前无有效治疗选项；其他药品乙可以申请优先审评。',{'F':0},'机会属于另一对象'),
 ('gap_field_only','目前无有效治疗药物字段不能为空。',{'F':0},'字段存在性'),
 ('self_data_distinct_role','在数据保护期内，其他申请人提交自行取得并未依赖他人受保护的数据申报注册，符合条件的应批准，但不给予数据保护期。',{'I':0},'自取且未依赖数据对象不是创新持有人的保护数据'),
 ('innovation_right_withdrawal','对创新药全部试验数据给予6年数据保护，违反资格条件的撤回数据保护。',{'I':1},'合格创新对象的实质权利限制仍保留'),
 ('innovator_reliance_restriction','其他申请人未经创新药持有人同意，依赖其受保护的数据申报注册，不予许可。',{'I':1},'其他申请人限制保护原创新持有人数据'),
 ('narrow_conditional_mother','符合附条件批准的药品可一并申请优先审评审批。',{},'未证明受限母对象交叉，不强行决定I/F'),
 ('routine_research_report','纳入研发计划后，申请人应定期书面报告进度。',{'I':0,'F':0},'报告义务没有技术服务'),
 ('explicit_technical_support','药审中心对创新药研发提供研究方案反馈。',{'I':1},'实际反馈直接面向创新研发'),
 ('generic_drug_feedback','药审中心对普通仿制药申请提供格式校验。',{'I':0,'F':0},'普通格式手续'),
 ('weak_elderly_data','老年患者数据缺失可能限制其临床治疗。',{},'保障边界继续待定'),
 ('outside_entry','目录编号甲乙丙。',{'I':0,'F':0},'入口外原逻辑完全等价'),
 ]:lit(n,t,e,reason)
# Programme material contains a unique finite scope, direct condition chain and same-stage service component.
def programme(n,current,expected,mode='service',scope=None,parent=None,foreign=False):
 scope=scope or '药物临床试验期间，创新药或者改良型新药且尚无有效治疗手段的，申请人可申请适用甲研发程序。'
 before=['甲研发程序','一、适用范围',scope,'（二）适用条件','申请适用甲研发程序的，应当同时满足以下条件：','药物应比现有治疗具有显著临床改善。具体包括下列情形：'] if mode=='qualification' else ['甲研发程序','一、适用范围',scope,'二、工作程序','（一）临床试验研制指导。对纳入甲研发程序的药物优先配置资源进行沟通交流，并给予研究方案反馈。']
 if mode=='termination':before+=['（二）终止程序。','发现以下任一情形，将终止甲研发程序：']
 if parent:before.append(parent)
 raw='\n'.join(before+[current,'三、工作要求','对已终止甲研发程序的品种，不再优先安排沟通交流。'])
 cs=[{'context_id':'current','kind':'paragraph','text':current,'source_ref':ref,'structure':{'paragraph_id':'current'}}]
 cs.append({'context_id':'scope','kind':'source_paragraph','text':scope,'source_ref':ref,'structure':{}})
 if mode=='qualification':
  for i,t in enumerate(before[4:]):cs.append({'context_id':'parent'+str(i),'kind':'parent_paragraph','text':t,'source_ref':ref if not foreign else {'sha256':'b'*64,'source_resource_id':'SOURCE-'+'b'*64,'locator':{}},'structure':{'sequence_index':i}})
 if mode=='termination':cs.append({'context_id':'parent','kind':'parent_paragraph','text':before[-1],'source_ref':ref,'structure':{'sequence_index':0}})
 if parent:cs.append({'context_id':'specific-parent','kind':'parent_paragraph','text':parent,'source_ref':ref,'structure':{'sequence_index':0}})
 cs.append({'context_id':'leaf','kind':'source_textleaf','text':raw,'source_ref':{'sha256':S,'source_resource_id':'SOURCE-'+S,'locator':{'unicode_code_point_interval_half_open':[0,len(raw)]}},'structure':{}})
 synthetics.append({'name':n,'semantic_input':unit(current,cs),'expected':expected,'hard_assertion':bool(expected),'semantic_reason':'同源唯一程序及确切阶段/父链；仅消费当前承接的分支','synthetic':True})
programme('linked_complete_response','与现有治疗相比，该药物可获得完全应答，而现有治疗仅能获得部分应答。',{'I':1},mode='qualification')
programme('linked_cause_treatment_change','现有治疗仅能处理症状，该药物可对病因治疗并产生持续临床获益。',{'I':1},mode='qualification')
programme('disease_member_no_sibling_comparison','用于防治严重危及生命的疾病。',{'I':0},mode='qualification')
programme('foreign_condition_parent','与现有治疗相比，该药物具有更显著治疗效果。',{'I':0},mode='qualification',foreign=True)
programme('unnamed_same_stage_feedback','申请人可在临床试验关键阶段提交资料，药审中心对下一步研究方案提出意见并反馈申请人。',{'I':1,'F':1})
programme('same_programme_signature_no_service','申请人需签章，并通过网站递交资料。',{'I':0,'F':0})
programme('same_programme_forms_no_service','沟通交流可采用电话或视频形式。',{'I':0,'F':0})
programme('same_programme_other_object','对其他仿制药申请提供格式校验。',{'I':0,'F':0})
programme('admitted_actual_service','对纳入甲研发程序的药物提供研究方案反馈。',{'I':1,'F':1})
programme('termination_general_member','因重大安全性问题，药物临床试验已终止的。',{'I':1,'F':1},mode='termination')
programme('termination_advantage_only_no_gap_copy','新的数据不再显示比现有治疗具有明显临床优势。',{},mode='termination')
programme('narrow_conditional_no_crossbranch','申请优先审评的，可一并提出申请。',{},parent='提交附条件批准上市申请的药品，可以向药审中心申请附条件批准。')
# Current rows with exact local geometry; no sibling row content can donate innovation.
for name,subject,cat in [('marketed_vaccine_row','境内已上市疫苗','3类/3.3'),('biosimilar_row','生物类似药','3类/3.3'),('other_biologic_row','其他生物制品','3类/3.4'),('qualified_innovation_denial','创新型疫苗','1类')]:
 cells=[cat,subject,'—','不给予数据保护。'];t=' | '.join(cells);headers=['分类','内容','数据保护期','备注'];cs=[]
 row={'context_id':'row','kind':'table_row','text':'','headers':headers,'row_cells':cells,'source_ref':ref,'structure':{'column_indices':list(range(4)),'row_cell_column_pairs':[{'cell_index':i,'header_index':i,'column_index':i} for i in range(4)]}}
 cs.append(row)
 for i in range(4):
  for kind,txt in [('table_row_cell',cells[i]),('table_header_cell',headers[i])]:cs.append({'context_id':kind+str(i),'kind':kind,'text':txt,'source_ref':ref,'structure':{'column_index':i,'parent_context_id':'row'}})
 cs.append({'context_id':'definition','kind':'source_resource_text','text':'创新药和改良型新药的全部试验数据给予数据保护。','source_ref':ref,'structure':{}})
 synthetics.append({'name':name,'semantic_input':unit(t,cs),'expected':{'I':1 if name=='qualified_innovation_denial' else 0},'hard_assertion':True,'semantic_reason':'分类、内容、待遇均是当前确切行；否定词本身不是排除条件','synthetic':True})
save('synthetic-controls-fixed-before-edit.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_N':len(synthetics),'expected_outside_semantic_input':True,'all_cases_including_failures_must_be_retained':True,'cases':synthetics})
entry='申请|纳入|终止|退出|撤回|取消|限制|维持|授予|准入|优先|条件|资格|标准|情形|情况|范围|符合|满足|发现|临床|治疗|防治|疗效|获益|应答|安全性|沟通|咨询|会议|反馈|方案|资料|审评|研发|研制|改良|创新|新品种|剂型|规格|短缺|供应|供药|断供|提供|安排|实施|执行|服务|支持|補充|补充|说明|阐述|评估|核验|审核|保护|数据|分类|权利|注册|许可|给予|机制|改变|设计|开发|试点|计划|资源|名额|鼓励'
save('impact-contract-before-edit.json',{'entry_regex':entry,'entry_version':'v2_bidirectional_current_dominating_gate','new_relation_kind':'v9_IF_relationship','entry_sites':['last RelationView.__init__ statement','judge immediately before acc.finish'],'recompute_scope':'whole record including every old/new unit, positive/additional evidence, IF requests and boundaries','all_existing_AST_unchanged_except_guard_calls':True,'nonjudgement_modules_byte_identical':True,'invalid_old_positive_filter':'only affirmative wrong beneficiary/row/stage evidence; never absence of new parser receipt','only_mutable_decision_dimensions':['I','F'],'existing_valid_evidence_preserved':True,'restricted_mother_object':'no whole programme inheritance without current intersection proof; unresolved chains retained','full_fallback_if':['guard isolation fails','global GAPS or shared helper changed','wrapper/adapter/material changed','mixed v7-v8 baseline equivalence cannot be inherited','new body audit incomplete'],'classifier_features_prohibited':['id','department','label','native answer','human answer','desired score'],'population_selector_execution':'not run; ROOT must approve full influence contract'})
save('input-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manual':bind(R/'03-manual/full4481-common-release-20261010-root/manual.txt'),'semantic_inputs':[bind(A/n) for n in inputs],'ROOT_adoption':bind(R/'08-audits/ROOT-v9-semantic-adoption-20261012.md'),'old_modules':[bind(V/(n+'.py')) for n in ['evidence','source_packet','source_receipts','relations','dimensions']],'selected_packet_N':len(packets),'selected_packets':list(packets.values()),'packet_open_log':'Each listed selected packet read only for binding during preparation; selected focused packet current/context inspections recorded in report. No unselected neighbouring packet opened.','prohibited_body_or_labels_opened':False})
print(json.dumps({'real_dimensions':len(cases),'hard':sum(x['hard_assertion'] for x in cases),'pending':len(pending),'selected_packet_N':len(packets),'synthetic_N':len(synthetics)},ensure_ascii=False))
