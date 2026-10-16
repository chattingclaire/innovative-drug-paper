import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CODE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/编码修订核查-20261008/LLM编码/统一判据编码准备/字面来源绑定03/literal_source_binder.py')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract = json.loads((HERE / 'implementation_contract_before02.json').read_text())
spec = importlib.util.spec_from_file_location('root_binder02_checks', CODE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
output = HERE / 'constructed_execution02.json'
assert not output.exists()
before_code = sha(CODE)
cases = []
with tempfile.TemporaryDirectory(prefix='literal02-declared-checks-') as tmp:
    for case in contract['predeclared_checks']:
        name = case['name']; folder = Path(tmp) / name; folder.mkdir()
        source = folder / ('source.docx' if name.startswith(('textbox_', 'ordinary_')) else 'source')
        leaf = 'The outer clinical paragraph.'
        plain = '<w:p><w:r><w:t>' + leaf + '</w:t></w:r></w:p>'
        if name == 'textbox_filtered_outer_paragraph':
            body = '<w:p><w:r><w:drawing><w:txbxContent>' + plain + '</w:txbxContent></w:drawing></w:r></w:p>'
        elif name == 'ordinary_outer_body_with_unrelated_textbox':
            body = '<w:p><w:r><w:t>' + leaf + '</w:t></w:r><w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>Separate floating text.</w:t></w:r></w:p></w:txbxContent></w:drawing></w:r></w:p>'
        else:
            body = plain
        if name == 'extensionless_fake_docx':
            source.write_bytes(b'not a Word ZIP package')
        else:
            with zipfile.ZipFile(source, 'w') as package:
                package.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '</w:body></w:document>')
        identity = {'source': str(source), 'source_sha256': sha(source)}
        if name.startswith('extensionless_') and name != 'extensionless_docx_no_declaration':
            identity['format'] = 'docx'
        elif name == 'unsupported_format_object':
            identity['format'] = {'untrusted': 'not a supported enum'}
        candidate = folder / 'candidate.json'
        candidate.write_text(json.dumps({'source': str(source), 'source_sha256': sha(source),
            'unit_candidates': [{'id': 'u', 'text': leaf, 'paragraph_id': 'p'}],
            'paragraphs': [{'id': 'p', 'text': leaf}]}))
        request = {'record_id': name, 'raw_pointer': '/text', 'source_identity': identity,
                   'candidate_identity': {'candidate_file': str(candidate), 'candidate_sha256': sha(candidate)},
                   'candidate_locator': {'leaf_scope': 'unit', 'unit_id': 'u', 'paragraph_id': 'p'},
                   'source_locator': {'xml_paragraph_index': 0} if name.startswith(('textbox_', 'ordinary_')) else {}}
        original = copy.deepcopy(request)
        actual = mod.bind_leaf(leaf, **request)
        assert request == original
        bound = actual['status'] in {mod.BOUND, mod.GRID_BOUND}
        expected_bound = name in {'ordinary_outer_body_with_unrelated_textbox', 'extensionless_docx_explicit_format'}
        cases.append({'name': name, 'expected': case['expected'], 'expected_bound': expected_bound,
                      'actual_bound': bound, 'passed': bound == expected_bound, 'binding': actual})
assert sha(CODE) == before_code
preserved = all(sha(p) == h for p, h in contract['old_files_sha256'].items())
assert preserved
report = {'scope': 'Six implementation behaviour checks, not independent empirical validation.',
          'contract_sha256': sha(HERE / 'implementation_contract_before02.json'),
          'code_sha256': before_code, 'code_unchanged_during_execution': True,
          'original01_files_unchanged': preserved, 'actual_policy_leaves_bound': 0,
          'checks': cases, 'passed': all(c['passed'] for c in cases)}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': [{'name': c['name'], 'passed': c['passed'], 'reasons': c['binding']['reasons']} for c in cases], 'output_sha256': sha(output)}, ensure_ascii=False))
