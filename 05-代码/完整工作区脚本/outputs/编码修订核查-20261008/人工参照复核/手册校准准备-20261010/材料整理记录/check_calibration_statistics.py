"""Numerical verification only: synthetic four-cell tables, no new human labels."""
from pathlib import Path
import importlib.util
import hashlib
import json
import math
import tempfile
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('calibration_results',HERE/'calibration_results.py')
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)
core_path = HERE.parents[4]/'outputs/coding-revision-20261007-r3/statistics/statistical_core_r3.py'
core_sha = hashlib.sha256(core_path.read_bytes()).hexdigest()
assert core_sha == 'a7be8f2a158d4d4ec4c96665306a6c91ac295afeac1b34afbeb6fcbceb83c7da'
spec = importlib.util.spec_from_file_location('verified_statistical_core',core_path)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
tables = [(a,b,c,40-a-b-c) for a in range(41) for b in range(41-a) for c in range(41-a-b)]
existing = core.metrics(np.asarray(tables))
maximum_error = 0.0
undefined = 0
for counts, old in zip(tables,existing):
    pairs = [pair for pair,count in zip([(1,1),(1,0),(0,1),(0,0)],counts) for _ in range(count)]
    result = calibration.kappa_feedback(pairs)
    a,b,c,d = counts
    den = (a+b)*(b+d)+(a+c)*(c+d)
    algebraic = 2*(a*d-b*c)/den if den else None
    if algebraic is None:
        assert result['kappa'] is None and np.isnan(old[0])
        undefined += 1
    else:
        assert math.isclose(result['kappa'],algebraic,abs_tol=1e-14)
        assert math.isclose(result['kappa'],old[0],abs_tol=1e-12)
        maximum_error = max(maximum_error,abs(result['kappa']-old[0]))
    reverse = calibration.kappa_feedback([(b,a) for a,b in pairs])
    assert result['kappa'] == reverse['kappa']
    assert result['n11']+result['n10']+result['n01']+result['n00'] == 40
    assert result['A_1_n'] == reverse['B_1_n']
assert undefined == 2
assert calibration.kappa_feedback([])['kappa'] is None
assert calibration.kappa_feedback([(0,0),(0,1)])['kappa'] == 0
assert calibration.kappa_feedback([(0,1)]*3)['kappa'] == 0
for invalid in [(None,0),('0',0),(True,1),(0,0.0),(2,1)]:
    try:
        calibration.kappa_feedback([invalid])
    except ValueError:
        pass
    else:
        raise AssertionError(f'Invalid label not rejected: {invalid}')
baseline = json.loads((HERE/'回收基线.json').read_text())
result,raw,_ = calibration.evaluate(HERE.parent/'校准试填-A.xlsx',HERE.parent/'校准试填-B.xlsx',baseline)
assert result['new_kappa_generated'] is False and 'dimensions' not in result
assert all(r['filled_label_cells'] == 0 for r in result['submissions'].values())
assert all(len(r['invalid_labels']) == 200 for r in result['submissions'].values())
assert all(not any('发生内容变化' in issue for issue in r['issues']) for r in result['submissions'].values())
assert all(hashlib.sha256(data).hexdigest() == baseline['workbooks'][coder]['blank_file_sha256'] for coder,data in raw.items())
with tempfile.TemporaryDirectory() as tmp:
    bad_path = Path(tmp)/'invalid-input.bin'
    bad_bytes = b'not a workbook: intentional parser failure control'
    bad_path.write_bytes(bad_bytes)
    bad_report,bad_labels,preserved = calibration.inspect_submission(bad_path,'A',baseline)
    assert bad_report['ready'] is False and bad_labels is None and preserved == bad_bytes
    assert bad_report['sha256'] == hashlib.sha256(bad_bytes).hexdigest()
    missing_report,missing_labels,missing_bytes = calibration.inspect_submission(Path(tmp)/'missing-file.xlsx','B',baseline)
    assert missing_report['ready'] is False and missing_labels is None and missing_bytes is None
qa = {'status':'通过','scope':'合成四格数学核查和现有空白表回收拒绝检查；不是新真人判定或论文信度',
      'synthetic_n40_tables_checked':len(tables),'constant_same_category_na_tables':undefined,
      'max_absolute_difference_from_existing_verified_core':maximum_error,
      'independent_integer_algebra_checked':True,'swap_A_B_symmetry_checked':True,
      'invalid_pair_values_rejected':True,'blank_400_labels_not_filled_or_imputed':True,
      'damaged_input_bytes_preserved_for_receipt':True,'missing_file_not_invented':True,
      'current_workbooks_unchanged':True,'new_human_kappa_generated':False,
      'calculation_code_sha256':hashlib.sha256((HERE/'calibration_results.py').read_bytes()).hexdigest(),
      'existing_core_sha256':core_sha,
      'method_reference':'Artstein与Poesio（2008），Cohen κ的边际机会一致及§5.3解释范围；https://aclanthology.org/J08-4004.pdf'}
(HERE/'回收与统计程序核查.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(qa,ensure_ascii=False))
