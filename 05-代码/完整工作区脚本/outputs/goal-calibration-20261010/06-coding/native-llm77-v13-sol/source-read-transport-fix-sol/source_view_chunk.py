"""One bounded original byte view; emitted bytes are not an actual-read receipt."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
import uuid


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def pointer_value(value, pointer):
    if not pointer.startswith('/'):
        raise ValueError('original JSON pointer beginning with / is required')
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            if not token.isdigit() or (token != '0' and token.startswith('0')):
                raise ValueError('invalid original array index')
            value = value[int(token)]
        elif isinstance(value, dict):
            value = value[token]
        else:
            raise ValueError('pointer descends through scalar')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', required=True)
    parser.add_argument('--file-sha256', required=True)
    parser.add_argument('--pointer')
    parser.add_argument('--encoding', choices=['utf8_text', 'canonical_json', 'file_utf8'],
                        required=True)
    parser.add_argument('--start-byte', type=int, default=0)
    parser.add_argument('--max-bytes', type=int, default=6000)
    parser.add_argument('--audit-log', required=True)
    args = parser.parse_args()
    path = Path(args.file).resolve()
    raw = path.read_bytes()
    if sha(raw) != args.file_sha256:
        raise ValueError('input file byte SHA mismatch')
    if not 1 <= args.max_bytes <= 6000:
        raise ValueError('chunk limit must be 1..6000 UTF8 bytes')
    if args.encoding == 'file_utf8':
        if args.pointer is not None:
            raise ValueError('file_utf8 cannot claim a JSON pointer')
        payload = raw
    else:
        if args.pointer is None:
            raise ValueError('JSON encoding requires an exact original pointer')
        value = pointer_value(json.loads(raw), args.pointer)
        if args.encoding == 'utf8_text':
            if not isinstance(value, str):
                raise ValueError('utf8_text requires an original string leaf')
            payload = value.encode('utf-8')
        else:
            payload = canonical(value)
    payload.decode('utf-8', errors='strict')
    start = args.start_byte
    if not 0 <= start <= len(payload):
        raise ValueError('start_byte outside this view')
    if start < len(payload) and payload[start] & 0xC0 == 0x80:
        raise ValueError('start_byte splits a UTF8 character')
    end = min(start + args.max_bytes, len(payload))
    while end < len(payload) and payload[end] & 0xC0 == 0x80:
        end -= 1
    if end == start and start < len(payload):
        raise ValueError('chunk ceiling cannot fit the next UTF8 character')
    chunk = payload[start:end]
    chunk.decode('utf-8', errors='strict')
    meta = {'local_execution_id': str(uuid.uuid4()),
            'executed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'input_file': str(path), 'input_file_bytes': len(raw),
            'input_file_byte_sha256': sha(raw), 'json_pointer': args.pointer,
            'view_encoding': args.encoding, 'view_sha256': sha(payload),
            'view_total_UTF8_bytes': len(payload), 'start_byte': start, 'end_byte': end,
            'chunk_UTF8_bytes': len(chunk), 'chunk_sha256': sha(chunk),
            'view_EOF_after_this_chunk': end == len(payload)}
    header = canonical(meta)
    emitted = b'BEGIN_SOURCE_VIEW_CHUNK ' + header + b'\n' + chunk
    emitted += b'\nEND_SOURCE_VIEW_CHUNK ' + header + b'\n'
    # This records a real process emission only. The actor must separately record
    # the actual returned event/end marker/delivery and its own reading.
    with Path(args.audit_log).open('xb') as log:
        sys.stdout.buffer.write(emitted)
        sys.stdout.buffer.flush()
        audit = dict(meta, program_stdout_bytes_written=len(emitted),
                     emission_status='program_stdout_write_completed',
                     actual_tool_event_id=None, actual_tool_delivery_status=None,
                     read_attestation='not_recorded', image_pixels_read=False)
        log.write(canonical(audit) + b'\n')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, IndexError, TypeError, OSError, UnicodeError) as exc:
        print('SOURCE_VIEW_TRANSPORT_FAILURE: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
