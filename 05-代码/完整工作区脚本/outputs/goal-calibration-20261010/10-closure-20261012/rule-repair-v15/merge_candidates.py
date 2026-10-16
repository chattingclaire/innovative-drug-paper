"""Compose disjoint, reviewed development changes; never dispatch a classifier.

All edits are expressed against the same v13b base. An overlap fails before any
output directory is created. The five output modules preserve all other bytes.
"""
from pathlib import Path
import ast
import difflib
import hashlib
import json
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSIONS = ROOT / '06-coding/rule-five-dimension-joint-root/versions'
BASE = VERSIONS / 'joint-v13b-clinical-safety-role-root'
SOURCES = {
    'E': VERSIONS / 'joint-v14e4-finite-standard-manual-root',
    'Ec': VERSIONS / 'joint-v14ece-finite-negotiation-geometry-root',
    'F': VERSIONS / 'joint-v14fb-form-gap-scope-root',
}
OUT = VERSIONS / 'joint-v15-E-Ec-F-integrated-root'
NAMES = ('evidence', 'source_packet', 'source_receipts', 'relations', 'dimensions')


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def compose(name):
    base_path = BASE / (name + '.py')
    base = base_path.read_text().splitlines(keepends=True)
    edits = []
    for owner, directory in SOURCES.items():
        source = (directory / (name + '.py')).read_text().splitlines(keepends=True)
        for kind, i, j, u, v in difflib.SequenceMatcher(None, base, source, autojunk=False).get_opcodes():
            if kind != 'equal':
                edits.append({'owner': owner, 'base_start': i, 'base_end': j,
                              'replacement': source[u:v], 'source_start': u, 'source_end': v})
    edits.sort(key=lambda x: (x['base_start'], x['base_end'], x['owner']))
    prior = None
    for edit in edits:
        if prior is not None:
            assert edit['base_start'] >= prior['base_end'], (name, 'overlap', prior, edit)
            assert (edit['base_start'], edit['base_end']) != (prior['base_start'], prior['base_end']), (name, 'shared insertion', prior, edit)
        prior = edit
    result, cursor = [], 0
    for edit in edits:
        result.extend(base[cursor:edit['base_start']])
        result.extend(edit['replacement'])
        cursor = edit['base_end']
    result.extend(base[cursor:])
    text = ''.join(result)
    ast.parse(text, filename=str(OUT / (name + '.py')))
    if name in ('evidence', 'source_packet', 'source_receipts'):
        assert not edits, (name, 'source/evidence protocol changed')
        assert text.encode() == base_path.read_bytes()
    return text, edits


def main():
    assert not OUT.exists(), 'Never overwrite an existing candidate'
    manifest_path = HERE / 'composition.json'
    assert not manifest_path.exists()
    prepared = {name: compose(name) for name in NAMES}
    sources = {owner: [binding(directory / (name + '.py')) for name in NAMES]
               for owner, directory in SOURCES.items()}
    OUT.mkdir()
    for name, (text, _) in prepared.items():
        (OUT / (name + '.py')).write_text(text)
    manifest = {
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'composed_isolated_candidate_not_executed_not_adopted',
        'builder': binding(Path(__file__)),
        'base': [binding(BASE / (name + '.py')) for name in NAMES],
        'sources': sources,
        'output': [binding(OUT / (name + '.py')) for name in NAMES],
        'changes': {name: edits for name, (_, edits) in prepared.items()},
        'all_changes_are_disjoint_source_edits': True,
        'classifier_calls': 0, 'model_calls': 0, 'production_adopted': False,
    }
    with manifest_path.open('x') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'candidate': str(OUT), 'edit_N': {name: len(edits) for name, (_, edits) in prepared.items()}}))


if __name__ == '__main__':
    main()
