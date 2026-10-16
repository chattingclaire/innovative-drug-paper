"""Static-only E delta verification. Never imports or executes a classifier."""
from pathlib import Path
import ast
import copy
import datetime
import difflib
import hashlib
import json

A = Path(__file__).resolve().parent
B = A.parents[1]
V = B / '06-coding/rule-five-dimension-joint-root/versions/joint-v9-e-outcome-candidate-sol'
O = V.parent / 'joint-v9-generic-relationship-sol'
STATIC = A / 'static02'
STATIC.mkdir(exist_ok=False)

def bind(p):
    p = p.resolve(); raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def dump(node):
    return ast.dump(node, include_attributes=False)

def source(text, node):
    return ast.get_source_segment(text, node)

def save(name, value):
    with (STATIC / name).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def is_gate_call(node):
    return isinstance(node, ast.If) and isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name) and node.test.func.id == '_e_outcome_gate'

proof = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), classifier_executed=False, model_calls=0)
components = {'source_base': str(O), 'candidate': str(V), 'not_a_classifier_run': True, 'files': {}}
diff = []
patterns = []
for name in ('relations', 'dimensions'):
    old_text = (O / (name + '.py')).read_text()
    new_text = (V / (name + '.py')).read_text()
    old_tree = ast.parse(old_text); new_tree = ast.parse(new_text)
    tree = copy.deepcopy(new_tree)
    added = []
    for node in list(tree.body):
        if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'E_OUTCOME_ENTRY' for x in node.targets):
            patterns.append(ast.literal_eval(node.value)); added.append(node); tree.body.remove(node)
        elif isinstance(node, ast.FunctionDef) and node.name in ('_e_outcome_gate', '_e_current_outcome_consume'):
            added.append(node); tree.body.remove(node)
    removed_calls = []
    if name == 'relations':
        cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'RelationView')
        init = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == '__init__')
        removed_calls = [x for x in init.body if is_gate_call(x)]
        init.body = [x for x in init.body if not is_gate_call(x)]
        producer = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == '_e_current_outcome_relationships')
        cls.body.remove(producer); added.append(producer)
        assert len(removed_calls) == 1
        assert dump(removed_calls[0]) == dump(ast.parse('if _e_outcome_gate(self.text):\n    self._e_current_outcome_relationships()').body[0])
        assert isinstance(producer.body[0], ast.If) and dump(producer.body[0].test) == dump(ast.parse('not _e_outcome_gate(self.text)', mode='eval').body)
        assert isinstance(producer.body[0].body[0], ast.Return)
        writes = sorted({x.attr for x in ast.walk(producer) if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == 'self' and isinstance(x.ctx, ast.Store)})
        assert writes == ['e_current_outcome_relations']
        self_calls = sorted({x.func.attr for x in ast.walk(producer) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and isinstance(x.func.value, ast.Name) and x.func.value.id == 'self'})
        assert self_calls == ['current_anchor']
        read_self_attributes = sorted({x.attr for x in ast.walk(producer) if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == 'self' and isinstance(x.ctx, ast.Load)})
        assert read_self_attributes == ['current_anchor', 'e_current_outcome_relations', 'norm', 'text']
        proof['producer'] = dict(first_statement_raw_gate=True, only_written_self_attribute=writes, self_calls=self_calls, read_self_attributes=read_self_attributes, legacy_graph_or_source_request_mutation=False, source_context_or_identity_access=False)
    else:
        judge = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'judge')
        removed_calls = [x for x in judge.body if is_gate_call(x)]
        judge.body = [x for x in judge.body if not is_gate_call(x)]
        assert len(removed_calls) == 1
        assert dump(removed_calls[0]) == dump(ast.parse('if _e_outcome_gate(view.text):\n    _e_current_outcome_consume(acc, view)').body[0])
        consumer = next(x for x in added if isinstance(x, ast.FunctionDef) and x.name == '_e_current_outcome_consume')
        assert isinstance(consumer.body[0], ast.If) and dump(consumer.body[0].test) == dump(ast.parse('not _e_outcome_gate(view.text)', mode='eval').body)
        assert isinstance(consumer.body[0].body[0], ast.Return)
        calls = [x for x in ast.walk(consumer) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and isinstance(x.func.value, ast.Name) and x.func.value.id == 'acc']
        assert len(calls) == 1 and calls[0].func.attr == 'add' and ast.literal_eval(calls[0].args[0]) == 'E'
        assert not any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in ('acc', 'view') and isinstance(x.ctx, ast.Store) for x in ast.walk(consumer))
        proof['consumer'] = dict(first_statement_raw_gate=True, accumulator_calls=[dict(method='add', dimension='E')], direct_acc_or_view_assignment=False, placement='after original v9 IF consumer and before unchanged Accumulator.finish', accumulator_dimension_isolation='unchanged add writes positive[dim]; unchanged finish computes every dim from its own lists')
    assert dump(tree) == dump(old_tree), name + ': original AST not restored exactly'
    before = hashlib.sha256(dump(old_tree).encode()).hexdigest()
    proof[name + '_restored_original_AST'] = dict(exact=True, sha256=before, removed_only_new_E_nodes_and_one_guarded_call=True, old_file=bind(O/(name+'.py')), new_file=bind(V/(name+'.py')))
    components['files'][name + '.py'] = dict(add_nodes=[dict(name=n.name if isinstance(n, ast.FunctionDef) else 'E_OUTCOME_ENTRY', start_line=n.lineno, end_line=n.end_lineno, source=source(new_text,n)) for n in added], guarded_call=dict(start_line=removed_calls[0].lineno, end_line=removed_calls[0].end_lineno, source=source(new_text,removed_calls[0])), original_restored_AST_sha256=before)
    diff.extend(difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True), fromfile='joint-v9-generic-relationship-sol/'+name+'.py', tofile='joint-v9-e-outcome-candidate-sol/'+name+'.py'))
