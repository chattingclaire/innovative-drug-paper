#!/usr/bin/env python3
"""Metadata-only audit. Never opens reserved policy texts or machine predictions."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import json, hashlib, math, zipfile, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
R=ROOT/'outputs/coding-revision-20261007-r3'
D=R/'admin/future_human_v5_sampling_PRIVATE.json'
M=R/'future-human-validation-v5/source_update_manifest.json'
U=R/'future-human-validation-v5/使用说明.md'
P=ROOT/'outputs/final-three-department-20261008-adopted-results/论文修订稿-三部门实测结果版.docx'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def binding(p): return {'path':str(p),'sha256':sha(p)}
def frac(x): return {'exact_fraction':str(x),'decimal':float(x)}
d=json.loads(D.read_text());m=json.loads(M.read_text())
# Access only structural sampling metadata. No identifiers are exported.
fam=d['all_eligible_families'];sample=d['sample'];groups=['NMPA','NHSA','NHC']
checks={};out={}
checks['240_rows']=len(sample)==240
checks['240_unique_units']=len({s['original_id'] for s in sample})==240
checks['240_unique_families']=len({s['family_id'] for s in sample})==240
checks['2012_eligible_families']=len(fam)==2012
checks['family_members_match_k']=all(len(f['members'])==f['k_family'] for f in fam)
checks['family_unique']=len({f['family_id'] for f in fam})==len(fam)
fm={f['family_id']:f for f in fam}
checks['each_selected_unit_is_valid_family_member']=all(s['original_id'] in fm[s['family_id']]['members'] and s['group']==fm[s['family_id']]['group'] and s['k_family']==fm[s['family_id']]['k_family'] for s in sample)
for g in groups:
 fs=[f for f in fam if f['group']==g];ss=[s for s in sample if s['group']==g]
 F=len(fs);n=len(ss);N=sum(f['k_family'] for f in fs)
 weights=[Fraction(F*s['k_family'],80) for s in ss]
 checks[g+'_counts']=F==d['eligible_family_counts'][g] and N==d['eligible_unit_counts'][g] and n==80
 checks[g+'_probability_weight_formula']=all(s['eligible_family_count']==F and s['sampled_family_count']==80 and math.isclose(s['family_inclusion_probability'],float(Fraction(80,F)),rel_tol=1e-12) and math.isclose(s['within_family_selection_probability'],float(Fraction(1,s['k_family'])),rel_tol=1e-12) and math.isclose(s['unit_inclusion_probability'],float(Fraction(80,F*s['k_family'])),rel_tol=1e-12) and math.isclose(s['unit_analysis_weight'],float(Fraction(F*s['k_family'],80)),rel_tol=1e-12) for s in ss)
 out[g]={'frame_families':F,'frame_units':N,'sample_families':n,'sample_units':n,'first_stage_sampling_fraction':frac(Fraction(n,F)),'population_family_size_distribution':dict(sorted(Counter(f['k_family'] for f in fs).items())),'sample_family_size_distribution':dict(sorted(Counter(s['k_family'] for s in ss).items())),'sample_weight_sum':frac(sum(weights,Fraction())),'weight_min':frac(min(weights)),'weight_max':frac(max(weights)),'census':n==F}
mp=d['mapping'];checks['two_coders_same240']=len(mp)==480 and len({x['coder'] for x in mp})==2 and all(len([x for x in mp if x['coder']==c])==240 and {x['original_id'] for x in mp if x['coder']==c}=={s['original_id'] for s in sample} for c in {x['coder'] for x in mp})
checks['source_only_no_resample_or_reweight']=m['source_only'] and not any(m[k] for k in ['resampled','sampling_design_changed','sample_weights_changed','sample_order_changed'])
checks['manifest_blank_identity_labels_reasons_evidence']=m['all_identity_coding_reason_evidence_fields_blank'] is True
checks['manifest_context_exact_v14']=m['all_contexts_equal_exact_frozen_v14'] is True
checks['manifest_no_unit_text_changes']=m['original_text_changes']==0
checks['manuscript_expected_sha']=sha(P)=='dd23f6e6e426d0a914eb206fb85ee152bdb0400700e769d8c28390efecb7226f'
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with zipfile.ZipFile(P) as z: ps=ET.fromstring(z.read('word/document.xml')).find(w+'body').findall(w+'p')
paragraphs=[]
for i in list(range(45,55))+[69,106,109]:
 text=''.join(t.text or '' for t in ps[i].iter(w+'t'))
 paragraphs.append({'zero_based_direct_body_p_index':i,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text})
checks['direct_body_paragraphs_172']=len(ps)==172
res={'status':'PASS_METADATA_ONLY' if all(checks.values()) else 'FAIL','audit_scope':'Sampling metadata, material manifest, instructions, and specified manuscript prose only. No reserved unit text or machine row labels opened.','verified_real_human_labels_received':False,'human_statistics_executed':False,'human_bootstrap_replicates_executed':0,'input_bindings':[binding(p) for p in [D,M,U,P]],'audit_script':binding(Path(__file__)),'checks':checks,'department_design':out,'sampling_seed':d['seed'],'sampling_design':d['sampling_design'],'normalization':d['normalization'],'scope':d['scope'],'historical_document_exposure_note':d['historical_full_document_exposure_note'],'exclusion_counts':{k:len(d[k]) for k in ['known_development_excluded_ids','current_training_excluded_ids','additional_units_excluded_by_normalized_text','cross_department_families_excluded']},'manifest_reported_blank_fields':m['all_identity_coding_reason_evidence_fields_blank'],'blank_fields_verification_boundary':'Manifest declaration verified by manifest hash; no reserved coder material files opened in this audit.','read_manuscript_paragraphs':paragraphs,'limitations':['The blank package status does not establish whether contacted humans have privately started work. No raw human submissions are available to this audit.','Remaining current-unit normalized-text family frame; not external unseen-document validation, excluded families, or the entire corpus.','Sample sums of inverse inclusion weights need not equal known frame unit counts; no unrequested calibration or change of estimand.']}
(OUT/'人检抽样元数据独立审计.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':res['status'],'checks':len(checks),'all_checks_pass':all(checks.values()),'outputs':[binding(OUT/'人检抽样元数据独立审计.json')]},ensure_ascii=False))
assert all(checks.values())
