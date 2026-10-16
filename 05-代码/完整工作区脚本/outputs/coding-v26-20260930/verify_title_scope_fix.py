"""Verify a code-review-driven title-scope fix, without selecting by metrics."""
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'autocode-v25-20260927'
sys.path.insert(0,str(HERE/'rules_candidate'))
sys.path.insert(0,str(BASE))
from audit_current_implementation import PROBES
from analyze_current_reruns import normalize_rule_record

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=HERE/'rules_candidate/policy_coding_v26_2.py'
    out=HERE/'title_scope_verification'
    out.mkdir(exist_ok=False)
    oldfreeze=json.loads((HERE/'rule_comparison/candidate_freeze.json').read_text())
    for p,digest in oldfreeze['bindings'].items():
        assert sha(Path(p))==digest, 'Prior frozen source changed'
    freeze={str(p):sha(p) for p in [source,Path(__file__).resolve(),BASE/'current_rule_inputs.jsonl']}
    (out/'freeze.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':freeze},ensure_ascii=False,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('v26_2_fixed',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    probes=list(PROBES)+[
        ('I','现发布《支持创新药的研发办法》。',0,'title_only'),
        ('I','现发布《改良给药途径指导原则》。',0,'title_only'),
        ('F','现发布《药品用于缺乏有效标准治疗手段的患者的研究指南》。',0,'title_only'),
        ('I','现发布《支持创新药的研发办法》，并对创新药研发予以支持。',1,'title_and_substantive_claim'),
        ('I','为促进药品创新发展，按照《药品试验数据保护办法》完善药品试验数据保护制度。',1,'valid_relation_crossing_citation')]
    results=[]
    for dim,text,expected,kind in probes:
        r=module.code_unit({'unit_text':text})
        results.append({'dimension':dim,'constructed_text':text,'expected':expected,'actual':r['labels'][dim],'kind':kind})
    assert all(x['actual']==x['expected'] for x in results), results
    previous={r['id']:r['prediction'] for r in map(json.loads,(HERE/'rule_comparison/all_predictions.jsonl').read_text().splitlines())}
    changes=[]
    n=0
    with (out/'all_predictions.jsonl').open('w') as f:
        for row in map(json.loads,(BASE/'current_rule_inputs.jsonl').read_text().splitlines()):
            r=module.code_unit(row['input'])
            old=previous[row['id']]
            for d in ('S','E','Ec'):
                assert r['labels'][d]==old['labels'][d]
            assert r['judgement_status']==old['judgement_status']
            for e in r['evidence']:
                assert row['input']['unit_text'][e['start']:e['end']]==e['text']
            if r['labels']!=old['labels']:
                changes.append({'id':row['id'],'old_labels':old['labels'],'new_labels':r['labels']})
            f.write(json.dumps({'id':row['id'],'original_id':row['original_id'],'prediction':r},ensure_ascii=False)+'\n')
            n+=1
    assert n==4924
    for path,digest in freeze.items():
        assert sha(Path(path))==digest
    report={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'reason_for_revision':'New V26 rules reintroduced dimension matches wholly inside document titles; found in constructed boundary probes, not from optimizing kappa.',
            'n':n,'probes':results,'label_changes_vs_v26_candidate1':changes,
            'S_E_Ec_and_pending_unchanged':True,
            'same_labels_imply_same_comparison_metrics':not changes,
            'comparison_metrics_if_identical':str(HERE/'rule_comparison/metrics.json') if not changes else None,
            'output_sha256':sha(out/'all_predictions.jsonl'),
            'status':'development_candidate_only; prior references exposed; no new LLM run or context recoding'}
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'n':n,'constructed_probes_passed':len(results),'label_changes_vs_candidate1':len(changes),'same_metrics':not changes},ensure_ascii=False))

if __name__=='__main__':
    main()
