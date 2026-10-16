"""Assemble a complete candidate prompt; this does not execute an LLM."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'coding-v26-20260930' / 'llm_candidate'
MANUAL = ROOT.parent / 'autocode-v28-review-20261004-111306' / 'protocol-v1.3.md'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

notes = ROOT / '修订说明-v29.md'
if not notes.exists():
    shutil.copy2(ROOT / '执行提示词-v29.md', notes)
changes = notes.read_text()
gate = changes.split('## 1. 替换“两阶段门禁”\n\n', 1)[1].split('## 2.', 1)[0].rstrip()
common = changes.split('## 2. 在“五维执行边界”前增补共通纳入规则\n\n', 1)[1].split('## 3.', 1)[0].rstrip()
quality = ('明确“药品质量安全”或“质量风险”可按冻结手册判断S；仅有一般质量、工艺、稳定性或生产规范不自动赋S。'
           '最终输出保留 `safety_quality_basis`：S=1且仅依据明确药品质量安全/质量风险时为 `quality_only`；'
           '同时有其他药物损害依据时为 `quality_and_other`；没有质量安全依据时为 `no_quality_basis`，'
           '包括S=0，以及S=1但仅依据不良反应等其他药物损害的情形。最终二元发布不使用 `undetermined`。')
prompt = (BASE / '执行提示词-v26.md').read_text().replace('执行提示词 v26', '执行提示词 v29', 1)
start, end = prompt.index('## 一、两阶段门禁'), prompt.index('## 二、每条必须执行的语义顺序')
prompt = prompt[:start] + '## 一、两阶段门禁\n\n' + gate + '\n\n' + prompt[end:]
prompt = prompt.replace('五维定义完全沿用 CAL-5D v1.3。以下只强调容易误判的执行边界。',
                        '五维定义完全沿用 CAL-5D v1.3。以下只强调容易误判的执行边界。\n\n' + common)
prompt = prompt.replace('### E 有效性', quality + '\n\n### E 有效性', 1)
prompt += '\n最终输出的 `execution_version` 固定为 `LLM-binary-v29`；采用同目录二元Schema。\n'
(ROOT / '执行提示词-v29.md').write_text(prompt)
shutil.copy2(MANUAL, ROOT / 'protocol-v1.3.md')
schema = json.loads((BASE / 'output_schema_binary.json').read_text())
schema['properties']['execution_version']['const'] = 'LLM-binary-v29'
(ROOT / 'output_schema_binary.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
validator = (BASE / 'validate_binary_output.py').read_text()
assert 'LLM-binary-v26' in validator
(ROOT / 'validate_binary_output.py').write_text(validator.replace('LLM-binary-v26', 'LLM-binary-v29'))
(ROOT / '完整系统提示词-v29.txt').write_text(prompt + '\n\n--- 冻结的完整手册 ---\n\n' + MANUAL.read_text()
    + '\n\n--- 最终二元输出结构 ---\n\n' + json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
report = {
    'status': 'candidate_assembled_not_model_validated',
    'execution_version': 'LLM-binary-v29',
    'protocol_version': 'CAL-5D-20260926-v1.3',
    'schema_change': 'Execution-version constant only; binary labels, evidence, reasons and subtype fields unchanged.',
    'source_bindings': {str(p): sha(p) for p in (BASE / '执行提示词-v26.md', BASE / 'output_schema_binary.json',
        BASE / 'validate_binary_output.py', MANUAL, notes)},
    'candidate_bindings': {n: sha(ROOT / n) for n in ('执行提示词-v29.md', '完整系统提示词-v29.txt',
        'protocol-v1.3.md', 'output_schema_binary.json', 'validate_binary_output.py', 'assemble_candidate.py')},
    'corpus_rerun': False,
    'new_performance_metrics': False,
    'remaining': ['development semantic checks with actual model', 'complete corpus run',
                  'repeated-run and equivalent-prompt stability', 'independent human reference validation'],
}
(ROOT / 'candidate_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('Complete v29 candidate assembled; no LLM execution or performance claims.')
