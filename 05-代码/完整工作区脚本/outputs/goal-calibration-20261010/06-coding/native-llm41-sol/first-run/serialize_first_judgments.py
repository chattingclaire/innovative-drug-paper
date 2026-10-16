"""Serialization and mechanical checks only. All dimension decisions are supplied by the AI.

No classifier, keyword rule, inference, default label, reference file, or score.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import sys
import hashlib

OUT = Path(__file__).parent
SOURCE = OUT.parent.parent / 'development-reference41-v11' / 'source.jsonl'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def write_batch(batch_path):
    source = [json.loads(x) for x in SOURCE.read_text().splitlines()]
    batch = json.loads(Path(batch_path).read_text())
    journal = OUT / 'first-judgments.jsonl'
    old = [json.loads(x) for x in journal.read_text().splitlines()] if journal.exists() else []
    assert batch['start_order'] == len(old) + 1
    rows = []
    for order, authored in enumerate(batch['records'], batch['start_order']):
        unit = source[order - 1]
        assert authored['id'] == unit['id']
        assert set(authored['dimensions']) == set(DIMS)
        contexts = {c['context_id']: c for c in unit['contexts']}
        evidence = {}
        labels = {}
        for dim in DIMS:
            d = authored['dimensions'][dim]
            assert 'value' in d and (d['value'] is None or type(d['value']) is int and d['value'] in (0, 1))
            assert d['reason'] and d['path'] and 'contexts' in d
            used = []
            for ref in d['contexts']:
                cid = ref if isinstance(ref, str) else ref['context_id']
                c = contexts[cid]
                if 'text' in c:
                    q = c['text'] if isinstance(ref, str) else ref['quote']
                    assert q and q in c['text']
                    used.append({'context_id': cid, 'quote': q, 'source_ref': c.get('source_ref'), 'structure': c.get('structure')})
                else:
                    assert isinstance(ref, str)
                    used.append({'context_id': cid, 'quote': None, 'text_status': 'absent_in_source', 'source_ref': c.get('source_ref'), 'structure': c.get('structure')})
            labels[dim] = d['value']
            evidence[dim] = {'value': d['value'], 'path': d['path'], 'current_quote': unit['text'], 'contexts_used': used, 'reason': d['reason']}
            if 'relation' in d:
                evidence[dim]['relation'] = d['relation']
        requests = authored['material_requests']
        null_dims = {dim for dim in DIMS if labels[dim] is None}
        assert null_dims <= {dim for r in requests for dim in r['dimensions']}
        row = {'id': unit['id'], 'labels': labels, 'evidence': evidence, 'material_requests': requests,
               'first_judgment': {'order': order, 'saved_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), 'semantic_author': 'single native Codex AI context', 'is_revision': False}}
        rows.append(row)
    # Append only; a successfully saved initial judgment is never replaced.
    with journal.open('a' if old else 'x', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
        f.flush()
        os.fsync(f.fileno())
    print(json.dumps({'saved_orders': [rows[0]['first_judgment']['order'], rows[-1]['first_judgment']['order']], 'total_saved': len(old)+len(rows), 'revised': 0}, ensure_ascii=False))


if __name__ == '__main__':
    write_batch(sys.argv[1])
