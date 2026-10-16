"""Machine-only full normalized reserved-sentence guard; never emits needles."""
import json
import unicodedata
from pathlib import Path
import hashlib


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_with_offsets(text):
    chars = []
    offsets = []
    for i, raw in enumerate(text):
        for c in unicodedata.normalize('NFKC', raw):
            if not c.isspace() and not unicodedata.category(c).startswith('P'):
                chars.append(c)
                offsets.append(i)
    return ''.join(chars), offsets


class ReservedRedactor:
    def __init__(self, root):
        self.metadata_path = Path(root)/'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
        self.text_path = Path(root)/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl'
        ids = set(json.loads(self.metadata_path.read_text())['all_registered_members_of_reserved_families_unit_ids'])
        self.needles = []
        found = set()
        for line in self.text_path.open():
            row = json.loads(line)
            rid = row.get('id')
            if rid in ids:
                normalized, _ = normalized_with_offsets(row['text'])
                assert normalized
                self.needles.append((rid, normalized))
                found.add(rid)
        assert len(ids) == 267 and found == ids
        self.contacts = []
        self.bindings = {'reserved_n': len(ids), 'metadata_sha256': digest_file(self.metadata_path), 'text_source_sha256': digest_file(self.text_path), 'normalization': 'per-character NFKC; remove whitespace and Unicode punctuation; exact full normalized reserved unit substring; merge overlapping spans'}

    def text(self, value, owner, path):
        norm, offsets = normalized_with_offsets(value)
        spans = []
        for rid, needle in self.needles:
            start = 0
            while True:
                at = norm.find(needle, start)
                if at < 0:
                    break
                a, b = offsets[at], offsets[at+len(needle)-1]+1
                spans.append((a, b))
                self.contacts.append({'owner': owner, 'reserved_id': rid, 'field_path': path, 'matched_full_normalized_sentence': True})
                start = at + 1
        if not spans:
            return value
        merged = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for a, b in reversed(merged):
            value = value[:a] + '[预留完整原句已机械遮蔽]' + value[b:]
        return value

    def walk(self, obj, owner='', path='$'):
        if isinstance(obj, str):
            return self.text(obj, owner, path)
        if isinstance(obj, list):
            return [self.walk(x, owner, path+'['+str(i)+']') for i, x in enumerate(obj)]
        if isinstance(obj, dict):
            return {k: self.walk(v, owner, path+'.'+k) for k, v in obj.items()}
        return obj
