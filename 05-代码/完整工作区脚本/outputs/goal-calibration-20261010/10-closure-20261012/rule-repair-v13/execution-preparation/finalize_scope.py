"""Bind a ROOT-supplied existing-format release; never create release/adoption."""
import argparse
import copy
from pathlib import Path
from merge_common import bind, exact, load, save
import rule_driver


def finalize(release_path, expected_sha, scope_output):
    h = Path(__file__).resolve().parent
    template = load(h/'release.UNRELEASED.json')
    scope = load(h/'scope.UNRELEASED.json')
    release = load(release_path)
    release_binding = bind(release_path)
    if release_binding['sha256'] != expected_sha:
        raise ValueError('Explicit ROOT release SHA differs')
    if release.get('status') != 'released_for_production_provisional' or not release.get('authorization_id'):
        raise ValueError('No actual external production_provisional release')
    for key, value in template.items():
        if key not in {'status', 'authorization_id', 'approval_created_by_this_preparation'} and release.get(key) != value:
            raise ValueError('ROOT release differs from reviewed preparation: ' + key)
    for entry in release['implementation_bindings']:
        exact(entry)
    scope = copy.deepcopy(scope)
    old_release = scope['release']
    scope.update(status='frozen_for_execution', authorization_id=release['authorization_id'], release=release_binding)
    scope['material_bindings'] = [release_binding if x == old_release else x for x in scope['material_bindings']]
    rule_driver.validate_sf_scope(scope)
    save(scope_output, scope)
    return bind(scope_output)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--release', required=True);p.add_argument('--release-sha256', required=True)
    p.add_argument('--scope-out', required=True)
    a=p.parse_args()
    print(finalize(a.release, a.release_sha256, a.scope_out))
