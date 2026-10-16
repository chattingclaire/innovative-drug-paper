from pathlib import Path
import ast,json,re,hashlib,sys
B=Path(__file__).resolve().parent
W=B.parents[2]
RT=B/'runtime'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
module=RT/'common_innovation_relations14.py'
tree=ast.parse(module.read_text())
fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='resolve_current_contents')
marker_node=next(n for n in ast.walk(fun) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='marker' for t in n.targets))
pattern=re.compile(ast.literal_eval(marker_node.value.args[0]))
def numbers(text):return [int(m.group('paren') or m.group('bare')) for m in pattern.finditer(text)]
controls=[
 ('explicit_parenthesized_after_chinese_full_stop','条件:(1)甲。(2)乙。(3)丙。',[1,2,3]),
 ('full_width_parenthesized_after_chinese_full_stop','条件：（1）甲。（2）乙。',[1,2]),
 ('semicolon_and_newline_preserved','条件:(1)甲;(2)乙\n(3)丙',[1,2,3]),
 ('bare_numeric_existing_boundary_preserved','条件:1甲;2乙\n3丙',[1,2,3]),
 ('bare_number_after_full_stop_not_new_member','要求:1甲。2乙',[1]),
 ('decimal_dose_not_enumeration','剂量:1.5mg;2.5mg',[]),
 ('sentence_medial_parenthesized_reference_not_new_member','条件:(1)甲。请参考(2)项补材料。',[1]),
 ('chinese_full_stop_quantity_not_enumeration','要求:1甲。2毫克即可。',[1]),
 ('explicit_non_contiguous_still_invalid','条件:(1)甲。(3)丙',[1,3]),
]
results=[]
for name,text,expected in controls:
 actual=numbers(text);results.append({'name':name,'text':text,'expected_number_sequence_for_syntax_only':expected,'actual_numbers':actual,'passed':actual==expected,'contiguous_1_to_n':len(actual)>=2 and actual==list(range(1,len(actual)+1))})
rows=[json.loads(l) for l in (W/'统计复算/来源读取与图示校正/规则输入4480.jsonl').read_text().splitlines()]
byid={r['id']:r for r in rows}
# Source-only module check: does not invoke an encoder or assign dimensions.
sys.path.insert(0,str(RT))
import common_innovation_relations14 as relations
source_checks=[]
for rid in ('RECODE25-01446','RECODE25-00103','RECODE25-01447'):
 try:
  dep=relations.resolve_current_contents(byid[rid]['input'])
  item={'id':rid,'status':'resolved' if dep else 'no_pointed_content','source_dependency':dep}
  if rid=='RECODE25-01446':item['passed']=dep is not None and len(dep['members'])==3 and dep['current_source_context']['source_sha256']==byid[rid]['input']['source_sha256']
  elif rid=='RECODE25-00103':item['passed']=dep is not None and len(dep['members'])>=2
  else:item['passed']=dep is None
 except Exception as e:item={'id':rid,'status':'failed','error_type':type(e).__name__,'error':str(e),'passed':False}
 source_checks.append(item)
report={'scope':'isolated syntax controls and authenticated source resolver only; no semantic coding','runtime_module_sha256':sha(module),'controls':results,'source_checks':source_checks,'all_checks_pass':all(x['passed'] for x in results+source_checks),'no_validation_accuracy_claim':True}
(B/'编号机制检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_checks_pass':report['all_checks_pass'],'syntax_controls':len(results),'source_checks':[{k:x.get(k) for k in ('id','status','passed','error')} for x in source_checks]},ensure_ascii=False,indent=2))
