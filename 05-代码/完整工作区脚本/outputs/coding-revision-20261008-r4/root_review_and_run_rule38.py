"""Root seals the semantically reviewed candidate, then runs one complete shadow.

No reference labels, scores or reserved sentences are printed/read for selection.
The root reviewed all predeclared constructs and the complete new module/diff.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEV = HERE / 'rules-v38-development'
OUT = HERE / 'rules-v38-shadow-full-v14'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    manifest_path = DEV / 'candidate_review_manifest_v2.json'
    manifest = json.loads(manifest_path.read_text())
    checked = 0
    for key in ('production_code_sha256', 'review_sha256', 'test_sha256', 'result_sha256'):
        for path, expected in manifest[key].items():
            assert sha(path) == expected, path
            checked += 1
    pre = manifest['preimplementation_v2_freeze']
    assert sha(pre['path']) == pre['sha256']
    parent = manifest['parent_candidate_freeze']
    assert sha(parent['path']) == parent['sha256']
    parent_data = json.loads(Path(parent['path']).read_text())
    for path, expected in parent_data['production_code_sha256'].items():
        assert sha(path) == expected, path
    review = {
        'status': 'root_semantic_code_control_review_pass_for_complete_shadow_not_independent_validity',
        'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'review_manifest_sha256': sha(manifest_path),
        'root_review': [
            'Reviewed complete local grammar module and two-line entry integration; no IDs, departments, filenames, human answers or scores used.',
            'Current drug, operative/proposed membership relation and actual institutional routine supply scope must be explicit. Application/administrative objects are separated.',
            'Root rejected two v1 expectations that incorrectly excluded explicit proposed/recommended coverage; v1 remains preserved and v2 was frozen before the correction.',
            'Reviewed v2 positive/negative boundaries, including conditional/negative exit and proposals. A missing local grammar match is a coverage limit, not a construct-negative human definition.',
            'Evidence offsets preserved. New module only adds F access evidence; existing dimensions and old candidate bytes remain unchanged.',
        ],
        'bound_files_checked_n': checked,
        'known_reserved_exposed_exception': 'RECODE25-01361 remains an exposed development case; no fresh independent-validation claim.',
        'model_calls': 0,
        'reference_labels_loaded': False,
        'adoption_requires': 'Complete mechanical comparison, all new nonreserved changes semantic review, reserved aggregate only, then synchronized findings and manuscript QA.',
    }
    review_path = HERE / 'root-rule-v38-v2-preflight.json'
    assert not review_path.exists()
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
    freeze = dict(manifest)
    freeze['status'] = 'root_reviewed_frozen_for_complete_shadow'
    freeze['root_review'] = {'path': str(review_path), 'sha256': sha(review_path)}
    freeze['root_builder_sha256'] = sha(__file__)
    freeze_path = DEV / 'candidate_freeze.json'
    assert not freeze_path.exists() and not OUT.exists()
    freeze_path.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + '\n')
    OUT.mkdir()
    command = [sys.executable, str(DEV/'runtime/predict_batch.py'),
        '--module-dir', str(DEV/'runtime'),
        '--input', str(ROOT/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'),
        '--output', str(OUT/'all_predictions_material_v14_shadow.jsonl'),
        '--version-expected', 'v38-institution-routine-drug-supply-membership-development',
        '--freeze', str(freeze_path)]
    (OUT/'actual_command.json').write_text(json.dumps(command, ensure_ascii=False, indent=2)+'\n')
    completed = subprocess.run(command, capture_output=True, text=True)
    (OUT/'actual_stdout.log').write_text(completed.stdout)
    (OUT/'actual_stderr.log').write_text(completed.stderr)
    (OUT/'actual_exit_code.txt').write_text(str(completed.returncode)+'\n')
    print(json.dumps({'exit_code': completed.returncode, 'freeze_sha256': sha(freeze_path),
                      'root_preflight_sha256': sha(review_path), 'output_directory': str(OUT),
                      'stdout': completed.stdout[-2000:], 'stderr': completed.stderr[-1000:]}, ensure_ascii=False))
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
