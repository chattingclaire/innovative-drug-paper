"""Read existing execution evidence and refresh the single closure status page.

Never dispatches, signals, revalidates, selects, or modifies coding attempts.
The metadata/ps snapshot is not atomic and is not a stability calculation.
"""
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAMPAIGN = ROOT / '06-coding/current-freeze-stability-external-capture-v2-sol/prepared-fixed800-87-v2'
CONDITIONS = ('R1', 'R2', 'R3', 'W', 'H')


def read(path):
    return json.loads(path.read_text())


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    initial_current = read(ROOT / 'progress.json')['current_closure_20261012']
    human_state = initial_current.get('human200_readiness', {}).get('actual_human_state', 'started_not_completed')
    human_label = {
        'user_reported_completed_pending_originals_and_independence': '用户已报告编码完成；原件及A/B独立性待核',
        'human_review_summary_received_independence_unconfirmed': '已保存单份真人复核汇总：996项数值、4项待定；两份真人独立首判尚未确认',
        'human_review_confirmed_descriptive_comparison_completed': '用户确认已经真人复核；200条单份复核汇总已接收，996项数值、4项待讨论',
    }.get(human_state, '用户确认已经开始、尚未完成；保留原表')
    raw_ps = subprocess.run(
        ['ps', '-axo', 'pid=,ppid=,lstart=,command='],
        check=True, capture_output=True, text=True).stdout
    processes = {}
    for line in raw_ps.splitlines():
        m = re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(.{24})\s+(.*)', line)
        if not m:
            raise ValueError('Unparsed process observation')
        pid, ppid, born, command = m.groups()
        processes[int(pid)] = {'pid': int(pid), 'ppid': int(ppid), 'lstart': born, 'command': command}
    original_controller = processes.get(13924)
    original_live = bool(original_controller and original_controller['lstart'] == 'Mon Oct 12 06:48:58 2026'
                         and '/stability-certified-PID-birth-compatibility-v2-sol/entry.py --mode run --target stability13 ' in original_controller['command'])
    controller = original_controller if original_live else None
    durable = initial_current.get('machine_work', {}).get('stability_durable_continuation')
    durable_observation = None
    if durable:
        auth_binding = durable['authorization']
        if binding(Path(auth_binding['path'])) != auth_binding:
            raise ValueError('Durable authorization binding changed')
        auth = read(Path(auth_binding['path']))
        run = Path(auth['output_directory'])
        if str(run) != durable['output_directory']:
            raise ValueError('Durable run directory changed')
        start_path, identity_path = run / 'controller-start.json', run / 'controller-identity.json'
        if start_path.exists() and identity_path.exists():
            start, identity = read(start_path), read(identity_path)
            expected_argv = ['/opt/homebrew/opt/python@3.14/bin/python3.14', '-B', auth['unchanged_entry']['path'],
                             '--mode', 'run', '--target', 'stability13', '--go', auth['unchanged_GO']['path'],
                             '--adoption', auth['unchanged_adoption']['path']]
            if auth.get('runtime_scope') == 'original_durable_wait_plus_adopted_outer_numeric_alias_guard':
                for field in ('execution_wrapper', 'actual_supervisor_entrypoint', 'outer_compatibility_adoption'):
                    if binding(Path(auth[field]['path'])) != auth[field]:
                        raise ValueError('Durable compatibility binding changed')
                expected_argv = [expected_argv[0], '-B', auth['execution_wrapper']['path'],
                                 '--original-entry', auth['unchanged_entry']['path'],
                                 '--go', auth['unchanged_GO']['path'],
                                 '--adoption', auth['unchanged_adoption']['path'],
                                 '--compatibility-adoption', auth['outer_compatibility_adoption']['path']]
                if auth.get('actual_controller_argv') != expected_argv:
                    raise ValueError('Actual compatibility argv differs')
            if (start['argv'] != expected_argv or start['controller_pid'] != identity['pid']
                    or read(run / 'supervisor-start.json')['provenance']['ROOT_authorization'] != auth_binding):
                raise ValueError('Durable controller identity chain differs')
            process = processes.get(identity['pid'])
            terminal_path = run / 'controller-terminal.json'
            live = bool(process and identity['lstart'] and process['lstart'] == identity['lstart']
                        and all(arg in process['command'] for arg in expected_argv[2:]))
            durable_observation = {'authorization': auth_binding, 'identity': binding(identity_path),
                                   'confirmed_live': live,
                                   'terminal_record': binding(terminal_path) if terminal_path.exists() else None}
            if live:
                if original_live:
                    raise ValueError('Two campaign controllers appear live')
                controller = process
    controller_live = controller is not None
    observation = {
        'at_shanghai': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'non_atomic_snapshot': True,
        'controller_identity_confirmed_live': controller_live,
        'controller': controller if controller_live else None,
        'original_controller_identity_confirmed_live': original_live,
        'durable_continuation': durable_observation,
        'campaign': str(CAMPAIGN),
        'human_submission': {'state': human_state, 'confirmation_date': initial_current['human200']['confirmation_date'],
                             'user_answer': initial_current['human200']['user_confirmation'],
                             'preserve_issued_forms_and_independent_initial_submissions': True,
                             'historical_remaining120_currently_confirmed_development_exposed_at_least': 29},
        'conditions': {},
        'actual_stability_calculated_by_this_script': False,
        'formal_validation_complete': False,
        'paper_writing_gate_open': False,
    }
    for condition in CONDITIONS:
        counts, record_counts, attempts, rows = Counter(), Counter(), Counter(), []
        for batch in sorted((CAMPAIGN / 'batches').glob('diagnostic-batch-*')):
            assignment = read(batch / 'assignment.json')
            expected = assignment['expected_N']
            out = batch / 'ROOT-output' / condition
            selected = out / 'root-selection.json'
            starts = list(out.glob('attempt-*/ROOT-dispatch-start.json'))
            ends = list(out.glob('attempt-*/ROOT-process-completion.json'))
            receptions = [read(f) for f in out.glob('root-attempt-reception-*.json')]
            invalid = [r for r in receptions if r.get('state') == 'technical_invalid_whole_batch']
            external = []
            for receipt in invalid:
                if receipt.get('error', {}).get('type') != 'OrphanedControllerWaitReceiptUnavailable':
                    continue
                evidence = receipt['completion']
                if binding(Path(evidence['path'])) != evidence:
                    raise ValueError('External terminal certificate changed')
                cert = read(Path(evidence['path']))
                if not (cert.get('actual_process_terminal') is True and cert.get('failure_only') is True
                        and cert.get('returncode') is None
                        and cert.get('returncode_status') == 'unknown_parent_wait_unavailable'):
                    raise ValueError('External closure incorrectly represented')
                external.append(receipt)
            live_pids = []
            for actual_file in out.glob('attempt-*/ROOT-actual-process-start.json'):
                if (actual_file.parent / 'ROOT-process-completion.json').exists():
                    continue
                actual = read(actual_file)
                process = processes.get(actual.get('pid'))
                if process and str(actual_file.parent / 'ROOT-cli-final-message.txt') in process['command']:
                    live_pids.append(process['pid'])
            if selected.exists():
                state = 'technical_valid_selected'
            elif live_pids:
                state = 'confirmed_live'
            elif len(invalid) >= assignment['max_total_technical_attempts']:
                state = 'technical_exhausted'
            elif starts or receptions:
                state = 'between_attempts_or_requires_attention'
            else:
                state = 'not_started'
            counts[state] += 1
            record_counts[state] += expected
            attempts.update({'dispatch_records': len(starts), 'completion_records': len(ends),
                             'external_unknown_returncode_closures': len(external),
                             'technical_invalid_receptions': len(invalid)})
            rows.append({'batch': batch.name, 'expected_record_N': expected, 'state': state,
                         'confirmed_live_pids': live_pids, 'dispatch_N': len(starts),
                         'completion_N': len(ends), 'invalid_reception_N': len(invalid)})
            rows[-1]['external_unknown_returncode_closure_N'] = len(external)
        result_files = sorted((CAMPAIGN / 'ROOT-controller-runs').glob(f'*/{condition}-result.json'))
        latest_result = result_files[-1] if result_files else None
        observation['conditions'][condition] = {
            'batch_counts': dict(counts), 'record_counts': dict(record_counts), 'attempt_counts': dict(attempts),
            'latest_result': binding(latest_result) if latest_result else None,
            'all_terminal_from_controller': read(latest_result).get('all_terminal') if latest_result else False,
            'batches': rows,
        }
    metadata_path = HERE / 'runtime-observation.json'
    metadata_path.write_text(json.dumps(observation, ensure_ascii=False, indent=2) + '\n')
    progress_path = ROOT / 'progress.json'
    progress = read(progress_path)
    current = progress['current_closure_20261012']
    current['latest_runtime_observation_at'] = observation['at_shanghai']
    current['controller_identity_confirmed_live'] = controller_live
    current['latest_condition_counts'] = {
        c: {'batches': r['batch_counts'], 'records': r['record_counts'],
            'all_terminal': r['all_terminal_from_controller']}
        for c, r in observation['conditions'].items()
    }
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')
    handoff_state = current.get('current_validation_preparation', {}).get('complete_statistics_handoff', {}).get('state')
    handoff_label = ('完整接续候选已通过独立复核' if handoff_state == 'independently_reviewed_candidate_ready_for_actual_inputs'
                     else '原件到45项指标的完整候选已贯通，独审中')
    goal_label = ('等待外部依赖（blocked）；后台检验保持运行，任务未完成'
                  if current.get('goal_status') == 'blocked' else '进行中，尚未完成')
    v12_ready = current.get('machine_work', {}).get('isolated_v12_SF_repair')
    v12_execution_label = ('2082条首轮执行已启动；接收核验尚未完成，生产未替换'
                           if v12_ready and v12_ready.get('execution') else '尚未运行新分类或替换生产')
    if v12_ready and v12_ready.get('received_composite'):
        v12_execution_label = '首轮执行与兼容合并已完成；候选结果待最终采用'
    v12_execution_sentence = ('2082条首轮实际分类及严格来源接收已完成，形成4481条兼容候选；尚未最终采用。'
                              if v12_ready and v12_ready.get('received_composite')
                              else '候选尚未采纳，新范围的实际分类及来源接收仍待完成。')
    if v12_ready and v12_ready.get('semantic_review_blocker'):
        v12_execution_label = '2082条首轮及4481条兼容合并完成；实际检查发现00302/S误修，未采用，隔离修复中'
        v12_execution_sentence = '2082条首轮及4481条兼容合并完成，实际11条标签变化；其中00302/S误把临床安全性分析当作数据安全，已阻止采用并启动单独修复。E/Ec/I完整决定及原来源请求与事件保持一致。'
    v13_ready = current.get('machine_work', {}).get('isolated_v13_S_regression_repair')
    v13_label = ('修复候选有限复核完成，原2082条范围的新版本首轮已实际启动；尚未接收或替换生产'
                 if v13_ready and v13_ready.get('execution') else '隔离修复及有限复核中，尚未实际执行')
    if v13_ready and v13_ready.get('received_composite'):
        v13_label = '2082条首轮及4481条严格合并完成；与v12相比仅恢复00302/S，其余四维完整决定相同，尚未替换生产'
    ee_repair = current.get('machine_work', {}).get('isolated_v14_E_Ec_repair')
    ee_label = ('E、Ec隔离修正及有限检查已执行；跨条文原文补充候选已准备，尚未递送；各候选独审状态另记，未采用或重算正式成绩'
                if ee_repair else '尚未据此开发新规则或重算成绩')
    if ee_repair and ee_repair.get('E_successor'):
        ee_label = 'E后继已完成392项检查，材料依赖记录问题已关闭，保留一项既有混合句遗漏；Ec后继完成409项检查，但独审发现一项新误判，暂不采用。共同材料v17仅补充2条原文，尚未执行机器分类或重算正式成绩'
    f_repair = current.get('machine_work', {}).get('F_00104_source_backed_followup', {}).get('implementation', {})
    f_label = ('377项有限检查已完成，原353项及其他四维结果保持；作者外独审状态另记，尚未采用'
               if f_repair.get('summary') else '00104原文及手册依据已核实，隔离候选开发中')
    if f_repair.get('new_regression'):
        f_label = '377项有限检查已完成；作者外检查发现后置免除条件被误当作必要资格，候选暂不采用，原正式结果保留'
    integration = current.get('machine_work', {}).get('isolated_v15_integration', {})
    if integration.get('display_status'):
        ee_label = integration['display_status']
        f_label = '原后置免除条件误判已在独立后继修复，31项中30项硬预期均通过、1项保留待定；后续合并状态见E/Ec行，未替换正式结果'
    reuse_label = ('原91必取＋1170补抽仅保留为v11历史准备；本次200条复核已用于v12开发，不再作为该候选的独立检验样本'
                   if v12_ready else '可作为新设计的必取组，再从1170条补抽；原200及权重保留')
    runtime_label = ('同一检验由已核实的控制器按原固定顺序推进' if controller_live
                     else '本次未确认控制器存活，须先核对终态及仍在运行的子任务，再判断接续方式')
    lines = [
        '# 本轮总进度', '',
        f"核查时间：{observation['at_shanghai']}。这是实时进程与执行元数据的非原子快照。", '',
        f'最终目标：完成独立验证、结果验收、整篇修订论文及经核验的DOCX/PDF。当前Goal：{goal_label}。', '',
        '| 工作 | 当前状态 | 下一项依赖 |', '|---|---|---|',
        '| 4481条规则与LLM全量 | 已完成，复用同版结果 | 独立参照检验 |',
        '| 77条校准指标 | 两机核心指标均达到0.80；用途为开发校准 | 不作为正式独立验证 |',
        f'| 真人200条复核 | {human_label}；新版A/B为同一结果的两种排序 | 复核对照已完成；独立双人首判仍未建立 |',
        '| 200条版本衔接 | 手册同版，400/400材料清单绑定与v16一致；原表可继续 | [版本核查](human200-readiness/version-compatibility-audit.json)；独立资格与机器接入须另核 |',
        '| 当前曝光及机器版本 | 开发曝光框独审完成并登记：1261条剩余、3220条曝光；4481条真实混合来源及11,689项证据绑定已核验 | [登记](current-validation/adoption.json)；独立抽样资格和真人参照仍需另行接入 |',
        '| A/B首判统计接入 | 已复用既有解析修复建立独立入口，准入/元数据/环境检查通过 | [使用说明](human200-readiness/README.md)；等待真实完整首判，尚未计算真人指标 |',
        f'| 原91条复用与补充设计 | {reuse_label} | [方案与条件](current-validation/README.md)；未另抽样或改写原权重 |',
        '| 已开始判读的时序接入 | 元数据组件独审通过，44项接收控制和11项原数学检查独立复现 | [独审](current-validation/reuse-admission/final-independent-review.json)；真实原件、盲法/反馈时序与正式统计仍待完成 |',
        f'| 现版完整统计接续 | {handoff_label}；原数学核心保留 | [使用说明](current-validation/statistics-handoff/README.md)；真实设计、双人独立首判及盲裁定仍待核实接入 |',
        '| 补样信息量规划 | 1170条中F任一机器阳性18条、I为37条，合并40条；40全取＋其余随机补抽方案可行 | [计数](current-validation/supplement-planning-counts.json)及[方案](current-validation/supplement-design-review.md)；未定总n或抽样 |',
        '| 正式独立指标及区间 | 未计算，尚不能判定通过或不通过 | A/B首判、另行裁定、权重和覆盖核查 |',
        '| 真人复核对照 | 已计算并独立核验200条与当前规则/LLM的原始及原权重指标，保留历史120/80与待定 | [对照报告](human-review-comparison/results/AI初评与真人复核对照结果.md)；用途为AI初评后真人复核的描述性对照，独立验收仍未完成 |',
        '| 检验小节写作 | 已按用户要求整理“独立检验”正文与10行结果表，如实保留AI初评后真人复核流程 | [正文与结果表](human-review-comparison/results/独立检验-正文与结果表.md)；未将标题当作独立准确性验收完成证据 |',
        '| 重复稳定性及W/H敏感性 | 见下表；尚无最终稳定性结果 | 沿现有执行及既定额度收尾 |',
        '| 中断后的机器接续 | 13次遗留尝试按未知退出码登记技术失败；已修复历史进程编号复用及本机运行路径误判，原计划实际接续 | [实际接续记录](stability-durable-supervisor/ROOT-resume-03-confirmation.json)；原结果、模型参数及max3额度保持 |',
        '| 稳定性材料版本 | 800/800条与当前v16材料一致；W条件800份仅改变JSON展示格式 | [核查](current-validation/stability-material-compatibility.json)；现有运行可继续 |',
        '| 注意力结论稳健性 | 已完成同版情景及留一结果汇总；存在实质反例 | [汇总](robustness/findings.md) |',
        '| 当前分歧证据 | 已完成旧审核与当前版本对照；60项仅作有限诊断 | [汇总](disagreements/findings.md) |',
        '| 真人复核后的重点分歧 | 完成F八项及S三项理由对接；定位权重集中及具体规则问题 | [分歧与权重解释](human-review-comparison/results/复核分歧与权重解释.md)；隔离修正状态见下文，当前生产结果未替换 |',
        f'| E/Ec逐项原文诊断 | 14项已核对并经独立只读复核；12项有规则漏识别研发依据，2项保留概念或承接边界争议 | [E诊断](human-review-comparison/results/E-disagreement-source-diagnosis.md) · [Ec诊断](human-review-comparison/results/Ec-disagreement-source-diagnosis.md)；{ee_label} |',
        f'| 儿童适宜剂型缺口修正 | {f_label} | [候选结果](rule-repair-v14/F/candidate-summary.json)；属于开发检查，不替代人工独立检验 |',
        f'| S/F修正的影响范围 | 静态范围独审完成：2082条可能受影响，2399条继承原实际来源；15项范围控制通过 | [范围与依据](rule-repair-v12/population-impact-preparation/README.md)；{v12_execution_label} |',
        f'| 临床安全性误排修复 | {v13_label} | [353项修复检查](rule-repair-v13/candidate-summary-attempt02.json) · [最终有限复核](rule-repair-v13/final-independent-review.json)；原01402/I材料失败及15待定保留，未宣称全部硬断言通过 |',
        '| 后续候选曝光范围 | 实际查阅27条后，较v12候选新增3条曝光；未来v13b采用后剩余1151、曝光3330 | [增量登记](rule-repair-v13/prospective-development-exposure-addendum.json)；当前v11登记、原权重均保持，未新抽样 |',
        '| 技术失败归因 | 已查明不同机制和兼容边界；当前进程状态见下表 | [诊断](stability-diagnostics/diagnosis.md) |',
        '| 全文及DOCX/PDF | 尚未进入新全文修订，既有底稿保留 | 必要验证验收完成后修订并逐页核验 |', '',
        '## 当前后台运行', '',
        f"控制器PID及出生时间核验：{('PID' + str(controller['pid']) + '，' + controller['lstart'] + '，仍在运行') if controller_live else '本次未确认存活；须核对完成记录，不自动重启'}。原PID13924状态：{'仍在运行' if original_live else '已不在原身份下运行'}。", '',
        f"外部终态确认且返回码未知的旧尝试共{sum(r['attempt_counts'].get('external_unknown_returncode_closures', 0) for r in observation['conditions'].values())}次，单列为技术失败；未伪造原父进程退出回执，未恢复重试额度。", '',
        '| 条件 | 有效批/条 | 重试耗尽批/条 | 实时运行批/条 | 未启动批/条 | 其他待核批/条 |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    states = ('technical_valid_selected', 'technical_exhausted', 'confirmed_live', 'not_started', 'between_attempts_or_requires_attention')
    for condition, result in observation['conditions'].items():
        values = [f"{result['batch_counts'].get(s, 0)}/{result['record_counts'].get(s, 0)}" for s in states]
        lines.append('| ' + condition + ' | ' + ' | '.join(values) + ' |')
    lines += [
        '', '技术有效仅表示通过接收检查；技术失败不等于编码错误。失败和待定均不填0，成功子集不代表完整样本。', '',
        'R1/R2/R3为同条件独立重复；W为JSON展示格式扰动，H为请求首行等义表述变化。它们与已完成的统计口径稳健性分析分开报告。', '',
        '原800条统计仍保留历史分组和原抽样概率：remaining600中现有427条剩余、173条后来曝光；exposed200仍全部曝光。当前交叉身份合计427/373，不把历史600条称为当前全部未开发，也不据此追改权重。', '',
        '验收口径：人工A/B逐维κ≥0.80；规则与LLM分别对可信参照的κ/P/R/F1≥0.80。机间κ、稳定性及其他诊断不机械增加统一0.80门槛。', '',
        '## 本轮新增成果及结论范围', '',
        '1. **稳健性已归并。** 总体经济性第一、公平性最后在两机8/9个列名口径及51/51次总体留一中保持；排除年度系列后两机均变为安全性第一、经济性最后。年度系列占42.62%条款，贡献规则89.73%、LLM85.85%的经济性阳性赋值。9口径中有数值重复，不是9次独立实验。', '',
        '2. **部门和年度结论已查反例。** 药监安全第一、医保经济第一在既有9口径及本部门留一中保持；卫健首位随联合来源或一份用药安全文件的排除而变化。2018—2025主表35个年度增减方向中，两机29个一致。正文不能把这些结果统称为所有口径排序不变。', '',
        '3. **旧分歧审核已校正用途。** 当前925项二元分歧、270项一方待定；旧final130仅9项仍同材料同标签，另51项仅为材料及数值匹配的旧辅助AI语义证据。60项诊断样例不能代表全体错误率，剩余865项二元与270项待定未被本次归并覆盖。', '',
        '4. **技术失败已分型。** 真实事件支持部分PDF证据编号不兼容；多数非文本拒绝涉及PNG，不能由PDF候选一并修复。另有真实声明/引文/格式错误，以及网络恢复后触发原无error契约的拒绝。完整证据和未部署建议见技术诊断。', '',
        '5. **200条版本兼容已核实，独立身份需另核。** 原抽样的120/80是历史设计，不等于现版仍有120条未参与开发。已有曝光台账确认原120中至少29条后来用于开发；旧200接入只绑定旧机器，不能直接改路径当现版独立验收。手册与当前冻结版逐字相同，400/400份A/B材料清单绑定与v16一致，唯一改变的01402不在200样本中，因此现有表可继续填写。旧frame解析缺陷已有封存后续实现修复，本轮5项元数据复用核查通过。保留已开始的人工原表和首判，不追改旧域及权重；未将其余91条预认定为充分的现版独立样本。', '',
        '6. **当前验证所需元数据已补齐。** 已登记完整4481条开发曝光框：在历史曝光基础上核对473个已记录开发ID，并按3754个文本家族闭合，得到1261条剩余、3220条曝光；旧200中109条曝光、91条剩余。独审已核清旧235个控件及v6—v8输入来源，没有发现已知开发材料留在剩余域。剩余域成员身份与样本独立性、信息量充分是不同问题；尚未删除旧样本、改权重或另抽样。当前两机4481条真实来源及11,689项文件绑定、唯一性和材料一致性均已核验，但这不是准确性验收。', '',
        '7. **已有人工工作可纳入新的补充设计。** 旧200嵌套于旧800，后续开发又依赖同一800，不能直接删29后以旧概率验证当前固定1261。候选方案将旧91全部作为新设计必取组，再在其余1170中作分层随机抽样；这样保留已有工作，并使用新设计概率估计当前剩余域。旧权重不被改写。如实时序元数据组件与完整统计接续候选均已独审通过；真实原件、实际盲法/反馈证据仍待提供。当前补充数量待工作量答复，没有新抽样或正式指标。', '',
        '8. **补样需要照顾稀少维度。** 当前1261条任一机器阳性S/E/Ec/I/F为126/72/153/39/20；旧91为8/6/8/2/2；其余1170为118/66/145/37/18。计数已独立复算一致。建议全部纳入F或I任一阳性的40条，再从其余1130按部门随机抽取；现有数学和接收组件支持该方案，无需修改核心。无机器阳性不等于真实阴性，仍须保留其抽中机会；这些计数不能保证100或200条充分，当前未定总n或抽样。', '',
        f'9. **实际结果到达后的计算流程已准备。** {handoff_label}。[独审](current-validation/statistics-handoff/independent-review.json)复现20项端到端、14项补充Excel和14项定向对应关系检查；混合抽样与全查设计的完整数学结果均与原核心一致，28个数学/状态函数保留。原200接收与重读的Excel相对路径兼容也已修复；补充组可继续交Excel。元数据齐备不等于人工填写完成，仍须结合覆盖、失败和共同可比较数判读。真实登记、新抽样和正式准确性统计尚未完成；人工提交状态见上表。', '',
        f'10. **S/F隔离候选已完成有限回归。** v12修正数据安全对象、处方禁忌核查和公平性当前行动范围。331项开发控制中316项为硬预期，315项通过；唯一旧01402/I在基线也失败，原因是旧控制仍用未补全条款的历史材料，原预期与失败均保留。另加当前v16材料01402控制通过；此前7项F新增回归已消除，E/Ec/I完整决定及来源状态未变。静态范围已独审：2082条入选、2399条继承原实际v7/v9/v10来源；材料、完整代码排除证明和已采用版本链均核齐。{v12_execution_sentence}[完整回归](rule-repair-v12/unified-attempt02/summary.json) · [范围独审](rule-repair-v12/population-impact-preparation/independent-review.json)。', '',
        '11. **新版本的独立样本范围须重新登记。** 本次200条复核已用于v12开发选择，不能再作为v12的独立验证样本。按既有文本家族闭合，候选未来采纳时将新增107条曝光，剩余1154条、曝光3327条；当前v11的1261/3220登记及旧权重未改。以上第7—8项仅为v11历史准备，不能直接套用于v12。[前瞻曝光记录](rule-repair-v12/prospective-development-exposure.json)。', '',
        '## 接续顺序与剩余依赖', '',
        f'- {runtime_label}；全五条件及已启动进程进入真实终态后，ROOT接续一次原统计入口（控制器不会自动计算），核对覆盖、共同可比集合、失败和待定。继续保留原首答、拒绝原因和每批最多3次额度；最终统计文件以独占方式创建，不覆盖已有结果。',
        f'- 真人200条：{human_label}。收到真实A/B提交后先保存原件、核实独立性并计算协商前一致性，再另行裁定。保留原120/80历史抽样事实，另报后续开发曝光；核清现版独立资格及统计适用范围后决定衔接，不能擅自重标域并沿用旧权重。',
        '- 若原200先于新设计及抽样完成而交回，先保存原件；不得用其答案或一致性结果选择新设计，再追认人工反馈未进入设计。实际盲法、反馈与时序须如实记录。',
        '- 正式参照形成后，执行机器逐维准确性、区间和同样本结构误差验收；当前没有把未计算项写为达标或不达标。',
        '- 必要验证完成后才进入整篇正文修订和DOCX/PDF逐页核验。底稿、期刊要求及文献准备材料已保留。', '',
        '[全量结果工作簿](../09-delivery/full4481-results-20261012-sol/全量编码与指标结果-20261012.xlsx) · [原完整目标及历史调整](../完整Goal指令.md)',
    ]
    (HERE / '总进度.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in observation.items() if k != 'conditions'}, ensure_ascii=False))
    print(json.dumps({c: {k:v for k,v in r.items() if k != 'batches'} for c,r in observation['conditions'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
