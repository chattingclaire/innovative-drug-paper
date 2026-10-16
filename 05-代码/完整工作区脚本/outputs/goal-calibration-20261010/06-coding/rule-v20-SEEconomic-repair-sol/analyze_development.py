"""Post-run descriptive changes only; reviews are not inference inputs or gold."""
from pathlib import Path
import hashlib,json,collections
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def main():
    prior=ROOT/'outputs/goal-calibration-20261010/06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
    original={x['id']:x for x in map(json.loads,prior.read_text().splitlines())}
    current=[json.loads(x) for x in (HERE/'development800-first/predictions.jsonl').read_text().splitlines()]
    audits=ROOT/'outputs/goal-calibration-20261010/08-audits/ai800-disagreement-semantic-root'
    reference={};bindings=[]
    for dimension,folder,file in [('S','safety89-sol','reviews.json'),('E','effectiveness49-sol','reviews-scoped.json'),('Ec','economic87-sol','reviews.json')]:
        path=audits/folder/file;raw=path.read_bytes();bindings.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
        for x in json.loads(raw):reference[(x['source_id'],dimension)]=x
    changes=[];scope=[];pending=[]
    for row in current:
        old=original[row['id']]
        for dim in ('S','E','Ec','I','F'):
            new=row['labels'][dim] if row['labels'] else None
            rv=reference.get((row['id'],dim))
            item={'id':row['id'],'dimension':dim,'frozen_rule':old['labels'][dim],
                'candidate':new,'candidate_record_status':row['status'],
                'candidate_decision':row['decisions'][dim] if row['decisions'] else None,
                'original_decision':old['decisions'][dim],
                'is_human_or_formal_reference':False,'formal_score_computed':False}
            if rv:
                excluded=rv['review_value'] not in (0,1) or rv['assessment'] in ('手册边界待核','材料不足','需补材')
                item.update(blind_id=rv['blind_id'],AI_review_suggestion=rv['review_value'],AI_assessment=rv['assessment'],
                    AI_review_identity='non-human semantic audit candidate; not gold',
                    needs_human_review=rv.get('needs_human_review'),excluded_from_any_optimization_target=excluded,
                    review_agrees_with_candidate=None if excluded or row['status']=='technical_failure' else new==rv['review_value'])
                scope.append(item)
                if excluded:pending.append(item)
            if new!=old['labels'][dim] or row['status']=='technical_failure':changes.append(item)
    for name,items in [('all-changes.json',changes),('reviewed-disagreement-followup.json',scope),('pending-review-not-targets.json',pending)]:
        with (HERE/'development800-first'/name).open('x') as f:json.dump(items,f,ensure_ascii=False,indent=2);f.write('\n')
    summary={'status':'descriptive_development_only','formal_validation_complete':False,'is_human_reference':False,
        'original_rule_binding':{'path':str(prior),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest()},
        'post_inference_only_review_bindings':bindings,'changed_slots_by_dimension':dict(collections.Counter(x['dimension'] for x in changes if x['candidate_record_status']!='technical_failure')),
        'technical_failure_records':sum(x['status']=='technical_failure' for x in current),'reviewed_disagreement_slots':len(scope),
        'human_boundary_slots_not_targets':len(pending),'IF_changes_on_successful_records':[x for x in changes if x['dimension'] in ('I','F') and x['candidate_record_status']!='technical_failure'],
        'unmatched_certain_AI_audit_candidates':[{'blind_id':x.get('blind_id'),'id':x['id'],'dimension':x['dimension'],
            'frozen_rule':x['frozen_rule'],'candidate':x['candidate'],'AI_review_suggestion':x.get('AI_review_suggestion'),
            'candidate_basis':x['candidate_decision']['basis_path'] if x['candidate_decision'] else x['candidate_record_status']}
            for x in scope if x.get('review_agrees_with_candidate') is False],
        'not_accuracy_or_acceptance_score':True}
    with (HERE/'development800-first/change-summary.json').open('x') as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:summary[k] for k in ('changed_slots_by_dimension','reviewed_disagreement_slots','human_boundary_slots_not_targets','unmatched_certain_AI_audit_candidates')},ensure_ascii=False))


if __name__=='__main__':main()
