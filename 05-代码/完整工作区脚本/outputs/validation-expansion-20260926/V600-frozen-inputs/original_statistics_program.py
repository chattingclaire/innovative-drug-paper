"""Versioned descriptive estimators; no coding, imputation or corpus approval.

Input documents: id, group, series. Input units: id, document_id, labels.
Labels must contain exactly S/E/Ec/I/F, with integer 0/1 values.
Optional weights apply to both coverage and dimension frequencies.
All proportions are fractions (0..1), never rounded before comparisons.
"""
from collections import defaultdict
from fractions import Fraction
from copy import deepcopy
from datetime import date

DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
VERSION = 'descriptive-estimators-v7'


def validate(documents, units):
    docs = {d['id']: d for d in documents}
    assert len(docs) == len(documents), 'Duplicate document ID'
    assert len({u['id'] for u in units}) == len(units), 'Duplicate unit ID'
    for d in documents:
        assert all(isinstance(d[k], str) and d[k] for k in ('id', 'group', 'series'))
    for u in units:
        assert u['document_id'] in docs, 'Unknown document'
        if 'component_series' in u or 'component_year' in u:
            assert isinstance(u.get('component_series'), str) and u['component_series'], 'Invalid component series'
            assert type(u.get('component_year')) is int and 1900 <= u['component_year'] <= 2100, 'Invalid component year'
        assert set(u['labels']) == set(DIMENSIONS), 'Missing or extra label'
        assert all(type(v) is int and v in (0, 1) for v in u['labels'].values()), 'Nonbinary label'
    return docs


def _ratio(n, d):
    return n / d if d else None


def _mean(values):
    values = list(values)
    return sum(values, Fraction()) / len(values) if values else None


def _leaders(shares):
    if shares['S'] is None:
        return []
    best = max(shares.values())
    return [d for d in DIMENSIONS if shares[d] == best]


def summary(units, weights=None):
    """Separate unique covered units from multi-label hit occurrences."""
    weights = weights if weights is not None else {u['id']: Fraction(1) for u in units}
    assert all(u['id'] in weights for u in units), 'Missing unit weight'
    ws = {u['id']: Fraction(weights[u['id']]) for u in units}
    assert all(w > 0 for w in ws.values()), 'Weights must be positive'
    total = sum(ws.values(), Fraction())
    covered = sum((ws[u['id']] for u in units if any(u['labels'].values())), Fraction())
    hits = {d: sum((ws[u['id']] * u['labels'][d] for u in units), Fraction()) for d in DIMENSIONS}
    hit_total = sum(hits.values(), Fraction())
    shares = {d: _ratio(hits[d], hit_total) for d in DIMENSIONS}
    return dict(raw_units=len(units), weighted_units=total, covered_units=covered,
                coverage=_ratio(covered, total), dimension_hits=hits, hit_total=hit_total,
                hit_share=shares, unit_rate={d: _ratio(hits[d], total) for d in DIMENSIONS},
                leaders=_leaders(shares))


