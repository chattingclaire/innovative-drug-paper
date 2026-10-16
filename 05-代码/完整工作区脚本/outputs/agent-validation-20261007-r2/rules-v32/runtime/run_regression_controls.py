"""Run applicable frozen controls against the separate v32 candidate runtime."""
import sys,unittest,io,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent))
import policy_coding_v27 as coder
assert Path(coder.__file__).parent==ROOT
SUPERSEDED='test_rules_se.SafetyEffectivenessTest.test_v28_guideline_inclusion_is_predicate_not_bare_title'
def flatten(s):
 for x in s:
  if isinstance(x,unittest.TestSuite):yield from flatten(x)
  else:yield x
def main():
 loader=unittest.defaultTestLoader
 mods=['test_rules_se','test_rules_ec','test_rules_if','test_context_validation','test_parent_certificates','test_integration']
 original=list(flatten(loader.loadTestsFromNames(mods)));assert len(original)==168
 applicable=unittest.TestSuite([t for t in original if t.id()!=SUPERSEDED])
 suites={'applicable_historical':applicable,
         'v30_boundaries':loader.loadTestsFromName('test_v30_effect_boundaries'),
         'v31_relations':loader.loadTestsFromName('test_v31_recall_boundaries'),
         'v2_source_certificates_and_coverage_grammar':loader.loadTestsFromNames(['test_v31_context_certificates','test_coverage_object_synonyms']),
         'v32_entity_boundaries':loader.loadTestsFromName('test_v32_entity_boundaries')}
 out={'classification_version':coder.VERSION,'superseded_preexisting_assumption':SUPERSEDED,
      'validation_status':'Development semantic boundary/regression controls, not independent accuracy validation.','groups':{}}
 for name,suite in suites.items():
  stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
  path=ROOT/(name+'.log');path.write_text(stream.getvalue())
  out['groups'][name]={'tests':r.testsRun,'successful':r.wasSuccessful(),
    'failures':[t.id() for t,_ in r.failures],'errors':[t.id() for t,_ in r.errors],
    'log_path':str(path),'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 (ROOT/'semantic_test_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False))
 assert all(x['successful'] for x in out['groups'].values())
 assert [x['tests'] for x in out['groups'].values()]==[167,9,11,20,12]
if __name__=='__main__':main()
