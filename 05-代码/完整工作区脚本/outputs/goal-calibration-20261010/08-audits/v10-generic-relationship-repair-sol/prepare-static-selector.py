from pathlib import Path
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol'
source=(V/'relations.py').read_text();import ast
tr=ast.parse(source);constant=next(x for x in tr.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='V10_REPAIR_ENTRY' for t in x.targets));pattern=ast.literal_eval(constant.value)
s=(OLD/'select_static_impact.py').read_text().replace('V9_REPAIR_ENTRY','V10_REPAIR_ENTRY').replace('_v9_','_v10_')
p=s.index('V10_REPAIR_ENTRY = ');q=s.index('\n',p);s=s[:p]+'V10_REPAIR_ENTRY = '+repr(pattern)+s[q:]
s=s.replace("    if isinstance(node, ast.Assign) and len(node.targets) == 1:","    if isinstance(node, ast.ImportFrom) and node.module == 'relations' and len(node.names)==1 and node.names[0].name=='_v10_repair_gate' and node.names[0].asname is None:\n        return True\n    if isinstance(node, ast.Assign) and len(node.targets) == 1:")
s=s.replace("        if len(entries) != 1 or ast.literal_eval(entries[0].value) != V10_REPAIR_ENTRY:","        if name == 'relations' and (len(entries) != 1 or ast.literal_eval(entries[0].value) != V10_REPAIR_ENTRY):")
s=s.replace("        if len(gate_defs) != 1 or dump(gate_defs[0]) != dump(expected_gate):", "        if name == 'relations' and len(gate_defs)==1 and gate_defs[0].body and isinstance(gate_defs[0].body[0],ast.Expr) and isinstance(gate_defs[0].body[0].value,ast.Constant) and isinstance(gate_defs[0].body[0].value.value,str):\n            gate_defs[0].body.pop(0)\n        if name == 'relations' and (len(gate_defs) != 1 or dump(gate_defs[0]) != dump(expected_gate)):")
s=s.replace("        if audit.get('approved') is not True:","        if audit.get('approved') is not True:")
s=s.replace("'mixed_baseline_equivalence_verified'","'actual_v9_baseline_compatible_verified'")
s=s.replace("'affected_records': selected,","'affected_records': selected,\n                      'selected_record_ids': [r['id'] for r in selected],\n                      'reusable_record_ids': [r['id'] for r in rows if r['id'] not in {x['id'] for x in selected}],")
s=s.replace("selected.append({'id': meta['id'], 'reasons': reasons,","selected.append({'id': meta['id'], 'packet_binding': meta['packet_binding'], 'gate_matched': any('all_new_route_effects' in x for x in reasons), 'reasons': reasons,")
s=s.replace("Not yet used on the real population.","Not used on the real population by the author. V10 current entry is dominated at every new call.")
(V/'select_static_impact.py').write_text(s)
# Export pure normalized current gate, no classifier or module import needed.
(V/'static_gate.py').write_text('"""Frozen pure V10 nomination gate; normalization matches unchanged evidence.py."""\nimport re\nimport unicodedata\nV10_REPAIR_ENTRY = '+repr(pattern)+"\n\ndef matching_current(raw):\n    joined=''.join(unicodedata.normalize('NFKC',char) for char in raw)\n    return re.sub(r'(?<=[\\u3400-\\u9fff])\\s+(?=[\\u3400-\\u9fff])','',joined)\n\ndef normalized_gate(text):\n    return bool(re.search(V10_REPAIR_ENTRY,text))\n\ndef gate(raw):\n    return normalized_gate(matching_current(raw))\n")
print('prepared static-only selector and gate export')
