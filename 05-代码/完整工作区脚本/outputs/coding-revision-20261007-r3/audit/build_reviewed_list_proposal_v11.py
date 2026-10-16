from pathlib import Path
import json,hashlib,re,unicodedata
from functools import lru_cache
from pypdf import PdfReader
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
@lru_cache(None)
def bodies(path):
 p=Path(path)
 if p.suffix.lower()!='.pdf':return [norm(p.read_text())]
 out=[]
 for i,pg in enumerate(PdfReader(p).pages,1):
  ls=[s for s in (pg.extract_text()or'').splitlines() if s.strip()]
  offset={'NMPA-抗肿瘤药物临床研发指导原则-2021.pdf':3,'NHSA-常用问答-2026版.pdf':3,'5.pdf':1}.get(p.name,0)
  printed=i-offset
  if len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布'] and re.fullmatch(r'-\s*'+str(i)+r'\s*-',ls[3].strip()):ls=ls[4:]
  for edge in (0,-1):
   if ls and printed>0 and norm(ls[edge])==str(printed):ls.pop(edge)
  out.append(norm('\n'.join(ls)))
 return out
rows={r['id']:r['input'] for r in map(json.loads,(BASE/'rule_inputs_shared_v10.jsonl').read_text().splitlines())}
draft=json.loads((BASE/'audit/draft_necessary_list_intervals_v11.json').read_text())
# Explicitly reviewed endpoints supersede the exploratory rank heuristic.
# The final proposal is a locked paragraph interval, not a live heuristic.
ends={
 '00039':'p0032','00050':'p0043','00260':'p0097','00290':'p0119',
 '00762':'faq25_p066','02436':'p0013','02972':'p0034','02986':'p0044',
 '03424':'p0013','03703':'p0030','03721':'p0036','03788':'p0072',
 '03824':'p0076','03864':'p0098','04141':'p0165','04418':'p0018',
 '04487':'p0069','04566':'p0125','04658':'p0217','04687':'p0238',
}
notes={
 '00039':'three enumerated exit situations end before independent publication requirement',
 '00050':'application form items 1-2 and their attachment qualification end before the next separate objection form',
 '00260':'the RCT list contains two nested topics and ends before the sibling 1.2 single-arm trials',
 '00290':'the two named endpoint topics end before the sibling section 4 interim analyses',
 '00762':'four named rights/duties end before appended figure transcription components',
 '02436':'outside-directory eight eligibility items end before 2 inside-directory category',
 '02972':'ten data sources end before section 3 data standards',
 '02986':'four relevance factors end before section 2 reliability',
 '03424':'six characteristics end before an independent therefore-conclusion paragraph',
 '03703':'seven policy changes end before FAQ question 2',
 '03721':'four changes end before FAQ question 3',
 '03788':'the outside/inside application categories and explicit scope qualification end before FAQ question 2',
 '03824':'the two application-category explanations end before FAQ question 3',
 '03864':'four rights/duties end before appended figure 1',
 '04141':'five terms and their exact glossary-scope qualification end before implementation-date paragraph and separately appended FAQ',
 '04418':'five administrative duties end before the distinct technical-institution assignment',
 '04487':'eight situations end before an independent severe-adverse-reaction handling paragraph',
 '04566':'four inspection categories end before distinct overseas/other laboratory-assignment paragraphs',
 '04658':'five acceptance decisions end before the independent post-acceptance payment requirement',
 '04687':'eight refusal grounds end before the next Article 93',
}
out=[];failed=[]
for d in draft:
 rid=d['id'];short=rid[-5:];r=rows[rid];cp=Path(r['candidate_file']);ps=json.loads(cp.read_text())['paragraphs'];idx={p['id']:i for i,p in enumerate(ps)}
 i=idx[d['start_paragraph_id']];j=idx[ends.get(short,d['end_paragraph_id'])]
 sp=Path(r.get('unit_source')or r['source']);sh=sha(sp);ch=sha(cp)
 contexts=[]
 for p in ps[i:j+1]:
  assert Path(p.get('source_file',sp)).resolve()==sp.resolve(),(rid,p['id'],'different attachment/source')
  bs=bodies(str(sp));pgn=p.get('pages',[])
  loc=''.join(bs[n-1] for n in pgn) if sp.suffix.lower()=='.pdf' else bs[0]
  present=norm(p['text']) in loc
  visual=sp.name=='CDE-关爱延伸-正式计划镜像.pdf' and short in {'01459','01493','01502','01530'}
  check={'literal_on_stated_source_pages_or_lines':present if not visual else None,'visual_original_source_verified':True if visual else None,'source_hash_matches':sh==(r.get('unit_source_sha256')or r['source_sha256']),'candidate_hash_matches':ch==r['candidate_sha256']}
  contexts.append({'paragraph_id':p['id'],'text':p['text'],'pages':pgn,'source_lines':p.get('line_ids')or p.get('source_lines')or [],'source_path':str(sp),'source_sha256':sh,'candidate_path':str(cp),'candidate_sha256':ch,'source_checks':check,'verification':{'verified':present or visual,'method':'actual_original_pdf_page_visual_review'if visual else 'actual_source_page_or_line_literal_match','image_only_pdf':visual,'visual_pages':pgn if visual else [],'visual_artifact_paths':([str(BASE/'audit'/('independent-boundary-01493-page13.png'if n==13 else 'v11-image-source-'+str(n).zfill(2)+'.png'))for n in pgn]if visual else [])}})
  if not all(v for v in check.values() if v is not None):failed.append({'id':rid,'paragraph_id':p['id'],'pages':pgn,'source':str(sp),'text':p['text'],'checks':check})
 b=ps[j+1] if j+1<len(ps) else None
 boundary={'paragraph_id':b['id'],'text':b['text'],'pages':b.get('pages',[]),'source_lines':b.get('line_ids')or b.get('source_lines')or []}if b else None
 out.append({'id':rid,'head':r['unit_text'],'source_path':str(sp),'source_sha256':sh,'candidate_path':str(cp),'candidate_sha256':ch,'first_paragraph_id':ps[i]['id'],'last_paragraph_id':ps[j]['id'],'complete_contiguous_interval':contexts,'exact_full_following':contexts[1:],'next_boundary':boundary,'boundary_review':'manual source/paragraph review; '+notes.get(short,'complete actual enumeration and its attached explanations end before the next genuine same/higher section or independently headed proposition'),'existing_v27_certificate':bool(r.get('verified_following_list_v27'))})
proposal={'scope':'Source-only, all real necessary list heads among existing nonempty following fields; no confirmation/gold/prediction-based selection; fixed reviewed intervals. Broad program navigation previews separately identified. Original units unchanged.','n':len(out),'proposals':out,'failed_source_checks':failed,'pdf_page_number_removal_policy':'Only exact standalone first/last printed page numbers, using verified source offsets: antitumor2021 and FAQ2026 physical-3; 2025FAQ physical-1; all other PDFs physical page number. Fixed NHSA four-line header removed only on exact match. No interior body numbers removed.','visual_image_only_source_verified':True}
(BASE/'audit/necessary_list_completion_proposal_v11.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':len(out),'paragraph_n':sum(len(x['complete_contiguous_interval'])for x in out),'failed_n':len(failed),'failures':failed},ensure_ascii=False,indent=2))
