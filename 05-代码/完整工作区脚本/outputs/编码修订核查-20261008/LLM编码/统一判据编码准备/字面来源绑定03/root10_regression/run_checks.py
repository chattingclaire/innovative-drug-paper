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
CODE = Path('/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/统一判据编码准备/字面来源绑定03/literal_source_binder.py')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
design = json.loads((HERE / 'design.json').read_text())
assert sha(CODE) == design['binder_sha256']
spec = importlib.util.spec_from_file_location('root_independent_binder01', CODE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
output = HERE / 'actual_execution.json'
assert not output.exists(), 'Preserve every actual first execution.'
results = []
with tempfile.TemporaryDirectory(prefix='root-independent-literal-') as tmp:
    for case in design['checks']:
        folder = Path(tmp) / case['name']; folder.mkdir()
        leaf = 'The medicine improves patient survival.'
        source = folder / 'actual.txt'
        source.write_text(leaf)
        generic = folder / 'generic.txt'; generic.write_text('Separate declared generic source.')
        candidate = folder / 'candidate.json'
        para = leaf
        source_locator = {}
        candidate_locator = {'leaf_scope': 'unit', 'unit_id': 'u-independent', 'paragraph_id': 'p-independent'}
        additional = [{'path': str(source), 'sha256': sha(source)}]
        name = case['name']
        if name == 'additional_source_wrong_sha':
            additional[0]['sha256'] = '0' * 64
        elif name == 'additional_source_identity_without_literal':
            source.write_text('The selected file contains a different statement.')
            additional[0]['sha256'] = sha(source)
        elif name == 'source_punctuation_change_not_whitespace':
            source.write_text('The medicine improves patient survival;')
            additional[0]['sha256'] = sha(source)
        elif name.startswith('docx_'):
            source = folder / 'actual.docx'
            if name == 'docx_normal_native_paragraph':
                body = '<w:p><w:r><w:t>' + leaf + '</w:t></w:r></w:p>'
            else:
                body = '<w:p><w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>' + leaf + '</w:t></w:r></w:p></w:txbxContent></w:drawing></w:r></w:p>'
            xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '</w:body></w:document>'
            with zipfile.ZipFile(source, 'w') as package:
                package.writestr('word/document.xml', xml)
            additional = [{'path': str(source), 'sha256': sha(source)}]
            if name == 'docx_textbox_filtered_outer_paragraph':
                source_locator['xml_paragraph_index'] = 0
        elif name == 'html_unique_native_node':
            source = folder / 'actual.html'
            source.write_text('<html><body><p>' + leaf + '</p></body></html>')
            additional = [{'path': str(source), 'sha256': sha(source)}]
        elif name.startswith('duplicate_'):
            para = leaf + '\n' + leaf
            source.write_text(para)
            additional = [{'path': str(source), 'sha256': sha(source)}]
            if name == 'duplicate_occurrence_explicit_native_positions':
                candidate_locator['unit_start_in_paragraph'] = len(leaf) + 1
                source_locator['char_start'] = len(leaf) + 1
        payload = {'source': str(generic), 'source_sha256': sha(generic), 'additional_sources': additional,
                   'unit_candidates': [{'id': 'u-independent', 'text': leaf, 'paragraph_id': 'p-independent'}],
                   'paragraphs': [{'id': 'p-independent', 'text': para}]}
        candidate.write_text(json.dumps(payload))
        inputs = {'record_id': name, 'raw_pointer': '/text',
                  'source_identity': {'source': str(source), 'source_sha256': sha(source)},
                  'candidate_identity': {'candidate_file': str(candidate), 'candidate_sha256': sha(candidate)},
                  'candidate_locator': candidate_locator, 'source_locator': source_locator,
                  'allow_whitespace_normalization': True}
        before = copy.deepcopy(inputs)
        binding = mod.bind_leaf(leaf, **inputs)
        assert inputs == before
        bound = binding['status'] in {mod.BOUND, mod.GRID_BOUND}
        results.append({'name': name, 'expected_bound': case['expected_bound'], 'actual_bound': bound,
                        'passed': bound == case['expected_bound'], 'binding': binding, 'input_unchanged': True})
assert sha(CODE) == design['binder_sha256']
report = {'scope': design['scope'], 'design_sha256': sha(HERE / 'design.json'), 'implementation_sha256': sha(CODE),
          'implementation_unchanged': True, 'authenticators_mocked': False, 'actual_policy_leaves_bound': 0,
          'checks': results, 'passed': all(r['passed'] for r in results)}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': [{'name': r['name'], 'passed': r['passed'], 'reasons': r['binding']['reasons']} for r in results], 'output_sha256': sha(output)}, ensure_ascii=False))
