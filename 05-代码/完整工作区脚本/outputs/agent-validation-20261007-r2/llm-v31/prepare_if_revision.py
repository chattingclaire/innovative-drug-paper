from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROUND=HERE.parent
OLD=ROUND.parent/'recall-revision-20261007/llm-v30'
HERE.mkdir(parents=True,exist_ok=True)
runner=(OLD/'run_production_v30.py').read_text().replace('LLM-binary-v30','LLM-IF-v31').replace('llm-v30-empty-','llm-v31-empty-').replace("HERE/'完整系统提示词-v30-候选02.txt'","HERE/'I-F复核提示词-v31.txt'")
(HERE/'run_production_v31.py').write_text(runner)
dim={'type':'integer','enum':[0,1]}
row={'type':'object','properties':{'id':{'type':'string'},'labels':{'type':'object','properties':{d:dim for d in ['I','F']},'required':['I','F'],'additionalProperties':False},'dimension_reasons':{'type':'object','properties':{d:{'type':'string'} for d in ['I','F']},'required':['I','F'],'additionalProperties':False},'evidence':{'type':'array','items':{'type':'object','properties':{'dimension':{'type':'string','enum':['I','F']},'source':{'type':'string','enum':['unit','context']},'quote':{'type':'string'}},'required':['dimension','source','quote'],'additionalProperties':False}},'innovation_subtypes':{'type':'array','items':{'type':'string','enum':['attribute','research_support','qualification_advantage']}},'fairness_subtypes':{'type':'array','items':{'type':'string','enum':['access','affordability','clinical_management','dimension_information']}}},'required':['id','labels','dimension_reasons','evidence','innovation_subtypes','fairness_subtypes'],'additionalProperties':False}
schema={'type':'object','properties':{'protocol_version':{'type':'string','enum':['CAL-5D-20260926-v1.3']},'execution_version':{'type':'string','enum':['LLM-IF-v31']},'release_stage':{'type':'string','enum':['final_binary_labels']},'rows':{'type':'array','items':row},'issue_records':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'status':{'type':'string','enum':['boundary_note','material_issue']},'description':{'type':'string'}},'required':['id','status','description'],'additionalProperties':False}}},'required':['protocol_version','execution_version','release_stage','rows','issue_records'],'additionalProperties':False}
(HERE/'output_schema_codex_compatible.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
prompt='''你是政策文本编码器。你只根据给定原文、完整上下文、冻结手册和共用操作说明，独立复核创新性I、公平性F两个维度。不得读取任何其他材料、调用工具、检索、运行代码或猜测其他方法答案。
本轮不判S/E/Ec，不把它们并入I/F。I/F仍是五维研究的原有两个维度；按以下同版标准逐条给0或1，不追求任何比例、排序或评分。
当前命题优先：上下文只能消解对象、条件、指代和表列，不把背景创新/保障复制到每个子项。逐项识别对象和完整谓词。对1给至少一个本单元连续逐字引文；依赖语境再给context连续逐字引文。对0给当前实际命题和排除边界。每维理由尽量30个汉字左右，但以准确为先。I/F子类型按真实依据填写；0必须空列表。
最终只返回规定JSON，protocol_version为CAL-5D-20260926-v1.3，execution_version为LLM-IF-v31，release_stage为final_binary_labels。每个输入ID原序输出一次。边界争议保留个人判断并在issue_records写明；若实质材料缺口导致无法判定，issue_records标material_issue，不得把不知情冒充可靠判断，发布端将阻止该批进入最终版本。
'''
prompt+='\n--- 完整五维语义手册 ---\n'+(ROUND/'protocol/完整五维手册-v1.3.md').read_text()
prompt+='\n--- 本轮统一操作澄清，优先解释对应边界 ---\n'+(ROUND/'共用操作说明-v1.4.md').read_text().split('## 版本与验证纪律')[0]
(HERE/'I-F复核提示词-v31.txt').write_text(prompt)
files=[HERE/'run_production_v31.py',HERE/'output_schema_codex_compatible.json',HERE/'I-F复核提示词-v31.txt',HERE/'validate_binary_output.py']
if all(p.exists() for p in files):
 (HERE/'candidate_freeze.json').write_text(json.dumps({'version':'LLM-IF-v31','frozen_before_new_agent_results':True,'model':'gpt-5.6-sol','scope':'Every one of the 4924 units is independently reread for I/F. S/E/Ec remain immutable actual v30 predictions with their own provenance.','sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},ensure_ascii=False,indent=2)+'\n')
