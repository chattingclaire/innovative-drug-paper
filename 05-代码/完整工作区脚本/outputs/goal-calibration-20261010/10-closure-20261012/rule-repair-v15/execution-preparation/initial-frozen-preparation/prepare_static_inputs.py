"""Mechanical full-frame preparation only. No coder import or classification."""
from pathlib import Path
from merge_common import bind, cj, exact, load, save, sha

H=Path(__file__).resolve().parent
ROOT=H.parents[2]
V17=ROOT/'01-review/source-interface-v17-finite-source-addendum-root'
BASE=ROOT/'01-review/context-projection-sol/full-frame-preflight'
PARENT=ROOT/'06-coding/rule-full4481-v13b-sf-v16-delta-merged-root'

def prepare():
    plan=load(H.parent/'full-run-plan.json')
    for b in plan['reuse_bindings']+plan['v17_bindings']:exact(b)
    packets=load(V17/'packet-bindings-v17.json')
    lines=(V17/'common-frame-bundles-v17.jsonl').read_bytes().splitlines(keepends=True)
    assert len(packets)==len(lines)==4481
    ids=[];materials={};leaf_N=0
    def add(path, expected_sha=None, expected_bytes=None):
        path=str(Path(path).resolve())
        if path not in materials:materials[path]=bind(path)
        b=materials[path]
        assert expected_sha is None or b['sha256']==expected_sha,path
        assert expected_bytes is None or b['bytes']==expected_bytes,path
        return b
    def literal_locators(value):
        if isinstance(value,dict):
            if value.get('absolute_path') and value.get('sha256'):
                add(value['absolute_path'],value['sha256'],value.get('bytes'))
            for v in value.values():literal_locators(v)
        elif isinstance(value,list):
            for v in value:literal_locators(v)
    for ordinal,(p,line) in enumerate(zip(packets,lines),1):
        exact(p);packet=load(p['path']);bundle=__import__('json').loads(line)
        assert set(packet)=={'output_id','packet_version','source_bundle','source_bundle_sha256','source_id','verified_asset_files'}
        assert packet['packet_version']=='native-full-source-3'
        assert packet['source_bundle']==bundle and cj(packet['source_bundle'])==cj(bundle)
        assert packet['source_id']==p['source_id']==bundle['source_record']['id']
        assert p['frame_ordinal_1based']==ordinal and packet['output_id']==p['output_id']
        assert sha(cj(bundle).encode())==p['source_bundle_sha256']==packet['source_bundle_sha256']
        assert len(cj(bundle).encode())==p['source_bundle_utf8_bytes']
        ids.append(p['source_id']);add(p['path'],p['sha256'],p['bytes'])
        for b in packet['verified_asset_files']:add(b.get('path',b.get('absolute_path')),b['sha256'],b.get('bytes'))
        for d in bundle['source_documents']:
            add(d['snapshot'],d['source_sha256'],d.get('bytes'))
            resource=d.get('source_text_resource')
            if resource:add(BASE/resource['relative_path'],resource['sha256'],resource.get('bytes'))
        for a in bundle['source_asset_locations']:add(a['absolute_path'],a['sha256'],a.get('bytes'))
        literal_locators(bundle['explicit_or_primary_source_resources'])
        for leaf in bundle['source_full_text_resources']:
            if leaf.get('kind')=='verbatim_UTF8_snapshot_text':
                add(leaf['locator']['snapshot_absolute_path'],leaf['source_sha256']);leaf_N+=1
    assert len(set(ids))==4481
    save(H/'packet-bindings.json',{'packet_N':4481,'ordered_source_ids':ids,'packets':packets,
         'current_complete_packet_manifest':bind(V17/'packet-bindings-v17.json'),
         'all_original_packets_and_common_lines_exact':True,'inherited_record_N':0})
    save(H/'full-frame.json',{'ordered_source_ids':ids,'record_N':4481,'dimension_N':22405,
         'common_source':bind(V17/'common-frame-bundles-v17.jsonl'),'packet_manifest':bind(V17/'packet-bindings-v17.json')})
    save(H/'source-material-bindings.json',{'materials':list(materials.values()),
         'derivation':'Union of all4481 original packet files, bound document snapshots/fulltext payloads, source assets and exact literal snapshot/structured-HTML locator files.',
         'literal_leaf_occurrence_N':leaf_N,'READ_or_USE_claimed':False,'classifier_calls':0})
    parent_seal=load(PARENT/'seal.json')
    for b in parent_seal['files']:exact(b)
    origins=[__import__('json').loads(l) for l in (PARENT/'execution-origin-lineage.jsonl').open()]
    assert len(origins)==4481 and [x['id'] for x in origins]==ids
    logs=[]
    for path in sorted({x['source_consumption_log'] for x in origins}):
        sealpath=Path(path).parent/'seal.json';s=load(sealpath)
        b=next(x for k in ['files','output_files'] for x in s.get(k,[]) if x['path']==path);exact(b)
        logs.append({'log':b,'actual_run_seal':bind(sealpath)})
    save(H/'comparison-baseline-bindings.json',{'parent_seal':bind(PARENT/'seal.json'),
         'parent_files':parent_seal['files'],'actual_origin_source_logs':logs,
         'status':'completed_v13b_comparison_baseline_not_a_claim_of_production_adoption'})
    old_scope=load(ROOT/'10-closure-20261012/rule-repair-v13/execution-preparation/scope.UNRELEASED.json')
    contract={'schema':'full4481-rule-v17-preparation-v1','status':'UNRELEASED_PREPARATION',
        'plan':bind(H.parent/'full-run-plan.json'),'source_bindings':plan['v17_bindings'],
        'source_input':bind(V17/'common-frame-bundles-v17.jsonl'),
        'source_package_seal':bind(V17/'output-seal.json'),
        'source_manifest':bind(V17/'frame-bundle-bindings-v17.jsonl'),
        'source_extension_manifest':bind(V17/'source-extension-manifest-v17.json'),
        'packet_bindings':bind(H/'packet-bindings.json'),'full_frame':bind(H/'full-frame.json'),
        'source_material_bindings':bind(H/'source-material-bindings.json'),
        'comparison_baseline_bindings':bind(H/'comparison-baseline-bindings.json'),
        'comparison_baseline_directory':str(PARENT),'v12_source_base':str(BASE),
        'manual_version':old_scope['manual_version'],
        **{k:old_scope[k] for k in ['manual','prompt','protocol','source_reading_protocol_code']},
        'actual_record_N':4481,'dimension_N':22405,'inherited_record_N':0,'max_runs':1,
        'allowed_mutable_dimensions':['S','E','Ec','F'],'immutable_dimensions':['I'],
        'conditional_S_contract':['finite_standard_S_content_or_dependency','current_parallel_treatment_benefit_risk'],
        'material_changed_record_ids':['RECODE25-02588','RECODE25-04598'],
        'output_directory':plan['proposed_paths']['actual_run'],
        'received_directory':plan['proposed_paths']['received_complete'],
        'wait_directory':plan['proposed_paths']['wait'],
        'wait_helper':next(x for x in plan['reuse_bindings'] if '/stability-durable-supervisor/' in x['path']),
        'python_executable':'/opt/homebrew/opt/python@3.14/bin/python3.14',
        'final_algorithm_manifest':None,'final_ROOT_review':None,'actual_release':None,
        'classification_executed':False,'ROOT_release_created':False}
    save(H/'execution-contract.json',contract)
    save(H/'static-input-preparation.json',{'full_frame_N':4481,'slot_N':22405,'inherited_N':0,
         'material_file_N':len(materials),'baseline_actual_log_N':len(logs),
         'packet_manifest_projection_exact':True,'source_sha_checks_passed':True,
         'no_classifier_import_or_call':True,'no_READ_or_USE_created':True,
         'script':bind(__file__),'outputs':[bind(H/n) for n in ['packet-bindings.json','full-frame.json','source-material-bindings.json','comparison-baseline-bindings.json','execution-contract.json']]})

if __name__=='__main__':prepare()
