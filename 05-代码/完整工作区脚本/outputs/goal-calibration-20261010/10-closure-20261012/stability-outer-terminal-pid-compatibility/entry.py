"""Narrow runtime adapter for already-certified historical PID/PGID aliases."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
TZ = dt.timezone(dt.timedelta(hours=8))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def exact(value):
    require(bind(value['path']) == value, 'Changed binding: ' + value['path'])


def module(value, name):
    exact(value)
    spec = importlib.util.spec_from_file_location(name, value['path'])
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def numeric_alias_guard(original_owned, certificate_at, expected_context=None):
    certified = dt.datetime.fromisoformat(certificate_at)
    require(certified.tzinfo is not None, 'Certificate timezone unknown')

    def guarded(rows, known, pgids, lease_pids=()):
        require(rows and len({r['pid'] for r in rows}) == len(rows), 'Ambiguous process table')
        if expected_context is not None:
            require(known == expected_context['known_owned_process_identity_registry']
                    and set(pgids) == set(expected_context['tracked_pgids'])
                    and list(lease_pids) == expected_context['all_lease_pids'], 'Unbound historical process context')
        bypid = {r['pid']: r for r in rows}

        def distinct_after(row):
            if row is None or any(row['pid'] == k['pid'] and row['lstart'] == k['lstart'] for k in known):
                return False
            try:
                birth = dt.datetime.strptime(row['lstart'], '%a %b %d %H:%M:%S %Y').replace(tzinfo=TZ)
                return birth > certified
            except (ValueError, TypeError, KeyError):
                return False  # Unreadable birth never relaxes a numeric blocker.

        kept_leases = [pid for pid in lease_pids if not distinct_after(bypid.get(pid))]
        kept_pgids = set(pgids)
        for pgid in pgids:
            members = [r for r in rows if r['pgid'] == pgid]
            leader = bypid.get(pgid)
            # A late-born child alone cannot establish that an old PGID is reused.
            if (members and leader is not None and leader['pgid'] == pgid
                    and distinct_after(leader) and all(distinct_after(r) for r in members)):
                kept_pgids.remove(pgid)
        # Original known-identity, command predicates and descendant closure remain exact.
        return original_owned(rows, known, kept_pgids, kept_leases)
    return guarded


def authorized(adoption_path):
    manifest = load(HERE / 'manifest.json')
    for value in manifest.values():
        if isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'}:
            exact(value)
    for value in load(HERE / 'seal.json')['files']:
        exact(value)
    authorization = bind(adoption_path)
    adoption = load(adoption_path)
    require(adoption.get('artifact_type') == 'ROOT_outer_terminal_numeric_PID_alias_compatibility_adoption'
            and adoption.get('issuer') == 'ROOT' and adoption.get('template_only') is False
            and adoption.get('fixture_only') is False and adoption.get('adopted') is True,
            'ROOT compatibility adoption required')
    expected = {'candidate_seal': bind(HERE / 'seal.json'), 'manifest': bind(HERE / 'manifest.json'),
                'wrapper_entry': bind(__file__), 'original_entry': manifest['original_entry'],
                'original_GO': manifest['original_GO'], 'original_adoption': manifest['original_adoption'],
                'production_terminal_certificate': manifest['production_terminal_certificate'],
                'actual_refusal_diagnosis': manifest['diagnosis']}
    require(all(adoption.get(k) == v for k, v in expected.items()), 'ROOT adoption binding mismatch')
    require(adoption.get('numeric_alias_only') is True and adoption.get('receiver_schema_max3_unchanged') is True,
            'ROOT adoption must retain full original reception and retry contract')
    exact(authorization)
    return manifest, authorization


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-entry', required=True)
    p.add_argument('--go', required=True)
    p.add_argument('--adoption', required=True)
    p.add_argument('--compatibility-adoption', required=True)
    args = p.parse_args()
    manifest, authorization = authorized(args.compatibility_adoption)
    require(Path(sys.executable).resolve() == Path(manifest['python']).resolve(), 'Frozen Python required')
    require(bind(args.original_entry) == manifest['original_entry'] and bind(args.go) == manifest['original_GO']
            and bind(args.adoption) == manifest['original_adoption'], 'Original entry/GO/adoption changed')
    require(subprocess.check_output(['/bin/date', '+%z'], text=True).strip() == '+0800', 'Process birth timezone unknown')
    common = module(manifest['terminal_common'], 'terminal_common')
    cert = common.verify_certificate(manifest['production_terminal_certificate'], fresh=False)
    proof = common.load(cert['terminal_evidence_bindings'][0]['path'])
    require(proof['new13_terminal_observation'] == manifest['historical_terminal_observation'], 'Different terminal history')
    observation = load(manifest['historical_terminal_observation']['path'])
    common.owned = numeric_alias_guard(common.owned, cert['at_utc'], observation)
    sys.modules['terminal_common'] = common
    original = module(manifest['original_entry'], 'unchanged_PID_birth_v2_after_outer_alias_fix')
    exact(authorization)
    sys.argv = [manifest['original_entry']['path'], '--mode', 'run', '--target', 'stability13',
                '--go', args.go, '--adoption', args.adoption]
    original.main()  # Original fresh terminal verification still runs; no direct dispatch bypass.


if __name__ == '__main__':
    main()
