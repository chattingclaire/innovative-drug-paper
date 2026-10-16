import hashlib, json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

here=Path(__file__).resolve().parent
corrected={13:'correction-013-01.json',16:'correction-016-01.json',19:'correction-019-01.json'}
first_invalid={13,16,19}
packets=[]
for n in range(1,43):
    inp=f'input-{n:03d}.json'; first=f'output-{n:03d}.json'
    effective=corrected.get(n,first)
    def sha(name):
        return hashlib.sha256((here/name).read_bytes()).hexdigest()
    item={
        'packet':n,
        'input_file':inp,
        'input_sha256':sha(inp),
        'first_output_file':first,
        'first_output_sha256':sha(first),
        'first_output_validation':'failed_structure' if n in first_invalid else 'valid',
        'effective_output_file':effective,
        'effective_output_sha256':sha(effective),
        'effective_output_validation':'valid',
    }
    if n in corrected:
        rec=f'correction-{n:03d}-01.record.json'
        item['correction_record_file']=rec
        item['correction_record_sha256']=sha(rec)
    packets.append(item)

out={
    'shard':6,
    'model_request_name':'gpt-5.6-sol',
    'run_name':'gpt56-sol-v13-native-1',
    'protocol_version':'CAL-5D-20260926-v1.3',
    'completed_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    'batch_count':42,
    'total_rows':420,
    'bottom_model_revision':'未知',
    'temperature':'未知',
    'random_seed':'未知',
    'packets':packets,
}
dst=here/'completion.json'
if dst.exists():
    raise SystemExit('refusing to overwrite completion.json')
dst.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
