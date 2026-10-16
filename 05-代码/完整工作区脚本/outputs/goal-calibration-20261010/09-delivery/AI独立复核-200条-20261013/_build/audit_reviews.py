from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / '独立真人判读-200条-20261013'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


class Material(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.current = []
        self.depth = 0
        self.current_depth = None

    def handle_starttag(self, tag, attrs):
        if tag not in ('meta', 'link', 'img', 'br', 'hr', 'input'):
            self.depth += 1
        if dict(attrs).get('id') == 'current-body':
            self.current_depth = self.depth

    def handle_endtag(self, tag):
        if self.current_depth == self.depth:
            self.current_depth = None
        self.depth -= 1

    def handle_data(self, data):
        self.text.append(data)
        if self.current_depth is not None:
            self.current.append(data)


def norm(text):
    return re.sub(r'\s+', '', text)


def main():
    report = {'reviewers': {}, 'source_preserved': True, 'source_changes': []}
    manifest = json.loads((ROOT / '_build/source-preservation.json').read_text())
    for item in manifest['source_files']:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            report['source_preserved'] = False
            report['source_changes'].append(item['path'])
    for who in 'AB':
        path = ROOT / f'AI复核者{who}/predictions.json'
        if not path.exists():
            report['reviewers'][who] = {'status': 'not submitted'}
            continue
        data = json.loads(path.read_text())
        assert isinstance(data, list), f'{who}: root must be a list'
        ids = [r['blind_id'] for r in data]
        expected = {f'{who}-{n:03d}' for n in range(1, 201)}
        assert len(ids) == len(set(ids)) == 200 and set(ids) == expected, f'{who}: missing or duplicate IDs'
        counts = {d: {'0': 0, '1': 0, 'null': 0} for d in DIMS}
        quote_flags = []
        context_flags = []
        no_quoted_anchor = []
        material_text = {}
        for row in data:
            blind_id = row['blind_id']
            html = (SOURCE / f'发给编码者{who}/材料/{blind_id}.html').read_text()
            parsed = Material()
            parsed.feed(html)
            full_text = norm(''.join(parsed.text))
            material_text[blind_id] = ''.join(parsed.current)
            assert set(row['judgments']) == set(DIMS), f'{blind_id}: wrong dimensions'
            for dim in DIMS:
                item = row['judgments'][dim]
                val = item['value']
                assert val is None or type(val) is int and val in (0, 1), f'{blind_id}/{dim}: invalid value'
                reason = item['reason']
                assert isinstance(reason, str) and len(reason.strip()) >= 10, f'{blind_id}/{dim}: empty or inadequate reason'
                if val is None:
                    assert reason.startswith('待定：'), f'{blind_id}/{dim}: pending reason must identify missing material or conflict'
                counts[dim]['null' if val is None else str(val)] += 1
                refs = re.findall(r'CTX-[0-9a-f]+', reason)
                for ref in refs:
                    if ref not in html:
                        context_flags.append({'blind_id': blind_id, 'dimension': dim, 'reference': ref})
                quotes = re.findall(r'“([^”]+)”|‘([^’]+)’|「([^」]+)」', reason)
                quotes = [next(q for q in group if q) for group in quotes]
                source_quotes = [q for q in quotes if len(norm(q)) >= 4 and norm(q) in full_text]
                if not source_quotes:
                    no_quoted_anchor.append({'blind_id': blind_id, 'dimension': dim, 'reason': reason})
                for quote in quotes:
                    if len(norm(quote)) >= 7 and norm(quote) not in full_text:
                        quote_flags.append({'blind_id': blind_id, 'dimension': dim, 'quote': quote, 'reason': reason})
        report['reviewers'][who] = {
            'status': 'submitted', 'records': len(data), 'judgments': len(data) * 5,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'counts': counts,
            'unmatched_quoted_phrases': quote_flags, 'unknown_context_ids': context_flags,
            'no_literal_quoted_anchor': no_quoted_anchor,
        }
        (ROOT / f'_build/current-text-{who}.json').write_text(json.dumps(material_text, ensure_ascii=False, indent=2))
    output = ROOT / '_build/review-audit.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({who: {k: v for k, v in summary.items() if k in ('status', 'records', 'judgments', 'counts')} | {k: len(v) for k, v in summary.items() if isinstance(v, list)} for who, summary in report['reviewers'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
