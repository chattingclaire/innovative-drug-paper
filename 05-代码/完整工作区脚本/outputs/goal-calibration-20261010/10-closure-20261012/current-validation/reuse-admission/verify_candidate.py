"""Read-only bound-artifact verifier; never executes controls or statistics."""
from pathlib import Path
import argparse
import hashlib
import json


def binding(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-seal-sha', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    seal_path = here / 'output-seal.json'
    if binding(seal_path)['sha256'] != args.expected_seal_sha:
        raise ValueError('Externally reviewed seal SHA differs')
    seal = json.loads(seal_path.read_text())
    for expected in seal['members'] + seal['upstream_bindings']:
        if binding(expected['path']) != expected:
            raise ValueError('Bound file changed: ' + expected['path'])
    registry = json.loads((here / 'ROOT-registry.UNADOPTED.json').read_text())
    if registry['registrations'] != {}:
        raise ValueError('This candidate must retain an empty real ROOT registry')
    print(json.dumps({'status': 'bindings_verified', 'members': len(seal['members']),
                      'upstream_bindings': len(seal['upstream_bindings']),
                      'actual_admission': False, 'statistics_executed': False}))


if __name__ == '__main__':
    main()
