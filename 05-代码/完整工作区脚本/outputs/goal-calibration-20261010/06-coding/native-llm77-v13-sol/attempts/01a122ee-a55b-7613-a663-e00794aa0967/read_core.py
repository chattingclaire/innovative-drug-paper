import json,pathlib,hashlib,sys,os
A=pathlib.Path(__file__).parent
INDEX=json.loads((A/'batch-index.json').read_text())
def summarize(v,pointer):
 if isinstance(v,dict):
  return {k:summarize(x,pointer+'/'+k) for k,x in v.items()}
 if isinstance(v,list):return [summarize(x,pointer+'/'+str(i)) for i,x in enumerate(v)]
 if isinstance(v,str) and len(v)>450:return {'unread_text_leaf_pointer':pointer,'unicode_length':len(v),'utf8_bytes':len(v.encode())}
 return v
def read(sid):
 x=next(x for x in INDEX if x['source_id']==sid);pk=json.loads(pathlib.Path(x['complete_packet_file']['path']).read_bytes());b=pk['source_bundle']
 z={'source_id':sid,'packet_file_sha256':x['complete_packet_file']['sha256'],'source_bundle_sha256':pk['source_bundle_sha256'],'source_record':b['source_record'],'source_reference_index':b['source_reference_index']}
 z['document_identity_and_titles']=[{k:v for k,v in d.items() if k in ['source_resource_id','source_sha256','source_pdf_sha256','source_title_lines_verbatim_extraction_candidates','document_year_candidate_from_recorded_original_path','recorded_path_year_is_not_source_publication_or_effective_date']} for d in b['source_documents']]
 for k in ['explicit_or_primary_source_resources','source_full_text_resources','preserved_historical_neutral_source_supplements','source_provenance_addenda','source_bundle_extension']:
  if k in b:z[k+'_overview']=summarize(b[k],'/'+k)
 s=json.dumps(z,ensure_ascii=False,separators=(',',':'));p=A/'read-events'/(sid+'-core.txt');p.parent.mkdir(exist_ok=True)
 with p.open('xb') as f:f.write(s.encode())
 print('BEGIN_SOURCE_CORE',sid,len(s.encode()),hashlib.sha256(s.encode()).hexdigest());print(s);print('END_SOURCE_CORE',sid)
if __name__=='__main__':read(sys.argv[1])
