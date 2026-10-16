"""Serialize ROOT's item-by-item AI semantic review; never edits original labels."""
from pathlib import Path
import json, hashlib

OUT=Path(__file__).resolve().parent
BASE=OUT.parents[2]/'ai-audit800-20261010'
# Explicit authored judgments after reading the complete current propositions,
# required same-version contexts and cited full-source paragraphs.
NOTES={
 'A-000123':(1,False,'规则遗漏依据','当前决定维持/退出同一试点资格，非仅发布通知。CARE-P021—P030核明完整资格，P025第二分支为境内无获批目标适应症药物，P030纳入及P044研发跟踪沟通直接形成缺口—支持机会—存续关系。不能把全部罕见病等同短缺。'),
 'A-000212':(1,False,'规则遗漏依据','当前以不满足优先条件为由终止实质优先待遇并转普通审评。完整同版第68条含临床急需短缺分支，第70条给予支持，第71条撤回，是操作性标准援引及待遇限制；不推定所有资格分支均有缺口。'),
 'A-000313':(1,False,'规则遗漏依据','当前无有效治疗手段疾病的药品条件是第63条明确可申请附条件批准的成员，当前条件与共同父谓词形成按需申请机会，不只是疾病严重程度。'),
 'A-000327':(1,False,'规则遗漏依据','当前实际保持纳入后研发沟通。同版附件1适用范围含无有效防治手段分支，二（四）明确优先配置资源、优先处理，三（一）实施同一服务；符合手册优先技术服务按需关系。'),
 'A-000363':(1,False,'规则遗漏依据','当前明确不再优先安排而恢复常规时限，直接撤回同一优先沟通待遇。同版附件1无有效防治手段分支及纳入后优先配置资源为有限补全；撤回仍表达公平议题，不断言产生不公平。'),
 'A-000376':(1,False,'规则遗漏依据','当前不是只列会议形式，而是给已纳入品种I类会议申请机会。同版附件1无有效防治手段分支及纳入后优先配置沟通资源，与附件2上市申请前的该项机会直接连接；不由I这个字母猜测优先。'),
 'A-000399':(1,False,'规则遗漏依据','当前实质不因治疗领域限制医保申报，并明确针对各领域用药需要开放机会；同一段确指其为维护医保公平的安排。依据不同治疗需要与适当保障机会，而非仅继承公平栏目或相邻儿童药例子的全部标签。'),
 'A-000432':(None,True,'手册边界待核','同段2024年对品种低于省均的基层机构按需增加药品，确有公平关系；但当前2027年句是体系全面建立与可及性预期。需统一：它是否是同一安排的实质实施承诺，可有限补全前文机制，还是概括目标不得继承。不能只因可及性或基层判1，也不能仅因未来时态判0。'),
 'A-000738':(None,True,'手册边界待核','第63条含无有效治疗手段疾病药品的附条件批准机会，第64条当前要求沟通确认附条件批准条件后申请。需统一：这是否构成对第63条实质资格的操作性核验，足以承载缺口—申请机会，还是只规定一般申报沟通步骤。所需材料已齐，争议是关系门槛。'),
 'A-000305':(1,False,'共同阳性有据','当前给临床急需境外已上市境内未上市罕见病药70日，与普通130日直接比较；存在明确按需机会差异。境内该药未上市不等于境内无任何有效药，理由不能扩张为全部治疗选项缺失。'),
 'A-000367':(1,False,'共同阳性有据','当前第63条总领实质授予附条件批准申请机会，完整成员之一明确无有效治疗手段；不是纯结构引导。'),
 'A-000405':(1,False,'共同阳性有据','当前并列或分支之一明确境内无药获批目标罕见病适应症；同版CARE申请资格、P030纳入和P044研发支持使之成为按需机会条件，不因其他新靶点/优势分支自动都具有缺口。'),
 'A-000476':(1,False,'共同阳性有据','当前为临床急需境外已上市境内未上市罕见病药设70日审评，同条130日支持为比较基准，构成按需优先审评机会。不能推断已改善患者获得治疗。'),
 'A-000609':(1,False,'共同阳性有据','当前与共同父句明确构成优先程序申请条件，完整成员含急需短缺、无有效儿童治疗选项及市场短缺儿童药分支；实质资格总领不是只排版引导。'),
 'A-000658':(1,False,'共同阳性有据','当前对急需短缺药首家优先纳入后，同成分同途径新申报不再接受优先申请，直接限制按缺口配置的机会；限制性表达仍属议题。'),
 'A-000685':(1,False,'共同阳性有据','当前明确要求药品公平性实质信息并保持材料摘要一致，符合概括公平信息路径，不是字段非空/格式，不虚构具体障碍。'),
 'A-000718':(1,False,'共同阳性有据','当前要求同时满足完整条件方可适用优先程序，成员含急需短缺、无有效儿童治疗选项与明确市场短缺儿童药优先安排，直接构成资格—按需机会总领。')
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ai={r['blind_id']:r for r in map(json.loads,(BASE/'AI原始判读-800条.jsonl').read_text().splitlines())}
rule_path=OUT.parents[1]/'06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
rules={r['id']:r for r in map(json.loads,rule_path.read_text().splitlines())}
rows=[]
for bid,(value,human,assessment,reason) in NOTES.items():
 p=BASE/'source-A/coder-A/materials'/f'{bid}.json'; packet=json.loads(p.read_text()); sr=packet['source_record']
 contexts=[]; seen=set()
 for c in sr['contexts']:
  t=c.get('text')
  if t and t not in seen:
   contexts.append({'context_id':c.get('context_id'),'text':t,'source_ref':c.get('source_ref')});seen.add(t)
 rows.append({'blind_id':bid,'source_id':sr['id'],'dimension':'F','AI':ai[bid]['judgments']['F']['value'],
              'rule':rules[sr['id']]['labels']['F'],'review_value':value,'assessment':assessment,
              'needs_human_review':human,'reason':reason,'current_text':sr['text'],
              'current_source_ref':sr['source_ref'],'packet_sha256':sha(p),
              'available_contexts_for_trace_not_all_used':contexts,
              'manual_basis':'§二有限确指与操作性标准援引；§七具体公平关系、上游F、优先技术服务；宗旨与实质内容门槛',
              'review_identity':'ROOT AI semantic audit; not human adjudication; no original value modified'})
out={'identity':'ROOT AI semantic review of 9 F disagreements and 8 common-positive records',
     'manual_sha256':sha(BASE/'source-A/coder-A/manual.txt'),'reviewed_records':len(rows),
     'no_accuracy_or_human_validity_claim':True,'rows':rows}
with (OUT/'fairness-root-review.json').open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'reviewed':len(rows),'disagreements_supported_AI1':7,'unresolved_boundary':2,'common_positive_reviewed':8}))
