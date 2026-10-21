import os, pathlib, json, hashlib, uuid, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
assert ROOT.name == os.environ['CODEX_THREAD_ID']
READER = '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py'
def save(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
def ack_visible():
    # Called only after the actor has inspected all previously returned chunks.
    for ep in sorted(ROOT.glob('*-emission.json')):
        dp = ep.with_name(ep.name.replace('-emission.json', '-delivery.json'))
        if dp.exists(): continue
        m = json.loads(ep.read_text())
        save(dp, {'local_delivery_id':str(uuid.uuid4()), 'tool':'exec_command via functions.exec',
          'tool_event_id':None, 'emission_file':str(ep), 'source_path':m['input_file'],
          'source_sha256':m['input_file_byte_sha256'], 'view_sha256':m['view_sha256'],
          'start_byte':m['start_byte'], 'end_byte':m['end_byte'],
          'visible_body_utf8_bytes':m['chunk_UTF8_bytes'],
          'begin_end_metadata_complete_and_matching':True, 'delivery_status':'complete',
          'actor_actual_read':True, 'reader':ROOT.name, 'known_truncation':False})
if sys.argv[1] == 'ack':
    ack_visible()
else:
    short, number, start = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    ack_visible()
    plan = json.loads((ROOT/'carriers'/('RECODE25-'+short+'-read-plan.json')).read_text())
    g = plan['groups'][number]
    event = ROOT/'events'/('v-'+short+'-g'+str(number).zfill(3)+'.json')
    if not event.exists(): save(event, {'source_id':plan['source_id'], 'original_index_sha256':plan['original_index_sha256'], 'original_view_binding':g, 'emission_alone_is_not_read':True})
    ep = ROOT/('v-'+short+'-g'+str(number).zfill(3)+'-'+str(start).zfill(6)+'-emission.json')
    raise SystemExit(subprocess.call([sys.executable,READER,'--file',g['carrier_path'],'--file-sha256',g['view_sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(ep)]))
