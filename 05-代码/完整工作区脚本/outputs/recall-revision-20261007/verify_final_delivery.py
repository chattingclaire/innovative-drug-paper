"""Read-only final binding gate, using actual hashes and actual reviewed pages."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime
import json,argparse

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
BUNDLED_SOFFICE='/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/MacOS/soffice'
def digest(path):return sha256(Path(path).read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text())
def resolve(path):
 p=Path(path)
 return p.resolve() if p.is_absolute() else (PROJECT/p).resolve()
def bound(path,value):
 assert digest(path)==value,('Version/hash mismatch',str(path))
def passed(record):assert str(record.get('status','')).startswith('passed'),record.get('status')
def image_for(row,kind):
 page=row['page'];wanted=row.get('png_sha256') or row.get('sha256')
 if row.get('path'):
  path=Path(row['path']);bound(path,wanted);assert path.is_relative_to(ROOT)
  return path
 # Locate only within this new task root, by actual page filename and digest.
 matches=[p for p in ROOT.rglob(f'page-{page}.png') if digest(p)==wanted]
 assert matches,('Reviewed page image unavailable',kind,page,wanted)
 return matches[0]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--readiness',action='store_true');args=ap.parse_args()
 mandatory=['论文修订稿-三部门版.docx','校核与待确认事项.docx','三部门编码与注意力指标.xlsx',
  '三部门编码指标.json','三部门注意力分布与敏感性.json','文稿生成与证据绑定.json',
  '最终文稿数据与引用核验.json','最终LLM执行独立核验.json','三部门编码指标核验.json',
  '聚类区间独立重算核验.json','三部门数据独立QA.json','workbook-qa.json',
  'workbook-visual-qa.json','最终篇幅与模板核验.json','final_evidence_visual_QA.json',
  '论证证据索引.json','指标依据与理论对齐.md','指标依据与理论对齐.json','llm-v30/stability_comparison_v30.json',
  'rules-v31/release_completed_material_v3.json','source_safety_population_v3_independent_QA.json']
 missing=[n for n in mandatory if not (ROOT/n).is_file()]
 if args.readiness:
  print(json.dumps({'status':'ready_for_final_gate' if not missing else 'pending_actual_artifacts','missing':missing,
    'note':'Readiness only; does not certify data, model, sources, visual quality or final delivery.'},ensure_ascii=False));return
 assert not missing,('Final artifacts not ready',missing)
 coding=read('三部门编码指标.json');attention=read('三部门注意力分布与敏感性.json')
 assert coding['method_bindings']['rule']==attention['method_bindings']['rule']
 assert coding['method_bindings']['llm']['path']==attention['method_bindings']['llm']['path']
 rb=coding['method_bindings']['rule'];lp=Path(coding['method_bindings']['llm']['path']).resolve()
 assert lp.is_relative_to(ROOT) and coding['method_bindings']['llm']['method']=='llm_gpt56_sol_v30'
 assert rb['method']=='rules_v31'
 for record in [coding,attention]:
  for name,value in record['source_sha256'].items():bound(resolve(name),value)
 release=read('rules-v31/release_completed_material_v3.json')
 bound(Path(rb['rules']),release['prediction_sha256']);bound(Path(rb['inputs']),release['input_sha256'])
 for path,value in release['artifacts'].items():bound(path,value)
 final_manifest=json.loads((lp.parent/'final_manifest.json').read_text())
 assert final_manifest['status']=='complete_validated_full_corpus' and final_manifest['n']==4924
 assert final_manifest['source_material_version']=='v3'
 assert final_manifest['all_4924_rows_actual_selected_request_material_equal_final_v3'] is True
 bound(lp,final_manifest['predictions_sha256'])
 selected={'论文修订稿-三部门版.docx':ROOT/'论文修订稿-三部门版.docx',
  '校核与待确认事项.docx':ROOT/'校核与待确认事项.docx',
  '三部门编码与注意力指标.xlsx':ROOT/'三部门编码与注意力指标.xlsx',
  '三部门编码指标.json':ROOT/'三部门编码指标.json',
  '三部门注意力分布与敏感性.json':ROOT/'三部门注意力分布与敏感性.json',
  'actual_llm_predictions':lp,'actual_rule_predictions':Path(rb['rules']),
  'actual_shared_rule_material':Path(rb['inputs'])}
 expected={name:digest(path) for name,path in selected.items()}
 manuscript=read('最终文稿数据与引用核验.json');passed(manuscript)
 for key,name in [('main_sha256','论文修订稿-三部门版.docx'),('memo_sha256','校核与待确认事项.docx'),
  ('statistics_sha256','三部门编码指标.json'),('attention_sha256','三部门注意力分布与敏感性.json')]:
  assert manuscript[key]==expected[name],key
 assert manuscript['numerical_prose_checks']['stability_material_and_actual_output_binding_checked']
 composite=manuscript['numerical_prose_checks']['composite_selected_request_binding']
 assert composite['status']=='passed_current_v3_selected_actual_request_and_raw_output_binding'
 assert composite['prediction_sha256']==expected['actual_llm_predictions']
 assert composite['rule_input_sha256']==expected['actual_shared_rule_material']
 for path,value in composite['selected_raw_response_sha256'].items():bound(path,value)
 assert manuscript['embedded_figure_data_and_hashes_checked'] and manuscript['all_manifest_and_statistics_source_hashes_verified']
 document_manifest=read('文稿生成与证据绑定.json')
 assert document_manifest['status']=='actual_results_bound'
 for path,value in document_manifest['source_sha256'].items():bound(path,value)
 for path,value in document_manifest['output_sha256'].items():bound(path,value)
 for name,target in [('三部门编码指标核验.json','三部门编码指标.json'),('聚类区间独立重算核验.json','三部门编码指标.json'),('三部门数据独立QA.json','三部门注意力分布与敏感性.json')]:
  qa=read(name);passed(qa);assert qa['target_sha256']==expected[target]
 for name in ['workbook-qa.json','workbook-visual-qa.json']:
  qa=read(name);passed(qa);assert qa['workbook_sha256']==expected['三部门编码与注意力指标.xlsx']
 workbook=read('workbook-qa.json')
 assert workbook['explicit_incomplete_llm_records']==0 and workbook['unexpected_formula_errors']==0
 for name,value in workbook['source_sha256'].items():bound(ROOT/name,value)
 workbook_visual=read('workbook-visual-qa.json')
 assert workbook_visual['all_six_sheets_actually_viewed'] is True
 for view in workbook_visual['views']:
  assert view.get('actual_image_opened') is True;bound(ROOT/view['filename'],view['sha256'])
 layout=read('最终篇幅与模板核验.json');visual=read('final_evidence_visual_QA.json')
 passed(layout);passed(visual)
 assert layout['main_docx_sha256']==expected['论文修订稿-三部门版.docx']
 bound(layout['render_pdf_path'],layout['render_pdf_sha256'])
 for record in visual['document_bindings'].values():bound(record['path'],record['sha256'])
 assert visual['document_bindings']['论文修订稿-三部门版.docx']['sha256']==expected['论文修订稿-三部门版.docx']
 assert visual['document_bindings']['校核与待确认事项.docx']['sha256']==expected['校核与待确认事项.docx']
 main_n=layout['rendered_pages'];assert visual['main_page_count']==main_n
 memo_n=visual['memo_page_count'];pages=set()
 for row in layout['page_reviews']:
  assert row.get('actually_opened_and_viewed') is True
  image_for(row,'main');pages.add(row['page'])
 assert set(layout['actually_reviewed_pages'])<=pages
 for row in visual['actual_viewed_main_pages']:image_for(row,'main');pages.add(row['page'])
 memo_pages=set()
 for row in visual['actual_viewed_memo_pages']:image_for(row,'memo');memo_pages.add(row['page'])
 assert pages==set(range(1,main_n+1)),('Not all current main pages reviewed',pages,main_n)
 assert memo_pages==set(range(1,memo_n+1)),('Not all current memo pages reviewed',memo_pages,memo_n)
 execution=read('最终LLM执行独立核验.json');passed(execution)
 assert execution['n']==4924 and execution['predictions_sha256']==expected['actual_llm_predictions']
 assert execution['shared_rule_input_sha256']==expected['actual_shared_rule_material']
 assert execution['selected_tool_event_count']==0 and execution['mechanically_edited_output_selected'] is False
 assert execution['selected_actual_execution_count']==composite['selected_batch_count']==197
 assert execution['all_4924_rows_actual_selected_request_material_equal_final_v3'] is True
 stability=read('llm-v30/stability_comparison_v30.json')
 assert stability['status']=='computed_from_new_actual_model_calls' and stability['candidate']=='03'
 assert stability['production_predictions_sha256']==expected['actual_llm_predictions']
 assert len(stability['comparisons'])==3
 index=read('论证证据索引.json');assert index['status']=='final_bound'
 assert len(index['reference_catalog'])==manuscript['reference_count']
 for catalog in ['statistic_file_catalog','final_document_bindings','policy_source_catalog']:
  for entry in index[catalog].values():bound(entry['path'],entry['sha256'])
 bound(index['final_manifest']['path'],index['final_manifest']['sha256'])
 assert set(index['verification_artifacts'])==set(index['verification_artifact_bindings'])
 for p,entry in index['verification_artifact_bindings'].items():
  assert p==entry['path']
  bound(entry['path'],entry['sha256'])
  if 'reuse_scope' in entry:
   assert 'not current model, numerical, document-layout, or new visual validation' in entry['reuse_scope']
 basis=read('指标依据与理论对齐.json')
 assert basis['status']=='current_actual_results_bound' and basis['candidate']=='03'
 assert basis['output_sha256']==digest(ROOT/'指标依据与理论对齐.md')
 for p,value in basis['source_sha256'].items():bound(p,value)
 # Prior policy/text source review may be reused only with its original scope.
 prior=index['prior_source_audit_binding'];bound(prior['path'],prior['sha256'])
 policy=json.loads(Path(prior['path']).read_text())
 assert policy['source_hash_pass'] and policy['quote_pass'] and policy['matrix_complete']
 for name,value in policy['files_sha256'].items():bound(resolve(name),value)
 qa_names=[n for n in mandatory if n.endswith('.json')]
 result={'status':'passed_final_delivery_bindings','checked_at':datetime.now().astimezone().isoformat(),
  'files':{name:{'path':str(path),'sha256':expected[name]} for name,path in selected.items()},
  'evidence_and_qa':{name:{'path':str(ROOT/name),'sha256':digest(ROOT/name)} for name in qa_names},
  'actual_visual_review':{'main_pages':sorted(pages),'memo_pages':sorted(memo_pages)},
  'libreoffice_word_counts':layout['word_counts'],'bundled_render_runtime_required':BUNDLED_SOFFICE,
  'main_corpus_units':coding['population_n'],'all_model_execution_units':final_manifest['n'],
  'reference_count':manuscript['reference_count'],'human_validation_completed':False,
  'AC_actual_provenance':'AI agents; original first submissions and original visible materials retained as development references',
  'material_identity':'Current rules and each selected actual LLM request share material v3; affected whole batches were rerun unconditionally, unchanged batches retained by exact material identity. Original A/C were not rerun on the revised material.',
  'prior_source_review_reuse':prior,'remaining':['Actual independent human coding and adjudication','Author, affiliation, funding and submission details'],
  'scope':'Checks actual delivery/source/QA version bindings and recorded page coverage. Does not guarantee journal acceptance or independent human validity.'}
 (ROOT/'最终交付核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'delivered_files':3,'main_pages':main_n,'memo_pages':memo_n,'human_validation_completed':False},ensure_ascii=False))

if __name__=='__main__':main()
