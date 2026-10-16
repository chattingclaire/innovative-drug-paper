"""Read-only old-directory verification; writes only this new delivery folder."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parent
baseline=json.loads((ROOT/'old-version-preservation-baseline.json').read_text())
old=Path(baseline['old_root'])
expected={}
for item in baseline['files']:
    p=Path(item['path']);p=p if p.is_absolute() else old/p
    expected[p.relative_to(old).as_posix()]=item
current={p.relative_to(old).as_posix():p for p in old.rglob('*') if p.is_file()}
changed=[key for key in expected.keys()&current.keys()
         if hashlib.sha256(current[key].read_bytes()).hexdigest()!=expected[key]['sha256'] or current[key].stat().st_size!=expected[key]['bytes']]
result={'status':'unchanged' if not changed and set(expected)==set(current) else 'FAILED',
        'old_root':str(old),'old_file_count_including_cache':len(expected),
        'original_sealed_manifest_files_verified':baseline['sealed_manifest_files_verified'],
        'changed_files':sorted(changed),'added_files':sorted(set(current)-set(expected)),
        'missing_files':sorted(set(expected)-set(current)),
        'previous_engine_sha256':hashlib.sha256((old/'metrics_engine.py').read_bytes()).hexdigest(),
        'new_folder_local_frozen_copy_sha256':hashlib.sha256((ROOT/'old_engine_source_frozen.py').read_bytes()).hexdigest(),
        'old_directory_mutations':0 if not changed and set(expected)==set(current) else None}
(ROOT/'old-version-preservation-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if result['status']!='unchanged':raise AssertionError(result)
if result['previous_engine_sha256']!=result['new_folder_local_frozen_copy_sha256']:raise AssertionError('Previous source copy mismatch')
print(json.dumps(result,ensure_ascii=False))
