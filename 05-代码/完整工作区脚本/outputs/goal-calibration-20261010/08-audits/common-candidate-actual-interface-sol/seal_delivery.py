"""Seal own source-only audit; future child plan is separately sealed."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
def bind(p):
    raw = p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def main():
    target = D / 'output-seal.json'
    if target.exists():
        raise RuntimeError('Existing seal must remain unchanged')
    members = [bind(p) for p in sorted(D.rglob('*')) if p.is_file()
        and p.name != 'output-seal.json' and 'historical-human-S3-development-plan' not in p.parts]
    inputs = json.loads((D/'input-bindings.json').read_text())
    for item in members + inputs:
        assert bind(Path(item['path'])) == item
    value = {'status':'sealed_source_interface_audit_nonhuman',
        'record_ids':['RECODE25-00036','RECODE25-00038','RECODE25-00045'],
        'unique_adapter_identities':6,'actual_adapter_calls':7,
        'persistent_mechanical_pass_adapter_calls':0,
        'RelationView_calls':0,'judge_calls':0,'machine_output_files_read':0,
        'dimension_labels_created':0,'real_human_results_created':0,
        'members':members,'inputs':inputs,
        'future_child_exclusion':'historical-human-S3-development-plan/ is separately sealed and not part of this source-only audit'}
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    readback = json.loads(target.read_bytes())
    for item in readback['members'] + readback['inputs']:
        assert bind(Path(item['path'])) == item
    print(json.dumps({'seal':bind(target),'member_count':len(members),'input_count':len(inputs),
        'member_and_input_readback':'all_equal'},ensure_ascii=False))

if __name__ == '__main__':
    main()
