"""Compose the two bounded residual repairs without executing either classifier."""
from pathlib import Path
import importlib.util
import json
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('compose_only', HERE / 'merge_candidates.py')
compose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compose)
BASE = compose.OUT
OUT = compose.VERSIONS / 'joint-v15b-complete-repair-root'
MANIFEST = HERE / 'composition-complete.json'


def main():
    assert not OUT.exists() and not MANIFEST.exists()
    first = json.loads((HERE / 'composition.json').read_text())
    for item in first['output']:
        assert compose.binding(Path(item['path'])) == item
    summaries = {}
    sources = {}
    for domain in ('S', 'F'):
        path = HERE / (domain + '-residual') / 'candidate-summary.json'
        summary = json.loads(path.read_text())
        candidate = summary.get('candidate_directory') or summary.get('candidate')
        assert isinstance(candidate, str) and Path(candidate).is_dir()
        code = summary['code']
        assert len(code) == len(compose.NAMES)
        for item in code:
            actual = compose.binding(Path(item['path']))
            assert all(actual[k] == item[k] for k in ('path', 'bytes', 'sha256'))
            assert Path(item['path']).parent == Path(candidate)
        parent = summary.get('base_code') or summary['base']
        assert isinstance(parent, list) and len(parent) == len(compose.NAMES)
        for item in parent:
            actual = compose.binding(BASE / Path(item['path']).name)
            assert all(actual[k] == item[k] for k in ('path', 'bytes', 'sha256'))
        sources[domain] = Path(candidate)
        summaries[domain] = compose.binding(path)
    compose.BASE, compose.OUT, compose.SOURCES = BASE, OUT, sources
    prepared = {name: compose.compose(name) for name in compose.NAMES}
    OUT.mkdir()
    for name, (value, _) in prepared.items():
        (OUT / (name + '.py')).write_text(value)
    manifest = {
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'composed_isolated_complete_candidate_not_executed_not_adopted',
        'builder': compose.binding(Path(__file__)),
        'composition_helper': compose.binding(HERE / 'merge_candidates.py'),
        'parent_composition': compose.binding(HERE / 'composition.json'),
        'base': [compose.binding(BASE / (n + '.py')) for n in compose.NAMES],
        'source_summaries': summaries,
        'sources': {d: [compose.binding(p / (n + '.py')) for n in compose.NAMES] for d, p in sources.items()},
        'output': [compose.binding(OUT / (n + '.py')) for n in compose.NAMES],
        'changes': {n: edits for n, (_, edits) in prepared.items()},
        'all_changes_are_disjoint_source_edits': True,
        'classifier_calls': 0, 'model_calls': 0, 'production_adopted': False,
    }
    with MANIFEST.open('x') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'candidate': str(OUT), 'edit_N': {n: len(e) for n, (_, e) in prepared.items()}}))


if __name__ == '__main__':
    main()
