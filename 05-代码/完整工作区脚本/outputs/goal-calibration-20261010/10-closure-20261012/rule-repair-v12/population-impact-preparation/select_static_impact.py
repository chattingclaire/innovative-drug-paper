"""Preparation only: source-shape S/F superset, never imports a classifier.

No prediction/label/reference field is used for selection. Production prediction
bytes are hash-checked only. Any failure of the bound code proof selects all IDs;
input identity failures stop, rather than silently switching input populations.
"""
from __future__ import annotations
import argparse
import ast
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

HERE = Path(__file__).resolve().parent
_MATCHING_VIEW = None
S_HELPERS = {'_s_owned_data_security_scope', '_s_direct_parent_risk_review',
             '_s_field_answer_review', '_s_risk_question_content_scope',
             '_s_current_risk_question'}
# Every SE_RISK alternative contains at least one of these literal witnesses.
# Lookarounds and intervening content are deliberately relaxed. Safety and name
# witnesses cover both scope masks, including quoted medication-control content.
S_WITNESSES = {
    'S_security_scope': r'安全',
    'S_named_content_scope': r'字段|栏目|标题|文件|附件',
    'S_risk_action_scope': r'风险|不良|肝损伤|副作用|神经毒性|预防接种异常反应|治疗窗窄|AESI|ADR|SAE|AE|毒性|毒理|安全性事件|过敏|皮试|禁忌|药物相互作用|误选|误用|误刺|误吸|呛咳|窒息|用药差错|用药错误|超剂量|无指征',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}

def verified(entry):
    data = Path(entry['path']).read_bytes()
    if len(data) != entry['bytes'] or sha(data) != entry['sha256']:
        raise ValueError('Bound input changed: ' + entry['path'])
    return data

def matching_text(raw):
    if _MATCHING_VIEW is None:
        raise RuntimeError('Bound normalization was not initialized')
    return _MATCHING_VIEW(raw)[0]

def leaves(value, pointer=''):
    # All source text fields, including every body, raw/derived context, full
    # paragraph, visual transcription, source supplement and literal snapshot.
    # Administrative path/description strings cannot enter Unit.text. Those are
    # not semantic text (and a ubiquitous "文件" there would spuriously select all).
    if isinstance(value, dict):
        for key, item in value.items():
            child = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key == 'text' and isinstance(item, str):
                yield child, item
            elif isinstance(item, (dict, list)):
                yield from leaves(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, pointer + '/' + str(index))

def source_gate(bundle, v9_entry):
    reasons = {}
    for pointer, raw in leaves(bundle):
        # Both normalization routes feeding Unit.text are covered, including a
        # conservative removal of all whitespace before literal nomination.
        views = (re.sub(r'\s+', '', unicodedata.normalize('NFKC', raw)),
                 re.sub(r'\s+', '', unicodedata.normalize('NFKC', matching_text(raw))))
        for kind, pattern in S_WITNESSES.items():
            if kind not in reasons and any(re.search(pattern, text) for text in views):
                reasons[kind] = {'source_pointer': pointer, 'string_sha256': sha(raw.encode())}
    current = matching_text(bundle['source_record']['text'])
    if re.search(v9_entry, current):
        primary = bundle['source_record']['source_ref'].get('sha256')
        for index, doc in enumerate(bundle.get('source_full_text_resources', [])):
            paragraphs = doc.get('paragraphs', [])
            if doc.get('source_pdf_sha256', doc.get('source_sha256')) != primary or not paragraphs:
                continue
            text = '\n'.join(p.get('text', '') for p in paragraphs)
            if re.search('“([^”]{2,30})”(?:试点工作|试点项目|项目)', text):
                reasons['F_structured_plan_entry'] = {
                    'source_pointer': '/source_full_text_resources/' + str(index),
                    'same_primary_source': True,
                }
                break
    return reasons

def dump_ast(node):
    return ast.dump(node, include_attributes=False)

def functions(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name + '.' + child.name] = child
    return result

