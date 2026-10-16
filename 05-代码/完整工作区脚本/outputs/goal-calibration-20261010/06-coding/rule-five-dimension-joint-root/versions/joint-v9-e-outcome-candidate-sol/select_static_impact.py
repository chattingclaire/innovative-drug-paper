"""Pure necessary current-raw-text impact gate; importing never classifies or reads inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
E_OUTCOME_ENTRY = '完\\s*全\\s*应\\s*答\\s*率|部\\s*分\\s*应\\s*答\\s*率|客\\s*观\\s*应\\s*答\\s*率|完\\s*全\\s*缓\\s*解\\s*率|部\\s*分\\s*缓\\s*解\\s*率|客\\s*观\\s*缓\\s*解\\s*率'

def matches(text):
    if not isinstance(text, str):
        raise TypeError('Current original text must be an actual string')
    return bool(re.search(E_OUTCOME_ENTRY, text))

def select(source, output):
    p = Path(source).resolve()
    raw = p.read_bytes()
    rows = []
    for index, line in enumerate(raw.splitlines()):
        if not line.strip():
            continue
        obj = json.loads(line)
        text = obj.get('text')
        if text is None:
            text = obj.get('source_record', {}).get('text')
        if not isinstance(text, str):
            raise ValueError('Source row does not expose current raw text; do not substitute context or predictions')
        if matches(text):
            rows.append({'line_index_0based': index, 'record_identity_metadata_only': obj.get('id', obj.get('source_id')), 'current_text_sha256': hashlib.sha256(text.encode()).hexdigest()})
    result = {'source': {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}, 'gate_pattern': E_OUTCOME_ENTRY, 'selected_N': len(rows), 'selected': rows, 'classifier_executed': False, 'all_E_states_selected': True, 'not_semantic_acceptance': True}
    with Path(output).open('x', encoding='utf8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2);f.write('\n')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-jsonl', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(select(a.source_jsonl, a.output), ensure_ascii=False))
