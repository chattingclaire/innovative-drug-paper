from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, shutil, hashlib
from pypdf import PdfReader

work=Path(__file__).resolve().parent
out=work.parent
docx=out/'创新药评价的注意力配置差异与协调路径-交稿版.docx'
pdf=out/(docx.stem+'.pdf')
render=work/'render-final-v3'
shutil.copyfile(render/pdf.name,pdf)
assert len(PdfReader(pdf).pages)==23
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=work/'render'
for i in range(1,19):
    if i!=13:assert sha(old/f'page-{i}.png')==sha(render/f'page-{i}.png')
for i in range(19,24):assert sha(work/'render-final-v2'/f'page-{i}.png')==sha(render/f'page-{i}.png')
record=json.loads((work/'integration-record.json').read_text())
record.update({'pdf':str(pdf),'pdf_sha256':sha(pdf),'docx_sha256':sha(docx),'page_count':23,'visual_review':'completed_all_pages','visual_review_scope':{'pages_1_8':'submission_content_audit; identical in final render','pages_9_16':'submission_methods_edit; all except 13 identical in final render; page13 updated and reviewed by root','pages_17_18':'submission_validation_stats; identical in final render','pages_19_23':'root, render v2; all identical in final v3'},'table_C2_single_row_continuation_fixed':True,'citation_line_start_orphan_fixed':True,'render_engine':'bundled LibreOffice, journal render-fonts.conf','completed_at_shanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()})
(work/'integration-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
project=out.parent.parent
progress_path=project/'progress.json'
progress=json.loads(progress_path.read_text())
assert 'current_closure_20261012' in progress
progress['current_closure_20261012']['manuscript_submission_20261013']={'status':'completed_manuscript_delivery','docx':str(docx),'pdf':str(pdf),'page_count':23,'updated_at_shanghai':record['completed_at_shanghai'],'continues_original_manuscript':True,'all_66_original_references_preserved':True,'current_200_reference_process':'AI-assisted initial review followed by user human confirmation; A/B are numbered exports of same confirmed result','current_200_statistics_adopted':True,'full4481_machine_results_adopted':True,'new_full_machine_rerun':False,'all_pages_visually_reviewed':True,'previous_formal_two_independent_human_acceptance_not_reclassified':True,'integration_record':str(work/'integration-record.json')}
tmp=progress_path.with_suffix('.submission-tmp.json');tmp.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n');tmp.replace(progress_path)
print(json.dumps({'docx':str(docx),'pdf':str(pdf),'pages':23,'sha256_docx':sha(docx),'sha256_pdf':sha(pdf)},ensure_ascii=False))
