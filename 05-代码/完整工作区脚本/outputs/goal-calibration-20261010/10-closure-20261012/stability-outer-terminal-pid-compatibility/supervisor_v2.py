"""Thin explicit wrapper launch; reuse the bound original durable wait implementation."""
import argparse
import importlib.util
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('outer_alias_admission', HERE / 'entry.py')
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--compatibility-adoption', required=True)
    args = parser.parse_args()
    manifest, compatibility_adoption = compat.authorized(args.compatibility_adoption)
    original = compat.module(manifest['original_supervisor'], 'unchanged_durable_supervisor_helpers')
    require = compat.require
    require(os.getsid(0) == os.getpid(), 'Launch supervisor v2 with start_new_session=True')
    stdin = os.fstat(0)
    require(stat.S_ISCHR(stdin.st_mode) and stdin.st_rdev == os.stat('/dev/null').st_rdev, 'stdin must be DEVNULL')
    with original.exclusive():  # Same exclusion lock as v1, throughout actual wait.
        cfg, authorization, out, diagnosis = original.metadata_gate(args.authorization)
        auth = compat.load(args.authorization)
        expected = {'actual_supervisor_entrypoint': compat.bind(__file__),
                    'outer_compatibility_manifest': compat.bind(HERE / 'manifest.json'),
                    'execution_wrapper': compat.bind(HERE / 'entry.py'),
                    'outer_compatibility_adoption': compatibility_adoption,
                    'reused_wait_implementation': manifest['original_supervisor']}
        require(all(auth.get(k) == v for k, v in expected.items()), 'Actual wrapper/supervisor v2 not authorized')
        require(auth.get('runtime_scope') == 'original_durable_wait_plus_adopted_outer_numeric_alias_guard', 'Runtime disclosure missing')
        require(compat.bind(original.CONFIG) == manifest['original_supervisor_config'], 'Original admission configuration changed')
        observation = original.clear_process_gate(cfg, diagnosis)
        pid_entry = compat.module(cfg['entry'], 'unchanged_PID_birth_fresh_wrapper_observation')
        expected_self = [cfg['python'], '-B', str(Path(__file__).resolve()), '--authorization', args.authorization,
                         '--compatibility-adoption', args.compatibility_adoption]
        require(sys.argv == expected_self[2:], 'Unexpected supervisor v2 argument shape')
        for row in pid_entry.ps_rows():
            if str(HERE / 'entry.py') in row['command'] or str(Path(__file__).resolve()) in row['command']:
                if row['pid'] == os.getpid():
                    require(os.getsid(row['pid']) == row['pid'] and row['command'] == ' '.join(expected_self),
                            'Self exclusion requires exact PID/SID/argv')
                else:
                    raise ValueError('Another compatibility wrapper/supervisor v2 remains active')
        compat.exact(authorization); compat.exact(compatibility_adoption)
        argv = [cfg['python'], '-B', str(HERE / 'entry.py'), '--original-entry', cfg['entry']['path'],
                '--go', cfg['GO']['path'], '--adoption', cfg['original_adoption']['path'],
                '--compatibility-adoption', compatibility_adoption['path']]
        require(auth.get('actual_controller_argv') == argv, 'Actual controller argv not explicitly authorized')
        result = original.wait_and_seal(argv, out, {
            'ROOT_authorization': authorization, 'actual_supervisor_entrypoint': compat.bind(__file__),
            'reused_wait_implementation': manifest['original_supervisor'],
            'original_configuration': compat.bind(original.CONFIG),
            'execution_wrapper': compat.bind(HERE / 'entry.py'),
            'outer_compatibility_adoption': compatibility_adoption, 'fresh_process_gate': observation})
        if not result['actual_wait_returned'] or result['launch_or_supervision_error'] is not None:
            raise SystemExit(1)
        raise SystemExit(result['returncode'] if result['returncode'] >= 0 else 128 - result['returncode'])


if __name__ == '__main__':
    main()
