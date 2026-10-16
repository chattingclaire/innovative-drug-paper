"""Exactly two predeclared helper-only controls; no protocol or coding runs."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import source_packet
from source_receipts import resolve_inventory, SourceReceiptIdentityError

WORK = Path(__file__).resolve().parent


def approved_care_source():
    scope = json.loads((WORK / 'source-scope-v12.json').read_text())
    binding = scope['complete_bundle_snapshot']
    data = Path(binding['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != binding['sha256']:
        raise AssertionError('Sealed source-only snapshot SHA differs')
    # One approved positive source only, selected before bundle JSON decoding.
    selected = [line for line in data.splitlines() if b'"id":"RECODE25-01459"' in line]
    if len(selected) != 1: raise AssertionError('Approved source-positive identity not unique')
    bundle = json.loads(selected[0])
    if bundle['source_record']['id'] != 'RECODE25-01459': raise AssertionError('Source selection mismatch')
    return bundle, source_packet.source_inventory(bundle), scope['bindings'], scope['v12_source_base']


class MinimalSourceReceiptControls(unittest.TestCase):
    def test_positive_existing_care_payload_identity_bridge_preserves_raw_inputs(self):
        bundle, producer, bindings, base = approved_care_source()
        before_bundle, before_producer = copy.deepcopy(bundle), copy.deepcopy(producer)
        resolved, delta = resolve_inventory(bundle, producer, bindings, base)
        self.assertEqual(bundle, before_bundle)
        self.assertEqual(producer, before_producer)
        self.assertEqual(len(delta), 1)
        change = delta[0]
        self.assertIsNone(change['producer_value'])
        payload = bundle['source_full_text_resources'][0]
        self.assertEqual(change['resolved_value'], payload['source_pdf_sha256'])
        self.assertEqual(change['source_document_id'], payload['source_resource_id'])
        self.assertFalse(change['read_use_status_changed'])
        self.assertFalse(change['pixel_reading_claimed'])
        expected = copy.deepcopy(producer)
        next(item for item in expected if item['resource_id'] == change['resource_id'])['source_sha256'] = payload['source_pdf_sha256']
        self.assertEqual(resolved, expected)
        self.assertTrue(all(item['consumer_read_status'] == 'not_recorded' for item in resolved))
        self.assertEqual(change['payload_canonical_view_sha256'], producer[next(i for i, item in enumerate(producer)
                          if item['resource_id'] == change['resource_id'])]['available_views']['text'])

    def test_negative_missing_or_conflicting_identity_proof_stops_without_mutation(self):
        initial_bundle, initial_producer, initial_bindings, initial_base = approved_care_source()
        cases = ['missing_explicit_sha', 'conflicting_explicit_shas', 'conflicting_producer_sha',
                 'missing_snapshot_binding', 'unbound_payload_file', 'changed_payload_file_bytes']
        with tempfile.TemporaryDirectory(prefix='receipt-negative-', dir=WORK) as temp:
            for case in cases:
                bundle, producer, bindings, base = copy.deepcopy(initial_bundle), copy.deepcopy(initial_producer), copy.deepcopy(initial_bindings), initial_base
                payload = bundle['source_full_text_resources'][0]
                document = next(d for d in bundle['source_documents'] if d['source_resource_id'] == payload['source_resource_id'])
                inventory_entry = next(item for item in producer if item['resource_id'].startswith('FULLSOURCE-'))
                if case == 'missing_explicit_sha':
                    payload.pop('source_pdf_sha256')
                    producer = source_packet.source_inventory(bundle)
                elif case == 'conflicting_explicit_shas':
                    payload['source_sha256'] = '0' * 64
                    producer = source_packet.source_inventory(bundle)
                elif case == 'conflicting_producer_sha':
                    inventory_entry['source_sha256'] = '0' * 64
                elif case == 'missing_snapshot_binding':
                    bindings = [b for b in bindings if Path(b['path']).resolve() != Path(document['snapshot']).resolve()]
                elif case == 'unbound_payload_file':
                    document['source_text_resource']['relative_path'] = '../unbound-source-payload.json'
                elif case == 'changed_payload_file_bytes':
                    resource = document['source_text_resource']
                    original_path = Path(base) / resource['relative_path']
                    original_bytes = original_path.read_bytes()
                    path = Path(temp) / 'changed-payload.json'
                    path.write_bytes(original_bytes + b' ')
                    base = temp
                    resource['relative_path'] = path.name
                    bindings.append({'path': str(path), 'sha256': resource['sha256'], 'bytes': len(original_bytes)})
                before_bundle, before_producer = copy.deepcopy(bundle), copy.deepcopy(producer)
                with self.subTest(case=case), self.assertRaises(SourceReceiptIdentityError):
                    resolve_inventory(bundle, producer, bindings, base)
                self.assertEqual(bundle, before_bundle)
                self.assertEqual(producer, before_producer)


if __name__ == '__main__': unittest.main(verbosity=2)
