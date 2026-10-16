"""Release only label-free full inputs to explicitly requested GPT-5.6 Sol.

Native Codex agent execution is recorded as such, not misreported as a raw API
or Claude replication. The current reference and held-out labels are not read.
"""
from pathlib import Path
import datetime
import hashlib
import inspect
import json
import random
import llm_recoder

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'llm_runs/gpt56-sol-v13-native-1'
VERSION = 'llm-v4-protocol13-gpt56-sol-native-1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    inputs = HERE / 'current_llm_inputs.jsonl'
    source_manifest = json.loads((HERE / 'current_input_manifest.json').read_text())
    assert sha(inputs) == source_manifest['output_hashes'][inputs.name]
    rows = [json.loads(line) for line in inputs.read_text().splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == 4924
    seed = 2026092702
    random.Random(seed).shuffle(rows)
    instructions = '''\n【本次执行与留痕】
你执行的是 gpt-5.6-sol 的独立 LLM 方法。不是人工编码员，不是开发规则的研究者。
仅可阅读给定分片目录的规范、schema、材料和校验工具，以及你自己写入该目录的结果。禁止读取其他路径、其他分片结果、任何参考标签或机器输出；不访问网页、不调用其他模型、不另委派子 agent。
逐条完整阅读 text 和所附必要 contexts，再独立逐维作语义判断。脚本只用于读写、组装你已逐条明确作出的判断、检查结构和逐字引文；不能写关键词/正则/启发式分类器，不能根据模板自动推断标签、理由或证据，不把未读条目默认为0或待定。
每批 input-NNN.json 对应 output-NNN.json。输出顶层和行字段严格遵循 output_schema.json，顺序与原批次一致。保存第一次完整输出后不得覆盖；如果发现格式或引文录入错误，将更正另存 correction-NNN-01.json 并说明原值、改值和原因，原始结果一直保留。不得因其他方法/评审结论修改答案。
读文件的工具输出如果发生截断，继续分段读取直至完整；不得仅根据文本预览编码。每批仅在本人语义判断完成后保存，再运行 validate_output.py 做结构与逐字引文检查。验证不提供他人答案。
按批持续执行直至本分片所有材料完成，不需要再征求许可。完成时写 completion.json，仅记录分片、模型请求名、完成时间、批次数、总条数、每份输入/输出SHA256、首次输出校验状态。真实底层模型修订号、温度、随机种子不可获取时写未知，不能猜。
向主 agent 的中途和最终回复只报告完成数量、文件路径、SHA256和执行问题，不返回样本内容、标签、正类比例或指标。出现需要改变定义的疑问先报告并暂停该疑问，不自行扩充定义。
'''
    prompt = llm_recoder.system_prompt() + instructions
    schema = llm_recoder.schema()
    validator = '''"""No reference labels or inference: JSON shape and literal-evidence audit only."""\nimport json, sys\nfrom pathlib import Path\nDIMS=['S','E','Ec','I','F']\n'''
    validator += inspect.getsource(llm_recoder.iter_text) + '\n' + inspect.getsource(llm_recoder.validate)
    validator += '''
def shape(value, spec, location='root'):
    problems=[]
    if 'enum' in spec and not any(type(value) is type(v) and value==v for v in spec['enum']):
        problems.append(location+':enum')
    kind=spec.get('type')
    if kind=='object':
        if not isinstance(value,dict):return problems+[location+':object']
        keys=set(spec['properties'])
        if set(value)!=keys:problems.append(location+':fields')
        for k in keys & set(value):problems+=shape(value[k],spec['properties'][k],location+'.'+k)
    elif kind=='array':
        if not isinstance(value,list):return problems+[location+':array']
        if spec.get('uniqueItems') and len({json.dumps(v,sort_keys=True) for v in value})!=len(value):problems.append(location+':duplicate')
        for i,v in enumerate(value):problems+=shape(v,spec['items'],location+f'[{i}]')
    elif kind=='string':
        if not isinstance(value,str):problems.append(location+':string')
        elif len(value)<spec.get('minLength',0):problems.append(location+':short')
    return problems

if __name__=='__main__':
    packet=Path(sys.argv[1]);output=Path(sys.argv[2]);here=Path(__file__).resolve().parent
    assert packet.resolve().parent==here and output.resolve().parent==here
    inp=json.loads(packet.read_text())['rows'];result=json.loads(output.read_text())
    errors=shape(result,json.loads((here/'output_schema.json').read_text()))
    if not errors:errors+=validate(result,inp)
    print(json.dumps({'n':len(inp),'errors':errors,'valid':not errors},ensure_ascii=False))
    sys.exit(1 if errors else 0)
'''
    batches = [rows[i:i+10] for i in range(0,len(rows),10)]
    plan = {'method_version':VERSION,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'requested_model':'gpt-5.6-sol','reasoning_effort':'high',
        'execution':'native Codex collaboration agents with explicit model override; fresh history for every shard',
        'provider_internal_revision':'unknown','temperature':'not_exposed',
        'batch_size':10,'batch_count':len(batches),'shard_batch_cap':42,
        'n':4924,'display_shuffle_seed':seed,'reference_labels_supplied':False,
        'input_truncated':False,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
        'source_input_sha256':sha(inputs),'preparation_script_sha256':sha(Path(__file__)),
        'manual_sha256':sha(HERE/'protocol-v1.3.md'),
        'first_output_policy':'Preserve first complete outputs; separately log corrections without score-selected reruns.',
        'limitations':['Native agents retain within-shard conversation state; batches are not independent API calls.',
            'Only prescribed file reads/writes are allowed by instructions; filesystem tool availability itself is not disabled.',
            'AI references are not human gold standards and may share systematic model errors.'],
        'shards':[]}
    for offset in range(0,len(batches),42):
        index=offset//42+1;dest=ROOT/f'shard-{index:02d}';dest.mkdir()
        (dest/'执行规范.txt').write_text(prompt)
        (dest/'output_schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
        (dest/'validate_output.py').write_text(validator)
        meta={'shard':index,'n':0,'packets':[],'files':{}}
        for j,batch in enumerate(batches[offset:offset+42],1):
            f=dest/f'input-{j:03d}.json'
            f.write_text(json.dumps({'stage':'independent_method_prediction','rows':batch},ensure_ascii=False,indent=2)+'\n')
            meta['packets'].append({'name':f.name,'n':len(batch),'ids':[r['id'] for r in batch],'sha256':sha(f)})
            meta['n']+=len(batch)
        for n in ['执行规范.txt','output_schema.json','validate_output.py']:meta['files'][n]=sha(dest/n)
        (dest/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        plan['shards'].append({'index':index,'n':meta['n'],'batches':len(meta['packets']),'manifest_sha256':sha(dest/'manifest.json')})
    (ROOT/'run_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    amendment={'created_at':plan['created_at'],'user_instruction':'换一个model跑吧 用gpt-5.6-sol跑吧',
        'prior_release_sha256':sha(HERE/'H427/release_freeze.json'),
        'new_run_plan_sha256':sha(ROOT/'run_plan.json'),
        'fresh_H427_reference_labels_read_by_root':False,
        'disclosure_order':'Do not inspect H427 reference judgments until all current LLM predictions are sealed.',
        'old_Claude_attempt':'Only two synthetic units; authentication failure; no empirical predictions.'}
    (HERE/'H427/LLM模型变更冻结-20260927.json').write_text(json.dumps(amendment,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'n':4924,'batches':len(batches),'shards':len(plan['shards']),'root':str(ROOT),'plan_sha256':sha(ROOT/'run_plan.json')},ensure_ascii=False))

if __name__=='__main__':main()
