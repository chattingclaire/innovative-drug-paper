"""New material identity, existing strict schema/seal guard, observable literal reads.

Read-only. No output modification, semantic grading or provider identity assertion.
"""
import argparse, hashlib, json, re, types
from pathlib import Path
BASE=Path(__file__).resolve().parent

def binding(path):
    p=Path(path).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(path):
    def unique(pairs):
        d={}
        for k,v in pairs:assert k not in d,'Duplicate JSON key';d[k]=v
        return d
    def invalid(x):raise ValueError('Nonfinite JSON '+x)
    return json.loads(Path(path).read_bytes(),object_pairs_hook=unique,parse_constant=invalid)
def exact(x):assert binding(x['path'])=={k:x[k] for k in ('path','bytes','sha256')},'Changed binding'
def module(x):
    exact(x);m=types.ModuleType('frozen_read_only_receiver');m.__file__=x['path'];exec(compile(Path(x['path']).read_bytes(),x['path'],'exec'),m.__dict__);return m
def covers(ranges,length):
    cursor=0
    for a,b in sorted(ranges):
        if a>cursor:return False
        cursor=max(cursor,b)
    return cursor>=length

def observable_reads(assignment_path,first_path,events,submit_helper):
    a=load(assignment_path);first=load(first_path);fh=binding(first_path);marker='FIRST_CREATED '+fh['path']+' '+fh['sha256']
    outs=[(i,e['item']) for i,e in enumerate(events) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
    writers=[(i,it) for i,it in outs if marker in it.get('aggregated_output','') and str(submit_helper) in it.get('command','') and it.get('exit_code')==0]
    assert len(writers)==1,'Unique successful exclusive submission event absent'
    writer=writers[0][0];presented={};rejected=[]
    allowed={binding(assignment_path)['path']:binding(assignment_path)}
    for key,value in a.items():
        if key=='common_source_jsonl_identity_only':continue
        if isinstance(value,dict) and {'path','bytes','sha256'}<=set(value):allowed[value['path']]={k:value[k] for k in ('path','bytes','sha256')}
    for value in a['packets']+a['source_asset_bindings']:allowed[value['path']]={k:value[k] for k in ('path','bytes','sha256')}
    # Only complete, successful pre-first tool output counts; truncation requires new presentation.
    header=re.compile(r'^PRESENTATION (\{[^\n]+\})\n',re.M)
    for i,it in outs:
        if i>=writer or it.get('exit_code')!=0:continue
        output=it.get('aggregated_output','')
        if re.search(r'Warning: truncated output|\d+ tokens truncated|\d+ lines omitted|\d+ characters omitted',output,re.I):rejected.append(i);continue
        for h in header.finditer(output):
            p=json.loads(h.group(1));end='\nEND_PRESENTATION '+p['presentation_event'];b=output.find(end,h.end())
            if b<0:continue
            assert allowed.get(p['path'])=={k:p[k] for k in ('path','bytes','sha256')},'Event presentation outside frozen assignment'
            exact(p);text=Path(p['path']).read_bytes().decode('utf8');assert p['range_kind']=='unicode_code_points' and type(p['start']) is int and type(p['end']) is int
            assert 0<=p['start']<p['end']<=len(text) and p['end']-p['start']<=6500
            assert p['presentation_event']=='present:'+p['sha256']+':'+str(p['start'])+':'+str(p['end'])
            assert output[h.end():b]==text[p['start']:p['end']],'Presented literal differs from bound interval'
            presented.setdefault(p['path'],[]).append(dict(start=p['start'],end=p['end'],presentation_event=p['presentation_event'],event_index=i,item_id=it['id']))
    required=[binding(assignment_path),*[a[k] for k in ('manual','execution_prompt','actor_instructions','output_schema','output_validation_contract','campaign_scope_metadata_binding')],*a['packets']]
    checks=[]
    for b in required:
        exact(b);length=len(Path(b['path']).read_bytes().decode('utf8'));real=presented.get(b['path'],[])
        assert covers([(r['start'],r['end']) for r in real],length),'Observable required full-file coverage absent: '+b['path']
        checks.append(dict(path=b['path'],unicode_N=length,observed_ranges=real))
    declared={e['path']:e for e in first['read_manifest']['files']}
    for b in [a['manual'],a['execution_prompt'],*a['packets']]:
        claim=declared[b['path']]
        for r in claim['actual_presented_ranges']:
            assert r['range_kind']=='unicode_code_points','Use auditable Unicode presentation helper for mandatory files'
            assert any(all(t[k]==r[k] for k in ('start','end','presentation_event')) for t in presented[b['path']]),'Declared interval not in actual pre-first output'
    prep_max=max(r['event_index'] for b in (a['manual'],a['execution_prompt']) for r in presented[b['path']])
    previous=prep_max
    for b in a['packets']:
        indices=[r['event_index'] for r in presented[b['path']]]
        assert min(indices)>previous,'Manual/prompt before packet and original packet order violated'
        previous=max(indices)
    for r in first['records']:
        for d in r['dimensions'].values():
            for ev in d['evidence']:
                if 'asset_path' in ev:
                    ranges=presented.get(ev['asset_path'],[]);text=Path(ev['asset_path']).read_bytes().decode('utf8')
                    assert any(ev['quote'] in text[t['start']:t['end']] for t in ranges),'Supplemental asset quote lacks observable literal range'
    return dict(first_creation_event_index=writer,required_file_N=len(checks),required_files=checks,truncated_events_not_counted=rejected,observable_complete_text_presentations=True,provider_context_delivery_or_serving_identity_independently_verified=False)

def verify(manifest_path,assignment_path,first_path):
    m=load(manifest_path);exact(m['receiver']);assert m['receiver']==binding(__file__)
    result=module(m['base_guard']).verify(manifest_path,assignment_path,first_path,require_explicit_template_false=True)
    process=load(Path(first_path).parent/'process-completion.json');events=[json.loads(x) for x in Path(process['events']['path']).read_text().splitlines()]
    observed=observable_reads(assignment_path,first_path,events,m['submit_helper']['path'])
    seal=load(Path(first_path).parent/'seal.json');a=load(assignment_path);inputs={b['path'] for b in seal['actual_input_bindings']}
    assert {str(Path(assignment_path).resolve()),a['manual']['path'],a['execution_prompt']['path'],a['actor_instructions']['path'],a['output_schema']['path'],a['output_validation_contract']['path'],a['campaign_scope_metadata_binding']['path'],*[p['path'] for p in a['packets']]}<=inputs,'Actual actor receipt missing mandatory inputs'
    return dict(state='technical_valid_whole_batch',run_id=a['run_id'],batch_id=a['batch_id'],first=result['first'],actor_seal=result['actor_seal'],base_strict_reception=result,observable_readback=observed,legal_null_is_valid_without_retry=True,semantic_correctness_checked=False,new_v16_material_delta=True,independent_stability_repeat=False,provider_serving_model_verified=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--assignment',required=True);p.add_argument('--submission',required=True);x=p.parse_args();print(json.dumps(verify(x.manifest,x.assignment,x.submission),ensure_ascii=False,indent=2))
