"""Read-only candidate QA; output is evidence, never a self-declared freeze."""
import argparse, hashlib, json, collections
from pathlib import Path
from datetime import datetime
from sample_holdout import unique_map, choose_year, clean_context, DEFAULT_CONTEXT_FIELDS

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())

def inspect(paths):
    before = {k:sha(p) for k,p in paths.items()}
    corpus = [json.loads(s) for s in paths['corpus'].read_text().splitlines()]
    records = unique_map(corpus,'review_id','corpus ID')
    assert all(type(r['count_as_analysis_unit']) is bool for r in corpus)
    units = {k:r for k,r in records.items() if r['count_as_analysis_unit']}
    ad = load(paths['adapter']); prediction = load(paths['dictionary_predictions'])
    pred = unique_map(prediction['rows'],'id','prediction ID')
    docs = unique_map(ad['documents'],'id','adapter document')
    cl = unique_map([{**r,'stem':Path(r['original_file']).stem} for r in load(paths['classification'])['rows']],'stem','classification document')
    assert set(pred) == set(units)
    assert prediction['binding_sha256'] == ad['binding_sha256']
    assert prediction['coder_sha256'] == before['dictionary']
    assert prediction['codebook_sha256'] == before['protocol']
    years = collections.Counter(); sourcehashes = {}; supplemented = 0; context_count = 0
    actual_nested = set(); forbidden = {'labels','gold','prediction','prior_coder_answer','expected_labels','machine_labels','coder_A','coder_C'}
    def keys(x):
        if isinstance(x,dict):
            for k,v in x.items():actual_nested.add(k);assert k not in forbidden;keys(v)
        elif isinstance(x,list):
            for v in x:keys(v)
    for k,r in units.items():
        assert isinstance(r['unit_text'],str) and r['unit_text'].strip()
        text_sha = hashlib.sha256(r['unit_text'].encode()).hexdigest()
        assert pred[k]['unit_text_sha256'] == text_sha
        d=docs[r['original_file_stem']];cm=cl[r['original_file_stem']]
        assert d['group'] == cm['analysis_group']
        yr,basis=choose_year(r,d,cm);years[basis]+=1
        for f in DEFAULT_CONTEXT_FIELDS:
            if r.get(f):
                keys(r[f]);clean_context(r[f])
        supp=r.get('verified_supplemental_context',[])
        if supp:supplemented+=1
        for item in supp:
            assert item['review_id']==k and item['original_unit_text']==r['unit_text']
            assert item['original_unit_sha256']==text_sha
            for c in item['contexts']:
                context_count+=1
                source=Path(c['source'])
                if str(source) not in sourcehashes:sourcehashes[str(source)]=sha(source)
                assert c['source_sha256']==sourcehashes[str(source)]
                assert isinstance(c['text'],str) and c['text'].strip() and c['pages'] and c['verification']
    assert before == {k:sha(p) for k,p in paths.items()}
    return {'status':'candidate_input_QA_passed_not_frozen','created_at':datetime.now().astimezone().isoformat(),
            'files':{k:{'path':str(p),'sha256':before[k]} for k,p in paths.items()},
            'records':len(records),'analysis_units':len(units),'prediction_rows':len(pred),
            'binding_sha256':ad['binding_sha256'],'source_entries':len(docs),
            'prediction_input_assessment_counts':dict(collections.Counter(r.get('input_assessment_status') for r in pred.values())),
            'supplemented_units':supplemented,'supplemental_context_items':context_count,
            'supplemental_physical_sources_verified':sourcehashes,'context_nested_keys':sorted(actual_nested),
            'year_basis_counts':dict(years),
            'limits':['哈希/结构核查不等于重新阅读全部源PDF，也不等于全部单元质量已审定。','语料暴露排除、正式冻结和抽样须另行完成。']}

def main():
    p=argparse.ArgumentParser()
    for k in ('corpus','adapter','classification','dictionary','dictionary_predictions','protocol'):p.add_argument('--'+k.replace('_','-'),type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise RuntimeError('Preserve previous QA')
    report=inspect({k:v for k,v in vars(args).items() if k!='output'})
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:report[k] for k in ('status','records','analysis_units','supplemented_units','binding_sha256')},ensure_ascii=False))
if __name__=='__main__':main()
