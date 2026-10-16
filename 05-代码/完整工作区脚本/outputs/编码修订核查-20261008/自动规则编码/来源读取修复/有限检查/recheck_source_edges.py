"""Targeted recheck of four recorded reader failures and two source controls."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RT=BASE/'runtime';sys.path.insert(0,str(RT))
import common_innovation_relations14 as innovation
import common_guideline_scope11 as guideline
records={x['id'][-5:]:x['input'] for x in map(json.loads,Path(__file__).with_name('规则待核输入21.jsonl').read_text().splitlines())}
results=[]
def check(name,function,reject=False):
    try:
        value=function();results.append(dict(name=name,passed=not reject,actual_type=type(value).__name__))
    except Exception as error:
        results.append(dict(name=name,passed=reject,error_type=type(error).__name__,reason=getattr(error,'reason',str(error)),details=getattr(error,'details',{})))
for suffix in ['00889','02086','02124']:
    check('actual_v27_interval_recheck_'+suffix,lambda suffix=suffix:innovation.resolve_current_contents(records[suffix]))
check('actual_scope_component_reference_in_midpage',lambda:guideline.resolve_guideline_scope(records['02826']))
z=records['02124'];doc,paras,index=innovation._document(z);p=next(p for p in paras if 'renew22_L117' in (p.get('line_ids') or []));lm={x['id']:copy.deepcopy(x) for x in doc['lines']};lm['renew22_L117']['text']='；';changed=copy.deepcopy(p);changed['text']=''.join(lm[key]['text'] for key in changed['line_ids']);raw=subprocess.run(['pdftotext','-layout',z['unit_source'],'-'],capture_output=True,text=True,check=True).stdout.split('\f')
check('different_punctuation_not_present_in_actual_bound_gap',lambda:guideline._paragraph_context(z,changed,lm,raw),True)
z=copy.deepcopy(records['02826']);doc=json.loads(Path(z['candidate_file']).read_text());target=next(u for u in doc['unit_candidates'] if u.get('pages') and min(u['pages'])>=10 and u.get('text'))
z.update(unit_id=target['id'],unit_text=target['text'],pages=target['pages'])
check('actual_other_attachment_after_reference_boundary_rejected',lambda:guideline.resolve_guideline_scope(z),True)
out=dict(kind='targeted_source_failure_recovery_not_validity',n_checks=len(results),all_checks_pass=all(x['passed'] for x in results),checks=results,runtime_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in RT.iterdir() if p.is_file()})
Path(__file__).with_name('source_edge_recheck01.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['kind','n_checks','all_checks_pass']},ensure_ascii=False))
for x in results:
    if not x['passed']:print(json.dumps(x,ensure_ascii=False))
