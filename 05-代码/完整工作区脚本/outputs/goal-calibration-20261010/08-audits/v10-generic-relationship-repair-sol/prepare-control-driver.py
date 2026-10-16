from pathlib import Path
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol'
s=(OLD/'run_finite_controls.py').read_text()
s=s.replace("V=O.parent/'joint-v8-target-product-gap-sol'","V=O.parent/'joint-v9-generic-relationship-sol';AUD=R/'08-audits/v10-generic-relationship-repair-sol'")
s=s.replace('out=O/sys.argv[1]','out=AUD/sys.argv[1]')
s=s.replace("extra=[O/","extra=[V/").replace(",O/'supplemental",",V/'supplemental")
s=s.replace("for path in extra:synthetics['cases'].extend(json.loads(path.read_bytes())['cases'])","for path in extra:synthetics['cases'].extend(json.loads(path.read_bytes())['cases'])\nextra.append(AUD/'new-controls-fixed-before-edit.json');synthetics['cases'].extend(json.loads(extra[-1].read_bytes())['cases'])")
s=s.replace("new['dimensions']._v9_repair_gate","new['relations']._v10_repair_gate")
s=s.replace("path.startswith('v9_')","path.startswith(('v9_','v10_'))")
s=s.replace("'source_events':v.source_view_events}","'source_events':v.source_view_events,'input_unchanged':v.unit==before}")
# Add full relation/state identity checks, independent of expected values.
s=s.replace(" results.append(row)"," row['old_relations_preserved']=('baseline' in row and row['baseline']['relations']==[r for r in row['candidate']['relations'] if r['kind']!='v10_IF_relationship'])\n row['source_state_equal']=('baseline' in row and all(row['baseline'][k]==row['candidate'][k] for k in ['material_requests','source_requests','source_events']))\n if c.get('must_not_add_v10_positive') and 'candidate' in row:row['no_unproved_v10_positive']=not any(p['basis_path'].startswith('v10_') for d in ['I','F'] for p in row['candidate']['decisions'][d]['details'].get('positive_candidates',[])) and not any(row['candidate']['decisions'][d]['basis_path'].startswith('v10_') for d in ['I','F'])\n results.append(row)")
s=s.replace("'all_cases_retained':True}","'all_cases_retained':True,'original_control_N':189,'new_counter_control_N':10,'old_relation_mismatch':[c['name'] for c in results if not c['old_relations_preserved']],'source_state_mismatch':[c['name'] for c in results if not c['source_state_equal']],'unproved_v10_positive':[c['name'] for c in results if c.get('no_unproved_v10_positive') is False],'gate_in_N':sum(new['relations']._v10_repair_gate(new['relations'].norm(c['candidate']['decisions']['I']['current_proposition']['text'])) for c in results if 'candidate' in c)}")
# No assumed output shape for the optional gate count.
s=s.replace(",'gate_in_N':sum(new['relations']._v10_repair_gate(new['relations'].norm(c['candidate']['decisions']['I']['current_proposition']['text'])) for c in results if 'candidate' in c)",'')
(V/'run_finite_controls.py').write_text(s)
print('prepared baseline-v9 driver; no classifier execution')
