"""Symmetric, answer-free source rereading; never overwrite initial blind packets."""
from pathlib import Path
import copy, datetime, hashlib, json

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jl(p):return {x['id']:x for x in map(json.loads,Path(p).read_text().splitlines())}
def write(p,x):
    assert not p.exists(),f'preserve existing file: {p}'
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
version='v11'
old=jl(HERE/'effective_blind_inputs_v9.jsonl');new=jl(HERE/f'effective_blind_inputs_{version}.jsonl')
assert set(old)==set(new) and len(new)==4924
changed={k for k in old if old[k]!=new[k]}
assert all(old[k]['text']==new[k]['text'] for k in old)
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text())
schema=json.loads((HERE/'confirmation/结果schema.json').read_text())
schema['title']='Five-dimension independent source rereading '+version
schema['properties']['material_version']={'const':version}
write(HERE/f'confirmation/结果schema-{version}.json',schema)
bindings={}
for coder in ('A','C'):
    rows=[]
    for m in sorted((m for m in mapping if m['coder']==coder and m['original_id'] in changed),key=lambda m:m['blind_id']):
        original=new[m['original_id']]
        rows.append({'id':m['blind_id'],**{k:copy.deepcopy(original[k]) for k in ['text','source_title','pages','contexts','context_usage']}})
    packet={'material_version':version,'rows':rows}
    dest=HERE/f'confirmation/agent-{coder}/补充材料-{version}.json'
    write(dest,packet);bindings[coder]={'path':str(dest),'sha256':sha(dest),'n':len(rows),'blind_ids':[r['id'] for r in rows]}
assert {m['original_id'] for m in mapping if m['coder']=='A' and m['original_id'] in changed}=={m['original_id'] for m in mapping if m['coder']=='C' and m['original_id'] in changed}
instructions=f'''本轮仅修复源材料，编码手册v1.3和操作说明v1.4均不变。
请只读本方“补充材料-{version}.json”，逐条阅读当前原文及全部新语境，独立提交S/E/Ec/I/F二元判读、理由、逐字证据及来源子类。
补充包包括所有本方材料发生变化的条目，不只包括首次待定。不得读取另一方、任何机器或统计结果。
新增实际列表后项、明确引用条文及修正列表边界只供理解当前命题；不能把上下文标签复制到本单元，也不增加分析单元。
原首次结果保持不动。按结果schema-{version}.json另存本方“补料复读结果-{version}.json”，input_packet_sha256使用新补充包实际SHA。
若语义判断改变，另存本方“补料复读变更说明-{version}.json”，逐项注明变化及所依据的新增/删除原文；不为追求任何指标改标。
如果发现真实仍缺材料，具体指出所缺原文及其对判读的影响，不猜标签。完备材料下边界争议给本人0/1并留issues。
'''
write(HERE/f'confirmation/补料任务说明-{version}.json',{'instructions':instructions,'source_only':True,'standard_unchanged':True,'first_results_preserved':True,'human_validation_completed':False})
manifest={'created_at':datetime.datetime.now().astimezone().isoformat(),'version':version,'source_only_rereading':True,
 'old_inputs_sha256':sha(HERE/'effective_blind_inputs_v9.jsonl'),'new_inputs_sha256':sha(HERE/f'effective_blind_inputs_{version}.jsonl'),
 'all_context_changed_ids':sorted(changed),'all_sampled_changed_items_in_both_packets':True,
 'old_first_results_unchanged':True,'label_answers_in_packets':False,'same_real_items_for_A_C':True,
 'packets':bindings,'schema_sha256':sha(HERE/f'confirmation/结果schema-{version}.json'),
 'instruction_sha256':sha(HERE/f'confirmation/补料任务说明-{version}.json')}
write(HERE/f'admin/source_rereading_{version}_freeze.json',manifest)
print(json.dumps({'version':version,'changed_corpus_n':len(changed),'rereading_n_per_coder':{k:v['n'] for k,v in bindings.items()}},ensure_ascii=False))
