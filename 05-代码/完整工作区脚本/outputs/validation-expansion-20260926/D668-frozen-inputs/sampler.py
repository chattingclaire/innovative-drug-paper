"""D668 supplementary AI content-analysis sampler, never a new validation.

Import performs no study reads or draws. --inspect validates metadata without
loading material helpers or constructing an RNG. --draw requires the final,
hash-complete contract and reserves its fixed ledger and release directory
before the first RNG call. Incomplete directories remain quarantined; only a
valid final seal permits distribution. There is no redraw/recovery command.

--self-test reads code dependencies only and uses invented temporary fixtures.
It never reads actual study corpus, materials, labels or predictions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version as package_version
import json
import math
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import types

SCHEMA = 'd668_content_analysis_freeze_v1'
PHASE = 'D668'
FINAL = 'frozen_for_D668_supplementary_AI_content_analysis'
DRAFT = 'draft_D668_not_authorized_for_draw'
PURPOSE = 'supplementary_AI_content_analysis'
SEED = 2026092607
N = {'NMPA': 1077, 'NHSA': 1662, 'NHC': 329, 'GOV': 325}
M = {'NMPA': 133, 'NHSA': 222, 'NHC': 148, 'GOV': 165}
R_N = {'NMPA': 771, 'NHSA': 438, 'NHC': 204, 'GOV': 118}
ORDER = ['NMPA', 'NHSA', 'NHC', 'GOV']
ORDERING = 'one PCG64; departments NMPA,NHSA,NHC,GOV; lexical global review_id within department; choice indices without replacement; one same-RNG permutation of all 668 selected IDs'
DOCS = {'protocol': '五维共用编码协议.md', 'protocol_clarifications': '共同执行澄清.md',
        'reviewer_instructions': '评审任务说明.md'}
INHERITED = {k: k for k in ('corpus', 'adapter', 'classification', 'exposure',
             'protocol', 'protocol_clarifications', 'sample_helpers', 'legacy_results_helpers', 'results_bridge')}
INHERITED['v600_sampler'] = 'sampler'
FILES = set(INHERITED) | {'v600_freeze', 'v600_sampling_manifest', 'v600_seal',
        'reviewer_instructions', 'analysis_plan', 'sampler', 'statistics', 'admin_receiver',
        'r600_source_manifest', 'analysis_bridge'}
DRAFT_OPTIONAL = {'sampler', 'statistics', 'admin_receiver', 'r600_source_manifest', 'analysis_bridge'}
ROW_KEYS = {'id', 'text', 'source_title', 'pages', 'contexts', 'input_assessment', 'context_usage'}
PACKET_KEYS = {'protocol_version', 'purpose', 'batch', 'total_batches', 'rows'}
CONTEXT_USAGE = '只编码text；使用核验语境消解对象、条件、指代，不复制上级全标签。nearest_preceding_heading和immediately_preceding_paragraph仅表示位置相邻，未经核验不可自动当有效父级。材料不足保留待定。'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()


def digest(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode())


def read_json(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'Duplicate JSON key')
            out[k] = v
        return out
    def bad(_):
        raise ValueError('Nonfinite JSON number')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    def finite(x):
        if isinstance(x, float):
            require(math.isfinite(x), 'Nonfinite JSON number')
        elif isinstance(x, dict):
            for v in x.values(): finite(v)
        elif isinstance(x, list):
            for v in x: finite(v)
    finite(value)
    return value


def runtime():
    return {'python_version': platform.python_version(), 'numpy': package_version('numpy')}


def hash_string(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def canonical_path(value):
    require(isinstance(value, str), 'Path string required')
    path = Path(value)
    require(path.is_absolute() and str(path.resolve()) == value, 'Absolute resolved canonical path required')
    return path


def unique(rows, key):
    require(isinstance(rows, list), 'Row list required')
    out = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str) and row[key], 'Nonempty string ID required')
        require(row[key] not in out, 'Duplicate ID')
        out[row[key]] = row
    return out


def id_set(values):
    require(isinstance(values, list) and all(isinstance(x, str) and x for x in values)
            and len(values) == len(set(values)), 'Unique string ID list required')
    return set(values)


def check_contract(freeze, freeze_path, final):
    require(isinstance(freeze, dict) and freeze.get('schema') == SCHEMA, 'D668 schema required')
    require(freeze.get('status') == FINAL if final else freeze.get('status') in (DRAFT, FINAL), 'D668 final freeze required for draw')
    expected = {'phase': PHASE, 'purpose': PURPOSE, 'sampling_seed': SEED, 'random_generator': 'numpy.random.PCG64',
                'sample_n': 668, 'sample_budget': 668, 'U_N': 4924, 'R_N': 1531, 'D_N': 3393,
                'department_N': N, 'department_n': M, 'department_order': ORDER,
                'ordering': ORDERING, 'batch_size': 25, 'coders': ['A', 'C']}
    for k, value in expected.items():
        require(type(freeze.get(k)) is type(value) and freeze[k] == value, 'Unexpected frozen design field: '+k)
    for mapping in ('department_N', 'department_n'):
        require(all(type(x) is int for x in freeze[mapping].values()), 'Literal integer allocations required')
    require(isinstance(freeze.get('runtime'), dict) and all(freeze['runtime'].get(k) == v
            for k, v in runtime().items()), 'Python/NumPy runtime differs from contract')
    require(isinstance(freeze.get('protocol_version'), str) and freeze['protocol_version'], 'Protocol version required')
    fields = freeze.get('context_fields')
    require(isinstance(fields, list) and fields and len(fields) == len(set(fields)), 'Unique context fields required')
    require(isinstance(freeze.get('files'), dict) and set(freeze['files']) == FILES,
            'Exact sampler input allowlist required; do not include labels or predictions')
    release = canonical_path(freeze.get('release_directory'))
    ledger = canonical_path(freeze.get('ledger_path'))
    require(ledger == freeze_path.parent / '.D668-sampling-attempt.json', 'Fixed study-level ledger path required')
    require(release.parent == freeze_path.parent and release.name == 'D668', 'Release must be the canonical sibling D668 directory')
    return release, ledger


def load_snapshot(freeze_path, final):
    freeze_path = canonical_path(str(freeze_path))
    freeze_raw = freeze_path.read_bytes(); freeze = read_json(freeze_raw)
    release, ledger = check_contract(freeze, freeze_path, final)
    snapshots, tracked, missing = {}, {str(freeze_path): sha(freeze_raw)}, []
    for name in sorted(FILES):
        entry = freeze['files'][name]
        require(isinstance(entry, dict) and set(entry) == {'path', 'sha256', 'byte_count'}, 'Exact path/hash/byte_count entry required')
        path = canonical_path(entry['path'])
        require(path != release and release not in path.parents and path != ledger, 'Frozen inputs must be outside release/ledger')
        if not final and freeze['status'] == DRAFT and name in DRAFT_OPTIONAL and (entry['sha256'] is None or entry['byte_count'] is None):
            missing.append(name); continue
        require(hash_string(entry['sha256']) and type(entry['byte_count']) is int and entry['byte_count'] >= 0, 'Complete frozen binding required: '+name)
        data = path.read_bytes()
        require(sha(data) == entry['sha256'] and len(data) == entry['byte_count'], 'Frozen file changed: '+name)
        if str(path) in tracked:
            require(tracked[str(path)] == sha(data), 'Input changed during snapshot')
        tracked[str(path)] = sha(data); snapshots[name] = data
    if 'sampler' in snapshots:
        require(sha(Path(__file__).read_bytes()) == sha(snapshots['sampler']), 'Running sampler differs from frozen sampler')
    return {'freeze': freeze, 'freeze_raw': freeze_raw, 'snapshots': snapshots, 'tracked': tracked,
            'release': release, 'ledger': ledger, 'missing_bindings': missing}


def metadata_preflight(bundle):
    """No module execution, RNG construction, text selection or packet building."""
    f, b = bundle['freeze'], bundle['snapshots']
    prior = read_json(b['v600_freeze'])
    require(prior.get('phase') == 'V600' and prior.get('status') == 'frozen_for_paired_reference_label_holdout', 'Frozen V600 parent required')
    require(f['protocol_version'] == prior['protocol_version'] and f['context_fields'] == prior['context_fields'], 'Manual/context contract must equal V600')
    for key, old in INHERITED.items():
        require(sha(b[key]) == prior['files'][old]['sha256'], 'Changed inherited V600 bytes: '+key)
    corpus = [read_json(line) for line in b['corpus'].splitlines() if line.strip()]
    allunits = unique(corpus, 'review_id')
    require(all(type(x.get('count_as_analysis_unit')) is bool for x in corpus), 'Literal analysis flags required')
    units = {k: v for k, v in allunits.items() if v['count_as_analysis_unit']}
    require(len(units) == 4924, 'Analysis frame must contain 4924 units')
    exposure = read_json(b['exposure']); R = id_set(exposure['provisional_eligible_ids']); D = id_set(exposure['exclusions'])
    require(len(R) == 1531 and len(D) == 3393 and not R & D and R | D == set(units), 'U/R/D must be a disjoint exhaustive partition')
    classification = read_json(b['classification'])
    classes = unique([{**x, 'stem': Path(x['original_file']).stem} for x in classification['rows']], 'stem')
    adapter = read_json(b['adapter']); documents = unique(adapter['documents'], 'id'); prepared = unique(adapter['units'], 'id')
    binding = adapter['binding']; verified = adapter['verified_files']
    require(digest(binding) == adapter['binding_sha256'], 'Adapter binding digest mismatch')
    require(binding['adapter_version'] == adapter['version'] and binding['classification_version'] == classification['version'], 'Adapter metadata version mismatch')
    require(binding['input_sha256']['corpus'] == sha(b['corpus']) and binding['input_sha256']['classification'] == sha(b['classification']), 'Adapter/corpus/classification bytes mismatch')
    require(digest({'documents': adapter['documents'], 'units': adapter['units']}) == binding['prepared_payload_sha256'], 'Adapter payload digest mismatch')
    require(digest(verified) == binding['verified_files_sha256'], 'Verified source manifest digest mismatch')
    require(set(prepared) == set(units) == set(binding['analysis_unit_fingerprints']), 'Adapter/corpus ID inventory mismatch')
    pools = {g: [] for g in ORDER}; groups = {}
    for key, unit in units.items():
        require(isinstance(unit.get('unit_text'), str) and unit['unit_text'].strip(), 'Full unit text required')
        require(isinstance(unit.get('pages'), list) and all(type(x) is int and x > 0 for x in unit['pages']), 'Valid unit pages required')
        stem = unit['original_file_stem']; group = classes[stem]['analysis_group']
        require(group in pools and documents[stem]['group'] == group, 'Department metadata mismatch')
        groups[key] = group
        require(digest(unit) == binding['analysis_unit_fingerprints'][key] == prepared[key]['record_sha256'], 'Source/context record binding mismatch')
        require(prepared[key]['text'] == unit['unit_text'] and prepared[key]['unit_text_sha256'] == sha(unit['unit_text'].encode()), 'Unit text/hash mismatch')
        require(prepared[key]['document_id'] == stem, 'Adapter source entry mismatch')
        require(isinstance(unit.get('source'), str) and hash_string(unit.get('source_sha256'))
                and verified.get(unit['source']) == unit['source_sha256'], 'Primary source hash missing from frozen verified manifest')
        if unit.get('unit_source') is not None or unit.get('unit_source_sha256') is not None:
            require(isinstance(unit.get('unit_source'), str) and hash_string(unit.get('unit_source_sha256'))
                    and verified.get(unit['unit_source']) == unit['unit_source_sha256'], 'Component source hash missing from frozen verified manifest')
        if key in D: pools[group].append(key)
    require({g: len(x) for g, x in pools.items()} == N, 'D department counts differ from frozen design')
    require(dict(Counter(groups[k] for k in R)) == R_N, 'R department counts differ from V600')
    mapping, seal = read_json(b['v600_sampling_manifest']), read_json(b['v600_seal'])
    require(seal['freeze_manifest_sha256'] == sha(b['v600_freeze']) and seal['release_status'] == 'ready_for_blind_review', 'V600 seal/freeze mismatch')
    require(seal['output_files']['抽样清单-研究者.json'] == sha(b['v600_sampling_manifest']), 'V600 researcher manifest hash mismatch')
    plan = mapping['plan']; require(all(seal.get(k) == v for k, v in plan.items()), 'V600 plan/seal mismatch')
    require(plan['phase'] == 'V600' and plan['status'] == 'drawn' and plan['N_star'] == 1531 and plan['n'] == 600, 'V600 design mismatch')
    require(plan['freeze_manifest_sha256'] == sha(b['v600_freeze']), 'V600 manifest/freeze mismatch')
    vm = unique(mapping['rows'], 'review_id'); unique(mapping['rows'], 'id')
    require(len(vm) == 600 and set(vm) <= R and id_set(mapping['not_selected_ids']) == R-set(vm), 'V600 ID partition mismatch')
    for key, row in vm.items():
        require(row['group'] == groups[key] and row['unit_text_sha256'] == sha(units[key]['unit_text'].encode()), 'V600 source/ID mismatch')
    return {'units': units, 'pools': {g: sorted(x) for g, x in pools.items()}, 'groups': groups, 'R': R, 'D': D,
            'summary': {'phase': PHASE, 'U_N': 4924, 'R_N': 1531, 'D_N': 3393, 'department_N': N,
                        'department_n': M, 'n': 668, 'batches': 27, 'batch_sizes': [25]*26+[18],
                        'ordering': ORDERING, 'draw_performed': False, 'packets_created': False,
                        'missing_final_bindings': bundle['missing_bindings'],
                        'source_binding_limit': 'Checks frozen provenance hashes; does not reopen or semantically reverify original source documents.'}}


def frozen_module(raw, name):
    module = types.ModuleType('_d668_frozen_'+name)
    module.__file__ = '<hash-verified '+name+'.py>'
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def helpers_for_materials(bundle):
    b = bundle['snapshots']
    helpers = frozen_module(b['sample_helpers'], 'sample_helpers')
    sampler = frozen_module(b['v600_sampler'], 'v600_sampler')
    fields = bundle['freeze']['context_fields']
    require(set(fields) <= set(helpers.DEFAULT_CONTEXT_FIELDS) | {'verified_object_scope'}, 'Unreviewed material context root')
    return helpers, sampler


def make_material(unit, blind_id, fields, helpers, sampler):
    row = {'id': blind_id, 'text': unit['unit_text'], 'source_title': unit['original_file_stem'],
           'pages': unit['pages'], 'contexts': sampler.material_contexts(unit, fields, helpers.__dict__),
           'input_assessment': helpers.clean_assessment(unit.get('input_assessment', {'status': 'not_assessed'})),
           'context_usage': CONTEXT_USAGE}
    require(set(row) == ROW_KEYS and row['text'] == unit['unit_text'], 'Material text/field mismatch')
    require(set(row['contexts']) <= set(fields), 'Unexpected material context root')
    def scan(value, allowed):
        if isinstance(value, dict):
            require(set(value) <= allowed, 'Disallowed context/assessment field')
            for child in value.values(): scan(child, allowed)
        elif isinstance(value, list):
            for child in value: scan(child, allowed)
    for key, value in row['contexts'].items():
        if key != 'verified_object_scope': scan(value, helpers.CONTEXT_KEYS)
        # Object scopes have an exact, independently checked schema in the frozen material function.
    scan(row['input_assessment'], {'status','basis','reason','source','verification','assessed_at'})
    return row


def select_ids(frame):
    import numpy as np
    rng = np.random.Generator(np.random.PCG64(SEED)); selected = []
    for group in ORDER:
        ids = frame['pools'][group]
        require(ids == sorted(ids) and len(ids) == N[group], 'Noncanonical department pool')
        indices = rng.choice(len(ids), size=M[group], replace=False)
        selected.extend(ids[int(i)] for i in indices)
    selection_order = list(selected)
    selected = [selected[int(i)] for i in rng.permutation(len(selected))]
    require(len(selected) == len(set(selected)) == 668 and set(selected) <= frame['D']
            and not set(selected) & frame['R'], 'Invalid D-only SRSWOR selection')
    return selected, selection_order


def construct_release(bundle, frame):
    helpers, sampler = helpers_for_materials(bundle)
    fields = bundle['freeze']['context_fields']
    # Validate all D material contracts before RNG, so unselected corrupt scopes cannot escape validation.
    for group in ORDER:
        for key in frame['pools'][group]: make_material(frame['units'][key], 'PREFLIGHT', fields, helpers, sampler)
    selected, selection_order = select_ids(frame)
    rows, materials = [], []
    for i, key in enumerate(selected, 1):
        unit, group = frame['units'][key], frame['groups'][key]
        blind_id = f'D668-{i:04d}'
        rows.append({'id': blind_id, 'review_id': key, 'group': group, 'stratum': group,
                     'N_h': N[group], 'n_h': M[group], 'pi': M[group]/N[group], 'weight': N[group]/M[group],
                     'source_entry': unit['original_file_stem'], 'source_sha256': unit['source_sha256'],
                     'effective_source_sha256': unit.get('unit_source_sha256') or unit['source_sha256'],
                     'unit_text_sha256': sha(unit['unit_text'].encode()), 'record_sha256': digest(unit)})
        materials.append(make_material(unit, blind_id, fields, helpers, sampler))
    plan = {'phase': PHASE, 'status': 'drawn', 'purpose': PURPOSE, 'N_star': 3393, 'n': 668,
            'U_N': 4924, 'R_N': 1531, 'seed': SEED, 'random_generator': 'numpy.random.PCG64',
            'runtime': runtime(), 'ordering': ORDERING, 'department_order': ORDER,
            'strata': {g: {'N_h': N[g], 'n_h': M[g], 'pi': M[g]/N[g], 'weight': N[g]/M[g]} for g in ORDER},
            'batch_size': 25, 'batch_sizes': [25]*26+[18], 'scope': 'Supplementary AI content analysis in D; not new independent validation.',
            'freeze_manifest_sha256': sha(bundle['freeze_raw']),
            'input_hashes': {k: sha(v) for k, v in bundle['snapshots'].items()}}
    mapping = {'plan': plan, 'rows': rows, 'not_selected_ids': sorted(frame['D']-set(selected)),
               'selection_order_before_display_shuffle': selection_order}
    released = {'抽样清单-研究者.json': encode(mapping)}
    for coder in ('A','C'):
        for key, filename in DOCS.items(): released[f'agent-{coder}/{filename}'] = bundle['snapshots'][key]
        for batch in range(27):
            packet = {'protocol_version': bundle['freeze']['protocol_version'], 'purpose': PURPOSE,
                      'batch': batch+1, 'total_batches': 27, 'rows': materials[batch*25:(batch+1)*25]}
            require(set(packet) == PACKET_KEYS and len(packet['rows']) == (18 if batch==26 else 25), 'Packet schema/count mismatch')
            released[f'agent-{coder}/材料-{batch+1:02d}.json'] = encode(packet)
    require(len(released) == 61, 'Released inventory must contain 54 packets, 6 documents and one mapping')
    for name, data in released.items():
        if name.startswith('agent-A/'):
            require(released[name.replace('agent-A/','agent-C/',1)] == data, 'A/C full material bytes differ')
    return plan, released


def unchanged(bundle):
    for path, expected in bundle['tracked'].items():
        require(sha(Path(path).read_bytes()) == expected, 'Input changed; attempt must remain quarantined')


def exclusive(path, data):
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def draw(freeze_path):
    bundle = load_snapshot(freeze_path, final=True)
    release, ledger = bundle['release'], bundle['ledger']
    require(not os.path.lexists(release) and not os.path.lexists(ledger), 'Prior directory/ledger exists; no redraw')
    frame = metadata_preflight(bundle); unchanged(bundle)
    ledger_raw = encode({'schema':'d668_single_attempt_v1', 'phase':PHASE, 'freeze_sha256':sha(bundle['freeze_raw']),
                         'freeze_path':str(freeze_path), 'release_directory':str(release), 'seed':SEED,
                         'created_at':datetime.now(timezone.utc).isoformat(),
                         'rule':'Reserved before any RNG; failure preserves ledger/directory; only final valid seal authorizes distribution.'})
    exclusive(ledger, ledger_raw)
    # Exclusive destination reservation avoids directory-rename overwrite races.
    # No release is usable until its final seal exists and verifies every output.
    release.mkdir()
    plan, outputs = construct_release(bundle, frame)
    for coder in ('A','C'): (release/('agent-'+coder)).mkdir()
    for relative, data in outputs.items(): exclusive(release/relative, data)
    unchanged(bundle)
    expected_files = set(outputs)
    require({str(p.relative_to(release)) for p in release.rglob('*') if p.is_file()} == expected_files, 'Unexpected release file inventory')
    for relative, data in outputs.items():
        require((release/relative).read_bytes() == data, 'Written output changed before sealing')
    require(ledger.read_bytes() == ledger_raw, 'Attempt ledger changed')
    seal = {**plan, 'release_status':'ready_for_blind_review', 'created_at':datetime.now(timezone.utc).isoformat(),
            'ledger_path':str(ledger),'ledger_sha256':sha(ledger_raw),
            'output_files':{name:sha(data) for name,data in outputs.items()}}
    partial = release/'.封存信息.json.partial'; final = release/'封存信息.json'
    exclusive(partial, encode(seal)); os.link(partial, final); partial.unlink()
    return {'status':'drawn_once', 'phase':PHASE,'purpose':PURPOSE,'n':668,'N_star':3393,
            'batches_per_AI':27,'directory':str(release),'ledger':str(ledger)}


def synthetic_bundle(root, helper_bytes, old_sampler_bytes):
    """Invented full-sized fixture; source paths are provenance strings, never reopened."""
    fields=['paragraph_context','verified_rule_branch_context','verified_object_scope']
    corpus=[];R=[];D=[];documents=[];classes=[];verified={}
    for g in ORDER:
        source='/synthetic/'+g+'.pdf';source_hash=sha(('FICTIONAL '+g).encode());verified[source]=source_hash
        documents.append({'id':g,'group':g,'series':'synthetic','publication_date':'2000-01-01'})
        classes.append({'original_file':g+'.pdf','analysis_group':g})
        for i in range(R_N[g]+N[g]):
            key=f'{g}-{i:05d}'
            (R if i<R_N[g] else D).append(key)
            corpus.append({'review_id':key,'unit_id':'local-'+str(i%7),'original_file_stem':g,
                'source':source,'source_sha256':source_hash,'unit_source':source,'unit_source_sha256':source_hash,
                'count_as_analysis_unit':True,'unit_text':'FICTIONAL '+key+' 😀\n完整虚构材料\t', 'pages':[1],
                'paragraph_context':{'text':'FICTIONAL CONTEXT','labels':{'S':1},'predictions':{'I':1}}})
    cbytes=b''.join(encode(x).replace(b'\n',b' ') + b'\n' for x in corpus)
    classification={'version':'synthetic-v1','rows':classes};class_bytes=encode(classification)
    prepared=[{'id':x['review_id'],'document_id':x['original_file_stem'],'text':x['unit_text'],
               'unit_text_sha256':sha(x['unit_text'].encode()),'record_sha256':digest(x)} for x in corpus]
    binding={'adapter_version':'synthetic-v1','classification_version':'synthetic-v1',
             'input_sha256':{'corpus':sha(cbytes),'classification':sha(class_bytes)},
             'prepared_payload_sha256':digest({'documents':documents,'units':prepared}),
             'analysis_unit_fingerprints':{x['id']:x['record_sha256'] for x in prepared},'verified_files_sha256':digest(verified)}
    adapter={'version':'synthetic-v1','documents':documents,'units':prepared,'binding':binding,'binding_sha256':digest(binding),'verified_files':verified}
    data={'corpus':cbytes,'adapter':encode(adapter),'classification':class_bytes,
          'exposure':encode({'provisional_eligible_ids':R,'exclusions':D}), 'protocol':b'FICTIONAL MANUAL\n',
          'protocol_clarifications':b'FICTIONAL CLARIFICATION\n','sample_helpers':helper_bytes,
          'v600_sampler':old_sampler_bytes,'legacy_results_helpers':b'raise AssertionError("MUST NOT EXECUTE")\n',
          'results_bridge':b'raise AssertionError("MUST NOT EXECUTE")\n','reviewer_instructions':b'FICTIONAL supplementary content analysis instructions\n',
          'analysis_plan':b'FICTIONAL plan\n','sampler':Path(__file__).read_bytes(),
          'statistics':b'raise AssertionError("STATISTICS MUST NOT EXECUTE")\n',
          'admin_receiver':b'raise AssertionError("RECEIVER MUST NOT EXECUTE")\n',
          'analysis_bridge':b'raise AssertionError("ANALYSIS BRIDGE MUST NOT EXECUTE")\n',
          'r600_source_manifest':b'FICTIONAL PATH/HASH METADATA; MUST NOT PARSE\n'}
    prior={'phase':'V600','status':'frozen_for_paired_reference_label_holdout','protocol_version':'synthetic-v1','context_fields':fields,
           'files':{old:{'sha256':sha(data[key])} for key,old in INHERITED.items()}}
    data['v600_freeze']=encode(prior)
    vr=[]
    R_ids=set(R)
    for g, amount in zip(ORDER,(303,172,79,46)):
        for x in [x for x in corpus if x['review_id'] in R_ids and x['original_file_stem']==g][:amount]:
            vr.append({'id':f'V600-{len(vr)+1:04d}','review_id':x['review_id'],'group':g,'unit_text_sha256':sha(x['unit_text'].encode())})
    vp={'phase':'V600','status':'drawn','N_star':1531,'n':600,'freeze_manifest_sha256':sha(data['v600_freeze'])}
    data['v600_sampling_manifest']=encode({'plan':vp,'rows':vr,'not_selected_ids':sorted(set(R)-{x['review_id'] for x in vr})})
    data['v600_seal']=encode({**vp,'release_status':'ready_for_blind_review','output_files':{'抽样清单-研究者.json':sha(data['v600_sampling_manifest'])}})
    f={'schema':SCHEMA,'status':FINAL,'phase':PHASE,'purpose':PURPOSE,'sampling_seed':SEED,
       'random_generator':'numpy.random.PCG64','sample_n':668,'sample_budget':668,'U_N':4924,'R_N':1531,'D_N':3393,
       'department_N':N,'department_n':M,'department_order':ORDER,'ordering':ORDERING,'batch_size':25,
       'coders':['A','C'],'runtime':runtime(),'protocol_version':'synthetic-v1','context_fields':fields,
       'release_directory':str(root/'D668'),'ledger_path':str(root/'.D668-sampling-attempt.json'),
       'files':{k:{'path':str(root/'inputs'/k),'sha256':sha(v),'byte_count':len(v)} for k,v in data.items()}}
    return f,data


def self_test():
    # Named code dependencies only. No real corpus, freeze, material or result is read.
    here=Path(__file__).resolve().parent
    helper=(here/'V600-frozen-inputs/sample_helpers.py').read_bytes()
    old=(here/'V600-frozen-inputs/sampler.py').read_bytes()
    checks=[]
    with tempfile.TemporaryDirectory(prefix='d668-pure-synthetic-') as temp:
        root=Path(temp).resolve();f,b=synthetic_bundle(root,helper,old)
        (root/'inputs').mkdir()
        for k,v in b.items():exclusive(root/'inputs'/k,v)
        fp=root/'freeze.json';exclusive(fp,encode(f))
        snapshot=load_snapshot(fp,True);frame=metadata_preflight(snapshot)
        require(not (root/'D668').exists() and not (root/'.D668-sampling-attempt.json').exists(), 'Inspect wrote a release/ledger')
        checks.append('metadata_preflight_creates_no_rng_packets_or_ledger')
        p,release=construct_release(snapshot,frame);p2,release2=construct_release(snapshot,frame)
        require(p==p2 and release==release2,'Nondeterministic synthetic draw')
        mapping=read_json(release['抽样清单-研究者.json'])
        require(Counter(x['group'] for x in mapping['rows'])==M,'Synthetic department allocation differs')
        require(len({x['review_id'] for x in mapping['rows']})==668 and not {x['review_id'] for x in mapping['rows']}&frame['R'],'Synthetic selection violates partition')
        checks.extend(['fixed_PCG64_seed_and_order_reproduce_full_bytes','668_unique_D_only_exact_department_allocation','27_batches_26x25_plus18','A_C_material_and_document_bytes_identical'])
        for batch in range(1,28):
            packet=read_json(release[f'agent-A/材料-{batch:02d}.json'])
            for row in packet['rows']:
                require(set(row)==ROW_KEYS and set(row['contexts']['paragraph_context'])=={'text'},'Forbidden material field leaked')
        checks.append('recursive_allowed_field_scan_removes_label_prediction_fields')
        helpers,sampler=helpers_for_materials(snapshot)
        unit=dict(next(iter(frame['units'].values())));unit['unit_text']='😀 完整虚构长文\r\n\t'*7000
        material=make_material(unit,'SYNTHETIC-LONG',f['context_fields'],helpers,sampler)
        require(material['text']==unit['unit_text'] and len(material['text'])>32767,'Long original truncated')
        checks.append('long_unicode_text_whitespace_preserved_without_truncation')
        # Confirm invalid material source binding fails before any real release.
        rejected=[]
        def reject(name,fn):
            try:fn()
            except (ValueError,KeyError,FileExistsError):rejected.append(name)
            else:raise AssertionError('Synthetic invalid case accepted: '+name)
        broken=read_json(encode(f));broken['status']=DRAFT
        reject('draft_draw_contract',lambda:check_contract(broken,fp,True))
        broken=read_json(encode(f));broken['sampling_seed']+=1
        reject('changed_seed',lambda:check_contract(broken,fp,True))
        broken=read_json(encode(f));broken['department_n']['NMPA']+=1
        reject('changed_allocation',lambda:check_contract(broken,fp,True))
        broken=read_json(encode(f));broken['files']['predictions']={'path':'/unread','sha256':'0'*64,'byte_count':0}
        reject('prediction_file_not_allowlisted',lambda:check_contract(broken,fp,True))
        badbundle={**snapshot,'snapshots':dict(snapshot['snapshots'])}
        exp=read_json(b['exposure']);exp['exclusions'][0]=exp['provisional_eligible_ids'][0];badbundle['snapshots']['exposure']=encode(exp)
        reject('R_D_corruption',lambda:metadata_preflight(badbundle))
        badbundle={**snapshot,'snapshots':dict(snapshot['snapshots'])};badbundle['snapshots']['protocol']=b'CHANGED'
        reject('old_manual_bytes_changed',lambda:metadata_preflight(badbundle))
        # Actual filesystem orchestration is exercised only in this invented directory.
        outcome=draw(fp);require(outcome['n']==668,'Synthetic draw did not complete')
        seal=read_json((root/'D668/封存信息.json').read_bytes())
        require(len(seal['output_files'])==61 and seal['input_hashes']=={k:sha(v) for k,v in b.items()},'Seal binding differs')
        reject('repeat_same_freeze',lambda:draw(fp))
        copy=root/'freeze-copy.json';exclusive(copy,encode(f))
        reject('copied_freeze_same_global_ledger',lambda:draw(copy))
        checks.extend(['all_20_input_hashes_and_self_hash_verified','only_material_helpers_executed_not_statistics_receiver_bridge',
                       'exclusive_global_ledger_precedes_RNG','sealed_inventory_61_files_and_input_hashes','no_overwrite_or_redraw'])
        # A post-ledger failure is quarantined and blocks the next attempt.
        failed=root/'failed';failed.mkdir();ff,bb=synthetic_bundle(failed,helper,old);(failed/'inputs').mkdir()
        for k,v in bb.items():exclusive(failed/'inputs'/k,v)
        ffp=failed/'freeze.json';exclusive(ffp,encode(ff))
        original_select=globals()['select_ids']
        def fail_after_reservation(_):
            require((failed/'.D668-sampling-attempt.json').exists() and (failed/'D668').exists(),'RNG preceded reservation')
            raise ValueError('FICTIONAL post-ledger selection failure')
        globals()['select_ids']=fail_after_reservation
        try:reject('failed_attempt_quarantined',lambda:draw(ffp))
        finally:globals()['select_ids']=original_select
        require((failed/'.D668-sampling-attempt.json').exists() and (failed/'D668').exists()
                and not (failed/'D668/封存信息.json').exists(),'Failed attempt was not retained')
        reject('failed_attempt_retry',lambda:draw(ffp))
        checks.append('failure_preserves_unsealed_directory_and_ledger')
    return {'status':'passed_pure_synthetic_D668_sampler_QA','checks':checks,'rejected_cases':rejected,
            'real_study_inputs_read':False,'real_sample_drawn':False,'real_packets_created':False,
            'synthetic_frame':{'U':4924,'R':1531,'D':3393,'n':668},'runtime':runtime(),
            'code_dependencies_sha256':{'sample_helpers':sha(helper),'v600_sampler':sha(old)},
            'limitations':['Hash binding is not semantic source verification or a certificate of exposure/AI independence.',
                           'Real freeze, material contents and reviewer instructions have not been semantically reviewed by this synthetic QA.',
                           'Incomplete release directories are unusable without their final valid seal; no recovery/redraw is implemented.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--inspect',action='store_true');mode.add_argument('--draw',action='store_true');mode.add_argument('--self-test',action='store_true')
    parser.add_argument('--freeze',type=Path);parser.add_argument('--qa-output',type=Path)
    args=parser.parse_args()
    if args.self_test:
        require(args.freeze is None,'Synthetic test accepts no study freeze')
        out=self_test();out['sampler_sha256']=sha(Path(__file__).read_bytes())
        if args.qa_output:
            require(args.qa_output.is_absolute(),'Absolute QA output required');exclusive(args.qa_output,encode(out))
    else:
        require(args.freeze is not None and args.qa_output is None,'Explicit --freeze and no --qa-output required')
        if args.inspect:
            snap=load_snapshot(args.freeze,False);out=metadata_preflight(snap)['summary'];unchanged(snap)
        else:out=draw(args.freeze)
    print(json.dumps(out,ensure_ascii=False))


if __name__ == '__main__':
    main()
