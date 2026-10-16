"""Read-only, explicit-adoption measurement adapter. Never creates/edits DOCX.

No glob/latest/best-score selection, calls to models, or bootstrap execution.
PENDING adoption stops before reading any prediction or statistical file.
V3 adds explicit shared-rule-input and bound-rule-prediction dual-ID readers.
V2 explicit196+25 execution profile and strict LLM/reference readers are unchanged.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from collections import Counter
import argparse, datetime, hashlib, json, math, re, sys

DIMS = ('S','E','Ec','I','F')
GROUPS = ('NMPA','NHSA','NHC')
DIM_NAMES = dict(zip(DIMS,('安全性','有效性','经济性','创新性','公平性')))
GROUP_NAMES = {'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
COUNTS = {'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443}
FRAMES = {'NMPA':947,'NHSA':760,'NHC':60}
METRICS = ('kappa','precision','recall','f1')
CELLS = ('TP','FP','FN','TN')
MANUAL = ('FINAL_CONCLUSION_ATTENTION_SUMMARY','FINAL_CORE_SENSITIVITY_SUMMARY',
          'FINAL_DEPARTMENT_COMPARISON_SUMMARY','FINAL_ERROR_PATTERN_SUMMARY',
          'FINAL_FULL_CORPUS_COMPOSITION_SUMMARY','FINAL_LLM_EXECUTION_SUMMARY',
          'FINAL_LLM_STABILITY_SUMMARY','PROBABILITY180_ATTENTION_SUMMARY')
AUTO = ('FINAL_RULES_ID','FINAL_LLM_ID','AC_KAPPA_S_E_Ec_I_F','DEPARTMENT_DIRECTION_MATCH_N') + tuple(f'RULE_Q_{g}_{d}' for g in GROUPS for d in DIMS) + tuple(f'{role}_{kind}_{g}' for role in ('RULE','LLM') for kind in ('Ec','JOINT','P_F_GIVEN_Ec') for g in ('NHSA','NHC'))
FIELD = re.compile(r'\{\{([A-Za-z][A-Za-z0-9_]*)\}\}')
SHA = re.compile(r'^[0-9a-f]{64}$')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'statistics'))
import candidate03_reconciled_execution_profile_v2 as reconciled_v2

class GateError(ValueError): pass
def require(value, message):
    if not value: raise GateError(message)
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
def sha_text(s): return hashlib.sha256(s.encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def save(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def same_binding(a,b): return isinstance(a,dict) and isinstance(b,dict) and a.get('path')==b.get('path') and a.get('sha256')==b.get('sha256')
def numeric_same(a,b):
    return (a is None and b is None) or (a is not None and b is not None and type(a) in (int,float) and math.isfinite(a) and math.isclose(a,float(b),rel_tol=1e-10,abs_tol=1e-10))
def finite_or_none(x): return x is None or (type(x) in (int,float) and math.isfinite(x))
def number_text(x,places=3): return 'NA' if x is None else f'{float(x):.{places}f}'
def sign(x): return (x>0)-(x<0)
def citation_coverage(text,bibliography):
    for m in re.finditer(r'\[([0-9,，;；\s–—-]+)\]|〔([A-Za-z][A-Za-z0-9_;；,，\s]*)〕',text):
        if m[1] is not None:
            for part in re.split(r'[,，;；]',m[1]):
                ends=re.split(r'[–—-]',part.strip())
                for n in range(int(ends[0]),int(ends[-1])+1):
                    require(bibliography['old_number_to_new'].get(str(n)) is not None,'Narrative adds an unmapped citation; new preflight required: '+str(n))
        else:
            for key in re.split(r'[;；,，]',m[2]):
                require(bibliography['source_key_to_new'].get(key.strip()) is not None,'Narrative adds an unmapped source key; new preflight required: '+key.strip())
def fraction_value(x):
    return {'exact_fraction':None if x is None else str(x),'value':None if x is None else float(x)}
def safe_fraction(a,b): return F(a,b) if b else None

class BoundIO:
    def __init__(self): self.bindings={}; self.documents={}; self.expanded=set()
    def verify(self,b):
        require(isinstance(b,dict) and isinstance(b.get('path'),str) and isinstance(b.get('sha256'),str),'Missing path/SHA binding')
        p=Path(b['path']); require(p.is_absolute() and p.is_file(),'Missing absolute bound file: '+str(p))
        require(bool(SHA.fullmatch(b['sha256'])),'Malformed SHA: '+str(p))
        key=str(p)
        if key in self.bindings: require(self.bindings[key]['sha256']==b['sha256'],'Conflicting SHA binding: '+key)
        require(digest(p)==b['sha256'],'SHA mismatch: '+key)
        self.bindings[key]={'path':key,'sha256':b['sha256']}
        return p
    def tree(self,obj):
        if isinstance(obj,dict):
            if 'path' in obj and 'sha256' in obj:
                p=self.verify(obj)
                if p.suffix.lower()=='.json' and str(p) not in self.expanded:
                    self.expanded.add(str(p)); self.tree(self.json(obj,expand=False))
            # Historical audit schemas also use matching foo_path/foo_sha256.
            for key,value in obj.items():
                if key.endswith('_path') and key[:-5]+'_sha256' in obj and isinstance(value,str):
                    self.verify({'path':value,'sha256':obj[key[:-5]+'_sha256']})
                if isinstance(value,(dict,list)): self.tree(value)
        elif isinstance(obj,list):
            for value in obj: self.tree(value)
    def json(self,b,expand=True):
        p=self.verify(b)
        if str(p) not in self.documents: self.documents[str(p)]=read(p)
        result=self.documents[str(p)]
        if expand and str(p) not in self.expanded:
            self.expanded.add(str(p)); self.tree(result)
        return result
    def rows(self,b):
        p=self.verify(b); rows={}
        for line in p.read_text().splitlines():
            if not line.strip(): continue
            x=json.loads(line); rid=x.get('original_id',x.get('id'))
            require(isinstance(rid,str) and rid not in rows,'Missing/duplicate row ID: '+str(rid))
            require(x.get('id')==rid,'Unexpected alias in original-ID output: '+rid)
            rows[rid]=x
        return rows
    def shared_rule_inputs(self,b):
        p=self.verify(b);rows={};source_ids=set()
        for line in p.read_text().splitlines():
            if not line.strip():continue
            x=json.loads(line);rid=x.get('id');original=x.get('original_id')
            require(set(x)=={'id','original_id','input'} and isinstance(x['input'],dict),'Wrong shared-rule-input schema')
            require(isinstance(rid,str) and re.fullmatch(r'RECODE25-\d{5}',rid) and rid not in rows,'Invalid/duplicate rule-input canonical ID')
            require(isinstance(original,str) and original and original not in source_ids,'Invalid/duplicate rule-input source identity')
            require(x['input'].get('review_id')==original,'Source original_id/review_id mismatch')
            rows[rid]=x;source_ids.add(original)
        require(len(rows)==len(source_ids)==4924,'Shared-rule-input dual-ID map must cover4924')
        return rows
    def rule_predictions(self,b,shared_inputs):
        p=self.verify(b);rows={};source_ids=set()
        for line in p.read_text().splitlines():
            if not line.strip():continue
            x=json.loads(line);rid=x.get('id');original=x.get('original_id')
            require(set(x)=={'id','original_id','prediction'} and isinstance(x['prediction'],dict),'Wrong rule-prediction schema')
            require(isinstance(rid,str) and rid in shared_inputs and rid not in rows,'Unknown/duplicate rule-prediction canonical ID')
            require(original==shared_inputs[rid]['original_id'] and original not in source_ids,'Rule-prediction source identity differs from bound shared input')
            rows[rid]=x;source_ids.add(original)
        require(set(rows)==set(shared_inputs) and len(rows)==len(source_ids)==4924,'Rule predictions must match all4924 frozen dual-ID pairs')
        return rows
    def unchanged(self):
        for b in self.bindings.values(): require(digest(b['path'])==b['sha256'],'Bound input changed during assembly: '+b['path'])

def pending_items(cfg):
    missing=[]
    for k in ('root_adopted_methods_confirmed','root_semantic_adoption_confirmed'):
        if cfg.get(k) is not True: missing.append(k)
    if cfg.get('status')!='root_confirmed_complete_method_adoption': missing.append('status=root_confirmed_complete_method_adoption')
    for key in ('root_approved_at','root_adoption_note'):
        if not cfg.get(key): missing.append(key)
    for role in ('rules','LLM'):
        m=cfg.get('methods',{}).get(role,{})
        for key in ('method_id','statistics_method_key','statistics_frozen_method_id','execution_profile'):
            if not m.get(key): missing.append('methods.'+role+'.'+key)
        for key in ('output','execution_binding','classification','statistics_manifest','statistics_QA','statistics_freeze'):
            b=m.get(key)
            if not isinstance(b,dict) or not b.get('path') or not b.get('sha256'): missing.append('methods.'+role+'.'+key)
    for key in ('reference_manifest','candidate_reference','staged_replacements','preflight_report','preflight_freeze','bibliography','AC_statistics','AC_statistics_manifest','AC_statistics_freeze','mathematical_QA','manual_narratives'):
        b=cfg.get(key)
        if not isinstance(b,dict) or not b.get('path') or not b.get('sha256'): missing.append(key)
    return missing

def labels(rows,expected_ids):
    require(set(rows)==set(expected_ids),'Prediction/reference IDs differ from frozen scope')
    for rid,row in rows.items():
        target=row.get('prediction',row)
        require(set(target.get('labels',{}))==set(DIMS),'Exactly five labels required: '+rid)
        require(all(type(target['labels'][d]) is int and target['labels'][d] in (0,1) for d in DIMS),'Nonbinary/pending label: '+rid)
    return {rid:row.get('prediction',row)['labels'] for rid,row in rows.items()}

def context(cfg,io):
    manifest=io.json(cfg['reference_manifest'])
    require(manifest['root_final_bindings_confirmed'] is True,'Reference manifest not confirmed')
    require(manifest['material']['version']==cfg['material_version']=='v14','Material version mismatch')
    require(io.json(manifest['material']['source_qa'])['all_checks_pass'] is True,'Source QA not passed')
    a=io.shared_rule_inputs(manifest['material']['rule_inputs']); b=io.rows(manifest['material']['llm_inputs'])
    require(len(a)==len(b)==4924 and set(a)==set(b),'Full shared input ID mismatch')
    for rid in a:
        require(a[rid]['input']['unit_text']==b[rid]['text'],'Rule/LLM unit text mismatch: '+rid)
        require(a[rid]['input']['llm_v29_shared_context']==b[rid]['contexts'],'Rule/LLM context mismatch: '+rid)
    meta=io.json(manifest['metadata']); items={Path(x['original_file']).stem:x for x in meta['rows']}
    require(len(items)==len(meta['rows']),'Duplicate metadata file stems')
    group={rid:items[row['input']['original_file_stem']]['analysis_group'] for rid,row in a.items()}
    require(Counter(group.values())==Counter(COUNTS),'Actual metadata attribution does not match 4481+443')
    design=io.json(manifest['sampling_design']); sample={x['original_id']:x for x in design['sample']}
    require(len(sample)==len(design['sample'])==240 and design['frame_N_by_group']==FRAMES,'Sampling design mismatch')
    require(Counter((x['component'],x['group']) for x in sample.values())==Counter({('probability_canonical',g):60 for g in GROUPS}|{('enriched_challenge',g):30 for g in ('NMPA','NHSA')}),'Probability/challenge scope mismatch')
    for rid,x in sample.items():
        require(group[rid]==x['group'],'Sample group differs from metadata')
        require(sha_text(b[rid]['text'])==x['unit_text_sha256'],'Sample unit text changed')
        if x['component']=='probability_canonical':
            require(x['sample_n']==60 and x['canonical_frame_N']==FRAMES[x['group']],'Canonical frame differs')
            require(numeric_same(x['analysis_weight'],F(FRAMES[x['group']],60)),'Incorrect sampling weight')
            require(numeric_same(x['inclusion_probability'],F(60,FRAMES[x['group']])),'Incorrect inclusion probability')
        else: require(x['analysis_weight'] is None,'Challenge must not carry population weight')
    refs={}
    for coder in ('A','C'):
        rows=io.rows(manifest['references'][coder]); refs[coder]=labels(rows,sample)
        for rid,row in rows.items():
            require(row['effective_material_version']=='v14','Old reference material')
            p=row['annotation_provenance']['effective']; packet=io.json({'path':p['packet_path'],'sha256':p['packet_sha256']})
            items=[x for x in packet['rows'] if x['id']==p['blind_id']]
            require(len(items)==1,'Reference packet ID ambiguity')
            require(all(items[0][k]==b[rid][k] for k in ('text','source_title','pages','contexts','context_usage')),'Reference/current input mismatch: '+rid)
    refs['candidate']=labels(io.rows(cfg['candidate_reference']),sample)
    return manifest,a,b,group,sample,refs

def execution(m,role,manifest,io,rows):
    entry=io.json(m['execution_binding']); profile=m['execution_profile']
    source=manifest['material']['rule_inputs' if role=='rules' else 'llm_inputs']
    if profile=='rules_development_candidate':
        require(role=='rules','Rules execution profile on non-rule method')
        require(same_binding(entry['prediction'],m['output']) and same_binding(entry['input'],source),'Rule execution/input binding mismatch')
        require(entry['scope_closed'] is True and entry['reference_labels_edited'] is False,'Unclosed or label-edited rules')
        require(entry['not_independent_validation'] is True and entry['exposed240_used_for_development'] is True,'Development exposure must remain explicit')
        qa=io.json(entry['QA']); run=io.json(entry['run'])
        require(qa['all_checks_pass'] is True and run['n']==4924 and run['pending_n']==0,'Rule run incomplete')
        require(run['input_sha256']==source['sha256'] and run['prediction_sha256']==m['output']['sha256'],'Rule run hashes disagree')
        for p,h in run['runtime_code_sha256'].items(): io.verify({'path':p,'sha256':h})
    elif profile==reconciled_v2.PROFILE:
        require(role=='LLM' and m['method_id']==reconciled_v2.METHOD,'Wrong reconciled profile identity')
        require(same_binding(entry['output'],m['output']) and same_binding(entry['source_input'],source),'Reconciled source/output mismatch')
        reconciled_v2.verify_complete(m['execution_binding'],io,rows)
    elif profile=='LLM03_full_execution':
        require(role=='LLM','LLM profile on non-LLM method')
        require(entry['status']=='complete_actual_full_corpus_development_comparison_QA_PASS','LLM03 full execution not closed')
        require(entry['method_id']==m['method_id'] and entry['n']==4924 and entry['batches']==197,'LLM03 identity or full scope mismatch')
        require(same_binding(entry['output'],m['output']) and same_binding(entry['source_input'],source),'LLM03 execution/output/input mismatch')
        qa=io.json(entry['technical_QA']); plan=io.json(entry['run_plan']); summary=io.json(entry['execution_summary'])
        require(qa['status']=='PASS' and qa['n']==4924 and qa['batches']==197,'LLM03 QA incomplete')
        require(qa['output_sha256']==m['output']['sha256'] and qa['full_v14_source_sha256']==source['sha256'],'LLM03 QA hashes disagree')
        for q,k in (('plan_sha256','run_plan'),('summary_sha256','execution_summary'),('row_provenance_sha256','row_provenance')):
            require(qa[q]==entry[k]['sha256'],'LLM03 QA lineage hash mismatch: '+q)
        require(qa['selected_tool_event_count']==qa['all_attempt_tool_event_count']==0,'Tool events in LLM03 execution')
        require(qa['labels_spliced_or_quotes_repaired'] is False and qa['reference_or_metric_based_selection'] is False,'LLM03 posthoc output selection/repair')
        require(plan['input_sha256']==source['sha256'] and plan['prompt_sha256']==entry['prompt']['sha256'],'LLM03 actual plan differs')
        require(plan['model']==entry['requested_model']=='gpt-5.6-sol' and plan['reasoning_effort']==entry['reasoning_effort']=='medium','LLM runtime differs from staged prose')
        require(summary['status']=='complete_actual_calls_structurally_valid' and summary['accepted_batch_count']==197 and summary['source_unchanged_during_run'] is True,'LLM03 summary incomplete')
        require(summary['output_sha256']==m['output']['sha256'],'LLM03 summary output mismatch')
        require(len(qa['batch_audits'])==197 and {x['batch'] for x in qa['batch_audits']}==set(range(1,198)),'LLM03 batch coverage mismatch')
        require(len(qa['attempt_audits'])==qa['actual_attempts']==summary['actual_attempt_count'],'LLM03 actual-attempt count mismatch')
        require(sum(not x['valid'] for x in qa['attempt_audits'])==qa['failed_attempts_preserved']==entry['failed_attempts_preserved'],'LLM03 failed attempts missing')
        for x in qa['attempt_audits']:
            for k,file in (('metadata_sha256','run_metadata.json'),('request_sha256','request.txt'),('events_sha256','events.jsonl')):
                io.verify({'path':str(Path(x['path'])/file),'sha256':x[k]})
            if x['raw_output_sha256'] is not None: io.verify({'path':str(Path(x['path'])/'raw_output.json'),'sha256':x['raw_output_sha256']})
        for x in qa['batch_audits']:
            attempted=sorted((a for a in qa['attempt_audits'] if a['batch']==x['batch']),key=lambda a:a['attempt'])
            accepted=[a for a in attempted if a['valid']]
            require(accepted and accepted[0]['path']==x['selected_actual_attempt']==attempted[-1]['path'],'Not first valid actual attempt')
            require(x['status']=='PASS' and len(attempted)==x['actual_attempts'],'Batch execution failed')
        provenance=io.rows(entry['row_provenance']); require(set(provenance)==set(rows),'LLM03 row lineage incomplete'); sources=io.rows(source)
        for rid,x in provenance.items():
            canon=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            require(x['all_five_labels_from_one_intact_actual_row'] is True and x['output_row_canonical_sha256']==canon(rows[rid]),'LLM03 row not intact')
            require(x['source_row_canonical_sha256']==canon(sources[rid]),'LLM03 row source context differs')
    elif profile=='LLM02_reconciled_execution':
        require(role=='LLM' and m['method_id']=='LLM-v32-candidate02','Wrong identity for frozen LLM02 profile')
        old=manifest['methods']['LLM']
        require(same_binding(m['output'],old['output']) and same_binding(m['execution_binding'],old['execution_qa']),'LLM02 must use confirmed formal manifest binding')
        require(entry['all_checks_pass'] is True and entry['n']==4924 and entry['batch_count']==197,'LLM02 execution not complete')
        require(entry['final_material_version']=='v14' and entry['final_output_sha256']==m['output']['sha256'],'LLM02 execution hashes disagree')
        for k in ('all4924_exact_raw_objects_reconstructed','all_five_dimensions_from_actual_v32_row','row_provenance_bound_and_reconstructed','first_valid_selection_checked_independently','partial_historical_runs_not_misrepresented_as_complete'):
            require(entry[k] is True,'LLM02 execution QA failed: '+k)
        require(entry['all_historical_attempt_tool_events']==entry['selected_branch_all_attempt_tool_events']==0,'LLM02 tool events present')
        io.verify(old['actual_row_provenance'])
    elif profile=='rules33_confirmed_execution':
        require(role=='rules' and m['method_id']=='rules-v33','Wrong identity for frozen v33 profile')
        old=manifest['methods']['rules']; require(same_binding(m['output'],old['output']) and same_binding(m['execution_binding'],old['execution_qa']),'v33 formal binding differs')
        require(entry.get('all_checks_pass') is True or entry.get('status') in ('pass','pass_independent_execution_QA'),'v33 execution QA failed')
        require(entry.get('final_output_sha256',m['output']['sha256'])==m['output']['sha256'],'v33 QA output differs')
        require(entry['n']==4924 and entry['source_input_sha256']==source['sha256'],'v33 full input differs')
    else: raise GateError('Unsupported execution profile; explicit adapter update required: '+str(profile))

def statistics_document(binding,manifest_binding,cfg,io):
    doc=io.json(binding); provenance=doc['provenance']; require(provenance['material_version']=='v14','Statistics material differs')
    actual=provenance.get('bindings') or {'path':provenance.get('binding_manifest_path'),'sha256':provenance.get('binding_manifest_sha256')}
    require(same_binding(actual,manifest_binding),'Statistics provenance does not bind declared manifest')
    manifest=io.json(manifest_binding)
    if manifest.get('stage')=='development_only_all240_exposed':
        require(manifest.get('root_development_bindings_confirmed') is True,'Development statistics not confirmed')
        require(same_binding(manifest['reference_manifest'],cfg['reference_manifest']),'Statistics/reference manifest differs')
        require(same_binding(manifest['existing_candidate_reference'],cfg['candidate_reference']),'Candidate reference differs')
        require(provenance['all240_exposed'] is True and provenance['independent_validation'] is False,'Statistics development scope altered')
    else:
        require(same_binding(manifest_binding,cfg['reference_manifest']) and manifest.get('stage')=='final','Unknown statistical provenance schema')
    require(provenance['analysis_notes']['replications']==5000,'Statistics bootstrap count differs')
    require(provenance['human_validation_completed'] is False,'Unexpected human-reference identity claim')
    return doc,manifest

def statistics_seal(seal_binding,manifest_binding,required_files,io):
    seal=io.json(seal_binding); parent=Path(seal_binding['path']).parent
    require(seal['bindings_sha256']==manifest_binding['sha256'],'Statistics seal belongs to another manifest')
    for binding in required_files:
        require(Path(binding['path']).parent==parent,'Statistics/QA from mixed output directories')
        require(seal['files'][Path(binding['path']).name]==binding['sha256'],'Statistics file not covered by its output seal')
    for name,h in seal['files'].items(): io.verify({'path':str(parent/name),'sha256':h})

def exact_metrics(z):
    a,b,c,d=z; n=sum(z); div=lambda x,y:x/y if y else None
    po=div(a+d,n); p=div(a+b,n); q=div(a+c,n); pe=p*q+(1-p)*(1-q) if n else None
    return {'kappa':div(po-pe,1-pe) if n else None,'precision':div(a,a+b),'recall':div(a,a+c),'f1':div(2*a,2*a+b+c)}

def checked_record(doc,method,reference,dim,left,right,sample,is_ac=False):
    selection={'component':'probability_canonical','group':'ALL','weighting':'eligible_design_weighted','method':method,'reference':reference,'dimension':dim}
    hit=[(i,r) for i,r in enumerate(doc['comparisons']) if all(r.get(k)==v for k,v in selection.items())]
    require(len(hit)==1,'Missing/duplicate exact statistical selector: '+str(selection)); index,row=hit[0]
    ids=sorted(rid for rid,x in sample.items() if x['component']=='probability_canonical')
    require(row['paired_n']==row['unit_frame_n']==180 and row['excluded_pending_n']==0,'Statistic not on complete same180')
    require(sorted(row['paired_ids'])==ids and not row['excluded_ids'],'Statistical IDs differ')
    require(row['primary_bootstrap_mechanism']=='department_unit_rescaled_SRSWOR','Wrong primary CI mechanism')
    raw=[0]*4; weighted=[F(0)]*4
    for rid in ids:
        j={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[left[rid][dim],right[rid][dim]]
        raw[j]+=1; weighted[j]+=F(FRAMES[sample[rid]['group']],60)
    rk='symmetric_raw_cells' if is_ac else 'raw_confusion'; wk='symmetric_weighted_cells' if is_ac else 'weighted_confusion'
    ckeys=('A1_C1','A1_C0','A0_C1','A0_C0') if is_ac else CELLS
    require([row[rk][k] for k in ckeys]==raw,'Raw cells do not match adopted labels')
    require(all(numeric_same(row[wk][k],v) for k,v in zip(ckeys,weighted)),'Design-weighted cells differ')
    exact=exact_metrics(weighted); names=('kappa',) if is_ac else METRICS; audit={}
    for metric in names:
        m=row['metrics'][metric]; require(numeric_same(m['estimate'],exact[metric]),'Metric differs from exact adopted cells: '+metric)
        ci=m['ci95_primary']; require(ci['defined_repetitions']+ci['undefined_repetitions']==5000,'Incomplete primary interval repetitions')
        require(all(type(ci[k]) is int and 0<=ci[k]<=5000 for k in ('defined_repetitions','undefined_repetitions')),'Invalid interval repetition counts')
        require(finite_or_none(ci['low']) and finite_or_none(ci['high']),'Nonfinite interval')
        if ci['defined_repetitions']==0: require(ci['low'] is None and ci['high'] is None,'Undefined CI must be NA')
        else: require(ci['low'] is not None and ci['high'] is not None and ci['low']<=ci['high'],'Malformed primary interval')
        reason=row.get('undefined_point_reasons',{}).get(metric)
        if m['estimate'] is None: require(bool(reason),'NA metric has no explicit reason')
        audit[metric]={'estimate':m['estimate'],'exact_fraction':None if exact[metric] is None else str(exact[metric]),'ci95_primary':ci,'undefined_point_reason':reason,'json_pointer':f'/comparisons/{index}/metrics/{metric}'}
    return {'selector':selection,'row_json_pointer':f'/comparisons/{index}','raw_cells':dict(zip(ckeys,raw)),'exact_weighted_cells':dict(zip(ckeys,map(str,weighted))),'metrics':audit}

def full_statistics_scope(doc,method,refs):
    scopes=[('probability_canonical','ALL','eligible_design_weighted')]+[('probability_canonical',g,'unweighted') for g in ('ALL',)+GROUPS]+[('enriched_challenge',g,'unweighted') for g in ('ALL','NMPA','NHSA')]
    keys=Counter((r['component'],r['group'],r['weighting'],r['method'],r['reference'],r['dimension']) for r in doc['comparisons'])
    for comp,group,weight in scopes:
        for ref in refs:
            for dim in DIMS: require(keys[comp,group,weight,method,ref,dim]==1,'Classification bundle lacks complete scope coverage')

def full_profiles(predictions,groups):
    profiles=[]
    for role in ('rules','LLM'):
        rows=predictions[role]
        for g in GROUPS:
            ids=[rid for rid in rows if groups[rid]==g]
            counts={d:sum(rows[rid][d] for rid in ids) for d in DIMS}; denominator=sum(counts.values())
            require(denominator>0,'No five-dimensional coding denominator: '+role+'/'+g)
            shares={d:F(counts[d],denominator) for d in DIMS}
            require(sum(shares.values())==1,'Exact five shares do not sum to one')
            ec=counts['Ec']; joint=sum(rows[rid]['Ec']*rows[rid]['F'] for rid in ids)
            profiles.append({'group':g,'method_role':role,'unit_n':len(ids),'denominator':denominator,
              'dimensions':{d:{'count':counts[d],**fraction_value(shares[d]),'percentage':float(100*shares[d]),'coverage_exact_fraction':str(F(counts[d],len(ids)))} for d in DIMS},
              'Ec_F':{'Ec':ec,'F':counts['F'],'joint':joint,'Ec_only':ec-joint,'F_only':counts['F']-joint,'neither':len(ids)-ec-counts['F']+joint,'P_F_given_Ec':fraction_value(safe_fraction(joint,ec))}})
    return profiles

def assemble(cfg,io):
    # Header/QA gate precedes recursive closure, source/reference/label reads.
    lm=cfg['methods']['LLM']
    if lm['execution_profile']==reconciled_v2.PROFILE:
        reconciled_v2.closed_header(lm['execution_binding'])
    io.verify({'path':str(Path(reconciled_v2.__file__).resolve()),'sha256':digest(reconciled_v2.__file__)})
    io.tree(cfg)
    staged=io.json(cfg['staged_replacements']); preflight=io.json(cfg['preflight_report']); freeze=io.json(cfg['preflight_freeze']); bibliography=io.json(cfg['bibliography'])
    require(preflight['all_old_text_hash_checks_pass'] is True and preflight['replacements_n']==52,'Preflight paragraph checks incomplete')
    require(preflight['inputs'][cfg['staged_replacements']['path']]['sha256']==cfg['staged_replacements']['sha256'],'Staged text differs from preflight')
    require(Path(cfg['preflight_freeze']['path']).parent==Path(cfg['preflight_report']['path']).parent==Path(cfg['bibliography']['path']).parent,'Mixed preflight snapshots')
    for name,h in freeze['files'].items(): io.verify({'path':str(Path(cfg['preflight_freeze']['path']).parent/name),'sha256':h})
    require(freeze['files'][Path(cfg['bibliography']['path']).name]==cfg['bibliography']['sha256'],'Bibliography not from bound preflight')
    require(len(staged['replacements'])==52 and len(staged['measurement_fields'])==39,'Unexpected staged schema')
    manifest,rule_input,llm_input,groups,sample,refs=context(cfg,io)
    mathqa=io.json(cfg['mathematical_QA'])
    require(mathqa.get('all_checks_pass') is True or mathqa.get('status') in ('PASS','pass','pass_label_free_frame_and_synthetic_mathematical_QA'),'Mathematical QA not passed')
    require(mathqa['NHC_factors_strictly_one'] is True and mathqa['SRSWOR_n_minus_one_formula_checked'] is True and mathqa['zero_denominator_NA_checks_pass'] is True,'Required mathematical QA checks missing')
    predictions={}; table2audit=[]; machine_docs={}
    for role in ('rules','LLM'):
        m=cfg['methods'][role]; rows=io.rule_predictions(m['output'],rule_input) if role=='rules' else io.rows(m['output']); require(len(rows)==4924,'Full4924 method output required')
        predictions[role]=labels(rows,rule_input); execution(m,role,manifest,io,rows)
        if role=='rules':
            require(all(row['prediction']['unit_text_sha256']==sha_text(llm_input[rid]['text']) for rid,row in rows.items()),'Rule output unit text hashes differ')
        doc,sm=statistics_document(m['classification'],m['statistics_manifest'],cfg,io)
        statistics_seal(m['statistics_freeze'],m['statistics_manifest'],[m['classification'],m['statistics_QA']],io)
        require(m['statistics_method_key'] in sm['methods'],'Unknown statistics method key')
        declared=sm['methods'][m['statistics_method_key']]
        require(declared['frozen_method_id']==m['statistics_frozen_method_id'] and same_binding(declared['output'],m['output']),'Statistics use another method or output')
        require(declared['material_version']==cfg['material_version'],'Statistics method material differs')
        qa=io.json(m['statistics_QA']); require(qa.get('all_checks_pass') is True or qa.get('status') in ('PASS','pass'),'Complete-statistics QA not passed')
        full_statistics_scope(doc,m['statistics_method_key'],('A','C','candidate')); machine_docs[role]=doc
    ac,acmanifest=statistics_document(cfg['AC_statistics'],cfg['AC_statistics_manifest'],cfg,io)
    statistics_seal(cfg['AC_statistics_freeze'],cfg['AC_statistics_manifest'],[cfg['AC_statistics']],io)
    full_statistics_scope(ac,'A_C',('symmetric A/C',))
    acaudit={d:checked_record(ac,'A_C','symmetric A/C',d,refs['A'],refs['C'],sample,True) for d in DIMS}
    profiles=full_profiles(predictions,groups); by={(x['method_role'],x['group']):x for x in profiles}
    fields={'FINAL_RULES_ID':cfg['methods']['rules']['method_id'],'FINAL_LLM_ID':cfg['methods']['LLM']['method_id'],
            'AC_KAPPA_S_E_Ec_I_F':'、'.join(number_text(acaudit[d]['metrics']['kappa']['estimate']) for d in DIMS)}
    for g in GROUPS:
        for d in DIMS: fields[f'RULE_Q_{g}_{d}']=number_text(100*F(by['rules',g]['dimensions'][d]['exact_fraction']),2)
    for role,prefix in (('rules','RULE'),('LLM','LLM')):
        for g in ('NHSA','NHC'):
            z=by[role,g]['Ec_F']; require(z['P_F_given_Ec']['value'] is not None,'Cannot fill hardcoded conditional-proportion prose with zero Ec denominator')
            fields[f'{prefix}_Ec_{g}']=str(z['Ec']);fields[f'{prefix}_JOINT_{g}']=str(z['joint'])
            fields[f'{prefix}_P_F_GIVEN_Ec_{g}']=number_text(100*F(z['P_F_given_Ec']['exact_fraction']),2)
    directions=[]
    for one,two in combinations(GROUPS,2):
        for dim in DIMS:
            ds={role:F(by[role,one]['dimensions'][dim]['exact_fraction'])-F(by[role,two]['dimensions'][dim]['exact_fraction']) for role in ('rules','LLM')}
            directions.append({'department_one':one,'department_two':two,'dimension':dim,'difference':'one_minus_two','exact_q_differences':{r:str(v) for r,v in ds.items()},'signs':{r:sign(v) for r,v in ds.items()},'same_direction':sign(ds['rules'])==sign(ds['LLM'])})
    fields['DEPARTMENT_DIRECTION_MATCH_N']=str(sum(x['same_direction'] for x in directions))
    # Existing staged prose contains these concrete directions outside placeholders.
    for role in ('rules','LLM'):
        require(F(by[role,'NHSA']['dimensions']['Ec']['exact_fraction'])>F(by[role,'NHC']['dimensions']['Ec']['exact_fraction']),'Staged claim NHSA qEc>NHC is false; root must revise prose/preflight')
        require(F(by[role,'NHC']['Ec_F']['P_F_given_Ec']['exact_fraction'])>F(by[role,'NHSA']['Ec_F']['P_F_given_Ec']['exact_fraction']),'Staged claim NHC P(F|Ec)>NHSA is false; root must revise prose/preflight')
    t2=[['维度','方法','κ（A/C）','P（A/C）','R（A/C）','F1（A/C）']]
    for d in DIMS:
        for role in ('rules','LLM'):
            m=cfg['methods'][role]; entry={ref:checked_record(machine_docs[role],m['statistics_method_key'],ref,d,predictions[role],refs[ref],sample) for ref in ('A','C')}
            table2audit.append({'dimension':d,'method_role':role,'method_id':m['method_id'],'classification_binding':m['classification'],'references':entry})
            t2.append([DIM_NAMES[d],'规则' if role=='rules' else 'LLM']+['/'.join(number_text(entry[ref]['metrics'][metric]['estimate']) for ref in ('A','C')) for metric in METRICS])
    t3=[['部门','方法']+[DIM_NAMES[d]+'（%）' for d in DIMS]]
    for g in GROUPS:
        for role in ('rules','LLM'): t3.append([GROUP_NAMES[g],'规则' if role=='rules' else 'LLM']+[number_text(100*F(by[role,g]['dimensions'][d]['exact_fraction']),2) for d in DIMS])
    manual=io.json(cfg['manual_narratives']); require(manual['root_explicitly_supplied'] is True,'Narratives not explicitly supplied by root')
    require(set(manual['fields'])==set(MANUAL),'Exactly eight root narrative fields required')
    # Bind the immutable measurement inputs, not the adoption file itself: the
    # latter also hashes this narrative file, so mutual file hashes would cycle.
    require(manual['reference_manifest_sha256']==cfg['reference_manifest']['sha256'] and manual['staged_replacements_sha256']==cfg['staged_replacements']['sha256'],'Narratives refer to other references or staged prose')
    require(manual['method_output_sha256']=={role:cfg['methods'][role]['output']['sha256'] for role in ('rules','LLM')},'Narrative bundle refers to other adopted outputs')
    for k in MANUAL:
        entry=manual['fields'][k]; require(isinstance(entry.get('text'),str) and entry['text'].strip() and not FIELD.search(entry['text']),'Missing narrative: '+k)
        require(entry.get('root_approved') is True and entry.get('source_bindings'),'Narrative lacks explicit approval/source: '+k)
        require(isinstance(entry['source_bindings'],list) and all(isinstance(b,dict) and 'path' in b and 'sha256' in b for b in entry['source_bindings']),'Narrative sources must be path/SHA bindings: '+k)
        require(entry['method_output_sha256']=={role:cfg['methods'][role]['output']['sha256'] for role in ('rules','LLM')},'Narrative uses other method outputs: '+k)
        io.tree(entry); fields[k]=entry['text']
    require(set(fields)==set(staged['measurement_fields']) and len(fields)==39,'Resolved field set differs from 39-field contract')
    replacements=[]
    for item in staged['replacements']:
        s=FIELD.sub(lambda m:fields[m[1]],item['replacement_text']); require(not FIELD.search(s),'Unresolved field after replacement')
        citation_coverage(s,bibliography)
        replacements.append({'zero_based_body_p_index':item['zero_based_body_p_index'],'old_text_sha256':item['old_text_sha256'],'replacement_text':s})
    io.unchanged()
    return {'status':'assembled_pending_independent_QA','adapter_is_not_DOCX_authoring':True,'root_adoption_binding':cfg['_adoption_self_binding'],
      'input_bindings':sorted(io.bindings.values(),key=lambda x:x['path']),'resolved_replacements':replacements,
      'tables':{'2':{'rows':t2,'rows_include_header':True,'metric_unit':'original decimal units; no percentage scaling','n_data_rows':10,'point_n':80,'same_source_primary_CI_n':80,'audit':table2audit},
                '3':{'rows':t3,'rows_include_header':True,'n_data_rows':6,'q_n':30,'definition':'dimension positives / sum of five dimension positives','audit':profiles}},
      'figure2_data':profiles,'resolved_fields39':fields,'manual_narrative_bindings':manual,'remaining_fields':[],
      'bibliography_binding':cfg['bibliography'],'AC_before_third_audit':{'binding':cfg['AC_statistics'],'dimensions':acaudit},
      'method_id_mapping':{role:{'adopted_id':cfg['methods'][role]['method_id'],'statistics_key':cfg['methods'][role]['statistics_method_key'],'statistics_frozen_id':cfg['methods'][role]['statistics_frozen_method_id'],'actual_output':cfg['methods'][role]['output']} for role in ('rules','LLM')},
      'department_pair_directions':directions,'direction_tie_policy':'Signs of exact q differences; both exact zero count as agreement, one zero and one nonzero do not. Denominator is all15 comparisons.',
      'source_scope':{'full_output_n_each':4924,'three_department_n':4481,'excluded_GOV_n':443,'groups':COUNTS,'same_probability_n':180,'probability_frames':FRAMES,'challenge_n':60,'AI_references':True,'human_validation_completed':False,'development_exposure_not_removed_by_adoption':True},
      'limits':'Only an independent numerical QA matching this exact content can promote status to ready_for_authoring. Final DOCX render/reference/figure QA is a subsequent authoring step. This adapter does not certify semantic truth or independent validation.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--adoption','--config',dest='adoption',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--check-only',action='store_true');ap.add_argument('--independent-qa',type=Path);ap.add_argument('--independent-qa-sha256');args=ap.parse_args()
    require(not args.out.exists(),'Refuse to overwrite an existing output directory')
    cfg=read(args.adoption); missing=pending_items(cfg)
    report={'status':'blocked_pending_adoption','check_only':args.check_only,'adoption':{'path':str(args.adoption.resolve()),'sha256':digest(args.adoption)},'remaining_fields':sorted(AUTO+MANUAL),'manual_narrative_fields':list(MANUAL),'blocking_items':missing,'prediction_or_statistical_files_opened':False,'DOCX_generated_or_modified':False,'actual_completed_method_validation_run':False}
    if missing:
        args.out.mkdir(parents=True);save(args.out/'gate_report.json',report);print(json.dumps(report,ensure_ascii=False));return 2
    io=BoundIO();self_binding={'path':str(args.adoption.resolve()),'sha256':digest(args.adoption)};io.verify(self_binding)
    io.verify({'path':str(Path(__file__).resolve()),'sha256':digest(__file__)})
    cfg['_adoption_self_binding']=self_binding
    try:
        payload=assemble(cfg,io)
        core={k:v for k,v in payload.items() if k not in ('status','input_bindings','limits')}
        content_sha=hashlib.sha256(json.dumps(core,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        payload['payload_content_sha256']=content_sha
        payload['remaining_gates']=['independent_payload_QA']
        if args.independent_qa is not None or args.independent_qa_sha256 is not None:
            require(args.independent_qa is not None and args.independent_qa_sha256 is not None,'Both independent QA path and SHA required')
            qb={'path':str(args.independent_qa.resolve()),'sha256':args.independent_qa_sha256};qa=io.json(qb)
            io.verify(qa['script'])
            require(qa['status']=='PASS' and qa['all_checks_pass'] is True and qa['independent_of_adapter_execution'] is True,'Independent payload QA not passed')
            require(qa['adoption_sha256']==self_binding['sha256'] and qa['adapter_sha256']==digest(__file__) and qa['payload_content_sha256']==content_sha,'Independent QA belongs to another payload/adoption/code')
            require(qa['checked_counts']=={'fields':39,'replacements':52,'table2_points':80,'table2_primary_CIs':80,'table3_q':30,'department_directions':15},'Independent QA coverage incomplete')
            payload.update(status='ready_for_authoring',independent_payload_QA_binding=qb,remaining_gates=[],input_bindings=sorted(io.bindings.values(),key=lambda x:x['path']))
            io.unchanged()
    except (GateError,KeyError,TypeError,ValueError,OSError) as exc:
        report.update(status='blocked_integrity_or_unresolved_content',blocking_items=[str(exc)],prediction_or_statistical_files_opened=any(Path(p).suffix=='.jsonl' for p in io.bindings),verified_input_bindings=list(io.bindings.values()))
        args.out.mkdir(parents=True);save(args.out/'gate_report.json',report);print(json.dumps(report,ensure_ascii=False));return 2
    args.out.mkdir(parents=True)
    ready=payload['status']=='ready_for_authoring'
    report.update(status=payload['status'],blocking_items=payload['remaining_gates'],remaining_fields=[],prediction_or_statistical_files_opened=True,actual_completed_method_validation_run=True,verified_input_binding_n=len(io.bindings),payload_content_sha256=payload['payload_content_sha256'])
    save(args.out/'gate_report.json',report)
    if not args.check_only:
        save(args.out/'manuscript_measurement_payload.json',payload)
        save(args.out/'output_freeze.json',{'adoption':self_binding,'script':{'path':str(Path(__file__).resolve()),'sha256':digest(__file__)},'files':{p.name:digest(p) for p in args.out.iterdir() if p.is_file()},'created_at':datetime.datetime.now().astimezone().isoformat()})
    print(json.dumps(report,ensure_ascii=False));return 0 if ready else 2

if __name__=='__main__':
    try: sys.exit(main())
    except GateError as exc: print(str(exc),file=sys.stderr);sys.exit(2)
