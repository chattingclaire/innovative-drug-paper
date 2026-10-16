"""Versioned source-only repair; never reads coder labels or overwrites v1."""
from pathlib import Path
import copy,hashlib,json,re,unicodedata
from collections import Counter
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def shafile(p):return sha(Path(p).read_bytes())
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace())
def ser(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write_new(p,data):
 p=Path(p); b=data.encode('utf-8')
 if p.exists(): assert p.read_bytes()==b, 'Version exists with different bytes: '+str(p)
 else:p.write_bytes(b)
def dump_new(p,o):write_new(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def refs(v):
 if isinstance(v,dict):
  for a in v.values():yield from refs(a)
 elif isinstance(v,list):
  for a in v:yield from refs(a)
 elif isinstance(v,str) and v.startswith('CTX-'):yield v
oldpath=OUT/'canonical_source_context.jsonl'; oldhash=shafile(oldpath)
assert oldhash=='ff9901d0ea25cbc8aba8f875efb35701a9f36ac30cae73eb5d897b7df6f76a6c'
olda= json.loads((OUT/'projection-audit.json').read_text()); data=[json.loads(x) for x in oldpath.read_text().splitlines()]; byid={r['id']:r for r in data}
pa={(x['record_id'],x['context_id']):x for x in olda['context_provenance']}
# Physical page numbers are PDF file positions. Printed page numbers are separately recorded.
groups={
 '7f5b1829d0030b34':{'physical':[11,12],'printed':[10,11],'version':'2025国家医保药品目录调整申报常用问答','anchor':'二、政策问答（一）政策问题1，答复第三项','reason':'A paragraph crosses physical pages 11–12; a printed footer 10 interrupts the extracted sentence. No substantive text difference.'},
 'dec73b87b4d8fafa':{'physical':[2,3],'printed':[2,3],'version':'2024谈判药品续约规则','anchor':'规则二 简易续约，一、条件，第3项（1）','reason':'The preceding paragraph crosses physical pages 2–3; printed footer 2 interrupts the extracted sentence. No substantive text difference.'},
 'c3c24a85ab94498d':{'physical':[5,6],'printed':[5,6],'version':'2023谈判药品续约规则','anchor':'规则二 简易续约，四、其他，第1项','reason':'The paragraph crosses physical pages 5–6; printed footer 5 interrupts the extracted sentence. One source_paragraph is a subspan ending before the separately present failure sentence; the complete paragraph remains retained.'},
 'd41a0958157bc7d5':{'physical':[2,3],'printed':[2,3],'version':'2024国家医保药品目录调整工作方案','anchor':'二、调整范围（二）目录内西药和中成药，第2项（3）','reason':'The paragraph crosses physical pages 2–3; printed footer 2 interrupts the extracted sentence. No substantive text difference.'},
 'ec242f41dc57add1':{'physical':[8],'printed':[8],'version':'2022谈判药品续约规则附件6','anchor':'参考简图：2022年谈判药品续约规则及图下注释','reason':'The PDF graph is raster content, so extraction only gives the title/footer/note. The full branch transcription was compared against the visual tree, including year branches, A/B inequalities, unchanged-payment branches and the market-change note. Indentation and arrows are a transcription, not a verbatim contiguous PDF text span.'},
 '64ac48e587537802':{'physical':[11],'printed':[8],'version':'2026国家医保药品目录调整申报常用问答','anchor':'图3：商保创新药目录申报全流程示意图','reason':'The PDF diagram is raster content. The original rare-disease application branch is numbered 条件7, whereas the existing transcription said 条件2. The new version repairs that numeral in both unit text and its context; original stage/decision branches remain, and the complete source image is attached.'},
 '6976f68047990215':{'physical':[1,2],'printed':[1,2],'version':'药审中心加快创新药上市许可申请审评工作规范（试行），2023版华善镜像','anchor':'一、适用范围及审评时限（一）适用范围，第1项','reason':'The paragraph crosses physical pages 1–2; printed footer —1— interrupts the extracted final sentence. No substantive text difference. This is the archived mirror binary, not a newly authenticated official download.'},
 'b5f4e415ff277022':{'physical':[7],'printed':[5],'version':'国家卫生健康委员会公报2024年第11期','anchor':'三、完善基层药品集中供应配送机制，右栏整段','reason':'Layout extraction interleaves left and right columns. The complete retained paragraph and heading were checked visually in the right column. No substantive text difference.'},
}
reviews=[]; attachments={}
for z in olda['unresolved']:
 rid,cid=z['record_id'],z['context_id']; node=next(n for n in byid[rid]['contexts'] if n['context_id']==cid); original=copy.deepcopy(node); pre=z['source_sha256'][:16]; g=groups[pre]; source=Path(pa[(rid,cid)]['source_snapshot']);assert shafile(source)==z['source_sha256']
 extracted=(OUT/'literal-review-v2'/f'{pre}-extracted.txt').read_text()
 cleaned=re.sub(r'(?m)^\s*(?:[—－-]\s*)?\d+(?:\s*[—－-])?\s*$','',extracted)
 footer_match=norm(node['text']) in norm(cleaned)
 status='source_page_visual_checked_no_substantive_difference'
 changes=[]
 if rid=='RECODE25-03876' and cid=='CTX-52a3cb2de66c6d918a1f':
  before='条件2，2026年6月10日前';after='条件7，2026年6月10日前'
  assert node['text'].count(before)==1 and byid[rid]['text'].count(before)==1
  for obj,pointer in [(node,'/contexts/'+cid+'/text'),(byid[rid],'/text')]:
   old=obj['text'];obj['text']=old.replace(before,after)
   changes.append({'pointer':pointer,'operation':'source_verified_single_numeral_repair','before':before,'after':after,'old_text_sha256':sha(old.encode()),'new_text_sha256':sha(obj['text'].encode())})
  status='source_page_visual_checked_numeral_repaired_in_v2'
 pageproof=[]
 for page,printed in zip(g['physical'],g['printed']):
  image=OUT/'literal-review-v2/pages'/f'{pre}-p{page:02d}.png';assert image.is_file()
  at={'attachment_id':'SOURCEPAGE-'+shafile(image)[:20], 'sha256':shafile(image),'relative_path':str(image.relative_to(OUT)),'source_pdf_sha256':z['source_sha256'],'physical_page':page}
  pageproof.append({**at,'printed_page':printed,'reviewed_visual_pixels':True})
  attachments[(rid,at['attachment_id'])]=at
 reviews.append({'record_id':rid,'context_id':cid,'field':'text','original_node':original,'original_text_sha256':sha(original['text'].encode()),'new_text_sha256':sha(node['text'].encode()),'source_snapshot':str(source),'source_sha256':z['source_sha256'],'binary_sha_verified':True,'source_version':g['version'],'physical_pages':g['physical'],'printed_pages':g['printed'],'source_anchor':g['anchor'],'original_candidate_locator_matches':z.get('candidate_locator_matches',[]),'page_footers_removed_and_NFKC_whitespace_match':footer_match,'visual_review_status':status,'difference_cause':g['reason'],'source_readability':'complete paragraph/diagram and its immediate heading/branches are legible on the attached original source pages','policy_dimension_adjudication_performed':False,'source_page_evidence':pageproof,'changes':changes})
assert len(reviews)==13
for row in data:
 new=[v for (rid,_),v in attachments.items() if rid==row['id']]
 if new:row['source_page_attachments']=row.get('source_page_attachments',[])+new
 cs={n['context_id'] for n in row['contexts']};assert len(cs)==len(row['contexts'])
 assert all(r in cs for n in row['contexts'] for r in refs(n['structure']))
newpath=OUT/'canonical_source_context-v2.jsonl';write_new(newpath,''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in data))
changes=[{'record_id':r['record_id'],'context_id':r['context_id'],**x} for r in reviews for x in r['changes']]
log={'version':'v2','old_canonical':{'path':str(oldpath),'sha256':oldhash,'unchanged_after_revision':shafile(oldpath)==oldhash},'new_canonical':{'path':str(newpath),'sha256':shafile(newpath)},'policy_text_changes':changes,'source_attachment_additions':[{'record_id':rid,**a} for (rid,_),a in attachments.items()],'original_context_IDs_structures_and_all_nodes_retained':True,'supplements_merged_into_canonical':False,'initial_pilot_inputs_modified':False,'labels_read':False,'note':'Source verified repair before a new common development packet. It is not a change to the initial pilot01 input or sealed first submissions.'}
dump_new(OUT/'source-context-changes-v2.json',log)
dump_new(OUT/'literal-review-v2.json',{'source_review_agent_kind':'AI source authenticity review; not human coding','review_N':13,'groups':groups,'reviewed_context_occurrences':reviews,'unresolved_after_review':[],'limitations':['Local source snapshot SHA is verified. The archived CDE mirror is not an official-origin web binary authentication.','Flowchart arrows/indentation are source transcriptions, not a verbatim PDF text extraction. The full visual source page is required alongside them.','No dimension interpretation, reliability/performance calculation, or independent human validation is performed.']})
a=copy.deepcopy(olda);a.update({'status':'v2_source_projection_source_specific_review_complete_with_one_numbering_repair','output':log['new_canonical'],'v1_preserved':log['old_canonical'],'version_change_log':{'path':str(OUT/'source-context-changes-v2.json'),'sha256':shafile(OUT/'source-context-changes-v2.json')},'additional_source_literal_review':{'path':str(OUT/'literal-review-v2.json'),'sha256':shafile(OUT/'literal-review-v2.json')},'all_original_policy_text_fields_byte_equivalent':False,'source_verified_policy_text_exceptions':changes,'unresolved':[]})
a['counts']['source_specific_visual_review_new_occurrences']=13;a['counts']['source_verified_text_corrections']=1;a['counts']['unresolved_literal_or_source_issues']=0
for pr in a['context_provenance']:
 m=next((r for r in reviews if r['record_id']==pr['record_id'] and r['context_id']==pr['context_id']),None)
 if m:
  pr['source_specific_review_v2']={'status':m['visual_review_status'],'source_anchor':m['source_anchor'],'physical_pages':m['physical_pages'],'printed_pages':m['printed_pages'],'difference_cause':m['difference_cause']}
  pr['text_fields'][0]['v2_text_sha256']=m['new_text_sha256']
for r in data:a['record_content_bindings'][r['id']]['v2_canonical_source_content_sha256']=sha(ser(r).encode())
a['limits']=['Source authenticity/structure review is AI work, not human independent coding.','Original 41 source nodes retained; repaired diagram number and new page evidence exist only in v2.','Source-specific visual review cannot prove that every retained context is required under a final frozen manual.','Pure source supplements remain a separate next-version file and are not inserted into pilot01.']
dump_new(OUT/'projection-audit-v2.json',a)
# Six supplementary source excerpts: delete all rules, use true document locators and distinct dates.
sup_path=ROOT/'02-methods/source-supplements/prospective-common-supplements.jsonl';supp=[json.loads(x) for x in sup_path.read_text().splitlines()];assert len(supp)==6
frame={r['id']:r for r in (json.loads(x) for x in (ROOT/'00-baseline/source-only-frame.jsonl').read_text().splitlines())}
manifest=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());bysha={x['sha256']:x for x in manifest['files']}
spans={'SUP-NHC2024-EXP004':(10871,11219,25606,25954,'一、文件出台背景，正文第3段',4),'SUP-NHC2024-EXP007':(11894,12100,26629,26835,'二、《意见》的总体考虑，正文第2段',7),'SUP-NHC2024-EXP012':(13352,13540,28087,28275,'三、《意见》的主要内容，“三是完善基层药品集中供应配送机制”整段',12)}
pure=[];sa=[]
for item in supp:
 source=Path(item['source_snapshot']);raw=source.read_bytes();assert sha(raw)==item['source_sha256'];s=raw.decode('utf-8');text=item['text'];positions=[m.start() for m in re.finditer(re.escape(text),s)];n=copy.deepcopy(item);n.pop('selection_rule');n.pop('binary_status')
 if item['supplement_id']=='SUP-NMPA2024-PILOT':
  assert positions==[200] and s[200:2307]==text
  n['original_url']='https://www.nmpa.gov.cn/xxgk/fgwj/gzwj/gzwjyp/20240731184417109.html'
  n['locator']={'document_title':item['source_title'],'sections':'方案标题、引言及一至五全部正文','txt_line_start_1based':5,'txt_line_end_inclusive_1based':39,'character_range_0based_halfopen':[200,2307],'utf8_byte_range_0based_halfopen':[566,6735]}
  n['source_document_kind']='2024试点工作方案正文';n['document_date']='2024-07-31';n['republication_date']='2024-08-01';n['document_number']='国药监药注〔2024〕21号'
 else:
  aa,bb,cc,dd,anchor,pindex=spans[item['supplement_id']];assert positions==[aa,cc] and s[aa:bb]==text and s[cc:dd]==text
  n['locator']={'section_and_paragraph':anchor,'html_body_paragraph_index_1based':pindex,'character_ranges_0based_halfopen':[[aa,bb],[cc,dd]],'html_lines_1based':[229,414],'dom_occurrences':['PC正文','手机版同文副本'],'local_paragraph_identifier':item['locator']}
  n['source_document_kind']='同政策官方政策解读';n['policy_document_date']='2024-11-14';n['source_publication_date']='2024-11-22';n['republication_datetime']='2024-11-25 09:42:49';n['policy_document_number']='国卫药政发〔2024〕38号';n.pop('source_date')
 n['text_sha256']=sha(text.encode());pure.append(n)
 rid=item['record_id'];f=frame[rid];targetsha=f['source_position']['unit_source_sha256_recorded'];target=bysha[targetsha];assert shafile(target['snapshot'])==targetsha
 relationship={'RECODE25-01729':'same 2024 plan source document','RECODE25-02233':'2025 announcement explicitly mentions the trial organized in 2024; historical plan association, not an assertion that the whole 2024 plan is currently in force','RECODE25-02269':'2024 approval explicitly cites the exact plan title','RECODE25-04915':'official explainer title/republication links identify the same policy; the excerpt is explanatory source text, not the same primary-policy paragraph'}[rid]
 sa.append({'binding_key':[rid,item['supplement_id']],'input_text_byte_equivalent':True,'source_snapshot':str(source),'source_sha256':item['source_sha256'],'snapshot_byte_N':len(raw),'snapshot_hash_verified':True,'literal_character_positions':positions,'text_sha256':n['text_sha256'],'frame_original_id':f['original_id'],'frame_paragraph_ids':f['source_position']['paragraph_ids'],'target_source_sha256':targetsha,'target_source_snapshot_hash_verified':True,'target_source_unit_text':f['unit_text'],'document_linkage_evidence':relationship,'removed_rule_key':'selection_rule','old_locator':item['locator'],'new_locator':n['locator'],'source_binary_status':item['binary_status']})
