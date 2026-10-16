"""Seven predeclared invented DOCX boundary checks; no policy corpus/coder."""
import copy,hashlib,importlib.util,json,sys,tempfile,zipfile
from html import escape
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;CODE=HERE/'literal_source_binder.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
phase=sys.argv[1];assert phase in {'before','after'}
output=HERE/('constructed_execution03_'+phase+'.json');assert not output.exists()
contract=json.loads((HERE/'implementation_contract_before03.json').read_text())
initial=sha(CODE)
if phase=='before':assert initial==contract['parent_code']['sha256']
spec=importlib.util.spec_from_file_location('declared03_'+phase,CODE);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def p(text):return '<w:p><w:r><w:t>'+escape(text)+'</w:t></w:r></w:p>'
checks=[]
with tempfile.TemporaryDirectory(prefix='literal03-'+phase+'-') as tmp:
 for case in contract['checks']:
    name=case['name'];folder=Path(tmp)/name;folder.mkdir();source=folder/'native.docx';candidate=folder/'candidate.json'
    leaf='Fresh γ native text.';body=p(leaf);locator={};expected_index=0;expect_nested=None
    if name=='nested_level2_explicit_deep_p':
        body='<w:p><w:r><w:t>Outer.</w:t></w:r><w:p><w:r><w:t>Middle.</w:t></w:r>'+p(leaf)+'</w:p></w:p>';locator={'xml_paragraph_index':2}
    elif name=='nested_level2_outer_owned_flow':
        leaf='Root α\tEnd\nDone'
        body='<w:p><w:r><w:t>Root α</w:t><w:tab/></w:r><w:p><w:r><w:t>Unused middle.</w:t></w:r>'+p('Unused inner.')+'</w:p><w:r><w:t>End</w:t><w:br/><w:t>Done</w:t></w:r></w:p>';locator={'xml_paragraph_index':0}
    elif name=='same_level_paragraphs_explicit_third':
        body=p(leaf)*3;locator={'xml_paragraph_index':2};expected_index=2
    elif name=='ordinary_sdt_wrapped_paragraph':body='<w:sdt><w:sdtContent>'+p(leaf)+'</w:sdtContent></w:sdt>'
    elif name=='nested_p_unsupported_count_separate':
        body='<w:p><w:r><w:t>Unused outer.</w:t></w:r>'+p('Unused inner.')+'</w:p>'+p(leaf);expected_index=2;expect_nested=1
    elif name=='textbox_nested_p_explicit_deep_index':
        body='<w:p><w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>Unused middle.</w:t></w:r>'+p(leaf)+'</w:p></w:txbxContent></w:drawing></w:r></w:p>';locator={'xml_paragraph_index':2}
    elif name=='table_paragraph_explicit_index':body='<w:tbl><w:tr><w:tc>'+p(leaf)+'</w:tc></w:tr></w:tbl>';locator={'xml_paragraph_index':0}
    xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+body+'</w:body></w:document>'
    with zipfile.ZipFile(source,'w') as z:z.writestr('word/document.xml',xml)
    candidate.write_text(json.dumps({'source':str(source),'source_sha256':sha(source),'unit_candidates':[{'id':'u03','paragraph_id':'p03','text':leaf}],'paragraphs':[{'id':'p03','text':leaf}]},ensure_ascii=False))
    request={'record_id':name,'raw_pointer':'/text','source_identity':{'source':str(source),'source_sha256':sha(source)},'candidate_identity':{'candidate_file':str(candidate),'candidate_sha256':sha(candidate)},'candidate_locator':{'leaf_scope':'unit','unit_id':'u03','paragraph_id':'p03'},'source_locator':locator}
    prior=copy.deepcopy(request);result=b.bind_leaf(leaf,**request);assert prior==request
    bound=result['status'] in {b.BOUND,b.GRID_BOUND};evidence={}
    if bound:
      pos=result['source_position']['literal_position'];ext=result['source_position']['extraction']
      evidence={'xml_p_index':pos['xml_paragraph_index']==expected_index,'source_start':pos['start']==0,'source_end':pos['end']==len(leaf),'owned_native_text_sha':pos['container_text_sha256']==b.digest(leaf),'source_and_candidate_axes':result['axes']['source_literal_position_bound'] and result['axes']['candidate_position_bound']}
      if expect_nested is not None:
        evidence['nested_count_separate']=ext.get('unsupported_nested_paragraph_n')==expect_nested and ext['unsupported_table_or_textbox_paragraph_n']==0
    checks.append({'name':name,'expected_bound':case['expected_bound'],'actual_bound':bound,'passed':bound==case['expected_bound'] and all(evidence.values()),'evidence_checks':evidence,'binding':result,'input_unchanged':True})
assert sha(CODE)==initial
preservation=json.loads((HERE/'preservation_before03.json').read_text())['files_sha256'];assert all(sha(pth)==h for pth,h in preservation.items())
report={'phase':phase,'contract_sha256':sha(HERE/'implementation_contract_before03.json'),'code_sha256_before':initial,'code_sha256_after':sha(CODE),'code_unchanged_during_execution':True,'runner_sha256':sha(__file__),'previous_file_n':len(preservation),'previous_files_unchanged':True,'authenticators_mocked':False,'actual_policy_leaf_n':0,'rule_model_calls':0,'checks':checks,'passed':all(c['passed'] for c in checks)}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':phase,'n':len(checks),'pass_n':sum(c['passed'] for c in checks),'failed':[{'name':c['name'],'actual_bound':c['actual_bound'],'reasons':c['binding']['reasons'],'evidence_checks':c['evidence_checks']} for c in checks if not c['passed']],'report_sha256':sha(output)},ensure_ascii=False))
