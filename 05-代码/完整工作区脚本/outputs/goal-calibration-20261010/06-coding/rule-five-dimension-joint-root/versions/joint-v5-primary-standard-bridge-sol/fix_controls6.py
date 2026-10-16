from pathlib import Path
import hashlib,json,datetime,shutil
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
B=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
P=B.parent/'joint-v5-primary-standard-bridge-sol'
P.mkdir(exist_ok=False)
def bind(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def verify(b):assert bind(b['path'])==b,b['path']
def dump(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
seal=load=lambda p:json.loads(Path(p).read_text())
s=seal(B/'delivery-seal.json');assert bind(B/'delivery-seal.json')['sha256']=='7732efae659ca39b8474a726a915dacd86312e2300f4ed7daf73ee9f832c28ec'
for b in s['output_members']:verify(b)
(P/'baseline-code-snapshot').mkdir()
for name in ['source_packet','source_receipts','evidence','relations','dimensions','regression_tests']:
 for d in [P,P/'baseline-code-snapshot']:shutil.copyfile(B/(name+'.py'),d/(name+'.py'))
A=R/'08-audits/common-candidate-actual-interface-v4-execution-sol'
sa=seal(A/'output-seal.json');assert bind(A/'output-seal.json')['sha256']=='3440b911dd4eb92773a2edda27ea33e87b71e90da40165203a6af2300c4af8ca'
for b in sa['members']+sa['inputs']:verify(b)
rows=seal(A/'execution-results.json')
actual=[dict(source_id=x['record_id'],historical_expected_S=x['expected_S'],actual_baseline_S=x['actual_S'],source_packet=x['source_packet'],output=bind(A/'execution-results.json'),trace_row_index=i,other_dimension_values_are_observation_only=x['observed_values_only']) for i,x in enumerate(rows)]
assert [x['source_id'] for x in actual]==['RECODE25-00036','RECODE25-00038','RECODE25-00045']
baseline=seal(B/'algorithm-bindings.json')
dump('input-bindings.json',dict(identity='nonhuman v5 developer candidate source-only bridge',baseline_delivery_seal=bind(B/'delivery-seal.json'),baseline_preseal=bind(B/'pre-execution-seal.json'),baseline_algorithm=bind(B/'algorithm-bindings.json'),baseline_five_modules=baseline['five_modules'],manual=baseline['manual'],common_frozen_input_bindings=baseline['common_frozen_input_bindings'],actual_S3_baseline_seal=bind(A/'output-seal.json'),actual_S3_verified_member_N=len(sa['members']),actual_S3_verified_input_N=len(sa['inputs']),actual_S3_development_baseline=actual,new_actual_source_ids_outside_authorized_S3=[],new_hidden_v5_controls_read=False,cohort_run=False,main_LLM_labels_read=False))

def make(name,termination=False,missing_boundary=False,cross_component=False,boundary_risk=False,tail_risk=False,positive=True):
 title='临床研究计划'
 if not termination:
  current='药审机构应当核验申请适用临床研究计划药品的纳入条件，符合标准方可获得资格。'
  lines=[title,'一、适用条件','药品申请适用临床研究计划，应当同时满足以下条件：',('1.该药品应当核验过敏风险证据。' if positive else '1.该药品申请表中的文件名须符合字符格式。'),'2.该药品申请文件应当签章。']
  if not missing_boundary:lines.append('二、药品安全性与过敏风险工作程序' if boundary_risk else '二、工作程序')
  lines.append(current)
  if not missing_boundary:lines.append('三、工作要求')
  seed_index=2
 else:
  current='应当审核临床研究计划药品资格，对符合终止临床研究计划情形的，应当予以终止。'
  lines=[title,'（一）终止程序','药品申请适用临床研究计划，发现以下任一情形时应当终止：','1.申请文件缺少签章。',('2.因重大安全性问题，药物临床试验已终止。' if positive else '2.申请文件编号不符合字符格式。'),'3.申请文件未及时递交。',('药审机构应当核验该药品的过敏风险证据。' if tail_risk else '药审机构公开药品名单并更新状态信息。'),'二、药品过敏风险工作要求',current]
  seed_index=2
 raw='\n'.join(lines)+'\n';sha=hashlib.sha256(raw.encode()).hexdigest();starts=[];start=0
 for line in lines:starts.append([start,start+len(line)]);start+=len(line)+1
 def ref(span,component='body'):
  return {'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'component_id':component,'unicode_code_point_interval_half_open':span,'coordinate_basis':'exact supplied raw UTF8 string'}}
 ci=lines.index(current);cr=ref(starts[ci]); sr=ref(starts[seed_index]);leaf=ref([0,len(raw)],'other' if cross_component else 'body')
 unit={'text':current,'source_ref':cr,'contexts':[{'context_id':'CURRENT','kind':'paragraph','text':current,'source_ref':cr,'structure':{'component_id':'body','paragraph_id':'p'+str(ci+1),'sequence_index':ci}}, {'context_id':'SEED','kind':'source_paragraph','text':lines[seed_index],'source_ref':sr,'structure':{'component_id':'body','paragraph_id':'p'+str(seed_index+1),'sequence_index':seed_index}}, {'context_id':'REL','kind':'structural_relation','text':'','source_ref':cr,'structure':{'related_context_ids':['SEED']}}, {'context_id':'LEAF','kind':'source_textleaf','text':raw,'source_ref':leaf,'structure':{'component_id':'other' if cross_component else 'body'}}]}
 expected={'S':None if missing_boundary or cross_component else 1 if positive else 0,'E':None if missing_boundary or cross_component else 0,'Ec':None if missing_boundary or cross_component else 0,'I':0,'F':0}
 return dict(name=name,synthetic_input=unit,synthetic_literal_binding={'sha256':sha,'utf8_bytes':len(raw.encode()),'unicode_N':len(raw)},expected=expected,interface_case_not_policy=True,expected_is_development_relation_not_human_gold=True,condition='genuine same-leaf finite group and actual next heading; source coordinates must agree; heading/trailing independent paragraph are boundary-only')
cases=[make('same leaf admission risk standard before actual next section'),make('leaf EOF is not a standard boundary',missing_boundary=True),make('same SHA but leaf component conflicts with current',cross_component=True),make('safe format condition with neighboring risk heading',positive=False,boundary_risk=True),make('termination explicit numbered risk member with trailing status paragraph',termination=True),make('termination tail and next section risk are not condition members',termination=True,positive=False,tail_risk=True)]
dump('controls6-fixed-before-edit.json',dict(identity='nonhuman source-only finite primary-standard bridge controls',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=cases,new_hidden_v5_controls_read=False))
manual=Path(baseline['manual']['path']).read_text();rawbytes=manual.encode();quotes=[];start=0
for i,line in enumerate(manual.splitlines(keepends=True),1):
 if i in [9,15,40,41,42,43,44,52,214]:
  text=line.rstrip('\r\n');quotes.append(dict(line=i,text=text,unicode_code_point_interval_half_open=[start,start+len(text)],utf8_byte_interval_half_open=[len(manual[:start].encode()),len(manual[:start+len(text)].encode())]))
 start+=len(line)
dump('control-pre-edit-seal.json',dict(identity='nonhuman developer pre-fixed 6 controls before code edit',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),controls=bind(P/'controls6-fixed-before-edit.json'),five_modules=[bind(P/(n+'.py')) for n in ['source_packet','source_receipts','evidence','relations','dimensions']],manual=baseline['manual'],manual_quotes=quotes,actual_S3_baseline=bind(A/'output-seal.json'),new_hidden_v5_controls_read=False))
shutil.copyfile('/tmp/build_v5_controls_sol.py',P/'fix_controls6.py')
print(P)
print(json.dumps(bind(P/'control-pre-edit-seal.json'),ensure_ascii=False))
