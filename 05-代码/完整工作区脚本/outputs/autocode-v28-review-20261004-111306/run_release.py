"""Freeze rules, predict without references, then separately compare.

Use --predict after the semantic regression suite passes. --compare verifies
the frozen output and unchanged reference bindings before descriptive analysis.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'autocode-v25-20260927'
PREV=ROOT.parent/'autocode-v27-final-20261004-1034'
sys.path.insert(0,str(OLD))
DIMS=('S','E','Ec','I','F')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()]


def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def predict():
    import policy_coding_v27 as coder
    test_log=ROOT/'regression-tests.log'
    test_text=test_log.read_text()
    assert test_text.rstrip().endswith('OK'), 'Semantic regression suite has not passed'
    test_count=int(re.search(r'Ran (\d+) tests',test_text).group(1))
    files=[ROOT/n for n in ['policy_coding_v27.py','inherited_rules_v25.py','rule_support.py',
                           'context_validation.py','rules_se.py','rules_ec.py','rules_if.py',
                           'prepare_inputs.py','run_release.py','rule_inputs_v27.jsonl']]
    files += [ROOT/n for n in ['coverage_se.json','coverage_ec.json','coverage_if.json','regression-tests.log',
                              'test_context_validation.py','test_parent_certificates.py','test_integration.py','test_rules_se.py','test_rules_ec.py','test_rules_if.py']]
    files += [OLD/n for n in ['baseline_candidate17.py','policy_coding_v25.py','protocol-v1.3.md',
                             'current_rule_inputs.jsonl']]
    files += [ROOT/'review_protocol.json',ROOT/'protocol-v1.3.md']
    for group in ('se','ec','if'):
        files += [ROOT/f'{prefix}_{group}.{suffix}' for prefix,suffix in
                  [('audit_packet','jsonl'),('semantic_review','jsonl'),('amendment_log','json')]]
    files += [PREV/'rule_inputs_v27.jsonl']
    for name in ('prepare_parent_context_v28.py','parent_context_patch_v28.json',
                 'context_proposals_se.json','context_proposals_ec_if.json','amendment_log_ec_context_fix.json',
                 'semantic_review_se_context_updated.jsonl','audit_packet_se_context_updated.jsonl',
                 'new_discrepancy_semantic_review_se.json','amendment_log_se_name_only_fix.json'):
        if (ROOT/name).exists(): files.append(ROOT/name)
    prepared=rows(ROOT/'rule_inputs_v27.jsonl')
    for row in prepared:
        for context in row['input'].get('verified_parent_context', []):
            if context.get('repair_version')=='v28':
                for key in ('source_path','candidate_path'):
                    path=Path(context[key])
                    if path not in files: files.append(path)
    assert sha(ROOT/'protocol-v1.3.md')==sha(OLD/'protocol-v1.3.md')
    bindings={str(p):sha(p) for p in files}
    started=datetime.now(timezone.utc).isoformat()
    original={r['id']:r for r in rows(OLD/'current_rule_inputs.jsonl')}
    prior_inputs={r['id']:r for r in rows(PREV/'rule_inputs_v27.jsonl')}
    assert len(prepared)==len(original)==4924
    predictions=[]; unchanged_inputs=[]; changed_context=[]; prior_input_predictions=[]; new_context_changes=[]
    checks=Counter()
    for row in prepared:
        old=original[row['id']]
        assert old['original_id']==row['original_id']
        assert old['input']['unit_text']==row['input']['unit_text']
        out=coder.code_unit(row['input'])
        initial=coder.code_unit(old['input'])
        prior_input=coder.code_unit(prior_inputs[row['id']]['input'])
        assert out['judgement_status']!='undetermined',row['id']
        assert set(out['labels'])==set(DIMS)
        for evidence in out['evidence']:
            assert row['input']['unit_text'][evidence['start']:evidence['end']]==evidence['text']
            checks['literal_evidence_spans']+=1
        for suppression in out.get('suppressions',[]):
            if all(k in suppression for k in ('start','end','text')):
                assert row['input']['unit_text'][suppression['start']:suppression['end']]==suppression['text']
                checks['literal_suppression_spans']+=1
        predictions.append({'id':row['id'],'original_id':row['original_id'],'prediction':out})
        unchanged_inputs.append({'id':row['id'],'original_id':row['original_id'],'prediction':initial})
        prior_input_predictions.append({'id':row['id'],'original_id':row['original_id'],'prediction':prior_input})
        if out['labels']!=prior_input['labels']:
            new_context_changes.append({'id':row['id'],'on_v27_inputs':prior_input['labels'],
                                        'on_v28_inputs':out['labels']})
        if out['labels']!=initial['labels']:
            changed_context.append({'id':row['id'],'before_context_repair':initial['labels'],
                                    'after_context_repair':out['labels']})
    assert bindings=={str(p):sha(p) for p in files},'Code/input changed during prediction'
    for name,data in [('all_predictions.jsonl',predictions),('original_input_predictions.jsonl',unchanged_inputs),
                      ('v27_input_predictions.jsonl',prior_input_predictions)]:
        (ROOT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data))
    manifest={'version':coder.VERSION,'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat(),
              'n':len(predictions),'pending_n':0,'code_and_input_bindings':bindings,
              'output_bindings':{n:sha(ROOT/n) for n in ('all_predictions.jsonl','original_input_predictions.jsonl','v27_input_predictions.jsonl')},
              'evidence_checks':dict(checks),'context_only_label_changes':changed_context,
              'v28_added_context_only_label_changes':new_context_changes,
              'reference_labels_loaded_during_prediction':False,
              'semantic_regression_tests_passed':test_count,
              'validation_status':'Frozen development revision; independent external validation not performed.'}
    save(ROOT/'release_manifest.json',manifest)
    print(json.dumps({'n':len(predictions),'pending':0,'context_changed':len(changed_context),'checks':dict(checks)}))


def independently_checked(pairs):
    from comparison_statistics import agreement
    counts=Counter(pairs);n=len(pairs)
    expected_numerator=sum(sum(counts[x,y] for y in (0,1))*sum(counts[y,x] for y in (0,1)) for x in (0,1))
    denominator=n*n-expected_numerator
    kappa=float(Fraction(n*(counts[0,0]+counts[1,1])-expected_numerator,denominator)) if denominator else None
    report=agreement([(p,r,1) for p,r in pairs])
    assert kappa is None or abs(kappa-report['binary_agreement']['kappa'])<1e-12
    return report


def compare():
    from analyze_current_reruns import load_sealed_predictions,load_reference_units,normalize_rule_record
    from comparison_statistics import agreement
    manifest=json.loads((ROOT/'release_manifest.json').read_text())
    for path,digest in manifest['code_and_input_bindings'].items():assert sha(path)==digest
    for path,digest in manifest['output_bindings'].items():assert sha(ROOT/path)==digest
    rules,llm,llm_inputs,seal=load_sealed_predictions()
    previous_path=PREV/'all_predictions.jsonl'
    previous_check=json.loads((PREV/'release_manifest.json').read_text())
    assert sha(previous_path)==previous_check['output_bindings']['all_predictions.jsonl']
    frozen_masks=json.loads((PREV/'comparison_masks.json').read_text())
    frozen_metrics=json.loads((PREV/'metrics.json').read_text())
    previous={r['id']:normalize_rule_record(r['prediction']) for r in rows(previous_path)}
    new={r['id']:r['prediction'] for r in rows(ROOT/'all_predictions.jsonl')}
    unchanged={r['id']:normalize_rule_record(r['prediction']) for r in rows(ROOT/'original_input_predictions.jsonl')}
    prior_input={r['id']:normalize_rule_record(r['prediction']) for r in rows(ROOT/'v27_input_predictions.jsonl')}
    inputs={r['id']:r for r in rows(ROOT/'rule_inputs_v27.jsonl')}
    assert set(previous)==set(new)==set(inputs)==set(llm)
    comparisons={};reference_rows={};reference_bindings={};excel_metrics=[];masks={}
    methods={'rules_v27':previous,'rules_v28':new,'rules_v28_original_input':unchanged,
             'rules_v28_v27_input':prior_input,'llm_unchanged':llm}
    for scope in ('H427','current1268'):
        units,bindings=load_reference_units(scope,rules,llm,llm_inputs)
        reference_bindings.update(bindings)
        for u in units:
            assert u['id'] not in reference_rows,'Overlapping reference frames'
            reference_rows[u['id']]={'scope':scope,**u}
        group={'n':len(units),'references':{},'reference_identity':'AI A/C first submissions; not human gold standard'}
        for ref in ('A','C'):
            group['references'][ref]={}
            for dim in DIMS:
                wanted=set(frozen_masks[f'{scope}/{ref}/{dim}'])
                common=[u for u in units if u['id'] in wanted]
                assert len(common)==len(wanted)
                assert all(u['references'][ref]['labels'][dim] in (0,1) and
                           all(p[u['id']]['labels'][dim] in (0,1) for p in methods.values())
                           for u in common)
                masks[f'{scope}/{ref}/{dim}']=[u['id'] for u in common]
                entry={'common_n':len(common),'excluded_n':len(units)-len(common),'methods':{}}
                for name,pred in methods.items():
                    pairs=[(pred[u['id']]['labels'][dim],u['references'][ref]['labels'][dim]) for u in common]
                    metric=independently_checked(pairs)
                    weighted=agreement([(pred[u['id']]['labels'][dim],u['references'][ref]['labels'][dim],u['weight']) for u in common])
                    all_available=agreement([(pred[u['id']]['labels'][dim],u['references'][ref]['labels'][dim],1) for u in units])
                    entry['methods'][name]={'common_unweighted':metric,'common_historical_weighted':weighted,
                                            'all_pairs_including_pending':all_available}
                    if name=='rules_v27':
                        original=frozen_metrics['comparisons'][scope]['references'][ref][dim]['methods']['rules_v27']['common_unweighted']
                        assert metric['confusion_on_joint_determinate']==original['confusion_on_joint_determinate']
                    if name in ('rules_v27','rules_v28','llm_unchanged'):
                        excel_metrics.append({'scope':scope,'reference':ref,'dimension':dim,'method':name,
                                              'n':len(common),'confusion':metric['confusion_on_joint_determinate'],
                                              'kappa':metric['binary_agreement']['kappa'],
                                              **metric['conditional_scores']})
                group['references'][ref][dim]=entry
        comparisons[scope]=group
    changes=[];by_dim={d:Counter() for d in DIMS};full=[]
    for rid,row in inputs.items():
        before=previous[rid]['labels'];after=new[rid]['labels']
        changed=[d for d in DIMS if before[d]!=after[d]]
        if changed:changes.append({'id':rid,'dimensions':changed,'before':before,'after':after})
        for d in DIMS:
            by_dim[d][str(before[d])+'->'+str(after[d])]+=1
        refs=reference_rows.get(rid)
        full.append({'id':rid,'original_id':row['original_id'],'text':row['input']['unit_text'],
                     'source':row['input'].get('unit_source') or row['input'].get('source'),
                     'scope':refs['scope'] if refs else '未纳入A/C比较',
                     'before':before,'after':after,
                     'references':{r:refs['references'][r]['labels'] if refs else None for r in ('A','C')},
                     'evidence':{d:'；'.join(dict.fromkeys(e['text'] for e in new[rid]['evidence'] if e['dimension']==d)) for d in DIMS},
                     'changed_dimensions':','.join(changed),
                     'context_repaired':bool(row['input'].get('verified_following_list_v27')),
                     'parent_context_added_v28':any(c.get('repair_version')=='v28' for c in row['input'].get('verified_parent_context',[])),
                     'innovation_scope_added':bool(row['input'].get('verified_innovation_scope_v27'))})
    report={'created_at':datetime.now(timezone.utc).isoformat(),'rules_version':manifest['version'],
            'n':len(new),'pending_n':0,'changed_units':len(changes),'transitions':{d:dict(c) for d,c in by_dim.items()},
            'comparisons':comparisons,'reference_bindings':reference_bindings,
            'policy':'Exact v27 comparison masks retained for each reference/dimension. Pending references never filled with 0. H427 and current1268 remain separate.',
            'validity':'Descriptive results on exposed development materials. No independent validation claim and no human-gold-standard claim.',
            'LLM':'gpt56-sol-v13-native-1; not rerun or revised in this release',
            'context_effect_separated_in':'release_manifest.json; rules_v28_v27_input isolates this release context repair, rules_v28_original_input includes historical context repairs',
            'working_kappa_target':0.8,
            'target_status': 'Development review only; independent validation not performed'}
    assert masks==frozen_masks,'Comparison masks changed'
    assert reference_bindings==frozen_metrics['reference_bindings'],'Reference identities changed'
    save(ROOT/'metrics.json',report);save(ROOT/'comparison_masks.json',masks)
    save(ROOT/'label_changes.json',changes)
    save(ROOT/'workbook_data.json',{'metrics':excel_metrics,'rows':full,'summary':{k:report[k] for k in ('n','pending_n','changed_units','transitions')}})
    for path,digest in reference_bindings.items():assert sha(path)==digest
    save(ROOT/'analysis_binding.json',{'analysis_script_sha256':sha(__file__),
         'statistics_script_sha256':sha(OLD/'comparison_statistics.py'),
         'release_manifest_sha256':sha(ROOT/'release_manifest.json'),
         'metrics_sha256':sha(ROOT/'metrics.json'),'reference_bindings':reference_bindings,
         'independent_fraction_kappa_check_passed':True})
    print(json.dumps({'n':len(new),'changed_units':len(changes),'transitions':report['transitions']},ensure_ascii=False))
    for d in DIMS:
        print(d,[(r,comparisons['H427']['references'][r][d]['common_n'],
                  {m:round(comparisons['H427']['references'][r][d]['methods'][m]['common_unweighted']['binary_agreement']['kappa'],6)
                   for m in ('rules_v27','rules_v28','llm_unchanged')}) for r in ('A','C')])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--predict',action='store_true');parser.add_argument('--compare',action='store_true')
    args=parser.parse_args()
    if args.predict:predict()
    if args.compare:compare()
