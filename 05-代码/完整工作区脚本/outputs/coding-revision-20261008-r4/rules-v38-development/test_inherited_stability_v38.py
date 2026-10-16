"""Exercise v38 on inherited synthetic units and compare synthetic-only pipelines."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent
P=R.parent/'rules-v37.2-development'
sys.path.insert(0,str(R/'runtime'))
from policy_coding_v27 import code_unit
from rules_supply_membership_v38 import revise,RULE
from rule_support import rebuild
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=json.loads((P/'candidate_freeze.json').read_text())
assert all(sha(p)==expected for p,expected in f['production_code_sha256'].items())

overlay=[]
for packet,key in [('constructed_controls_results.json','rows'),('legacy_v35_controls.json','rows'),('inherited67_controls.json','rows'),('inherited_v37_constructed_only_results.json','constructed_rows'),('patch_overlay_controls_results_v37.json','purpose_rows')]:
    for row in json.loads((R/packet).read_text())[key]:
        text=row.get('constructed_text',row.get('text'))
        rec={'unit_text':text,**(row.get('context_fixture') or {})}
        result=rebuild(revise(rec,{'judgement_status':'determined','evidence':[],'suppressions':[]}))
        assert not result['evidence'],(packet,row['name'],result)
        overlay.append({'packet':packet,'name':row['name'],'new_branch_abstains':True})

# These old controls previously exercised the complete unseeded pipeline.
# Reuse only their synthetic text and locally generated, authenticated source
# fixtures.  No corpus/reference path is read by this test.
records=[];locators=[]
scope='药物临床试验期间，用于防治严重疾病的创新药或者改良型新药，申请人可以申请适用突破性治疗药物程序。'
for packet,subdir in [('end_to_end_controls_results_v37_1.json','end_to_end_constructed_source_fixtures'),('end_to_end_controls_results_v37_2.json','complete_object_constructed_source_fixtures')]:
    for row in json.loads((R/packet).read_text())['rows']:
        text=row['constructed_text'];rec={'unit_text':text}
        if row['scope_fixture']:
            source=R/subdir/(row['name']+'.txt');candidate=R/subdir/(row['name']+'.json')
            rec.update(unit_source=str(source.resolve()),unit_source_sha256=sha(source),candidate_file=str(candidate.resolve()),candidate_sha256=sha(candidate),unit_id='unit')
            rec['verified_innovation_scope_v27']={'text':scope,'text_sha256':hashlib.sha256(scope.encode()).hexdigest(),'source_sha256':sha(source),'original_unit_sha256':hashlib.sha256(text.encode()).hexdigest(),'component':'突破性治疗程序','verified':True,'locator':{'source_lines':[1],'paragraph_id':'scope'},'component_binding':{'unit_id':'unit','candidate_sha256':sha(candidate)}}
        records.append(rec);locators.append({'packet':packet,'name':row['name']})
inputs=R/'inherited50_synthetic_pipeline_inputs.json';inputs.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
baseline_code="""import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from policy_coding_v27 import code_unit
records=json.loads(Path(sys.argv[2]).read_text())
Path(sys.argv[3]).write_text(json.dumps([code_unit(r) for r in records],ensure_ascii=False,indent=2)+'\\n')
"""
baseline=R/'inherited50_baseline_v37_2_synthetic_results.json'
completed=subprocess.run([sys.executable,'-B','-c',baseline_code,str((P/'runtime').resolve()),str(inputs.resolve()),str(baseline.resolve())],capture_output=True,text=True,check=True)
old=json.loads(baseline.read_text());comparisons=[]
for locator,record,previous in zip(locators,records,old):
    current=code_unit(record)
    a=dict(previous);b=dict(current);a.pop('version',None);b.pop('version',None)
    assert a==b,(locator,previous,current)
    comparisons.append({**locator,'all_labels_and_evidence_identical_except_version':True})
report={'all_checks_pass':True,'v38_branch_abstention_inherited_n':len(overlay),'full_unseeded_pipeline_comparison_n':len(comparisons),'not_independent_validation':True,'actual_corpus_units_run':0,'baseline_subprocess_python_no_bytecode':True,'parent_frozen_runtime_24_hashes_match':True,'reference_labels_or_scores_read':False,'test_sha256':sha(__file__),'synthetic_inputs_sha256':sha(inputs),'baseline_synthetic_results_sha256':sha(baseline),'overlay_rows':overlay,'pipeline_comparison_rows':comparisons}
(R/'inherited_stability_results_v38.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('all_checks_pass','v38_branch_abstention_inherited_n','full_unseeded_pipeline_comparison_n','actual_corpus_units_run')},ensure_ascii=False))
