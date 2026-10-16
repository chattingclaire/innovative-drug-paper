"""Register explicitly reported source-page/line exposure; no predictions or labels.

Read-only source matching. CLI output is exclusive and contains IDs/provenance,
not new reference labels. It does not modify any corpus or select a sample.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata
from pypdf import PdfReader


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).strip('。.!！?？;；')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-audit', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--register', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Never overwrite an audit')
    snapshots = {}
    def read(path):
        path = path.resolve()
        raw = path.read_bytes()
        if str(path) in snapshots:
            require(snapshots[str(path)] == sha(raw), 'Input changed during audit')
        snapshots[str(path)] = sha(raw)
        return raw
    base = json.loads(read(args.base_audit))
    corpus_bytes = read(args.corpus)
    require(base['input_hashes'].get(str(args.corpus.resolve())) == sha(corpus_bytes), 'Corpus differs from base audit')
    rows = [json.loads(line) for line in corpus_bytes.splitlines() if line.strip()]
    units = {r['review_id']: r for r in rows if r['count_as_analysis_unit'] is True}
    require(len(units) == base['analysis_units'], 'Analysis IDs/count changed')
    baseline_ids = set(base['variants']['also_exclude_visible_context_candidates']['candidate_ids'])
    require(baseline_ids <= units.keys(), 'Base candidate IDs missing')
    normalized = {key: norm(row['unit_text']) for key, row in units.items()}
    direct = defaultdict(list)
    bodies = defaultdict(list)
    source_summaries = []
    for register_path in args.register:
        register = json.loads(read(register_path))
        require(isinstance(register.get('pdf_reads', []), list) and isinstance(register.get('text_reads', []), list), 'Invalid source register')
        if 'analysis_unit_reads' in register:
            entries = register['analysis_unit_reads']
            require(isinstance(entries, list), 'Explicit unit reads must be a list')
            source_adapter = Path(register['source_adapter'])
            require(sha(read(source_adapter)) == register['source_adapter_sha256'], 'Unit-read adapter source changed')
            for entry in entries:
                key = entry['review_id']
                require(key in units and sha(units[key]['unit_text'].encode()) == entry['unit_text_sha256'], 'Registered explicit unit differs from corpus')
                direct[key].append({'basis': 'explicit_actual_coordinator_text_read',
                                    'source_adapter': str(source_adapter),
                                    'source_adapter_sha256': register['source_adapter_sha256'],
                                    'register': str(register_path.resolve())})
            source_summaries.append({'kind': 'explicit_unit_reads', 'count': len(entries), 'register': str(register_path.resolve())})
        for entry in register.get('pdf_reads', []):
            source = Path(entry['source'])
            raw = read(source)
            require(sha(raw) == entry['source_sha256'], 'Registered PDF source hash mismatch')
            pages = entry['physical_pages']
            require(isinstance(pages, list) and pages and all(type(p) is int and p > 0 for p in pages), 'Physical pages must be positive integers')
            require(len(pages) == len(set(pages)), 'Duplicate PDF page')
            pdf = PdfReader(BytesIO(raw))
            require(max(pages) <= len(pdf.pages), 'Page outside source PDF')
            page_origins = {}
            for page in pages:
                text = pdf.pages[page - 1].extract_text() or ''
                require(bool(norm(text)), 'Registered PDF page has no extractable text; explicit alternative needed')
                origin = {'source': str(source), 'source_sha256': sha(raw), 'physical_page': page,
                          'extracted_text_sha256': sha(text.encode()), 'register': str(register_path.resolve())}
                bodies[norm(text)].append(origin)
                page_origins[page] = origin
            mapped = []
            for key, row in units.items():
                if row.get('source_sha256') == sha(raw):
                    unit_pages = row.get('pages')
                    require(isinstance(unit_pages, list) and all(type(p) is int and p > 0 for p in unit_pages), 'Invalid frozen PDF page metadata')
                    overlap = set(unit_pages) & set(pages)
                    if overlap:
                        direct[key].append({'basis': 'source_hash_and_physical_page_overlap',
                                            'origins': [page_origins[p] for p in sorted(overlap)]})
                        mapped.append(key)
            source_summaries.append({'kind': 'pdf', 'source': str(source), 'sha256': sha(raw),
                                     'physical_pages': pages, 'mapped_analysis_unit_count': len(mapped)})
        for entry in register.get('text_reads', []):
            source = Path(entry['source'])
            raw = read(source)
            require(sha(raw) == entry['source_sha256'], 'Registered text source hash mismatch')
            lines = raw.decode().splitlines()
            indexes = entry['matching_lines']
            require(isinstance(indexes, list) and indexes and all(type(i) is int and 1 <= i <= len(lines) for i in indexes), 'Invalid text line index')
            require(len(indexes) == len(set(indexes)), 'Duplicate text line')
            for index in indexes:
                body = norm(lines[index - 1])
                if body:
                    bodies[body].append({'source': str(source), 'source_sha256': sha(raw), 'line': index,
                                         'text_sha256': sha(lines[index - 1].encode()), 'register': str(register_path.resolve())})
            # Units can span consecutive displayed lines. Permit only blank
            # intervening source lines; never bridge an unread nonempty line.
            blocks = []
            for index in sorted(indexes):
                if blocks and not any(line.strip() for line in lines[blocks[-1][-1]:index - 1]):
                    blocks[-1].append(index)
                else:
                    blocks.append([index])
            for block in blocks:
                if len(block) > 1:
                    raw_block = '\n'.join(lines[index - 1] for index in block)
                    body = norm(raw_block)
                    if body:
                        bodies[body].append({'source': str(source), 'source_sha256': sha(raw),
                                             'registered_line_block': block, 'text_sha256': sha(raw_block.encode()),
                                             'register': str(register_path.resolve())})
            source_summaries.append({'kind': 'text', 'source': str(source), 'sha256': sha(raw), 'lines': indexes})
    # Text inclusion also covers same text in other corpus sources. Page joins
    # conservatively exclude units crossing a read-page boundary in full.
    for key, text in normalized.items():
        for body, origins in bodies.items():
            if text and (text == body or (len(text) >= 20 and text in body)):
                direct[key].append({'basis': 'registered_display_text_contains_unit', 'origins': origins})
    exact_seeds = defaultdict(list)
    for key in direct:
        exact_seeds[normalized[key]].append(key)
    for key in baseline_ids - direct.keys():
        if normalized[key] in exact_seeds:
            direct[key].append({'basis': 'same_normalized_text_as_registered_visible_unit',
                                'seed_ids': sorted(exact_seeds[normalized[key]])})
    newly_direct = baseline_ids & direct.keys()
    remaining = baseline_ids - newly_direct
    grams = {key: {text[i:i + 5] for i in range(len(text) - 4)}
             for key, text in normalized.items() if key in remaining and len(text) >= 30}
    postings = defaultdict(set)
    for key, values in grams.items():
        for value in values:
            postings[value].add(key)
    seed_texts = defaultdict(list)
    for body, origins in bodies.items():
        seed_texts[body].append({'basis': 'registered_raw_source_body', 'origins': origins})
    for key in direct:
        seed_texts[normalized[key]].append({'basis': 'direct_visible_unit', 'seed_id': key})
    near = defaultdict(list)
    for body, origins in seed_texts.items():
        if len(body) < 30:
            continue
        values = {body[i:i + 5] for i in range(len(body) - 4)}
        matches = Counter(key for value in values for key in postings.get(value, ()))
        for key, overlap in matches.items():
            ratio = min(len(body), len(normalized[key])) / max(len(body), len(normalized[key]))
            dice = 2 * overlap / (len(values) + len(grams[key]))
            if ratio >= .75 and dice >= .85:
                near[key].append({'origins': origins, 'displayed_normalized_sha256': sha(body.encode()), 'dice': round(dice, 6)})
    eligible = remaining - near.keys()
    require(all(sha(Path(path).read_bytes()) == digest for path, digest in snapshots.items()), 'Inputs changed; no output')
    output = {
        'status': 'additional_source_exposure_audit_no_sample_no_predictions_no_reference_labels',
        'created_at': datetime.now(timezone.utc).isoformat(), 'base_candidate_N': len(baseline_ids),
        'registered_source_summaries': source_summaries,
        'all_registered_visible_analysis_units': len(direct),
        'new_direct_exclusions_n': len(newly_direct), 'new_near_exclusions_n': len(near), 'remaining_N': len(eligible),
        'new_direct_exclusions': {key: direct[key] for key in sorted(newly_direct)},
        'new_near_exclusions': dict(near), 'provisional_eligible_ids': sorted(eligible),
        'exclusions': sorted(set(units) - eligible), 'input_hashes': snapshots,
        'script_sha256': sha(Path(__file__).read_bytes()),
        'rules': {'normalization': 'NFKC, whitespace removed, leading and trailing characters in 。.!！?？;； stripped (same implementation as base audit)',
                  'page_matching': 'source_sha256 exact and any frozen physical-page overlap; complete crossing unit conservatively excluded',
                  'text_matching': 'equal normalized full body, or unit>=20 characters contained in registered source body; consecutive registered text lines also joined across blank lines only, never unread nonempty lines',
                  'near': 'one hop from registered raw source bodies and directly visible units; min30 characters, length ratio>=.75, char5gram Dice>=.85'},
        'limitations': ['Source page mapping relies on frozen physical-page metadata; source hashes do not verify that metadata.',
                       'This records reported additional reading, not every unknown historical exposure.',
                       'No candidate text, label or prediction is printed; no sample selected.',
                       'Final development and input changes require a final exposure register before freeze.'],
    }
    require(len(output['exclusions']) + len(eligible) == len(units), 'Exposure partition failed')
    with args.output.open('x') as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    print(json.dumps({k: output[k] for k in ('status', 'base_candidate_N', 'all_registered_visible_analysis_units',
                                           'new_direct_exclusions_n', 'new_near_exclusions_n', 'remaining_N')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
