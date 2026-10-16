"""Prepare audited full-five-dimension execution without assigning any labels."""
from pathlib import Path
import json, hashlib, random, copy
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'recall-revision-20261007/llm-v30'
PREV=HERE.parent/'agent-validation-20261007-r2'
DEST=HERE/'llm-v32';DEST.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
runner=(OLD/'run_production_v30.py').read_text().replace('LLM-binary-v30','LLM-binary-v32').replace('llm-v30-empty-','llm-v32-empty-').replace("HERE/'完整系统提示词-v30-候选02.txt'","HERE/'完整系统提示词-v32-候选01.txt'")
(DEST/'run_production_v32.py').write_text(runner)
validator=(OLD/'validate_binary_output.py').read_text().replace('LLM-binary-v30','LLM-binary-v32')
validator=validator.replace('"resolved_text_issue", "resolved_context_issue", "boundary_note"','"resolved_text_issue", "resolved_context_issue", "boundary_note", "material_issue"')
needle='            if issue["status"] not in ISSUE_STATUSES:'
assert needle in validator
validator=validator.replace(needle,'            if issue["status"] == "material_issue":\n                errors.append(f"{loc}:unresolved_material_issue")\n'+needle)
needle='    rows = output["rows"]'
assert needle in validator
early='''    material_issues = [i for i in output.get("issue_records", [])
                       if isinstance(i, dict) and i.get("status") == "material_issue"]
    if material_issues:
        valid_input_ids = {r.get("id") for r in inputs if isinstance(r, dict)}
        return errors + [f"{i.get('id')}:unresolved_material_issue" if i.get("id") in valid_input_ids
                         else f"{i.get('id')}:unknown_material_issue_id" for i in material_issues]

'''
validator=validator.replace(needle,early+needle)
(DEST/'validate_binary_output.py').write_text(validator)
schema=json.loads((OLD/'output_schema_codex_compatible.json').read_text().replace('LLM-binary-v30','LLM-binary-v32'))
schema['properties']['execution_version']['enum']=['LLM-binary-v32']
schema['properties']['issue_records']['items']['properties']['status']['enum'].append('material_issue')
(DEST/'output_schema_codex_compatible.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
# This already-exposed development probe never supplies old labels to the model.
raw={r['id']:r for r in jl(HERE/'effective_blind_inputs_v9.jsonl')}
ref={r['id']:r for r in jl(PREV/'reference/adjudicated_candidate_reference_v8.jsonl')}
llm={r['id']:r for r in jl(PREV/'llm-v31/sealed-final-material-v8/all_predictions_composite.jsonl')}
different=sorted(k for k in ref if ref[k]['labels']!=llm[k]['labels'])
control=random.Random(2026100767).sample(sorted(set(ref)-set(different)),30)
ids=different+control;random.Random(2026100771).shuffle(ids)
probe=DEST/'development_probe_inputs.jsonl'
probe.write_text(''.join(json.dumps(raw[k],ensure_ascii=False)+'\n' for k in ids))
plan={'purpose':'Exposed r2 development diagnosis only; not independent confirmation',
      'n':len(ids),'LLM_disagreement_cases_n':len(different),'random_agreement_controls_n':30,
      'input_sha256':sha(probe),'ids':ids,'no_labels_in_model_input':True,
      'requested_model':'gpt-5.6-sol','reasoning_effort':'medium',
      'material_version':'v9','full_five_dimensions':True,
      'source_sha256':{str(OLD/n):sha(OLD/n) for n in ['run_production_v30.py','validate_binary_output.py','output_schema_codex_compatible.json']},
      'new_runtime_sha256':{str(DEST/n):sha(DEST/n) for n in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']}}
(DEST/'execution_preparation.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'development_probe_n':len(ids),'all_five_dimensions':True,'material_version':'v9'},ensure_ascii=False))
