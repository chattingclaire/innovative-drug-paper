"""Build the documented-development exposure candidate from metadata only.

Normal run writes only candidate-frame.jsonl and coverage.json beside this script.
--check recomputes and compares those files without writing anything.
No source packets, policy bodies, workbook cells, human answers, or prediction tables
are opened. Binding-only files are hashed and never interpreted as case labels.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, hashlib, json, re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
OLD_FRAME='02-methods/prospective-exposure-refresh-root/coordinator-private/future-frame-candidate.jsonl'
OLD_OVERLAY='02-methods/prospective-exposure-refresh-root/future-development-exposure-overlay.json'
OLD_BUILDER='02-methods/prepare-prospective-exposure-refresh-root.py'
DESIGN='05-validation/human200-reception-root/assigned-design-metadata.json'
EXPECTED_FRAME_SHA='b53899e36201233f2c870e875b3b9bfa52a814bc1b81145e78341d7335a0f7a5'
# Each entry is a reviewed source-ID or file-path metadata field, not policy text.
RECEIPTS=[
 ('v3_prior37','06-coding/rule-five-dimension-joint-root/versions/joint-v3-interface-sol/source-reading-log.json','fields',['75_existing_packet_fixture_source_ids'],'development_replay'),
 ('v4_prior37','06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol/source-reading-log.json','fields',['original75_existing_packet_source_ids'],'development_replay'),
 ('v5_prior37_and_S3','06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol/source-reading-log.json','fields',['prior_exposed_original75_packet_ids','authorized_actual_source_ids'],'development_replay'),
 ('v5_S3_saved_interface','08-audits/v5-historical-S3-ledger-interface-sol/inspection-scope.json','fields',['allowed_already_exposed_actual_ids'],'mechanical_audit_only'),
 ('existing77','06-coding/native-llm77-v16-sol/run-manifest.json','manifest_ids',[],'already_development_set_identity'),
 ('current130_first40','08-audits/current-machine-rare-disagreement-semantic-20261011-sol/selected-packet-read-receipts.json','row_ids',['packet_checks'],'actual_semantic_read'),
 ('current130_next90','08-audits/current-machine-rare-disagreement-semantic-20261011-sol/remaining90-packet-read-receipts.json','row_ids',['packet_checks'],'actual_semantic_read'),
 ('v9_original98','08-audits/v9-generic-relationship-repair-design-sol/final-candidate-delivery-20261012-sol/actual-opened-input-bindings.json','paths',['original_packets'],'actual_semantic_development'),
 ('v9_independent98','08-audits/v9-repair-adoption-independent-20261012-sol/final-static-adoption/actual-opened-exposed-packets-and-used-quote-resources.json','row_source_ids',['packet_bindings'],'mechanical_audit_only'),
 ('v10_original98','08-audits/v10-generic-relationship-repair-sol/actual-opened-input-bindings.json','paths',['actual_packets'],'actual_semantic_development'),
 ('v11_packet99','08-audits/v11-protected-data-role-repair-sol/read-scope-and-input-bindings.json','paths',['actual_packet_bindings'],'actual_semantic_development'),
 ('v11_v16_receipt','08-audits/v11-v16-01402-consumption-binding-diagnostic-sol/input-bindings-and-read-scope.json','fields',['selected_record_id'],'mechanical_audit_only'),
]
SUPPORT={
 'v3_235_prior_scope':'06-coding/rule-five-dimension-joint-root/versions/joint-v3-interface-sol/README.md',
 'v4_scope':'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol/README.md',
 'v5_scope':'06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol/README.md',
 'v6_pre_edit':'06-coding/rule-five-dimension-joint-root/versions/joint-v6-direct-content-root/pre-edit-plan.json',
 'v7_delivery':'06-coding/rule-five-dimension-joint-root/versions/joint-v7-relation-content-sol/delivery-report.json',
 'v7_report':'06-coding/rule-five-dimension-joint-root/versions/joint-v7-relation-content-sol/delivery-report.md',
 'v8_delivery':'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/report.json',
 'v8_report':'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/report.md',
 'v9_adoption':'08-audits/v9-final-adoption-and-selection-root/ROOT-static-candidate-adoption.json',
 'E_repair_scope':'08-audits/e-complete-response-coverage-repair-sol/report.md',
 'E_candidate_binding':'06-coding/rule-five-dimension-joint-root/versions/joint-v9-e-outcome-candidate-sol/candidate-freeze.json',
 'v10_literal_combination':'08-audits/v10-if-e-combination-v2-root/literal-combination-proof.json',
 'v10_adoption':'08-audits/v10-if-e-combination-v2-root/ROOT-approved-static-contract.json',
 'v11_release':'06-coding/rule-v11-I-v16-affected-v2-root/rule-production-release.json',
 'v11_algorithm':'06-coding/rule-v11-I-v16-affected-v2-root/algorithm-bindings.json',
 'v16_material_proof':'01-review/source-interface-v16-article6-addendum-sol/byte-and-source-interface-proof.json',
 'v16_material_seal':'01-review/source-interface-v16-article6-addendum-sol/output-seal.json',
 'rule_current_output_seal':'06-coding/rule-full4481-v11-v16-receipt-delta-merged-root/seal.json',
 'llm_current_output_seal':'06-coding/native-full4481-v16-three-member-compatible-root/seal.json',
 'manual':'03-manual/full4481-common-release-20261010-root/manual.txt',
 'prompt':'03-manual/full4481-common-release-20261010-root/execution-prompt.txt',
}
INPUTS={}
def raw(path):
 p=ROOT/path;b=p.read_bytes();new={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if path in INPUTS:assert INPUTS[path]==new,'Input changed during read'
 INPUTS[path]=new
 return b

def load(path):return json.loads(raw(path))
def digest_ids(values):return hashlib.sha256(('\n'.join(sorted(values))+'\n').encode()).hexdigest()
def ids_from_metadata(v):return set(re.findall(r'RECODE25-\d{5}',json.dumps(v,ensure_ascii=False)))
def jbytes(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def main(check=False):
 frame_bytes=raw(OLD_FRAME);assert hashlib.sha256(frame_bytes).hexdigest()==EXPECTED_FRAME_SHA
 rows=[json.loads(line) for line in frame_bytes.splitlines()]
 allowed={'source_id','department','family_id','historical_domain','candidate_domain','current_direct_development_read','new_exclusion_reason'}
 assert len(rows)==4481 and all(set(x)==allowed for x in rows)
 meta={x['source_id']:x for x in rows};assert len(meta)==4481
 assert all(re.fullmatch(r'TEXTFAM-[0-9a-f]{64}',x['family_id']) for x in rows)
 overlay=load(OLD_OVERLAY);raw(OLD_BUILDER)
 old_direct=set(overlay['direct_source_ids']);assert len(old_direct)==331
 assert old_direct=={x['source_id'] for x in rows if x['current_direct_development_read']}
 inherited_ex={x['source_id'] for x in rows if x['candidate_domain']=='exposed'}
 historical_ex={x['source_id'] for x in rows if x['historical_domain']=='exposed'}
 assert len(historical_ex)==3037 and len(inherited_ex)==3220
 assert inherited_ex==set(overlay['candidate_excluded_ids'])
 assert set(meta)-inherited_ex==set(overlay['candidate_remaining_ids'])
 # Reuse original34-source accounting through the sealed explicit331-ID union.
 # Do not reopen its source packets merely to repeat the original identity check.
 inherited_groups=[]
 for g in overlay['source_groups']:
  p=Path(g['binding']['path']);rel=str(p.relative_to(ROOT));raw(rel)
  assert INPUTS[rel]==g['binding'],'Inherited source-group binding changed'
  inherited_groups.append({'name':g['name'],'registered_N':g['N'],'binding':g['binding'],'membership_policy':'Inherited sealed331-ID union; prior builder and original group binding retained.'})
 all_sets={};read_checks=[];followup=set();reasons=defaultdict(set)
 for name,path,mode,keys,kind in RECEIPTS:
  d=load(path)
  if mode=='manifest_ids':v=d # metadata manifest has only IDs, assignments, bindings and model settings
  elif mode=='row_ids':v=[x['id'] for x in d[keys[0]]]
  elif mode=='row_source_ids':v=[x['source_id'] for x in d[keys[0]]]
  elif mode=='paths':v=[x['path'] for x in d[keys[0]]]
  else:v=[d[k] for k in keys]
  found=ids_from_metadata(v);assert found<=set(meta)
  counted=kind!='mechanical_audit_only'
  if counted:
   followup|=found
   for rid in found:reasons[rid].add(name)
  all_sets[name]=found
  read_checks.append({'name':name,'kind':kind,'counted_as_development_seed':counted,'binding':INPUTS[path],'metadata_projection':{'mode':mode,'keys':keys},'record_N':len(found),'source_ids':sorted(found),'source_ids_sha256':digest_ids(found),'outside_prior_candidate_excluded_N':len(found-inherited_ex)})
 assert len(all_sets['existing77'])==77
 assert len(all_sets['v9_original98'])==len(all_sets['v10_original98'])==len(all_sets['v11_packet99'])==98
 assert all_sets['current130_first40']|all_sets['current130_next90']==all_sets['v9_original98']
 assert all_sets['v9_original98']==all_sets['v10_original98']==all_sets['v11_packet99']
 for path in SUPPORT.values():raw(path)
 v16=load(SUPPORT['v16_material_proof'])
 assert v16['other_4480_lines_including_terminators_byte_equal'] is True
 assert v16['current_source_record_contexts_unchanged'] is True
 # Preserve inherited normalization hashes exactly; v16 adds context for01402,
 # with current proposition and its text-family identity unchanged.
 family_members=defaultdict(set)
 for rid,x in meta.items():family_members[x['family_id']].add(rid)
 direct=old_direct|followup
 seed_families={meta[rid]['family_id'] for rid in direct}
 excluded=historical_ex|set().union(*(family_members[f] for f in seed_families))
 remaining=set(meta)-excluded
 assert inherited_ex<=excluded,'Candidate cannot silently restore exposure eligibility'
 witness_by_family=defaultdict(set)
 for rid in direct:witness_by_family[meta[rid]['family_id']].add(rid)
 newrows=[]
 for x in rows:
  rid=x['source_id'];family=x['family_id']
  row=dict(x)
  row['inherited_candidate_domain']=row.pop('candidate_domain')
  row['candidate_domain']='exposed' if rid in excluded else 'remaining'
  row['inherited_current_direct_development_read']=row.pop('current_direct_development_read')
  row['documented_direct_development_seed']=rid in direct
  row['documented_followup_development_seed']=rid in followup
  row['followup_evidence_groups']=sorted(reasons[rid])
  row['same_family_documented_seed_ids']=sorted(witness_by_family[family]) if rid in excluded and rid not in historical_ex else []
  row['candidate_exposure_basis']='historical_exposure' if rid in historical_ex else 'documented_development_seed' if rid in direct else 'same_normalized_text_family' if rid in excluded else None
  newrows.append(row)
 content=b''.join((json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for x in newrows)
 design=load(DESIGN);selected=[{k:x[k] for k in ['source_id','domain','family_id','already_in_development77']} for x in design['records']]
 assert len(selected)==200
 assert Counter(x['domain'] for x in selected)=={'remaining':120,'exposed':80}
 assert all(x['family_id']==meta[x['source_id']]['family_id'] for x in selected)
 selected_remaining={x['source_id'] for x in selected if x['domain']=='remaining'}
 selected_all={x['source_id'] for x in selected}
 def stage(n,names,support,status,note,gap=None):
  ss=set().union(*(all_sets[x] for x in names))
  return {'stage':n,'included_evidence_groups':names,'unique_record_N':len(ss),'support_bindings':[INPUTS[SUPPORT[s]] for s in support],'coverage_status':status,'coverage_explanation':note,'specific_evidence_gap':gap}
 stages=[
  stage('v3',['v3_prior37'],['v3_235_prior_scope'],'ID_receipt_plus_prior_fixture_attestation','37 real-source IDs from existing75 fixtures; source-reading log reports new actual sourceIDs0. New18/independent20 are synthetic; previous235 fixtures are attested already development-exposed.','Identity-stripped235 fixtures are not independently remapped to every real sourceID here; their pre-existing artifact bindings and no-new-source declaration are retained.'),
  stage('v4',['v4_prior37'],['v4_scope'],'ID_receipt_plus_prior_fixture_attestation','Same37 real-source IDs and previous fixed fixtures; exposed old12 reused; numbering/semantic additions are synthetic; log declares new actual sourceIDs0.','No separate sourceID mapping for identity-stripped inherited controls beyond37 packet fixtures; no newly opened real source is declared.'),
  stage('v5',['v5_prior37_and_S3'],['v5_scope'],'explicit_ID_read_scope','Prior37 plus3 authorized S3 identities; standalone S3 audit is mechanical and not an added semantic seed.'),
  stage('v6',['existing77','v5_prior37_and_S3'],['v6_pre_edit','v7_delivery'],'conservative_inherited_development_set','Existing77 plus preceding exposed fixtures included in full; v6 pre-edit scope and v7 baseline linkage establish the repair lineage.','No standalone v6 per-record actual semantic-read receipt located in inspected adopted version directory. Candidate conservatively includes all identified77 development records and inherited fixtures; reviewer must assess the bounded-scope evidence.'),
  stage('v7',['existing77','v5_prior37_and_S3'],['v7_delivery','v7_report'],'named_development_set_plus_delivery_scope','Delivery explicitly reports current77 development and prior finite regressions; all77 included rather than selecting only changed cases.','No separate every-read packet ledger for v7 beyond named77 and inherited fixture bindings; report identifies bounded repairs and no new material release.'),
  stage('v8',['existing77','v5_prior37_and_S3'],['v8_delivery','v8_report'],'named_development_set_plus_delivery_scope','Reuses77 and previous22/75/235; targeted additions are synthetic controls. Entire known development set retained.','Like v7, current77 is included conservatively from named development manifest rather than an independent per-read ledger.'),
  stage('v9',['current130_first40','current130_next90','v9_original98'],['v9_adoption'],'actual_read_ID_receipts_and_adoption','130 reviewed dimension cases resolve to98 unique sourceIDs; two actual read receipts unite exactly to the98 implementation packet bindings.59 new controls are synthetic.'),
  stage('v10',['v10_original98'],['E_repair_scope','E_candidate_binding','v10_literal_combination','v10_adoption'],'actual_read_ID_receipts_plus_E_scope_attestation','I/F uses same98 packet IDs; E repair expressly reuses original189/98 and fixed synthetic E controls; literal combination adds no new real-source set.'),
  stage('v11_v16',['v11_packet99'],['v11_release','v11_algorithm','v16_material_proof','v16_material_seal'],'actual_packet_binding_receipt_and_adoption','99 packet-version bindings resolve to98 unique IDs;01402 has original andv16 versions. Its proposition text remains unchanged, so inherited normalized-text family remains applicable.')
 ]
 result={
  'schema':'documented-development-family-closure-candidate-v1',
  'status':'candidate_ready_for_independent_scope_review_not_registered_for_sampling',
  'scope':'Recorded development through adopted joint-v11 and v16-compatible materials; full4481 metadata frame, no sample draw.',
  'policy':{'family_rule':'Historical_exposed union all full-frame members sharing exact inherited normalized_text_family.family_id with any documented development seed. Hashes are inherited without re-normalizing or reading policy text.','seed_rule':'Carry sealed prior331 semantic IDs; add explicit later semantic-read/development fixtures and the whole established77 development set. Do not add automatic full-corpus predictions, static selection hits, output statistics, pure hash/receipt reads, or synthetic controls as new semantic cases.','current_unit_scope':'A context/source document being visible does not expose all of its other current-unit records automatically; use documented current-record IDs as in prior builder.','prior_human_work':'Original200 forms, domains, IDs, probabilities, weights and already-started human first judgements remain unchanged.'},
  'inherited_groups':inherited_groups,
  'read_metadata_checks':read_checks,
  'stage_coverage':stages,
  'counts':{
   'frame_N':len(rows),'family_N':len(family_members),'historical_domains':dict(Counter(x['historical_domain'] for x in rows)),
   'inherited_domains':dict(Counter(x['candidate_domain'] for x in rows)),
   'prior_registered_direct_ID_N':len(old_direct),'followup_documented_development_ID_N':len(followup),'followup_IDs_not_in_prior_direct_registry_N':len(followup-old_direct),'cumulative_documented_direct_ID_N':len(direct),
   'followup_IDs_newly_outside_prior_exposed_N':len(followup-inherited_ex),
   'newly_exposed_after_family_closure_N':len(excluded-inherited_ex),'current_candidate_domains':{'remaining':len(remaining),'exposed':len(excluded)},
   'cumulative_direct_exclusions_from_historical_remaining_N':len(direct-historical_ex),'cumulative_family_only_exclusions_from_historical_remaining_N':len(excluded-historical_ex-direct),
   'candidate_domains_by_department':{d:dict(Counter(x['candidate_domain'] for x in newrows if x['department']==d)) for d in ['NHC','NHSA','NMPA']},
   'historical200':{'N':200,'historical_remaining_N':120,'historical_exposed_N':80,'historical_remaining_in_candidate_exposed_N':len(selected_remaining&excluded),'historical_remaining_in_candidate_remaining_N':len(selected_remaining&remaining),'total_in_candidate_exposed_N':len(selected_all&excluded),'total_in_candidate_remaining_N':len(selected_all&remaining),'design_or_weights_changed':False}},
  'candidate_membership':{'remaining_ids':sorted(remaining),'exposed_ids':sorted(excluded),'new_exposed_vs_prior_candidate_ids':sorted(excluded-inherited_ex),'remaining_ids_sha256':digest_ids(remaining),'exposed_ids_sha256':digest_ids(excluded)},
  'evidence_limits':[{'type':'specific_stage_receipt_detail','stages':['v3','v4','v6','v7','v8'],'detail':'See each stage specific_evidence_gap. These are finite named evidence limitations, not a general demand to prove that nobody ever read anything.'},{'type':'registration_decision','detail':'This candidate records the complete4481 membership implied by the enumerated evidence. Independent reviewer decides whether inherited fixture attestations and named77 coverage are adequate for a new validation scope; unresolved stage detail must be accepted or resolved explicitly.'}],
  'freeze_bindings':{k:INPUTS[v] for k,v in SUPPORT.items() if k in ['v11_release','v11_algorithm','v16_material_proof','v16_material_seal','rule_current_output_seal','llm_current_output_seal','manual','prompt']},
  'outputs':{'candidate_frame':{'path':str(OUT/'candidate-frame.jsonl'),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()},'builder':{'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}},
  'input_bindings':list(INPUTS.values()),
  'checks':{'frame_unique4481':True,'inherited_direct331_exact':True,'prior_domains_reproduced':True,'family_hashes_inherited':True,'current130_receipts_union_equals98':True,'v9_v10_v11_unique_ID_sets_equal':True,'v16_current_proposition_unchanged':True,'all_registered_IDs_in_frame':True,'no_prior_exposed_record_restored':True,'historical200_domain_counts_preserved':True,'all_input_hashes_rechecked':True},
  'not_performed':{'blind_policy_body_reads':0,'human_answer_reads':0,'model_or_classifier_calls':0,'new_sampling':0,'production_output_changes':0,'old_form_or_weight_changes':0},
  'formal_validation_complete':False,'independent_scope_registered':False}
 for rel,b in list(INPUTS.items()):
  now=(ROOT/rel).read_bytes();assert len(now)==b['bytes'] and hashlib.sha256(now).hexdigest()==b['sha256']
 coverage=jbytes(result)
 if check:
  assert (OUT/'candidate-frame.jsonl').read_bytes()==content
  assert (OUT/'coverage.json').read_bytes()==coverage
  print(json.dumps({'check':'exact_reproduction_passed','counts':result['counts']},ensure_ascii=False))
 else:
  assert not (OUT/'candidate-frame.jsonl').exists() and not (OUT/'coverage.json').exists(),'Use --check for existing outputs'
  (OUT/'candidate-frame.jsonl').write_bytes(content)
  (OUT/'coverage.json').write_bytes(coverage)
  print(json.dumps({'status':result['status'],'counts':result['counts']},ensure_ascii=False))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');main(parser.parse_args().check)
