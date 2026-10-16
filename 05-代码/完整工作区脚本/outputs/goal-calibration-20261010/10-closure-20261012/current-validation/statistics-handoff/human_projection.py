"""Re-read original human bytes after authority/time gates; never invent labels.

Issued200 XLSX reader and JSON five-state projection are sealed old helpers.
Only their pure read/normalization functions are used, not old metadata gates.
"""
from collections import Counter
from support import require,verify,load,jsonlines,module,canonical,binding
from dynamic_xlsx_projection import read_workbook,project_dynamic_xlsx
DIMS=('S','E','Ec','I','F')

def legacy_control(person,deps,source,synthetic):
    reader=module('_unchanged_issued200_reader',deps['legacy_reader'])
    if synthetic:
        cb=load(verify(source['synthetic_xlsx_control']))
        require(cb.get('synthetic_only')is True,'TOY XLSX control must be synthetic')
        template=read_workbook(reader,verify(cb['template']).read_bytes())['独立初判']['cells']
        bundle=cb['bundle']
        require(len(bundle)==200 and all(k.startswith('TOY-')for k in bundle),'Synthetic legacy XLSX must use200 TOY blind IDs')
    else:
        require('synthetic_xlsx_control'not in source,'Synthetic XLSX control prohibited in actual path')
        rb=load(verify(deps['legacy_receiver_bindings']))
        require(rb['vendor']==deps['legacy_reader'],'Original reader binding differs')
        template=read_workbook(reader,verify(rb['template_inputs'][person]).read_bytes())['独立初判']['cells']
        pages=load(verify(rb['materials']))['pages']
        bundle={r['blind_id']:r['source_bundle_sha256']for r in pages if r['side']==person}
    return reader,{'spec':{'worksheet':'独立初判'},'cells':template,'source':set(bundle),'bundle':bundle,'bids':set(bundle)}

def project_xlsx(person,source,receipt,view,frame,deps,synthetic):
    require(source['format']=='issued200_xlsx','Inherited original200 must retain issued XLSX format')
    require(source['raw_binding']==receipt['raw_first_submission_binding'],'Inherited original bytes differ from reviewed receipt')
    reader,control=legacy_control(person,deps,source,synthetic)
    checked,derived=reader.inspect(person,verify(source['raw_binding']).read_bytes(),control)
    require(checked.get('content_valid')is True,'Issued XLSX content/identity invalid; no statistic emitted')
    cells={(r['blind_id'],r['dimension']):r for r in derived}
    require(len(cells)==1000,'Legacy XLSX unique1000 slots required')
    out={}; statuses=Counter()
    for row in receipt['projection']['rows']:
        uid,bid=row['unit_id'],row['original_blind_id']
        require(control['bundle'].get(bid)==frame[uid]['source_identity_sha256'],'Inherited material SHA differs from frozen current unit')
        labels={};ds={}; unfinished=0
        for dim in DIMS:
            c=cells[bid,dim];st=c['completion_status'];statuses[st]+=1
            require(st in ('filled','lawful_null','unfilled','incomplete'),'Unsupported human cell state')
            labels[dim]=c['value']
            if st in ('unfilled','incomplete'):
                require(c['value']is None,'Unfinished cell carries a value')
                ds[dim]='execution_failure';unfinished+=1
        if unfinished==5: output=None
        else:
            output={'status':'completed','labels':labels}
            if ds: output.update(dimension_status=ds,failure_code='unfilled_or_incomplete_original_human_slot')
        out[uid]=output
    return out,{'original':source['raw_binding'],'unchanged_reader':deps['legacy_reader'],
                'all200_content_valid':True,'projected_slot_statuses':dict(statuses),
                'unfinished_never_imputed_or_silently_dropped':True}

def project_json(source,receipt,assignments,frame,identity_code,helper,synthetic):
    require(source['format']=='blind_five_slot_jsonl_v1','Use actual explicit human JSONL slot format')
    require(source['raw_binding']==receipt['raw_first_submission_binding'],'Human raw bytes differ from reviewed original')
    raw=jsonlines(verify(source['raw_binding']))
    expected=[r['original_blind_id']for r in assignments]
    require(len(raw)==len(assignments)and[r.get('blind_id')for r in raw]==expected and len(set(expected))==len(expected),'Actual human assigned IDs/order must match complete fixed projection')
    out={}
    for row,assigned in zip(raw,assignments):
        uid=assigned['unit_id']
        require(uid.startswith('TOY-')==synthetic,'Synthetic human source identity differs')
        identity={'source_bundle_sha256':frame[uid]['source_identity_sha256']}
        out[uid]=helper.reference_output(row,identity,{identity_code})
    return out,{'original':source['raw_binding'],'unchanged_projection':'handoff.reference_output',
                'every_assigned_row_retained':True}

def project_humans(reuse,view,sources,frame,deps,*,synthetic):
    helper=module('_unchanged_human_slot_projection',deps['legacy_handoff'])
    output={};proof={}
    for person in ('A','B'):
        require(set(sources[person])=={'inherited','supplement'},'Both original cohorts must be supplied')
        p=reuse['human_receipts'][person];out={};details={}
        for group in ('inherited','supplement'):
            receipt=p['cohorts'][group];source=sources[person][group]
            if group=='inherited': result,evidence=project_xlsx(person,source,receipt,view,frame,deps,synthetic)
            elif source['format']=='frozen_dynamic_xlsx':
                require(source['raw_binding']==receipt['raw_first_submission_binding'],'Supplement original Excel differs from reviewed first bytes')
                assignments=[{'unit_id':r['unit_id'],'original_blind_id':r['original_blind_id'],
                              'source_bundle_sha256':frame[r['unit_id']]['source_identity_sha256']}for r in receipt['projection']['rows']]
                reader=module('_unchanged_dynamic_excel_normalizer',deps['legacy_reader'])
                result,evidence=project_dynamic_xlsx(source['raw_binding'],source['template_binding'],assignments,reader)
            else: result,evidence=project_json(source,receipt,receipt['projection']['rows'],frame,p['identity_code'],helper,synthetic)
            require(not(set(out)&set(result)),'Census and supplementary human rows overlap')
            out.update(result);details[group]=evidence
        output[person]=out;proof[person]=details
    if reuse['stage']=='machine_reference':
        ref=reuse['human_receipts']['reference'];source=sources['reference']
        assignments=source['assignments']
        require([r['unit_id']for r in assignments]==ref['unit_ids'],'Credible reference must preserve all assigned IDs/order')
        output['reference'],proof['reference']=project_json(source,ref,assignments,frame,ref['identity_code'],helper,synthetic)
    else: require('reference'not in sources,'Do not ingest unused human reference at human_first stage')
    return output,proof
