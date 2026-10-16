"""Separate supplementary AI reading review; never replace original A/C."""
from pathlib import Path
from fractions import Fraction
import json,hashlib
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[OUT/'semantic-blind-a/first_judgments.json',OUT/'semantic-blind-c/first_judgments.json'];panel=[json.loads(p.read_text()) for p in files]
 inp=OUT/'llm-v29/stability_sample_36_v2.json';raw=json.loads(inp.read_text())['rows'];expected=[r['id'] for r in raw];source={r['id']:r for r in raw}
 for p in panel:
  assert [r['id'] for r in p['rows']]==expected and not p['issue_records']
  for r in p['rows']:
   assert set(r['labels'])=={'S','E','Ec','I','F'} and all(type(v)is int and v in [0,1] for v in r['labels'].values())
 results=[];differences=[]
 for dim in ['S','E','Ec','I','F']:
  x=[r['labels'][dim] for r in panel[0]['rows']];y=[r['labels'][dim] for r in panel[1]['rows']];n=len(x)
  cells={'TP':sum(u==v==1 for u,v in zip(x,y)),'FP':sum(u==1 and v==0 for u,v in zip(x,y)),'FN':sum(u==0 and v==1 for u,v in zip(x,y)),'TN':sum(u==v==0 for u,v in zip(x,y))}
  agree=Fraction(cells['TP']+cells['TN'],n);p1=Fraction(sum(x),n);p2=Fraction(sum(y),n);chance=p1*p2+(1-p1)*(1-p2);kappa=(agree-chance)/(1-chance) if chance!=1 else None
  results.append({'dimension':dim,'n':n,'A_positive_n':sum(x),'C_positive_n':sum(y),'cross_tab':cells,'agreement':float(agree),'kappa':None if kappa is None else float(kappa)})
  for ar,cr in zip(panel[0]['rows'],panel[1]['rows']):
   if ar['labels'][dim]!=cr['labels'][dim]:differences.append({'id':ar['id'],'dimension':dim,'A':ar['labels'][dim],'C':cr['labels'][dim],'text':source[ar['id']]['text'],'A_reason':ar['dimension_reasons'][dim],'C_reason':cr['dimension_reasons'][dim],'status':'first judgments preserved; not adjudicated or substituted into original references'})
 report={'status':'complete_separate_AI_semantic_review','identity':'Two new AI agents; not humans and not the original A/C1057 references','sampling':'Same frozen 36 records used for LLM stability, 12 per actual department; labels/predictions unavailable to reviewers','not_used_for_tuning':True,'source_sha256':{str(p):sha(p) for p in files+[inp,Path(__file__)]},'n':36,'first_judgment_issue_records':0,'results':results,'differences':differences,'interpretation':'Supplementary semantic/codebook execution evidence only. The 36 records were not established as a new independent held-out human gold standard; no population validity or publication threshold claim.'}
 (OUT/'新增36条独立AI盲审核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'n':36,'differences':len(differences),'results':results},ensure_ascii=False))
if __name__=='__main__':main()
