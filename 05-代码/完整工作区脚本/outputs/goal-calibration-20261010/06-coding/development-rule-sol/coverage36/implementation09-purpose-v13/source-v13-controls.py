"""Exactly two predeclared source-only v13 controls; no judge imports."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
SCOPE_PATH = HERE / 'source-scope-v13.json'
spec = importlib.util.spec_from_file_location('candidate_source_packet', HERE / 'source_packet.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def exact_file(entry):
    data = Path(entry.get('path', entry.get('absolute_path'))).read_bytes()
    assert len(data) == entry['bytes'] and digest(data) == entry['sha256']
    return data


def selected_bundles(data, approved):
    result = {}
    for line in data.splitlines():
        if not line.strip():
            continue
        ids = set(re.findall(rb'"id"\s*:\s*"(RECODE25-[0-9]{5})"', line))
        assert len(ids) == 1
        rid = ids.pop().decode('ascii')
        if rid not in approved:
            continue
        bundle = json.loads(line)
        assert bundle['source_record']['id'] == rid and rid not in result
        result[rid] = bundle
    return result


def pure_function(path, name, namespace):
    tree = ast.parse(Path(path).read_bytes())
    function = next(z for z in tree.body if isinstance(z, ast.FunctionDef) and z.name == name)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class SourceV13Controls(unittest.TestCase):
    def test_finite77_matches_official_extension_and_truthful_inventory(self):
        scope = json.loads(SCOPE_PATH.read_bytes())
        approved = set(scope['approved_record_ids'])
        self.assertEqual(len(approved), 77)
        bundles = reader.load_scope(SCOPE_PATH)
        self.assertEqual([z['source_record']['id'] for z in bundles], scope['approved_record_ids'])
        self.assertEqual(digest((canonical(bundles) + '\n').encode()), scope['complete_bundles_canonical_sha256'])
        snapshot = selected_bundles(exact_file(scope['complete_bundle_snapshot']), approved)
        old = selected_bundles(exact_file(scope['base_v12_complete_bundle_snapshot']), approved)
        old_spec = importlib.util.spec_from_file_location('original_v12_source_packet', HERE / 'source_packet-before-v13.py')
        old_reader = importlib.util.module_from_spec(old_spec)
        old_spec.loader.exec_module(old_reader)
        base = Path(scope['v13_source_base'])
        bindings = {z['path']: z for z in scope['bindings']}
        official = selected_bundles(exact_file(bindings[str(base / 'affected-common-source-bundles.jsonl')]), approved)
        self.assertTrue(official)
        ns = {'copy': copy, 'cj': canonical, 'h': lambda text: digest(text.encode())}
        old_inventory = pure_function(Path(scope['v12_source_base']) / 'source_only_interface_v12.py', 'source_inventory', ns)
        ns['_base'] = types.SimpleNamespace(source_inventory=old_inventory)
        official_inventory = pure_function(base / 'source_only_interface_v13.py', 'source_inventory', ns)
        for bundle in bundles:
            rid = bundle['source_record']['id']
            self.assertEqual(bundle, snapshot[rid])
            self.assertEqual(bundle['source_record'], old[rid]['source_record'])
            if rid in official:
                self.assertEqual(bundle, official[rid])
                self.assertEqual(set(bundle) - set(old[rid]), {'source_bundle_extension'})
                for key, value in old[rid].items():
                    if key in ('explicit_or_primary_source_resources', 'source_full_text_resources'):
                        self.assertEqual(bundle[key][:len(value)], value)
                    else:
                        self.assertEqual(bundle[key], value)
            else:
                self.assertEqual(bundle, old[rid])
            inventory = reader.source_inventory(bundle)
            self.assertEqual(inventory, official_inventory(bundle))
            before = canonical(bundle)
            unit = reader.semantic_unit(bundle)
            self.assertEqual(canonical(bundle), before)
            self.assertEqual(unit['contexts'][:len(bundle['source_record']['contexts'])], bundle['source_record']['contexts'])
            old_unit = old_reader.semantic_unit(old[rid])
            self.assertEqual(unit['contexts'][:len(old_unit['contexts'])], old_unit['contexts'])
            for context_id, old_origin in old_unit['derived_context_origins'].items():
                self.assertEqual(unit['derived_context_origins'][context_id], old_origin)
            paragraphs = [z for z in bundle['source_full_text_resources']
                          if z.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML']
            for paragraph in paragraphs:
                entry = next(z for z in inventory if z['resource_id'] == paragraph['source_resource_id'])
                self.assertEqual(entry['available_views'], {'text': digest(paragraph['text'].encode())})
                self.assertEqual(entry['locator'], paragraph['source_locator'])
                self.assertNotIn('physical_page', entry['locator'])
                matches = [z for z in unit['derived_context_origins'].values()
                           if z['source_resource_id'] == paragraph['source_resource_id']]
                self.assertEqual(len(matches), 1)
                origin = matches[0]
                self.assertEqual(origin['origin_inventory_resource_id'], paragraph['source_resource_id'])
                self.assertEqual(origin['origin_inventory_view'], 'text')
                self.assertEqual(origin['origin_inventory_view_sha256'], paragraph['text_sha256'])
                self.assertEqual(origin['origin_inventory_consumption_scope'], 'complete_literal_text_view')
                context = next(z for z in unit['contexts'] if unit['derived_context_origins'].get(z['context_id']) == origin)
                self.assertEqual(context['text'], paragraph['text'])
                self.assertEqual(context['source_ref']['locator'], paragraph['source_locator'])
                self.assertEqual(context['structure']['article'], paragraph['article'])
                self.assertEqual(context['structure']['clause_index_one_based'], paragraph['clause_index_one_based'])
                self.assertEqual(context['structure']['source_role'], paragraph['role'])
        frame = bindings[str(base / 'frame-bundle-bindings.jsonl')]
        matched = {}
        for line in exact_file(frame).splitlines():
            if not line.strip(): continue
            envelope = reader._top_strings(line)
            rid = envelope.get(b'record_id', envelope.get(b'id', b'')).decode('ascii')
            if rid in approved:
                matched[rid] = json.loads(line)
        self.assertEqual(set(matched), approved)
        for bundle in bundles:
            row = matched[bundle['source_record']['id']]
            hashes = [value for key, value in row.items() if isinstance(value, str) and 'sha' in key.lower()]
            self.assertIn(digest(canonical(bundle).encode()), hashes)

    def test_missing_or_conflicting_extension_proof_stops(self):
        original = json.loads(SCOPE_PATH.read_bytes())
        base = Path(original['v13_source_base'])
        for mode in ('missing_registry_binding', 'conflicting_original_binding'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=HERE) as directory:
                scope = copy.deepcopy(original)
                if mode == 'missing_registry_binding':
                    scope['bindings'] = [z for z in scope['bindings'] if z['path'] != str(base / 'source-resource-registry.json')]
                else:
                    registry = json.loads((base / 'source-resource-registry.json').read_bytes())
                    path = registry['original_source_assets']['raw_html']['absolute_path']
                    next(z for z in scope['bindings'] if z['path'] == path)['sha256'] = '0' * 64
                candidate = Path(directory) / 'scope.json'
                candidate.write_text(json.dumps(scope, ensure_ascii=False))
                with self.assertRaises(reader.PacketInterfaceError):
                    reader.load_scope(candidate)
        self.assertEqual(json.loads(SCOPE_PATH.read_bytes()), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
