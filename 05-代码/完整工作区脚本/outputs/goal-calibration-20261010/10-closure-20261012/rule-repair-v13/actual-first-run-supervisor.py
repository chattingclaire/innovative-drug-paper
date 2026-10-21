import importlib.util,sys
from pathlib import Path
sys.dont_write_bytecode=True
helper_binding={'path': '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/stability-durable-supervisor/supervisor.py', 'bytes': 13069, 'sha256': '3b3f631aa58867d160864fd3e1dd9e7bc7d7fa3b758a029554dc0cf854f60829'}
release_binding={'path': '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/ROOT-execution-release-01.json', 'bytes': 7851, 'sha256': '34cb7ec630e8b766e7eafdfd519c972ae9a47b2a9ceaeffd9e87c4ab476d71d8'}
scope_binding={'path': '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/ROOT-frozen-execution-scope-01.json', 'bytes': 781535, 'sha256': '6929bf22659c70a470f016189e8f8dd654e5e6f028e68e33ccd9a7750f55ab8c'}
argv=['/opt/homebrew/opt/python@3.14/bin/python3.14', '-B', '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/execution-preparation/rule_driver.py', '--scope', '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/ROOT-frozen-execution-scope-01.json', '--scope-sha256', '6929bf22659c70a470f016189e8f8dd654e5e6f028e68e33ccd9a7750f55ab8c', '--input', '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v12/execution-preparation/affected-current-v16-common-lines.jsonl', '--input-sha256', 'e9ffbf6554e1e095f27fe912f7617003be0633f0c3224315592403a3b2ef1625', '--out', '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-v13b-sf-v16-affected-root/run-affected-first']
waitdir='/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/actual-first-run-wait'
spec=importlib.util.spec_from_file_location('bound_actual_wait',helper_binding['path'])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for item in (helper_binding,release_binding,scope_binding):m.exact(item)
result=m.wait_and_seal(argv,waitdir,{'purpose':'single_actual_rule_SF2082_execution','ROOT_release':release_binding,'frozen_scope':scope_binding,'helper':helper_binding,'no_automatic_restart':True})
if not result['actual_wait_returned'] or result['launch_or_supervision_error'] is not None:raise SystemExit(1)
raise SystemExit(result['returncode'] if result['returncode']>=0 else 128-result['returncode'])
