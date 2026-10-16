import json,pathlib,sys,re,hashlib
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent
CODE=ROOT/'06-coding/full4481-rule-production-adapter-sol'
sys.path.insert(0,str(CODE))
import relations,dimensions
P=ROOT/'06-coding/rule-full4481-v2-root/run4481-first'
IDS={'RECODE25-'+s for s in ['00133','04197','03477','00125','00141','00132','00138','03474','04162','00038','00118']}
saved={r['id']:r for r in map(json.loads,open(P/'predictions.jsonl')) if r['id'] in IDS}
out=[]
def match(p,t):
 m=re.search(p,t);return m.group() if m else None
for item in map(json.loads,open(P/'effective-semantic-units.jsonl')):
 rid=item['id']
 if rid not in IDS:continue
 view=relations.RelationView(item['semantic_unit'])
 answer=dimensions.judge(view)
 assert {d:a['value'] for d,a in answer.items()}==saved[rid]['labels'],rid
 unit_traces=[]
 for u in dimensions._units(view):
  obj=dimensions._object(view,u);combined=u.text+'。'+u.inherited
  unit_traces.append({'kind':u.kind,'current_text':u.text,'inherited':u.inherited,'relation_subtype':u.details.get('relation_subtype'),
   'object':obj,'I_innovation':match(dimensions.INNOVATION_OBJECT,u.text+'。'+str(obj.get('object_text',''))+'。'+u.inherited),
   'I_support':match(dimensions.SUPPORT,combined),'I_action':match(dimensions.SUPPORT_ACTION,u.text+('。'+u.inherited if u.kind=='parent_predicate' else '')),
   'I_rnd_word':match(r'研发|研制|研究方案|试验方案|临床试验|上市前|申报前',u.text+str(obj.get('object_text',''))+u.inherited),
   'I_change':match(dimensions.MODIFICATION_CHANGE,u.text),
   'I_improvement':match(r'缓解|改善|减少|解决|克服|便利|便于|更易|提高[^。；;]{0,8}(?:表现|能力)|实质改良',u.text),
   'F_gap_matches':{k:match(p,combined) for k,p in dimensions.GAPS.items()},'F_opportunity':match(dimensions.OPPORTUNITY,combined),'F_current_allocation':match(dimensions.ACTUAL_ALLOCATION,u.text),
   'evidence':u.contexts})
 out.append({'id':rid,'source_text':view.text,'saved_labels':saved[rid]['labels'],'same_saved_labels':True,'decisions':answer,'units':unit_traces,'relation_traces':view.traces()})
(OUT/'少量确定性路径复现.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('records',len(out))
for r in out:
 print(r['id'],'I,F',r['saved_labels']['I'],r['saved_labels']['F'],'units',[(u['kind'],u['relation_subtype'],u['object']['established'],u['I_innovation'],u['I_support'],u['I_action'],u['I_rnd_word'],u['F_opportunity'],[k for k,v in u['F_gap_matches'].items() if v]) for u in r['units']])