assert len({(x['record_id'],x['supplement_id']) for x in pure})==6
sup_new=OUT/'prospective-common-supplements-source-only-v2.jsonl';write_new(sup_new,''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in pure))
dump_new(OUT/'prospective-common-supplements-audit-v2.json',{'status':'six source excerpts verified; four target record bindings; pure next-version supplemental source only','input':{'path':str(sup_path),'sha256':shafile(sup_path),'unchanged':True},'output':{'path':str(sup_new),'sha256':shafile(sup_new)},'source_review_agent_kind':'AI source review; not human coding','source_review_model':'GPT-6.1 Sol / ultra','source_binding_N':6,'target_record_N':4,'source_document_N':2,'source_text_fields_unchanged':True,'selection_or_rule_hints_in_output':False,'rule_text_removed_N':6,'non_locator_rule_text_removed_N':3,'labels_or_unsealed_pilot_inputs_read':False,'pilot01_modified':False,'merged_into_canonical_v2':False,'bindings':sa,'independent_online_checks':{'NMPA':'Official Shanghai drug regulator repost full text read. The original NMPA page/local derived TXT were not authenticated as identical online HTML bytes.','NHC':'Child source reviewer fetched Shanxi official repost in memory: HTTP200,45784bytes,SHA a316b256f96485f4b4bb62ffd5eb5b70c09b7d118fe5dd7ba5e7303607d705a2; equal to saved HTML. Primary NHC URL returned HTTP412; official index supports explainer date2024-11-22. PC/mobile duplicates are one source.'},'limits':['2024 trial plan does not import the 2025 announcement conditions. The 2025 announcement historical mention is not current whole-plan incorporation.','EXP004/007/012 are local IDs, not original native HTML anchors.','Supplement text does not itself supply a dimension label or adjudication.']})
assert shafile(oldpath)==oldhash
print(json.dumps({'v1_unchanged':True,'v2_sha256':shafile(newpath),'pending_reviewed_N':13,'policy_text_change_field_N':len(changes),'pure_supplement_sha256':shafile(sup_new)},ensure_ascii=False,indent=2))
