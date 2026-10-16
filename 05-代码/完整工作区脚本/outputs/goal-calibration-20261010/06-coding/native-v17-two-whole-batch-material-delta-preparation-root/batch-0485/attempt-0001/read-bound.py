import json
import subprocess
import sys
from pathlib import Path

slot = Path(__file__).resolve().parent
assignment = slot.parent / 'assignment.json'
bindings = json.loads(assignment.read_text())
key = sys.argv[1]
start = int(sys.argv[2])
if key.startswith('packet:'):
    path = Path(bindings['packets'][int(key.split(':')[1])]['path'])
elif key.startswith('asset:'):
    path = Path(bindings['source_asset_bindings'][int(key.split(':')[1])]['path'])
else:
    path = Path(bindings[key]['path'])
end = min(start + 6500, len(path.read_text()))
if len(sys.argv) > 3:
    end = min(end, int(sys.argv[3]))
result = subprocess.run(['python3', str(slot.parent.parent / 'emit-presentation.py'),
    '--assignment', str(assignment), '--path', str(path),
    '--start', str(start), '--end', str(end)], capture_output=True, text=True)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
if result.returncode == 0:
    header = json.loads(result.stdout.splitlines()[0].split(' ', 1)[1])
    with (slot / 'presentation-events.jsonl').open('a') as stream:
        stream.write(json.dumps(header, ensure_ascii=False) + '\n')
raise SystemExit(result.returncode)