class SNoopReduction(ast.NodeTransformer):
    """Substitute proved helper no-op values, then simplify only those expressions."""
    def visit_Assign(self, node):
        names = {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
        if names & {'current_risk_question', 'parent_risk_review', 'data_security_properties'}:
            return None
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == '_s_risk_question_content_scope':
            return None
        return self.generic_visit(node)

    def visit_If(self, node):
        if isinstance(node.test, ast.Name) and node.test.id == 'data_security_properties':
            return None
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in {'current_risk_question', 'parent_risk_review'}:
            return ast.Constant(False)
        return node

    def visit_UnaryOp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.op, ast.Not) and isinstance(node.operand, ast.Constant) and type(node.operand.value) is bool:
            return ast.Constant(not node.operand.value)
        return node

    def visit_BoolOp(self, node):
        node = self.generic_visit(node)
        identity = isinstance(node.op, ast.And)
        values = [v for v in node.values if not (isinstance(v, ast.Constant) and v.value is identity)]
        if len(values) == 1:
            return values[0]
        node.values = values
        return node

    def visit_IfExp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and type(node.test.value) is bool:
            return node.body if node.test.value else node.orelse
        return node

    def visit_Dict(self, node):
        node = self.generic_visit(node)
        pairs = [(k, v) for k, v in zip(node.keys, node.values)
                 if not (k is None and isinstance(v, ast.Dict) and not v.keys)]
        node.keys, node.values = [p[0] for p in pairs], [p[1] for p in pairs]
        return node

def module_without(tree, removed, replace=None):
    tree = copy.deepcopy(tree)
    replace = replace or {}
    tree.body = [n for n in tree.body if not (isinstance(n, ast.FunctionDef) and n.name in removed)]
    for index, node in enumerate(tree.body):
        if isinstance(node, ast.FunctionDef) and node.name in replace:
            tree.body[index] = copy.deepcopy(replace[node.name])
        elif isinstance(node, ast.ClassDef):
            node.body = [n for n in node.body if not (isinstance(n, ast.FunctionDef) and n.name in removed)]
            for j, child in enumerate(node.body):
                if isinstance(child, ast.FunctionDef) and child.name in replace:
                    node.body[j] = copy.deepcopy(replace[child.name])
    return tree

