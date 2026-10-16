"""Freeze finite geometry controls before candidate edits; no corpus run."""
import copy, hashlib, json, shutil
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[5]
BASE=P.parent/'v2'
AUD=ROOT/'outputs/goal-calibration-20261010/08-audits/SE-Ec-v2-independent-controls-sol'
MODULES=['source_packet','source_receipts','evidence','relations','dimensions']
ARTIFACTS=['controls40-final-scope.json','structural-final-scope.json','dependency-final-scope.json','bridge20-final-scope.json','legacy42-final-scope.json','interface-final-scope.json','closure-bindings-final-scope.json','missing-middle-final.json']
SCRIPTS=['v2_fixed_controls.py','structural_controls.py','dependency_controls.py','replay_bridge_controls.py','semantic_selfcheck.py','interface_controls.py','closure_binding_controls.py','middle_scope_control.py']
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,value):
    with (P/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
seal=json.loads((AUD/'output-seal.json').read_text())
assert bind(AUD/'output-seal.json')['sha256']=='8a043197a1393a41030b3565ee78005c712367a77ba7f3856ba835460d7cb890'
for x in seal['output_members']:assert bind(x['path'])==x
assert bind(BASE/'candidate-seal.json')['sha256']=='a630f5b6c3da8a2a91bd9fd0375caf890d5dfaef83ef2a81df3d8ab062cfc0dd'
assert bind(BASE/'delivery-seal.json')['sha256']=='39a87613fc07027fe97a7e739535d6101da0d248c8b84a1c573a6f699cba1d47'
for name in MODULES:
    assert bind(BASE/(name+'.py'))['sha256']==bind(AUD/'code-snapshot'/(name+'.py'))['sha256']
for name in [n+'.py' for n in MODULES]+SCRIPTS:
    assert not (P/name).exists();shutil.copyfile(BASE/name,P/name)
fixed={c['name']:c for c in json.loads((AUD/'new20-fixed-before-execution.json').read_text())['cases']}
new=[]
def clone(source,name,expected,reason):
    c=copy.deepcopy(fixed[source]);c.update(name=name,expected=expected,manual_reason=reason,control_category='owner_new_finite_geometry_development',is_human_reference=False)
    c['derived_from_exposed_independent_case']=source
    new.append(c);return c
def ctx(c,id):return next(x for x in c['synthetic_bundle']['source_record']['contexts'] if x['context_id']==id)
def geometry(c,id,**kw):
    x=ctx(c,id);x['structure'].update(kw);x['source_ref']['locator'].update(kw)
clone('closed_article_all_three','near_closed_group',{'S':1,'E':1,'Ec':1},'同源同组件连续成员及真正下一段闭合，仍消费完整条文。')
c=clone('closed_article_all_three','next_pid_near_but_sequence_remote',dict.fromkeys(['S','E','Ec']), '下一段号看似紧邻，但明确序号远隔；闭合证据冲突，需核真实末界。');geometry(c,'NEXT',sequence_index=99)
c=clone('closed_article_all_three','next_sequence_near_but_pid_remote',dict.fromkeys(['S','E','Ec']), '序号看似紧邻，但实际段号远隔；不能忽略已供段号冲突。');geometry(c,'NEXT',paragraph_id='p0099');ctx(c,'BOUNDARY')['structure']['next_paragraph_id']='p0099'
clone('single_article_boundary_does_not_donate','near_single_article',{'S':1,'E':0,'Ec':0},'同源同组件相邻下一条只证闭合，不给本条捐献效果费用。')
c=clone('single_article_boundary_does_not_donate','single_article_sequence_conflict',dict.fromkeys(['S','E','Ec']), '单段下一条明确远序号，不由相邻段号强行闭合。');geometry(c,'NEXT',sequence_index=40)
c=clone('safety_parent_wrong_target','near_safety_parent',{'S':1,'E':0,'Ec':0},'同源同组件直接安全内容父句准确指向当前第一成员。');ctx(c,'PARENT')['structure']['target_paragraph_id']='p0002'
clone('safety_parent_other_component_reused_pid','cross_component_safety_parent',{'S':0,'E':0,'Ec':0},'另一组件同段号的父句不是当前数据成员的内容要求。')
clone('direct_payment_child_condition','near_payment_parent',{'S':0,'E':0,'Ec':1},'直接费用父句同源同组件明确指向当前成员，构成条件—支付后果。')
c=clone('direct_payment_child_condition','payment_parent_wrong_target',{'S':0,'E':0,'Ec':0},'支付父句明确指向另一段，旧generic和SE路径都不能使用。');ctx(c,'PARENT')['structure']['target_paragraph_id']='p0999'
c=clone('direct_payment_child_condition','payment_first_member_remote_parent',{'S':0,'E':0,'Ec':0},'第一成员被错标局部父句，已供序号及段号远隔；不能只据role/target继承。');geometry(c,'CURRENT',paragraph_id='p0050',sequence_index=50);ctx(c,'PARENT')['structure']['target_paragraph_id']='p0050'
clone('effect_indicator_not_safety_sibling','effect_qualified_same_paragraph',{'S':0,'E':1,'Ec':0},'疗效限定指代只选疗效定义，不能借兄弟安全指标。')
# Rebuild the mirror as a full literal synthetic document, not a relabelled source.
c=clone('effect_indicator_not_safety_sibling','safety_qualified_same_paragraph',{'S':1,'E':0,'Ec':0},'安全性限定指代只选安全定义，不借同段兄弟疗效指标。')
raw='本药的疗效观察指标为疾病控制率。另设本药的安全性观察指标为肝损伤发生率。应核验上述安全性观察指标是否充分。'
text='应核验上述安全性观察指标是否充分。';doc=raw+'\n';sha=hashlib.sha256(doc.encode()).hexdigest();r=c['synthetic_bundle']['source_record'];r['text']=text
for x in [r]+r['contexts']:
    x['source_ref']['sha256']=sha;x['source_ref']['source_resource_id']='SOURCE-SYNTHETIC-'+sha;x['source_ref']['locator']['unicode_code_point_interval_half_open']=[0,len(raw)]
ctx(c,'CURRENT')['text']=raw;c['synthetic_documents']=[{'sha256':sha,'text':doc,'is_synthetic':True,'is_original_policy':False}]
write('geometry-controls-fixed-before-edit.json',{'status':'fixed_before_candidate_edit_non_human_development','cases':new,'case_N':len(new),'no_original_expectations_changed':True})
manual=json.loads((AUD/'manual-basis-quotes.json').read_text());m=Path(manual['binding']['path']).read_text();assert bind(manual['binding']['path'])==manual['binding']
for q in manual['quotes']:assert m[q['start']:q['end']]==q['quote']
write('manual-basis-bound.json',manual)
write('input-bindings.json',{'status':'SE_v3_geometry_only_candidate','base_seals':[bind(BASE/'candidate-seal.json'),bind(BASE/'delivery-seal.json')],'base_five_modules':[bind(BASE/(n+'.py')) for n in MODULES],'independent_seal':bind(AUD/'output-seal.json'),'independent_controls':[bind(AUD/n) for n in ['legacy20-controls.json','new20-fixed-before-execution.json','owner-closure3-fixed-before-execution.json','all-failures-full-inputs-and-paths.json']],'original156_scripts':[bind(BASE/n) for n in SCRIPTS],'original156_artifacts':[bind(BASE/n) for n in ARTIFACTS],'manual':manual['binding'],'scope':'Only SE evidence geometry and dedicated predicate consumers. Keep shared __init__/_add/_units/judge and IF logic unchanged; no common material release changes.','frozen_inputs_not_mutated':True,'whole77_800_4481_runs':0,'new_projection_used':False,'not_human_or_independent_formal_accuracy':True})
write('pre-edit-seal.json',{'five_modules':[bind(P/(n+'.py')) for n in MODULES],'new_controls':bind(P/'geometry-controls-fixed-before-edit.json'),'binding':bind(P/'input-bindings.json'),'manual':bind(P/'manual-basis-bound.json')})
print('prepared',len(new),'new controls; five exact SEv2 modules; manual and 26 audit members verified')
