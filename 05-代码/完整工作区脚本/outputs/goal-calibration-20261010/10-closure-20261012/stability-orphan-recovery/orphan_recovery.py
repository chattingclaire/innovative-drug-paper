#!/usr/bin/env python3
"""Failure-only orphan closure; no launch, signals, capture parsing or valid receipt."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
SCOPE_SHA = 'a74c30953bb7d8c654b7a9b95ea8afc13e700130d4694209b2c4592ca930a0ca'
FIXED = [(42, 3), (47, 2), (49, 3), (51, 1), (52, 1), (53, 1),
         (54, 1), (55, 1), (56, 1), (57, 1), (58, 1), (59, 2), (60, 1)]
TZ = dt.timezone(dt.timedelta(hours=8))
FILES = ('ROOT-actual-process-start.json', 'ROOT-dispatch-start.json',
         'ROOT-cli-events.jsonl', 'ROOT-stderr.txt', 'ROOT-cli-final-message.txt')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def time(s):
    t = dt.datetime.fromisoformat(s)
    require(t.tzinfo is not None, 'timestamp needs timezone')
    return t

def load(p):
    return json.loads(Path(p).read_text())

def blob(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def bind(p):
    p = Path(p)
    require(p.is_file() and not p.is_symlink(), 'binding missing/nonregular')
    p = p.resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def check(b):
    require(bind(b['path']) == b, 'binding drift: ' + b['path'])
    return b

def put(p, x):
    p = Path(p)
    with p.open('xb') as f:
        f.write(blob(x))
        f.flush()
        os.fsync(f.fileno())
    return bind(p)

def key(e):
    r = e['route']
    return (r['batch_number'], r['attempt_number'])

def scope(path=HERE / 'scope.json', *, synthetic=False):
    p = Path(path).resolve()
    s = load(p)
    require(s['fixture_only'] is synthetic, 'fixture/real scope mismatch')
    if not synthetic:
        require(p == HERE / 'scope.json' and bind(p)['sha256'] == SCOPE_SHA, 'unadopted real scope')
        require([key(e) for e in s['entries']] == FIXED, 'fixed 13 routes changed')
    else:
        require(s.get('NONHUMAN') is True and 'NONHUMAN' in str(p.parent), 'synthetic sandbox required')
        require(all(Path(e['route']['output_directory']).is_relative_to(p.parent)
                    and Path(e['receipt_destination']).is_relative_to(p.parent) for e in s['entries']),
                'synthetic paths escape sandbox')
    require(len({key(e) for e in s['entries']}) == len(s['entries']), 'duplicate route')
    require(s['max_total_attempts'] == 3 and s['original_timeout_seconds'] == 3600, 'budget/timeout changed')
    for field in ('manifest', 'original_GO', 'original_adoption', 'diagnosis'):
        check(s[field])
    for b in s['original_implementation'].values():
        check(b)
    routes = load(s['manifest']['path'])['routes']
    for e in s['entries']:
        r = e['route']
        require(r in routes and r['condition'] == 'R3' and 1 <= r['attempt_number'] <= 3, 'route mismatch')
        a, d = load(check(e['actual_start'])['path']), load(check(e['dispatch_start'])['path'])
        require(a['start'] == e['dispatch_start'] and a['actual_CLI_process_started'] is True,
                'actual start chain')
        require(a['pid'] == e['pid'] == e['process_group_id'] == a['process_group_id'], 'process identity')
        require(a['at_utc'] == e['actual_started_at_utc'], 'actual time changed')
        require(d['GO'] == s['original_GO'] and d['assignment'] == r['assignment']
                and d['stdin'] == r['fixed_request'] and d['argv'] == e['argv']
                and d['working_directory'] == r['working_directory'], 'dispatch context mismatch')
        require((d['condition'], d['batch_number'], d['attempt_number']) == ('R3', *key(e)), 'dispatch route')
        require(str(Path(r['selection_directory']) / f"root-attempt-reception-{r['attempt_number']:04d}.json")
                == e['receipt_destination'], 'receipt destination mismatch')
        check(r['assignment']); check(r['fixed_request'])
    return s

def ps_rows(raw):
    rows = []
    for line in raw.splitlines():
        m = re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.{24})\s+(.+)', line)
        require(m is not None, 'ambiguous ps row')
        pid, ppid, pgid, stat, birth, command = m.groups()
        born = dt.datetime.strptime(birth, '%a %b %d %H:%M:%S %Y').replace(tzinfo=TZ)
        rows.append(dict(pid=int(pid), ppid=int(ppid), pgid=int(pgid), stat=stat,
                         lstart=birth, born_at=born.isoformat(), command=command))
    require(rows and len({r['pid'] for r in rows}) == len(rows), 'empty/duplicate ps table')
    return rows

def get_ps():
    env = {**os.environ, 'LC_ALL': 'C', 'TZ': 'Asia/Shanghai'}
    raw = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,stat=,lstart=,command='], env=env, text=True)
    return raw, ps_rows(raw)

def process_blockers(s, rows, prior_rows=()):
    """Birth distinguishes reused root PIDs; any old PGID occupant remains conservative blocker."""
    bypid = {r['pid']: r for r in rows}
    blocked = {}
    for r in rows:
        c = r['command']
        if (s['isolated_cli_directory'] in c and (' exec ' in c or 'codex-code-mode-host' in c)):
            blocked[r['pid']] = 'isolated CLI/host still present'
        if s['campaign_directory'] in c and (' exec ' in c or 'successor_entry.py' in c):
            blocked[r['pid']] = 'campaign process still present'
        old = s['controller_identity']
        if r['pid'] == old['pid'] and r['lstart'] == old['lstart']:
            blocked[r['pid']] = 'original controller identity still present'
    for e in s['entries']:
        born = time(e['actual_started_at_utc']).replace(microsecond=0)
        root = bypid.get(e['pid'])
        if root and time(root['born_at']) <= born + dt.timedelta(seconds=1):
            blocked[root['pid']] = 'original/ambiguous root identity present'
        for r in rows:
            if r['pgid'] == e['process_group_id']:
                blocked[r['pid']] = 'original numeric process group occupied; wait or independent identity review'
            if e['route']['output_directory'] in r['command']:
                blocked[r['pid']] = 'route capture process present'
        old_owned = {r['pid']: r for r in prior_rows
                     if r['pgid'] == e['process_group_id'] or e['route']['output_directory'] in r['command']}
        changed = True
        while changed:
            changed = False
            for r in prior_rows:
                if r['ppid'] in old_owned and r['pid'] not in old_owned:
                    old_owned[r['pid']] = r; changed = True
        for pid, old in old_owned.items():
            if pid in bypid and bypid[pid]['lstart'] == old['lstart']:
                blocked[pid] = 'known descendant identity remains'
    return [dict(pid=p, reason=blocked[p]) for p in sorted(blocked)]

def files_and_conflicts(s, allow_receipts=None):
    proofs = []
    allow_receipts = allow_receipts or {}
    for e in s['entries']:
        r = e['route']; slot = Path(r['output_directory']); selection = Path(r['selection_directory'])
        require(not (slot / 'ROOT-process-completion.json').exists(), 'original completion appeared')
        require(not (slot / 'first.json').exists(), 'first already exists; independent reception review required')
        require(not (selection / 'root-selection.json').exists() and not (selection / 'root-zero-call-block.json').exists(),
                'batch already selected/blocked')
        dest = Path(e['receipt_destination'])
        if dest.exists():
            require(str(dest) in allow_receipts and bind(dest) == allow_receipts[str(dest)], 'receipt conflict')
        for n in range(1, r['attempt_number']):
            old = load(selection / f'root-attempt-reception-{n:04d}.json')
            require(old['state'] == 'technical_invalid_whole_batch', 'predecessor not invalid')
            cp = load(check(old['completion'])['path'])
            require(cp.get('actual_process_terminal') is True, 'predecessor terminal unknown')
        for n in range(r['attempt_number'] + 1, 4):
            later = selection / f'attempt-{n:04d}'
            require(not (selection / f'root-attempt-reception-{n:04d}.json').exists()
                    and (not later.exists() or not any(later.iterdir())), 'later attempt already used')
        require(all(p.name in FILES and p.is_file() and not p.is_symlink() for p in slot.iterdir()), 'unexpected slot artifact')
        f = {n: bind(slot/n) if (slot/n).exists() else None for n in FILES}
        require(all(f[n] for n in FILES[:4]), 'required raw metadata/events/stderr missing')
        proofs.append(dict(batch_number=r['batch_number'], attempt_number=r['attempt_number'], files=f))
    return proofs

def observe(scope_path, output, *, synthetic=False, raw_ps=None, at=None):
    s = scope(scope_path, synthetic=synthetic)
    require(at is None or synthetic, 'real observer cannot inject time')
    if raw_ps is not None:
        require(synthetic, 'real observer cannot inject ps')
        raw, rows = raw_ps, ps_rows(raw_ps)
    else:
        raw, rows = get_ps()
    started = at or now()
    files = files_and_conflicts(s)
    if synthetic:
        after_raw, after = raw, rows
    else:
        after_raw, after = get_ps()
    x = dict(artifact_type='orphan_process_and_file_observation', fixture_only=synthetic,
             scope=bind(scope_path), observer=bind(__file__), started_at=started, finished_at=at or now(),
             ps_raw=raw, ps_rows=rows, ps_after_raw=after_raw, ps_after_rows=after,
             blockers=process_blockers(s, rows) + process_blockers(s, after, rows),
             retained_files=files, label_content_parsed=False, process_signals_sent=False)
    return put(output, x)

def validate_pair(s, scope_path, bindings, *, synthetic=False, allow_receipts=None):
    require(len(bindings) == 2 and bindings[0] != bindings[1], 'two independent observations required')
    a, b = [load(check(x)['path']) for x in bindings]
    for x in (a, b):
        require(x['fixture_only'] is synthetic and x['scope'] == bind(scope_path)
                and x['observer'] == bind(__file__), 'observation provenance mismatch')
        require(x['ps_rows'] == ps_rows(x['ps_raw']) and x['ps_after_rows'] == ps_rows(x['ps_after_raw']), 'ps projection mismatch')
        require(time(x['started_at']) <= time(x['finished_at']), 'observation internal time reversed')
        require(all(time(e['actual_started_at_utc']) < time(x['started_at']) for e in s['entries']),
                'observation predates actual start')
        if not synthetic:
            require(time(x['finished_at']) <= time(now()), 'future observation')
        require(not process_blockers(s, x['ps_rows'], a['ps_rows'])
                and not process_blockers(s, x['ps_after_rows'], a['ps_rows'] + a['ps_after_rows']), 'process still live/uncertain')
    require(time(a['finished_at']) < time(b['started_at']), 'observation times overlap/reverse')
    require(a['retained_files'] == b['retained_files'] == files_and_conflicts(s, allow_receipts), 'capture bytes changed')
    return b

def prepare(scope_path, observations, unknown_batches, output, *, synthetic=False):
    s = scope(scope_path, synthetic=synthetic)
    require(unknown_batches and len(set(unknown_batches)) == len(unknown_batches), 'explicit nonduplicate unknown subset required')
    chosen = [e for e in s['entries'] if e['route']['batch_number'] in unknown_batches]
    require(len(chosen) == len(unknown_batches), 'unknown subset outside fixed scope')
    last = validate_pair(s, scope_path, observations, synthetic=synthetic)
    # A fresh live observation is required during later installation too.
    out = Path(output).resolve(); out.mkdir(exist_ok=False)
    (out/'certificates').mkdir(); (out/'receipts').mkdir()
    entries = []
    for e in chosen:
        r = e['route']; name = f"R3-{r['batch_number']:04d}-a{r['attempt_number']}"
        retained = next(x['files'] for x in last['retained_files'] if (x['batch_number'], x['attempt_number']) == key(e))
        cert = dict(artifact_type='ROOT_external_orphan_process_terminal_certificate',
                    provenance='ROOT_two_observation_external_process_identity_and_sealed_files',
                    fixture_only=synthetic, actual_process_terminal=True,
                    terminal_meaning='Observed process/known descendants/isolated hosts absent; no parent wait receipt recovered.',
                    returncode=None, returncode_status='unknown_parent_wait_unavailable',
                    parent_wait_returncode=None, timed_out=None, timeout_status='unknown_parent_wait_unavailable',
                    external_exit_evidence=None, failure_only=True, actual_CLI_process_started=True,
                    pid=e['pid'], process_group_id=e['process_group_id'], condition='R3',
                    batch_number=r['batch_number'], attempt_number=r['attempt_number'],
                    original_actual_process_start=e['actual_start'], original_dispatch_start=e['dispatch_start'],
                    original_GO=s['original_GO'], original_adoption=s['original_adoption'], scope=bind(scope_path),
                    observations=observations, retained_actual_files=[v for v in retained.values() if v], observer=bind(__file__),
                    label_content_parsed=False, original_timeout_seconds=3600,
                    original_deadline_at=(time(e['actual_started_at_utc'])+dt.timedelta(seconds=3600)).isoformat())
        cb = put(out/'certificates'/f'{name}.json', cert)
        receipt = dict(artifact_type='ROOT_external_capture_whole_batch_reception', issuer='ROOT_transport',
                       at_utc=now(), fixture_only=synthetic, run_id=s['run_id'], condition='R3',
                       batch_id=r['batch_id'], batch_number=r['batch_number'], attempt_number=r['attempt_number'],
                       state='technical_invalid_whole_batch', completion=cb, assignment=r['assignment'],
                       first_origin='unreceived_original_capture_retained_no_selection', actor_created_seal_claimed=False,
                       semantic_correctness_checked=False, reference_or_accuracy_checked=False,
                       retained_actual_files=[v for v in retained.values() if v],
                       error=dict(type='OrphanedControllerWaitReceiptUnavailable',
                                  message='Original parent wait result unavailable; unknown returncode cannot pass unchanged receiver contract.'))
        rb = put(out/'receipts'/f'{name}.json', receipt)
        entries.append(dict(condition='R3', batch_number=r['batch_number'], attempt_number=r['attempt_number'],
                            certificate=cb, receipt_payload_binding=rb, receipt_destination=e['receipt_destination'],
                            remaining_original_attempts=3-r['attempt_number'], exhausted=r['attempt_number']==3))
    plan = dict(artifact_type='failure_only_orphan_closure_plan', fixture_only=synthetic,
                actual_ROOT_adoption=False, scope=bind(scope_path), implementation=bind(__file__),
                original_GO=s['original_GO'], original_adoption=s['original_adoption'], observations=observations,
                entries=entries, unchanged_max_total_attempts=3, new_attempts_launched=0,
                unprepared_batch_numbers=[e['route']['batch_number'] for e in s['entries'] if e not in chosen])
    return put(out/'plan.json', plan)

@contextlib.contextmanager
def lock(path):
    with Path(path).open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield

def install(scope_path, plan_binding, authorization_path, *, synthetic=False):
    """Future explicit ROOT adoption only. No controller launch or original completion writing."""
    s = scope(scope_path, synthetic=synthetic)
    p = load(check(plan_binding)['path']); auth = load(authorization_path)
    require(auth.get('artifact_type') == 'ROOT_failure_only_orphan_closure_adoption'
            and auth.get('issuer') == 'ROOT' and auth.get('template_only') is False
            and auth.get('fixture_only') is synthetic and auth.get('adopted') is True,
            'actual ROOT adoption absent')
    for k, b in dict(plan=plan_binding, scope=bind(scope_path), implementation=bind(__file__),
                     original_GO=s['original_GO'], original_adoption=s['original_adoption']).items():
        require(auth.get(k) == b, 'ROOT adoption binding mismatch: '+k)
    require(p['fixture_only'] is synthetic and p['scope'] == bind(scope_path)
            and p['implementation'] == bind(__file__), 'plan context mismatch')
    allowed = {}
    for e in p['entries']:
        check(e['certificate']); check(e['receipt_payload_binding'])
        r = load(e['receipt_payload_binding']['path']); c = load(e['certificate']['path'])
        require(c['returncode'] is None and c['timed_out'] is None and c['failure_only'] is True
                and c['actual_process_terminal'] is True and c['external_exit_evidence'] is None,
                'only reviewed unknown-returncode failure branch supported')
        require(r['state'] == 'technical_invalid_whole_batch' and r['completion'] == e['certificate'], 'receipt is not failure')
        original = next(x for x in s['entries'] if key(x)==(e['batch_number'],e['attempt_number']))
        require(e['receipt_destination'] == original['receipt_destination'], 'destination drift')
        require((c['condition'],c['batch_number'],c['attempt_number'])==('R3',*key(original)), 'certificate route drift')
        if Path(e['receipt_destination']).exists():
            target = bind(e['receipt_destination']); source = e['receipt_payload_binding']
            require((target['sha256'],target['bytes']) == (source['sha256'],source['bytes']), 'immutable receipt conflict')
            allowed[e['receipt_destination']] = target
    with contextlib.ExitStack() as stack:
        stack.enter_context(lock(Path(s['campaign_directory'])/'ROOT-controller.lock'))
        for e in s['entries']:
            stack.enter_context(lock(Path(e['route']['selection_directory'])/'ROOT-reception.lock'))
        if synthetic:
            require(auth.get('NONHUMAN_process_table') is not None, 'toy process table absent')
            rows = ps_rows(auth['NONHUMAN_process_table'])
        else:
            _, rows = get_ps()
        prior = validate_pair(s, scope_path, p['observations'], synthetic=synthetic, allow_receipts=allowed)
        require(not process_blockers(s, rows, prior['ps_rows']+prior['ps_after_rows']), 'fresh process guard failed')
        require(files_and_conflicts(s, allowed) == prior['retained_files'], 'fresh file guard failed')
        for e in p['entries']:
            dest = Path(e['receipt_destination'])
            if str(dest) not in allowed:
                with dest.open('xb') as f:
                    f.write(Path(e['receipt_payload_binding']['path']).read_bytes()); f.flush(); os.fsync(f.fileno())
    return dict(installed_N=len(p['entries']), launch_count=0, original_completion_created=False)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['observe','prepare','install'])
    ap.add_argument('--scope', default=str(HERE/'scope.json'))
    ap.add_argument('--output'); ap.add_argument('--observation', action='append')
    ap.add_argument('--unknown-batches', help='Explicit comma-separated subset; never infer unknown from absent capture.')
    ap.add_argument('--plan'); ap.add_argument('--adoption')
    a=ap.parse_args()
    if a.mode=='observe': result=observe(a.scope,a.output)
    elif a.mode=='prepare':
        result=prepare(a.scope,[bind(x) for x in a.observation], [int(x) for x in a.unknown_batches.split(',')],a.output)
    else: result=install(a.scope,bind(a.plan),a.adoption)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
