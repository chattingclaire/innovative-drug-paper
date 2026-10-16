"""Reuse only preregistered 36 random IDs; refresh all materials, never reuse old outputs."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[2]
EXPECTED_INPUT='6fa91f237c8762fb117cb6c920d6a689dd65ee35f3b938db2f0a569bf9b965b8';EXPECTED_PROMPT='5b8afc4459839ceb77bb3e1ff78e42f6bf81379c3316cb1ef6d776fca90d285d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 full=BASE/'effective_blind_inputs_v30.jsonl';prompt=HERE/'完整系统提示词-v30-候选02.txt';assert sha(full)==EXPECTED_INPUT and sha(prompt)==EXPECTED_PROMPT
 prior=ROOT/'outputs/final-three-department-20261007/llm-v29/stability_sample_manifest_v2.json';old=json.loads(prior.read_text());assert old['groups']==['NMPA','NHSA','NHC'] and old['n']==36 and old['n_per_department']==12
 allrows={r['id']:r for r in [json.loads(l) for l in full.read_text().splitlines() if l.strip()]};ids=[rid for group in old['groups'] for rid in old['ids'][group]];assert len(ids)==36 and len(set(ids))==36
 dest=HERE/'stability-v30';dest.mkdir(exist_ok=True);packet=dest/'same_batch_36.jsonl';newrows=[allrows[rid] for rid in ids];data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in newrows)
 if packet.exists():assert packet.read_text()==data
 else:packet.write_text(data)
 order=dest/'完整提示词-仅维度执行顺序扰动.txt';ordered_prompt=prompt.read_text()+'\n\n--- 稳定性检验的唯一顺序扰动 ---\n本次逐维阅读、核对并独立判定的执行顺序为 F、I、Ec、E、S。其余定义、对象、上下文用途、纳入排除、证据要求及输出Schema全部不变。返回标签仍使用原Schema字段名称。\n'
 if order.exists():assert order.read_text()==ordered_prompt
 else:order.write_text(ordered_prompt)
 manifest={'status':'frozen_before_new_stability_model_calls','design':'same 36 rows in exactly one batch; two normal-prompt actual independent calls and one dimension-evaluation-order-only perturbation call','same_material_order_and_batch_composition':True,'n':36,'n_per_department':12,'seed_of_previously_frozen_ID_selection':old['seed'],'selection_source':str(prior),'selection_source_sha256':sha(prior),'selection_reuses_only_prior_random_IDs_not_labels_outputs_or_stability_scores':True,'old_model_outputs_used':False,'material_policy':'Every record refreshed by exact ID from current completed input; old materials and results are not used.','full_input_sha256':sha(full),'sample_sha256':sha(packet),'normal_prompt_sha256':sha(prompt),'order_prompt_sha256':sha(order),'order_perturbation_only':'append dimension evaluation order F,I,Ec,E,S; same definitions and output schema','ids':old['ids'],'model':'gpt-5.6-sol','reasoning_effort':'medium','temperature_and_provider_revision':'not_exposed','not_independent_human_validation':True}
 write(dest/'sample_and_execution_plan.json',manifest);print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':main()
