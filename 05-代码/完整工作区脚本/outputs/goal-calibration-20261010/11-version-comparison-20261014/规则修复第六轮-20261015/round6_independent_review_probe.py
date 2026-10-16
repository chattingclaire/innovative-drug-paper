import pathlib,sys,json,copy,hashlib
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent
e={'__file__':str(P/'round6_relations_tests.py')};exec((P/'round6_relations_tests.py').read_text().split('results=[]')[0],e)
run,transform,units=e['run'],e['transform'],e['units'];out=[]
def record(name,u):
 v,l=run(u);rs=[r for r in v.traces() if r['details'].get('relation_subtype') in [e['PROTECT'],e['RISK'],'bounded_annex_protection_substantive_condition']]
 dec=e['dimensions'].judge(v)
 out.append({'name':name,'labels':l,'relations':[r['details']['relation_subtype'] for r in rs],'requests':v.material_requests,'reasons':{k:dec[k]['reason'] for k in ['S','E','I']}})
for key in ['RECODE25-01383','RECODE25-04067']:
 u=units[key];record('original_'+key,u)
 x=copy.deepcopy(u);x['source_ref']['sha256']='f'*64;record('cross_source_'+key,x)
 x=copy.deepcopy(u);x['structure']={'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 for doc in x['source_bundle']['source_full_text_resources']:
  if doc.get('kind')=='verbatim_UTF8_snapshot_text':doc['structure']={'component_id':'B'}
 record('raw_leaf_cross_component_'+key,x)
 x=copy.deepcopy(u);x['text']='表格字段写为“'+x['text']+'”';record('form_only_'+key,x)
u=units['RECODE25-01383']
x=transform(u,'并提交本办法第五条第三款规定的用于证明药品安全性、有效性和质量可控性的全部试验数据的','并提交本办法第五条第三款规定的用于证明药品安全性、有效性和质量可控性的全部试验数据的封面复印件的')
record('data_condition_only_cover_copy',x)
x=transform(u,'提出药品试验数据保护申请。','提出药品试验数据保护申请，并填写申请表。')
record('application_plus_form',x)
x=transform(u,'境外已上市境内未上市的原研药品，首次提交','医疗器械（不是境外已上市境内未上市的原研药品），首次提交')
record('conditional_object_is_device_not_drug',x)
x=transform(u,'自创新药首次境内上市许可之日起','自非创新药首次境内上市许可之日起');record('noninnovation_entitlement_se_independent',x)
x=copy.deepcopy(u);d=x['source_bundle']['explicit_or_primary_source_resources'][1];g=next(z for z in d['ordered_article_groups'] if z['article']=='第七条');g['ordered_source_resource_ids'].pop();record('condition_missing_exception',x)
u=units['RECODE25-04067'];x=copy.deepcopy(u);g=next(z for z in x['source_bundle']['explicit_or_primary_source_resources'][0]['ordered_article_groups'] if z['article']=='第四十二条');g['ordered_source_resource_ids'].pop(4);record('risk_missing_member',x)
x=transform(u,'应当对临床试验进行风险管理。','应当对临床试验进行风险管理，并登记文件名称。');# Rebase every TXT literal interval after this length-changing synthetic edit.
# transform now rebases TXT offsets; independently verify its literal spans below.
newraw=next(c['text'] for c in x['contexts'] if c['kind']=='source_textleaf')
for t in x['source_bundle']['explicit_or_primary_source_resources'][0]['source_texts']:
 a,b=t['source_locator']['unicode_code_point_interval_half_open'];assert newraw[a:b]==t['text']
record('risk_substance_plus_form',x)
(P/'round6-independent-review-probes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps([{k:v for k,v in r.items() if k not in ['requests','reasons']} for r in out],ensure_ascii=False,indent=2))
