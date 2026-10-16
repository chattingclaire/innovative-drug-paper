"""Run historical controls honestly, then applicable controls and new boundaries."""
from pathlib import Path
import unittest, io, json, hashlib

ROOT=Path(__file__).resolve().parent
MODULES=['test_rules_se','test_rules_ec','test_rules_if','test_context_validation','test_parent_certificates','test_integration']
SUPERSEDED='test_rules_se.SafetyEffectivenessTest.test_v28_guideline_inclusion_is_predicate_not_bare_title'

def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item

def run(suite,name):
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    path=ROOT/name;path.write_text(stream.getvalue())
    return {'tests_run':result.testsRun,'failures':[x.id() for x,_ in result.failures],
            'errors':[x.id() for x,_ in result.errors],'skipped':[(x.id(),reason) for x,reason in result.skipped],
            'successful':result.wasSuccessful(),'log_path':str(path),'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    loader=unittest.defaultTestLoader
    historical=run(loader.loadTestsFromNames(MODULES),'legacy_168_original_expectations.log')
    assert historical['tests_run']==168
    assert historical['failures']==[SUPERSEDED] and not historical['errors']
    applicable=unittest.TestSuite([test for test in flatten(loader.loadTestsFromNames(MODULES)) if test.id()!=SUPERSEDED])
    adapted=run(applicable,'legacy_167_applicable.log')
    new=run(loader.loadTestsFromName('test_v30_effect_boundaries'),'v30_boundary_controls.log')
    assert adapted['successful'] and adapted['tests_run']==167
    assert new['successful'] and new['tests_run']==9
    summary={'historical_original_expectations':historical,'applicable_historical_controls':adapted,
             'new_constructed_controls':new,'superseded_assumptions':[{'test_id':SUPERSEDED,
             'old_assumption':'纳入某诊疗方案的药品这一名单/申报身份本身赋E=1。',
             'new_boundary':'无独立治疗推荐、效果/获益或相应证据时E=0；原函数其他两个负控制已在新边界测试继续执行。'}],
             'validation_status':'开发边界/回归测试，不是新增独立样本准确性验证。'}
    (ROOT/'semantic_test_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'old_controls':168,'old_passed':167,'superseded':1,'applicable_passed':167,'new_test_methods_passed':9},ensure_ascii=False))

if __name__=='__main__':main()
