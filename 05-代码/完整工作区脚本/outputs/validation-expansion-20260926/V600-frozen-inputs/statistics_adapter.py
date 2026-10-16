"""Bind complete labels to exact source, corpus, context and metadata versions.

This adapter does not code units or approve scientific validity. The inspect CLI
checks real source files without generating labels or departmental results.
"""
from pathlib import Path
from copy import deepcopy
from datetime import date
import hashlib
import json
from policy_statistics import validate, DIMENSIONS

VERSION = 'statistics-input-adapter-v7-candidate'

class InputMismatch(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise InputMismatch(message)

def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()

def digest_json(value):
    return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                  separators=(',', ':'), allow_nan=False).encode())

def file_hash(path):
    return digest_bytes(Path(path).read_bytes())

def unique_index(rows, field):
    out = {}
    for row in rows:
        value = row.get(field)
        require(isinstance(value, str) and bool(value), f'Missing {field}')
        require(value not in out, f'Duplicate {field}: {value}')
        out[value] = row
    return out

def prepare(corpus_path, metadata_path, classification_path):
    """Read all inputs, verify provenance bytes, join by explicit original stem."""
    paths = {'corpus': Path(corpus_path), 'metadata': Path(metadata_path),
             'classification': Path(classification_path)}
    raw = {k: p.read_bytes() for k, p in paths.items()}
    corpus = [json.loads(line) for line in raw['corpus'].decode().splitlines() if line.strip()]
    metadata = json.loads(raw['metadata'])
    classification = json.loads(raw['classification'])
    unique_index(corpus, 'review_id')
    meta = unique_index(metadata, 'original_file')
    frozen = unique_index(classification['rows'], 'original_file')
    require(set(meta) == set(frozen), 'Metadata/classification file sets differ')
    bystem = {}
    documents = []
    locked = ('analysis_group', 'policy_series', 'joint_publication', 'annual_series', 'publishers')
    for name, m in meta.items():
        f = frozen[name]
        require(all(m.get(k) == f.get(k) for k in locked), f'Classification changed: {name}')
        stem = Path(name).stem
        require(stem not in bystem, f'Ambiguous original stem: {stem}')
        bystem[stem] = m
        require(m['analysis_group'] in {'NMPA','NHSA','NHC','GOV'}, f'Unknown group: {name}')
        require(type(m['joint_publication']) is bool, f'Unknown joint status: {name}')
        require(type(m['annual_series']) is bool, f'Unknown series status: {name}')
        for key in ('publication_date','publication_date_upper_bound','effective_date','cutoff'):
            value = m.get(key)
            if value is not None:
                try: date.fromisoformat(value)
                except (TypeError, ValueError): raise InputMismatch(f'Invalid {key}: {name}')
        require(m.get('cutoff'), f'Missing cutoff: {name}')
        require(not m.get('publication_date') or m['publication_date'] <= m['cutoff'],
                f'Post-cutoff publication: {name}')
        documents.append(dict(id=stem, original_file=name, group=m['analysis_group'],
                              series=m['policy_series'], joint=m['joint_publication'],
                              annual_series=m['annual_series'], publishers=m['publishers'],
                              publication_date=m.get('publication_date'),
                              publication_date_upper_bound=m.get('publication_date_upper_bound'),
                              publication_date_bound_basis=m.get('publication_date_bound_basis'),
                              effective_date=m.get('effective_date'), cutoff=m['cutoff']))
    checked_files = {}
    def check_source(path, expected):
        require(isinstance(path,str) and bool(path), 'Missing source path')
        require(isinstance(expected,str) and len(expected)==64, f'Missing hash: {path}')
        if path not in checked_files:
            require(Path(path).is_file(), f'Source missing: {path}')
            checked_files[path] = file_hash(path)
        require(checked_files[path] == expected, f'Source hash mismatch: {path}')
    for m in metadata:
        if m.get('metadata_evidence_source'):
            check_source(m['metadata_evidence_source'], m.get('metadata_evidence_sha256'))
        for extra in m.get('additional_metadata_evidence', []):
            check_source(extra.get('source'), extra.get('sha256'))
    candidate_manifests = {}
    units, excluded, stems = [], [], set()
    for r in corpus:
        stem = r.get('original_file_stem')
        require(stem in bystem, f'Unmapped corpus file: {stem}')
        stems.add(stem)
        m = bystem[stem]
        require(r.get('source_sha256') == m.get('source_sha256'), f'Metadata/source mismatch: {stem}')
        for path_key, hash_key in [('source','source_sha256'),('candidate_file','candidate_sha256'),
                                   ('unit_source','unit_source_sha256')]:
            check_source(r.get(path_key), r.get(hash_key))
        candidate_path = r['candidate_file']
        if candidate_path not in candidate_manifests:
            try:
                manifest = json.loads(Path(candidate_path).read_text())
            except (ValueError, UnicodeError):
                raise InputMismatch(f'Invalid candidate manifest: {candidate_path}')
            require(isinstance(manifest,dict), 'Candidate manifest must be an object')
            sources = {}
            entries = [dict(path=manifest.get('source'),sha256=manifest.get('source_sha256'))]
            require(isinstance(manifest.get('additional_sources',[]),list), 'Additional sources must be a list')
            entries.extend(manifest.get('additional_sources',[]))
            for entry in entries:
                require(isinstance(entry,dict), 'Invalid source manifest entry')
                path, sha = entry.get('path'), entry.get('sha256')
                check_source(path, sha)
                require(path not in sources or sources[path]==sha, 'Conflicting source hashes')
                sources[path] = sha
            candidate_manifests[candidate_path] = (manifest, sources)
        manifest, sources = candidate_manifests[candidate_path]
        target_doc = next(d for d in documents if d['id']==stem)
        if 'component_versions' in manifest:
            versions = manifest['component_versions']
            require(isinstance(versions,list), 'Component versions must be a list')
            seen_versions = set()
            for v in versions:
                require(isinstance(v,dict) and isinstance(v.get('series'),str) and v['series'], 'Invalid component metadata')
                require(type(v.get('year')) is int and 1900<=v['year']<=2100, 'Invalid component metadata year')
                key = (v['series'],v['year'])
                require(key not in seen_versions, 'Duplicate component metadata');seen_versions.add(key)
                require(type(v.get('annual_series')) is bool, 'Component annual status required')
                require(isinstance(v.get('source_basis'),str) and v['source_basis'], 'Component source basis required')
                evidence = v.get('evidence_sources')
                require(isinstance(evidence,list) and evidence, 'Component source files required')
                for e in evidence:
                    require(isinstance(e,dict), 'Invalid component evidence')
                    check_source(e.get('path'),e.get('sha256'))
                for field in ('publication_date','publication_date_upper_bound'):
                    value = v.get(field)
                    if value is not None:
                        try: date.fromisoformat(value)
                        except (TypeError,ValueError): raise InputMismatch('Invalid component publication date')
                        require(value<=m['cutoff'], 'Post-cutoff component publication')
                if v.get('annual_series'):
                    require(v.get('publication_date') or v.get('publication_date_upper_bound'), 'Component publication date missing')
                if v.get('publication_date_upper_bound'):
                    require(v.get('publication_date_bound_basis'), 'Component bound evidence required')
                    require(not v.get('publication_date') or v['publication_date']<=v['publication_date_upper_bound'], 'Conflicting component dates')
            require('component_versions' not in target_doc or target_doc['component_versions']==versions, 'Conflicting component versions')
            target_doc['component_versions'] = deepcopy(versions)
        require(manifest.get('source')==r['source'] and manifest.get('source_sha256')==r['source_sha256'],
                'Candidate primary source mismatch')
        require(sources.get(r['unit_source'])==r['unit_source_sha256'], 'Unit source absent from candidate manifest')
        require(type(r.get('count_as_analysis_unit')) is bool, f'Unresolved inclusion: {r["review_id"]}')
        require(isinstance(r.get('unit_text'),str) and r['unit_text'].strip(), 'Empty unit text')
        require(isinstance(r.get('unit_type'),str) and r['unit_type'], 'Missing unit type')
        require(isinstance(r.get('pages'),list), 'Missing source page list')
        component = {}
        if r.get('component_series') is not None or r.get('component_year') is not None:
            require(isinstance(r.get('component_series'),str) and r['component_series'], 'Missing component series')
            require(type(r.get('component_year')) is int and 1900<=r['component_year']<=2100, 'Invalid component year')
            original = [u for u in manifest.get('unit_candidates',[]) if u.get('id')==r.get('unit_id')]
            require(len(original)==1, 'Component unit missing from source manifest')
            require(all(original[0].get(k)==r[k] for k in ('component_series','component_year')), 'Component provenance mismatch')
            component = {k:r[k] for k in ('component_series','component_year')}
        if not r['count_as_analysis_unit']:
            excluded.append(dict(id=r['review_id'],document_id=stem,reason='context_only',
                                 record_sha256=digest_json(r), **component))
            continue
        require(r.get('content_role','unreviewed') in {'primary_policy_text','official_interpretation','unreviewed'}, 'Unknown content role')
        if r.get('content_role','unreviewed') != 'unreviewed':
            require(isinstance(r.get('content_role_basis'),str) and r['content_role_basis'], 'Content role evidence missing')
        units.append(dict(id=r['review_id'], document_id=stem, text=r['unit_text'],
                          unit_type=r['unit_type'], pages=r['pages'],
                          content_role=r.get('content_role','unreviewed'),
                          content_role_basis=r.get('content_role_basis'),
                          source=r['source'], source_sha256=r['source_sha256'],
                          unit_source=r['unit_source'], unit_source_sha256=r['unit_source_sha256'],
                          unit_text_sha256=digest_bytes(r['unit_text'].encode()),
                          record_sha256=digest_json(r), **component))
    require(stems == set(bystem), 'Corpus does not account for every mapped document')
    snapshot = {k: digest_bytes(v) for k, v in raw.items()}
    binding = dict(adapter_version=VERSION, verified_files_sha256=digest_json(checked_files), input_sha256=snapshot,
                   input_paths={k:str(p.resolve()) for k,p in paths.items()},
                   prepared_payload_sha256=digest_json(dict(documents=documents,units=units)),
                   classification_version=classification['version'],
                   analysis_unit_fingerprints={u['id']:u['record_sha256'] for u in units})
    blockers = []
    for u in units:
        if u.get('component_series'):
            d = next(d for d in documents if d['id']==u['document_id'])
            found = any(v['series']==u['component_series'] and v['year']==u['component_year'] for v in d.get('component_versions',[]))
            if not found:
                blockers.append(dict(document_id=u['document_id'],unit_id=u['id'],scenario='latest_annual_series',reason='component_version_metadata_missing',component_series=u['component_series'],component_year=u['component_year']))
    for d in documents:
        if d['annual_series'] and not (d['publication_date'] or d['publication_date_upper_bound']):
            blockers.append(dict(document_id=d['id'], scenario='latest_annual_series',reason='publication_date_unknown'))
        if not d['effective_date']:
            blockers.append(dict(document_id=d['id'], scenario='exclude_not_yet_effective',reason='effective_date_unknown'))
    return dict(version=VERSION, status='prepared_unlabelled_not_frozen',
                documents=documents, units=units, excluded_context=excluded,
                binding=binding, binding_sha256=digest_json(binding),
                verified_files=checked_files, metadata_gaps=blockers,
                scientific_validation=False, submission_ready=False)

