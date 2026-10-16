"""Small constructed source-boundary checks; no research IDs or reference rows."""
import copy, hashlib, json
from pathlib import Path
from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions


def case(name, standard, current, expected, linked=True, termination=False, split=False, inline=False, mixed=False, mention=False, punctuation="。"):

    scope = '药物临床试验期间,用于重大疾病药物研究,申请人可以申请适用早期药物研发程序。'
    sep=punctuation if inline else '\n'
    group = ('（五）终止程序'+sep+'对纳入早期药物研发程序的药物临床试验,申请人应当按条件办理。\n发现以下任一情形,管理机构将终止早期药物研发程序:\n' if termination else '一、适用范围和适用条件'+sep+scope+'\n（二）适用条件'+sep+'申请适用早期药物研发程序的,应当同时满足以下条件:\n')
    if mention:
        group=group.replace('（五）终止程序','本段只是提到（五）终止程序',1)
    body = '早期药物研发工作程序（试行）\n' + (scope + '\n' if termination else '') + group + standard + '\n' + (('三、工作要求。' if mixed else '三、工作要求\n') if termination else '二、工作程序\n') + current + '\n附件2\n其他药物审评工作程序（试行）\n一、适用条件\n1.提供药物安全性风险证据。\n二、工作程序\n'
    sha = hashlib.sha256(body.encode()).hexdigest()
    ref = {'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{}}
    contexts = [{'context_id':'CTX-SEED','kind':'source_paragraph','text':scope,'source_ref':ref,'structure':{}},
                {'context_id':'CTX-CURRENT','kind':'paragraph','text':current,'source_ref':ref,'structure':{}},
                {'context_id':'CTX-LINK','kind':'structural_relation','source_ref':ref,'structure':{'related_context_ids':['CTX-SEED'] if linked else []}}]
    cuts=[0,len(body)] if not split else [0,body.index('2.')+2,len(body)]
    resources=[]
    for index,(a,b) in enumerate(zip(cuts,cuts[1:])):
        text=body[a:b]
        resources.append({'kind':'verbatim_UTF8_snapshot_text','source_resource_id':'TOY-LEAF-'+str(index),'source_sha256':sha,'source_version_id':'SOURCEVERSION-'+sha,'text':text,'text_utf8_sha256':hashlib.sha256(text.encode()).hexdigest(),'locator':{'unicode_code_point_interval_half_open':[a,b]}})
    bundle={'common_source_bundle_version':'constructed-not-study','source_record':{'id':'TOY-'+name,'text':current,'source_ref':ref,'contexts':contexts},'source_documents':[],'explicit_or_primary_source_resources':[],'preserved_historical_neutral_source_supplements':[],'source_full_text_resources':resources,'source_asset_locations':[],'source_locator_bases':{},'source_reference_index':[],'source_provenance_addenda':[]}
    view=RelationView(semantic_unit(bundle)); decisions=judge(view);validate_decisions(view.unit,decisions)
    selected=[r for r in view.traces() if r['details'].get('resolution_path')=='primary_literal_complete_operative_standard']
    result={'name':name,'expected_S':expected,'actual_S':decisions['S']['value'],'completed_standard_group_N':len(selected),'selected_group_spans':[r['details']['selected_group_snapshot_span'] for r in selected],'S_basis_path':decisions['S']['basis_path'],'synthetic_only':True}
    assert result['actual_S']==expected,result
    if expected==1 or name=='inline-no-risk':assert len(selected)==1,result
    return result


def main():
    admission='申请人发现不符合早期药物研发程序纳入条件时,应当及时终止该程序。'
    term='管理机构对早期药物研发程序的资格进行审核,对符合终止程序情形的,应当予以终止。'
    risk='1.药物不再具备治疗效果优势。\n2.因药物重大安全性问题而终止临床试验。'
    no_risk='1.药物不再具备治疗效果优势。\n2.申请人不再从事该项研发。'
    admission_risk='1.药物临床研究应有治疗效果证据。\n2.与现有治疗相比,该药物具有显著的安全性优势。'
    rows=[case('old-valid-newline',risk,term,1,termination=True),
          case('actual-inline-layout',risk,term,1,termination=True,inline=True),
          case('mixed-inline-and-newline',risk,term,1,termination=True,inline=True,mixed=True),
          case('inline-ascii-colon',risk,term,1,termination=True,inline=True,punctuation=': '),
          case('inline-no-risk',no_risk,term,0,termination=True,inline=True),
          case('inline-pure-paperwork',risk,'申请人应当核验早期药物研发程序申请材料格式是否符合递交条件。',0,termination=True,inline=True),
          case('inline-status-only',risk,'该药品已纳入早期药物研发程序,现不再符合纳入条件。',0,termination=True,inline=True),
          case('prose-mention-not-heading',risk,term,0,termination=True,inline=True,mention=True),
          case('inline-unlinked-fulltext',risk,term,0,linked=False,termination=True,inline=True),
          case('inline-cross-leaf',risk,term,1,termination=True,inline=True,split=True),
          case('inline-admission',admission_risk,admission,1,inline=True)]
    p=Path(__file__).parent/'generic-boundary-check-results.json'
    with p.open('x') as f:json.dump({'check_N':len(rows),'passed':True,'cases':rows,'not_actual_cohort_inference':True,'same_line_layout_based_on_previously_verified_source':True,'no_research_reference_rows_used':True},f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'generic_check_N':len(rows),'passed':True},ensure_ascii=False))

if __name__=='__main__': main()
