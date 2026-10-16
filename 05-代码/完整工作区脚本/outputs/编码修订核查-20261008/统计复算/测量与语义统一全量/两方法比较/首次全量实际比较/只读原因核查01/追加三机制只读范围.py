from pathlib import Path
import hashlib,json,re,subprocess,unicodedata
B=Path(__file__).resolve().parent;W=B.parents[4]
P=W/'统计复算/来源读取与图示校正/规则输入4480.jsonl';FIRST=B.parent/'I_二元分歧.jsonl';BASE=W/'自动规则编码/测量与语义统一/runtime'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[json.loads(l) for l in P.read_text().splitlines()];byid={r['id']:r for r in rows}
patterns={
 'I_explicit_attribute_evaluation_envelope':(re.compile(r'创新(?:性|价值|程度|属性)|原创性|新颖性'),re.compile(r'量化|分级|评分|评价|评估|比较|分析|研判|核验|验证|确定')),
 'I_actual_rnd_review_arrangement_envelope':(re.compile(r'创新药|改良型(?:新药|药品)'),re.compile(r'临床(?:试验|研究)|研发|开发'),re.compile(r'组织开展|开展|设置|安排|实施|加速|加快|缩短'),re.compile(r'审评|审批')),
 'F_existing_basic_clinical_supply_family_exposure':(re.compile(r'(?:保障|确保|保证)临床(?:基本|必需|急需)(?:的)?(?:用药|药品|药物)(?:的)?(?:供应|配备|获取)'),)
}
scopes={}
for name,pats in patterns.items():
 picked=[r for r in rows if all(p.search(r['input']['unit_text']) for p in pats)]
 scopes[name]={'n':len(picked),'ids':[r['id'] for r in picked],'scope_algorithm':[p.pattern for p in pats],'scope_use':'current-source-text lexical exposure envelope only; not predictions, semantic categories or an instruction to recode','rows':[{'id':r['id'],'unit_text':r['input']['unit_text'],'unit_source':r['input'].get('unit_source'),'unit_source_sha256':r['input'].get('unit_source_sha256'),'candidate_file':r['input']['candidate_file'],'unit_id':r['input']['unit_id']} for r in picked]}
actual=[]
for line in FIRST.open():
 r=json.loads(line)
 if r['id'] not in {'RECODE25-03710','RECODE25-02206'}:continue
 input_now=byid[r['id']]['input'];oldinput=r['rule_source_input_complete']['input'];assert input_now['unit_text']==oldinput['unit_text']
 pos=r['source_position'];source=Path(pos['unit_source_file']);candidate=Path(pos['candidate_file']);raw=subprocess.run(['textutil','-convert','txt','-stdout',str(source)],check=True,capture_output=True,text=True).stdout if source.suffix=='.doc' else subprocess.run(['pdftotext','-layout','-enc','UTF-8',str(source),'-'],check=True,capture_output=True,text=True).stdout
 def norm(x):return re.sub(r'\s+','',unicodedata.normalize('NFKC',x)).translate(str.maketrans({'，':',','。':'.','；':';','：':':'}))
 assert norm(r['text']) in norm(raw)
 rr=r['rule_output_complete']['result']
 actual.append({'id':r['id'],'text':r['text'],'direction':{'rule':r['rule_label'],'llm':r['llm_label']},'source_position':pos,'actual_source_sha256':sha(source),'candidate_sha256':sha(candidate),'current_text_read_in_actual_source':True,'source_and_candidate_match_recorded':sha(source)==pos['unit_source_sha256_recorded'] and sha(candidate)==pos['candidate_sha256_recorded'],'rule_current_role':rr['current_unit_role'],'rule_i_suppressions':[s for s in rr['suppressions'] if 'I' in s.get('dimensions',[])],'prior_i_evidence':[e for e in rr.get('common_definition_prior_evidence',[]) if e['dimension']=='I'],'final_i_evidence':[e for e in rr['evidence'] if e['dimension']=='I'],'family_migration_trace':rr.get('family_migration_trace'),'llm_i_reason':r['llm_output_complete']['dimension_reasons']['I'],'llm_i_evidence':[e for e in r['llm_output_complete']['evidence'] if e['dimension']=='I']})
files=['policy_coding_v27.py','rules_if.py','common_definition_stage.py','common_if_relations.py','common_if_current_relations05.py','common_coverage_relations11.py','current_innovation_support.py','common_innovation_relations14.py','common_medicine_access14.py','common_scope09.py']
result={'purpose':'read-only concrete code mechanism follow-up requested by root; no coder invoked','input_sha256':sha(P),'input_n':4480,'first_I_comparison_sha256':sha(FIRST),'manual_sha256':sha(W/'定义溯源核查/测量与计数统一/共用编码手册.md'),'code_baseline':str(BASE),'read_code_sha256':{f:sha(BASE/f) for f in files},'actual_two_i_cases':actual,'source_only_exposure':scopes,'limits':['Exposure cooccurrence is intentionally conservative and is not a semantic positive count.','No current or old labels select exposure; source strings only.','No changes to frozen runtime/bundle/input/output and no encoding run.']}
(B/'三机制追查与来源范围.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'scopes':{k:{'n':v['n'],'ids':v['ids']} for k,v in scopes.items()},'actual_cases':[{'id':a['id'],'matched':a['source_and_candidate_match_recorded']} for a in actual]},ensure_ascii=False,indent=2))
