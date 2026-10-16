"""Bounded in-task administrative watcher; no labels/metrics printed or computed."""
from pathlib import Path
import importlib.util
import json
import time

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('D668_frozen_receiver', ROOT / 'D668-frozen-inputs/admin_receiver.py')
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)
release = ROOT / 'D668'
receipts = ROOT / 'D668-原始提交接收'


def fingerprint():
    return tuple((str(p.relative_to(release)), p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                 for p in sorted(release.glob('agent-*/结果-*.json')))


if __name__ == '__main__':
    previous = None
    deadline = time.monotonic() + 7200
    print(json.dumps({'watcher': 'started', 'scope': 'administrative first-byte receipts only', 'timeout_seconds': 7200}), flush=True)
    while time.monotonic() < deadline:
        current = fingerprint()
        if current != previous:
            report = receiver.receive(ROOT / 'D668-最终冻结清单.json', release, receipts)
            print(json.dumps({'checked_at': report['checked_at'], 'status': report['status'],
                              'summary': {c: {'batches': len(v['validated_batches']), 'rows': v['validated_rows']}
                                          for c, v in report['summary'].items()},
                              'structural_errors': report['structural_errors'],
                              'validation_report': report['validation_report'], 'performance_computed': False},
                             ensure_ascii=False), flush=True)
            if report['structural_errors']:
                raise SystemExit('Stopped on structural error; original first bytes preserved.')
            if all(len(v['validated_batches']) == 27 and v['validated_rows'] == 668 for v in report['summary'].values()):
                print(json.dumps({'watcher': 'complete', 'performance_computed': False}), flush=True)
                break
            previous = current
        time.sleep(15)
    else:
        print(json.dumps({'watcher': 'timeout', 'performance_computed': False}), flush=True)
