"""Static impact-selector design; NEVER imports/executes a classifier.

Not used on the real population by the author. V11 current entry is dominated at every new call. The caller must supply a separately sealed
complete manifest, compatible baseline, audited candidate and equivalence chain.
Only metadata/IDs/reasons go to stdout. Classification and labels cannot select.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import unicodedata

DIMS = ('S', 'E', 'Ec', 'I', 'F')
DECISION_KEYS = {'value', 'basis_path', 'current_anchor', 'current_proposition',
                 'context_evidence', 'reason', 'needed_material', 'rule_conflict', 'details'}
MODULES = ('evidence', 'source_packet', 'source_receipts', 'relations', 'dimensions')
V11_REPAIR_ENTRY = '数据保护|受保护[^。；;]{0,6}数据'


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def verified(spec):
    if not isinstance(spec, dict) or not {'path', 'bytes', 'sha256'} <= set(spec):
        raise ValueError('missing exact binding')
    seen = binding(spec['path'])
    if any(seen[key] != spec[key] for key in ('path', 'bytes', 'sha256')):
        raise ValueError('binding mismatch: ' + str(spec['path']))
    return Path(seen['path'])


def match_view(raw):
    # Exact copied old evidence.matching_view normalization, no classifier import.
    joined = ''.join(unicodedata.normalize('NFKC', char) for char in raw)
    return re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])', '', joined)


def gate(raw):
    return bool(re.search(V11_REPAIR_ENTRY, match_view(raw)))


def dump(node):
    return ast.dump(node, include_attributes=False)


def expected_call(module):
    source = ('if _v11_repair_gate(self.norm):\n self._v11_protected_data_roles()'
              if module == 'relations' else
              'if _v11_repair_gate(view.norm):\n _v11_protected_data_I_consume(acc, view)')
    return ast.parse(source).body[0]


def is_new_definition(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if not node.name.startswith('_v11_'):
            return False
        if node.decorator_list:
            raise ValueError('new definitions cannot have eager decorators')
        # Global state and dynamic escape hatches invalidate record independence.
        prohibited_calls = {'eval', 'exec', 'globals', 'locals', '__import__',
                            'setattr', 'delattr', 'open', 'compile'}
        for item in ast.walk(node):
            if isinstance(item, (ast.Global, ast.Nonlocal, ast.Import, ast.ImportFrom)):
                raise ValueError('new function has global/dynamic state')
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Name):
                if item.func.id in prohibited_calls:
                    raise ValueError('new function has dynamic or external access')
        for value in node.args.defaults + [x for x in node.args.kw_defaults if x]:
            if any(isinstance(item, ast.Call) for item in ast.walk(value)):
                raise ValueError('eager new default computation is not allowed')
        return True
    if isinstance(node, ast.ImportFrom) and node.module == 'relations' and len(node.names)==1 and node.names[0].name=='_v11_repair_gate' and node.names[0].asname is None:
        return True
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == 'V11_REPAIR_ENTRY':
            if ast.literal_eval(node.value) != V11_REPAIR_ENTRY:
                raise ValueError('candidate entry differs from frozen selector')
            return True
    return False


def strip_extensions(tree, module):
    out = []
    guard_n = 0
    for item in tree.body:
        if is_new_definition(item):
            continue
        if module == 'relations' and isinstance(item, ast.ClassDef) and item.name == 'RelationView':
            members = []
            for member in item.body:
                if is_new_definition(member):
                    continue
                if isinstance(member, ast.FunctionDef) and member.name == '__init__':
                    if not member.body or dump(member.body[-1]) != dump(expected_call(module)):
                        raise ValueError('new relation call must be the guarded last init statement')
                    member.body = member.body[:-1]
                    guard_n += 1
                members.append(member)
            item.body = members
        elif module == 'dimensions' and isinstance(item, ast.FunctionDef) and item.name == 'judge':
            positions = [i for i, statement in enumerate(item.body)
                         if dump(statement) == dump(expected_call(module))]
            if len(positions) != 1:
                raise ValueError('one exact guarded new consumer call required')
            position = positions[0]
            following = item.body[position + 1] if position + 1 < len(item.body) else None
            expected_finish = ast.parse('decisions = acc.finish()').body[0]
            if following is None or dump(following) != dump(expected_finish):
                raise ValueError('new consumer must follow old loop immediately before finish')
            item.body.pop(position)
            guard_n += 1
        out.append(item)
    tree.body = out
    if guard_n != 1:
        raise ValueError('missing or multiple isolated entry calls')
    return tree


def prove_code(old_specs, new_specs):
    old = {Path(s['path']).stem: s for s in old_specs}
    new = {Path(s['path']).stem: s for s in new_specs}
    if set(old) != set(MODULES) or set(new) != set(MODULES):
        raise ValueError('five exact old and candidate modules required')
    for name in MODULES:
        before, after = verified(old[name]), verified(new[name])
        if name not in ('relations', 'dimensions'):
            if before.read_bytes() != after.read_bytes():
                raise ValueError('shared source/evidence/receipt module changed')
            continue
        old_tree = ast.parse(before.read_text())
        new_tree = ast.parse(after.read_text())
        entries = [x for x in new_tree.body if isinstance(x, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'V11_REPAIR_ENTRY' for t in x.targets)]
        if name == 'relations' and (len(entries) != 1 or ast.literal_eval(entries[0].value) != V11_REPAIR_ENTRY):
            raise ValueError('one exact top-level entry constant required')
        if name == 'relations':
            classes = [x for x in new_tree.body if isinstance(x, ast.ClassDef) and x.name == 'RelationView']
            if len(classes) != 1 or sum(isinstance(x, ast.FunctionDef) and x.name == '_v11_protected_data_roles'
                                         for x in classes[0].body) != 1:
                raise ValueError('one new relationship builder method required')
        elif sum(isinstance(x, ast.FunctionDef) and x.name == '_v11_protected_data_I_consume' for x in new_tree.body) != 1:
            raise ValueError('one new IF-only consumer required')
        gate_defs = [x for x in new_tree.body if isinstance(x, ast.FunctionDef)
                     and x.name == '_v11_repair_gate']
        expected_gate = ast.parse('def _v11_repair_gate(text):\n return bool(re.search(V11_REPAIR_ENTRY, text))').body[0]
        if name == 'relations' and len(gate_defs)==1 and gate_defs[0].body and isinstance(gate_defs[0].body[0],ast.Expr) and isinstance(gate_defs[0].body[0].value,ast.Constant) and isinstance(gate_defs[0].body[0].value.value,str):
            gate_defs[0].body.pop(0)
        if name == 'relations' and (len(gate_defs) != 1 or dump(gate_defs[0]) != dump(expected_gate)):
            raise ValueError('entry gate must have the exact side-effect-free implementation')
        if dump(old_tree) != dump(strip_extensions(new_tree, name)):
            raise ValueError('existing AST changed outside isolated new route')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True,
                        help='separately sealed contract; no classifier executes')
    args = parser.parse_args()
    contract_path = Path(args.contract).resolve()
    contract = json.loads(contract_path.read_bytes())
    manifest_path = verified(contract['manifest_binding'])
    manifest = json.loads(manifest_path.read_bytes())
    rows = manifest['records']
    ids = [row['id'] for row in rows]
    if len(ids) != 4481 or len(set(ids)) != 4481 or ids != manifest['approved_record_ids']:
        raise ValueError('complete ordered 4481 identity manifest required; no partial population claim')
    fallback = []
    try:
        prove_code(contract['old_modules'], contract['candidate_modules'])
        audit = contract['manual_static_audit']
        if audit.get('approved') is not True:
            raise ValueError('new bodies and caller/wrapper contracts have not been independently audited')
        for key in ('record_local_only', 'new_relation_not_consumed_by_old_units',
                    'only_I_decision_or_explicit_I_request_mutations',
                    'same_adapter_evidence_wrapper_and_input_delta_closure_verified', 'actual_combined_v2_baseline_compatible_verified'):
            if audit.get(key) is not True:
                raise ValueError('missing audited proof obligation: ' + key)
        for spec in audit['proof_artifact_bindings']:
            verified(spec)
    except Exception as exc:
        fallback.append(str(exc))
    baseline_path = verified(contract['baseline_prediction_binding'])
    baseline_rows = []
    with baseline_path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                raise ValueError('unfinished baseline stream')
            baseline_rows.append(json.loads(line))
    if [row.get('id') for row in baseline_rows] != ids:
        raise ValueError('baseline/manifest identity or order mismatch')
    if contract.get('global_baseline_error') is not False:
        fallback.append('global baseline error status is not verified clean')
    baseline_meta = {}
    try:
        previous_manifest_path = verified(contract['baseline_manifest_binding'])
        previous_manifest = json.loads(previous_manifest_path.read_bytes())
        previous_rows = previous_manifest['records']
        if [row['id'] for row in previous_rows] != ids or previous_manifest['approved_record_ids'] != ids:
            raise ValueError('baseline input manifest identity/order differs')
        baseline_meta = {row['id']: row for row in previous_rows}
    except Exception as exc:
        fallback.append('baseline input material binding closure unproved:' + str(exc))
    selected = []
    reuse_n = 0
    for meta, baseline in zip(rows, baseline_rows):
        reasons = []
        if fallback:
            reasons.append('full4481_fallback_unproved_scope_contract')
        if baseline_meta and meta['packet_binding'] != baseline_meta[meta['id']]['packet_binding']:
            reasons.append('input_material_binding_changed_whole_record_recompute')
        try:
            packet_path = verified(meta['packet_binding'])
            packet = json.loads(packet_path.read_bytes())
            body = packet['source_bundle']['source_record']['text']
            if not isinstance(body, str):
                raise ValueError('current body is not a string')
            if gate(body):
                reasons.append('all_new_route_effects_dominated_by_frozen_current_entry')
        except Exception as exc:
            # Never reuse an unbound input, even if a lexical projection looked empty.
            reasons.append('input_not_eligible_for_reuse:' + type(exc).__name__)
        if baseline.get('implementation_errors'):
            reasons.append('record_baseline_technical_failure')
        decisions = baseline.get('decisions')
        if not isinstance(decisions, dict) or set(decisions) != set(DIMS) or any(
                not isinstance(decisions[d], dict) or set(decisions[d]) != DECISION_KEYS for d in DIMS):
            reasons.append('incomplete_baseline_decisions')
        elif baseline.get('candidate_decisions_diagnostic_only') != decisions:
            reasons.append('final_candidate_nonidentity_or_missing_diagnostic')
        if reasons:
            selected.append({'id': meta['id'], 'packet_binding': meta['packet_binding'], 'gate_matched': any('all_new_route_effects' in x for x in reasons), 'reasons': reasons,
                             'recompute_scope': 'whole record; every old/new unit, role, I request and complete evidence chain'})
        else:
            reuse_n += 1
    print(json.dumps({'status': 'static_selection_only_no_classifier_execution',
                      'record_N': 4481, 'selected_N': len(selected),
                      'reusable_N': reuse_n, 'full_fallback_reasons': fallback,
                      'affected_records': selected,
                      'selected_record_ids': [r['id'] for r in selected],
                      'reusable_record_ids': [r['id'] for r in rows if r['id'] not in {x['id'] for x in selected}],
                      'contract_binding': binding(contract_path),
                      'manifest_binding': binding(manifest_path),
                      'baseline_prediction_binding': binding(baseline_path),
                      'selector_binding': binding(__file__),
                      'labels_departments_ids_not_selection_features': True,
                      'actual_selected_count_not_yet_measured_in_design': True},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