def estimate(documents, units, weights=None):
    """Compute pooled, equal-file and equal-series estimators for every group.

    Zero-hit files are excluded only from hit-share means; their unit rates
    and coverage remain visible. Files with no retained units have undefined
    rates. Every denominator and excluded file count is reported.
    """
    validate(documents, units)
    bydoc = defaultdict(list)
    for u in units:
        bydoc[u['document_id']].append(u)
    per_file = {d['id']: summary(bydoc[d['id']], weights) for d in documents}
    groups = {}
    for group in sorted({d['group'] for d in documents}):
        selected = [d for d in documents if d['group'] == group]
        ids = {d['id'] for d in selected}
        pooled = summary([u for u in units if u['document_id'] in ids], weights)
        valid_shares = [per_file[d['id']] for d in selected if per_file[d['id']]['hit_total']]
        valid_rates = [per_file[d['id']] for d in selected if per_file[d['id']]['weighted_units']]
        file_share = {k: _mean(s['hit_share'][k] for s in valid_shares) for k in DIMENSIONS}
        series_shares = {}
        # Preserve original files for file-equal/LOO; within each series,
        # average the portions belonging to that series in each source file.
        portions = defaultdict(list)
        for d in selected:
            if not bydoc[d['id']]:
                portions[(d['id'], d['series'])] = []
            for u in bydoc[d['id']]:
                portions[(d['id'], u.get('component_series', d['series']))].append(u)
        portion_summaries = {key: summary(value, weights) for key,value in portions.items()}
        for series in sorted({key[1] for key in portions}):
            rows = [row for (file_id, own_series), row in portion_summaries.items()
                    if own_series == series and row['hit_total']]
            series_shares[series] = {k: _mean(s['hit_share'][k] for s in rows) for k in DIMENSIONS}
        valid_series = [s for s in series_shares.values() if s['S'] is not None]
        series_share = {k: _mean(s[k] for s in valid_series) for k in DIMENSIONS}
        groups[group] = dict(
            files=len(selected), pooled=pooled,
            zero_hit_files=sum(not per_file[d['id']]['hit_total'] for d in selected),
            empty_files=sum(not per_file[d['id']]['weighted_units'] for d in selected),
            file_equal=dict(hit_share=file_share, leaders=_leaders(file_share),
                            eligible_share_files=len(valid_shares), eligible_rate_files=len(valid_rates),
                            unit_rate={k: _mean(s['unit_rate'][k] for s in valid_rates) for k in DIMENSIONS},
                            coverage=_mean(s['coverage'] for s in valid_rates)),
            series_equal=dict(hit_share=series_share, leaders=_leaders(series_share),
                              eligible_series=len(valid_series), total_series=len(series_shares),
                              series_file_mean_shares=series_shares,
                              source_file_series_portions=[dict(document_id=k[0],series=k[1],summary=v) for k,v in sorted(portion_summaries.items())]))
    return dict(version=VERSION, groups=groups, per_file=per_file)


def leave_one_file_out(documents, units):
    """All groups, unweighted pooled hit shares; ties never imply a sole leader."""
    validate(documents, units)
    result = {}
    for group in sorted({d['group'] for d in documents}):
        ds = [d for d in documents if d['group'] == group]
        ids = {d['id'] for d in ds}
        us = [u for u in units if u['document_id'] in ids]
        baseline = summary(us)
        if len(ds) < 2:
            result[group] = dict(status='insufficient_files', files=len(ds), baseline=baseline)
            continue
        trials = [dict(removed=d['id'], result=summary([u for u in us if u['document_id'] != d['id']])) for d in ds]
        valid = [t for t in trials if t['result']['hit_total']]
        sole = baseline['leaders'][0] if len(baseline['leaders']) == 1 else None
        margins = []
        if sole:
            for t in valid:
                s = t['result']['hit_share']
                margins.append(s[sole] - max(s[k] for k in DIMENSIONS if k != sole))
        result[group] = dict(
            status='complete' if len(valid) == len(trials) else 'undefined_trials',
            files=len(ds), baseline=baseline, trials=trials, valid_trials=len(valid),
            share_ranges={k: [min(t['result']['hit_share'][k] for t in valid), max(t['result']['hit_share'][k] for t in valid)] if valid else None for k in DIMENSIONS},
            baseline_sole_leader=sole,
            sole_leader_preserved=bool(sole and len(valid) == len(trials) and all(t['result']['leaders'] == [sole] for t in valid)),
            minimum_lead_margin=min(margins) if margins else None)
    return result


def exact_duplicate_weights(documents, units, duplicate_key):
    """1/k across distinct files in the same group and series.

    Call only after layout duplicates have been removed by reviewed decisions.
    Legitimate within-file repeats remain and never inflate k.
    """
    docs = validate(documents, units)
    files_by_key = defaultdict(set)
    keys = {}
    for u in units:
        d = docs[u['document_id']]
        key = (d['group'], u.get('component_series', d['series']), duplicate_key(u['text']))
        assert key[2], 'Empty comparison key'
        keys[u['id']] = key
        files_by_key[key].add(d['id'])
    return {u['id']: Fraction(1, len(files_by_key[keys[u['id']]])) for u in units}


