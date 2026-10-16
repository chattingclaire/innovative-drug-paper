"""Pure NONHUMAN process-table controls; never observes or starts a process."""
import importlib.util
import json
from pathlib import Path
import entry as c


def run():
    manifest = c.load(c.HERE / 'manifest.json')
    original = c.module(manifest['terminal_common'], 'sealed_terminal_owned_NONHUMAN_controls')
    certified = '2026-10-12T04:00:00+08:00'
    early = 'Mon Oct 12 03:00:00 2026'
    late = 'Mon Oct 12 05:00:00 2026'
    def row(pid, pgid=None, ppid=1, birth=late, command='/NONHUMAN/unrelated'):
        return dict(pid=pid, ppid=ppid, pgid=pid if pgid is None else pgid, stat='S', lstart=birth, command=command)
    guard = c.numeric_alias_guard(original.owned, certified)
    tests = []
    def case(name, rows, known, groups, leases, expected):
        actual = [r['pid'] for r in guard(rows, known, set(groups), leases)]
        assert actual == expected, (name, actual, expected)
        tests.append({'name':name, 'passed':True})
    case('distinct post-terminal lease PID', [row(10)], [], [], [10], [])
    case('entire post-terminal reused group with actual leader', [row(10),row(11,10,10)], [], [10], [], [])
    case('late child cannot erase original live group leader', [row(10,birth=early),row(11,10,10)], [], [10], [], [10,11])
    case('late child with vanished leader remains uncertain', [row(11,10)], [], [10], [], [11])
    case('unknown leader birth blocks', [row(10,birth='unparsed'),row(11,10,10)], [], [10], [], [10,11])
    case('unknown member birth blocks whole numeric group', [row(10),row(11,10,10,birth='unparsed')], [], [10], [], [10,11])
    case('old member blocks despite post-terminal new leader', [row(10),row(11,10,10,birth=early)], [], [10], [], [10,11])
    case('exact historical identity never excluded', [row(10)], [row(10)], [10], [10], [10])
    case('post-terminal codex exec still blocks', [row(10,command='/NONHUMAN/codex exec args')], [], [10], [10], [10])
    case('post-terminal isolated host still blocks', [row(10,command=original.ISOLATED+'/codex-code-mode-host')], [], [10], [10], [10])
    case('original recovery command still blocks', [row(10,command='/NONHUMAN/recover-native-whole-batches-v4-root.py')], [], [10], [10], [10])
    case('true historical parent preserves later descendants', [row(10,birth=early),row(11,90,10),row(12,91,11)], [row(10,birth=early)], [10], [10], [10,11,12])
    case('command seed retains descendants after numeric alias removal', [row(10,command='/NONHUMAN/codex exec args'),row(11,90,10)], [], [10], [10], [10,11])
    case('unknown lease PID birth blocks', [row(10,birth='unparsed')], [], [], [10], [10])
    return {'artifact_type':'NONHUMAN_outer_terminal_numeric_alias_controls', 'implementation':c.bind(c.HERE/'entry.py'),
            'original_owned_source':manifest['terminal_common'], 'N':len(tests),'passed_N':len(tests),'cases':tests,
            'actual_process_observations':0,'signals':0,'model_calls':0,'campaign_launches':0,'label_content_read':False}


if __name__ == '__main__':
    result=run()
    with (c.HERE/'controls.json').open('x') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'N':result['N'],'passed_N':result['passed_N']}))
