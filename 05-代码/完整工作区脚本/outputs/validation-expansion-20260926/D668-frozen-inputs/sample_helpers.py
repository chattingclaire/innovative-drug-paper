"""Plan or draw H600. Actual drawing requires an explicit, hashed freeze manifest."""
import argparse, collections, hashlib, json, math, random, re
from pathlib import Path
from datetime import datetime, date
OUT=Path(__file__).parent
BASE=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
SEED=2026092602
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CONTEXT_KEYS={'paragraph_id','text','pages','caption','headers','row_cells','usage','kind','contexts','selection_basis','source','source_sha256','verification','position','separately_existing_unit_ids','unit_boundary_note','definition','title','note','original_unit_sha256','source_unit_id'}
DEFAULT_CONTEXT_FIELDS=['paragraph_context','nearest_preceding_heading','immediately_preceding_paragraph','verified_parent_context','verified_table_context','verified_rule_branch_context','verified_cross_reference_context','verified_list_context','supplemental_verified_context','verified_supplemental_context','content_role','content_role_basis']
def clean_context(x):
    if isinstance(x,dict):
        return {k:clean_context(v) for k,v in x.items() if k in CONTEXT_KEYS}
    if isinstance(x,list):return [clean_context(v) for v in x]
    if x is None or isinstance(x,(str,int,float,bool)):return x
    raise ValueError('Unsupported context type')
def clean_assessment(x):
    if not isinstance(x,dict):raise ValueError('Assessment must be an object')
    status=x.get('status','not_assessed')
    if status not in {'not_assessed','sufficient','context_insufficient','text_problem'}:raise ValueError('Unknown assessment status')
    out={'status':status}
    for k in ('basis','reason','source','verification','assessed_at'):
        if k in x:
            if not isinstance(x[k],str):raise ValueError('Assessment free-text field must be string: '+k)
            out[k]=x[k]
    return out
def unique_map(rows,key,label):
    out={}
    for r in rows:
        k=r[key]
        if not isinstance(k,str) or not k or k in out:raise ValueError('Missing/duplicate '+label)
        out[k]=r
    return out
def year_value(x):
    if isinstance(x,bool) or not re.fullmatch(r'[12][0-9]{3}',str(x)):raise ValueError('Invalid stratification year')
    return str(x)
def choose_year(r,d,cm):
    if r.get('component_year') is not None:return year_value(r['component_year']),'component_year_from_frozen_metadata'
    if d.get('publication_date'):
        raw=d['publication_date']
        if not isinstance(raw,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw):raise ValueError('Non-ISO publication_date')
        return str(date.fromisoformat(raw).year),'publication_date_from_frozen_metadata'
    if cm.get('year_in_filename') is not None:return year_value(cm['year_in_filename']),'document_designated_year_not_verified_publication_date'
    return 'unknown','unknown'
def allocate(counts,n):
    n=min(n,sum(counts.values()));total=sum(counts.values())
    low={h:min(2,N) for h,N in counts.items()}
    if sum(low.values())>n:raise ValueError('Merge sparse strata under predeclared rule before drawing')
    ideal={h:n*N/total for h,N in counts.items()}
    nh={h:min(N,max(low[h],int(math.floor(ideal[h])))) for h,N in counts.items()}
    while sum(nh.values())<n:
        h=max((h for h in counts if nh[h]<counts[h]),key=lambda h:(ideal[h]-nh[h],h));nh[h]+=1
    while sum(nh.values())>n:
        h=max((h for h in counts if nh[h]>low[h]),key=lambda h:(nh[h]-ideal[h],h));nh[h]-=1
    assert sum(nh.values())==n
    assert all(low[h]<=nh[h]<=counts[h] for h in counts)
    return nh

