"""Small saved-source replays and synthetic boundary controls; no corpus rewrite."""
import copy,json,pathlib,sys,hashlib
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'code'))
import relations,dimensions,evidence

ids={'RECODE25-'+s for s in ['00125','00132','00133','00138','00141','04162','04197','00038','00118']}
units={r['id']:r['semantic_unit'] for r in map(json.loads,open(ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl')) if r['id'] in ids}
positive=[]
for rid,u in units.items():
 v=relations.RelationView(u);a=dimensions.judge(v)
 evidence.validate_decisions(v.unit,a)
 positive.append({'id':rid,'labels':{d:x['value'] for d,x in a.items()},'relations':v.traces()})

# These constructed controls test entry gates, not previously coded records.
# If a mere notification/formal channel reaches full-programme expansion, fail.
controls=[
 ('ordinary_contact_form','_postadmission_technical_support','对纳入优先审评审批程序的品种，可以通过电话、视频、面对面等沟通交流方式联系。'),
 ('bare_submitting_form','_postadmission_technical_support','对纳入优先审评审批程序的品种，申请人可以提交沟通交流申请表。'),
 ('preapplication_not_postadmission','_postadmission_technical_support','对纳入优先审评审批程序的品种，在申报前提供研究方案反馈的沟通交流。'),
 ('status_not_withdrawal','_programme_condition_consequence','纳入优先审评审批程序的品种不符合优先审评审批条件。'),
 ('withdrawal_unrelated_to_conditions','_programme_condition_consequence','纳入优先审评审批程序的品种已经结束审评，将通知申请人。'),
 ('staffing_administration','_team_service_execution','审评团队内部应加强沟通，及时解决行政文件归档问题，保证按时限完成报送。'),
 ('ordinary_deadline','_team_service_execution','审评团队内部应加强沟通，保证按时限完成审评工作。'),
 ('priority_notice_only','_priority_resource_arrangements','对纳入优先审评审批程序的药品，仅通知申请人优先配置资源进行审评的结果。'),
 ('priority_not_implemented','_priority_resource_arrangements','对纳入优先审评审批程序的药品，未实施优先配置资源进行审评。'),
 ('routine_postmarketing_check','_need_linked_inspection_deferral','药品上市后应进行常规监督检查。'),
 ('inspection_not_testing','_need_linked_inspection_deferral','完成上市审批后，可以开展药品注册检验。'),
]
negative=[]
for name,method,text in controls:
 v=relations.RelationView.__new__(relations.RelationView)
 v.norm=relations.norm(text);v.text=text;v.relations=[];v.contexts=[];v.unit={}
 def unexpected(*a,**kw):raise AssertionError(name+' reached source expansion')
 v._closed_primary_programme=unexpected
 v._current_source=unexpected
 getattr(v,method)()
 assert not v.relations,name
 negative.append({'name':name,'text':text,'no_expansion':True})

# Deferral requires a same-source baseline specifically about registration
# inspection, not registration testing. These in-memory variants are controls,
# never replacement policy texts or saved corpus predictions.
for name,change in [('missing_baseline','remove'),('testing_baseline_not_inspection','testing'),('different_source_baseline','source')]:
 u=copy.deepcopy(units['RECODE25-00132'])
 if change=='remove':u['contexts']=[c for c in u['contexts'] if c['kind']!='preceding_paragraph']
 else:
  for c in u['contexts']:
   if c['kind']=='preceding_paragraph':
    if change=='testing':c['text']=c['text'].replace('核查','检验')
    else:c['source_ref']['sha256']='0'*64
 v=relations.RelationView(u)
 assert not any(r['details'].get('relation_subtype')=='bounded_need_linked_inspection_deferral' for r in v.traces()),name
 negative.append({'name':name,'constructed_control':True,'no_deferral_relation':True})

# All support fields must be backed by the same component. Without the closed
# header scope, execution of an otherwise relevant team cannot inherit a title.
u=copy.deepcopy(units['RECODE25-04197']);u['contexts']=[c for c in u['contexts'] if c['kind']!='following_heading']
v=relations.RelationView(u)
assert not any(r['details'].get('relation_subtype')=='bounded_specialized_team_execution' for r in v.traces())
negative.append({'name':'team_scope_not_closed','constructed_control':True,'no_team_execution_relation':True})
result={'positive_replays':positive,'negative_controls':negative,'source_prediction_changes':0,
 'code_bindings':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')},
 'scope':'9 saved-input deterministic replays and 15 synthetic boundary controls; not new validation or full coding'}
(HERE/'relations-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'positive':[(r['id'],r['labels']) for r in positive],'negative_passed':len(negative)},ensure_ascii=False))
