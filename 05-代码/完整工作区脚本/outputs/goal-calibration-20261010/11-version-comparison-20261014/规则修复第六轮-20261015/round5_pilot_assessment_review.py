"""Independent additional relation binding probes; no production input/code edits."""
from pathlib import Path
import copy,hashlib,json,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
e={'__file__':str(P/'round5_pilot_assessment_tests.py')}
exec((P/'round5_pilot_assessment_tests.py').read_text().split('results=[]')[0],e)
units=e['units'];variant=e['variant'];PILOT=e['PILOT'];ASSESS=e['ASSESS'];NEST=e['NEST'];out=[]
before={n:hashlib.sha256((P/'code'/n).read_bytes()).hexdigest() for n in ['relations.py','dimensions.py']}
def reflow(u):
 u=copy.deepcopy(u);offset=0
 for c in sorted([c for c in u['contexts'] if c['kind']=='source_textleaf'],key=lambda c:c['source_ref']['locator']['unicode_code_point_interval_half_open'][0]):
  end=offset+len(c['text']);c['source_ref']['locator']['unicode_code_point_interval_half_open']=[offset,end]
  pointer=u['derived_context_origins'][c['context_id']]['source_bundle_pointer']
  doc=u['source_bundle']['source_full_text_resources'][int(pointer.split('/')[2])]
  for field in ['locator','source_locator']:
   if field in doc:doc[field]['unicode_code_point_interval_half_open']=[offset,end]
  offset=end
 return u

def record(name,u,sub,want):
 u=reflow(u)
 v,l=e['run'](u);found=sub in e['types'](v)
 out.append({'name':name,'relation':sub,'expected':want,'actual':found,'passed':found==want,'labels':l,'requests':v.material_requests,'traces':v.traces()})
for key in ['RECODE25-01735','RECODE25-01745']:
 u=units[key]
 # The canonical source identity cannot be overridden by a matching fallback snapshot.
 x=copy.deepcopy(u);doc=x['source_bundle']['explicit_or_primary_source_resources'][0]
 doc['source_sha256']='f'*64
 record('canonical_source_mismatch_despite_snapshot_'+key,x,PILOT,False)
 # Identical repeated resource metadata may be deduplicated without losing scope.
 x=copy.deepcopy(u);docs=x['source_bundle']['explicit_or_primary_source_resources'];docs.append(copy.deepcopy(docs[0]))
 record('duplicate_identical_full_resource_'+key,x,PILOT,True)
 # Full work-plan object without the qualification subsection boundary cannot be declared complete.
 record('qualification_scope_boundary_removed_'+key,variant(u,'（二）试点项目\n','试点项目\n'),PILOT,False)
u=units['RECODE25-01745']
record('confirmation_other_object',variant(u,'向同意推荐的试点项目申请人发送项目确认书','向另一个项目申请人发送普通登记回执'),PILOT,False)
u=units['RECODE25-00111']
record('whole_current_as_form_field',variant(u,u['text'],'会议纪要字段名称：“'+u['text']+'”'),ASSESS,False)
# Preserve complete source and five branches but change only the explicitly cited edition.
record('cited_edition_differs',variant(u,'参照《突破性治疗药物审评工作程序（试行）》关于临床优势的适用条件','参照《突破性治疗药物审评工作程序（新版）》关于临床优势的适用条件'),NEST,False)
# Current assessment must still concern the same pre-submission stage.
record('assessment_after_submission',variant(u,'申请人在提出药品上市许可申请前','申请人在提出药品上市许可申请后'),ASSESS,False)
# A later express qualification of this very activity is not an unrelated clerk's duty.
record('assessment_explicitly_form_only',variant(u,'应当在会议纪要中予以明确','应当在会议纪要中予以明确；上述沟通不讨论研究数据和纳入资格，前述内容仅为表格栏目名称'),ASSESS,False)
# A separate clerical act does not remove substantive assessment; its own later
# explicit exclusion of assessment must nevertheless remain effective.
record('secretary_then_actual_assessment_denied',variant(u,'应当在会议纪要中予以明确','应当在会议纪要中予以明确，秘书仅记录会议开始时间；上述沟通不进行审核'),ASSESS,False)
after={n:hashlib.sha256((P/'code'/n).read_bytes()).hexdigest() for n in before};assert before==after
report={'scope':'independent finite pilot/assessment relation probes; no production edits','code_sha256':before,'passed':sum(x['passed'] for x in out),'total':len(out),'tests':out}
(P/'round5-pilot-assessment-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passed'],'total':len(out),'results':[{k:r[k] for k in ['name','expected','actual','passed','labels']} for r in out]},ensure_ascii=False,indent=2))
