"""Build an isolated preparation package. Does not execute the coding runner."""
import hashlib
import json
from pathlib import Path

W = Path('/PROJECT_ROOT/outputs/编码修订核查-20261008')
OLD = W / 'LLM编码/共同操作判据准备'
HERE = Path(__file__).resolve().parent
MANUAL = W / '定义溯源核查/测量与计数统一/共用编码手册.md'
MANUAL_SHA = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
OLD_EXECUTION = 'LLM-common-operations-fb78f1922e2e'
EXECUTION = 'LLM-measurement-semantic-24007a19a724'
CORE = ['编码提示.txt', 'output_schema_codex_compatible.json', 'validate_binary_output.py', 'run_coding.py']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert all(not (HERE / name).exists() for name in CORE), 'prepared files already exist; do not overwrite'
    before = {str(p): sha(p) for p in OLD.iterdir() if p.is_file()}
    manual = MANUAL.read_bytes()
    assert hashlib.sha256(manual).hexdigest() == MANUAL_SHA
    old_prompt = (OLD / '编码提示.txt').read_text(encoding='utf-8')
    prefix = old_prompt.split('<common_manual>\n', 1)[0] + '<common_manual>\n'
    suffix = old_prompt.split('</common_manual>', 1)[1].replace(OLD_EXECUTION, EXECUTION)
    lines = suffix.splitlines()
    quote_lines = [i for i, line in enumerate(lines) if line.startswith('每个1必须至少一条')]
    innovation_lines = [i for i, line in enumerate(lines) if line.startswith('innovation_subtypes：')]
    assert len(quote_lines) == len(innovation_lines) == 1
    lines[quote_lines[0]] = (
        '每个1必须至少一条source=unit的当前原文连续逐字引文。引文与理由须保留实际影响判断的否定、条件、时间、比较对象及例外范围；必要时引用完整当前句段。不能只摘否定词后的短语并把否定命题解释为肯定结论，也不将否定、条件或未来语气统一判0。'
        '标签依赖给定语境补全药物对象、指代、资格范围、比较基准或实质要求时，必须同时提供该维度source=context的实际使用逐字引文，并在对应理由中简要说明当前单元与该语境的关系；需完整读取确指范围，不能只选有利成员。'
        '纯结构引导不从成员内容汇总五维标签；当前有独立实质总领命题时，确指完整成员可补足其对象或条件，当前承接关系锚点可作为unit引文，仍须保存实际使用的context引文。成员按自身内容和必要共同谓词判断，不继承全部兄弟项。'
        '不得引用未用于该标签的背景，不需提供内部思维过程。每条evidence写dimension、source和quote；逐字复制实际提供文本，保留原空白、标点和Unicode字符，不改写、不做规范化、不跨不连续片段拼接，不给0维度填证据。'
        'context仅指给定语境中的政策文字，metadata、证书或定位描述不构成原文依据。材料齐全而缺乏实质依据时填0，不因为一般背景可推测相关而填1。'
    )
    lines[innovation_lines[0]] = (
        'innovation_subtypes：仅I=1时按独立依据选择attribute（技术新颖性、实质改良或其价值）、'
        'research_support（明确创新/改良研发实际支持安排及其设立、适用、限制或撤回，须有对象、当前支持安排与直接关系；不由普通技术要求或一般指南功能推出）、'
        'qualification_advantage（创新/改良资格及比较条件）；I=0为空数组。一般创新指南中的产品设计、试验实施或证据形成要求，按当前实际内容判断，不因指南整体指导功能加I。技术要求确实设置支持路径、便利或反馈机会时，按手册的实际关系判断，不一律排除。'
    )
    suffix = '\n'.join(lines) + '\n'
    prompt = prefix.encode('utf-8') + manual + b'</common_manual>' + suffix.encode('utf-8')
    (HERE / '编码提示.txt').write_bytes(prompt)
    for name in ['validate_binary_output.py', 'run_coding.py']:
        source = (OLD / name).read_text(encoding='utf-8')
        assert OLD_EXECUTION in source
        (HERE / name).write_text(source.replace(OLD_EXECUTION, EXECUTION), encoding='utf-8')
    schema = json.loads((OLD / 'output_schema_codex_compatible.json').read_text(encoding='utf-8'))
    schema['title'] = 'COMMON-5D measurement-and-semantic-manual development LLM output'
    schema['properties']['execution_version']['const'] = EXECUTION
    schema['properties']['execution_version']['enum'] = [EXECUTION]
    schema['properties']['rows']['items']['properties']['innovation_subtypes']['description'] = (
        'Content audit subtypes only. research_support records an actual support arrangement for explicitly linked innovative/improved drug research, including its establishment, applicability, restriction or withdrawal. Ordinary technical requirements or the general function of a guideline do not by themselves establish research_support. Apply the common manual; the schema does not verify this semantic relation.'
    )
    (HERE / 'output_schema_codex_compatible.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert prompt.split(b'<common_manual>\n', 1)[1].split(b'</common_manual>', 1)[0] == manual
    assert all(OLD_EXECUTION not in (HERE / name).read_text(encoding='utf-8') for name in CORE)
    after = {str(p): sha(p) for p in OLD.iterdir() if p.is_file()}
    assert before == after, 'old preparation changed'
    record = {
        'status': 'prepared_only_no_model_execution',
        'manual_path': str(MANUAL), 'manual_sha256': MANUAL_SHA,
        'execution_identity': EXECUTION,
        'requested_model': 'gpt-5.6-sol', 'reasoning_effort': 'medium',
        'actual_model_calls': 0, 'runner_invocations': 0, 'plan_only_invocations': 0,
        'source_preparation': str(OLD), 'source_files_sha256': before,
        'old_preparation_unchanged_at_build': before == after,
        'change_scope': {
            'prompt': 'exact new manual; output wrapper synchronized for I3, structural/substantive leads, negation, conditions, exceptions, full literal quotation',
            'schema': 'execution identity, descriptive title, and research_support explanation only; fields and enum sets retained',
            'validator': 'execution identity only; structural and literal rules unchanged',
            'runner': 'execution identity only; model, effort, preservation and technical-attempt selection unchanged'
        },
        'semantic_validity_established': False,
        'material_completeness_verified': False,
        'input_material_frozen': False,
        'adopted_for_paper': False,
        'prepared_files_sha256': {name: sha(HERE / name) for name in CORE}
    }
    (HERE / '准备记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'execution_identity': EXECUTION, 'prepared_files_sha256': record['prepared_files_sha256']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
