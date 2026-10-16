"""Reuse existing constructed-only suites against isolated current runtime."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
sys.path.insert(0,str(HERE/'runtime'));sys.path.append(str(BASE/'rules-v33/runtime'))
suite=unittest.TestSuite()
for name in ['test_rules_se','test_rules_ec','test_rules_if']:
 spec=importlib.util.spec_from_file_location(name,BASE/'rules-v33/runtime'/f'{name}.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
with (HERE/'existing_constructed_regression_sealed.log').open('w') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'successful':result.wasSuccessful(),'scope':'existing constructed-only suites; no reference labels loaded'}
(HERE/'existing_constructed_regression_sealed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
