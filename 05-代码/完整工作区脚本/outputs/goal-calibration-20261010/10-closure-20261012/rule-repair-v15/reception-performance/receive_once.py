"""Run the original complete receiver with one fixed material-index cache.

No classification, inventory, file-content, event or decision result is cached.
Original frozen files remain unchanged. This wrapper is itself bound in the
received status, which is then covered by the original receiver's output seal.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / 'execution-preparation-technical-repair01/receive_merge.py'


def same_plain_value(actual, expected):
    """Full JSON value equality, including types (1.0/True cannot equal 1)."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            same_plain_value(a, b) for a, b in zip(actual, expected))
    if type(expected) is dict:
        return (len(actual) == len(expected)
                and all(type(key) is str for key in actual)
                and actual.keys() == expected.keys()
                and all(same_plain_value(actual[key], value)
                        for key, value in expected.items()))
    if type(expected) in (str, int, float, bool, type(None)):
        return actual == expected
    return False


class FixedMaterialIndex:
    """Cache only the original _bindings result for the complete fixed list."""

    def __init__(self, original, fixed_materials):
        self.original = original
        self.fixed_materials = copy.deepcopy(fixed_materials)
        self.cached = None
        self.counts = {
            'calls': 0, 'cache_hits': 0, 'fixed_index_builds': 0,
            'nonmatching_original_validations': 0,
            'original_validation_calls': 0, 'original_validation_rejections': 0,
        }

    @staticmethod
    def independent_index(index):
        # Path keys are immutable; each binding value and the container are new.
        return {path: copy.deepcopy(entry) for path, entry in index.items()}

    def __call__(self, entries):
        self.counts['calls'] += 1
        fixed = same_plain_value(entries, self.fixed_materials)
        if fixed and self.cached is not None:
            self.counts['cache_hits'] += 1
            return self.independent_index(self.cached)
        self.counts['original_validation_calls'] += 1
        if not fixed:
            self.counts['nonmatching_original_validations'] += 1
        try:
            result = self.original(entries)
        except Exception:
            self.counts['original_validation_rejections'] += 1
            raise
        if fixed:
            self.cached = self.independent_index(result)
            self.counts['fixed_index_builds'] += 1
            return self.independent_index(self.cached)
        return result


def load_receiver():
    sys.path.insert(0, str(ORIGINAL.parent))
    spec = importlib.util.spec_from_file_location('unchanged_complete_receiver', ORIGINAL)
    receiver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(receiver)
    return receiver


def receive_once(scope_path, run_path, output_path, validate_only=False):
    if not __debug__:
        raise RuntimeError('Original exact binding assertions must remain active')
    receiver = load_receiver()
    scope_path = Path(scope_path).resolve()
    output_path = Path(output_path).resolve()
    scope = receiver.load(scope_path)
    receiver.validate_full_scope(scope)
    scope_binding = receiver.bind(scope_path)
    wrapper_binding = receiver.bind(__file__)
    receiver_binding = receiver.bind(ORIGINAL)
    materials = copy.deepcopy(scope['material_bindings'])
    material_rechecks = {'before_original_receiver': 0, 'before_status_commit': 0,
                         'after_validate_only': 0}

    def recheck_materials(stage):
        receiver.exact(scope_binding)
        receiver.exact(wrapper_binding)
        receiver.exact(receiver_binding)
        for entry in materials:
            receiver.exact(entry)
        material_rechecks[stage] += 1

    recheck_materials('before_original_receiver')
    original_loader = receiver.rule_driver.load_frozen_coders
    original_save = receiver.save
    installed = []

    def cached_loader(implementation, code):
        modules = original_loader(implementation, code)
        if installed:
            raise ValueError('Original frozen coder loader invoked more than once')
        receipts = modules['source_receipts']
        index = FixedMaterialIndex(receipts._bindings, materials)
        installed.append((receipts, receipts._bindings, index))
        receipts._bindings = index
        return modules

    def metadata():
        if len(installed) != 1:
            raise ValueError('Fixed-index wrapper was not installed exactly once')
        return {
            'role': 'fixed_material_binding_index_cache_only',
            'wrapper_binding': wrapper_binding,
            'original_receiver': receiver_binding,
            'actual_scope': scope_binding,
            'fixed_material_binding_N': len(materials),
            'cache_key': 'complete_fixed_material_list_type_strict_deep_equality',
            'cache_counts': dict(installed[0][2].counts),
            'original_material_file_reads_and_hashes_preserved': True,
            'original_per_record_checks_preserved': True,
            'inventory_or_event_or_file_content_cache': False,
            'classifier_calls': 0,
            'model_calls': 0,
            'extra_material_rechecks': dict(material_rechecks),
            'commit_recheck_boundary': 'before_composite_status_save; failure leaves partial output unsealed',
        }

    def transparent_save(path, value):
        if Path(path).resolve() == output_path / 'composite-status.json':
            recheck_materials('before_status_commit')
            if value.get('receiver') != receiver_binding or value.get('current_scope') != scope_binding:
                raise ValueError('Original receiver/scope status binding differs')
            if 'wrapper_binding' in value or 'reception_performance' in value:
                raise ValueError('Do not replace existing receiver provenance')
            value = {**value, 'wrapper_binding': wrapper_binding,
                     'reception_performance': metadata()}
        original_save(path, value)

    receiver.rule_driver.load_frozen_coders = cached_loader
    receiver.save = transparent_save
    try:
        result = receiver.receive(scope_path, run_path, output_path, validate_only)
        if validate_only:
            recheck_materials('after_validate_only')
        elif material_rechecks['before_status_commit'] != 1:
            raise ValueError('Original received status did not pass the extra commit recheck')
        return {**result, 'wrapper_binding': wrapper_binding,
                'reception_performance': metadata()}
    finally:
        receiver.rule_driver.load_frozen_coders = original_loader
        receiver.save = original_save
        for module, original, _ in installed:
            module._bindings = original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', required=True)
    parser.add_argument('--run', '--delta', dest='run', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    result = receive_once(args.scope, args.run, args.output, args.validate_only)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