def static_code_proof(config):
    global _MATCHING_VIEW
    result = {'kind': 'bound_AST_plus_control_flow_noop_proof', 'checks': {}}
    trees = {name: ast.parse(verified(entry).decode()) for name, entry in config['algorithm_bindings'].items()}
    normalizer_nodes = [n for n in trees['v12_evidence'].body if
                        (isinstance(n, ast.FunctionDef) and n.name == 'matching_view') or
                        (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_CJK_WHITESPACE' for t in n.targets))]
    if len(normalizer_nodes) != 2:
        raise ValueError('Bound normalization shape changed')
    normalizer_globals = {'re': re, 'unicodedata': unicodedata}
    exec(compile(ast.Module(body=normalizer_nodes, type_ignores=[]), '<bound evidence normalizer only>', 'exec'), normalizer_globals)
    _MATCHING_VIEW = normalizer_globals['matching_view']
    result['checks']['normalizer_uses_exact_bound_evidence_matching_view_AST'] = True
    base, candidate = trees['v11_dimensions'], trees['v12_dimensions']
    bf, cf = functions(base), functions(candidate)
    reduced = SNoopReduction().visit(copy.deepcopy(cf['_safety_effect']))
    result['checks']['S_noop_body_equals_v11_AST'] = dump_ast(reduced) == dump_ast(bf['_safety_effect'])
    stripped = module_without(candidate, S_HELPERS, {'_safety_effect': bf['_safety_effect']})
    result['checks']['dimensions_only_five_helpers_and_safety_effect_changed'] = dump_ast(stripped) == dump_ast(base)
    base, candidate = trees['v11_relations'], trees['v12_relations']
    bf, cf = functions(base), functions(candidate)
    stripped = module_without(candidate, {'_v12_plan_f_current_action'}, {'_v9_structured_plan': bf['RelationView._v9_structured_plan']})
    result['checks']['relations_only_F_helper_and_structured_plan_changed'] = dump_ast(stripped) == dump_ast(base)
    old = bf['RelationView._v9_structured_plan']; new = cf['RelationView._v9_structured_plan']
    # Old ends with F-if. New inserts a pure helper assignment immediately before
    # its F-if; every earlier statement, including the I emit, is unchanged.
    result['checks']['structured_plan_entire_prefix_and_I_emit_identical'] = (
        len(new.body) == len(old.body) + 1 and
        [dump_ast(n) for n in new.body[:-2]] == [dump_ast(n) for n in old.body[:-1]])
    expected = {'evidence', 'source_packet', 'source_receipts'}
    for name in expected:
        result['checks'][name + '_byte_identical'] = config['algorithm_bindings']['v11_' + name]['sha256'] == config['algorithm_bindings']['v12_' + name]['sha256']
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in trees['v12_relations'].body
                 if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'V9_REPAIR_ENTRY'}
    result['passed'] = all(result['checks'].values())
    result['candidate_SF_helpers_executed'] = False
    result['classifiers_imported'] = False
    result['no_selection_from_outputs_or_reference'] = True
    return result, constants['V9_REPAIR_ENTRY']

def inherited_compatibility(config, ids, lineage):
    """Read adopted scope metadata, never inspect old labels to choose this scope."""
    latest = {rid: 'joint-v7-relation-content-sol' for rid in ids}
    covered, stages, previous_seal = {rid: [] for rid in ids}, [], None
    for stage in config['adopted_compatibility_chain']:
        bound = {k: verified(v) for k, v in stage['bindings'].items()}
        plan = json.loads(bound['impact_closure_plan'])
        status = json.loads(bound['composite_status'])
        seal = json.loads(bound['composite_seal'])
        if stage['bindings']['composite_status'] not in seal['files']:
            raise ValueError('Composite status not sealed')
        if previous_seal is not None and stage['bindings']['parent_seal'] != previous_seal:
            raise ValueError('Adopted compatibility ancestors are discontinuous')
        previous_seal = stage['bindings']['composite_seal']
        selected = plan['affected_record_ids']
        if len(selected) != len(set(selected)) or not set(selected) <= set(ids) or len(selected) != plan['affected_record_N']:
            raise ValueError('Old adopted scope identity differs')
        if stage['stage'] == 'v8':
            if not all(plan.get(k) is True for k in ('all_old_branch_hits_included_including_positive_F',
                    'outside_branch_four_modules_and_remainder_byte_identical', 'same_original_inputs_manual_and_protocol')):
                raise ValueError('Original v8 exclusion proof not established')
            selected_basis = 'bound original changed-body exclusion proof and adopted seven-record scope'
        else:
            selection = json.loads(bound['selection'])
            contract = json.loads(bound['contract'])
            if (selection['record_N'] != 4481 or selection.get('full_fallback_reasons') or
                    [row['id'] for row in selection['affected_records']] != selected or
                    contract['manual_static_audit']['approved'] is not True):
                raise ValueError('Old adopted static selection/contract differs')
            if plan.get('full_fallback_reasons') or plan.get('all_entry_records_included_without_old_label_filter') is not True:
                raise ValueError('Old scope has unresolved static exclusions')
            selected_basis = 'bound ROOT-adopted static selector, complete affected list and prior compatibility proofs'
        selected_set = set(selected)
        for rid in ids:
            if rid in selected_set:
                latest[rid] = stage['actual_algorithm']
            else:
                covered[rid].append(stage['stage'])
        stages.append({'stage': stage['stage'], 'affected_N': len(selected),
                       'unaffected_N': len(ids) - len(selected), 'basis': selected_basis,
                       'bound_file_N': len(bound)})
    mismatch = [r['id'] for r in lineage if latest[r['id']] != r['actual_inference_algorithm']]
    if mismatch:
        raise ValueError('Current actual lineage not last adopted affected version: ' + ','.join(mismatch))
    return {'stages': stages, 'all4481_current_actual_algorithm_matches_adopted_scope_chain': True,
            'actual_new_v12_inference_claimed': False,
            'receipt_recovery_is_new_inference': False,
            'old_source_selection_not_rerun': True}, covered

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True, help='new exclusive directory')
    args = parser.parse_args()
    config_path = HERE / 'input-bindings.json'
    config = json.loads(config_path.read_text())
    inputs = {name: verified(entry) for name, entry in config['inputs'].items()}
    proof, v9_entry = static_code_proof(config)
    ids = json.loads(inputs['frame_ids'])['approved_record_ids']
    if len(ids) != 4481 or len(set(ids)) != len(ids):
        raise ValueError('Frame not the bound complete 4481')
    packets = json.loads(inputs['current_packet_metadata'])
    bundles = [json.loads(line) for line in inputs['current_common_source'].splitlines()]
    lineage = [json.loads(line) for line in inputs['rule_execution_lineage'].splitlines()]
    if len(packets) != 4481 or [p['source_id'] for p in packets] != ids or [b['source_record']['id'] for b in bundles] != ids or [r['id'] for r in lineage] != ids:
        raise ValueError('Frame/source/packet/lineage ID coverage or order differs')
    inherited, old_exclusions = inherited_compatibility(config, ids, lineage)
    rows, selected, counts = [], [], collections.Counter()
    for rid, bundle, meta, origin in zip(ids, bundles, packets, lineage):
        packet_bytes = verified(meta)
        packet = json.loads(packet_bytes)
        body = canonical(bundle)
        if (packet['source_id'] != rid or packet['source_bundle'] != bundle or
                packet['source_bundle_sha256'] != sha(body) or meta['source_bundle_sha256'] != sha(body) or
                meta['source_bundle_utf8_bytes'] != len(body)):
            raise ValueError('Current packet/common row not identical: ' + rid)
        reasons = source_gate(bundle, v9_entry)
        if not proof['passed']:
            reasons['full_scope_fallback_code_proof_not_established'] = True
        if reasons:
            selected.append(rid)
        counts.update(reasons.keys())
        rows.append({'id': rid, 'selected': bool(reasons), 'static_reasons': reasons,
                     'current_packet_sha256': meta['sha256'], 'current_source_bundle_sha256': sha(body),
                     'actual_production_algorithm': origin['actual_inference_algorithm'],
                     'actual_production_run': origin['actual_run_directory'],
                     'actual_prediction_line_sha256': origin['actual_prediction_line_sha256'],
                     'inherited_through_adopted_static_exclusion_stages': old_exclusions[rid],
                     'off_gate_noop_certificate': None if reasons else {
                         'S_scope_masks_are_identity': True,
                         'S_current_and_direct_parent_risk_helpers_are_false': True,
                         'F_changed_structured_plan_suffix_unreachable': True,
                         'all_original_functions_AST_unchanged_except_proved_noops': proof['passed'],
                         'same_current_bound_packet_required': True}})
    summary = {
        'schema': 'v12-SF-static-population-impact-preparation-v1',
        'status': 'candidate_for_ROOT_review_not_adopted',
        'frame_N': len(ids), 'selected_N': len(selected), 'unselected_N': len(ids) - len(selected),
        'reason_counts_overlap_not_sum': dict(sorted(counts.items())),
        'selected_record_ids': selected,
        'unselected_record_ids': [r['id'] for r in rows if not r['selected']],
        'current_production_actual_algorithm_counts': dict(collections.Counter(r['actual_inference_algorithm'] for r in lineage)),
        'current_source_packet_binding_verified_N': len(rows),
        'source_input_changed_relative_to_current_v16': False,
        'classification_executed': False, 'predictions_parsed': False, 'human_reference_read': False,
        'production_modified': False, 'ROOT_adoption': False,
        'allowed_candidate_change_dimensions': ['S', 'F'],
        'required_unchanged_complete_decisions': ['E', 'Ec', 'I'],
        'unselected_equivalence_basis': 'v12 versus complete v11 on identical current v16 input; reuse actual mixed production via existing adopted compatible lineage, never relabel as fresh v12 execution',
        'proof': proof,
        'adopted_mixed_production_compatibility': inherited,
        'bindings': {'input_config': binding(config_path), 'selector': binding(__file__),
                     'input_files': config['inputs'], 'algorithm_files': config['algorithm_bindings']},
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'selection.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    (args.out / 'record-scope.jsonl').write_bytes(b''.join(canonical(row) + b'\n' for row in rows))
    print(json.dumps({k: summary[k] for k in ('frame_N', 'selected_N', 'unselected_N', 'reason_counts_overlap_not_sum', 'proof')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
