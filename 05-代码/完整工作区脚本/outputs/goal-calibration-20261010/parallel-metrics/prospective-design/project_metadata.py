"""One-time, metadata-only projection. Never outputs source text or coding reasons."""
from pathlib import Path
import json, hashlib
from collections import Counter

ROOT = Path('/PROJECT_ROOT')
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/goal-calibration-20261010'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def save(p, d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def main():
    if (OUT/'source-bindings.json').exists():
        raise RuntimeError('Projection already frozen; do not overwrite.')
    adopt=ROOT/'outputs/编码修订核查-20261008/整套编码采用记录.json'
    binding=json.loads(adopt.read_text())
    sources={
        'adoption_record':adopt,
        'frame':BASE/'00-baseline/source-only-frame.jsonl',
        'exposure':BASE/'01-review/exposure-ids.json',
        'exposure_audit':BASE/'01-review/exposure-audit-sol.json',
        'design_json':BASE/'01-review/validation-design-sol.json',
        'design_md':BASE/'01-review/validation-design-sol.md',
        'rules39':Path(binding['rules']['path']),
        'LLM03':Path(binding['LLM']['path']),
    }
    info={k:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for k,p in sources.items()}
    for key,ak in [('rules39','rules'),('LLM03','LLM')]:
        assert info[key]['sha256']==binding[ak]['sha256']
    exposure=json.loads(sources['exposure'].read_text())
    assert exposure['frame_sha256']==info['frame']['sha256']
    excluded=set(exposure['excluded_ids']);direct=set(exposure['direct_exposure_ids'])
    metadata={}
    with sources['frame'].open() as f:
        for line in f:
            row=json.loads(line)
            # Whitelist only. Source body, context, evidence, reasons never copied.
            rid=row['id']; assert rid not in metadata
            metadata[rid]={'id':rid,'department':row['analysis_group'],
                           'family':row['normalized_text_family']['family_id'],
                           'exposure':'direct' if rid in direct else 'family_only' if rid in excluded else 'remaining'}
    assert len(metadata)==4481 and excluded<=metadata.keys() and direct<=excluded
    qa={}
    for key in ['rules39','LLM03']:
        seen=set();target=set();extra=[];labels_na=Counter();bad=[];counts=Counter();versions=Counter()
        with sources[key].open() as f:
            for line_no,line in enumerate(f,1):
                row=json.loads(line);rid=row['id'];assert rid not in seen
                seen.add(rid)
                if rid not in metadata:
                    extra.append(rid);continue
                pred=row.get('prediction',row)
                labels=pred.get('labels',{})
                projected={}
                for dim in DIMS:
                    val=labels.get(dim)
                    if type(val) is int and val in (0,1):
                        projected[dim]=val;counts[(dim,str(val))]+=1
                    else:
                        projected[dim]=None;labels_na[dim]+=1
                        bad.append({'id':rid,'dimension':dim,'line':line_no,'type':type(val).__name__})
                metadata[rid][key]=projected;target.add(rid)
                if key=='rules39':versions[pred.get('version','MISSING')]+=1
        missing=sorted(metadata.keys()-target)
        for rid in missing:metadata[rid][key]={dim:None for dim in DIMS}
        qa[key]={'all_unique_rows':len(seen),'target_rows':len(target),'non_target_rows':len(extra),
                 'missing_target_ids':missing,'invalid_or_NA_by_dimension':dict(labels_na),
                 'invalid_or_NA_locations':bad,'rule_version_counts':dict(versions),
                 'positive_by_dimension':{d:counts[(d,'1')] for d in DIMS},
                 'negative_by_dimension':{d:counts[(d,'0')] for d in DIMS}}
        assert len(seen)==binding['rules' if key=='rules39' else 'LLM']['n']==4924
        assert len(target)==4481 and len(extra)==443 and not missing
    projected=OUT/'inputs/metadata-and-fixed-labels.jsonl'
    projected.write_text(''.join(json.dumps(metadata[rid],ensure_ascii=False,sort_keys=True)+'\n' for rid in sorted(metadata)))
    eligible=[r for r in metadata.values() if r['exposure']=='remaining']
    assert len(eligible)==1444
    assert Counter(r['department'] for r in eligible)==Counter({'NMPA':778,'NHSA':562,'NHC':104})
    summary={
        'target_N':len(metadata),'remaining_N':len(eligible),
        'remaining_department_N':dict(Counter(r['department'] for r in eligible)),
        'remaining_families':len({r['family'] for r in eligible}),
        'target_exposure_counts':dict(Counter(r['exposure'] for r in metadata.values())),
        'remaining_positive_counts':{m:{d:sum(r[m][d]==1 for r in eligible) for d in DIMS} for m in ['rules39','LLM03']},
        'remaining_NA_counts':{m:{d:sum(r[m][d] is None for r in eligible) for d in DIMS} for m in ['rules39','LLM03']},
    }
    save(OUT/'source-bindings.json',{
        'status':'metadata_auxiliary_projection_frozen_only__final_execution_not_frozen',
        'date':'2026-10-10','model':'GPT-6.1 Sol','reasoning_effort':'ultra',
        'sources':info,'adoption_status':binding['status'],'QA':qa,'summary':summary,
        'projection':{'path':str(projected),'sha256':sha(projected),'bytes':projected.stat().st_size,
                      'permitted_fields':['id','department','family','exposure','rules39.{S,E,Ec,I,F}','LLM03.{S,E,Ec,I,F}'],
                      'prohibited_content_written':False,
                      'mechanism':'JSON decode for whitelist projection; no body, context, reason, evidence or human label is accessed semantically or emitted.'},
        'interpretation':'Historical adopted predictions are frozen sampling auxiliaries, not final new-manual outputs or human truth. Remaining pool inference excludes the 3037 developed/exposed records.'
    })
    print(json.dumps({'projection_QA':qa,'summary':summary},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
