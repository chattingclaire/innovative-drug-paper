"""Lock the current methods and audit the remaining frame before selecting cases.

No classifier execution, human-label changes, or sampling takes place here.
"""
from pathlib import Path
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

ADMIN = Path(__file__).resolve().parent
ROOT = ADMIN.parents[2]
OLD = ROOT / '09-delivery/独立真人判读-200条-20261013/管理员留存-勿发编码者'
ROUND = ROOT / '11-version-comparison-20261014/规则修复第六轮-20261015'

def read(p):
    return json.loads(Path(p).read_text())

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bind(p):
    p = Path(p).resolve()
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)}

def save(p, x):
    text = json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    if p.exists():
        assert p.read_text() == text, f'Frozen file differs: {p}'
    else:
        p.write_text(text)

def main():
    lock = ADMIN / '方法与标准冻结.json'
    assert not lock.exists(), 'Methods already frozen; do not replace the freeze.'
    current = read(ROUND / '完成核验.json')
    assert current['counts'] == {'agreed': 991, 'disagreed': 9}
    snapshot = ADMIN / '冻结版本'
    snapshots = []
    def copy_file(src, relative, expected=None):
        src = Path(src)
        if expected:
            assert digest(src) == expected, str(src)
        dest = snapshot / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert dest.read_bytes() == src.read_bytes()
        else:
            shutil.copyfile(src, dest)
        snapshots.append({'original': bind(src), 'snapshot': bind(dest)})

    for name, b in current['code'].items():
        copy_file(b['path'], 'rule/' + name + '.py', b['sha256'])
    common = ROOT / '03-manual/full4481-common-release-20261010-root'
    for name in ['manual.txt', 'execution-prompt.txt', 'common-execution-protocol.txt']:
        copy_file(common / name, 'common/' + name)
    llm_run = ROOT / '06-coding/native-full4481-v1-sol'
    for name in ['actor-instructions.txt', 'run-scope.json', 'response-retention-policy.json']:
        copy_file(llm_run / name, 'llm/' + name)
    copy_file(ROUND / 'semantic-overrides.json', 'rule/semantic-overrides.json')
    copy_file(ROUND / 'prepare_source_overrides.py', 'rule/prepare_source_overrides.py')
    copy_file(ROUND / 'source-projection-bindings.json', 'rule/source-projection-bindings.json')
    copy_file(ROUND / '完成核验.json', 'rule/开发完成核验.json')
    f, draw = read(OLD/'sampling-freeze.json'), read(OLD/'draw.json')
    frame_binding = f['inputs']['metadata_frame']
    assert digest(frame_binding['path']) == frame_binding['sha256']
    frame = [json.loads(x) for x in Path(frame_binding['path']).read_text().splitlines()]
    old_excluded = set(f['excluded_source_ids'])
    used200 = {x['unit_id'] for x in draw['records']}
    used_families = {x['family_id'] for x in frame if x['source_id'] in used200}
    excluded_new = {x['source_id'] for x in frame if x['family_id'] in used_families}
    remaining = [x for x in frame if x['source_id'] not in old_excluded | excluded_new]
    assert len(frame)==4481 and len(remaining)==923
    allowed = {x['source_id'] for x in remaining}
    machine_bindings, machine_counts = {}, {}
    for method, rel in [('LLM', '07-statistics/original-whole-batch-native-full4481-cap13-root/selected-records.jsonl'),
                        ('old_rule', '06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl')]:
        src = ROOT / rel
        rows = [x for x in map(json.loads, src.read_text().splitlines()) if x['id'] in allowed]
        assert len(rows)==923
        machine_bindings[method] = bind(src)
        machine_counts[method] = {d: sum(x['labels'][d]==1 for x in rows) for d in ['S','E','Ec','I','F']}
    audit = {
        'status': 'preliminary_remaining_frame_audit_not_drawn',
        'original_N':4481, 'inherited_excluded_N':len(old_excluded),
        'old200_N':len(used200), 'new_family_exclusion_N_beyond_inherited':len(excluded_new-old_excluded),
        'preliminary_remaining_N':len(remaining),
        'departments':dict(Counter(x['department'] for x in remaining)),
        'existing_machine_positive_counts':machine_counts,
        'interpretation':'机器阳性为零不等于人工阳性为零；新样本不能保证有足够创新性、公平性阳性。不得承诺任取200条可验证五维召回率。',
        'document_and_source_exposure_audit_pending':True,
        'remaining_metadata':remaining,
        'excluded_ids':sorted(old_excluded|excluded_new),
        'bindings': {'old_sampling_freeze':bind(OLD/'sampling-freeze.json'), 'old_draw':bind(OLD/'draw.json'),
                     'metadata_frame':frame_binding, **machine_bindings},
    }
    save(ADMIN/'剩余样本初核.json',audit)
    save(lock,{
        'frozen_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'status':'methods_frozen_before_new_sample_selection',
        'human_results_received':False, 'new_sample_drawn':False,
        'rule_candidate':'第六轮关闭回归；200条开发诊断991/1000一致',
        'common_manual':'v1.3F-r1，原字节保留；不另写一个改变含义的简化版标准',
        'manual_sha256':digest(common/'manual.txt'),
        'llm_requested_model':'gpt-6.1-sol', 'llm_requested_reasoning_effort':'ultra',
        'historical_serving_model_independently_verified':False,
        'llm_note':'冻结原提示词及请求设置，不将历史请求型号写成已独立核实的实际服务型号。新材料若执行推理，须保存实际请求/响应及首次输出，未经核实不得声称完全复现历史执行环境。',
        'input_parity_requirement':'逐条共同正文、来源版本和可用上下文须一致；机器和两位真人按同一手册执行。新输入适配须先完成机械核验并冻结，不能依据新人工答案修补。',
        'no_prediction_based_redraw':True,
        'post_freeze_rule_edits_invalidate_this_holdout':True,
        'snapshots':snapshots,
        'frame_audit':bind(ADMIN/'剩余样本初核.json'),
        'original_llm_output':machine_bindings['LLM'],
    })
    print(json.dumps({'methods_frozen':True,'snapshot_files':len(snapshots),'preliminary_remaining_N':923,'sample_drawn':False},ensure_ascii=False))

if __name__=='__main__':
    main()
