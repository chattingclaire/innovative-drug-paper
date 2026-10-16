"""Descriptive M12/M13 diagnostics; inputs must be complete sealed, preregistered runs."""
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
CONDITIONS = ('R1', 'R2', 'R3', 'W', 'H')
PAIRS = (('R1', 'R2'), ('R1', 'R3'), ('R2', 'R3'), ('R1', 'W'), ('R1', 'H'))

def binary(run, dimension):
    result = run.get('semantic_result')
    if run.get('state') not in {'first_valid', 'simulated_first_valid'} or not result:
        return None
    value = result['labels'][dimension]
    return value if type(value) is int and value in (0, 1) else None

def pair_report(ids, a, b):
    report = {}
    for d in DIMENSIONS:
        cells = {'n00': 0, 'n01': 0, 'n10': 0, 'n11': 0}
        excluded, changed = [], []
        for uid in ids:
            x, y = binary(a[uid], d), binary(b[uid], d)
            if x is None or y is None:
                excluded.append(uid)
            else:
                cells[f'n{x}{y}'] += 1
                if x != y:
                    changed.append(uid)
        n = sum(cells.values())
        margins_a = [cells['n00'] + cells['n01'], cells['n10'] + cells['n11']]
        margins_b = [cells['n00'] + cells['n10'], cells['n01'] + cells['n11']]
        po = (cells['n00'] + cells['n11']) / n if n else None
        pe = sum(x * y for x, y in zip(margins_a, margins_b)) / n**2 if n else None
        kappa = (po - pe) / (1 - pe) if n and pe != 1 else None
        report[d] = {'planned_n': len(ids), 'scorable_n': n, **cells,
                     'margin_first_0_1': margins_a, 'margin_second_0_1': margins_b,
                     'po': po, 'kappa': kappa, 'kappa_na_reason': ('empty_common_binary_set' if not n else 'degenerate_margins') if kappa is None else None,
                     'changed_ids': changed, 'excluded_ids': excluded}
    full = [i for i in ids if all(binary(a[i], d) is not None and binary(b[i], d) is not None for d in DIMENSIONS)]
    report['full_vector'] = {'scorable_n': len(full), 'equal_n': sum(all(binary(a[i], d) == binary(b[i], d) for d in DIMENSIONS) for i in full)}
    return report

