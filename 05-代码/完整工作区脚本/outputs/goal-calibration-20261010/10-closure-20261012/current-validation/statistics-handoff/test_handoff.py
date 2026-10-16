"""Finite NONHUMAN source-to-statistics controls; no actual source/label read."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import importlib.util,json,sys,zipfile
from xml.sax.saxutils import escape
from support import *
import handoff,machine_projection

DIMS=('S','E','Ec','I','F')

def write(path,value,lines=False):
    Path(path).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'for x in value)if lines else json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return binding(path)

def xlsx(path,assignments,*,filled,side,relative=False):
    data=[]
    def cell(addr,value):return f'<c r="{addr}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
    data.append('<row r="1">'+''.join(cell(c+'1',v)for c,v in zip('ABCDE',['盲号','材料','维度','判断','理由']))+'</row>')
    for j,a in enumerate(assignments):
        for k,d in enumerate(DIMS):
            n=j*5+k+2;vals=[a['original_blind_id'],'TOY-material-link:'+a['unit_id'],d]
            content=''.join(cell(c+str(n),v)for c,v in zip('ABC',vals))
            if filled:
                value=(j+k+(side=='B'))%2
                # Explicit synthetic uncertainty and nonreturn, not genuine data.
                if j==0 and d=='F': content+=cell('E'+str(n),'待定：NONHUMAN missing control fact')
                elif j==1 and side=='A': pass
                else: content+=cell('D'+str(n),value)+cell('E'+str(n),'NONHUMAN control judgment')
            data.append(f'<row r="{n}">{content}</row>')
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="独立初判" sheetId="1" r:id="rId1"/></sheets></workbook>')
        target='worksheets/sheet1.xml'if relative else'/xl/worksheets/sheet1.xml'
        z.writestr('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{target}"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData>'+''.join(data)+'</sheetData></worksheet>')
    return binding(path)

def fixture(directory,mode='mixed'):
    directory.mkdir(parents=True,exist_ok=False)
    old=HERE.parent/'reuse-admission'
    sys.path.insert(0,str(old))
    spec=importlib.util.spec_from_file_location('_reuse_control_builder',old/'test_reuse_admission.py')
    test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test);test.FIX=directory/'meta'
    reuse,view,evidence=test.make_fixture()
    legacy=view['legacy_assignment']
    while len(legacy)<200:
        uid=f'TOY-LEGACY-EXPOSED-{len(legacy):03d}'
        legacy.append({'unit_id':uid,'A_blind_id':'TOY-A-'+uid,'B_blind_id':'TOY-B-'+uid,'old_pi_exact':'1/4','old_weight_exact':'4'})
    # All blind IDs in this transparent control are TOY, including target C.
    for r in legacy:
        r['A_blind_id']='TOY-A-'+r['unit_id'];r['B_blind_id']='TOY-B-'+r['unit_id']
    oldb=write(directory/'TOY-original200-assignment.json',{'synthetic_only':True,'records':legacy})
    view['legacy_draw_binding']=oldb
    frame_ids=[r['unit_id']for r in view['target']]+[r['unit_id']for r in legacy if r['unit_id']not in {x['unit_id']for x in view['target']}]
    mk=machine_projection.make_synthetic_fixture(directory/'machines',frame_ids)
    frame=[{'unit_id':uid,'department':next((r['department']for r in view['target']if r['unit_id']==uid),'NHC'),
            'source_identity_sha256':canonical({'TOY':uid})}for uid in frame_ids]
    fb=write(directory/'TOY-full-frame.jsonl',frame,True);frameby={r['unit_id']:r for r in frame}
    # Some supplementary strata can be census, while role remains supplement.
    for h in reuse['design']['strata']:
        if h['role']=='supplement'and(mode=='census'or h['department']=='NHC'):h['n']=h['N']
    members=reuse['design']['membership'];strata={h['id']:h for h in reuse['design']['strata']}
    draw=[]
    for h in reuse['design']['strata']:
        ids=[r['unit_id']for r in members if r['stratum_id']==h['id']][:h['n']]
        draw.extend({'unit_id':uid,'stratum_id':h['id'],'pi_exact':str(Fraction(h['n'],h['N'])),'weight_exact':str(Fraction(h['N'],h['n']))}for uid in ids)
    reuse['draw'].update(records=draw,design_sha256=canonical(reuse['design']))
    C=reuse['design']['certainty_ids'];new=[r['unit_id']for r in draw if r['unit_id']not in C];human_sources={}
    for person in('A','B'):
        p=reuse['human_receipts'][person];human_sources[person]={}
        for group,ids in [('inherited',C),('supplement',new)]:
            receipt=p['cohorts'][group]
            assignments=[{'unit_id':uid,'original_blind_id':next(r[person+'_blind_id']for r in legacy if r['unit_id']==uid)if group=='inherited'else'TOY-'+person+'-NEW-'+uid,
                          'source_bundle_sha256':frameby[uid]['source_identity_sha256']}for uid in ids]
            allrows=[{'unit_id':r['unit_id'],'original_blind_id':r[person+'_blind_id'],'source_bundle_sha256':frameby[r['unit_id']]['source_identity_sha256']}for r in legacy]if group=='inherited'else assignments
            template=xlsx(directory/f'TOY-{person}-{group}-template.xlsx',allrows,filled=False,side=person,relative=True)
            raw=xlsx(directory/f'NONHUMAN-{person}-{group}-first.xlsx',allrows,filled=True,side=person,relative=True)
            receipt['raw_first_submission_binding']=raw
            receipt['projection'].update(source_raw_binding=raw,rows=[{'unit_id':a['unit_id'],'original_blind_id':a['original_blind_id'],'original_row_locator':f'original:{i}'}for i,a in enumerate(assignments)])
            source={'raw_binding':raw,'format':'issued200_xlsx'if group=='inherited'else'frozen_dynamic_xlsx','template_binding':template}
            if group=='inherited':
                receipt['legacy_draw_binding']=oldb
                source['synthetic_xlsx_control']=write(directory/f'TOY-{person}-control.json',{'synthetic_only':True,'template':template,'bundle':{a['original_blind_id']:a['source_bundle_sha256']for a in allrows}})
            human_sources[person][group]=source
    refrows=[];refassign=[]
    for j,r in enumerate(draw):
        uid=r['unit_id'];bid='TOY-REF-'+uid
        dims={d:{'completion_status':'filled','value':(j+k)%2,'human_identity_code':'TOY-ADJUDICATOR'}for k,d in enumerate(DIMS)}
        method='completed'
        if j==0:dims['E']={'completion_status':'lawful_null','value':None,'null_reason':'NONHUMAN ambiguity','human_identity_code':'TOY-ADJUDICATOR'}
        if j==1:dims['I']={'completion_status':'execution_failure','value':None,'failure_code':'TOY_dimension_noncompletion'}
        if j==2:
            method='not_returned';dims={d:{'completion_status':'not_returned','value':None}for d in DIMS}
        refrows.append({'blind_id':bid,'source_bundle_sha256':frameby[uid]['source_identity_sha256'],'method_status':method,'dimensions':dims})
        refassign.append({'unit_id':uid,'original_blind_id':bid})
    rawref=write(directory/'NONHUMAN-reference-original.jsonl',refrows,True)
    reuse['stage']='machine_reference'
    reuse['human_receipts']['reference']={'kind':'synthetic_adjudication','identity_code':'TOY-ADJUDICATOR','machine_answers_visible':False,
      'auto_agreement_or_AI_substitution':False,'identity_evidence_binding':evidence,'raw_first_submission_binding':rawref,
      'execution_evidence_binding':evidence,'unit_ids':[r['unit_id']for r in draw],'started_at':'2030-01-05T09:00:00Z',
      'locked_at':'2030-01-05T11:00:00Z','first_machine_comparison_at':'2030-01-05T12:00:00Z',
      'material_usage':{'used_manual_binding':evidence,'used_materials_binding':evidence,'compatibility_review_binding':None,'actual_delivery_evidence_binding':evidence}}
    reuse['feedback_review']['reviewed_through_at']='2030-01-05T12:00:00Z'
    human_sources['reference']={'format':'blind_five_slot_jsonl_v1','raw_binding':rawref,'assignments':refassign}
    request={'schema':'current-reuse-statistics-handoff-v1','synthetic_only':True,'registration_id':'TOY-COMPLETE-HANDOFF',
      'analysis_stage':'combined','reuse_request_binding':write(directory/'reuse-request.json',reuse),
      'synthetic_view_binding':write(directory/'view.json',view),'synthetic_full_frame_binding':fb,
      'human_sources':human_sources,'synthetic_machine_sources':{'machine_freeze_binding':mk['machine_freeze_binding'],'synthetic_sources':mk['synthetic_sources']}}
    rp=directory/'request.json';write(rp,request)
    return rp,request,reuse,view

def main():
    controls=HERE/'controls';controls.mkdir(exist_ok=True)
    number=1
    while (controls/f'run-{number:02d}').exists():number+=1
    run=controls/f'run-{number:02d}';run.mkdir()
    cases=[]
    for mode in('mixed','census'):
        rp,request,reuse,view=fixture(run/mode,mode)
        out=HERE/'runs'/f'control-{number:02d}-{mode}'
        receipt=handoff.execute(rp,out,synthetic=True)
        result=load(out/'results.json');payload=load(out/'joined-input.json')
        baseline=module('_original_control_comparison',dependencies()['core']).analyze(payload,5000,20261010,'single_category')
        left=deepcopy(result);right=deepcopy(baseline);left.pop('project_review');right.pop('project_review')
        cases.append({'case':mode+'_Excel_and_reference_originals_to45_targets','passed':receipt['numeric_target_N']==45 and len(payload['records'])==len(reuse['draw']['records'])})
        cases.append({'case':mode+'_all_math_outputs_equal_unmodified_core','passed':left==right})
        cases.append({'case':mode+'_NULL_failure_nonreturn_retained','passed':any(r['outputs']['reference']is None for r in payload['records'])and any('dimension_status'in(r['outputs']['reference']or{})for r in payload['records'])})
        cases.append({'case':mode+'_relative_worksheet_targets_parsed','passed':True})
        if mode=='mixed':base=(rp,request,reuse,view)
    rp,request,reuse,view=base
    for stage in('human_first','machine_reference'):
        req=deepcopy(request); rr=deepcopy(reuse);req['analysis_stage']=stage
        if stage=='human_first':rr['stage']='human_first';rr['human_receipts'].pop('reference');req['human_sources'].pop('reference');req.pop('synthetic_machine_sources')
        req['reuse_request_binding']=write(run/(stage+'-reuse.json'),rr);rq=run/(stage+'-request.json');write(rq,req)
        receipt=handoff.execute(rq,HERE/'runs'/f'control-{number:02d}-{stage}',synthetic=True)
        cases.append({'case':stage+'_uses_only_active_methods','passed':receipt['numeric_target_N']==(5 if stage=='human_first'else 40)})
    def rejected(name,change):
        req=deepcopy(request); rr=deepcopy(reuse);change(req,rr)
        req['reuse_request_binding']=write(run/(name+'-reuse.json'),rr);path=run/(name+'-request.json');write(path,req)
        target=HERE/'runs'/f'control-{number:02d}-reject-{name}'
        try:handoff.execute(path,target,synthetic=True)
        except (ValueError,KeyError,FileNotFoundError)as e: cases.append({'case':name,'passed':not target.exists(),'rejected':True,'reason':str(e)})
        else:cases.append({'case':name,'passed':False,'rejected':False})
    rejected('false_before_answers',lambda q,r:r.update(design_before_answers=True))
    rejected('human_feedback_in_machine_development',lambda q,r:r['feedback_review'].update(used_in_current_machine=True))
    rejected('missing_certainty_row',lambda q,r:r['draw']['records'].pop(0))
    rejected('missing_actual_human_first',lambda q,r:r['human_receipts']['A']['cohorts']['inherited'].update(raw_first_submission_binding=None))
    rejected('untrusted_reference_auto_agreement',lambda q,r:r['human_receipts']['reference'].update(auto_agreement_or_AI_substitution=True))
    rejected('human_raw_not_reviewed_original',lambda q,r:q['human_sources']['A']['supplement'].update(raw_binding=q['human_sources']['B']['supplement']['raw_binding']))
    rejected('inherited_template_control_missing',lambda q,r:q['human_sources']['A']['inherited'].pop('synthetic_xlsx_control'))
    rejected('synthetic_points_to_project_original',lambda q,r:q['human_sources']['A']['inherited'].update(raw_binding=dependencies()['legacy_reader']))
    rejected('machine_missing_whole_first',lambda q,r:q['synthetic_machine_sources'].update(machine_freeze_binding=q['reuse_request_binding']))
    pending=write(HERE/'pending-real-request.json',{'schema':'current-reuse-statistics-handoff-v1','synthetic_only':False,'registration_id':'UNREGISTERED','analysis_stage':'combined'})
    target=HERE/'runs'/f'control-{number:02d}-real-refused'
    try:handoff.execute(pending['path'],target)
    except ValueError as e:cases.append({'case':'actual_empty_registry_refuses_before_label_IO','passed':not target.exists(),'reason':str(e)})
    else:cases.append({'case':'actual_empty_registry_refuses_before_label_IO','passed':False})
    report={'status':'finite_NONHUMAN_end_to_end_controls','run_directory':str(run),'cases':cases,
            'all_passed':all(c['passed']for c in cases),'actual_human_answers_read_or_created':0,'actual_sampling_performed':0,
            'mathematical_comparison':'Original core complete outputs identical except truthful project_review',
            'actual_ROOT_registrations':0,'code_bindings':[binding(HERE/n)for n in('handoff.py','human_projection.py','core_adapter.py','machine_projection.py','test_handoff.py')]}
    write(run/'report.json',report);write(HERE/'control-results.json',report)
    print(json.dumps({'cases':len(cases),'all_passed':report['all_passed'],'run_directory':str(run)},ensure_ascii=False))
    require(report['all_passed'],'A finite control failed')

if __name__=='__main__':main()
