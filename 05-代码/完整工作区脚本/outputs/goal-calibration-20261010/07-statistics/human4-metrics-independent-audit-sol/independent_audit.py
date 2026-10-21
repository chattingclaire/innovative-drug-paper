#!/usr/bin/env python3
"""Read-only human4 arithmetic audit. Standard-library implementation only.

No project calculation code is imported or executed. XML caches are compared
with exact Fraction arithmetic and an independent small Excel expression parser.
Only the assigned audit directory is written. Policy materials are hash-only.
"""
from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
OUT = ROOT / '07-statistics/human4-metrics-independent-audit-sol'
DELIVERY = ROOT / '09-delivery/agent-review-20261010/真人4项复核后-v2'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
TARGETS = {('RECODE25-00005', 'S'), ('RECODE25-03876', 'Ec'),
           ('RECODE25-00138', 'I'), ('RECODE25-00138', 'F')}
TOLERANCE = 1e-12
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
reads, binding_declarations, issues, checks = {}, [], [], []


def guard(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Outside assigned ROOT: {path}')
    if re.search(r'formal[-_]?800|gold', str(path.relative_to(ROOT)), re.I):
        raise ValueError(f'Prohibited source: {path}')
    return path


def fingerprint(path):
    path = guard(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def register(path, mode='hash-only', purpose='binding verification'):
    path = guard(path)
    key = str(path)
    if key not in reads:
        reads[key] = {**fingerprint(path), 'modes': [], 'purposes': []}
    if mode not in reads[key]['modes']:
        reads[key]['modes'].append(mode)
    if purpose not in reads[key]['purposes']:
        reads[key]['purposes'].append(purpose)
    return path


def read_json(path, purpose):
    return json.loads(register(path, 'JSON metadata/label extraction', purpose).read_text())


def read_jsonl(path, purpose):
    return [json.loads(line) for line in register(path, 'JSON label extraction', purpose).read_text().splitlines() if line.strip()]


def collect_bindings(value, origin):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            binding_declarations.append({**{k: value[k] for k in ('path', 'bytes', 'sha256') if k in value}, 'origin': origin})
        for key, child in value.items():
            collect_bindings(child, f'{origin}/{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            collect_bindings(child, f'{origin}/{index}')


def check(name, passed, details=None):
    row = {'name': name, 'passed': bool(passed)}
    if details is not None:
        row['details'] = details
    checks.append(row)
    if not passed:
        issues.append(row)


def read_xlsx(path):
    path = register(path, 'XLSX XML saved values/formulas', 'labels, caches, provenance and preservation')
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {n.attrib['Id']: (n.attrib['Target'].lstrip('/') if n.attrib['Target'].startswith('/')
                   else posixpath.normpath('xl/' + n.attrib['Target'])) for n in rels}
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = {}
        for sheet in wb.find('s:sheets', NS):
            xml = ET.fromstring(z.read(targets[sheet.attrib[REL_NS]]))
            cells = {}
            for cell in xml.findall('s:sheetData/s:row/s:c', NS):
                raw = cell.findtext('s:v', default=None, namespaces=NS)
                kind = cell.attrib.get('t', 'n')
                if kind == 's':
                    value = strings[int(raw)] if raw is not None else None
                elif kind == 'inlineStr':
                    value = ''.join(cell.find('s:is', NS).itertext())
                elif kind in ('str', 'e'):
                    value = raw
                elif kind == 'b':
                    value = bool(int(raw)) if raw is not None else None
                else:
                    value = Fraction(raw) if raw is not None else None
                cells[cell.attrib['r']] = {'value': value,
                    'formula': cell.findtext('s:f', default=None, namespaces=NS), 'type': kind}
            sheets[sheet.attrib['name']] = cells
        return sheets


def value(book, sheet, addr):
    return book[sheet].get(addr, {}).get('value')


def extract_labels(book, sheet='编码表', column='D'):
    result = {}
    for row in range(7, 392):
        key = (value(book, sheet, f'A{row}'), str(value(book, sheet, f'C{row}')).split()[0])
        label = value(book, sheet, f'{column}{row}')
        if key in result:
            raise ValueError(f'Duplicate label key {key}')
        if label not in (Fraction(0), Fraction(1)):
            raise ValueError(f'Nonbinary/missing label at {sheet}!{column}{row}: {label}')
        result[key] = int(label)
    return result


def flatten_predictions(records):
    out = {}
    ids = []
    for record in records:
        ids.append(record['id'])
        if set(record['labels']) != set(DIMENSIONS):
            raise ValueError(f'Missing dimension in {record["id"]}')
        for dimension, label in record['labels'].items():
            if type(label) is not int or label not in (0, 1):
                raise ValueError(f'Nonbinary prediction: {record["id"]}/{dimension}')
            out[(record['id'], dimension)] = label
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate machine record ID')
    return out


def four_cells(reference, prediction, dimension=None):
    four = dict(TP=0, FP=0, FN=0, TN=0)
    disagreements = []
    for key, ref in reference.items():
        if dimension is not None and key[1] != dimension:
            continue
        pred = prediction[key]
        direction = {(1, 1): 'TP', (0, 1): 'FP', (1, 0): 'FN', (0, 0): 'TN'}[(ref, pred)]
        four[direction] += 1
        if pred != ref:
            disagreements.append({'id': key[0], 'dimension': key[1], 'prediction': pred,
                                  'reference': ref, 'direction': direction})
    return four, disagreements


def exact_metrics(four):
    tp, fp, fn, tn = (four[k] for k in ('TP', 'FP', 'FN', 'TN'))
    n = tp + fp + fn + tn
    def ratio(a, b):
        return Fraction(a, b) if b else None
    po = ratio(tp + tn, n)
    pe = ratio((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp), n * n)
    kappa = (po - pe) / (1 - pe) if po is not None and pe != 1 else None
    metrics = {'kappa': kappa, 'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
               'F1': ratio(2 * tp, 2 * tp + fp + fn), 'Po': po, 'Pe': pe,
               'Ppos': ratio(2 * tp, 2 * tp + fp + fn), 'Pneg': ratio(2 * tn, 2 * tn + fp + fn),
               'specificity': ratio(tn, tn + fp), 'NPV': ratio(tn, tn + fn)}
    denominators = {'kappa_1_minus_Pe': 1 - pe if pe is not None else None,
                    'precision': tp + fp, 'recall': tp + fn, 'F1_Ppos': 2 * tp + fp + fn,
                    'Po': n, 'Pe': n * n, 'Pneg': 2 * tn + fp + fn,
                    'specificity': tn + fp, 'NPV': tn + fn}
    return metrics, denominators


def compatible(a, b):
    if isinstance(a, (int, float, Fraction)) and not isinstance(a, bool) and isinstance(b, (int, float, Fraction)) and not isinstance(b, bool):
        return abs(float(a) - float(b)) <= TOLERANCE
    return a == b


TOKEN = re.compile(r'\s*(?:((?:\'(?:[^\']|\'\')+\'!)?\$?[A-Z]+\$?\d+(?::\$?[A-Z]+\$?\d+)?)|("(?:[^"]|"")*")|(\d+(?:\.\d+)?)|([A-Z][A-Z0-9_.]*)|(<>|<=|>=|[=<>+*/^(),-]))')


class FormulaParser:
    """Small independent parser for saved IF/SUM/COUNTIFS scalar formulas."""
    def __init__(self, formula):
        self.tokens, end = [], 0
        for match in TOKEN.finditer(formula.lstrip('=')):
            if match.start() != end:
                raise ValueError(f'Unsupported formula text: {formula[end:match.start()]}')
            self.tokens.append(next(v for v in match.groups() if v is not None))
            end = match.end()
        if end != len(formula.lstrip('=')):
            raise ValueError(f'Unsupported formula tail: {formula[end:]}')
        self.position = 0

    def take(self):
        token = self.tokens[self.position]
        self.position += 1
        return token

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def expression(self, minimum=0):
        token = self.take()
        if token == '(':
            left = self.expression()
            if self.take() != ')':
                raise ValueError('Unbalanced parentheses')
        elif token == '-':
            left = ('neg', self.expression(5))
        elif token.startswith('"'):
            left = ('literal', token[1:-1].replace('""', '"'))
        elif re.fullmatch(r'\d+(?:\.\d+)?', token):
            left = ('literal', Fraction(token))
        elif self.peek() == '(':
            self.take()
            args = [self.expression()]
            while self.peek() == ',':
                self.take()
                args.append(self.expression())
            if self.take() != ')':
                raise ValueError('Unbalanced function')
            left = ('function', token, args)
        else:
            left = ('reference', token)
        precedence = {'=': 1, '<>': 1, '<': 1, '>': 1, '<=': 1, '>=': 1,
                      '+': 2, '-': 2, '*': 3, '/': 3, '^': 4}
        while self.peek() in precedence and precedence[self.peek()] >= minimum:
            op = self.take()
            right = self.expression(precedence[op] + (0 if op == '^' else 1))
            left = ('operation', op, left, right)
        return left

    def parse(self):
        result = self.expression()
        if self.peek() is not None:
            raise ValueError(f'Unexpected token {self.peek()}')
        return result


def col_number(column):
    n = 0
    for c in column:
        n = n * 26 + ord(c) - 64
    return n


def col_letters(n):
    s = ''
    while n:
        n, digit = divmod(n - 1, 26)
        s = chr(digit + 65) + s
    return s


class FormulaEvaluator:
    def __init__(self, book):
        self.book, self.memo, self.active = book, {}, set()

    def cell(self, sheet, addr):
        addr = addr.replace('$', '')
        key = (sheet, addr)
        if key in self.memo:
            return self.memo[key]
        if key in self.active:
            raise ValueError(f'Circular formula {key}')
        self.active.add(key)
        item = self.book[sheet].get(addr, {})
        result = self.eval(FormulaParser(item['formula']).parse(), sheet) if item.get('formula') else item.get('value')
        self.active.remove(key)
        self.memo[key] = result
        return result

    def reference(self, token, default_sheet):
        sheet, addr = token.split('!', 1) if '!' in token else (default_sheet, token)
        sheet = sheet.strip("'").replace("''", "'")
        addr = addr.replace('$', '')
        if ':' not in addr:
            return self.cell(sheet, addr)
        first, last = addr.split(':')
        c1, r1 = re.fullmatch(r'([A-Z]+)(\d+)', first).groups()
        c2, r2 = re.fullmatch(r'([A-Z]+)(\d+)', last).groups()
        return [self.cell(sheet, f'{col_letters(c)}{r}') for r in range(int(r1), int(r2) + 1)
                for c in range(col_number(c1), col_number(c2) + 1)]

    def eval(self, node, sheet):
        kind = node[0]
        if kind == 'literal':
            return node[1]
        if kind == 'reference':
            return self.reference(node[1], sheet)
        if kind == 'neg':
            return -self.eval(node[1], sheet)
        if kind == 'operation':
            a, b, op = self.eval(node[2], sheet), self.eval(node[3], sheet), node[1]
            if a is None:
                a = Fraction(0)
            if b is None:
                b = Fraction(0)
            return {'+': lambda: a + b, '-': lambda: a - b, '*': lambda: a * b,
                    '/': lambda: a / b, '^': lambda: a ** b, '=': lambda: a == b,
                    '<>': lambda: a != b, '<': lambda: a < b, '>': lambda: a > b,
                    '<=': lambda: a <= b, '>=': lambda: a >= b}[op]()
        name, args = node[1], node[2]
        if name == 'IF':
            return self.eval(args[1] if self.eval(args[0], sheet) else args[2], sheet)
        values = [self.eval(arg, sheet) for arg in args]
        if name == 'SUM':
            flat = [v for group in values for v in (group if isinstance(group, list) else [group])]
            return sum((v for v in flat if isinstance(v, (Fraction, int))), Fraction(0))
        if name == 'COUNTIFS':
            ranges, criteria = values[::2], values[1::2]
            if any(not isinstance(r, list) or len(r) != len(ranges[0]) for r in ranges):
                raise ValueError('COUNTIFS mismatched ranges')
            return Fraction(sum(all(group[i] == criterion for group, criterion in zip(ranges, criteria))
                                for i in range(len(ranges[0]))))
        raise ValueError(f'Unsupported Excel function {name}')


def serializable(obj):
    if isinstance(obj, Fraction):
        return {'exact': str(obj), 'value': float(obj)}
    if isinstance(obj, dict):
        return {str(k): serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serializable(v) for v in obj]
    return obj


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = read_json(ROOT / 'logs/human4-reference-v2-delivery/edit-inputs.json', 'four-label human receipt')
    verification = read_json(ROOT / 'logs/human4-reference-v2-delivery/saved-workbook-verification.json', 'existing preservation claims')
    raw = read_json(ROOT / '07-statistics/human4-reference-v2-raw77-root/metrics.json', 'reported metrics and provenance')
    metric_seal = read_json(ROOT / '07-statistics/human4-reference-v2-raw77-root/seal.json', 'reported metric seal')
    rule_dir = ROOT / '06-coding/rule-v18-overall-health-boundary-development-root/run77-first'
    rule_seal = read_json(rule_dir / 'seal.json', 'rule first binding')
    rule_freeze = read_json(rule_dir / 'freeze.json', 'original rule implementation and material version')
    rule_execution = read_json(rule_dir / 'execution.json', 'original execution coverage')
    native_verification = read_json(ROOT / '07-statistics/native-v16-current-posthoc-reference-root/verification-and-metrics.json', 'original native run metadata')
    for name, obj in [('receipt', receipt), ('saved-verification', verification), ('raw-metrics', raw),
                      ('metric-seal', metric_seal), ('rule-seal', rule_seal), ('rule-freeze', rule_freeze),
                      ('native-verification', native_verification)]:
        collect_bindings(obj, name)

    refs, originals, preservation = [], [], []
    for index, job in enumerate(receipt['jobs']):
        original, updated = read_xlsx(job['source']['path']), read_xlsx(job['target'])
        old_labels, new_labels = extract_labels(original), extract_labels(updated)
        changed_labels = {key for key in old_labels if old_labels[key] != new_labels[key]}
        check(f'reference_{index}_only_four_labels_changed', changed_labels == TARGETS)
        check(f'reference_{index}_four_zero_to_one', all(old_labels[k] == 0 and new_labels[k] == 1 for k in TARGETS))
        expected_changes = {('编码表', 'A4'), ('原文语境', 'A4')}
        for row in (7, 179, 215, 216):
            expected_changes |= {('编码表', f'{col}{row}') for col in ('D', 'E', 'H')}
        actual_changes = {(sheet, addr) for sheet in original for addr, cell in original[sheet].items()
                          if not compatible(cell['value'], value(updated, sheet, addr))}
        check(f'reference_{index}_existing_cells_preserved_except_14', actual_changes == expected_changes,
              {'changed_existing_cells': sorted(actual_changes)})
        check(f'reference_{index}_saved_verification_change_list', actual_changes == set(map(tuple, verification['tables'][index]['changed_existing_cells'])))
        appendix_ok = all(value(updated, '原文语境', f'{col_letters(j + 1)}{receipt["appendix_start_row"] + i}') == cell
                          for i, row in enumerate(receipt['appendix_rows']) for j, cell in enumerate(row))
        check(f'reference_{index}_43_appendix_rows_851_893', len(receipt['appendix_rows']) == 43 and appendix_ok)
        refs.append(new_labels)
        originals.append(old_labels)
        preservation.append({'reference': index, 'changed_labels': sorted(changed_labels),
                             'changed_existing_cells': sorted(actual_changes), 'appendix_rows': 43,
                             'other_existing_label_values_preserved': len(new_labels) - len(changed_labels)})
    reference = refs[0]
    check('A_B_385_saved_values_identical', refs[0] == refs[1] and len(reference) == 385)
    ids = {key[0] for key in reference}
    check('reference_77_complete_five_dimension_records', len(ids) == 77 and all({k[1] for k in reference if k[0] == i} == set(DIMENSIONS) for i in ids))
    check('human4_not_all385_one', sum(reference.values()) == 77 and len(reference) - sum(reference.values()) == 308)
    check('receipt_four_targeted_labels_and_explicit_identity', receipt['human_targeted_labels_received_N'] == 4 and
          'not all 385' in receipt['message_interpretation'] and not receipt['independent_human_initial_coding'] and
          not receipt['formal_acceptance'] and 'AI' in receipt['reference_identity'] and 'AI' in receipt['reason_origin'])

    predictions = {}
    for method in ('native', 'rule'):
        records = read_jsonl(raw['prediction_bindings'][method]['path'], f'unchanged {method} binary predictions')
        predictions[method] = flatten_predictions(records)
        check(f'{method}_77_records_385_complete_binary_labels', len(records) == 77 and len(predictions[method]) == 385 and set(predictions[method]) == set(reference))
        if method == 'native':
            collect_bindings(records, 'native-prediction-projection')

    raw_first_labels = {}
    for batch in raw['native_batches_verified']:
        first = read_json(batch['first_binding']['path'], 'original native first label extraction only')
        seal = read_json(batch['seal_binding']['path'], 'original native first seal metadata')
        collect_bindings(first, f'native-{batch["batch_id"]}/first')
        collect_bindings(seal, f'native-{batch["batch_id"]}/seal')
        for record in first['records']:
            for dimension, decision in record['dimensions'].items():
                key = (record['source_id'], dimension)
                if key in raw_first_labels:
                    raise ValueError(f'Duplicate native first {key}')
                raw_first_labels[key] = decision['value']
    check('native_projection_385_matches_13_original_firsts', len(raw['native_batches_verified']) == 13 and raw_first_labels == predictions['native'])
    check('rule_single_original_run_coverage', rule_execution['actual_cohort_inference_runs'] == 1 and
          rule_execution['actual_record_N'] == 77 and rule_execution['actual_dimension_N'] == 385 and
          rule_execution['technical_failure_dimension_N'] == 0 and rule_execution['lawful_null_N'] == 0)

    calculations, disagreements = {}, {}
    for method, prediction in predictions.items():
        calculations[method] = {}
        _, disagreements[method] = four_cells(reference, prediction)
        check(f'{method}_all_disagreement_directions_exposed', sorted(disagreements[method], key=str) == sorted(raw['binary_disagreements'][method], key=str))
        for dimension in DIMENSIONS:
            four, errors = four_cells(reference, prediction, dimension)
            metric_values, denominators = exact_metrics(four)
            row = raw['dimensions'][method][dimension]
            check(f'{method}_{dimension}_reported_four_cells', four == row['four_cells'])
            check(f'{method}_{dimension}_10_reported_metrics', all(compatible(metric_values[k], row['metrics'][k]) for k in metric_values))
            check(f'{method}_{dimension}_no_NA_or_dead_denominator', all(v is not None and v != 0 for v in denominators.values()) and all(v is not None for v in metric_values.values()))
            targets = {k: metric_values[k] is not None and metric_values[k] >= Fraction(4, 5) for k in ('kappa', 'precision', 'recall', 'F1')}
            check(f'{method}_{dimension}_project_0_8_and_reported_flags', all(targets.values()) and targets == row['point_targets'])
            check(f'{method}_{dimension}_coverage_no_null_pair', row['assigned_N'] == row['saved_N'] == row['joint_binary_N'] == 77 and row['null_pairs'] == [])
            calculations[method][dimension] = {'four_cells': four, 'metrics': metric_values,
                                              'denominators': denominators, 'point_targets_ge_0_8': targets, 'errors': errors}

    expected_native_errors = [{'id': 'RECODE25-02573', 'dimension': 'Ec', 'prediction': 1, 'reference': 0, 'direction': 'FP'}]
    check('native_one_02573Ec_FP', disagreements['native'] == expected_native_errors)
    check('rule_four_targeted_FN_retained', len(disagreements['rule']) == 4 and
          {(x['id'], x['dimension']) for x in disagreements['rule']} == TARGETS and all(x['direction'] == 'FN' for x in disagreements['rule']))

    companion_path = DELIVERY / '77条机器编码与指标-真人补核后.xlsx'
    companion = read_xlsx(companion_path)
    for column, label_set in [('D', reference), ('E', predictions['native']), ('F', predictions['rule'])]:
        check(f'companion_385_{column}_labels_raw_direction', extract_labels(companion, '编码对照', column) == label_set)
    expected_formula_values = {}
    four_formula_direction_checks = []
    for idx, (method, dimension) in enumerate((m, d) for m in ('native', 'rule') for d in DIMENSIONS):
        count_row, core_row, auxiliary_row = 21 + idx, 6 + idx, 36 + idx
        calculation = calculations[method][dimension]
        four, metrics = calculation['four_cells'], calculation['metrics']
        tp, fp, fn, tn = (four[k] for k in ('TP', 'FP', 'FN', 'TN'))
        count_values = {'C': tp + fp + fn + tn, 'D': tp + fn, 'E': tn + fp,
                        'F': tp, 'G': fp, 'H': fn, 'I': tn, 'J': 0}
        for col, expected in count_values.items():
            expected_formula_values[f'{col}{count_row}'] = Fraction(expected)
        for col, metric in zip('CDEF', ('kappa', 'precision', 'recall', 'F1')):
            expected_formula_values[f'{col}{core_row}'] = metrics[metric]
        for col, metric in zip('CDEFGH', ('Po', 'Pe', 'Ppos', 'Pneg', 'specificity', 'NPV')):
            expected_formula_values[f'{col}{auxiliary_row}'] = metrics[metric]
        expected_formula_values[f'I{auxiliary_row}'] = Fraction(tp + fp)
        pred_col = 'E' if method == 'native' else 'F'
        for col, ref_criterion, pred_criterion in [('F', 1, 1), ('G', 0, 1), ('H', 1, 0), ('I', 0, 0)]:
            addr = f'{col}{count_row}'
            expected_formula = (f"COUNTIFS('编码对照'!$C$7:$C$391,$B{count_row},"
                                f"'编码对照'!$D$7:$D$391,{ref_criterion},"
                                f"'编码对照'!${pred_col}$7:${pred_col}$391,{pred_criterion})")
            four_formula_direction_checks.append({'cell': addr, 'matches': companion['指标'][addr]['formula'] == expected_formula})
    evaluator = FormulaEvaluator(companion)
    formula_checks = []
    for sheet, cells in companion.items():
        for addr, cell in cells.items():
            if cell['formula'] is None:
                continue
            computed = evaluator.cell(sheet, addr)
            expected = expected_formula_values.get(addr) if sheet == '指标' else None
            formula_checks.append({'sheet': sheet, 'cell': addr, 'cached_value': cell['value'],
                'computed_exact': computed, 'independent_expected': expected,
                'cache_matches_computed': compatible(cell['value'], computed),
                'formula_matches_independent_raw_result': expected is not None and compatible(expected, computed)})
    check('companion_190_formulas_all_caches_and_raw_arithmetic', len(formula_checks) == len(expected_formula_values) == 190 and
          all(x['cache_matches_computed'] and x['formula_matches_independent_raw_result'] for x in formula_checks))
    check('companion_40_four_cell_formula_directions', len(four_formula_direction_checks) == 40 and all(x['matches'] for x in four_formula_direction_checks))
    error_cells = [{'sheet': sheet, 'cell': addr, 'value': cell['value']} for sheet, cells in companion.items()
                   for addr, cell in cells.items() if cell['type'] == 'e' or cell['value'] in ('NA', 'N/A', '#N/A', '#DIV/0!', '#REF!', '#VALUE!', '#NAME?', '#NUM!', '#NULL!')]
    check('companion_no_NA_or_excel_error_cache', error_cells == [], error_cells)
    provenance_cells = {addr: value(companion, '指标', addr) for addr in ('A3', 'A17', 'A18', 'A47', 'A54', 'A56')}
    provenance_cells['编码对照!A4'] = value(companion, '编码对照', 'A4')
    check('companion_explicit_version_and_posthoc_identity',
          all(t in provenance_cells['A47'] for t in ('v1.3F', 'v16', 'v18', '13', '77')) and
          all(t in provenance_cells['A54'] for t in ('κ=1', '独立真人初判信度尚未完成', '独立重复尚未完成')) and
          '未按新共同材料重新编码' in provenance_cells['编码对照!A4'] and 'AI初表' in provenance_cells['A3'])
    check('raw_posthoc_only_no_new_machine_run_or_formal_claim',
          raw['same_new_common_material_rerun'] is False and raw['machine_firsts_modified'] is False and
          raw['machine_coding_executed_again'] is False and raw['independent_human_initial_coding'] is False and
          raw['formal_acceptance'] is False and raw['population_CI95_calculated'] is False and raw['p_values_calculated'] is False)
    status = register(DELIVERY / '配套检验状态.txt', 'UTF-8 provenance statement', 'candidate and formal status').read_text()
    check('delivery_status_candidates_and_formal_work_still_pending', '候选未最终冻结' in status and '并非新共同材料上的重跑' in status and '待完成' in status)
    ab_four, _ = four_cells(refs[0], refs[1])
    ab_metrics, _ = exact_metrics(ab_four)
    check('A_B_saved_value_kappa_1_only', ab_metrics['kappa'] == 1)

    binding_results = []
    for declaration in binding_declarations:
        path = register(declaration['path'])
        observed = reads[str(path)]
        match = observed['sha256'] == declaration['sha256'] and ('bytes' not in declaration or observed['bytes'] == declaration['bytes'])
        binding_results.append({**declaration, 'observed_sha256': observed['sha256'],
                                'observed_bytes': observed['bytes'], 'matches': match})
    check('all_declared_read_only_source_bindings_match', all(x['matches'] for x in binding_results),
          {'declarations': len(binding_results), 'unique_files': len({x['path'] for x in binding_results}),
           'mismatches': [x for x in binding_results if not x['matches']]})
    changed_files = []
    for path, before in reads.items():
        after = fingerprint(path)
        if after['sha256'] != before['sha256'] or after['bytes'] != before['bytes']:
            changed_files.append(path)
    check('all_inputs_unchanged_during_read_only_audit', not changed_files, changed_files)

    all_core_pass = all(v['point_targets_ge_0_8'][metric] for m in calculations.values() for v in m.values()
                        for metric in ('kappa', 'precision', 'recall', 'F1'))
    audit = {'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'ROOT': str(ROOT),
        'audit_directory': str(OUT), 'status': 'PASS_WITH_SCOPE_LIMITS' if not issues else 'FAIL',
        'scope': 'Finite independent arithmetic and provenance only; 77 development records, 385 labels, 10 machine/dimension groups.',
        'independent_implementation': 'Standard library ZIP/XML parsing, Fraction four-cell metrics, independently implemented Excel IF/SUM/COUNTIFS expression parser; no ROOT calculate imports or machine execution.',
        'tolerance': TOLERANCE, 'all_core_development_point_targets_ge_0_8': all_core_pass,
        'formal_acceptance': False, 'semantic_audit_performed': False, 'independent_human_initial_reliability_established': False,
        'candidate_manual_rule_common_material_rerun_verified': False, 'prohibited_corpora_opened': False,
        'posthoc_scope': {'received_human_labels': 4, 'remaining_existing_labels_preserved': 381,
                         'reference_positive_N': sum(reference.values()), 'reference_negative_N': len(reference) - sum(reference.values()),
                         'A_B_saved_four_cells': ab_four, 'A_B_saved_metrics': ab_metrics,
                         'interpretation': 'A/B agreement is agreement of identical AI-seeded saved values after targeted human corrections, not independent human first coding.'},
        'calculations': calculations, 'binary_disagreements': disagreements, 'preservation': preservation,
        'formula_checks': formula_checks, 'four_cell_formula_direction_checks': four_formula_direction_checks,
        'provenance_cells': provenance_cells, 'checks': checks, 'issues': issues}
    manifest = {'created_at_utc': audit['created_at_utc'], 'scope': audit['scope'],
        'parsed_vs_hash_only_rule': 'Policy/source materials, manual/implementation files and source-reading manifests bound by hashes were never semantically read. Only assigned metadata, labels, workbook XML and provenance statements were extracted.',
        'write_boundary': str(OUT), 'inputs': list(reads.values()), 'binding_declarations': binding_results,
        'all_input_hashes_unchanged': not changed_files}
    (OUT / 'read-only-binding-manifest.json').write_text(json.dumps(serializable(manifest), ensure_ascii=False, indent=2) + '\n')
    (OUT / 'audit.json').write_text(json.dumps(serializable(audit), ensure_ascii=False, indent=2) + '\n')
    lines = ['真人4项后事后参照v2：有限独立算术与来源审查',
             f'ROOT={ROOT}', f'状态：{audit["status"]}',
             '范围：77条开发材料、385标签、LLM/规则×五维共10组；仅审查算术、保存缓存与来源，不评价政策语义或正式效度。',
             '独立实现：Python标准库、ZIP/XML、Fraction四格指标及自行实现IF/SUM/COUNTIFS表达式解析；未导入ROOT计算函数，未运行机器编码。',
             f'四项0→1已限定到指定标签；其余381标签保留。参照共{sum(reference.values())}个1、{len(reference)-sum(reference.values())}个0，未将385标签全部设为1。',
             'A/B全部385个当前保存值相同，整体κ=1；该值不能代表独立真人初判信度。',
             '', '方法  维度  TP/FP/FN/TN  κ  P  R  F1  逐维≥0.80']
    for method, groups in calculations.items():
        for dimension, result in groups.items():
            metrics, four = result['metrics'], result['four_cells']
            lines.append(f'{method}  {dimension}  {four["TP"]}/{four["FP"]}/{four["FN"]}/{four["TN"]}  ' +
                         '  '.join(f'{float(metrics[k]):.9f}' for k in ('kappa', 'precision', 'recall', 'F1')) +
                         f'  {all(result["point_targets_ge_0_8"].values())}')
    lines += ['', 'Po、Pe、Ppos、Pneg、specificity、NPV共60辅助值与原metrics一致；100指标均有有效分母，无NA。',
              '190个公式缓存均按独立解析复算并与raw四格结果一致；40个四格公式方向正确；编码对照D/E/F三列各385标签与参照/原LLM/原规则方向一致。',
              '错误公开保留：LLM 02573Ec为1个FP；规则00005S、03876Ec、00138I、00138F为4个FN。',
              '版本说明保留共同手册v1.3F、LLM提示v16、规则v18，以及13批次构成一次77条运行。四项事后更新仅改变参照，未产生新的机器运行。',
              '独立真人初判与裁定、同设置LLM独立重复、新共同材料候选manual/rule重跑及正式检验仍未完成；本审查不宣称这些检验通过。',
              f'来源绑定：{len(binding_results)}个声明、{len({x["path"] for x in binding_results})}个文件全部核对；审查输入前后SHA-256未变。',
              f'问题数：{len(issues)}。' if not issues else f'发现问题：{json.dumps(issues, ensure_ascii=False)}',
              'formal800、Gold及其他全量正文未打开；政策材料仅核对绑定哈希，不作语义审查。']
    (OUT / 'audit.txt').write_text('\n'.join(lines) + '\n')
    seal = {'created_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': audit['status'],
            'files': [fingerprint(OUT / filename) for filename in ('independent_audit.py', 'read-only-binding-manifest.json', 'audit.json', 'audit.txt')],
            'scope': audit['scope'], 'input_files_modified': False, 'machine_firsts_modified': False,
            'formal_acceptance': False, 'seal_policy': 'This seal binds only independent audit outputs; it does not replace original machine/reference seals.'}
    (OUT / 'seal.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': audit['status'], 'issues': issues, 'formula_N': len(formula_checks),
                      'binding_declarations_N': len(binding_results), 'source_files_N': len(reads),
                      'all_core_development_point_targets_ge_0_8': all_core_pass, 'audit_directory': str(OUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
