"""Retain verified literature and bind implementation prose to this actual run."""
from pathlib import Path
from fractions import Fraction
from hashlib import sha256
import json
import re

ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text())
def digest(p):return sha256(Path(p).read_bytes()).hexdigest()

def main():
    coding=read('三部门编码指标.json');attention=read('三部门注意力分布与敏感性.json')
    execution=read('最终LLM执行独立核验.json')
    stability=read('llm-v30/stability_comparison_v30.json')
    for name,target in [('三部门编码指标核验.json','三部门编码指标.json'),('三部门数据独立QA.json','三部门注意力分布与敏感性.json')]:
        qa=read(name);assert qa['status']=='passed' and qa['target_sha256']==digest(ROOT/target)
    assert execution['status']=='passed' and execution['n']==4924
    lp=Path(coding['method_bindings']['llm']['path'])
    assert execution['predictions_sha256']==digest(lp)
    assert coding['method_bindings']['rule']==attention['method_bindings']['rule']
    for key in ['method','path']:
        assert coding['method_bindings']['llm'][key]==attention['method_bindings']['llm'][key]
    assert lp.resolve().is_relative_to(ROOT)
    assert coding['method_bindings']['llm']['method']=='llm_gpt56_sol_v30'
    assert coding['method_bindings']['rule']['method']=='rules_v31'
    manifest_path=lp.parent/'final_manifest.json';manifest=json.loads(manifest_path.read_text())
    assert manifest['status']=='complete_validated_full_corpus' and manifest['predictions_sha256']==digest(lp)
    assert manifest['effective_input_sha256']==digest(ROOT/'effective_blind_inputs_v30_v3.jsonl')
    assert manifest['shared_rule_input_sha256']==digest(ROOT/'rule_inputs_v31_shared_v3.jsonl')
    assert manifest['source_material_version']=='v3'
    assert manifest['system_prompt_sha256']==digest(ROOT/'llm-v30/完整系统提示词-v30-候选03.txt')
    assert stability['status']=='computed_from_new_actual_model_calls'
    assert stability['candidate']=='03' and stability['production_predictions_sha256']==digest(lp)
    n_records=len(coding['records'])
    n_intervals=sum('ci95' in m for row in coding['records'] for m in row['metrics'].values())
    scenario_counts={method:1+len(v['scenarios'])+len(v['leave_one_policy_file_out']) for method,v in attention['sensitivities'].items()}
    assert n_records==200 and n_intervals==1280
    assert len(scenario_counts)==4 and set(scenario_counts.values())=={61}
    assert manifest['n']==4924 and attention['population_n']==4481 and attention['background_n']==443
    plan=json.loads((lp.parent/'run_plan.json').read_text())
    assert plan['batch_count']==197 and plan['batch_size']==25 and plan['n']==manifest['n']
    template=ROOT/'指标依据与理论对齐-文献依据底稿.md'
    text=template.read_text()
    text=re.sub(r'日期：2026年10月7日。用途：.*?\n',
        '日期：2026年10月7日。用途：本轮三部门修订的方法依据、变量定义及真实执行绑定。文献职责沿用已核验原始来源，执行状态和数值仅采用本轮规则v31、LLM候选03与最终同版v3材料。\n',text,count=1)
    text=text.replace('实际阅读的原始来源及其具体用途','已核验的原始来源及其具体用途')
    text=text.replace('Cohen（1960）为κ的原始出处，最终文稿对应[44]：','Cohen（1960）为κ的原始出处：')
    text=text.replace('明确研发支持及创新资格比较优势','明确针对药物研发创新的支持措施及创新资格比较优势')
    text=text.replace('创新性指实质创新属性与研发支持','创新性指实质创新属性、注册创新分类、明确针对药物研发创新的支持措施及创新资格比较优势')
    text=text.replace('药品临床管理要求操作化','药品临床管理难度操作化')
    old_root=str(ROOT.parent/'final-three-department-20261007')
    text=text.replace(old_root+'/recalculate_three_department_coding_metrics.py',str(ROOT/'recalculate_three_department_coding_metrics.py'))
    comps=stability['comparisons']
    assert len(comps)==3 and all(c['n']==36 for c in comps)
    repeat=next(c for c in comps if c['comparison_identity']=='strict_same_prompt_same_36_row_batch_repeat')
    order=next(c for c in comps if c['comparison_identity']=='equivalent_prompt_dimension_order_perturbation_same_36_row_batch')
    production=next(c for c in comps if c['comparison_identity']=='batch_composition_changed_recoding_difference_not_strict_repeat')
    def rate(c):return f"{round(c['all_five_labels_exact_agreement']*c['n'])}/{c['n']}（{c['all_five_labels_exact_agreement']*100:.2f}%）"
    implementation=(
        '本轮封存的gpt-5.6-sol候选03使用medium推理强度，最终选中197个批次覆盖4924个单元；三部门4481个单元进入主分析，443个中央单元保留作制度背景。实际请求、首输出及执行或引文校验失败后的同请求重跑均保存；不根据参照符合程度选择输出。全量校验回源补全5条列表语境后，对所在原批71/72共50条整批实际重跑并无条件采用，其他195批逐行证明实际请求材料与最终v3相同后保留；全部历史调用另存，不将197称为全部实际调用次数。最终规则与LLM逐单元使用相同原文及列表条件、对象范围和表头。首次A/C的标签及其原有可见材料保留，不将本轮同材条件追溯移写给A/C。'
        f"原先冻结的36条样本不含5条补料单元，三次实际稳定性调用的材料与最终v3子集逐行及字节完全相同。同提示同36条整批重复的五维标签完全一致率为{rate(repeat)}，维度顺序扰动为{rate(order)}；与生产25条分批输出的对照为{rate(production)}，另列为批次组成差异。逐维κ、四格与全部差异理由见《llm-v30/stability_comparison_v30.json》。这些检查衡量模型重复和提示敏感性，不改写为真人验证。真实全量执行与未机械修改输出的核验见本轮《最终LLM执行独立核验.json》；生产输出SHA256为`{digest(lp)}`。"
    )
    text=re.sub(r'实际封存的gpt-5\.6-sol v29.*?实际记录见.*?。',implementation,text,count=1)
    dims=['S','E','Ec','I','F'];groups={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
    descriptions=[]
    for method,label in [('rules_v31','规则v31全量'),('llm_gpt56_sol_v30','LLM候选03平行测量')]:
        vectors=[]
        for g,name in groups.items():
            values=[Fraction(attention['primary'][method][g]['dimensions'][d]['attention_share']['exact_fraction']) for d in dims]
            assert sum(values)==1
            vectors.append(name+'为'+'/'.join(f'{float(v)*100:.2f}%' for v in values))
        descriptions.append(label+'五维向量（S/E/Ec/I/F）中，'+'；'.join(vectors)+'。')
    vectors=''.join(descriptions)+'A/C设计加权点估计及不确定性另列，两套参照之间的范围不写成置信区间。上述数值绑定本轮《三部门注意力分布与敏感性.json》，正文以规则全量向量组织主描述。'
    text=re.sub(r'规则全量五维向量（S/E/Ec/I/F）中，.*?正文以规则全量向量组织主描述。',vectors,text,count=1)
    lines=text.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| LLM定稿版本 |'):
            lines[i]=f'| LLM定稿版本 | 真实候选03全量运行、模型可得标识及参数、最终同版v3完整语境、首输出、重复和维度顺序扰动 | 已完成真实gpt-5.6-sol 4924条；197批选用调用的工具事件为0，逐字引文、输入同一性与原输出重建通过。最终标签SHA256为`{digest(lp)}` |'
        elif line.startswith('| 三部门范围的指标重算 |'):
            lines[i]='| 三部门范围的指标重算 | 逐维可配对掩码、正类数量、四格及文件聚类区间 | 本轮接入规则v31与候选03，完成主1057与补充H411的200组分类比较及1280项文件聚类区间核验。三部门4481单元的注意力分布及4方法各含主口径的61种口径另算；不把开发复核称为新独立验证 |'
    text='\n'.join(lines)+'\n'
    text=text.replace('LLM作平行测量，逐项保留原文依据。','LLM作平行测量；规则保存命中与排除记录，LLM保存逐维理由及原文依据。')
    text=text.replace('依据读取：最新主DOCX、plan.md、指标与变量一致性审查、CAL-5D-v1.3、既有方法文献证据和政策原文核验。上述安排是报告与测量建议，没有变动任何既有标签、统计文件或主稿。',
        '依据：CAL-5D-v1.3、既有原始方法文献与政策来源核验，以及本轮冻结材料、真实调用输出、统计JSON及独立数值QA。文献核查范围保持原记录；本文件更新实施状态和结果绑定，不修改任何标签或统计值。')
    assert '真实gpt-5.6-sol v29全量' not in text and '规则v30，完成' not in text
    target=ROOT/'指标依据与理论对齐.md';target.write_text(text)
    sources=[template,ROOT/'三部门编码指标.json',ROOT/'三部门注意力分布与敏感性.json',ROOT/'最终LLM执行独立核验.json',ROOT/'llm-v30/stability_comparison_v30.json',manifest_path,lp]
    result={'status':'current_actual_results_bound','candidate':'03','rule_method':'rules_v31','llm_method':'llm_gpt56_sol_v30','source_sha256':{str(p):digest(p) for p in sources},'output_sha256':digest(target),'literature_scope':'Original source-review scope retained; implementation and numerical statements regenerated for current actual run.'}
    (ROOT/'指标依据与理论对齐.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Bound method basis to actual candidate03/v3 statistics')

if __name__=='__main__':main()
