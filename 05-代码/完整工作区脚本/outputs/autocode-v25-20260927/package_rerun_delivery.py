"""Package reproducible completed artifacts; never modifies frozen raw outputs."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import zipfile

HERE=Path(__file__).resolve().parent
DEST=HERE.parent/'01a0dbb7-43f0-7a61-a367-7f0c814ee9d4/两方法重跑-20260927'
LLM=HERE/'llm_runs/gpt56-sol-v13-native-1'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    required=[LLM/'prediction_seal.json',
        HERE/'rerun_comparisons/current1268/analysis_binding.json',
        HERE/'rerun_comparisons/H427/analysis_binding.json',
        HERE/'rerun_comparisons/LLM更正影响/correction_audit.json',
        HERE/'workbook_verification.json',
        DEST/'AI评审A-1695条-同版首次结果.xlsx',
        DEST/'AI评审C-1695条-同版首次结果.xlsx',
        DEST/'自动与LLM重跑-同版对照.xlsx',DEST/'本轮结论与使用说明.md']
    assert all(p.is_file() for p in required),'Complete and inspect all deliverables before packaging'
    assert (HERE/'workbook_independent_verification.json').is_file()
    parallel=HERE/'rerun_comparisons/full_corpus_parallel/parallel_full_corpus.json'
    assert parallel.is_file(),'Complete full-corpus parallel summaries before release'
    target=DEST/'两方法重跑-完整复核材料.zip'
    manifest_target=DEST/'文件校验清单.json'
    assert not target.exists() and not manifest_target.exists(),'Do not overwrite a released package'
    DEST.mkdir(parents=True,exist_ok=True)
    context_target=DEST/'完整分析单元与语境.jsonl'
    if context_target.exists():assert sha(context_target)==sha(HERE/'current_llm_inputs.jsonl')
    else:shutil.copyfile(HERE/'current_llm_inputs.jsonl',context_target)
    selected={}
    def add(path,arcname):
        assert path.is_file(),path
        assert arcname not in selected,arcname
        selected[arcname]=path
    # Explicitly restricted to research inputs, outputs, code and audit files.
    # Runtime auth probes, credentials, caches and unrelated project files are excluded.
    root_names=[
        'protocol-v1.3.md','current_input_manifest.json','current_rule_inputs.jsonl',
        'current_llm_inputs.jsonl','current_1268_references.jsonl',
        'build_current_inputs.py','prepare_gpt56_native.py','collect_gpt56_native.py',
        'baseline_candidate17.py','policy_coding_v25.py','policy_coding_v25_review_fix.py',
        'rerun_rules.py','comparison_statistics.py','analyze_current_reruns.py',
        'analyze_llm_corrections.py','rerun_analysis_plan.json','LLM更正影响分析预登记.json',
        'rerun_analysis_plan_amendment_null.json','统计实现-独立只读复核.md','统计实现-独立只读复核.json',
        '统计实现-null修复复核.md','统计实现-null修复复核.json',
        '统计实现-规则待定适配复核.md','统计实现-规则待定适配复核.json',
        'LLM执行组装审计.md','LLM执行组装审计.json',
        'rerun_analysis_plan_amendment_rule_null.json',
        'test_comparison_statistics.py','test_rerun_sensitivities.py',
        'test_policy_coding_v25.py','test_v25_review_repairs.py',
        'prepare_rerun_delivery.py','build_rerun_workbooks.mjs','package_rerun_delivery.py',
        'verify_rerun_workbooks.py','workbook_independent_verification.json','write_rerun_report.py',
        'prepare_diagnostic_cases.py','diagnostic_case_selection_plan.json','正文主分析衔接计划.json',
        '本轮两方法重跑说明.md','方法与新验证框评估.json','方法与新验证框评估.md',
        '新验证框-新增暴露接入.json','新验证框-新增暴露接入.md',
        '新验证框-新增暴露接入-根复现.json','integrate_incremental_exposure.py',
        'release_residual_review.py','workbook_verification.json','workbook_layout_verification.json','full_corpus_handoff_verification.json']
    for name in root_names:add(HERE/name,'研究复现/'+name)
    paper_root=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
    full_script=paper_root/'重跑接入准备/summarize_parallel_full_corpus.py'
    full_summary=json.loads(parallel.read_text())
    assert sha(full_script)==full_summary['script_sha256']
    add(full_script,'正文接入代码/summarize_parallel_full_corpus.py')
    source_map=paper_root/'来源条目与分析单元明细.json'
    assert sha(source_map)==full_summary['input_bindings'][str(source_map)]
    add(source_map,'正文接入代码/来源条目与分析单元明细.json')
    for folder in [HERE/'H427',HERE/'rule_runs/v25-candidate-3',HERE/'analysis_pre_null_fix_snapshot',
                   HERE/'analysis_pre_rule_null_adapter_snapshot',HERE/'rerun_comparisons_attempt1_rule_null_failure',
                   LLM,HERE/'rerun_comparisons']:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and p.suffix in {'.json','.jsonl','.py','.md','.txt','.csv'} and '__pycache__' not in p.parts:
                add(p,'研究复现/'+str(p.relative_to(HERE)))
    clarifications=HERE.parent/'validation-expansion-20260926/V600-frozen-inputs/protocol_clarifications.md'
    add(clarifications,'研究复现/统一澄清.md')
    add(clarifications,'validation-expansion-20260926/V600-frozen-inputs/protocol_clarifications.md')
    for p in required[5:]:add(p,'交付/'+p.name)
    add(context_target,'交付/'+context_target.name)
    created=datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest={'created_at':created,'encoding':'UTF-8; labels 0/1/待定',
        'primary':'First complete outputs; recorded corrections are secondary only',
        'reference':'Current v1.3 AI A/C, not human gold standard',
        'files':{name:{'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in sorted(selected.items())}}
    raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sorted(selected.items()):z.write(p,name)
        z.writestr('文件校验清单.json',raw)
        z.writestr('阅读顺序.txt','先读交付/本轮结论与使用说明.md，再看三份Excel。正式统计以研究复现/rerun_comparisons为准；attempt1目录仅保留一次接口失败的审计，不作为正式结果。\n原始预测、首次A/C、输入、规范、校验和更正分别保留。代码对既有输出目录设有防覆盖保护；若需复算，请在另存副本中操作。\n本包含完整分析单元和语境；原始政策文件仍见原研究资料目录。原生agent模型底层修订号和温度未暴露，不能承诺逐字复现模型生成。\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name,meta in manifest['files'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==meta['sha256'],name
    manifest['archive']={'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target)}
    manifest_target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'archive':str(target),'files':len(selected),'bytes':target.stat().st_size,
        'archive_sha256':sha(target),'manifest':str(manifest_target)},ensure_ascii=False))

if __name__=='__main__':main()
