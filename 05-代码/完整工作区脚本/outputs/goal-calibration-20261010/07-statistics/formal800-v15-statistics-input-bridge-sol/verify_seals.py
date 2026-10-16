"""Check expected byte size/SHA; not certification of people, release or truth."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent


def main():
    count = 0
    for name, key in (('input-seal.json', 'inputs'), ('output-seal.json', 'members')):
        seal = json.loads((HERE / name).read_text(encoding='utf-8'))
        for member in seal[key]:
            path = Path(member['absolute_path'])
            raw = path.read_bytes()
            if len(raw) != member['bytes'] or hashlib.sha256(raw).hexdigest() != member['sha256']:
                raise ValueError('Seal mismatch: ' + str(path))
            count += 1
    print(json.dumps({'status': 'seals_match', 'verified_bindings': count,
                      'human_identity_or_source_truth_authenticated': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
