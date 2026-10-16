"""Finite independent facility audit; invented mathematics and copied TOY shape."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from fractions import Fraction

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'native-batch-stability-adapter-sol'
sys.path.insert(0, str(CANDIDATE))
import batch_adapter as adapter


def bind(p):
    p = Path(p).resolve()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def write(name, value):
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b'\n'
    with path.open('xb') as f:
        f.write(data)


seal = json.loads((CANDIDATE / 'candidate-seal.json').read_text())
before_seal = bind(CANDIDATE / 'candidate-seal.json')
checks = []
reads = set()
external = {Path(x['path']).resolve() for x in seal['read_only_external_files']}
def audit(event, args):
    if event != 'open' or not args or isinstance(args[0], int):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    mode, flags = args[1], args[2] or 0
    writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
    if writing:
        if HERE not in p.parents:
            raise PermissionError('audit write outside new directory: ' + str(p))
    else:
        if CANDIDATE not in p.parents and HERE not in p.parents and p not in external:
            raise PermissionError('audit read outside exact scope: ' + str(p))
        reads.add(str(p))
sys.addaudithook(audit)


def check(name, value, detail=None):
    checks.append({'name': name, 'passed': bool(value), 'detail': detail})


inventory = [bind(CANDIDATE / x['path']) for x in seal['files']]
check('candidate-seal-296-file-bytes-and-SHA', len(inventory) == 296 and all(
      b['bytes'] == x['bytes'] and b['sha256'] == x['sha256'] for b,x in zip(inventory, seal['files'])))
actual = sorted(str(p.relative_to(CANDIDATE)) for p in CANDIDATE.rglob('*')
                if p.is_file() and p.name != 'candidate-seal.json' and '__pycache__' not in p.parts and p.suffix != '.pyc')
check('candidate-seal-exact-membership', actual == sorted(x['path'] for x in seal['files']))
check('all-ten-bound-technical-sources-unchanged', all(bind(x['path']) == x for x in seal['read_only_external_files']))
check('vendor-math-byte-identical-to-bound-typing-fixed-source',
      (CANDIDATE/'vendor/stability_engine.py').read_bytes() == Path(seal['read_only_external_files'][0]['path']).read_bytes())
native_source = next(x for x in seal['read_only_external_files'] if x['path'].endswith('native-output.schema.json'))
check('native-schema-byte-identical-to-bound-source', (CANDIDATE/'vendor/native-output.schema.json').read_bytes() == Path(native_source['path']).read_bytes())

# The candidate's schema-valid TOY shell is explicitly copied, not claimed as
# independently sampled or real data. Independent mutations exercise contracts.
fixture = HERE/'copied-toy-input'
shutil.copytree(CANDIDATE/'constructed-controls/inputs/mixed', fixture)
reg_path, ledger_path = fixture/'registry.json', fixture/'ledger.json'
raw_registry = reg_path.read_bytes()
reg, ledger = adapter.read_json_bytes(raw_registry,'audit toy registry'), adapter.read_json_bytes(ledger_path.read_bytes(),'audit toy ledger')
reader = adapter.AssetReader(fixture)
meta = adapter.validate_registry(reg, reader)
write('prior-expectations.json', {
    'scope': 'saved before independent mutations and invented mathematics execution',
    'copied_toy_shell_not_independent_dataset': True,
    'expected_rejections': ['last-member-bad-quote','fixed-pointer-order-reversal','semantic-null-after-valid-retry','four-batch-attempts','invalid-attempt-first','provider-model-string-drift','toy-as-production'],
    'five-diagnostic-snapshot': {'unlocked': False, 'paired_comparisons': {}, 'three_main_runs': None},
    'invented_five_ids_weights': {'u':1,'v':2,'w':3,'n':4,'t':5},
    'invented_R1_R2_S_raw': {'n00':1,'n01':1,'n10':1,'n11':0,'Po':'1/3','Pe':'5/9','kappa':'-1/2'},
    'invented_R1_R2_S_weighted': {'n00':1,'n01':3,'n10':2,'n11':0,'Po':'1/6','Pe':'1/2','kappa':'-2/3'},
    'C5_pair_and_triple': {'IDs':['u','v','w'],'agreement_n':1,'N':3,'weight_agree':1,'weight_N':6},
    'q_weighted': {'R1':{'S':'2/5','Ec':'3/5'},'R2':{'S':'1/2','Ec':'1/2'},'R3':{'S':'2/5','Ec':'3/5'}},
    'semantic_null_mask_same': {'n':1,'denominator':1,'rate':1}, 'real_cohort_or_provider_calls':0})

report, firsts, ledger_audit, input_bindings = adapter.analyze(reg_path, ledger_path)
write('baseline-toy-original-output.json', {'report':report,'firsts':firsts,'audit':ledger_audit,'inputs':input_bindings})
ids = reg['sample']['batches'][0]['members']
pointers = [firsts['runs']['R1'][i]['extraction_pointer'] for i in ids]
origins = [firsts['runs']['R1'][i]['original_batch_response'] for i in ids]
check('fixed-items-pointers-share-complete-original-file', pointers == ['/items/0','/items/1'] and origins[0] == origins[1]
      and all(firsts['runs']['R1'][i]['derived_record_is_original_response'] is False for i in ids), {'pointers':pointers,'original_ref':origins[0]})
check('first-valid-selected-own-condition-and-null-kept', firsts['runs']['P'][ids[0]]['attempt_number'] == 2
      and report['per_record_states']['P'][ids[0]]['labels']['E'] is None)
failed_ids = reg['sample']['batches'][1]['members']
check('exhausted-whole-batch-no-partial-member-salvage', all(report['per_record_states']['P'][i]['labels'] is None
      and report['per_record_states']['P'][i]['failure_exhausted_three_attempts'] for i in failed_ids))
check('baseline-five-terminal-conditions-open-comparison', report['comparison_gate']['unlocked'] and len(report['paired_comparisons']) == 5)
check('requested-model-not-provider-identity-or-API-count', report['identity_and_independence']['actual_model_identity_proven'] is False
      and report['identity_and_independence']['independent_contexts_verified'] is False and report['limits']['provider_API_call_count'] is None
      and reg['configuration']['request_settings']['provider_parameters'] is None)

run, bid = 'R1','THREE'
binding = reg['conditions'][run]['batches'][bid]
raw = reader.read(ledger['runs'][run]['batches'][1]['attempts'][0]['original_batch_response'],'toy whole raw')
original = adapter.read_json_bytes(raw,'original toy whole')
for name, mutate in [
    ('last-member-bad-quote', lambda x: x['items'][-1]['evidence']['S'].__setitem__('current_quote','not the actual continuous text')),
    ('fixed-pointer-order-reversal', lambda x: x['items'].reverse())]:
    changed = copy.deepcopy(original); mutate(changed)
    changed_raw = adapter.canonical(changed)+b'\n'
    parsed, result = adapter.qualify_whole_batch(changed_raw,reg,meta,run,bid,binding)
    write('actual-failures/'+name+'.raw', changed_raw)
    write('actual-failures/'+name+'.qualification.json',result)
    check(name, parsed is None and result['technical_valid'] is False and result['record_checks'] == [],result)
different_bytes = b' \n'+raw+b'\n'
parsed, qualified = adapter.qualify_whole_batch(different_bytes,reg,meta,run,bid,binding)
check('original-byte-SHA-distinct-from-parsed-object-SHA', qualified['technical_valid'] and adapter.digest(different_bytes) != adapter.digest(raw)
      and adapter.object_sha(parsed) == adapter.object_sha(original))
write('equivalent-json-distinct-original-bytes.raw',different_bytes)


def reseal(stream):
    stream['seal']['content_sha256'] = adapter.object_sha({k:v for k,v in stream.items() if k != 'seal'})


def reject_ledger(name, mutate, expected):
    changed = copy.deepcopy(ledger); mutate(changed)
    for stream in changed['runs'].values(): reseal(stream)
    write('actual-failures/'+name+'.ledger.json',changed)
    try:
        adapter.validate_ledger(reg,changed,meta,adapter.AssetReader(fixture),raw_registry)
    except (adapter.ContractError,ValueError,KeyError,TypeError) as e:
        result={'rejected':True,'reason':str(e)}
        check(name,expected in str(e),result)
    else:
        result={'rejected':False};check(name,False,result)
    write('actual-failures/'+name+'.execution.json',result)

reject_ledger('semantic-null-after-valid-retry',lambda x:x['runs']['P']['batches'][0]['attempts'].append(copy.deepcopy(x['runs']['P']['batches'][0]['attempts'][-1])), 'after first technically valid batch')
reject_ledger('four-batch-attempts',lambda x:x['runs']['P']['batches'][1]['attempts'].append(copy.deepcopy(x['runs']['P']['batches'][1]['attempts'][-1])), 'max three')
reject_ledger('invalid-attempt-first',lambda x:x['runs']['H']['batches'][0]['first'].__setitem__('attempt_number',1), 'first must equal earliest valid')
def model_drift(x):
    for run, model in [('R1','observed-A'),('R2','observed-B')]:
        x['runs'][run]['batches'][0]['attempts'][0]['provider_receipt'].update(status='observed_unverified',returned_model=model)
reject_ledger('provider-model-string-drift',model_drift,'returned-model string drift')

snapshot=copy.deepcopy(ledger)
s=snapshot['runs']['H'];s['batches'][0]['attempts']=s['batches'][0]['attempts'][:1];s['batches'][0]['first']=None
s['seal']['status']='snapshot_not_terminal';reseal(s)
snapshot_path=HERE/'snapshot-ledger.json';write('snapshot-ledger.json',snapshot)
snapshot_report,_,snapshot_audit,_=adapter.analyze(reg_path,snapshot_path)
write('snapshot-original-output.json', {'report':snapshot_report,'audit':snapshot_audit})
check('one-unfinished-diagnostic-locks-all-comparisons',snapshot_report['comparison_gate']['unlocked'] is False
      and snapshot_report['paired_comparisons'] == {} and snapshot_report['three_main_runs'] is None
      and snapshot_audit['runs']['H'][0]['remaining_retry_slots_if_unresolved'] == 2)
production=copy.deepcopy(reg);production['data_mode']='prospective_registered_inputs'
try:
    adapter.qualification_binding(production,adapter.AssetReader(fixture))
except adapter.ContractError as e:
    write('actual-failures/toy-as-production.json',{'rejected':True,'reason':str(e)})
    check('production-interface-not-adopted-fails-closed','production source/schema/opaque adapter/quote verifier adoption absent' in str(e))
else:check('production-interface-not-adopted-fails-closed',False)

# New hand-computed vectors do not copy candidate response labels.
weights={i:Fraction(w) for i,w in {'u':1,'v':2,'w':3,'n':4,'t':5}.items()}
mathmeta={'ids':list(weights),'weights':weights,'records':{i:{'material_state':'complete'} for i in weights}}
values={'R1':[(0,0,0,0,0),(1,0,0,0,0),(0,0,1,0,0),(None,1,0,0,0),None],
        'R2':[(0,0,0,0,0),(0,0,0,0,0),(1,0,1,0,0),(None,1,0,0,0),(1,0,0,0,0)],
        'R3':[(0,0,0,0,0),(1,0,0,0,0),(0,0,1,0,0),(None,1,0,0,0),(0,0,0,0,0)]}
values['W']=values['R1'];values['H']=values['R3'];values['P']=values['R1']
selected={r:{i:{'labels':None if v is None else dict(zip(adapter.DIMS,v)),
               'state':'technical_failure' if v is None else 'valid_semantic_null' if None in v else 'valid_binary'}
             for i,v in zip(weights,rows)} for r,rows in values.items()}
origins={r:{i:{'constructed_math_origin':i,'run_id':r} for i in weights} for r in values}
pairs,triple=adapter.statistics({'sample':{'weight_kind':'preassigned_analytic'}},mathmeta,selected,origins)
write('invented-math-original-output.json', {'meta':{'IDs':list(weights),'weights':{i:int(w) for i,w in weights.items()}},
                                          'values':values,'paired_comparisons':pairs,'three_main_runs':triple})
table=pairs['R1/R2']['dimensions']['S']
check('invented-S-raw-negative-kappa',table['raw']['cells']=={'n00':1,'n01':1,'n10':1,'n11':0}
      and math.isclose(table['raw']['Po'],1/3) and math.isclose(table['raw']['Pe'],5/9) and table['raw']['kappa']==-.5,table['raw'])
check('invented-S-weighted-negative-kappa',table['weighted']['cells']=={'n00':1,'n01':3,'n10':2,'n11':0}
      and math.isclose(table['weighted']['Po'],1/6) and table['weighted']['Pe']==.5 and math.isclose(table['weighted']['kappa'],-2/3),table['weighted'])
check('null-versus-technical-failure-dimension-accounting',table['domain']['joint_comparable_assignedIDs']==['u','v','w']
      and table['domain']['excluded_assignedIDs']==['n','t'] and pairs['R1/R2']['dimensions']['E']['domain']['joint_comparable_n']==4)
v=triple['five_dimension_vector']
check('invented-C5-triple-and-weighted-denominators',v['denominator_n']==3 and v['agreement_n']==1
      and v['weighted_denominator']==6 and v['weighted_agreement_mass']==1 and math.isclose(v['weighted_complete_agreement_rate'],1/6),v)
q=triple['q']
check('own-run-sum5T-weighted-q',q['by_run']['R1']['weighted_T']['S']==2 and q['by_run']['R1']['weighted_T']['Ec']==3
      and q['by_run']['R1']['weighted_sum5T']==5 and q['by_run']['R2']['weighted_sum5T']==6
      and q['by_run']['R1']['weighted_q']['S']==.4 and q['by_run']['R2']['weighted_q']['S']==.5,q['by_run'])
check('semantic-null-mask-not-binary-stability',triple['semantic_null_patterns']['same_null_mask_n']==1
      and triple['semantic_null_patterns']['same_null_mask_denominator']==1 and triple['semantic_null_patterns']['is_binary_stability'] is False)

# Replay a single legacy TOY shell through the actual unchanged old CLI. The
# legacy external true check report remains solely a mathematical fixture.
legacy=HERE/'copied-legacy-toy-input'
shutil.copytree(CANDIDATE/'constructed-controls/inputs/legacy-one-record',legacy)
commands=[('legacy', [sys.executable,'-B',str(CANDIDATE/'vendor/stability_engine.py'),'analyze','--registry',str(legacy/'registry.json'),'--ledger',str(legacy/'ledger.json'),'--out-dir',str(HERE/'legacy-cli-output')]),
          ('batch',[sys.executable,'-B',str(CANDIDATE/'batch_adapter.py'),'analyze','--registry',str(reg_path),'--ledger',str(ledger_path),'--out-dir',str(HERE/'batch-cli-output')])]
for name,command in commands:
    completed=subprocess.run(command,capture_output=True,text=True)
    write(name+'-actual-cli.json',{'argv':command,'exit_code':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr,'real_model_calls':0})
    check(name+'-actual-CLI-compatible',completed.returncode==0,completed.stderr)
legacy_report=json.loads((HERE/'legacy-cli-output/report.json').read_text())
legacy_S=legacy_report['paired_comparisons']['R1/R2']['dimensions']['S']['raw']
check('legacy-single-record-math-preserved',legacy_S['cells']=={'n00':0,'n01':1,'n10':0,'n11':0}
      and legacy_S['Po']==legacy_S['Pe']==legacy_S['kappa']==0)
check('batch-CLI-statistics-match-in-process-toy-analysis',json.loads((HERE/'batch-cli-output/report.json').read_text())==report)
check('candidate-seal-and-all296-files-still-unchanged',bind(CANDIDATE/'candidate-seal.json')==before_seal
      and all(bind(b['path'])==b for b in inventory))
write('candidate-bindings-check.json',{'candidate_seal':before_seal,'296_candidate_files_verified_before_after':True,
                                     'external_technical_source_bindings':seal['read_only_external_files'],
                                     'executed_code':[bind(CANDIDATE/n) for n in ['batch_adapter.py','toy_qualification.py','vendor/stability_engine.py','vendor/native-output.schema.json','toy-source.schema.json']]})
write('audit-controls.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed',
                            'check_N':len(checks),'passed_N':sum(c['passed'] for c in checks),'checks':checks,
                            'actual_in_process_read_paths':sorted(reads),'model_or_real_cohort_calls':0,
                            'candidate_and_all_existing_files_read_only':True,'production_qualification_adopted':False,
                            'synthetic_shell_copied_not_independent_dataset':True,'invented_math_vectors_are_new':True})
print(json.dumps({'status':'passed' if all(c['passed'] for c in checks) else 'failed',
                  'check_N':len(checks),'passed_N':sum(c['passed'] for c in checks),'real_model_calls':0}))
for c in checks:
    if not c['passed']: print(json.dumps(c,ensure_ascii=False))
