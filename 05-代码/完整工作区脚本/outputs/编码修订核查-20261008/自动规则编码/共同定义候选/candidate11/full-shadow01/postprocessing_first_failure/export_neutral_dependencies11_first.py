"""Export source material actually consulted in the one completed shadow run.

This reads only unlabelled original inputs, machine dependency provenance, and
bound source/candidate files. No coder/helper call or annotation is consulted.
The shareable JSONL excludes dimensions, rule names, rationales and opinions.
"""
import collections
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata

ROOT=Path(__file__).resolve().parent
TEXT_KEYS={'text','scope_text','paragraph_text','antecedent_text','definition_text','cited_text','parent_text','quote','requirement_text'}
RAW_KEYS=TEXT_KEYS|{'unit_text','title','source_title','body_text'}
SKIP={'source_authentication','authentication','authentication_v34','layout_reconstruction','authenticated_source_lines','context_anchors','current_relation_anchors','current_source_authentication','title_context','scope_context','attachment_context','current_paragraph_context','component_binding'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dig(text):return hashlib.sha256(text.encode()).hexdigest()
def norm(text):return ''.join(c for c in unicodedata.normalize('NFKC',text)if not c.isspace()and not unicodedata.category(c).startswith('P'))
def flat_positions(text):
    flat=[];positions=[]
    for n,ch in enumerate(text):
        for c in unicodedata.normalize('NFKC',ch):
            if not c.isspace()and not unicodedata.category(c).startswith('P'):flat.append(c);positions.append(n)
    return ''.join(flat),positions

def raw_materials(value,pointer='/input'):
    if isinstance(value,dict):
        for key,item in value.items():
            if isinstance(item,str)and key in RAW_KEYS:yield pointer+'/'+key,item
            elif isinstance(item,(dict,list)):yield from raw_materials(item,pointer+'/'+key)
    elif isinstance(value,list):
        for n,item in enumerate(value):yield from raw_materials(item,pointer+'/'+str(n))

def presence(raw,text):
    found=[];needle=norm(text)
    for pointer,value in raw:
        start=value.find(text)
        if start>=0:found.append({'raw_pointer':pointer,'start':start,'end':start+len(text),'literal_match':True});continue
        if len(needle)<5:continue
        flat,pos=flat_positions(value);start=flat.find(needle)
        if start>=0:found.append({'raw_pointer':pointer,'start':pos[start],'end':pos[start+len(needle)-1]+1,'literal_match':False,'match_method':'NFKC_whitespace_punctuation_normalized_literal'})
    return {'availability':'already_in_original_input'if found else'additional_source_lookup','raw_matches':found}

class Exporter:
    def __init__(self,inputs):
        self.inputs=inputs;self.candidates={};self.sources={};self.doc_cache={};self.source_cache={};self.issues=[]
        for r in inputs.values():
            self.candidates.setdefault(r['candidate_sha256'],r['candidate_file'])
            for p,h in [('source','source_sha256'),('unit_source','unit_source_sha256')]:
                if r.get(p)and r.get(h):self.sources.setdefault(r[h],r[p])
    def doc(self,path,h):
        if not path:return None
        assert sha(path)==h,('candidate changed',path)
        if path not in self.doc_cache:self.doc_cache[path]=json.loads(Path(path).read_text())
        return self.doc_cache[path]
    def source(self,path,h):
        assert sha(path)==h,('source changed',path)
        if path not in self.source_cache:
            if Path(path).suffix.lower()=='.pdf':
                value=subprocess.run(['pdftotext','-layout','-enc','UTF-8',path,'-'],check=True,capture_output=True,text=True).stdout.split('\f')
                if value and not value[-1].strip():value.pop()
            else:value=[Path(path).read_text()]
            self.source_cache[path]=value
        return self.source_cache[path]
    def locate(self,raw,text):
        flat,positions=flat_positions(raw);needle=norm(text);start=flat.find(needle)
        if start<0 or not needle:return None
        a,b=positions[start],positions[start+len(needle)-1]+1
        return {'raw_extracted_text_start':a,'raw_extracted_text_end':b,'raw_extracted_exact_span':raw[a:b],'extracted_text_sha256':dig(raw),'match_method':'NFKC_whitespace_punctuation_normalized_literal'}
    def binding(self,value,record,inherited=None):
        base=dict(inherited or{})
        base['source_sha256']=value.get('cited_source_sha256')or value.get('source_sha256')or base.get('source_sha256')or record.get('unit_source_sha256')or record['source_sha256']
        base['source_path']=value.get('cited_source_path')or value.get('source_path')or value.get('locator',{}).get('source')or self.sources.get(base['source_sha256'])or base.get('source_path')or record.get('unit_source')or record['source']
        base['candidate_sha256']=value.get('cited_candidate_sha256')or value.get('candidate_sha256')or base.get('candidate_sha256')or record['candidate_sha256']
        base['candidate_path']=value.get('candidate_path')or self.candidates.get(base['candidate_sha256'])or base.get('candidate_path')
        base['paragraph_id']=value.get('cited_paragraph_id')or value.get('paragraph_id')or value.get('locator',{}).get('paragraph_id')or base.get('paragraph_id')
        base['pages']=value.get('pages')or value.get('locator',{}).get('physical_pages')or base.get('pages')or[]
        base['source_lines']=value.get('source_lines')or value.get('locator',{}).get('source_lines')or base.get('source_lines')or[]
        return base
    def fragment(self,record,raw,role,text,binding,context=None):
        if not isinstance(text,str)or not text.strip():return None
        b=dict(binding);doc=self.doc(b.get('candidate_path'),b.get('candidate_sha256'))if b.get('candidate_path')else None
        paragraph=None
        if doc:
            ps=doc.get('paragraphs',[])
            paragraph=next((p for p in ps if p.get('id')==b.get('paragraph_id')),None)
            if paragraph is None:paragraph=next((p for p in ps if norm(p.get('text',''))==norm(text)),None)
        item={'role':role,'text':text,'text_sha256':dig(text),'source':{'path':b['source_path'],'sha256':b['source_sha256']},'candidate':{'path':b.get('candidate_path'),'sha256':b.get('candidate_sha256')},'physical_pages':b.get('pages',[]),'candidate_paragraph_id':b.get('paragraph_id'),**presence(raw,text)}
        locations=[]
        if paragraph:
            item['candidate_paragraph_id']=paragraph['id'];item['physical_pages']=paragraph.get('pages',item['physical_pages']);loc=self.locate(paragraph['text'],text)
            if loc:item['candidate_paragraph_start']=loc['raw_extracted_text_start'];item['candidate_paragraph_end']=loc['raw_extracted_text_end']
            line_ids=paragraph.get('line_ids',[]);lm={l.get('id'):l for l in doc.get('lines',[])}
            source_pages=self.source(b['source_path'],b['source_sha256'])
            for lid in line_ids:
                line=lm.get(lid)
                if not line:continue
                page=line.get('page');raw_page=source_pages[page-1]if type(page)is int and 0<page<=len(source_pages)else source_pages[0]if len(source_pages)==1 else None
                if raw_page is None:continue
                found=self.locate(raw_page,line['text'])
                if found:locations.append({'candidate_line_id':lid,'physical_page':page,'line_text':line['text'],**found})
                else:self.issues.append({'record_id':record['review_id'],'paragraph_id':paragraph['id'],'line_id':lid,'source':b['source_path'],'issue':'exporter cannot independently locate bound candidate line in plain layout extraction; runtime provenance retained'})
        if not locations:
            source_pages=self.source(b['source_path'],b['source_sha256'])
            page_numbers=item['physical_pages']or list(range(1,len(source_pages)+1))
            for page in page_numbers:
                if type(page)is int and 0<page<=len(source_pages):
                    found=self.locate(source_pages[page-1],text)
                    if found:locations.append({'physical_page':page if Path(b['source_path']).suffix.lower()=='.pdf'else None,**found});break
        item['actual_source_locations']=locations
        if context:
            auth=context.get('authentication_v34')or context.get('authentication')or context.get('source_authentication')
            if auth:
                # Structural authentication only; no coding reason or dimension.
                item['runtime_source_authentication']={k:copy.deepcopy(auth[k])for k in ('method','literal_reproduced_in_current_runtime','layout_reconstructed_literal_reproduced','layout_reconstruction')if k in auth}
        return item
    def gather_generic(self,value,record,raw,fragments,inherited=None):
        if isinstance(value,list):
            for child in value:self.gather_generic(child,record,raw,fragments,inherited)
        elif isinstance(value,dict):
            b=self.binding(value,record,inherited);texts=[(k,v)for k,v in value.items()if k in TEXT_KEYS and isinstance(v,str)]
            if not texts and b.get('paragraph_id')and b.get('candidate_path'):
                doc=self.doc(b['candidate_path'],b['candidate_sha256']);p=next((p for p in doc.get('paragraphs',[])if p.get('id')==b['paragraph_id']),None)
                if p:texts=[('paragraph_text',p['text'])]
            for k,text in texts:
                f=self.fragment(record,raw,'source_context_fragment',text,b,value)
                if f:fragments.append(f)
            for k,v in value.items():
                if k not in SKIP and k not in TEXT_KEYS and isinstance(v,(dict,list)):self.gather_generic(v,record,raw,fragments,b)
    def guideline(self,dep,record,raw,fragments,components):
        if dep.get('kind')=='COMMON11_actual_current_guideline_supply':
            context=dep['current_source_authentication'];b=self.binding(context,record)
            fragments.append(self.fragment(record,raw,'current_publication_paragraph',context['text'],b,context));return
        if dep.get('kind')!='COMMON11_authenticated_guideline_rnd_object_and_current_guidance':return
        cb=dep['component_binding']
        for role,context in [('published_title_and_notice',dep['title_context']),('same_title_attachment_link',dep['attachment_context']),('self_declared_scope',dep['scope_context']),('current_paragraph',dep['current_paragraph_context']),('body_opening',cb['first_paragraph_context']),('body_last_paragraph',cb['last_paragraph_context'])]:
            fragments.append(self.fragment(record,raw,role,context['text'],self.binding(context,record),context))
        for anchor in dep.get('context_anchors',[]):
            context=dep['title_context']if anchor['paragraph_id']==dep['title_context']['paragraph_id']else dep['scope_context'];assert context['text'][anchor['start']:anchor['end']]==anchor['text']
            f=self.fragment(record,raw,'actual_title_or_scope_anchor',anchor['text'],self.binding(context,record),context);f['candidate_paragraph_start']=anchor['start'];f['candidate_paragraph_end']=anchor['end'];fragments.append(f)
        page=cb['actual_reference_boundary_page'];pages=self.source(dep['source_path'],dep['source_sha256']);rawpage=pages[page-1];line=next(s for s in rawpage.splitlines()if s.strip());assert norm(line)=='参考文献';assert dig(rawpage)==cb['actual_reference_boundary_page_sha256'];f=self.fragment(record,raw,'actual_reference_component_boundary',line,dict(source_path=dep['source_path'],source_sha256=dep['source_sha256'],candidate_path=dep['candidate_path'],candidate_sha256=dep['candidate_sha256'],pages=[page],paragraph_id=None));fragments.append(f)
        components.append({k:copy.deepcopy(cb[k])for k in ('first_paragraph','last_paragraph','paragraph_ids','candidate_interval_sha256','physical_first_body_page','current_paragraph_id')})
        components[-1].update(reference_boundary_physical_page=page,reference_boundary_extracted_page_text_sha256=cb['actual_reference_boundary_page_sha256'])

def main():
    manifest=ROOT/'full_actual4924.run.json';assert manifest.exists(),'Full single execution must finish before export'
    run=json.loads(manifest.read_text());frozen=json.loads((ROOT/'execution_freeze_full_shadow01.json').read_text());assert sha(run['output'])==run['output_sha256'];assert sha(frozen['input'])==frozen['input_sha256']
    rows=list(map(json.loads,Path(frozen['input']).read_text().splitlines()));inputs={r['id']:r['input']for r in rows};outputs=list(map(json.loads,Path(run['output']).read_text().splitlines()));assert len(outputs)==4924
    exporter=Exporter(inputs);material=[];audit=[];pending=[];kind_counts=collections.Counter();dep_records=0
    for row in outputs:
        rid=row['id'];record=inputs[rid];pred=row.get('prediction',{});raw=list(raw_materials(record));fragments=[];components=[]
        deps=[e['context_dependency']for e in pred.get('evidence',[])if isinstance(e.get('context_dependency'),dict)]
        obj=pred.get('object_scope_dependencies',[]);deps+=obj if isinstance(obj,list)else[obj]
        if isinstance(pred.get('drug_object_evidence'),(dict,list)):deps.append(pred['drug_object_evidence'])
        if deps:dep_records+=1
        for dep in deps:
            if isinstance(dep,dict):kind_counts[dep.get('kind','object_source_anchor')]+=1;exporter.guideline(dep,record,raw,fragments,components)
            exporter.gather_generic(dep,record,raw,fragments)
        unique={}
        for f in fragments:
            if f:unique.setdefault((f['source']['sha256'],f['candidate']['sha256'],f['role'],f['text'],f.get('candidate_paragraph_id'),tuple(f['physical_pages'])),f)
        fragments=list(unique.values())
        if fragments:
            extra=[f for f in fragments if f['availability']=='additional_source_lookup']
            item={'material_type':'neutral_actual_source_dependency_material','association':{'record_id':rid,'source_unit_id':record['unit_id'],'current_unit_text_sha256':dig(record['unit_text'])},'current_unit_text':record['unit_text'],'source':{'path':record['source'],'sha256':record['source_sha256']},'unit_source':{'path':record.get('unit_source')or record['source'],'sha256':record.get('unit_source_sha256')or record['source_sha256']},'candidate':{'path':record['candidate_file'],'sha256':record['candidate_sha256']},'fragments':fragments,'acting_component_ranges':components,'runtime_used_additional_source_text':bool(extra),'original_input_modified':False,'cross_method_equal_material_range_claimed':False,'shared_with_other_methods_yet':False,'statement':'Actual source material and locators only. Extracted page text hashes are not PDF page-byte hashes. Material synchronization to human/LLM is pending.'}
            material.append(item);audit.append({'record_id':rid,'fragment_count':len(fragments),'additional_source_lookup_count':len(extra),'component_count':len(components),'fragments':[{'role':f['role'],'availability':f['availability'],'raw_matches':f['raw_matches'],'source':f['source'],'candidate_paragraph_id':f.get('candidate_paragraph_id'),'physical_pages':f['physical_pages']}for f in fragments]})
        if row.get('first_execution_failure')or pred.get('judgement_status')=='undetermined':
            pending.append({'record_id':rid,'current_unit_text':record['unit_text'],'source':record['source'],'source_sha256':record['source_sha256'],'unit_source':record.get('unit_source'),'unit_source_sha256':record.get('unit_source_sha256'),'candidate_file':record['candidate_file'],'candidate_sha256':record['candidate_sha256'],'first_execution_failure':row.get('first_execution_failure'),'unresolved_reasons':[v for items in pred.get('common11_pending_dimensions',{}).values()for v in items],'statement':'No source material or judgement is invented to resolve this issue.'})
    out=ROOT/'material_supplement_all11.jsonl';assert not out.exists()
    with out.open('x')as f:
        for item in material:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    with(ROOT/'unresolved_material_dependencies11.jsonl').open('x')as f:
        for item in pending:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    diff={'scope':'all actual dependency roots in final evidence, object scopes and drug-object evidence, not restricted to prior17','input_sha256':frozen['input_sha256'],'shadow_output_sha256':run['output_sha256'],'material_sha256':sha(out),'records_with_dependency_roots':dep_records,'material_record_count':len(material),'records_with_additional_source_text':sum(i['runtime_used_additional_source_text']for i in material),'additional_source_fragment_count':sum(f['availability']=='additional_source_lookup'for i in material for f in i['fragments']),'acting_component_record_count':sum(bool(i['acting_component_ranges'])for i in material),'dependency_kind_counts_for_audit_only':dict(kind_counts),'records':audit,'material_synchronization_pending':True,'original_inputs_changed':False}
    (ROOT/'source_context_difference_all11.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2)+'\n')
    qa={'completed_at':datetime.datetime.now().astimezone().isoformat(),'script_sha256':sha(__file__),'coded_records_reexecuted':0,'manual_or_LLM_annotations_loaded':False,'dimension_or_opinion_fields_in_neutral_material':False,'full_shadow_manifest_sha256':sha(manifest),'all_protected_sha256_unchanged':all(sha(p)==h for p,h in frozen['protected_sha256'].items()),'all_runtime_sha256_unchanged':all(sha(p)==h for p,h in frozen['code_sha256'].items()),'material_sha256':sha(out),'unresolved_material_record_count':len(pending),'export_locator_issues':exporter.issues,'material_synchronization_pending':True}
    (ROOT/'neutral_export_QA11.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:diff[k]for k in ('material_record_count','records_with_additional_source_text','additional_source_fragment_count','acting_component_record_count')},ensure_ascii=False));print(json.dumps({'locator_issues':len(exporter.issues),'unresolved_material_records':len(pending),'material_sha256':sha(out)},ensure_ascii=False))
if __name__=='__main__':main()