def bind_labels(prepared, bundle, codebook_path, coder_path):
    """Join an entire single-version coding run. Never fill missing labels with 0.

    The caller must provide a coding bundle generated with the exact binding
    digest and one record per analysis unit. A bound result is not independent
    validation, corpus acceptance or permission to publish.
    """
    require(prepared.get('binding_sha256') == digest_json(prepared['binding']), 'Corrupted input binding')
    require(prepared['binding'].get('prepared_payload_sha256') == digest_json(dict(documents=prepared['documents'],units=prepared['units'])), 'Prepared dataset changed')
    for name,path in prepared['binding']['input_paths'].items():
        require(file_hash(path)==prepared['binding']['input_sha256'][name], f'Input changed after preparation: {name}')
    require(prepared['binding'].get('verified_files_sha256')==digest_json(prepared['verified_files']), 'Verified-source manifest changed')
    for path,expected in prepared['verified_files'].items():
        require(file_hash(path)==expected, f'Source changed after preparation: {path}')
    require(bundle.get('binding_sha256') == prepared['binding_sha256'], 'Coding/corpus version mismatch')
    require(bundle.get('codebook_sha256') == file_hash(codebook_path), 'Codebook version mismatch')
    require(bundle.get('coder_sha256') == file_hash(coder_path), 'Coder version mismatch')
    require(isinstance(bundle.get('method'), str) and bundle['method'], 'Coding method missing')
    require(isinstance(bundle.get('run_id'), str) and bundle['run_id'], 'Coding run ID missing')
    labels = unique_index(bundle['rows'], 'id')
    units = deepcopy(prepared['units'])
    require(set(labels) == {u['id'] for u in units}, 'Missing, extra or context-only coding records')
    for u in units:
        row = labels[u['id']]
        require(row.get('record_sha256') == u['record_sha256'], f'Stale text/context: {u["id"]}')
        require(row.get('unit_text_sha256') == u['unit_text_sha256'], f'Stale text: {u["id"]}')
        values = row.get('labels')
        require(isinstance(values,dict) and set(values)==set(DIMENSIONS), f'Invalid dimensions: {u["id"]}')
        require(all(type(v) is int and v in (0,1) for v in values.values()), f'Invalid label: {u["id"]}')
        kinds = row.get('fairness_subtypes')
        require(isinstance(kinds,list) and all(isinstance(x,str) for x in kinds), 'Missing F subtypes')
        require(len(kinds)==len(set(kinds)) and set(kinds)<= {'access','affordability','clinical_management','dimension_information'}, 'Invalid F subtype')
        require(bool(kinds)==bool(values['F']), 'F label/subtype contradiction')
        u['labels'] = deepcopy(values)
        u['fairness_subtypes'] = list(kinds)
        # Rule-based positive labels must have verifiable spans, not a bare label.
        if bundle['method']=='rule_based':
            evidence=row.get('evidence')
            require(isinstance(evidence,list), 'Missing rule evidence')
            found=set();found_f_subtypes=set()
            for e in evidence:
                require(e.get('dimension') in DIMENSIONS, 'Unknown evidence dimension')
                start,end=e.get('start'),e.get('end')
                require(type(start) is int and type(end) is int and 0<=start<end<=len(u['text']), 'Invalid evidence offset')
                require(u['text'][start:end]==e.get('text'), 'Evidence span/text mismatch')
                require(isinstance(e.get('rule'),str) and e['rule'], 'Missing rule ID')
                found.add(e['dimension'])
                if e['dimension']=='F':
                    require(e.get('subtype') in {'access','affordability','clinical_management','dimension_information'}, 'Missing evidence F subtype')
                    found_f_subtypes.add(e['subtype'])
            require(found=={k for k,v in values.items() if v}, 'Rule evidence/label mismatch')
            require(found_f_subtypes==set(kinds), 'Rule evidence/F subtype mismatch')
        # Explicit quality-risk rules preserve quality-only and mixed safety bases.
        skinds = row.get('safety_subtypes')
        if bundle['method']=='rule_based':
            quality_rules = {'S07', 'risk_stop_quality_condition'}
            for e in row['evidence']:
                if e['dimension']=='S' and e.get('safety_basis') is not None:
                    expected='quality_safety' if e['rule'] in quality_rules else 'other_safety'
                    require(e['safety_basis']==expected, 'Unexpected safety basis for rule')
            derived = sorted({'quality_safety' if e['rule'] in quality_rules else 'other_safety'
                              for e in row['evidence'] if e['dimension']=='S'})
            require(skinds is None or skinds==derived, 'Rule evidence/S subtype mismatch')
            skinds = derived
        if skinds is not None:
            require(isinstance(skinds,list) and all(isinstance(x,str) for x in skinds), 'Invalid S subtypes')
            require(len(skinds)==len(set(skinds)) and set(skinds)<={'quality_safety','other_safety'}, 'Invalid S subtype')
            require(bool(skinds)==bool(values['S']), 'S label/subtype contradiction')
            u['safety_subtypes'] = list(skinds)
        u['coding_record'] = deepcopy(row)
    documents=deepcopy(prepared['documents'])
    validate(documents, units)
    return dict(documents=documents,units=units,provenance=dict(
        binding_sha256=prepared['binding_sha256'],input_sha256=prepared['binding']['input_sha256'],
        codebook_sha256=bundle['codebook_sha256'],coder_sha256=bundle['coder_sha256'],
        coding_bundle_sha256=digest_json(bundle),run_id=bundle['run_id'],method=bundle['method']),
        status='inputs_bound_not_scientific_approval',submission_ready=False)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args();w=args.workspace
    result=prepare(w/'统一文本复核包.jsonl',w/'55条部门与系列映射-核验中.json',w/'部门归属与年度系列-冻结v1.json')
    (w/'统计输入接入准备.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],documents=len(result['documents']),
        units=len(result['units']),context=len(result['excluded_context']),
        verified_files=len(result['verified_files']),metadata_gaps=len(result['metadata_gaps']),
        binding_sha256=result['binding_sha256']),ensure_ascii=False))
