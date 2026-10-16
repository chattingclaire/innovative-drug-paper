"""Bounded actual certificate checks; no labels are generated."""
import copy,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RT=BASE/'runtime';sys.path.insert(0,str(RT))
import common_innovation_relations14 as innovation
import cross_carrier_source_reader as cross
import visual_source_reader as visual
records={x['id'][-5:]:x['input'] for x in map(json.loads,Path(__file__).with_name('规则待核输入21.jsonl').read_text().splitlines())}
results=[]
def check(name,function,reject=False):
    try:
        value=function();results.append(dict(name=name,passed=not reject,actual_type=type(value).__name__))
    except Exception as error:
        results.append(dict(name=name,passed=reject,error_type=type(error).__name__,reason=getattr(error,'reason',str(error)),details=getattr(error,'details',{})))
def auth(suffix):
    z=records[suffix];doc,paras,index=innovation._document(z);return innovation._authenticate_paragraph(z,paras[index],doc)
for suffix in ['00588','01459','01472','03875','02371']:
    check('actual_added_certificate_'+suffix,lambda suffix=suffix:auth(suffix))
check('actual_complete_cross_carrier_article_and_all_members',lambda:innovation.resolve_current_contents(records['03273']))
z=records['01459'];doc,paras,index=innovation._document(z);p=next(p for p in paras if p['pages']==[5,6]);entries=json.loads((RT/'visual_transcriptions.json').read_text())['entries'];e=next(e for e in entries if e.get('physical_pages')==[5,6] and e['paragraph_text_sha256']==hashlib.sha256(p['text'].encode()).hexdigest())
check('actual_visual_all_pages_reproduced',lambda:visual.verify_visual_entry(z,p,e))
bad=copy.deepcopy(e);bad['rendered_pages'].pop()
check('visual_missing_second_page_rejected',lambda:visual.verify_visual_entry(z,p,bad),True)
bad=copy.deepcopy(e);bad['rendered_pages'][1]['sha256']='0'*64
check('visual_second_page_wrong_bytes_sha_rejected',lambda:visual.verify_visual_entry(z,p,bad),True)
z=records['02371'];doc,paras,index=innovation._document(z);p=paras[index];e=next(e for e in json.loads((RT/'cross_carrier_certificates.json').read_text())['certificates'] if e['pdf_source']['sha256']==z['unit_source_sha256'])
bad=copy.deepcopy(e);bad['page_bounded_region']['end_boundary_exclusive']='不存在的段落边界'
check('cross_carrier_missing_actual_end_boundary_rejected',lambda:cross.verify_cross_carrier_entry(z,p,doc,bad),True)
bad=copy.deepcopy(e);bad['page_bounded_region']['cross_carrier_normalized_paragraph_sha256']='0'*64
check('cross_carrier_full_actual_region_sha_difference_rejected',lambda:cross.verify_cross_carrier_entry(z,p,doc,bad),True)
z=records['03273'];doc,paras,index=innovation._document(z);e=next(e for e in json.loads((RT/'cross_carrier_certificates.json').read_text())['certificates'] if e['pdf_source']['sha256']==z['unit_source_sha256']);bad_doc=copy.deepcopy(doc);bad_doc['paragraphs'].pop(index+1);p=bad_doc['paragraphs'][index]
check('cross_carrier_omitted_member_rejected_even_with_whole_TXT_source_available',lambda:cross.verify_cross_carrier_entry(z,p,bad_doc,e),True)
out=dict(kind='actual_page_certificate_controls_not_validity',n_checks=len(results),all_checks_pass=all(x['passed'] for x in results),checks=results,runtime_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in RT.iterdir() if p.is_file()})
Path(__file__).with_name('added_source_certificate_checks01.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['kind','n_checks','all_checks_pass']},ensure_ascii=False))
for x in results:
    if not x['passed']:print(json.dumps(x,ensure_ascii=False))
