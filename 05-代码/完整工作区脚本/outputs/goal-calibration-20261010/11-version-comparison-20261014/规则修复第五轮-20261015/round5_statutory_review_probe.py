from pathlib import Path
import sys,json,hashlib,copy
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
e={'__file__':str(P/'round5_relations_tests.py')};exec((P/'round5_relations_tests.py').read_text().split('results=[]')[0],e)
run,transform,units=e['run'],e['transform'],e['units']
out=[]
def record(name,u):
 v,l=run(u);rs=e['rels'](v);dec=e['dimensions'].judge(v)
 out.append({'name':name,'labels':l,'relation_count':len(rs),'requests':v.material_requests,
 'relation_direction_fields':[{k:val for k,val in r['details'].items() if 'direction' in k or 'delivery' in k or k=='current_support_quotes'} for r in rs],
 'decision_reasons':{k:dec[k]['reason'] for k in ['I','F']},'decision_details':{k:dec[k]['details'] for k in ['I','F']}})
for key,u in units.items():record('original_'+key,u)
u=units['RECODE25-04589']
x=transform(u,'药品审评中心安排审评人员进行沟通交流','药品审评中心不安排审评人员进行沟通交流')
x=transform(x,'对下一步研究方案提出意见或者建议，并反馈给申请人','不对下一步研究方案提出意见或者建议，也不反馈给申请人')
record('both_technical_services_denied',x)
x=transform(u,'药物临床试验期间，用于防治严重危及生命','兽药临床试验期间，用于防治严重危及生命')
record('qualification_veterinary_object',x)
x=transform(u,'符合条件的，药品审评中心按照程序公示后纳入突破性治疗药物程序','不保证符合条件的，药品审评中心按照程序公示后纳入突破性治疗药物程序')
record('admission_not_guaranteed',x)
x=transform(u,'申请人可以申请适用突破性治疗药物程序','申请人不可以申请适用突破性治疗药物程序')
record('eligibility_application_forbidden',x)
for key,u in units.items():
 x=copy.deepcopy(u);x['source_ref']['sha256']='f'*64;record('cross_source_'+key,x)
 x=copy.deepcopy(u);x['contexts']=[c for c in x['contexts'] if c['kind']!='source_textleaf'];record('missing_fulltext_'+key,x)
 x=transform(u,u['text'],'系统栏目记载“'+u['text']+'”这一表述。');record('form_'+key,x)
(P/'round5-statutory-review-probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
