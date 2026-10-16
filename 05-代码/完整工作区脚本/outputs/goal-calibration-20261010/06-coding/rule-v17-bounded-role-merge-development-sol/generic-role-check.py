"""Finite constructed role controls; no research IDs/reference rows."""
import json,hashlib
from pathlib import Path
from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

NAME='早期药物研发程序'
CURRENT='管理机构对'+NAME+'的资格进行审核,对符合终止'+NAME+'情形的,应当予以终止。'

def check(name, expected, current=CURRENT, gap=True, innovation=True, safety=True, support=True, same_service=True, cross_leaf=False):
    need='尚无有效防治手段或者与现有治疗相比具有明显临床优势' if gap else '与现有治疗相比具有明显临床优势'
    obj='创新药或者改良型新药' if innovation else '常规药物'
    scope='药物临床试验期间,用于防治严重影响生存质量的疾病且'+need+'的'+obj+',申请人可以申请适用'+NAME+'。'
    resource='管理机构对纳入'+NAME+'的药物优先配置资源进行沟通交流,加强指导并促进药物研发。'
    withdrawal='（三）对于已终止'+NAME+'的品种,自终止之日起,管理机构不再优先安排相关'+('沟通交流' if same_service else '技术培训')+'。'
    termination='（五）终止程序。对納入'+NAME+'的药物,管理机构按条件办理。\n发现以下任一情形,管理机构将终止'+NAME+':\n1.临床试验数据不再显示疗效优势。\n2.'+('因药物重大安全性问题而终止药物临床试验。' if safety else '申请人停止该项药物研发。')+'\n3.其他应当终止程序的情形。\n'
    full='早期药物研发工作程序（试行）\n一、适用范围和适用条件\n（一）适用范围\n'+scope+'\n（二）适用条件\n申请适用'+NAME+'的,应当同时满足以下条件:\n1.满足治疗效果研究条件。\n2.提供药物安全性证据。\n二、工作程序\n（四）研发指导。'+(resource if support else '申请人选择电话或者书面沟通形式。')+'\n'+termination+'三、工作要求\n（二）'+current+'\n'+withdrawal+'\n附件2\n其他药物研究工作程序（试行）\n一、工作程序\n'+resource+'\n'
    sha=hashlib.sha256(full.encode()).hexdigest();ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{}}
    ctx=[{'context_id':'CTX-SCOPE','kind':'source_paragraph','text':scope,'source_ref':ref,'structure':{}},{'context_id':'CTX-CURRENT','kind':'paragraph','text':current,'source_ref':ref,'structure':{}},{'context_id':'CTX-LINK','kind':'structural_relation','source_ref':ref,'structure':{'related_context_ids':['CTX-SCOPE']}}]
    cuts=[0,len(full)] if not cross_leaf else [0,full.index('（五）'),len(full)]
    leaves=[]
    for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
        text=full[a:b];leaves.append({'kind':'verbatim_UTF8_snapshot_text','source_resource_id':'CONSTRUCTED-LEAF-'+str(i),'source_sha256':sha,'source_version_id':'SOURCEVERSION-'+sha,'text':text,'text_utf8_sha256':hashlib.sha256(text.encode()).hexdigest(),'locator':{'unicode_code_point_interval_half_open':[a,b]}})
    bundle={'common_source_bundle_version':'constructed-not-study','source_record':{'id':'TOY-'+name,'text':current,'source_ref':ref,'contexts':ctx},'source_documents':[],'explicit_or_primary_source_resources':[],'preserved_historical_neutral_source_supplements':[],'source_full_text_resources':leaves,'source_asset_locations':[],'source_locator_bases':{},'source_reference_index':[],'source_provenance_addenda':[]}
    view=RelationView(semantic_unit(bundle));d=judge(view);validate_decisions(view.unit,d)
    roles=[r for r in view.traces() if r['details'].get('relation_subtype')=='bounded_primary_qualification_support_roles']
    result={'name':name,'expected':expected,'actual':{x:d[x]['value'] for x in expected},'role_relation_N':len(roles),'I_basis_path':d['I']['basis_path'],'F_basis_path':d['F']['basis_path'],'S_basis_path':d['S']['basis_path'],'role_kinds':sorted({x['role'] for r in roles for x in r['details']['source_roles']}),'F_gap_branches':d['F']['details'].get('F_gap_branches'),'model_calls_N':0,'constructed_only':True}
    assert result['actual']==expected,result
    if expected.get('I')==1:assert d['I']['basis_path']=='I3_actual_innovative_research_support' and d['I']['details'].get('I3_role_evidence'),result
    if expected.get('F')==1:assert d['F']['details'].get('F_role_evidence') and [x['kind'] for x in d['F']['details']['F_gap_branches']]==['no_effective_option'],result
    if expected.get('I')==1 or expected.get('F')==1:assert result['role_kinds']==['object_and_eligibility_definition','priority_research_support','qualification_standard','withdrawal_direct_mechanism'],result
    return result

def main():
    results=[check('standards-and-support-coexist',{'S':1,'I':1,'F':1}),
      check('support-no-safety-standard',{'S':0,'I':1,'F':1},safety=False),
      check('clinical-advantage-only-not-fairness',{'S':1,'I':1,'F':0},gap=False),
      check('noninnovation-object-not-I3',{'S':1,'I':0,'F':1},innovation=False),
      check('status-only',{'I':0,'F':0},current='该药品已纳入'+NAME+',目前处于终止状态。'),
      check('paperwork-only',{'I':0,'F':0},current='申请人应当递交'+NAME+'的书面材料并核验格式。'),
      check('general-purpose-only',{'I':0,'F':0},current='为促进创新药研发及按需资源配置,制定本'+NAME+'。'),
      check('support-only-in-other-programme',{'I':0,'F':0},support=False),
      check('different-withdrawn-service-not-merged',{'I':0,'F':0},same_service=False),
      check('cross-leaf-roles',{'S':1,'I':1,'F':1},cross_leaf=True)]
    with (Path(__file__).parent/'generic-role-check-results.json').open('x',encoding='utf8') as f:json.dump({'check_N':len(results),'passed':True,'cases':results,'not_actual_cohort_inference':True,'not_new_acceptance_gate':True},f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'generic_role_check_N':len(results),'passed':True},ensure_ascii=False))

if __name__=='__main__':main()
