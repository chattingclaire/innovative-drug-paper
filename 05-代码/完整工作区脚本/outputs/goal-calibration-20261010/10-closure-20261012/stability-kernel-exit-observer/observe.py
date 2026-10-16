"""Passive Darwin kernel exit observations; never signals or receives model output."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent / 'stability-diagnostics/controller-exit-20261012.json'
NOTE_EXITSTATUS = 0x04000000


def now():
    return datetime.now(timezone.utc).isoformat()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def rows():
    raw = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart=,command='],
                         capture_output=True, text=True, check=True).stdout
    result = {}
    for line in raw.splitlines():
        m = re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(.{24})\s+(.*)', line)
        if not m:
            raise ValueError('Unparsed process observation')
        pid, ppid, pgid, born, command = m.groups()
        result[int(pid)] = {'pid': int(pid), 'ppid': int(ppid), 'pgid': int(pgid),
                            'lstart': born, 'command': command}
    return result


def main():
    out = HERE / sys.argv[1]
    out.mkdir(exist_ok=False)
    diagnosis = json.loads(DIAG.read_text())
    observed = rows()
    queue = select.kqueue()
    pending, registrations = {}, []
    for case in diagnosis['unclosed_started_attempts']:
        actual_binding = case['start']
        assert binding(actual_binding['path']) == actual_binding
        actual = json.loads(Path(actual_binding['path']).read_text())
        assert binding(actual['start']['path']) == actual['start']
        dispatch = json.loads(Path(actual['start']['path']).read_text())
        pid = actual['pid']
        row = observed.get(pid)
        if not row:
            continue
        born = datetime.strptime(row['lstart'], '%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('Asia/Shanghai'))
        launched = datetime.fromisoformat(actual['at_utc'])
        assert abs((born - launched).total_seconds()) < 1
        assert row['pgid'] == actual['process_group_id'] == pid
        assert row['command'].endswith(' '.join(dispatch['argv']))
        registration = {'at_utc': now(), 'actual_start': actual_binding, 'dispatch': actual['start'],
                        'route': {k: dispatch[k] for k in ('condition', 'batch_number', 'attempt_number')},
                        'identity_before_registration': row}
        try:
            queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                         flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                         fflags=select.KQ_NOTE_EXIT | NOTE_EXITSTATUS)], 0, 0)
            registration['kernel_registration_succeeded'] = True
            pending[pid] = registration
        except OSError as exc:
            registration['kernel_registration_succeeded'] = False
            registration['error'] = {'errno': exc.errno, 'message': str(exc)}
        registrations.append(registration)
    save(out / 'registration.json', {'at_utc': now(), 'observer_pid': os.getpid(),
         'observer_session': os.getsid(0), 'code': binding(__file__), 'diagnosis': binding(DIAG),
         'registrations': registrations, 'signals_sent': False, 'capture_contents_read': False,
         'model_calls': 0, 'actual_receptions': 0,
         'kernel_definition_source': 'https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/event.h'})
    deadline = time.monotonic() + 7200
    while pending and time.monotonic() < deadline:
        events = queue.control(None, len(pending), 30)
        for event in events:
            pid = event.ident
            if pid not in pending:
                raise ValueError('Event outside registered process objects')
            status_present = bool(event.fflags & NOTE_EXITSTATUS)
            exit_seen = bool(event.fflags & select.KQ_NOTE_EXIT)
            error_seen = bool(event.flags & select.KQ_EV_ERROR)
            save(out / f'kernel-exit-{pid}.json', {
                'observed_at_utc': now(), 'provenance': 'Darwin_EVfilt_PROC_real_kernel_event',
                'registration': pending.pop(pid),
                'event': {'ident': pid, 'filter': event.filter, 'flags': event.flags,
                          'fflags': event.fflags, 'data': event.data, 'udata': event.udata},
                'kernel_exit_event_seen': exit_seen, 'exit_status_flag_present': status_present,
                'kernel_event_error': error_seen,
                'actual_kernel_returncode': os.waitstatus_to_exitcode(event.data)
                    if exit_seen and status_present and not error_seen else None,
                'Popen_wait_claimed': False, 'all_child_groups_terminal_claimed': False,
                'technical_validity_or_label_claimed': False, 'signals_sent': False})
    save(out / 'observer-completion.json', {'at_utc': now(), 'unresolved_registered_pids': sorted(pending),
         'all_registered_exit_events_received': not pending, 'model_receptions_performed': 0,
         'signals_sent': False, 'real_returncode_or_process_terminal_not_inferred_from_deadline': True})


if __name__ == '__main__':
    main()