def frame(corpus,adapter,classification,exposure):
    allunits=unique_map(corpus,'review_id','review_id')
    units={k:r for k,r in allunits.items() if r['count_as_analysis_unit'] is True}
    docs=unique_map(adapter['documents'],'id','source entry')
    cl=unique_map([{**d,'stem':Path(d['original_file']).stem} for d in classification['rows']],'stem','classification source')
    eligible=set(exposure['provisional_eligible_ids'])
    if len(eligible)!=len(exposure['provisional_eligible_ids']):raise ValueError('Duplicate eligible ID')
    if not eligible:raise ValueError('Empty holdout frame')
    if not eligible<=set(units):raise ValueError('Exposure frame has obsolete IDs')
    for k,d in docs.items():
        if k not in cl or d['group']!=cl[k]['analysis_group']:raise ValueError('Department mapping mismatch: '+k)
    pools=collections.defaultdict(list);meta={}
    for k in sorted(eligible):
        r=units[k];d=docs[r['original_file_stem']];cm=cl[r['original_file_stem']]
        year,basis=choose_year(r,d,cm)
        if d['group'] not in {'NMPA','NHSA','NHC','GOV'}:raise ValueError('Unresolved source group')
        series=r.get('component_series') or d['series']
        h=f'{d["group"]}|{year}';pools[h].append(k)
        meta[k]={'group':d['group'],'stratification_year':year,'year_basis':basis,'stratum':h,'source_entry':r['original_file_stem'],'series':series}
    return units,pools,meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--draw',action='store_true');p.add_argument('--self-test',action='store_true');p.add_argument('--preview-exposure');p.add_argument('--preview-corpus',type=Path,default=BASE/'统一文本复核包.jsonl');p.add_argument('--preview-adapter',type=Path,default=BASE/'统计输入接入准备.json');args=p.parse_args()
    if args.self_test:
        cases=[({'a':100,'b':200,'c':1},60),({'a':2,'b':2,'c':96},20),({'a':1,'b':1},600)]
        for counts,n in cases:
            out=allocate(counts,n);assert sum(out.values())==min(n,sum(counts.values()))
        try:allocate({'a':20,'b':20,'c':20},4)
        except ValueError:pass
        else:raise AssertionError('Impossible lower bounds accepted')
        assert clean_context({'text':'合成语境','labels':{'S':1},'contexts':[{'text':'合成内容','answer':1}]})=={'text':'合成语境','contexts':[{'text':'合成内容'}]}
        assert clean_assessment({'status':'not_assessed','labels':{'S':1}})=={'status':'not_assessed'}
        for fn in (lambda:choose_year({'component_year':'unknown'},{},{}),lambda:choose_year({}, {'publication_date':'2025-02-30'},{}),lambda:unique_map([{'id':'x'},{'id':'x'}],'id','test')):
            try:fn()
            except ValueError:pass
            else:raise AssertionError('Invalid frame accepted')
        print('allocation, nested answer filtering, date/year and unique-key checks passed');return
    freeze=None
    if args.draw:
        freeze_path=OUT/'最终冻结清单.json';freeze_sha=sha(freeze_path);freeze=load(freeze_path)
        if freeze['status']!='frozen_for_reference_label_holdout':raise ValueError('Not frozen')
        required={'corpus','adapter','classification','exposure','protocol','dictionary','dictionary_predictions','sampler','survey_metrics','llm_prompt'}
        if not required<=freeze['files'].keys():raise ValueError('Missing freeze input')
        for name,f in freeze['files'].items():
            if sha(Path(f['path']))!=f['sha256']:raise ValueError('Changed frozen file '+name)
        paths={name:Path(f['path']) for name,f in freeze['files'].items()}
        if sha(Path(__file__))!=freeze['files']['sampler']['sha256']:raise ValueError('Running sampler differs from frozen sampler')
    else:
        if not args.preview_exposure:raise ValueError('Preview requires explicit --preview-exposure; no stale default')
        paths={'corpus':args.preview_corpus,'adapter':args.preview_adapter,'classification':BASE/'部门归属与年度系列-冻结v1.json','exposure':OUT/args.preview_exposure}
    corpus=[json.loads(l) for l in paths['corpus'].read_text().splitlines()]
    units,pools,meta=frame(corpus,load(paths['adapter']),load(paths['classification']),load(paths['exposure']))
    counts={h:len(v) for h,v in sorted(pools.items())};alloc=allocate(counts,600)
    plan={'status':'drawn' if args.draw else 'planning_only_no_sample_drawn','N_star':sum(counts.values()),'n':sum(alloc.values()),'seed':SEED,
      'strata':{h:{'N_h':N,'n_h':alloc[h],'pi':alloc[h]/N,'weight':N/alloc[h]} for h,N in counts.items()},
      'scope':'仅代表U*；不是未见原文证书，不外推原4924或未来政策；资料标示年不等同已核发布日期。',
      'input_hashes':{name:sha(p) for name,p in paths.items()}}
    if not args.draw:
        (OUT/'H600-分配预览-未抽样.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print(json.dumps(plan,ensure_ascii=False));return
    dest=OUT/'H600'
    partial=OUT/'.H600.partial'
    if dest.exists() or partial.exists():raise ValueError('H600 or partial attempt already exists; never silently redraw')
    rng=random.Random(SEED);selected=[]
    for h in sorted(pools):selected+=rng.sample(sorted(pools[h]),alloc[h])
    rng.shuffle(selected)
    mapping=[];blind=[]
    fields=freeze['context_fields']
    if not isinstance(fields,list) or not fields or any(not isinstance(f,str) for f in fields):raise ValueError('Explicit frozen context field list required')
    if len(fields)!=len(set(fields)) or not set(fields)<=set(DEFAULT_CONTEXT_FIELDS):raise ValueError('Unreviewed context root field')
    for i,k in enumerate(selected,1):
        r=units[k];bid=f'H600-{i:04d}';h=meta[k]['stratum']
        mapping.append({'id':bid,'review_id':k,**meta[k],**plan['strata'][h],'unit_text_sha256':hashlib.sha256(r['unit_text'].encode()).hexdigest()})
        blind.append({'id':bid,'text':r['unit_text'],'source_title':r['original_file_stem'],'pages':r['pages'],
           'contexts':{f:clean_context(r[f]) for f in fields if r.get(f)},'input_assessment':clean_assessment(r.get('input_assessment',{'status':'not_assessed'})),
           'context_usage':'只编码text；使用核验语境消解对象、条件、指代，不复制上级全标签。nearest_preceding_heading和immediately_preceding_paragraph仅表示位置相邻，未经核验不可自动当有效父级。材料不足保留待定。'})
    partial.mkdir();plan['created_at']=datetime.now().astimezone().isoformat();plan['freeze_manifest_sha256']=freeze_sha
    (partial/'抽样清单-研究者.json').write_text(json.dumps({'plan':plan,'rows':mapping,'not_selected_ids':sorted(set(units)&set(meta)-set(selected))},ensure_ascii=False,indent=2))
    for coder in ('A','C'):
        d=partial/f'agent-{coder}';d.mkdir()
        (d/'五维共用编码协议.md').write_bytes(paths['protocol'].read_bytes())
        for batch in range(math.ceil(len(blind)/25)):
            b={'protocol_version':freeze['protocol_version'],'purpose':'reference_label_holdout_AI_independent','batch':batch+1,'total_batches':math.ceil(len(blind)/25),'rows':blind[batch*25:(batch+1)*25]}
            (d/f'材料-{batch+1:02d}.json').write_text(json.dumps(b,ensure_ascii=False,indent=2))
    for name,f in freeze['files'].items():
        if sha(Path(f['path']))!=f['sha256']:raise RuntimeError('Freeze source changed while drawing; quarantine output '+name)
    if sha(freeze_path)!=freeze_sha:raise RuntimeError('Freeze manifest changed; quarantine partial output')
    assert len({r['id'] for r in mapping})==len(mapping)==plan['n']
    assert not set(selected)&set(load(paths['exposure'])['exclusions'])
    for a in (partial/'agent-A').glob('*'):
        assert sha(a)==sha(partial/'agent-C'/a.name)
    plan['release_status']='ready_for_blind_review'
    plan['output_files']={str(p.relative_to(partial)):sha(p) for p in sorted(partial.rglob('*')) if p.is_file()}
    (partial/'封存信息.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
    partial.rename(dest)
    print(json.dumps({'drawn':len(blind),'N_star':plan['N_star'],'strata':len(pools),'output':str(dest)},ensure_ascii=False))
if __name__=='__main__':main()