def sensitivity_input(documents, units, mode, cutoff=None):
    """Return a copied dataset plus a complete exclusion/change ledger.

    Required metadata is never inferred from filenames or text. Unknown
    effective dates stay visible, and make that scenario incomplete.
    Latest-version selection uses verified publication dates, not file order.
    """
    validate(documents, units)
    ds, us = deepcopy(documents), deepcopy(units)
    excluded_docs, excluded_units, changed_labels, unresolved = [], [], [], []
    selection_evidence = []
    if mode == 'exclude_joint':
        for d in ds:
            assert type(d.get('joint')) is bool, 'Joint-publication status required'
            if d['joint']:
                excluded_docs.append(d['id'])
    elif mode == 'exclude_interpretation':
        for u in us:
            role = u.get('content_role','unreviewed')
            assert role in {'primary_policy_text','official_interpretation','unreviewed'}, 'Unknown content role'
            if role == 'unreviewed':
                unresolved.append(dict(unit_id=u['id'], reason='content_role_unreviewed'))
            else:
                assert isinstance(u.get('content_role_basis'),str) and u['content_role_basis'], 'Content role evidence required'
                if role == 'official_interpretation':
                    excluded_units.append(u['id'])
        removed = set(excluded_units)
        for d in ds:
            own = [u for u in us if u['document_id'] == d['id']]
            if own and all(u['id'] in removed for u in own):
                excluded_docs.append(d['id'])
    elif mode == 'exclude_figures':
        for u in us:
            assert isinstance(u.get('unit_type'), str) and u['unit_type'], 'Unit type required'
            if u['unit_type'] == 'figure_transcription':
                excluded_units.append(u['id'])
    elif mode in {'fairness_without_management_only', 'fairness_without_information_only', 'fairness_access_affordability_only'}:
        removed_kinds = {'fairness_without_management_only': {'clinical_management'},
                         'fairness_without_information_only': {'dimension_information'},
                         'fairness_access_affordability_only': {'clinical_management', 'dimension_information'}}[mode]
        for u in us:
            if not u['labels']['F']:
                continue
            kinds = u.get('fairness_subtypes')
            assert isinstance(kinds, list) and kinds, 'Every positive F needs reviewed subtypes'
            assert len(kinds) == len(set(kinds)), 'Duplicate subtype'
            assert set(kinds) <= {'access', 'affordability', 'clinical_management', 'dimension_information'}, 'Unknown F subtype'
            if set(kinds) <= removed_kinds:
                u['labels']['F'] = 0
                changed_labels.append(dict(unit_id=u['id'], dimension='F', before=1, after=0))
    elif mode == 'innovation_without_qualification_only':
        for u in us:
            if not u['labels']['I']:
                continue
            # Bound coding_record retains the exact source trace from the coder.
            kinds = u.get('innovation_subtypes', u.get('coding_record', {}).get('innovation_subtypes'))
            assert isinstance(kinds, list) and kinds, 'Every positive I needs explicit subtypes'
            assert len(kinds) == len(set(kinds)), 'Duplicate I subtype'
            assert set(kinds) <= {'attribute', 'research_support', 'qualification_advantage'}, 'Unknown I subtype'
            record = u.get('coding_record')
            if record is not None:
                assert record.get('innovation_subtype_status') == 'complete', 'Unresolved I attribution'
                assert set(kinds) == {e['subtype'] for e in record['evidence'] if e['dimension']=='I'}, 'I subtype/evidence mismatch'
            if set(kinds) == {'qualification_advantage'}:
                u['labels']['I'] = 0
                changed_labels.append(dict(unit_id=u['id'], dimension='I', before=1, after=0))
    elif mode == 'safety_without_quality_only':
        for u in us:
            if not u['labels']['S']:
                continue
            kinds = u.get('safety_subtypes')
            assert isinstance(kinds, list) and kinds, 'Every positive S needs reviewed subtypes'
            assert len(kinds) == len(set(kinds)), 'Duplicate S subtype'
            assert set(kinds) <= {'quality_safety', 'other_safety'}, 'Unknown S subtype'
            if set(kinds) == {'quality_safety'}:
                u['labels']['S'] = 0
                changed_labels.append(dict(unit_id=u['id'], dimension='S', before=1, after=0))
    elif mode == 'exclude_not_yet_effective':
        assert cutoff, 'Explicit cutoff required'
        end = date.fromisoformat(cutoff)
        for d in ds:
            if d.get('effective_date') is None:
                unresolved.append(dict(document_id=d['id'], reason='effective_date_unknown'))
            elif date.fromisoformat(d['effective_date']) > end:
                excluded_docs.append(d['id'])
    elif mode == 'latest_annual_series':
        assert cutoff, 'Explicit cutoff required'
        end = date.fromisoformat(cutoff)
        grouped = defaultdict(list)
        portions = {}
        for d in ds:
            own = [u for u in us if u['document_id'] == d['id']]
            # Explicit component metadata, never infer publication from the
            # component year or silently inherit the parent publication date.
            component_meta = {}
            for m in d.get('component_versions', []):
                assert isinstance(m.get('series'),str) and m['series'], 'Component series required'
                assert type(m.get('year')) is int, 'Component year required'
                key = (m['series'], m['year'])
                assert key not in component_meta, 'Duplicate component metadata'
                assert m.get('source_basis'), 'Component source evidence required'
                component_meta[key] = m
            ids_by_part = defaultdict(list)
            for u in own:
                key = (u['component_series'],u['component_year']) if 'component_series' in u else None
                ids_by_part[key].append(u['id'])
            if not own:
                ids_by_part[None] = []
            for key, unit_ids in ids_by_part.items():
                if key is None:
                    m = d
                    series = d['series']
                else:
                    assert key in component_meta, 'Mixed-file component-level review metadata required'
                    m = component_meta[key]
                    series = key[0]
                assert type(m.get('annual_series')) is bool, 'Annual-series flag required'
                part_id = (d['id'], key)
                portions[part_id] = dict(unit_ids=unit_ids, retained=True)
                if not m['annual_series']:
                    continue
                published = date.fromisoformat(m['publication_date']) if m.get('publication_date') else None
                upper = date.fromisoformat(m['publication_date_upper_bound']) if m.get('publication_date_upper_bound') else None
                assert published or upper, 'Annual-series publication date or sourced upper bound required'
                if upper:
                    assert m.get('publication_date_bound_basis'), 'Publication upper bound needs evidence basis'
                    assert not published or published <= upper, 'Publication date exceeds upper bound'
                assert (published or upper) <= end, 'Input includes unverified/post-cutoff publication'
                grouped[(d['group'], series)].append((published, upper, part_id, m))
        for (group, series), versions in grouped.items():
            if len(versions) == 1:
                selected = versions[0][2]
            else:
                exact = [v for v in versions if v[0] is not None]
                if not exact:
                    raise ValueError('Upper bounds alone cannot order multiple annual versions')
                latest = max(v[0] for v in exact)
                if sum(v[0] == latest for v in exact) > 1:
                    raise ValueError('Multiple latest versions: resolve source identity before analysis')
                if any(v[0] is None and v[1] >= latest for v in versions):
                    raise ValueError('Unknown publication date could tie or exceed latest exact date')
                selected = next(v[2] for v in exact if v[0] == latest)
            for published, upper, part_id, m in versions:
                keep = part_id == selected
                portions[part_id]['retained'] = keep
                if not keep:
                    excluded_units.extend(portions[part_id]['unit_ids'])
                selection_evidence.append(dict(group=group, series=series, document_id=part_id[0],
                    component_year=part_id[1][1] if part_id[1] else None,
                    source_basis=m.get('source_basis'),
                    publication_date=published.isoformat() if published else None,
                    publication_date_upper_bound=upper.isoformat() if upper else None,
                    retained=keep, basis='exact_date' if published else 'sourced_upper_bound',
                    latest_selected_document=selected[0],
                    latest_selected_component_year=selected[1][1] if selected[1] else None,
                    unit_ids=portions[part_id]['unit_ids']))
        # A file disappears only when every one of its portions is excluded.
        # A retained annex can therefore survive exclusion of its parent body.
        for d in ds:
            if all(not p['retained'] for key,p in portions.items() if key[0] == d['id']):
                excluded_docs.append(d['id'])

    else:
        raise ValueError(f'Unknown sensitivity mode: {mode}')
    excluded_doc_set = set(excluded_docs)
    excluded_unit_set = set(excluded_units)
    excluded_units = [u['id'] for u in us if u['document_id'] in excluded_doc_set or u['id'] in excluded_unit_set]
    ds = [d for d in ds if d['id'] not in excluded_doc_set]
    us = [u for u in us if u['id'] not in set(excluded_units)]
    validate(ds, us)
    return dict(documents=ds, units=us, ledger=dict(
        mode=mode, cutoff=cutoff, status='incomplete_metadata' if unresolved else 'complete',
        excluded_documents=sorted(excluded_docs), excluded_units=excluded_units,
        changed_labels=changed_labels, unresolved=unresolved, selection_evidence=selection_evidence,
        original_documents=len(documents), retained_documents=len(ds),
        original_units=len(units), retained_units=len(us)))
