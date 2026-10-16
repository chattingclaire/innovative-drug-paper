"""Exact path-bearing inventory of legacy Stage B quotable context leaves.

This deliberately preserves iter_context_text's behavior: naked strings inside
lists are not yielded, even under a recognized key. No input is modified and no
context or source field is removed before a model receives the original rows.
"""
import hashlib

QUOTABLE_FIELDS = frozenset({
    'text', 'headers', 'row_cells', 'caption', 'definition', 'title', 'note',
})


def _token(value):
    """Escape one RFC 6901 JSON Pointer reference token."""
    return str(value).replace('~', '~0').replace('/', '~1')


def _walk(value, path):
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, path + '/' + str(index))
    elif isinstance(value, dict):
        for key, item in value.items():
            child_path = path + '/' + _token(key)
            if key in QUOTABLE_FIELDS:
                if isinstance(item, str):
                    yield {'path': child_path, 'text': item}
                else:
                    yield from _walk(item, child_path)
            elif isinstance(item, (dict, list)):
                yield from _walk(item, child_path)


def inventory(row):
    """Return [{path, text}, ...] in legacy iter_context_text traversal order."""
    if not isinstance(row, dict):
        raise TypeError('row must be an object')
    return list(_walk(row.get('contexts', {}), '/contexts'))


def inventory_packet(rows):
    """Return per-ID path hashes and exact-text grouping indices, without text.

    Shape: {id: {paths: [{path, text_sha256}],
                 text_sha256_groups: [{text_sha256, paths: [...]}]}}.
    Groups are keyed by exact original text, not normalized strings or hashes.
    Empty recognized text leaves are preserved. Duplicate IDs are rejected.
    """
    if not isinstance(rows, list):
        raise TypeError('rows must be an array')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            raise ValueError('each row requires a nonempty string id')
        if row['id'] in result:
            raise ValueError('duplicate row id')
        paths = []
        by_text = {}
        for leaf in inventory(row):
            text_hash = hashlib.sha256(leaf['text'].encode('utf-8')).hexdigest()
            paths.append({'path': leaf['path'], 'text_sha256': text_hash})
            if leaf['text'] not in by_text:
                by_text[leaf['text']] = {'text_sha256': text_hash, 'paths': []}
            by_text[leaf['text']]['paths'].append(leaf['path'])
        result[row['id']] = {'paths': paths, 'text_sha256_groups': list(by_text.values())}
    return result