def report(ids, runs, *, simulation=False):
    if not ids:
        return {'state': 'not_executed', 'planned_ids': [], 'statistics': None, 'reason': 'diagnostic sample not frozen'}
    if len(set(ids)) != len(ids) or set(runs) != set(CONDITIONS) or any(set(runs[c]) != set(ids) for c in CONDITIONS):
        raise ValueError('require exactly all preregistered conditions and IDs, including failed/not-called rows')
    import re
    hashes = ('packet_binding_sha256', 'manual_sha256', 'neutral_request_sha256')
    for c in CONDITIONS:
        for i in ids:
            row = runs[c][i]
            if row.get('purpose') != c or row.get('simulation') is not simulation:
                raise ValueError('purpose/simulation provenance mismatch')
            if any(not isinstance(row.get(k), str) or not re.fullmatch('[a-f0-9]{64}', row[k]) for k in hashes):
                raise ValueError('missing real request/source/manual hash')
            if row['state'] in {'first_valid', 'simulated_first_valid'}:
                selected = [a for a in row.get('attempts', []) if a.get('selected')]
                if len(selected) != 1 or selected[0].get('outcome') != 'technical_valid' or not selected[0].get('independent_context_id'):
                    raise ValueError('valid result lacks sealed selected attempt/context provenance')
                if any(not isinstance(selected[0].get(k), str) or not re.fullmatch('[a-f0-9]{64}', selected[0][k]) for k in ('raw_response_sha256', 'wire_request_sha256', 'receipt_sha256')):
                    raise ValueError('valid result lacks sealed raw/wire/receipt hashes')
                if not simulation and (row['state'] != 'first_valid' or not row.get('actual_model_identity') or not row.get('model_evidence_source') or row.get('actual_attempts', 0) < 1):
                    raise ValueError('actual diagnostic result lacks provider execution evidence')
                if simulation and (row['state'] != 'simulated_first_valid' or row.get('actual_attempts') != 0):
                    raise ValueError('toy diagnostic cannot count actual attempts')
    for i in ids:
        if len({runs[c][i].get('packet_binding_sha256') for c in CONDITIONS}) != 1 or len({runs[c][i].get('manual_sha256') for c in CONDITIONS}) != 1:
            raise ValueError('diagnostic source/manual versions differ')
        if len({runs[c][i].get('neutral_request_sha256') for c in ('R1', 'R2', 'R3')}) != 1:
            raise ValueError('primary repeat requests are not byte-identical')
        primary = [runs[c][i] for c in ('R1', 'R2', 'R3') if runs[c][i].get('actual_attempts', 0) > 0 or runs[c][i].get('simulated_attempts', 0) > 0]
        if primary and (any(not r.get('expected_wire_request_sha256') for r in primary) or len({r['expected_wire_request_sha256'] for r in primary}) != 1):
            raise ValueError('primary repeat exact wire bodies differ or are unsealed')
        if not simulation:
            scheduled = [runs[c][i] for c in CONDITIONS if runs[c][i].get('actual_attempts', 0) > 0]
            if any(not r.get('scheduling') for r in scheduled):
                raise ValueError('actual diagnostic lacks order/batch provenance')
            for key in ('unit_sequence', 'batch_id', 'planned_order_sha256', 'batch_manifest_sha256'):
                if len({r['scheduling'][key] for r in scheduled}) > 1:
                    raise ValueError('diagnostic order/batch conditions differ')
            if len({r['scheduling']['run_id'] for r in scheduled}) != len(scheduled):
                raise ValueError('diagnostic run identities reused')
    contexts = set()
    for c in CONDITIONS:
        for i in ids:
            for a in runs[c][i].get('attempts', []):
                ctx = a.get('independent_context_id')
                if ctx:
                    if ctx in contexts:
                        raise ValueError('diagnostic context reused')
                    contexts.add(ctx)
    states = {}
    for c in CONDITIONS:
        states[c] = {i: {'state': runs[c][i]['state'], 'actual_attempts': runs[c][i]['actual_attempts'],
                         'null_dimensions': [d for d in DIMENSIONS if runs[c][i].get('semantic_result') and runs[c][i]['semantic_result']['labels'][d] is None],
                         'technical_invalid_returns': sum(a.get('outcome') == 'technical_invalid' for a in runs[c][i].get('attempts', [])),
                         'transport_failures': sum(a.get('outcome') == 'transport_failure' for a in runs[c][i].get('attempts', []))} for i in ids}
    if not simulation and sum(runs[c][i].get('actual_attempts', 0) for c in CONDITIONS for i in ids) == 0:
        return {'state': 'not_executed', 'planned_ids': ids, 'states': states, 'statistics': None, 'reason': 'zero actual model attempts'}
    paired = {f'{a}/{b}': pair_report(ids, runs[a], runs[b]) for a, b in PAIRS}
    common = [i for i in ids if all(binary(runs[c][i], d) is not None for c in CONDITIONS for d in DIMENSIONS)]
    q = {}
    for c in CONDITIONS:
        totals = {d: sum(binary(runs[c][i], d) for i in common) for d in DIMENSIONS}
        denominator = sum(totals.values())
        q[c] = {'common_n': len(common), 'T': totals, 'sum_five_T': denominator,
                'q': {d: totals[d] / denominator if denominator else None for d in DIMENSIONS}}
    qranges = {d: [min(q[c]['q'][d] for c in CONDITIONS), max(q[c]['q'][d] for c in CONDITIONS)] if all(q[c]['q'][d] is not None for c in CONDITIONS) else None for d in DIMENSIONS}
    tri = [i for i in ids if all(binary(runs[c][i], d) is not None for c in ('R1', 'R2', 'R3') for d in DIMENSIONS)]
    tri_changes = {d: [i for i in ids if all(binary(runs[c][i], d) is not None for c in ('R1', 'R2', 'R3')) and len({binary(runs[c][i], d) for c in ('R1', 'R2', 'R3')}) > 1] for d in DIMENSIONS}
    return {'state': 'constructed_toy_descriptive_only' if simulation else 'actual_descriptive_only', 'simulation': simulation, 'planned_ids': ids, 'states': states, 'pairs': paired,
            'three_run_label_changes': tri_changes, 'three_run_full_vector': {'common_n': len(tri), 'equal_n': sum(all(len({binary(runs[c][i], d) for c in ('R1', 'R2', 'R3')}) == 1 for d in DIMENSIONS) for i in tri)},
            'q_common_ids': common, 'q_excluded_ids': [i for i in ids if i not in common], 'q_runs': q, 'q_ranges': qranges,
            'weighting': 'unweighted; weighted diagnostic design requires a separate pre-frozen extension', 'threshold': None}
