"""Exclusive finite audit seal; no candidate modification or model call."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / 'native-batch-stability-adapter-sol'


def binding(p):
    p = Path(p).resolve()
    d = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(d).hexdigest(), 'bytes': len(d)}


def write(name, obj):
    with (HERE / name).open('x', encoding='utf8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


result = json.loads((HERE / 'audit-controls.json').read_text())
bindings = json.loads((HERE / 'candidate-bindings-check.json').read_text())
assert result['status'] == 'passed' and result['check_N'] == result['passed_N'] == 30
assert binding(CANDIDATE / 'candidate-seal.json') == bindings['candidate_seal']
assert all(binding(x['path']) == x for x in bindings['external_technical_source_bindings'])
for code in bindings['executed_code']:
    assert binding(code['path']) == code
with (HERE / 'audit-report.md').open('x', encoding='utf8') as f:
    f.write('''本次独立有限审查的30项检查全部通过，未发现阻断候选构造批次统计衔接的新增缺陷。完整原提交字节绑定、固定items指针、全批技术失效、首个有效选择、合法null停重试、max3和五诊断条件封存门均与候选契约一致。请求身份与真实provider身份明确分开；实际provider/API调用数、独立上下文真实性和事前时序不由SHA认证。

候选296项文件的清单成员、字节数、SHA及10份明确绑定技术/数学出处全部核对，封存前后候选未改变。数学vendor与已审typing-fixed出处、native schema与绑定原schema逐字一致。仅在本新审查目录写入，未读取真实77/800/4481编码、答案、参照或政策正文，没有派发真实coding actor或调用模型。审查者为AI，请求6.1 Sol/ultra；不是真人审查。

控制有两种来源：复制候选已封存TOY接口外壳后作独立拒绝/状态变换，及全新手算的五ID不等权数学向量。前者不冒称独立数据集，后者也不是现实样本。修改后的完整失败原字节、原资格输出和台账拒绝原因保存于actual-failures；含末成员引文失效、乱序、合法null后重试、四次attempt、invalid first和已见模型字符串漂移。未终结H快照保持两次余量、paired_comparisons为空和three_main_runs=null；不会产生部分记录救回或提前比较。

新手算R1/R2-S的原始四格为(1,1,1,0)，Po=1/3、Pe=5/9、κ=-1/2；权重四格为(1,3,2,0)，Po=1/6、Pe=1/2、κ=-2/3。共同C5为3条、权重6，一致1条、权重1；语义null和技术失败分别排除，其他充分维度继续按逐维集合计算。每运行自身Σ5T作q分母：R1/R3加权S/Ec=2/5、3/5，R2为1/2、1/2。原始输出见invented-math-original-output.json，先验在执行前保存。

实际执行新批次CLI和未修改旧单记录CLI，两个都成功；旧单记录仅使用复制的TOY数学回归，外部true报告不升级为来源/引用资格。批次CLI结果等于同输入内存分析。派生记录标derived_record_is_original_response=false，同批记录保留同一整批原文件ref和固定/items/N；等价JSON的原字节SHA可不同而解析对象SHA相同，不把结构化文件字节称provider wire证据。

production资格接口仍未采用。本候选只执行固定synthetic schema、opaque adapter和quote checker，改成prospective_registered_inputs会实际拒绝；共同正式来源schema、位置/CTX/资产、连续引用、交付和真实工具证据仍需另行冻结采用。这里没有真实R运行、现实稳定性、分类正确性、真人信度、CI、稳定性通过线或总体推断。有限设施通过仅支持本范围内工程与数学衔接，不能视为生产资格或完整项目验收。
''')
write('audit-report.json', {'status': 'finite_independent_facility_checks_passed',
                          'check_N': 30, 'passed_N': 30,
                          'new_blocking_implementation_findings': [],
                          'production_qualification_adopted': False,
                          'actual_provider_or_independence_authenticated': False,
                          'real_cohort_or_model_calls': 0, 'true_stability_estimated': False,
                          'candidate_and_existing_files_unchanged': True,
                          'candidate_seal': bindings['candidate_seal'],
                          'control_results': binding(HERE / 'audit-controls.json'),
                          'scope': 'whole-batch facility, limited copied-TOY interface mutations and new hand mathematics; not coding/Gold/source-body review'})
files = [binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
seal = {'status': 'sealed_finite_independent_statistics_facility_audit',
        'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'candidate_seal': bindings['candidate_seal'], 'output_files': files,
        'candidate_and_existing_files_read_only': True, 'real_cohort_or_model_calls': 0,
        'production_qualification_adopted': False}
seal['self_sha256_excluding_field'] = hashlib.sha256(json.dumps(seal, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
write('seal.json', seal)
print(json.dumps({'status': 'sealed', 'checks': 30, 'passed': 30, 'file_N': len(files),
                  'seal': binding(HERE / 'seal.json'), 'real_model_calls': 0}, ensure_ascii=False))
