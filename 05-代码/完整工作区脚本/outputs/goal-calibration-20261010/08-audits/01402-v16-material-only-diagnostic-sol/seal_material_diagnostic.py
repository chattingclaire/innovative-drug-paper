"""Mechanical interpretation report and seal. Does not execute any classifier."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import unicodedata

A=Path(__file__).resolve().parent

def bind(p):
    p=Path(p).resolve();b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def save(name,x):
    with (A/name).open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')

fixed=json.loads((A/'input-seal-before-execution.json').read_bytes())
theory=json.loads((A/'theoretical-judgment-before-execution.json').read_bytes())
rows=json.loads((A/'actual-material-comparison-results.json').read_bytes())
summary=json.loads((A/'actual-material-comparison-summary.json').read_bytes())
assert len(rows)==2 and summary['actual_comparative_run_N']==1
for x in fixed['packets']+fixed['code']+fixed['snapshots']+[fixed['article6'],fixed['manual'],fixed['material_preparation_seal'],fixed['ROOT_material_adoption'],fixed['theoretical_judgment']]:
    assert bind(x['path'])==x
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
norm=lambda s:''.join(unicodedata.normalize('NFKC',s).split())
new=rows[1];unit=new['semantic_unit'];bundle=unit['source_bundle']
article_ids={x['source_resource_id'] for x in json.loads(Path(fixed['article6']['path']).read_bytes())['source_texts']}
article_ids.add('SOURCE-ARTICLES-09d813b3014db413-SIXTH-FINITE')
article_events=[x for x in new['source_view_events'] if x.get('resource_id') in article_ids]
assert len(article_events)==6
current=norm(unit['text']);preceding=norm(next(c['text'] for c in unit['contexts'] if c['kind']=='preceding_paragraph'))
def resource_matches(text):
    return [dict(resource_id=x['source_resource_id'],article=x.get('article'),clause=x.get('clause_index_one_based')) for d in bundle['explicit_or_primary_source_resources'] for x in d['source_texts'] if norm(x['text'])==text]
current_matches=resource_matches(current);preceding_matches=resource_matches(preceding)
assert current_matches==[dict(resource_id='SOURCETEXT-09d813b3014db413-NP016',article='第六条',clause=4)]
assert preceding_matches==[dict(resource_id='SOURCETEXT-09d813b3014db413-NP015',article='第六条',clause=3)]
derived=[dict(context_id=c['context_id'],kind=c['kind'],structure=c['structure'],origin=unit['derived_context_origins'][c['context_id']]) for c in unit['contexts'] if unit['derived_context_origins'].get(c['context_id'],{}).get('source_bundle_pointer','').startswith('/explicit_or_primary_source_resources/1/')]
save('article6-actual-read-and-binding-diagnostic.json',dict(at_utc=now,current_original_contexts_byte_shape_unchanged=True,source_events_old_N=len(rows[0]['source_view_events']),source_events_new_N=len(new['source_view_events']),derived_context_count_old=len(rows[0]['semantic_unit']['contexts']),derived_context_count_new=len(unit['contexts']),current_unique_resource_match=current_matches,preceding_unique_resource_match=preceding_matches,article6_scan_events=article_events,new_article6_context_structures=derived,source_relation_traces=new['source_relation_traces'],material_requests=new['material_requests'],source_requests=new['source_requests'],structural_text_scan_not_relation_use=True,original_pixel_or_external_source_files_opened_during_classifier=False))
rel=A/'code-snapshot/relations.py';text=rel.read_text();tree=ast.parse(text)
wanted={'_v10_repair_gate','_bounded_IF_right_operation','object_evidence','_v10_complete_articles','_v10_qualified_right_execution'}
excerpts=[dict(name=n.name,start_line=n.lineno,end_line=n.end_lineno,source=ast.get_source_segment(text,n)) for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in wanted]
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('OBJECT','V10_REPAIR_ENTRY') for t in n.targets):
        excerpts.append(dict(name=','.join(t.id for t in n.targets if isinstance(t,ast.Name)),start_line=n.lineno,end_line=n.end_lineno,source=ast.get_source_segment(text,n)))
diagnosis=[
    dict(location='_bounded_IF_right_operation first guard, L1080',actual_unmet='Current text contains 仿制药 and lacks 创新药/改良型新药, so the builder returns before checking same-right holder and article6 roles.',role_gap='It treats the other applicant drug category as a blanket reason to refuse a potentially qualified protected-holder relation, instead of distinguishing protected holder and data-reliant other applicant.'),
    dict(location='V10_REPAIR_ENTRY L85–96 and _v10_qualified_right_execution L3126–3141',actual_unmet='This current protection-period refusal sentence does not meet the v10 nomination gate; the builder further only accepts 经审核符合药品试验数据保护条件的药品,...有关规定执行.',role_gap='The added v10 path represents a different post-qualification execution operation; it has no current holder-right refusal/consent/independent-data exception consumer.'),
    dict(location='_v10_qualified_right_execution entitlement test L3137',actual_unmet='The entitlement test literally requires 自创新药... and does not include the complete 改良型药品 article6 definition.',role_gap='This is an additional static restriction if that different builder were reached, not an actual later executed condition or a reason to borrow another article.'),
    dict(location='OBJECT L11 and object_evidence L1876–1902',actual_unmet='The current 仿制药/生物类似药 terms are not in OBJECT; the fallback object resolver accepts parent/heading/table/anaphor roles, not article6 source_resource_text scope.',role_gap='Available article6 holder/product scope is not converted into current object evidence by the existing route. Actual I reason says 候选词未建立药物、用药或药品治疗/支付对象。'),
    dict(location='article6 material structures vs consumed relations',actual_unmet='Article/clause/source binding is present and uniquely locates current clause4 and preceding clause3, but no typed I relationship or consumption trace is emitted.',role_gap='Scanned availability is proven; an actual same-holder qualification→protected data→current refusal/exception relation is still not constructed. Source requests and needed_material remain empty in both actual decisions.')
]
save('static-unmet-consumption-diagnostic.json',dict(at_utc=now,code=bind(rel),excerpts=excerpts,diagnosis=diagnosis,diagnostic_only_no_code_revision=True,no_candidate_function_reexecution=True,article6_actual_structures_available=True))
report=dict(at_utc=now,conclusion='Complete same-version article6 supports an AI I4 semantic reading, but adding this material alone did not resolve the actual combined-v2 control failure. No output label or code was changed.',theoretical_judgment_frozen_before_comparison=fixed['theoretical_judgment'],same_five_module_code=fixed['code'],actual_summary=summary,existing_expected={'I':1},old_new_expected_matched=[x['existing_expected_matched'] for x in rows],actual_full_decisions={x['case']:x['decisions'] for x in rows},article6_role_evidence=theory['supporting_roles'],manual_reasons=theory['manual_quotes'],counter_reading=theory['counter_reading'],precise_unmet_consumption=diagnosis,actual_source_binding=bind(A/'article6-actual-read-and-binding-diagnostic.json'),actual_results=bind(A/'actual-material-comparison-results.json'),scope={'human_semantic_review':'only original/new01402 current record and its necessary same-version article6/preceding context; no other records or source files opened for interpretation','machine_semantic_input':'original/new01402 entire immutable packet, including previously supplied same-source resources; scan events preserved, not automatically used','manual_read':'same frozen common manual substantive/context/I rules','new_200_or_remaining_body_read':False,'model_calls':0,'production_classifier_calls':0,'code_changes':0,'expected_changes':0,'independent_human_adjudication':False},necessary_next_step='ROOT cannot declare this material-only result repaired or replace a production label by the AI theoretical judgment. A separately authorized, isolated qualified-holder/current-right consumer change would require its own frozen tests and impact proof; this task performs neither the change nor another run.',state='comparison_complete_stop')
save('report.json',report)
md=f'''# 01402 同版第六条材料比较诊断

完整第六条更支持 **I4 的实质改良资格—保护权利关系**；但只补材料没有修复实际控制：同一 `joint-v10-if-e-combined-v2-root` 五模块下，旧、新两份01402均为 **S0/E0/Ec0/I0/F0**，完整五维 decision 相同。一次比较性实际运行、两个输入、0技术错误；无模型、无生产分类、无代码或期待修订。本诊断不是独立人工核定。

## 先于运行封存的语义判断

当前原文：“{theory['current_text']}”

同版第六条四款构成有限直接链：第1、2款界定改良型药品与首次境内上市许可起的4年数据保护；第3款把受保护范围限定为证明相较已知活性成份药品/已上市生物制品具有明显临床优势的新临床试验数据，并保留三类排除；第4款当前规定，在保护期内未经持有人同意依赖该数据的仿制/类似药申请不予许可，同时保留自行取得且未依赖他人数据的例外。

手册§二允许补足当前实际限制的同一制度安排之对象与直接机制；§六I4允许具体创新/改良资格决定实质权利义务，且权利存在本身不足。这里有已核明的改良资格/数据范围及当前许可限制，不是仅一般报送手续，也不等于 I3 研发服务。原期待 I=1 原样保留，但没有作为权威推断。运行前判断 SHA256 `{fixed['theoretical_judgment']['sha256']}`；准确逐字引文、否定和例外在理论 JSON。

反对读法在薄材料下成立：仅见持有人、同意与数据保护，不能推出技术新颖性或实质改良。新材料补的是同版当前所指的保护对象和范围，不能把其他申请人认定为创新持有人、把所有数据都视为符合资格、把独立数据例外改写成全面禁入，或因第3款出现临床优势给当前自动增 E。

## 材料身份与真实读取

旧/new current source_record 及原 contexts 完全相同，旧 explicit resource 前缀也相同；新增只有第六条资源及中性 extension 绑定。当前规范化原文在供应资源中唯一对应 `NP016/第六条第4款`，原 preceding context 唯一对应 `NP015/第3款`。新 derived contexts 有第六条四款的 `article/clause_index_one_based/source_bundle_pointer` 和第七条**标题边界**，无第七条实质正文。

真实 unit contexts 从11变16，source scan events 从23变29；新增四款、边界标题和第六条容器均有扫描事件。新增材料实际可见且被结构化扫描，但 `relations=[]`、`source_relation_traces=[]`，没有生成使用该材料的 I 证据关系。保存完整原/新 semantic_unit、五维 decisions、来源事件/请求/reads；扫描不冒称适用或消费。分类期间物理文件/目录、进程及网络 I/O被阻断，拒绝尝试0；输入和原代码前后哈希完全相同。

## 具体未成立的消费路径

| 冻结代码位置 | 当前阻断与角色缺口 |
| --- | --- |
| `relations.py:1080` `_bounded_IF_right_operation` | 遇当前“仿制药”而无当前“创新药/改良型新药”立即返回，尚未区分受保护的改良持有人与受限制的数据依赖申请人。 |
| `V10_REPAIR_ENTRY`、`_v10_qualified_right_execution:3126` | 新路径只提名并接受“经审核符合……药品试验数据保护条件……执行”的另一种操作，当前保护期间拒许可/同意/自取数据例外不匹配。 |
| `entitlements:3137` | 该路径进一步只接受“自创新药……”的完整条款，不接受改良型药品第六条；这是静态附加限制，不能说本次已走到该判断。 |
| `OBJECT:11`、`object_evidence:1876` | 当前“仿制药/生物类似药”不在对象模式中；一般 fallback 不以新增 `source_resource_text` 的第六条对象补足。实际 I0 理由为“候选词未建立药物、用药或药品治疗/支付对象。” |
| 当前 I decision 与材料请求 | 两侧 `needed_material=[]`、material/source requests 都为空。完整材料的 holder—资格—数据范围—当前许可限制/例外链没有被现有 producer/consumer 建立。 |

逐字函数片段与行位置保存在 `static-unmet-consumption-diagnostic.json`，基于实际使用的五模块 snapshot，未另行执行候选函数或修改规则。不能通过扩大一般仿制药/资料关键词、借另一条资格或直接替换标签绕过这项角色关系缺口。

## 保留结果及停止边界

原期待 I1在旧、新两侧都未满足；程序结果原样保留，不能把语义判断写成已经实际编码为1。该单例支持“补材已进入中性接口，但现 consumer 无对应通路”的结论，不能声称所有代码/其他记录均有同样问题。若 ROOT 后续决定修复，须另行冻结针对同一受保护持有人和当前实质权利的最小代码关系及控制/影响证明；本任务不改、不再跑、不扫描其他真实误判。

本轮语义范围仅01402旧/新 packet中的当前及必要同版第六条/原邻段。没有打开其他记录、human200或remaining正文，没有另开政策全文或HTML原件。机器输入完整旧/新01402 packet内已供同源资源，其原扫描台账完整保留；理论判断不借这些其他条的资格。输入与输出哈希见 input/output seal。
'''
with (A/'report.md').open('x',encoding='utf8') as f:f.write(md)
save('output-seal.json',dict(at_utc=now,state='complete_stopped_no_production_adoption',files=[bind(p) for p in sorted(A.rglob('*')) if p.is_file()],self_excluded=True,input_and_code_hash_readback_exact=True,one_actual_comparative_run_two_material_inputs=True,model_calls=0,production_classifier_calls=0,no_code_or_expected_changes=True))
print(json.dumps(dict(report=bind(A/'report.md'),output_seal=bind(A/'output-seal.json'),actual_values=summary['values'],actual_comparison_runs=1,code_changes=0,stop=True),ensure_ascii=False,indent=2))
