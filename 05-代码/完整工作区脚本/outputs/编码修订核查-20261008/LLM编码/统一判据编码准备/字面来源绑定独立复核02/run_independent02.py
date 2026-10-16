"""Independent invented source tests only. Original binder01/02 remain read-only."""
import copy,hashlib,importlib.util,json,sys,tempfile,zipfile
from html import escape
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
design=json.loads((HERE/'design_independent02.json').read_text())
CODE=Path(design['binder']['path']); initial=sha(CODE)
assert initial==design['binder']['sha256']
assert not (HERE/'actual_independent02.json').exists()
spec=importlib.util.spec_from_file_location('independent_literal02',CODE)
binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def p(text):return '<w:p><w:r><w:t>'+escape(text)+'</w:t></w:r></w:p>'
def textbox(text):return '<w:r><w:drawing><w:txbxContent>'+p(text)+'</w:txbxContent></w:drawing></w:r>'
def package(path,body,member='word/document.xml',malformed=False):
    xml='<w:document xmlns:w="'+W+'"><w:body>'+body+'</w:body></w:document>'
    with zipfile.ZipFile(path,'w') as z:z.writestr(member,xml if not malformed else '<w:document')
results=[]
with tempfile.TemporaryDirectory(prefix='independent-literal02-') as tmp:
 for case in design['checks']:
    name=case['name'];folder=Path(tmp)/name;folder.mkdir()
    leaf='Native α literal.';container=leaf;para=leaf;expected_start=0;expected_p=None
    source=folder/'actual.txt';source.write_text(leaf,encoding='utf-8')
    source_locator={};candidate_locator={'leaf_scope':'unit','unit_id':'u-new','paragraph_id':'p-new'}
    format_declared=None;additional_override=None
    if name.startswith('docx_'):
      source=folder/'actual.docx';body=p(leaf)
      if name=='docx_outer_text_across_textbox_preserved':
        leaf='Outer α\tBeta\nEnd';container=leaf;para=leaf
        body='<w:p><w:r><w:t>Outer α</w:t><w:tab/></w:r>'+textbox('Floating not owned.')+'<w:r><w:t>Beta</w:t><w:br/><w:t>End</w:t></w:r></w:p>'
        source_locator={'xml_paragraph_index':0};expected_p=0
      elif name in {'docx_textbox_partial_outer_index_rejected','docx_textbox_inner_index_rejected'}:
        body='<w:p><w:r><w:t>Outer other.</w:t></w:r>'+textbox(leaf)+'</w:p>'
        source_locator={'xml_paragraph_index':0 if 'outer_index' in name else 1}
      elif name in {'docx_nested_p_outer_index_rejected','docx_nested_p_inner_index_rejected'}:
        body='<w:p><w:r><w:t>Outer other.</w:t></w:r>'+p(leaf)+'</w:p>'
        source_locator={'xml_paragraph_index':0 if 'outer_index' in name else 1}
      elif name=='docx_nested_table_outer_index_rejected':
        body='<w:p><w:r><w:t>Outer other.</w:t></w:r><w:tbl><w:tr><w:tc>'+p(leaf)+'</w:tc></w:tr></w:tbl></w:p>'
        source_locator={'xml_paragraph_index':0}
      elif name.startswith('docx_outer_duplicate_with_textbox'):
        body='<w:p><w:r><w:t>'+escape(leaf)+'</w:t></w:r>'+textbox(leaf)+'</w:p>'
        if name.endswith('explicit_outer'):source_locator={'xml_paragraph_index':0};expected_p=0
      elif name.startswith('docx_two_native_paragraphs'):
        body=p(leaf)+p(leaf)
        if name.endswith('explicit_second'):source_locator={'xml_paragraph_index':1};expected_p=1
      elif name=='docx_format_conflicting_txt_suffix':
        source=folder/'actual.txt';format_declared='docx'
      package(source,body)
    elif name.startswith('extensionless_'):
      source=folder/'source';format_declared='docx'
      if name=='extensionless_xml_not_zip':source.write_text('<w:document>'+leaf+'</w:document>')
      else:package(source,p(leaf),member='word/header.xml' if name=='extensionless_zip_missing_document' else 'word/document.xml',malformed=name=='extensionless_zip_malformed_document')
      if name=='extensionless_docx_real_undeclared':format_declared=None
      if name=='extensionless_docx_real_explicit':expected_p=0
    elif name.startswith('additional_'):
      if name=='additional_relation_literal_absent':source.write_text('Different literal in selected source.')
    elif name.startswith('txt_'):
      para=leaf+'\n'+leaf;container=para;source.write_text(container)
      candidate_locator['unit_start_in_paragraph']=0
      if name=='txt_both_repeat_positions_explicit':source_locator['char_start']=len(leaf)+1;expected_start=len(leaf)+1
    elif name=='html_duplicate_nodes_explicit_second':
      source=folder/'actual.html';source.write_text('<html><body><p>'+escape(leaf)+'</p><p>'+escape(leaf)+'</p></body></html>')
      source_locator={'html_node_path':'/html[0]/body[0]/p[1]'}
    elif name=='json_pointer_repeat_explicit_second':
      source=folder/'actual.json';container=leaf+'\n'+leaf;source.write_text(json.dumps({'native':{'value':container}},ensure_ascii=False))
      source_locator={'json_pointer':'/native/value','char_start':len(leaf)+1};expected_start=len(leaf)+1
    generic=folder/'generic.txt';generic.write_text('Separate declared source.')
    additional=[{'path':source.name,'sha256':sha(source)}]
    if name=='additional_relative_target_second_entry':additional=[{'path':generic.name,'sha256':sha(generic)},*additional]
    if name=='additional_duplicate_path_entries':additional=additional*2
    if name=='additional_wrong_target_sha':additional[0]['sha256']='0'*64
    payload={'source':str(generic),'source_sha256':sha(generic),'additional_sources':additional,
             'unit_candidates':[{'id':'u-new','text':leaf,'paragraph_id':'p-new'}],
             'paragraphs':[{'id':'p-new','text':para}]}
    candidate=folder/'candidate.json';candidate.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    identity={'source':str(source),'source_sha256':sha(source)}
    if format_declared is not None:identity['format']=format_declared
    request={'record_id':name,'raw_pointer':'/text','source_identity':identity,
             'candidate_identity':{'candidate_file':str(candidate),'candidate_sha256':sha(candidate)},
             'candidate_locator':candidate_locator,'source_locator':source_locator}
    prior=copy.deepcopy(request);binding=binder.bind_leaf(leaf,**request)
    assert prior==request
    bound=binding['status'] in {binder.BOUND,binder.GRID_BOUND}
    evidence_checks={}
    if bound:
      pos=binding['source_position']['literal_position']
      evidence_checks={'source_start':pos['start']==expected_start,'source_end':pos['end']==expected_start+len(leaf),
        'native_container_sha':pos['container_text_sha256']==binder.digest(container),
        'candidate_leaf_sha':binding['text_sha256']==binder.digest(leaf),
        'candidate_source_axes':binding['axes']['candidate_position_bound'] and binding['axes']['source_literal_position_bound'],
        'source_identity_sha':binding['source']['sha256']==sha(source),
        'candidate_identity_sha':binding['candidate_identity']['sha256']==sha(candidate)}
      if expected_p is not None:evidence_checks['xml_p_index']=pos['xml_paragraph_index']==expected_p
      if name=='extensionless_docx_real_explicit':evidence_checks['explicit_format_resolution']=binding['source']['format_resolution']['method']=='explicit_declaration_and_actual_ZIP_word_document_xml'
      if name=='additional_relative_target_second_entry':evidence_checks['additional_pointer']=binding['candidate_position']['source_relation']['candidate_source_json_pointer']=='/additional_sources/1'
      if name=='txt_both_repeat_positions_explicit':evidence_checks['candidate_and_source_positions_separate']=binding['candidate_position']['unit_in_paragraph_span']['start']==0 and pos['start']==len(leaf)+1
      if name=='html_duplicate_nodes_explicit_second':evidence_checks['html_node_path']=pos['html_node_path']==source_locator['html_node_path']
      if name=='json_pointer_repeat_explicit_second':evidence_checks['source_json_pointer']=binding['source_position']['source_json_pointer']==source_locator['json_pointer']
    results.append({'name':name,'expected_bound':case['expected_bound'],'actual_bound':bound,'passed':bound==case['expected_bound'] and all(evidence_checks.values()),'evidence_checks':evidence_checks,'binding':binding,'input_unchanged':True})
assert sha(CODE)==initial
preservation=json.loads((HERE/'preservation_before02.json').read_text())['files_sha256']
assert all(sha(pth)==h for pth,h in preservation.items())
report={'scope':design['scope'],'design_sha256':sha(HERE/'design_independent02.json'),'runner_sha256':sha(__file__),
        'binder_sha256_before':initial,'binder_sha256_after':sha(CODE),'binder_unchanged':True,'original01_02_file_n':len(preservation),'original01_02_unchanged':True,
        'authenticators_mocked':False,'actual_policy_leaves_bound':0,'model_or_rule_calls':0,'checks':results,'passed':all(r['passed'] for r in results)}
output=HERE/'actual_independent02.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'check_n':len(results),'pass_n':sum(r['passed'] for r in results),'failures':[{'name':r['name'],'expected_bound':r['expected_bound'],'actual_bound':r['actual_bound'],'reasons':r['binding']['reasons'],'evidence_checks':r['evidence_checks']} for r in results if not r['passed']],'output_sha256':sha(output)},ensure_ascii=False))