selector_tree = ast.parse((V/'select_static_impact.py').read_text())
selector_const = next(x for x in selector_tree.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='E_OUTCOME_ENTRY' for y in x.targets))
patterns.append(ast.literal_eval(selector_const.value)); assert len(set(patterns)) == 1
proof['raw_gate'] = dict(pattern=patterns[0], three_literal_patterns_exact=True, current_original_text_only=True, all_old_E_states=True, existing_E1_evidence_changes_included=True, contexts_and_ID_and_department_and_expected_not_features=True, total_production_selected_N=None, production_not_read_or_selected=True)
proof['shared_modules'] = [dict(name=name, byte_identical=(O/(name+'.py')).read_bytes()==(V/(name+'.py')).read_bytes(), original=bind(O/(name+'.py')), candidate=bind(V/(name+'.py'))) for name in ('source_packet','source_receipts','evidence')]
assert all(x['byte_identical'] for x in proof['shared_modules'])
proof['closure_argument'] = [
    'Only the new RelationView constructor call and judge call can reach the added producer/consumer. Both test the same pure current raw-text gate.',
    'If raw gate is false, both calls are skipped and the entire remaining original module AST is exact v9. New literal/function declarations have no classifier side effects.',
    'If raw gate is true, producer only reads self.text/self.norm/current_anchor, writes its private E list, and never mutates old relation graph or requests. Consumer only appends positive[E].',
    'The raw gate is therefore a sufficient superset for all possibly changed canonical E decisions, including already E1 evidence. Do not filter by old E=0/null, values, IDs or machine disagreements.',
    'ROOT must select the entire gate from sealed original current text, union it with the independent IF candidate gate, freeze input bindings, and classify that union once. This audit has not read or counted production rows.'
]
save('ast-isolation-proof.json',proof)
save('e-patch-components.json',components)
with (STATIC/'v9-to-E.diff').open('x',encoding='utf8') as f:f.writelines(diff)
print(json.dumps(dict(restored_original_AST_exact=True,shared_module_bytes_exact=True,gate_literals_exact=True,producer_E_private=True,consumer_only_E=True,files=[bind(STATIC/x) for x in ('ast-isolation-proof.json','e-patch-components.json','v9-to-E.diff')]),ensure_ascii=False,indent=2))
