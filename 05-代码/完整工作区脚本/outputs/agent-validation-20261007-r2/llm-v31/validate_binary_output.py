"""Structural/literal validator only: does not attest semantic correctness."""
import json
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
def validate(packet,out):
 errors=[];inp={r['id']:r for r in packet['rows']};rows=out.get('rows',[])
 if [r.get('id') for r in rows]!=[r['id'] for r in packet['rows']]:errors.append('input_ID_order_or_closure')
 if out.get('protocol_version')!='CAL-5D-20260926-v1.3' or out.get('execution_version')!='LLM-IF-v31' or out.get('release_stage')!='final_binary_labels':errors.append('wrong_version')
 for r in rows:
  rid=r.get('id');src=inp.get(rid)
  if src is None:continue
  labs=r.get('labels',{});reason=r.get('dimension_reasons',{})
  if set(labs)!={'I','F'} or any(type(v)is not int or v not in (0,1) for v in labs.values()):errors.append(f'{rid}:bad_labels');continue
  if set(reason)!={'I','F'} or any(not isinstance(v,str) or not v.strip() for v in reason.values()):errors.append(f'{rid}:bad_reasons')
  found=set()
  for e in r.get('evidence',[]):
   d=e.get('dimension');s=e.get('source');q=e.get('quote','')
   if d not in labs or labs.get(d)!=1 or not q:errors.append(f'{rid}:bad_evidence');continue
   if s=='unit':
    if q not in src['text']:errors.append(f'{rid}:{d}:nonliteral_unit_quote')
    else:found.add(d)
   elif s=='context':
    if not any(q in t for t in strings(src.get('contexts',{}))):errors.append(f'{rid}:{d}:nonliteral_context_quote')
   else:errors.append(f'{rid}:bad_evidence_source')
  for d in ['I','F']:
   if labs[d] and d not in found:errors.append(f'{rid}:{d}:missing_unit_quote')
  for d,k,allowed in [('I','innovation_subtypes',{'attribute','research_support','qualification_advantage'}),('F','fairness_subtypes',{'access','affordability','clinical_management','dimension_information'})]:
   v=r.get(k)
   if not isinstance(v,list) or any(x not in allowed for x in v) or len(v)!=len(set(v)) or bool(v)!=bool(labs[d]):errors.append(f'{rid}:{d}:bad_subtypes')
 for i in out.get('issue_records',[]):
  if i.get('id') not in inp:errors.append('unknown_issue_ID')
  if i.get('status')=='material_issue':errors.append(f"{i.get('id')}:unresolved_material_issue")
 return errors
