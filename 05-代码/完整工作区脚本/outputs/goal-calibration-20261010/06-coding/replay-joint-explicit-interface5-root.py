"""Preserve explicit post-construction relation operations in five API controls."""
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'06-coding/rule-five-dimension-joint-root/versions/merge-baseline01'
SE=ROOT/'06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'
OUT=V/'explicit-interface5-root-replay02'
def load(p):return json.loads(Path(p).read_text())
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(b):assert bind(b['path'])=={k:b[k]for k in ('path','bytes','sha256')},b['path']
def save(p,v):
    with p.open('x',encoding='utf8')as h:json.dump(v,h,ensure_ascii=False,indent=2);h.write('\n')
assert not OUT.exists()
for item in load(V/'pre-execution-seal.json')['output_members']:exact(item)
for item in load(SE/'delivery-seal.json')['files']:exact(item)
modules={}
for name in ('evidence','source_packet','source_receipts','relations','dimensions'):
    spec=importlib.util.spec_from_file_location(name,V/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);modules[name]=mod
helper=SE/'interface_controls.py';tree=ast.parse(helper.read_text())
table=next(ast.literal_eval(node.iter)for node in tree.body if isinstance(node,ast.For) and isinstance(node.iter,ast.List))
assert len(table)==5
parent=load(SE/'interface-final-scope.json')['tests'];controls=[]
for (name,dims,ifonly,kind,expected),case in zip(table,parent[:5]):
    assert case['name']==name and case['expected_fixed_before_execution']==expected
    details=dict(relation_subtype='SE_test_consumer_permission',shared_predicate='本药安全性证据应核验，治疗费用应测算。',affected_dimensions=dims,only_IF_consumers=ifonly)
    if kind=='price_arrangement':details.update(relation_subtype='same_edition_price_node_content_definition',version_binding={'established':True},direct_mapping=True)
    controls.append(dict(name=name,semantic_input=case['synthetic_input'],kind=kind,details=details,expected=expected,synthetic_test_API_operation_not_source_claim=True))
OUT.mkdir()
save(OUT/'controls-fixed-before-execution.json',dict(cases=controls,original_helper=bind(helper),parent=bind(SE/'interface-final-scope.json'),reason='The parent helper explicitly adds a synthetic relation after RelationView construction; first235 loader omitted that operation. No classifier error was demonstrated by the omitted operation. Original input/expected preserved; these5 are executed with complete test protocol.'))
save(OUT/'pre-execution-seal.json',dict(controls=bind(OUT/'controls-fixed-before-execution.json'),code=[bind(V/(n+'.py'))for n in modules],runner=bind(__file__),first_attempt_preserved=bind(V/'joint-parent235-root-replay01/output-seal.json')))
results=[]
for case in controls:
    unit=copy.deepcopy(case['semantic_input']);view=modules['relations'].RelationView(unit)
    view._add(case['kind'],[view._quote(view.by_id['CTX-REL'],'显式受限关系测试')],'测试仅指定消费者',**case['details'])
    decisions=modules['dimensions'].judge(view);modules['evidence'].validate_decisions(unit,decisions)
    observed={dim:decisions[dim]['value']for dim in case['expected']}
    results.append(dict(name=case['name'],expected=case['expected'],observed=observed,passed=observed==case['expected'],decisions=decisions,relations=view.traces(),evidence_validation_passed=True))
save(OUT/'results.json',results)
save(OUT/'summary.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),case_N=5,matched=sum(x['passed']for x in results),failed_names=[x['name']for x in results if not x['passed']],original_protocol_relation_injection_restored=True,classifier_or_source_or_expected_edits=False,remaining230_inputs_not_rerun=True,formal_acceptance=False))
save(OUT/'output-seal.json',dict(output_members=[bind(p)for p in sorted(OUT.iterdir())if p.is_file()],self_excluded=True))
print(json.dumps(load(OUT/'summary.json'),ensure_ascii=False))
