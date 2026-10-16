"""Standalone synthetic repro; real temp ZIP/JSON, no authentication mocking."""
import hashlib,importlib.util,json,sys,tempfile,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
CODE=BASE/'字面来源绑定02/literal_source_binder.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(CODE)=='c0819f3ebfe39d67c76a7504b66de253e8a04f0712523a19cfc55caa9f875753'
spec=importlib.util.spec_from_file_location('binder02_repro',CODE)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
with tempfile.TemporaryDirectory(prefix='nested-p02-repro-') as temp:
    d=Path(temp);source=d/'actual.docx';candidate=d/'candidate.json';generic=d/'generic.txt'
    leaf='Native α literal.';generic.write_text('Separate declared source.')
    xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Outer other.</w:t></w:r><w:p><w:r><w:t>'+leaf+'</w:t></w:r></w:p></w:p></w:body></w:document>'
    with zipfile.ZipFile(source,'w') as z:z.writestr('word/document.xml',xml)
    candidate.write_text(json.dumps({'source':str(generic),'source_sha256':sha(generic),'additional_sources':[{'path':source.name,'sha256':sha(source)}],
        'unit_candidates':[{'id':'u-new','text':leaf,'paragraph_id':'p-new'}],'paragraphs':[{'id':'p-new','text':leaf}]},ensure_ascii=False))
    result=b.bind_leaf(leaf,record_id='docx_nested_p_inner_index_rejected',raw_pointer='/text',
        source_identity={'source':str(source),'source_sha256':sha(source)},
        candidate_identity={'candidate_file':str(candidate),'candidate_sha256':sha(candidate)},
        candidate_locator={'leaf_scope':'unit','unit_id':'u-new','paragraph_id':'p-new'},source_locator={'xml_paragraph_index':1})
    print(json.dumps({'expected_bound':False,'actual_bound':result['status'] in {b.BOUND,b.GRID_BOUND},'binding':result},ensure_ascii=False,indent=2))
