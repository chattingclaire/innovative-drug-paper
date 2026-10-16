"""One authorized full800 draw and lossless v14 source preparation; no coding."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import datetime, hashlib, importlib.util, json, platform, random, shutil, struct, sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PLAN = ROOT / 'parallel-metrics/prospective-design'
SOURCE = ROOT / '01-review/context-projection-sol/source-interface-v14-textleaf'
SOURCE_BASE = ROOT / '01-review/context-projection-sol/full-frame-preflight'
MANUAL = ROOT / '06-coding/protocol-necessary-read-v3/manual-v1.3.txt'
SEED = 20261010
PRESENTATION_SEEDS = {'A': 'full800-source-v14-preparation-A-20261010',
                      'B': 'full800-source-v14-preparation-B-20261010'}
H = lambda b: hashlib.sha256(b).hexdigest()
def cj(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def bind(p):
    p = Path(p).resolve(); b = p.read_bytes()
    return {'absolute_path': str(p), 'bytes': len(b), 'sha256': H(b)}
def put(p, b):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with p.open('xb') as f: f.write(b)
    p.chmod(0o600)
def js(p, x): put(p, (json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode())
def jsonl(p, rows): put(p, b''.join((cj(x) + '\n').encode() for x in rows))

assert not (OUT / 'pre-draw-freeze.json').exists(), 'A draw already started; do not rerun or overwrite'
assert not (OUT / 'seal.json').exists(), 'Sealed input cannot be replaced'
OUT.chmod(0o700)
COORD = OUT / 'coordinator-private'; SHARED = OUT / 'shared-source'
COORD.mkdir(mode=0o700); SHARED.mkdir(mode=0o700)

input_paths = [PLAN / 'small-plan-comparison.json', PLAN / 'full-domain-supplement/full-domain-allocation.json',
               PLAN / 'inputs/metadata-and-fixed-labels.jsonl', PLAN / 'full-domain-supplement/full_domain_plan.py',
               ROOT / '01-review/exposure-ids.json', SOURCE / 'common-frame-bundles-v14.jsonl',
               SOURCE / 'frame-bundle-bindings-v14.jsonl', SOURCE / 'source_only_interface_v14.py', SOURCE / 'seal.json',
               SOURCE / 'development77-common-v14/source-resource-index.json', MANUAL,
               ROOT / '02-methods/prospective-statistical-contract-v2/validation-design-v2.json',
               ROOT / '07-statistics/prospective-engine-domain-sol/metrics_engine.py',
               ROOT / '07-statistics/prospective-engine-domain-sol/delivery-manifest.json']
inputs = [bind(p) for p in input_paths]
manual_binding = bind(MANUAL)
assert manual_binding['sha256'] == 'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f'
allocation = read(PLAN / 'full-domain-supplement/full-domain-allocation.json')
plan = allocation['plans']['full800']; assert plan['assigned_n'] == 800 and len(plan['strata']) == 41
rows = [json.loads(s) for s in (PLAN / 'inputs/metadata-and-fixed-labels.jsonl').read_text().splitlines()]
exposure = read(ROOT / '01-review/exposure-ids.json'); excluded = set(exposure['excluded_ids'])
assert len(rows) == 4481 and len(excluded) == 3037
frame_bindings = [json.loads(s) for s in (SOURCE / 'frame-bundle-bindings-v14.jsonl').read_text().splitlines()]
frame_ids = [r['id'] for r in frame_bindings]; fb = {r['id']: r for r in frame_bindings}
assert len(frame_ids) == len(set(frame_ids)) == 4481
assert set(frame_ids) == {r['id'] for r in rows}
assert set(frame_ids) - excluded == {r['id'] for r in rows if r['exposure'] == 'remaining'}
dev77 = set(read(SOURCE / 'development77-common-v14/source-resource-index.json')['fixed_record_ids_in_input_order'])
assert len(dev77) == 77 and dev77 <= excluded
spec = importlib.util.spec_from_file_location('existing_full800_partition', PLAN / 'full-domain-supplement/full_domain_plan.py')
old_plan = importlib.util.module_from_spec(spec); spec.loader.exec_module(old_plan)
metadata = {r['id']: r for r in rows}; groups = {}
for r in rows: groups.setdefault(old_plan.unit_stratum(r), []).append(r['id'])
assert Counter({k: len(v) for k, v in groups.items()}) == Counter({h['key']: h['N'] for h in plan['strata']})
assignment = [{'id': r['id'], 'stratum': old_plan.unit_stratum(r)} for r in sorted(rows, key=lambda r:r['id'])]
assert H(cj(assignment).encode()) == allocation['full_frame_stratum_assignment_hash_only']

freeze = {'version': 'full800-v14-source-preparation-1', 'selected_plan': 'full800',
          'root_authorization': 'ROOT explicitly selected existing full800 and seed20261010 for one actual draw and unreleased blank source packets; coding not authorized.',
          'frozen_at_utc_before_draw': now(), 'sampling_seed': SEED,
          'selector': {'python': sys.version, 'random_generator': 'stdlib random.Random(integer seed)',
                       'stratum_order': 'lexical stratum key', 'pool_order': 'lexical stable source ID',
                       'noncensus': 'rng.sample(pool,n_h), with no replacement; one generator consumed in frozen stratum order',
                       'census': 'all sorted IDs, no RNG call', 'post_selection_order': 'original sealed frame order',
                       'retry_or_seed_search': 'not permitted'},
          'presentation_seeds': PRESENTATION_SEEDS, 'presentation_algorithm': 'independent SHA256(string) integer seeds; shuffle sorted selected IDs; deterministic one-position B rotation only on complete order collision',
          'manual': dict(manual_binding, status='unchanged development preparation copy; final release freeze pending'),
          'statistics': {'contract': bind(ROOT / '02-methods/prospective-statistical-contract-v2/validation-design-v2.json'),
                         'engine': bind(ROOT / '07-statistics/prospective-engine-domain-sol/metrics_engine.py'),
                         'primary': 'joint unit FPC rescaled Rao-Wu bootstrap', 'B':5000, 'bootstrap_seed':20261010,
                         'sampling_seed_and_bootstrap_seed_distinct_purposes':True, 'CI':'marginal95', 'no_CI_gate_added':True},
          'population_N':4481, 'domain_population_N':{'remaining':1444,'exposed':3037},
          'sample_n':800, 'domain_sample_n':{'remaining':600,'exposed':200},
          'strata':plan['strata'], 'stratum_assignment_sha256':allocation['full_frame_stratum_assignment_hash_only'],
          'input_bindings':inputs, 'generator':bind(__file__), 'real_people_assigned':False,
          'final_release_freeze_completed':False, 'human_or_AI_coding_authorized':False}
js(OUT / 'pre-draw-freeze.json', freeze)

# Exactly one draw. There is no outcome input and no redraw branch.
started_draw = now(); rng = random.Random(SEED); chosen = set(); by_stratum = []
for h in sorted(plan['strata'], key=lambda h:h['key']):
    pool = sorted(groups[h['key']]); n = h['n']
    pick = pool[:] if n == len(pool) else rng.sample(pool, n)
    assert len(pick) == len(set(pick)) == n and not (chosen & set(pick))
    chosen.update(pick)
    by_stratum.append({'stratum':h['key'],'domain':h['domain'],'department':h['department'],
                       'N_h':h['N'],'n_h':n,'pi':h['pi'],'pi_exact':h['pi_exact'],
                       'weight':h['weight'],'weight_exact':h['weight_exact'],
                       'selected_ids_sorted':sorted(pick)})
selected_ids = [rid for rid in frame_ids if rid in chosen]
assert len(selected_ids) == len(chosen) == 800
design = {h['key']:h for h in plan['strata']}
admin_rows = []
for rid in selected_ids:
    r = metadata[rid]; h = design[old_plan.unit_stratum(r)]
    admin_rows.append({'source_id':rid,'stratum':h['key'],'domain':h['domain'],'department':h['department'],
                       'family_id':r['family'],'registered_exposure_status':r['exposure'],
                       'already_in_development77':rid in dev77,'N_h':h['N'],'n_h':h['n'],
                       'pi':h['pi'],'pi_exact':h['pi_exact'],'weight':h['weight'],'weight_exact':h['weight_exact']})
assert Counter(r['domain'] for r in admin_rows) == {'remaining':600,'exposed':200}
assert Counter(r['department'] for r in admin_rows) == plan['department_n']
weighted = {d:sum((Fraction(r['N_h'],r['n_h']) for r in admin_rows if d == 'ALL' or r['domain']==d), Fraction(0)) for d in ['ALL','remaining','exposed']}
assert weighted == {'ALL':Fraction(4481),'remaining':Fraction(1444),'exposed':Fraction(3037)}
weighted_dept = {d:sum((Fraction(r['N_h'],r['n_h']) for r in admin_rows if r['department']==d), Fraction(0)) for d in plan['department_population_N']}
assert {d:int(v) for d,v in weighted_dept.items()} == plan['department_population_N']
draw = {'version':'full800-actual-draw-v14-preparation-1','actual_drawn':True,'sampling_execution':'completed',
        'started_at_utc':started_draw,'completed_at_utc':now(),'sampling_seed':SEED,
        'pre_draw_freeze':bind(OUT / 'pre-draw-freeze.json'),'input_bindings':inputs,
        'plan_key':'full800','sample_n':800,'domain_sample_n':{'remaining':600,'exposed':200},
        'selected_record_ids_in_frame_order':selected_ids,'selected_ID_UTF8_LF_sha256':H(('\n'.join(selected_ids)+'\n').encode()),
        'selected_strata':by_stratum,'department_n':plan['department_n'],
        'weighted_assigned_population':{k:str(v) for k,v in weighted.items()},
        'weighted_assigned_department_population':{k:str(v) for k,v in weighted_dept.items()},
        'new_labels_available_at_draw':False,'human_coding_started':False,'real_people_assigned':False,
        'release_status':'prepared_not_released; final joint release freeze and real personnel pending',
        'old_plan_flags_not_modified':True}
js(COORD / 'draw-contract.json',draw)

spec = importlib.util.spec_from_file_location('sealed_source_v14_inventory', SOURCE / 'source_only_interface_v14.py')
source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
FORBIDDEN = set('labels label predictions prediction expected gold reference_label rule_hit score scores confidence dimension_reasons innovation_subtypes fairness_subtypes original_coder_answer sampling_stratum weight pi development_rationale verified_context_certificates'.split())
def check_source_only(v):
    if isinstance(v, dict):
        for k,z in v.items():
            kl=k.lower(); assert kl not in FORBIDDEN and not kl.startswith(('machine_','prediction_','old_label','expected_','gold_')), 'Result/private key in source bundle'
            check_source_only(z)
    elif isinstance(v,list):
        for z in v:check_source_only(z)
files = {}; checked_paths = {}; per_record = []; bundles = {}; raw_by_id = {}
def pixels(b):
    if b.startswith(b'\x89PNG\r\n\x1a\n'):w,h=struct.unpack('>II',b[16:24]);return {'width':w,'height':h,'format':'PNG'}
    if b.startswith((b'GIF87a',b'GIF89a')):w,h=struct.unpack('<HH',b[6:10]);return {'width':w,'height':h,'format':'GIF'}
    if b.startswith(b'\xff\xd8'):
        i=2
        while i+4<len(b):
            if b[i]!=255:i+=1;continue
            while i+1<len(b) and b[i+1]==255:i+=1
            marker=b[i+1]
            if marker in [0xD8,0xD9,0x01] or 0xD0<=marker<=0xD7:i+=2;continue
            n=int.from_bytes(b[i+2:i+4],'big')
            if marker in [0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF]:
                return {'width':int.from_bytes(b[i+7:i+9],'big'),'height':int.from_bytes(b[i+5:i+7],'big'),'format':'JPEG'}
            if n<2:break
            i+=2+n
    return None
def asset(path, expected, kind, rid, locator=None):
    p=Path(path).resolve(); key=str(p)
    if key not in checked_paths:
        b=p.read_bytes(); assert H(b)==expected, 'Asset/source file SHA mismatch'
        checked_paths[key]={'bytes':len(b),'sha256':H(b),'pixels':pixels(b)}
        suffix=p.suffix.lower() or '.bin'; dest=SHARED/'source-files'/(expected+suffix)
        if expected not in files:
            put(dest,b)
            files[expected]={'sha256':expected,'bytes':len(b),'prepared_absolute_path':str(dest),
                             'prepared_relative_path':str(dest.relative_to(OUT)),'original_absolute_paths':[],
                             'resource_kinds':[],'source_ids':[],'source_locators':[],'image_pixels':pixels(b)}
    a=files[expected];assert a['bytes']==checked_paths[key]['bytes']
    if key not in a['original_absolute_paths']:a['original_absolute_paths'].append(key)
    if kind not in a['resource_kinds']:a['resource_kinds'].append(kind)
    if rid not in a['source_ids']:a['source_ids'].append(rid)
    if locator is not None and locator not in a['source_locators']:a['source_locators'].append(locator)
    return expected
def explicit_paths(v,rid,found):
    if isinstance(v,dict):
        if isinstance(v.get('absolute_path'),str) and isinstance(v.get('sha256'),str):
            found.add(asset(v['absolute_path'],v['sha256'],'explicit_bound_file_view',rid))
        for z in v.values():explicit_paths(z,rid,found)
    elif isinstance(v,list):
        for z in v:explicit_paths(z,rid,found)
with (SOURCE/'common-frame-bundles-v14.jsonl').open('rb') as fh:
    for ordinal,line in enumerate(fh,1):
        rid=frame_ids[ordinal-1]
        if rid not in chosen:continue
        raw=line[:-1] if line.endswith(b'\n') else line; expected=fb[rid]
        assert len(raw)==expected['new_v14_bundle_utf8_bytes'] and H(raw)==expected['new_v14_bundle_sha256']
        bundle=json.loads(raw);assert bundle['source_record']['id']==rid and cj(bundle).encode()==raw
        check_source_only(bundle)
        rec=bundle['source_record'];assert H(rec['text'].encode())==expected['body_utf8_sha256']
        assert H(cj(rec).encode())==expected['source_record_object_sha256']
        assert H(cj(rec['contexts']).encode())==expected['old_CTX_object_sha256']
        found=set()
        for doc in bundle['source_documents']:
            found.add(asset(doc['snapshot'],doc['source_sha256'],'document_snapshot',rid))
            for field in ['source_text_resource','source_visual_text_resource','source_display_geometry_resource']:
                if doc.get(field):
                    z=doc[field];found.add(asset(SOURCE_BASE/z['relative_path'],z['sha256'],field,rid,{'source_document_sha256':doc['source_sha256']}))
        for resource in bundle['explicit_or_primary_source_resources']:
            snap=resource.get('snapshot')
            if not snap and resource.get('snapshot_relative_path'):snap=SOURCE_BASE/'source-library'/resource['snapshot_relative_path']
            if snap:found.add(asset(snap,resource.get('snapshot_sha256',resource.get('source_sha256')),'explicit_document_snapshot',rid))
        for image in bundle['source_asset_locations']:
            found.add(asset(image['absolute_path'],image['sha256'],'image_asset',rid,
                            {'source_document_sha256':image.get('source_pdf_sha256'),'physical_page':image.get('physical_page')}))
        explicit_paths(bundle,rid,found)
        inventory=source.source_inventory(bundle)
        bundles[rid]=bundle;raw_by_id[rid]=raw
        per_record.append({'source_id':rid,'bundle_canonical_sha256':H(raw),'bundle_UTF8_bytes':len(raw),
                           'source_record_canonical_sha256':H(cj(rec).encode()),'body_UTF8_sha256':expected['body_utf8_sha256'],
                           'CTX_object_canonical_sha256':expected['old_CTX_object_sha256'],'CTX_N':len(rec['contexts']),
                           'all_original_root_fields_preserved':list(bundle),'source_file_SHAs':sorted(found),
                           'available_source_inventory':inventory,'resource_available_not_method_read_or_use':True})
assert list(bundles)==selected_ids
put(SHARED/'common-source-bundles.jsonl',b''.join(raw_by_id[rid]+b'\n' for rid in selected_ids))
source_index={'version':'full800-source-v14-lossless-preparation-1','source_accessor':bind(SOURCE/'source_only_interface_v14.py'),
              'common_source_file':bind(SHARED/'common-source-bundles.jsonl'),'record_N':800,
              'per_record':per_record,'deduplicated_files':list(files.values()),
              'locator_policy':'Original bundle values/paths/locators remain unchanged; prepared byte-identical copies resolved by SHA and original absolute path through this index.',
              'available_not_actual_read_or_use':True,'image_pixels_from_file_headers_not_visual_certification':True}
js(SHARED/'source-resource-index.json',source_index)

orders={}
for side,seed in PRESENTATION_SEEDS.items():
    order=sorted(selected_ids);random.Random(int(H(seed.encode()),16)).shuffle(order);orders[side]=order
rotated=orders['A']==orders['B']
if rotated:orders['B']=orders['B'][1:]+orders['B'][:1]
assert orders['A']!=orders['B'] and set(orders['A'])==set(orders['B'])==chosen
packet_manifests={}; side_index={}; admin_by_id={r['source_id']:r for r in admin_rows}
GUIDE='''本包为未发布的来源材料准备版，不授权开始编码。共同手册v1.3保持原SHA和开发版声明；最终release freeze及真人安排由ROOT另行完成。
发布后仅在本方包内独立判读，完整当前正文→必要父子/表格范围→确指同版资源与必要原图；资源可用不等于实际读入或使用。资料不足记录具体未知/统一补材请求，不将未知或空白占位填0。
每条原v14完整bundle保留全部正文、CTX、公共资源、geometry、原locator、例示角色及未决来源版本。示例不是自动政策结论。原源绝对路径保留，source-assets-index.json提供同SHA实际准备副本。
labels.blank.jsonl全部unfilled null是占位，未产生任何首判/NA/unknown裁定。真人身份、开始/提交和图片阅读均留空。A/B分别分发；不得查看另一方包、coordinator-private、机器/参照答案或请求AI代填。
来源不足统一报告管理员，首判/补材重判/裁定另版封存。实际阅读、使用和真实身份须由发生后的真实记录证明；本生成器没有创建这些证据。
'''
for side in ['A','B']:
    folder=OUT/('coder-'+side);folder.mkdir(mode=0o700); lines=[]; idx=[]; blanks=[]; cursor=0
    for n,rid in enumerate(orders[side],1):
        blind=f'{side}-{n:06d}'; braw=raw_by_id[rid]
        packet={'packet_version':'full800-v14-role-wrapper-preparation-1','blind_id':blind,
                'source_bundle_canonical_sha256':H(braw),'source_bundle_canonical_UTF8_bytes':len(braw),
                'source_bundle':bundles[rid]}
        line=(cj(packet)+'\n').encode();lines.append(line)
        idx.append({'blind_id':blind,'packet_line_start_UTF8_byte':cursor,'packet_line_end_UTF8_byte_exclusive':cursor+len(line),
                    'packet_line_sha256':H(line),'source_bundle_canonical_sha256':H(braw),
                    'source_bundle_canonical_UTF8_bytes':len(braw)})
        cursor+=len(line)
        blanks.append({'blind_id':blind,'source_bundle_canonical_sha256':H(braw),'completion_status':'unfilled',
                       'dimensions':{d:{'value':None,'evidence_path':None,'current_quote':None,'context_quotes':[],
                                        'source_quotes':[],'reason':None,'material_request':None} for d in ['S','E','Ec','I','F']}})
        admin_by_id[rid][side+'_blind_id']=blind
    put(folder/'packet.jsonl',b''.join(lines));js(folder/'packet-index.json',{'version':'full800-v14-packet-index-1','side':side,'record_N':800,'entries':idx})
    put(folder/'manual-v1.3.txt',MANUAL.read_bytes());put(folder/'操作说明.txt',GUIDE.encode())
    jsonl(folder/'labels.blank.jsonl',blanks)
    js(folder/'source-assets-index.json',{'version':'full800-v14-prepared-assets-1','files':list(files.values()),'availability_not_reading_or_use':True})
    pm={'packet_version':'full800-v14-role-wrapper-preparation-1','status':'prepared_unreleased_no_coding_authorized',
        'side':side,'record_N':800,'dimension_blank_N':4000,'packet_file':bind(folder/'packet.jsonl'),
        'packet_index':bind(folder/'packet-index.json'),'manual':dict(bind(folder/'manual-v1.3.txt'),declared_status='development preparation copy'),
        'blank_labels_file':bind(folder/'labels.blank.jsonl'),'source_asset_index':bind(folder/'source-assets-index.json'),
        'common_bundle_multiset_SHA256':H(cj(sorted(H(raw_by_id[r]) for r in selected_ids)).encode()),
        'real_executor_assigned':False,'real_executor_code':None,'identity_registry_SHA256':None,
        'final_release_freeze_completed':False,'current_or_context_or_public_source_values_changed':False}
    js(folder/'packet-manifest.json',pm);packet_manifests[side]=pm;side_index[side]=idx
    js(folder/'submission.blank.json',{'version':'full800-v14-human-submission-preparation-1','completion_status':'unfilled',
                                     'packet_file_sha256':pm['packet_file']['sha256'],'manual_sha256':manual_binding['sha256'],
                                     'record_N':800,'dimensions_N':4000,'actual_actor_type':None,'executor_code':None,
                                     'identity_registry_sha256':None,'actual_started_at':None,'actual_submitted_at':None,
                                     'labels_sha256':None,'independence_declaration':None,'AI_assistance':None,
                                     'prior_development_exposure':None,'image_view_records':None,
                                     'source_read_or_use_attestation':None,'human_coding_completed':False})
assert packet_manifests['A']['common_bundle_multiset_SHA256']==packet_manifests['B']['common_bundle_multiset_SHA256']
js(COORD/'mapping.json',{'version':'full800-v14-coordinator-private-1','draw_contract':bind(COORD/'draw-contract.json'),
                       'records':admin_rows,'presentation_seeds':PRESENTATION_SEEDS,
                       'B_collision_rotation_applied':rotated,'no_auxiliary_prediction_values_copied':True,
                       'identity_registry_status':'pending_real_people; no fabricated participants',
                       'distribution_status':'not_released; independent permissions and final freeze pending'})

# Read back generated files once. Exact original values and source canonical bytes,
# not packet file SHA equality, establish A/B material equivalence.
seen_by_side={};blank_N=0
for side in ['A','B']:
    folder=OUT/('coder-'+side);seen={}
    with (folder/'packet.jsonl').open('rb') as f:
        for n,line in enumerate(f):
            p=json.loads(line);rid=p['source_bundle']['source_record']['id'];assert rid not in seen
            assert p['source_bundle']==bundles[rid] and cj(p['source_bundle']).encode()==raw_by_id[rid]
            assert H(line)==side_index[side][n]['packet_line_sha256'];check_source_only(p['source_bundle'])
            seen[rid]=H(cj(p['source_bundle']).encode())
    assert len(seen)==800 and set(seen)==chosen;seen_by_side[side]=seen
    for p in (folder/'labels.blank.jsonl').open():
        z=json.loads(p);assert z['completion_status']=='unfilled' and set(z['dimensions'])=={'S','E','Ec','I','F'}
        assert all(d['value'] is None and d['current_quote'] is None and d['reason'] is None for d in z['dimensions'].values());blank_N+=5
    sub=read(folder/'submission.blank.json');assert sub['actual_actor_type'] is None and sub['actual_started_at'] is None and sub['human_coding_completed'] is False
assert seen_by_side['A']==seen_by_side['B'] and blank_N==8000
for z in files.values():
    current=bind(z['prepared_absolute_path']);assert current['bytes']==z['bytes'] and current['sha256']==z['sha256']
for z in inputs:assert bind(z['absolute_path'])==z

image_files=[x for x in files.values() if 'image_asset' in x['resource_kinds']]
checks={'selected_N':800,'unique_N':800,'remaining_selected_N':600,'exposed_selected_N':200,
        'all41_actual_sample_counts_match_fixed_n':True,'all_selected_IDs_in_frozen_frame':True,
        'all_selected_original_body_CTX_and_root_values_match':True,'A_B_all800_source_bundle_values_and_canonical_bytes_equal':True,
        'actual_packet_file_SHA_separate_from_source_bundle_SHA':True,'same_original_manual_SHA_both_sides':True,
        'source_bundle_result_private_forbidden_key_occurrences_N':0,'public_private_design_mapping_in_packet_outer_fields':False,
        'blank_dimension_slots_N':8000,'all_blank_values_null_unfilled':True,'human_or_AI_judgment_N':0,
        'weighted_assigned_population':{k:str(v) for k,v in weighted.items()},'weighted_assigned_department_population':{k:str(v) for k,v in weighted_dept.items()},
        'original_input_bindings_unchanged_N':len(inputs),'prepared_actual_file_distinct_SHA_N':len(files),
        'prepared_actual_file_total_bytes_deduplicated':sum(x['bytes'] for x in files.values()),
        'prepared_image_asset_distinct_SHA_N':len(image_files),'prepared_image_asset_bytes':sum(x['bytes'] for x in image_files),
        'image_header_pixel_information_not_visual_certification':True,
        'selected_registered_development77_N':sum(r['already_in_development77'] for r in admin_rows),
        'final_release_freeze_completed':False,'actual_participants_assigned':False,'independent_access_controls_tested':False}
js(OUT/'mechanical-checks.json',checks)
js(OUT/'preparation-status.json',{'actual_drawn':True,'plan':'full800','seed':SEED,'actual_human_coding_started':False,
                                'real_human_labels_N':0,'AI_new_labels_N':0,'status':'material_preparation_complete_unreleased',
                                'release_pending':['ROOT final M/source/methods/statistical release freeze','real A/B and adjudication arrangements','independent distribution access test'],
                                'original_manual_development_declaration_preserved':True,
                                'source_technical_guideline_version_unknown_and_original_DOC_new_verification_false_preserved':True,
                                'coding_before_final_release_not_authorized':True})
put(OUT/'README.md',('Full800实际一次抽样与纯来源准备包。remaining600＋exposed200，41层固定分配，seed20261010；原计划、旧源、手册及旧尝试只读。\n\n'
                    'coder-A/B各800份完整v14 bundle；不同盲号/顺序，同一来源原值和canonical SHA。packet fileSHA另外绑定，不能用不同外套文件SHA冒称材料不同。完整原来源/图片实际同SHA副本在shared-source/source-files，原bundle locator未改，source-assets-index给副本路径。资源可用不表示实际读/用。\n\n'
                    '这是未release准备版：manual1.3原development正文同SHA保留。没有分配真人、开始时间、真人/AI首判或裁定；所有8000维空格是unfilled null占位。最终联合release freeze与独立分发访问确认前不得开始判读。A/B分别发各自目录，coordinator-private不得给编码员。原始source ID在完整bundle中为中性来源标识，不含分层/权重/历史开发77标志或旧预测值。\n\n'
                    'remaining域仅代表1444登记剩余池的独立检验；exposed200仍为开发曝光域，可能包括77开发ID，不能写作新holdout。full800支持全4481有限语料正概率审计，全域/两域从共同W及加权四格计算，不平均域指标；不是4481人工全文认证。统计契约保持joint FPC RaoWu5000/seed20261010，点值0.80目标不变，无新CI门槛。\n').encode())
print(json.dumps({'status':'unreleased_source_preparation_written','selected_N':800,'domains':{'remaining':600,'exposed':200},
                  'asset_distinct_SHA_N':len(files),'asset_total_bytes':checks['prepared_actual_file_total_bytes_deduplicated'],
                  'images_N':len(image_files),'selected_development77_N':checks['selected_registered_development77_N']},ensure_ascii=False))
