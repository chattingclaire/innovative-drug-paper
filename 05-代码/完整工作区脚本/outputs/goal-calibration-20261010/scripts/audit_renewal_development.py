"""Audit sealed same-source AI rejudgments; never recode source labels."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DIMS = ['S', 'E', 'Ec', 'I', 'F']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_rows(p):
    return [json.loads(line) for line in Path(p).read_text().splitlines() if line.strip()]

def fraction(a, b):
    return None if not b else float(Fraction(a, b))

def calculate(left, right, dimension):
    cells = Counter((left[k]['labels'][dimension], right[k]['labels'][dimension]) for k in left)
    tp, fp, fn, tn = (cells[1, 1], cells[1, 0], cells[0, 1], cells[0, 0])
    n = tp + fp + fn + tn
    po = Fraction(tp+tn, n) if n else None
    pe = Fraction((tp+fp)*(tp+fn)+(tn+fn)*(tn+fp), n*n) if n else None
    kappa = None if po is None or pe == 1 else float((po-pe)/(1-pe))
    return {'assigned_n':len(left),'comparable_n':n,'four_cells':dict(TP=tp,FP=fp,FN=fn,TN=tn),
            'unknown_n':len(left)-n,'Po':None if po is None else float(po),
            'Pe':None if pe is None else float(pe),'kappa':kappa,
            'kappa_NA_reason':'both sides constant; Pe=1' if pe==1 else None,
            'precision':fraction(tp,tp+fp),'recall':fraction(tp,tp+fn),
            'F1':fraction(2*tp,2*tp+fp+fn),'Ppos':fraction(2*tp,2*tp+fp+fn),
            'Pneg':fraction(2*tn,2*tn+fp+fn),'specificity':fraction(tn,tn+fp),
            'NPV':fraction(tn,tn+fn),'CI95':None,
            'CI_reason':'two historically exposed nonprobability development records',
            'full_3x3':{f'{a}|{b}':cells[a,b] for a in [0,1,None] for b in [0,1,None]}}

def main():
    plan = json.loads((ROOT/'04-calibration/renewal-rejudge-v11/admin/design.json').read_text())
    source = {x['id']:x for x in load_rows(plan['source']['path'])}
    for key in ['source','manual','resource']:
        assert sha(plan[key]['path']) == plan[key]['sha256']
    for a in plan['source_page_assets']:
        assert sha(a['path']) == a['sha256']
    locations = {
        'A':(ROOT/'04-calibration/renewal-rejudge-v11/A','output-seal.json','labels.jsonl'),
        'B':(ROOT/'04-calibration/renewal-rejudge-v11/B','delivery-seal.json','labels.jsonl'),
        'native_LLM':(ROOT/'06-coding/native-llm41-sol/renewal-rejudge','seal.json','predictions.jsonl')}
    seals, parsed, issues = {}, {}, []
    for name,(base,seal_name,data_name) in locations.items():
        seal = json.loads((base/seal_name).read_text())
        checks=[]
        for f in seal['files']:
            path = Path(f.get('absolute_path') or f.get('path') or base/f['name'])
            assert sha(path)==f['sha256'] and path.stat().st_size==f['bytes']
            checks.append(str(path))
        all_metadata = json.dumps(seal)+ (base/'submission.json').read_text()
        for key in ['source','manual','resource']:
            assert plan[key]['sha256'] in all_metadata, (name,key)
        items=load_rows(base/data_name)
        if name=='B':
            binding=json.loads((base/'id-map.json').read_text())['mapping']
            aliases={v['output_blind_id']:v['source_id'] for v in binding}
            raw={json.loads(line)['id']:line for line in Path(plan['source']['path']).read_text().splitlines()}
            for m in binding:
                assert hashlib.sha256(raw[m['source_id']].encode()).hexdigest()==m['raw_jsonl_row_sha256_excluding_line_ending']
            items=[{**x,'id':aliases[x['blind_id']]} for x in items]
        if name=='native_LLM':
            assert sha(base/'first-judgments.jsonl')==sha(base/data_name)
        assert len(items)==2 and {x['id']for x in items}==set(source)
        parsed[name]={x['id']:x for x in items}
        for x in items:
            assert set(x['labels'])==set(DIMS)
            contexts={c['context_id']:c for c in source[x['id']]['contexts']}
            for dim in DIMS:
                value=x['labels'][dim];assert value is None or type(value)is int and value in [0,1]
                ev=x['evidence'][dim]
                assert ev['current_quote']==source[x['id']]['text'] and ev['reason']
                assert 'value' not in ev or ev['value']==value
                for q in ev.get('contexts_used',[]):
                    c=contexts[q['context_id']]
                    available=[c[k]for k in ['text','headers','row_cells','caption','title']if isinstance(c.get(k),str)]
                    available += [v for k in ['headers','row_cells']for v in (c.get(k)or[])if isinstance(v,str)]
                    quote=q['quote']
                    if quote is None and not available:continue
                    if not quote or not any(quote in text for text in available):
                        issues.append(dict(coder=name,id=x['id'],dimension=dim,quote=quote))
        seals[name]={'path':str(base/seal_name),'sha256':sha(base/seal_name),'files_verified_n':len(checks),
                     'predictions_sha256':sha(base/data_name)}
    assert not issues, issues
    comparisons={}; disagreements=[]
    for left,right in [('A','B'),('native_LLM','A')]:
        key=left+'|'+right
        comparisons[key]={d:calculate(parsed[left],parsed[right],d) for d in DIMS}
        for ident in source:
            for dim in DIMS:
                if parsed[left][ident]['labels'][dim]!=parsed[right][ident]['labels'][dim]:
                    disagreements.append(dict(comparison=key,id=ident,dimension=dim))
    original={x['id']:x for x in load_rows(ROOT/'06-coding/native-llm41-sol/first-run/predictions.jsonl')}
    changes=[{'id':ident,'dimension':dim,'before':original[ident]['labels'][dim],
              'after':parsed['native_LLM'][ident]['labels'][dim],
              'reason':'same-version complete source supplement; separate AI developmental rejudgment'}
             for ident in source for dim in DIMS
             if original[ident]['labels'][dim]!=parsed['native_LLM'][ident]['labels'][dim]]
    result={'checked_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
            'identity':'AI development A/B and native LLM; own previous judgments; A restored source',
            'record_n':2,'dimension_n':10,'source':plan['source'],'manual':plan['manual'],'resource':plan['resource'],
            'seals':seals,'quality_issues':issues,'comparisons':comparisons,'disagreements':disagreements,
            'native_changes_from_preserved_first_run':changes,
            'no_two_record_kappa_imputed_to_one':True,'human_validation':False,'formal_acceptance':False,
            'rule_new_material_run':'not yet available; not evaluated or inferred',
            'old_41_77_development_and_first_machine_artifacts_unchanged':True,
            'no_uniform_new_41_run_claim':'Only these two received the newly supplemented shared material.'}
    dest=ROOT/'04-calibration/renewal-rejudge-v11/admin'
    with (dest/'root-seal-quality-and-arithmetic-audit.json').open('x')as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files_verified':{k:v['files_verified_n']for k,v in seals.items()},
          'disagreements':disagreements,'native_changes':changes,
          'kappa':{k:{d:v['kappa']for d,v in values.items()}for k,values in comparisons.items()}},ensure_ascii=False))

if __name__=='__main__': main()
